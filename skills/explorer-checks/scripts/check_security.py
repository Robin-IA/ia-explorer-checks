"""Code security: secrets, injection sinks, dependencies, Python patterns.

    python check_security.py <repo> --out security.json [--live-url URL]

An explorer's main risk is XSS. It renders text it did not write: archive.org
titles, Wayback page text, donor metadata. So every place the page turns a
string into markup is reported for review. The scanner cannot tell an
escaped string from a raw one, but Claude reading the code can.

Dependencies are audited whether they are Python (pip-audit), front-end
JavaScript loaded from a CDN or kept in the repository (js_libraries.py), or
GitHub Actions.
"""

import argparse
import json
import pathlib
import re
import subprocess
import sys
import urllib.request

from common import (Finding, line_of, read_text, rel, repo_files,
                    source_line, write_findings)
from js_libraries import check_js_libraries

TEXT_SUFFIXES = {".py", ".js", ".mjs", ".ts", ".html", ".htm", ".json",
                 ".yml", ".yaml", ".toml", ".cfg", ".ini", ".sh", ".md",
                 ".txt", ".env", ".conf"}

# Token formats with a recognisable shape. A match is treated as a real
# secret, because a false alarm costs a minute and a missed key does not.
SECRETS = [
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|"
                                r"github_pat_[A-Za-z0-9_]{60,})\b")),
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?"
                               r"PRIVATE KEY-----")),
    ("slack-token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("anthropic-key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("openai-key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{32,}\b")),
    # archive.org S3-style auth: "LOW accesskey:secret"
    ("ia-s3-auth", re.compile(r"\bLOW\s+[A-Za-z0-9]{12,}:[A-Za-z0-9]{12,}")),
]

# Assignment of a literal to something named like a credential. Weaker
# evidence, so it goes to review rather than straight to fail.
NAMED_SECRET = re.compile(
    # secret[_-]?key first: Flask's SECRET_KEY has no word boundary after
    # "secret", so the bare alternative never matched it. The optional
    # quote and bracket after the name catch app.config["SECRET_KEY"] = and
    # JSON's "password": forms.
    r"""(?i)\b[\w-]*(?:api[_-]?key|secret[_-]?key|secret|passwd|password|"""
    r"""access[_-]?token|"""
    r"""auth[_-]?token)\b["']?\]?\s*[:=]\s*["']([^"'\s]{8,})["']""")
PLACEHOLDER = re.compile(r"(?i)^(?:x+|\*+|changeme|example|your[_-]|<|\$\{|"
                         r"\{\{|os\.environ|process\.env|placeholder|dummy)")

# Places a string becomes markup or code in the browser.
SINKS = [
    ("dom:innerHTML", re.compile(r"\.(?:inner|outer)HTML\s*\+?=(?!=)")),
    ("dom:insertAdjacentHTML", re.compile(r"\.insertAdjacentHTML\s*\(")),
    ("dom:document.write", re.compile(r"\bdocument\.write(?:ln)?\s*\(")),
    ("dom:eval", re.compile(r"(?<![\w.])eval\s*\(|\bnew\s+Function\s*\(")),
    ("dom:string-timer", re.compile(r"\bset(?:Timeout|Interval)\s*\(\s*[\"'`]")),
    ("jquery:html", re.compile(r"\.html\s*\(\s*[^)\s]")),
    ("flask:markup", re.compile(r"\|\s*safe\b|\bMarkup\s*\(|autoescape\s+false")),
]

EXT_SCRIPT = re.compile(
    r"""<(script|link)\b[^>]*?\b(?:src|href)\s*=\s*["'](https?:)?//([^"']+)"""
    r"""["'][^>]*>""", re.I)
BLANK_TARGET = re.compile(r"""<a\b[^>]*target\s*=\s*["']_blank["'][^>]*>""",
                          re.I)


