"""Run every automated check against one explorer checkout.

    python run_checks.py <repo> [--base-url URL] [--page PATH ...]
                                [--live-url URL] [--out-dir DIR]

Writes <out-dir>/findings.json and prints a summary. The default out-dir is
a folder per repository under the system temp directory, so nothing is
written into the explorer until the report is rendered there on purpose.

This is the automated half. The other half is Claude's review, written as
review.json; render_report.py combines the two.
"""

import argparse
import datetime
import pathlib
import subprocess
import sys
import tempfile

from common import CHECKS, Finding, make_id, read_findings, write_findings

HERE = pathlib.Path(__file__).resolve().parent
VERSION_FILE = HERE.parent / "VERSION"


def git(root, *args):
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return r.stdout.strip()


def run_part(name, script, root, out, extra):
    """Run one checker. A checker that crashes becomes a finding, so a broken
    tool can never read as a clean result."""
    r = subprocess.run([sys.executable, str(HERE / script), str(root),
                        "--out", str(out), *extra],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    print((r.stdout or "").strip())
    if r.returncode != 0 or not out.exists():
        check = "accessibility" if name == "browser" else name
        return {}, [Finding(
            check, "review", f"tool:{name}-crashed",
            f"The {name} checker did not finish, so this check is incomplete",
            evidence=(r.stderr or "").strip()[-600:],
            fix="Fix the cause (often a missing package: pip install -r "
                "requirements.txt, then python -m playwright install "
                "chromium) and re-run.",
            source="explorer-checks")]
    return read_findings(out)


def distinct(findings):
    """Same id and same place is one problem reported twice (a parse error
    recovered from twice on one line): keep one. Same id in two places is two
    identical lines in one file: number the later ones so both survive."""
    seen, out = {}, []
    for f in findings:
        if f.id not in seen:
            seen[f.id] = [f.where]
        elif f.where in seen[f.id]:
            continue
        else:
            seen[f.id].append(f.where)
            f.key = f"{f.key}#{len(seen[f.id])}"
            f.id = make_id(f.check, f.rule, f.where, f.key)
        out.append(f)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--base-url")
    ap.add_argument("--page", action="append", default=[])
    ap.add_argument("--live-url")
    ap.add_argument("--out-dir")
    args = ap.parse_args()

    root = pathlib.Path(args.repo).resolve()
    out_dir = pathlib.Path(args.out_dir or pathlib.Path(
        tempfile.gettempdir()) / "explorer-checks" / root.name)
    out_dir.mkdir(parents=True, exist_ok=True)

    browser_args = []
    if args.base_url:
        browser_args += ["--base-url", args.base_url]
    for p in args.page:
        browser_args += ["--page", p]
    security_args = ["--live-url", args.live_url] if args.live_url else []

    findings, pages, axe = [], [], ""
    for name, script, extra in [
            ("validity", "check_validity.py", []),
            ("security", "check_security.py", security_args),
            ("browser", "check_browser.py", browser_args)]:
        meta, found = run_part(name, script, root,
                               out_dir / f"{name}.json", extra)
        findings += found
        if name == "browser":
            pages, axe = meta.get("pages", []), meta.get("axe", "")

    remote = git(root, "remote", "get-url", "origin") or \
        git(root, "remote", "get-url", "canada")
    meta = {
        "repo": remote.removesuffix(".git") or root.name,
        "commit": git(root, "rev-parse", "HEAD"),
        "branch": git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(git(root, "status", "--porcelain")),
        "date": datetime.date.today().isoformat(),
        "pages": pages,
        "served": args.base_url or "repository root, served locally",
        "live_url": args.live_url or "",
        "axe": axe,
        "skill_version": VERSION_FILE.read_text(encoding="utf-8").strip()
                         if VERSION_FILE.exists() else "unversioned",
    }
    findings = distinct(findings)
    path = out_dir / "findings.json"
    write_findings(path, findings, meta)

    print(f"\nfindings: {path}")
    print(f"pages checked: {', '.join(pages) or '(none)'}")
    print(f"{'check':<14}{'fail':>6}{'review':>8}{'advisory':>10}")
    for check in CHECKS:
        n = {s: sum(1 for f in findings if f.check == check and f.status == s)
             for s in ("fail", "review", "advisory")}
        print(f"{check:<14}{n['fail']:>6}{n['review']:>8}{n['advisory']:>10}")


if __name__ == "__main__":
    main()
