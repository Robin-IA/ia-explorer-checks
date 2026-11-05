"""Front-end JavaScript libraries with known vulnerabilities.

pip-audit sees Python and npm audit sees package.json, but a static explorer
usually has neither: it loads DOMPurify or Highcharts from a CDN, or keeps a
copy of jquery.min.js in the repository. Pinning an exact version does not
help if that version is vulnerable, so each library is looked up:

- CDN URLs that name an npm package and version (jsDelivr, unpkg, cdnjs)
  are queried against OSV. A version range (d3@7) cannot be looked up, and
  the file behind it can change, so it is reported as such.
- Files in the repository, and CDN URLs OSV cannot name, are matched against
  Retire.js's repository of library signatures.

A lookup that fails is reported as a finding, never skipped quietly.
"""

import datetime
import json
import pathlib
import re
import tempfile
import urllib.request

from common import Finding, line_of, read_text, rel, repo_files

OSV_URL = "https://api.osv.dev/v1/query"
RETIRE_URL = ("https://raw.githubusercontent.com/RetireJS/retire.js/master/"
              "repository/jsrepository.json")

SCAN_SUFFIXES = {".html", ".htm", ".js", ".mjs"}
# Version banners sit near the top of a library; some of Retire's patterns
# use .* across a minified line, so very large files are cut short.
MAX_CONTENT = 512 * 1024

PKG = r"((?:@[\w.-]+/)?[\w.-]+)"
VER = r"([^/\"'`\s?#)]+)"
CDN = [
    re.compile(r"cdn\.jsdelivr\.net/npm/" + PKG + "@" + VER),
    re.compile(r"unpkg\.com/" + PKG + "@" + VER),
    re.compile(r"cdnjs\.cloudflare\.com/ajax/libs/([\w.-]+)/" + VER + "/"),
]
URL = re.compile(r"""(?:https?:)?//[^\s"'`<>()]+""")
SCRIPT = re.compile(r"\.m?js$")
EXACT = re.compile(r"^\d+\.\d+\.\d+(?:[-+][\w.-]+)?$")
RETIRE_VERSION = r"[0-9][0-9.a-z_\-]+"


def cdn_refs(root):
    """(package, version, url, where) for each remote script the code names.
    Package and version are None when the URL is not a CDN that names them."""
    refs = []
    for path in repo_files(root, SCAN_SUFFIXES):
        text = read_text(path) or ""
        for m in URL.finditer(text):
            url = m.group(0)
            where = f"{rel(root, path)}:{line_of(text, m.start())}"
            c = next(filter(None, (rx.search(url) for rx in CDN)), None)
            if c:
                refs.append((c.group(1).lower(), c.group(2), url, where))
            elif SCRIPT.search(url.split("?")[0]):
                refs.append((None, None, url, where))
    return refs


def osv_query(package, version):
    body = json.dumps({"package": {"name": package, "ecosystem": "npm"},
                       "version": version}).encode()
    req = urllib.request.Request(OSV_URL, data=body,
                                 headers={"Content-Type": "application/json"})
    # B310 is urlopen with an open scheme; fixed https URL.
    with urllib.request.urlopen(req, timeout=30) as r:  # nosec B310
        return json.load(r).get("vulns", [])


def retire_repository():
    cache = pathlib.Path(tempfile.gettempdir()) / "explorer-checks"
    cache.mkdir(exist_ok=True)
    path = cache / f"retire-{datetime.date.today().isoformat()}.json"
    if not path.exists():
        with urllib.request.urlopen(RETIRE_URL, timeout=60) as r:  # nosec B310
            path.write_bytes(r.read())
    return json.loads(path.read_text(encoding="utf-8"))


def _patterns(entry, kind):
    out = []
    for p in entry.get("extractors", {}).get(kind, []):
        try:
            out.append(re.compile(p.replace("§§version§§", RETIRE_VERSION)))
        except re.error:
            pass  # JavaScript-only syntax; the other patterns still run
    return out


def _version_key(v):
    parts = []
    for tok in re.split(r"[.\-+_]", v):
        # A number sorts above a pre-release word: 3.0.0 > 3.0.0-beta.
        parts.append((1, int(tok), "") if tok.isdigit() else (0, 0, tok))
    return parts


def _affected(version, vuln):
    v = _version_key(version)
    if "below" in vuln and not v < _version_key(vuln["below"]):
        return False
    if "atOrAbove" in vuln and v < _version_key(vuln["atOrAbove"]):
        return False
    if "above" in vuln and not v > _version_key(vuln["above"]):
        return False
    return True