def scan_text(root, findings):
    for path in repo_files(root, TEXT_SUFFIXES):
        where_file = rel(root, path)
        if path.name == ".env" or path.suffix == ".env":
            findings.append(Finding(
                "security", "fail", "secret:env-file",
                f"Environment file committed: {where_file}", where=where_file,
                fix="Remove it from the repository and from history, rotate "
                    "anything it held, and add it to .gitignore.",
                source="explorer-checks"))
        text = read_text(path)
        if text is None:
            continue
        for rule, rx in SECRETS:
            for m in rx.finditer(text):
                findings.append(Finding(
                    "security", "fail", f"secret:{rule}",
                    f"Credential in source ({rule})",
                    where=f"{where_file}:{line_of(text, m.start())}",
                    evidence=_redact(m.group(0)),
                    fix="Revoke and rotate it now; it is in git history. "
                        "Then read it from the environment and purge the "
                        "history.",
                    source="explorer-checks"))
        if path.suffix != ".md":
            for m in NAMED_SECRET.finditer(text):
                if PLACEHOLDER.match(m.group(1)):
                    continue
                findings.append(Finding(
                    "security", "review", "secret:named-literal",
                    "Literal assigned to a credential-named variable",
                    where=f"{where_file}:{line_of(text, m.start())}",
                    evidence=_redact(m.group(0)),
                    fix="If it is a real credential, rotate it and load it "
                        "from the environment. If it is a placeholder or "
                        "public value, clear it with that reason.",
                    source="explorer-checks"))
        if path.suffix in {".js", ".mjs", ".ts", ".html", ".htm"}:
            scan_frontend(root, path, text, findings)


def scan_frontend(root, path, text, findings):
    where_file = rel(root, path)
    for rule, rx in SINKS:
        for m in rx.finditer(text):
            line = line_of(text, m.start())
            findings.append(Finding(
                "security", "review", rule,
                f"String rendered as markup or code ({rule.split(':')[1]})",
                where=f"{where_file}:{line}",
                evidence=text.splitlines()[line - 1].strip()[:200],
                fix="Trace what reaches this sink. If any part comes from "
                    "data (archive.org metadata, captured page text, the URL, "
                    "user input), escape it or build nodes with textContent. "
                    "Clear it only if every part is a literal or already "
                    "escaped, and name the escaping function.",
                source="explorer-checks"))
    if path.suffix not in {".html", ".htm"}:
        return
    for m in EXT_SCRIPT.finditer(text):
        tag, scheme, url = m.group(1).lower(), m.group(2), m.group(3)
        if tag == "link" and "stylesheet" not in m.group(0).lower():
            continue
        line = line_of(text, m.start())
        where = f"{where_file}:{line}"
        if scheme == "http:":
            findings.append(Finding(
                "security", "fail", "resource:http",
                f"{tag} loaded over plain http: {url}", where=where, key=url,
                fix="Load it over https; browsers block mixed content and a "
                    "network attacker can replace it.",
                source="explorer-checks"))
        elif "integrity=" not in m.group(0).lower() and \
                "fonts.googleapis.com" not in url:
            findings.append(Finding(
                "security", "advisory", "resource:no-sri",
                f"Third-party {tag} without integrity hash: {url}",
                where=where, key=url,
                fix="Pin an exact version and add integrity=\"sha384-...\" "
                    "crossorigin=\"anonymous\", or vendor the file into the "
                    "repository.",
                source="explorer-checks"))
    for m in BLANK_TARGET.finditer(text):
        if "noopener" not in m.group(0).lower() and \
                "noreferrer" not in m.group(0).lower():
            findings.append(Finding(
                "security", "advisory", "link:blank-no-noopener",
                "target=\"_blank\" without rel=\"noopener\"",
                where=f"{where_file}:{line_of(text, m.start())}",
                key=m.group(0)[:160],
                fix="Add rel=\"noopener\". Current browsers imply it, but "
                    "older ones give the opened page a handle on this one.",
                source="explorer-checks"))


