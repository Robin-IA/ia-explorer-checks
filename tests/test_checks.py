"""The checks find what they should, and the report and note behave.

Fixtures are written into tmp_path, not committed, because a committed
fake credential trips GitHub's secret scanning on push.
"""

import json
import pathlib
import subprocess
import sys

import pytest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "skills" / \
    "explorer-checks" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from add_page_note import BLOCK  # noqa: E402
from common import Finding, read_findings, write_findings  # noqa: E402

BAD_PAGE = """<title>Bad</title>
<div id="x"></div><div id="x"></div>
<a href="missing.html">gone</a>
<script>
document.getElementById("x").innerHTML = data.title;
</script>
"""

GOOD_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Good</title></head>
<body><main><h1>Good</h1><p>Fine.</p></main>
<footer><p>Footer</p></footer></body></html>
"""


def run(script, *args):
    r = subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r


@pytest.fixture
def site(tmp_path):
    root = tmp_path / "site"
    root.mkdir()
    (root / "bad.html").write_text(BAD_PAGE, encoding="utf-8")
    (root / "good.html").write_text(GOOD_PAGE, encoding="utf-8")
    (root / "config.js").write_text(
        'const awsKey = "AKIA' + "Q" * 16 + '";\n', encoding="utf-8")
    return root


def rules(path):
    return {f.rule for f in read_findings(path)[1]}


def test_validity_finds_markup_faults(site, tmp_path):
    out = tmp_path / "v.json"
    run("check_validity.py", site, "--out", out)
    found = rules(out)
    assert "html:expected-doctype-but-got-start-tag" in found
    assert "html:duplicate-id" in found
    assert "link:missing-local" in found


def test_security_finds_secret_and_sink(site, tmp_path):
    out = tmp_path / "s.json"
    run("check_security.py", site, "--out", out)
    found = {(f.rule, f.status) for f in read_findings(out)[1]}
    assert ("secret:aws-access-key", "fail") in found
    assert ("dom:innerHTML", "review") in found


def test_ids_are_stable_and_distinct():
    a = Finding("security", "review", "dom:innerHTML", "t", where="a.js:3",
                evidence="el.innerHTML = x")
    moved = Finding("security", "review", "dom:innerHTML", "t",
                    where="a.js:9", evidence="el.innerHTML = x")
    other = Finding("security", "review", "dom:innerHTML", "t",
                    where="a.js:3", evidence="el.innerHTML = y")
    assert a.id == moved.id != other.id
    assert a.id.startswith("S-")


def test_id_survives_lines_added_above(site, tmp_path):
    """Fixing one thing (adding a doctype) must not make every finding below
    it look new; the review's resolutions are keyed on these ids."""
    def sink_ids():
        out = tmp_path / "s.json"
        run("check_security.py", site, "--out", out)
        return {f.id for f in read_findings(out)[1] if f.rule == "dom:innerHTML"}
    before = sink_ids()
    page = site / "bad.html"
    page.write_text("<!doctype html>\n<html lang=\"en\">\n" +
                    page.read_text(encoding="utf-8"), encoding="utf-8")
    assert sink_ids() == before


def write_run(tmp_path, findings):
    meta = {"repo": "x/y", "commit": "abc1234567", "branch": "explorer-checks",
            "date": "2026-10-30", "pages": ["index.html"], "axe": "4.10.3"}
    path = tmp_path / "findings.json"
    write_findings(path, findings, meta)
    return path


MANUAL = {"security": [{"item": "No secrets", "result": "pass"}],
          "accessibility": [{"item": "2.1.1 Keyboard", "result": "pass"}]}


def render(tmp_path, findings, review, report):
    f = write_run(tmp_path, findings)
    r = tmp_path / "review.json"
    r.write_text(json.dumps(review), encoding="utf-8")
    run("render_report.py", f, "--review", r, "--out", report)
    return report.read_text(encoding="utf-8")


def test_report_lifecycle(tmp_path):
    report = tmp_path / "security-accessibility-checks.md"
    sink = Finding("security", "review", "dom:innerHTML", "sink",
                   where="index.html:9")
    lang = Finding("accessibility", "fail", "axe:html-has-lang", "no lang",
                   where="/ html-has-lang", wcag="3.1.1")

    text = render(tmp_path, [sink, lang], {"manual": MANUAL}, report)
    assert "Status: not passing" in text
    assert sink.id in text and lang.id in text

    # Second run: lang fixed, sink cleared on review.
    review = {"manual": MANUAL, "resolutions": {
        sink.id: {"verdict": "cleared", "reason": "literals only"}}}
    text = render(tmp_path, [sink], review, report)
    assert "Status: passing" in text
    assert "Fixed since the last run" in text and lang.id in text
    assert "literals only" in text


def test_no_manual_review_no_pass(tmp_path):
    text = render(tmp_path, [], {}, tmp_path / "r.md")
    assert "Status: not passing" in text
    assert "manual review not done" in text


def test_note_only_when_passing(tmp_path):
    page = tmp_path / "index.html"
    page.write_text(GOOD_PAGE, encoding="utf-8")
    report = tmp_path / "r.md"
    url = "https://github.com/x/y/blob/main/security-accessibility-checks.md"

    render(tmp_path, [Finding("validity", "fail", "r", "t")], {"manual": MANUAL},
           report)
    r = subprocess.run([sys.executable, str(SCRIPTS / "add_page_note.py"),
                        str(page), "--report", str(report),
                        "--report-url", url], capture_output=True, text=True)
    assert r.returncode != 0 and "not adding" in r.stderr

    render(tmp_path, [], {"manual": MANUAL}, report)
    for _ in range(2):  # re-running replaces, never duplicates
        run("add_page_note.py", page, "--report", report, "--report-url", url)
    text = page.read_text(encoding="utf-8")
    assert len(BLOCK.findall(text)) == 1
    assert text.index("explorer-checks:note") < text.index("</footer>")
    assert "30 October 2026" in text

    run("add_page_note.py", page, "--remove")
    assert "explorer-checks" not in page.read_text(encoding="utf-8")
