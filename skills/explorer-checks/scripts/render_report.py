"""Combine the automated findings and Claude's review into the report.

    python render_report.py <findings.json> --review review.json
                            --out <explorer>/security-accessibility-checks.md

The report is one file at one path, passing or not, so a re-run replaces it
and the explorer's history shows the progress. Its last line is a comment
holding the open finding ids. The next run reads it to list what was fixed
in between.

review.json, written by Claude after reading the code:

    {
      "reviewer": "Claude (claude-opus-5-5) via the explorer-checks skill",
      "resolutions": {"S-1a2b3c": {"verdict": "cleared",
                                   "reason": "only literals reach it"}},
      "findings": [{"check": "accessibility", "status": "fail",
                    "rule": "manual:link-purpose", "title": "...",
                    "where": "mockup/index.html:212", "evidence": "...",
                    "fix": "...", "wcag": "2.4.4"}],
      "manual": {"accessibility": [{"item": "1.3.1 Info and relationships",
                                    "result": "pass", "note": "..."}],
                 "security": [...]}
    }

A check passes only when it has no `fail`, no unresolved `review`, and,
for security and accessibility, a completed manual checklist. Automated
tools miss too much for a clean tool run to count as a pass on its own.
"""

import argparse
import json
import pathlib
import re

from common import CHECKS, Finding, read_findings

STATE = re.compile(r"<!-- explorer-checks:state (\{.*\}) -->")
NAMES = {"validity": "Code validity", "security": "Code security",
         "accessibility": "Accessibility (WCAG 2.2 AA)"}
NEEDS_MANUAL = {"security", "accessibility"}


def load_review(path):
    if not path or not pathlib.Path(path).exists():
        return {"resolutions": {}, "findings": [], "manual": {}}
    review = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    review.setdefault("resolutions", {})
    review.setdefault("findings", [])
    review.setdefault("manual", {})
    return review


def previous_open(path):
    if not path.exists():
        return None
    m = STATE.search(path.read_text(encoding="utf-8"))
    return json.loads(m.group(1)) if m else None


def apply_review(findings, review):
    """Turn review items into fail or cleared. Returns (findings, cleared)."""
    cleared = []
    out = []
    for f in findings + [Finding(**{"source": "review", **r})
                         for r in review["findings"]]:
        res = review["resolutions"].get(f.id)
        if res and f.status in ("review", "fail"):
            if res["verdict"] == "cleared":
                cleared.append((f, res["reason"]))
                continue
            f.status = "fail"
            if res.get("reason"):
                f.evidence = (f.evidence + "\n\nReview: " + res["reason"]
                              ).strip()
        out.append(f)
    return out, cleared


def verdicts(findings, review):
    result = {}
    for check in CHECKS:
        mine = [f for f in findings if f.check == check]
        manual = review["manual"].get(check, [])
        manual_fail = [m for m in manual if m.get("result") == "fail"]
        open_ = [f for f in mine if f.status in ("fail", "review")]
        missing_manual = check in NEEDS_MANUAL and not manual
        # A checklist fail blocks the pass but is not counted: the skill
        # requires a finding for it, and that finding is already counted.
        result[check] = {
            "pass": not open_ and not manual_fail and not missing_manual,
            "fail": sum(f.status == "fail" for f in mine),
            "review": sum(f.status == "review" for f in mine),
            "advisory": sum(f.status == "advisory" for f in mine),
            "missing_manual": missing_manual,
        }
    return result


