"""Combine the automated findings and Claude's review into the report.

    python render_report.py <findings.json> --review review.json
                            --out <explorer>/security-accessibility-checks.md

The report is one file at one path, passing or not, so a re-run replaces it
and the explorer's history shows the progress. Its last line is a comment
holding the open finding ids and titles. The next run reads it to list
what was fixed in between. "The last run" is the report as last committed,
not the file on disk, so rendering twice before a commit (as the pass step
does, after adding the page note) does not lose the list.

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
import datetime
import json
import pathlib
import re
import subprocess

from common import CHECKS, Finding, read_findings

STATE = re.compile(r"<!-- explorer-checks:state (\{.*\}) -->")
HEADING = re.compile(r"^### `([A-Z]-[0-9a-f]+(?:-\d+)?)` (.+)$", re.M)
NAMES = {"validity": "Code validity", "security": "Code security",
         "accessibility": "Accessibility (WCAG 2.2 AA)"}
NEEDS_MANUAL = {"security", "accessibility"}
STANDARD = "WCAG 2.2 Level AA"
# Met along with it, for the page note; the report says why.
ALSO_MET = "WCAG 2.1 AA and 2.0 AA"
SECURITY_REFS = "OWASP Top 10:2025 and ASVS 5.0.0"


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
    return _state(path.read_text(encoding="utf-8"))


def committed_open(path, ref="HEAD"):
    """The state of the report as committed at ref, else as on disk."""
    r = subprocess.run(["git", "-C", str(path.parent), "show",
                        f"{ref}:./{path.name}"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode == 0:
        return _state(r.stdout)
    return previous_open(path)


def _state(text):
    m = STATE.search(text)
    if not m:
        return None
    state = json.loads(m.group(1))
    # Reports from before titles were kept in the state still have them in
    # their headings.
    state.setdefault("titles", dict(HEADING.findall(text)))
    return state


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
    L += [f"| Standard | {STANDARD} |",
          f"| Security references | {SECURITY_REFS} |",
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
    if passing:
        L += ["", "## Standards met", "",
              f"Checked {_day(meta['date'])} at commit `{commit}`, on the "
              f"pages listed above:", "",
              f"- **{STANDARD}**: every Level A and AA success criterion, by "
              f"automated tests and a manual review of each criterion "
              f"(checklists under each check below).",
              "- **WCAG 2.1 Level AA** and **WCAG 2.0 Level AA**, which "
              "WCAG 2.2 includes. 4.1.1 Parsing, dropped from 2.2 but still "
              "in 2.0 and 2.1, is covered by the code validity check "
              "(no HTML parse errors, no duplicate ids).",
              "- These are the web content requirements of **Section 508** "
              "(US federal; WCAG 2.0 AA) and **EN 301 549** clause 9 "
              "(WCAG 2.1 AA).",
              "- Security was checked against the OWASP Top 10:2025 risks "
              "and ASVS 5.0.0 chapters that apply to an explorer; each "
              "finding and checklist item names its category. That is not an "
              "ASVS verification at any level."]
    L += ["", "## What a pass means", "",
          "Each check combines automated tools with a review of the code "
          "and pages against a written checklist. A pass means neither "
          "found anything open on the date and commit above. The standards "
          "are met as far as those checks can establish: it is a "
          "self-assessment, not third-party certification. Automated "
          "testing finds a minority of accessibility barriers. Testing with "
          "people who use assistive technology is still worth doing, and a "
          "change to the explorer needs a re-run.", ""]

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
                  (f" · WCAG {f.wcag}" if f.wcag else "") +
                  (f" · OWASP {f.owasp}" if f.owasp else ""),
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
        titles = prev.get("titles", {})
        L += ["## Fixed since the last run", ""]
        L += [f"- `{i}` {titles.get(i, '')}".rstrip() for i in fixed]
        L.append("")

    adv = [f for f in findings if f.status == "advisory"]
    if adv:
        L += [f"## Advisory ({len(adv)})", "",
              "Optional. These items never block a pass.", "",
              "| Id | Check | Item | Where | Reference | Suggestion |",
              "|---|---|---|---|---|---|"]
        L += [f"| `{f.id}` | {f.check} | {_cell(f.title)} | `{f.where}` | "
              f"{f.wcag and 'WCAG ' + f.wcag or f.owasp} | {_cell(f.fix)} |"
              for f in adv]
        L.append("")

    state = {"passing": passing, "date": meta["date"],
             "commit": meta.get("commit", ""), "open": open_ids,
             "titles": {f.id: f.title for f in findings if f.id in open_ids}}
    L.append(f"<!-- explorer-checks:state {json.dumps(state)} -->")
    return "\n".join(line for line in L if line is not None) + "\n", passing


def _day(iso):
    """A date in US English, "November 9, 2026", as the explorer best
    practices ask for everything an explorer publishes."""
    d = datetime.date.fromisoformat(iso)
    return f"{d:%B} {d.day}, {d.year}"


def _cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")[:300]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("findings")
    ap.add_argument("--review")
    ap.add_argument("--out", required=True)
    ap.add_argument("--since", default="HEAD",
                    help="commit whose report is 'the last run'")
    args = ap.parse_args()
    meta, findings = read_findings(args.findings)
    review = load_review(args.review)
    out = pathlib.Path(args.out)
    prev = committed_open(out, args.since)
    findings, cleared = apply_review(findings, review)
    text, passing = render(meta, findings, cleared, review, prev)
    out.write_text(text, encoding="utf-8", newline="\n")
    print(f"{'PASSING' if passing else 'NOT PASSING'}: {out}")


if __name__ == "__main__":
    main()