def run_bandit(root, findings):
    if not any(root.rglob("*.py")):
        return
    r = subprocess.run([sys.executable, "-m", "bandit", "-r", str(root),
                        "-f", "json", "-q", "-x",
                        ",".join(str(root / d) for d in
                                 ("tests", ".git", ".venv", "venv",
                                  "node_modules"))],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if not r.stdout.strip():
        findings.append(Finding(
            "security", "review", "tool:bandit-missing",
            "bandit did not run, so Python was not scanned",
            evidence=r.stderr.strip()[:200],
            fix="pip install bandit, then re-run.", source="explorer-checks"))
        return
    # bandit's MEDIUM is mostly urlopen and subprocess, which every harvest
    # script uses on URLs it built itself, so it goes to review, not fail.
    status = {"HIGH": "fail", "MEDIUM": "review"}
    for item in json.loads(r.stdout).get("results", []):
        findings.append(Finding(
            "security", status.get(item["issue_severity"], "advisory"),
            f"bandit:{item['test_id']}", item["issue_text"],
            where=f"{rel(root, item['filename'])}:{item['line_number']}",
            evidence=item["code"].strip()[:200],
            key=source_line(item["filename"], item["line_number"]),
            fix=f"See {item['more_info']}. If the flagged input can never "
                f"come from outside (say why in the review), clear it.",
            source="bandit"))


def run_dependency_audit(root, findings):
    for req in sorted(root.glob("requirements*.txt")):
        r = subprocess.run([sys.executable, "-m", "pip_audit", "-r", str(req),
                            "-f", "json", "--progress-spinner", "off"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=600)
        try:
            deps = json.loads(r.stdout)["dependencies"]
        except (json.JSONDecodeError, KeyError):
            findings.append(Finding(
                "security", "review", "tool:pip-audit",
                f"pip-audit could not audit {req.name}",
                where=rel(root, req), evidence=r.stderr.strip()[-300:],
                fix="pip install pip-audit; if the file has unpinned or "
                    "private packages, audit the installed environment "
                    "instead.",
                source="pip-audit"))
            continue
        for dep in deps:
            for v in dep.get("vulns", []):
                fixed = ", ".join(v.get("fix_versions", [])) or "none yet"
                findings.append(Finding(
                    "security", "fail", f"dep:{v['id']}",
                    f"{dep['name']} {dep['version']} has {v['id']}",
                    where=rel(root, req),
                    evidence=(v.get("description") or "")[:200],
                    fix=f"Upgrade {dep['name']} to a fixed version "
                        f"({fixed}).",
                    source="pip-audit"))
    if (root / "package.json").exists():
        findings.append(Finding(
            "security", "review", "dep:npm-not-audited",
            "package.json present; npm dependencies were not audited",
            where="package.json",
            fix="Run `npm audit --omit=dev` and record the result in the "
                "review, or resolve as a finding.",
            source="explorer-checks"))


REQ_LINE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?\s*(.*)$")
USES = re.compile(r"""^\s*-?\s*uses:\s*["']?([^\s"'#]+)@([^\s"'#]+)""", re.M)
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def check_pins(root, findings):
    """Requirements without an exact version. pip-audit checks what it
    would install today, so an unpinned file passes the audit and then
    installs something else next month."""
    for req in sorted(root.glob("requirements*.txt")):
        loose = []
        for line in (read_text(req) or "").splitlines():
            line = line.split("#", 1)[0].strip()
            if not line or line.startswith("-") or "://" in line:
                continue
            m = REQ_LINE.match(line)
            if m and "==" not in m.group(3):
                loose.append(m.group(1))
        if loose:
            findings.append(Finding(
                "security", "advisory", "supply:unpinned",
                f"{len(loose)} requirement(s) without an exact version in "
                f"{req.name}", where=rel(root, req), key=req.name,
                evidence=", ".join(loose)[:300],
                fix="Pin each to the version tested (name==1.2.3), for "
                    "example from `pip freeze`, so the audit and the "
                    "deployment install the same thing.",
                source="explorer-checks"))


def check_actions(root, findings):
    """GitHub Actions referenced by a tag or branch, which the action's
    owner can move to different code."""
    for wf in sorted((root / ".github" / "workflows").glob("*.y*ml")):
        text = read_text(wf) or ""
        for m in USES.finditer(text):
            action, ref = m.group(1), m.group(2)
            if action.startswith(("./", "docker://")) or FULL_SHA.match(ref):
                continue
            findings.append(Finding(
                "security", "advisory", "supply:action-unpinned",
                f"Workflow uses {action}@{ref}, a movable reference",
                where=f"{rel(root, wf)}:{line_of(text, m.start())}",
                key=f"{action}@{ref}",
                fix=f"Pin to the full commit SHA of {ref}, with the tag in a "
                    f"comment: uses: {action}@<40-hex sha>  # {ref}",
                source="explorer-checks"))


GITHUB_REMOTE = re.compile(r"github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?/?$")


def check_pages(root, findings):
    """A private repository with GitHub Pages publishes the served folder to
    everyone on most plans, so code and notes meant to stay private go out
    with the site. Needs the gh CLI; without it the check is named as not
    done rather than passed."""
    remotes = subprocess.run(["git", "-C", str(root), "remote", "-v"],
                             capture_output=True, text=True).stdout
    repos = sorted({m.group(1, 2) for line in remotes.splitlines()
                    for m in [GITHUB_REMOTE.search(line.split()[1])
                              if len(line.split()) > 1 else None] if m})
    for owner, name in repos:
        try:
            r = subprocess.run(
                ["gh", "api", f"repos/{owner}/{name}", "-q",
                 '"\\(.private) \\(.has_pages)"'],
                capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired) as e:
            r = subprocess.CompletedProcess([], 1, "", str(e))
        if r.returncode != 0:
            findings.append(Finding(
                "security", "advisory", "pages:not-checked",
                f"Could not read {owner}/{name} from GitHub, so Pages "
                f"visibility was not checked", key=f"{owner}/{name}",
                evidence=(r.stderr or "").strip()[:200],
                fix="Install and log in to the gh CLI, then re-run.",
                source="explorer-checks"))
            continue
        private, pages = r.stdout.strip().split()
        if private == "true" and pages == "true":
            findings.append(Finding(
                "security", "review", "pages:private-repo-published",
                f"{owner}/{name} is private but serves a GitHub Pages site",
                key=f"{owner}/{name}",
                fix="Everything in the Pages folder is public. Either that "
                    "is intended (clear it, saying so), or serve from a "
                    "folder that holds only the site, or turn Pages off.",
                source="explorer-checks"))


META_CSP = re.compile(
    r"""<meta\b[^>]*http-equiv\s*=\s*["']?content-security-policy""", re.I)


def meta_csp_pages(root):
    """Pages in the checkout that set a CSP with <meta http-equiv>, the only
    way a static host such as GitHub Pages can set one."""
    return [rel(root, p) for p in repo_files(root, {".html", ".htm"})
            if META_CSP.search(read_text(p) or "")]


def check_headers(url, findings, root=None):
    """Response headers of the live site. Advisory: static hosts such as
    GitHub Pages cannot set most of them. A <meta> CSP in the checkout
    counts, because the checkout is what is being checked and the live
    site catches up when it is deployed."""
    if not url.startswith(("https://", "http://")):
        raise SystemExit(f"--live-url must be an http(s) URL, not {url!r}")
    try:
        req = urllib.request.Request(url, method="GET",
                                     headers={"User-Agent": "explorer-checks"})
        # B310 is urlopen with an open scheme; scheme checked above.
        with urllib.request.urlopen(req, timeout=30) as resp:  # nosec B310
            headers = {k.lower(): v for k, v in resp.headers.items()}
            final = resp.geturl()
    except Exception as e:
        findings.append(Finding(
            "security", "review", "live:unreachable",
            f"Live URL could not be fetched: {e}", where=url,
            fix="Check the URL; headers were not checked.",
            source="explorer-checks"))
        return
    if final.startswith("http:"):
        findings.append(Finding(
            "security", "fail", "live:no-https", "Live site served over http",
            where=final, fix="Serve over https and redirect http to it.",
            source="explorer-checks"))
    meta = meta_csp_pages(root) if root else []
    for header, why in [
            ("content-security-policy", "limits the damage of any XSS that "
             "gets through; a <meta http-equiv> CSP works on static hosts"),
            ("x-content-type-options", "stops browsers guessing content "
             "types. It has no <meta> form, so on a host that cannot set "
             "headers (GitHub Pages) it stays open; the explorer's owners "
             "decide whether that matters enough to change host")]:
        if header == "content-security-policy" and meta:
            continue
        if header not in headers:
            findings.append(Finding(
                "security", "advisory", f"live:no-{header}",
                f"No {header} header", where=final,
                fix=f"Set it; it {why}.", source="explorer-checks"))


def _redact(s):
    return s if len(s) <= 12 else s[:6] + "…" + s[-2:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--out", required=True)
    ap.add_argument("--live-url")
    args = ap.parse_args()
    root = pathlib.Path(args.repo).resolve()
    findings = []
    scan_text(root, findings)
    run_bandit(root, findings)
    run_dependency_audit(root, findings)
    check_js_libraries(root, findings)
    check_pins(root, findings)
    check_actions(root, findings)
    check_pages(root, findings)
    if args.live_url:
        check_headers(args.live_url, findings, root)
    write_findings(args.out, findings, {"check": "security"})
    print(f"security: {len(findings)} finding(s)")


if __name__ == "__main__":
    main()