def render(meta, findings, cleared, review, prev):
    v = verdicts(findings, review)
    passing = all(x["pass"] for x in v.values())
    open_ids = sorted(f.id for f in findings if f.status in ("fail", "review"))
    fixed = sorted(set(prev.get("open", [])) - set(open_ids)) if prev else []
    commit = meta.get("commit", "")[:10]
    L = ["# Security and accessibility checks", ""]

    if passing:
        L += [f"**Status: passing.** All three checks passed on "
              f"{meta['date']} at commit `{commit}`. Nothing is open. "
              f"Advisory items below are optional.", ""]
    else:
        n = sum(not x["pass"] for x in v.values())
        L += [f"**Status: not passing.** {n} of 3 checks have open items. "
              f"Each one below has a recommended fix. Make the fixes, then "
              f"re-run the explorer-checks skill. This file is replaced on "
              f"every run.", ""]
    if meta.get("dirty"):
        L += ["> The checkout had uncommitted changes when this ran, so it "
              "describes a working tree, not a commit.", ""]

    L += ["| | |", "|---|---|",
          f"| Explorer | {meta.get('repo', '')} |",
          f"| Commit | `{commit}` on `{meta.get('branch', '')}` |",
          f"| Date | {meta['date']} |",
          f"| Pages checked | {', '.join(f'`{p}`' for p in meta.get('pages', [])) or '—'} |",
          f"| Served from | {meta.get('served', '')} |"]
    if meta.get("live_url"):
        L += [f"| Live site (headers) | {meta['live_url']} |"]
    L += ["| Standard | WCAG 2.2 level AA |",
          f"| Tools | axe-core {meta.get('axe') or '—'}, html5lib, ruff, "
          f"bandit, pip-audit, headless Chromium |",
          f"| Reviewed by | {review.get('reviewer', 'not reviewed')} |",
          f"| Skill version | {meta.get('skill_version', '')} |", ""]

    L += ["## Summary", "",
          "| Check | Result | Must fix | Needs review | Advisory |",
          "|---|---|---:|---:|---:|"]
    for check in CHECKS:
        x = v[check]
        res = "Pass" if x["pass"] else "**Not passing**"
        if x["missing_manual"]:
            res += " (manual review not done)"
        L.append(f"| {NAMES[check]} | {res} | {x['fail']} | {x['review']} "
                 f"| {x['advisory']} |")
    L += ["", "## What a pass means", "",
          "Each check combines automated tools with a review of the code "
          "and pages against a written checklist. A pass means neither "
          "found anything open on the date and commit above. It is not a "
          "formal WCAG conformance claim. Automated testing finds a minority "
          "of accessibility barriers. Testing with people who use assistive "
          "technology is still worth doing, and a change to the explorer "
          "needs a re-run.", ""]

    for check in CHECKS:
        L += [f"## {NAMES[check]}", ""]
        open_ = [f for f in findings
                 if f.check == check and f.status in ("fail", "review")]
        if not open_:
            L += ["No open items.", ""]
        for f in sorted(open_, key=lambda f: (f.status != "fail", f.where)):
            label = "Must fix" if f.status == "fail" else "Needs review"
            L += [f"### `{f.id}` {f.title}", "",
                  f"- **{label}** · found by {f.source}" +
                  (f" · WCAG {f.wcag}" if f.wcag else ""),
                  f"- **Where:** `{f.where}`" if f.where else "", ""]
            if f.evidence:
                L += ["```text", f.evidence.strip(), "```", ""]
            L += [f"**Recommended fix:** {f.fix}", ""]
        manual = review["manual"].get(check, [])
        if manual:
            L += ["<details><summary>Manual checklist "
                  f"({sum(m.get('result') == 'pass' for m in manual)} pass, "
                  f"{sum(m.get('result') == 'fail' for m in manual)} fail, "
                  f"{sum(m.get('result') == 'n/a' for m in manual)} n/a)"
                  "</summary>", "", "| Item | Result | Note |",
                  "|---|---|---|"]
            L += [f"| {m['item']} | {m.get('result', '')} | "
                  f"{_cell(m.get('note', ''))} |" for m in manual]
            L += ["", "</details>", ""]
        mine = [(f, r) for f, r in cleared if f.check == check]
        if mine:
            L += [f"<details><summary>Cleared on review ({len(mine)})"
                  "</summary>", "", "| Id | Item | Where | Why cleared |",
                  "|---|---|---|---|"]
            L += [f"| `{f.id}` | {_cell(f.title)} | `{f.where}` | "
                  f"{_cell(r)} |" for f, r in mine]
            L += ["", "</details>", ""]

    if fixed:
        L += ["## Fixed since the last run", "",
              ", ".join(f"`{i}`" for i in fixed), ""]

    adv = [f for f in findings if f.status == "advisory"]
    if adv:
        L += [f"## Advisory ({len(adv)})", "",
              "Optional. These items never block a pass.", "",
              "| Id | Check | Item | Where | Suggestion |",
              "|---|---|---|---|---|"]
        L += [f"| `{f.id}` | {f.check} | {_cell(f.title)} | `{f.where}` | "
              f"{_cell(f.fix)} |" for f in adv]
        L.append("")

    state = {"passing": passing, "date": meta["date"],
             "commit": meta.get("commit", ""), "open": open_ids}
    L.append(f"<!-- explorer-checks:state {json.dumps(state)} -->")
    return "\n".join(line for line in L if line is not None) + "\n", passing


def _cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")[:300]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("findings")
    ap.add_argument("--review")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    meta, findings = read_findings(args.findings)
    review = load_review(args.review)
    out = pathlib.Path(args.out)
    prev = previous_open(out)
    findings, cleared = apply_review(findings, review)
    text, passing = render(meta, findings, cleared, review, prev)
    out.write_text(text, encoding="utf-8", newline="\n")
    print(f"{'PASSING' if passing else 'NOT PASSING'}: {out}")


if __name__ == "__main__":
    main()