def retire_match(repo, kind, subject):
    """(library, version) pairs that Retire's `kind` patterns find."""
    hits = []
    for name, entry in repo.items():
        if not isinstance(entry, dict) or name == "retire-example":
            continue
        for rx in _patterns(entry, kind):
            m = rx.search(subject)
            if m and m.groups():
                # The version pattern is greedy, so jquery-3.4.1.min.js
                # reads as 3.4.1.min.
                version = re.sub(r"[.-]min$", "", m.group(1))
                hits.append((entry.get("npmname") or name, version))
                break
    return hits


def retire_vulns(repo, library):
    for name, entry in repo.items():
        if isinstance(entry, dict) and \
                library in (name, entry.get("npmname")):
            return entry.get("vulnerabilities", [])
    return []


def _fixed(osv_vuln):
    for aff in osv_vuln.get("affected", []):
        for rng in aff.get("ranges", []):
            for ev in rng.get("events", []):
                if "fixed" in ev:
                    return ev["fixed"]
    return None


def _finding(lib, version, vid, summary, severity, fixed, where, source):
    return Finding(
        "security", "fail" if fixed else "review", f"dep:{vid}",
        f"{lib} {version} has {vid}", where=where, key=f"{lib}@{version}",
        evidence=f"{severity or 'unrated'}: {summary or ''}"[:200],
        fix=(f"Upgrade {lib} to {fixed} or later, and update the integrity "
             f"hash if the page has one." if fixed else
             f"No fixed version yet. Check whether the explorer uses the "
             f"affected feature; if it does, replace {lib} or disable it."),
        source=source)


def check_js_libraries(root, findings, osv=osv_query, repo=None):
    root = pathlib.Path(root)
    new, failed = [], set()
    if repo is None:
        try:
            repo = retire_repository()
        except (OSError, ValueError) as e:
            repo = {}
            failed.add(("retire", str(e)))

    for pkg, ver, url, where in cdn_refs(root):
        if pkg and not EXACT.match(ver):
            new.append(Finding(
                "security", "advisory", "supply:js-version-range",
                f"{pkg}@{ver} is a version range, so it was not checked",
                where=where, key=f"{pkg}@{ver}", evidence=url,
                fix=f"Pin an exact version ({pkg}@x.y.z) with an integrity "
                    f"hash. A range serves whatever is newest, and cannot be "
                    f"checked against advisories.",
                source="explorer-checks"))
            continue
        if pkg:
            try:
                vulns = osv(pkg, ver)
            except (OSError, ValueError) as e:
                failed.add(("osv", str(e)))
                continue
            for v in vulns:
                new.append(_finding(
                    pkg, ver, v["id"], v.get("summary"),
                    v.get("database_specific", {}).get("severity"),
                    _fixed(v), where, "osv"))
            continue
        name = url.split("?")[0].rstrip("/").rsplit("/", 1)[-1]
        hits = retire_match(repo, "uri", url) or             retire_match(repo, "filename", name)
        for lib, version in hits:
            new.extend(_retire_findings(repo, lib, version, where))

    for path in repo_files(root, {".js", ".mjs"}):
        where = rel(root, path)
        hits = retire_match(repo, "filename", path.name)
        if not hits:
            text = read_text(path)
            if text:
                hits = retire_match(repo, "filecontent", text[:MAX_CONTENT])
        for lib, version in hits:
            new.extend(_retire_findings(repo, lib, version, where))

    for tool, err in sorted(failed):
        name = {"osv": "OSV", "retire": "the Retire.js repository"}[tool]
        new.append(Finding(
            "security", "review", f"tool:{tool}",
            f"Could not reach {name}, so some JavaScript libraries were "
            f"not checked", evidence=err[:200],
            fix="Re-run with network access. Until then, check the "
                "libraries' versions against github.com/advisories by hand.",
            source="explorer-checks"))

    seen = set()
    for f in new:  # the same library twice in one file is one finding
        if f.id not in seen:
            seen.add(f.id)
            findings.append(f)


def _retire_findings(repo, lib, version, where):
    out = []
    for v in retire_vulns(repo, lib):
        if not _affected(version, v):
            continue
        ids = v.get("identifiers", {})
        vid = ids.get("githubID") or (ids.get("CVE") or [None])[0]
        if not vid:
            continue
        out.append(_finding(lib, version, vid, ids.get("summary"),
                            v.get("severity"), v.get("below"), where,
                            "retire.js"))
    return out
