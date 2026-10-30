"""Code validity, static half: does the code parse, and do its links resolve.

The browser half — runtime errors, failed requests, JavaScript that does not
compile — runs in check_browser.py, because only a loaded page shows them.

    python check_validity.py <repo> --out validity.json
"""

import argparse
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse

import html5lib

from common import (Finding, line_of, read_text, rel, repo_files,
                    source_line, write_findings)

# ruff rules that mean the code cannot run as written: syntax errors,
# undefined names, invalid comparisons. Everything else ruff reports by
# default is style or tidiness, which is advisory.
RUFF_BLOCKING = ("E9", "F63", "F7", "F82")

# html5lib reports these on pages that browsers and validators both accept,
# or on conventions an explorer has no reason to change.
HTML_NOISE = {"unexpected-character-after-solidus-in-tag",
              # a bare & in a URL query (?a=1&family=x); the W3C validator
              # accepts it, since no named entity starts "&family"
              "expected-named-entity"}

# Specific fixes for the parse errors explorers actually have; anything else
# gets the general advice.
HTML_FIXES = {
    "expected-doctype-but-got-start-tag":
        "Add <!doctype html> as the very first line. Without it the page "
        "renders in quirks mode, which changes layout and box sizing.",
    "expected-doctype-but-got-chars":
        "Add <!doctype html> as the very first line, before any text.",
    "end-tag-too-early":
        "An element is closed before its children; close them in order.",
}
HTML_FIX = ("Correct the markup so it parses without recovery; browsers "
            "repair it silently, but differently, and assistive technology "
            "reads the repaired tree.")

LOCAL_REF = re.compile(r'''\b(?:href|src)\s*=\s*["']([^"'#?]+)''', re.I)
ID_ATTR = re.compile(r'''\bid\s*=\s*["']([^"']+)["']''', re.I)


def check_html(root, findings):
    for path in repo_files(root, {".html", ".htm"}):
        text = read_text(path)
        if text is None:
            continue
        where = rel(root, path)
        if "{%" in text or "{{" in text:
            # A Jinja template is not HTML until it is rendered; the browser
            # pass checks it as served.
            continue
        parser = html5lib.HTMLParser(strict=False)
        parser.parse(text)
        for (line, col), code, data in parser.errors:
            if code in HTML_NOISE:
                continue
            findings.append(Finding(
                "validity", "fail", f"html:{code}",
                f"HTML parse error: {code.replace('-', ' ')}",
                where=f"{where}:{line}",
                evidence=_line(text, line),
                fix=HTML_FIXES.get(code, HTML_FIX),
                source="html5lib"))
        seen = {}
        for m in ID_ATTR.finditer(text):
            ident = m.group(1)
            if ident in seen:
                findings.append(Finding(
                    "validity", "fail", "html:duplicate-id",
                    f"Duplicate id \"{ident}\"",
                    where=f"{where}:{line_of(text, m.start())}",
                    evidence=f"first used on line {seen[ident]}", key=ident,
                    fix="Make every id unique on the page; labels, "
                        "aria-describedby and in-page links resolve to the "
                        "first match only.",
                    source="explorer-checks"))
            else:
                seen[ident] = line_of(text, m.start())
        check_local_refs(root, path, text, findings)


def check_local_refs(root, path, text, findings):
    """A relative href or src that names a file not in the repo."""
    for m in LOCAL_REF.finditer(text):
        ref = m.group(1).strip()
        if not ref or re.match(r"^[a-z][a-z0-9+.-]*:|^//|^\$|^\{", ref, re.I):
            continue
        target = (pathlib.Path(root) / ref.lstrip("/") if ref.startswith("/")
                  else path.parent / urllib.parse.unquote(ref))
        if target.exists() or (target / "index.html").exists():
            continue
        findings.append(Finding(
            "validity", "fail", "link:missing-local",
            f"Link to a file that is not in the repository: {ref}",
            where=f"{rel(root, path)}:{line_of(text, m.start())}", key=ref,
            fix="Point the link at a file that exists, or add the file. If "
                "it is generated at build time, say so in the README and "
                "re-run with the build output present.",
            source="explorer-checks"))


def check_json(root, findings):
    for path in repo_files(root, {".json"}):
        text = read_text(path)
        if text is None:
            continue
        try:
            json.loads(text)
        except json.JSONDecodeError as e:
            findings.append(Finding(
                "validity", "fail", "json:parse",
                "JSON file does not parse",
                where=f"{rel(root, path)}:{e.lineno}", evidence=e.msg,
                fix="Correct the JSON; a page that fetches it will fail "
                    "at runtime.",
                source="json"))


def check_python(root, findings):
    if not repo_files(root, {".py"}):
        return
    if not _module("ruff"):
        findings.append(Finding(
            "validity", "review", "tool:ruff-missing",
            "ruff is not installed, so Python was not linted",
            fix="pip install ruff, then re-run.", source="explorer-checks"))
        return
    cmd = [sys.executable, "-m", "ruff", "check", "--output-format=json",
           "--no-cache", "--exit-zero", "--select", "E4,E7,E9,F", str(root)]
    out = subprocess.run(cmd, capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stdout
    for item in json.loads(out or "[]"):
        code = item.get("code") or "E999"
        blocking = code.startswith(RUFF_BLOCKING)
        findings.append(Finding(
            "validity", "fail" if blocking else "advisory", f"ruff:{code}",
            item["message"],
            where=f"{rel(root, item['filename'])}:{item['location']['row']}",
            evidence=source_line(item["filename"], item["location"]["row"]),
            fix=(item.get("fix") or {}).get("message") or
                "See https://docs.astral.sh/ruff/rules/ for this rule.",
            source="ruff"))


def check_tests(root, findings):
    """Run the project's own tests, if it has any. Failing tests fail."""
    tests = pathlib.Path(root) / "tests"
    if not tests.is_dir() or not _module("pytest"):
        return
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x",
                        "--no-header", "-p", "no:cacheprovider", str(tests)],
                       cwd=root, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600)
    # 5 is "no tests collected", which is not a failure of the code.
    if r.returncode not in (0, 5):
        tail = "\n".join(r.stdout.strip().splitlines()[-15:])
        findings.append(Finding(
            "validity", "fail", "tests:pytest",
            "The project's own tests fail", where="tests/", evidence=tail,
            fix="Fix the code or the test; read the failure before choosing "
                "which.",
            source="pytest"))


def _line(text, n):
    lines = text.splitlines()
    return lines[n - 1].strip()[:200] if 0 < n <= len(lines) else ""


def _module(name):
    import importlib.util
    return importlib.util.find_spec(name) is not None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    root = pathlib.Path(args.repo).resolve()
    findings = []
    check_html(root, findings)
    check_json(root, findings)
    check_python(root, findings)
    check_tests(root, findings)
    write_findings(args.out, findings, {"check": "validity-static"})
    print(f"validity (static): {len(findings)} finding(s)")


if __name__ == "__main__":
    main()
