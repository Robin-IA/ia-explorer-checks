"""Shared shape for every check: one Finding, one findings file.

A finding has a **status**, not a severity scale, because the report has to
answer one question per check — does it pass — and a scale invites arguing
about where the line is:

- `fail`     — must be fixed before the check passes.
- `review`   — a tool flagged it but cannot decide; Claude reads the code and
               resolves it to `fail` or `cleared` (with a reason) in
               review.json. An unresolved `review` blocks a pass.
- `advisory` — worth doing, never blocks a pass.

The id is derived from what was found and where, not from the run, so the
same problem keeps the same id across re-runs. That is what lets the report
say what was fixed since last time.
"""

import dataclasses
import hashlib
import json
import pathlib
import re

CHECKS = ("validity", "security", "accessibility")
STATUSES = ("fail", "review", "advisory")
PREFIX = {"validity": "V", "security": "S", "accessibility": "A"}

# Directories never worth scanning: VCS, dependencies, caches, and the
# virtualenvs people leave lying around inside a checkout.
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "env",
             ".pytest_cache", ".ruff_cache", ".mypy_cache", "dist", "build-out"}

# Text files larger than this are data, not code; reading them costs time and
# finds nothing a person would act on.
MAX_SCAN_BYTES = 5 * 1024 * 1024


@dataclasses.dataclass
class Finding:
    check: str
    status: str
    rule: str          # tool rule id, or a short slug for Claude's own findings
    title: str
    where: str = ""    # file:line, or page URL + selector
    evidence: str = ""
    fix: str = ""
    source: str = ""   # the tool that found it, or "review"
    wcag: str = ""     # success criteria, accessibility only
    key: str = ""      # tells apart findings sharing rule and place
    id: str = ""

    def __post_init__(self):
        if self.check not in CHECKS:
            raise ValueError(f"unknown check {self.check!r}")
        if self.status not in STATUSES:
            raise ValueError(f"unknown status {self.status!r}")
        if not self.key and LINE_NO.search(self.where):
            first = self.evidence.strip().splitlines()
            self.key = first[0] if first else self.title
        if not self.id:
            self.id = make_id(self.check, self.rule, self.where, self.key)


LINE_NO = re.compile(r":\d+$")


def make_id(check, rule, where, key=""):
    """The id leaves out the line number, since an edit higher up the file
    would change it, and uses the content of the flagged line instead
    (`key`, whitespace-normalized). A finding then keeps its id until its
    own line changes, which is when it should be looked at again."""
    place = LINE_NO.sub("", where)
    key = " ".join(key.split())
    digest = hashlib.sha1(f"{check}|{rule}|{place}|{key}".encode("utf-8"),
                          usedforsecurity=False)
    return f"{PREFIX[check]}-{digest.hexdigest()[:6]}"


def source_line(path, n):
    try:
        lines = pathlib.Path(path).read_text(encoding="utf-8",
                                             errors="replace").splitlines()
    except OSError:
        return ""
    return lines[n - 1].strip()[:200] if 0 < n <= len(lines) else ""


def write_findings(path, findings, meta):
    data = {"meta": meta,
            "findings": [dataclasses.asdict(f) for f in findings]}
    pathlib.Path(path).write_text(json.dumps(data, indent=2,
                                             ensure_ascii=False),
                                  encoding="utf-8")


def read_findings(path):
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    return data["meta"], [Finding(**f) for f in data["findings"]]


def repo_files(root, suffixes):
    """Every file under root with one of the suffixes, skipping SKIP_DIRS."""
    root = pathlib.Path(root)
    out = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in suffixes:
            continue
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        out.append(p)
    return out


def read_text(path):
    """File text, or None when it is too large or not text."""
    p = pathlib.Path(path)
    if p.stat().st_size > MAX_SCAN_BYTES:
        return None
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def line_of(text, offset):
    return text.count("\n", 0, offset) + 1


def rel(root, path):
    return pathlib.Path(path).relative_to(root).as_posix()
