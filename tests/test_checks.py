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


def test_security_findings_name_owasp(site, tmp_path):
    out = tmp_path / "s.json"
    run("check_security.py", site, "--out", out)
    tags = {f.rule: f.owasp for f in read_findings(out)[1]}
    assert tags["secret:aws-access-key"] == "A07:2025 · ASVS V13"
    assert tags["dom:innerHTML"] == "A05:2025 · ASVS V1"


def test_supply_chain_and_flask_secret(site, tmp_path):
    (site / "requirements.txt").write_text(
        "flask==3.0.3\nrequests>=2\n# a comment\nhtml5lib\n-r other.txt\n",
        encoding="utf-8")
    wf = site / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "ci.yml").write_text(
        "jobs:\n  t:\n    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - uses: actions/setup-python@" + "a" * 40 + "\n"
        "      - uses: ./local-action\n", encoding="utf-8")
    (site / "app.py").write_text(
        'app.config["SECRET_KEY"] = "s3cr3t-value-123"\n', encoding="utf-8")
    from check_security import check_actions, check_pins, scan_text
    findings = []
    check_pins(site, findings)
    check_actions(site, findings)
    scan_text(site, findings)
    by_rule = {}
    for f in findings:
        by_rule.setdefault(f.rule, []).append(f)
    assert by_rule["supply:unpinned"][0].evidence == "requests, html5lib"
    assert [f.key for f in by_rule["supply:action-unpinned"]] == \
        ["actions/checkout@v4"]
    assert any("app.py" in f.where for f in by_rule["secret:named-literal"])


FAKE_RETIRE = {"jquery": {
    "npmname": "jquery",
    "extractors": {"filename": ["jquery-(§§version§§)(\\.min)?\\.js"],
                   "filecontent": ["/\\*!? jQuery v(§§version§§)"],
                   "func": ["jQuery.fn.jquery"]},
    "vulnerabilities": [{"atOrAbove": "1.2.0", "below": "3.5.0",
                         "severity": "medium",
                         "identifiers": {"summary": "XSS in htmlPrefilter",
                                         "githubID": "GHSA-gxr4-xjj5-5px2"}},
                        {"below": "1.9.0", "severity": "medium",
                         "identifiers": {"CVE": ["CVE-2012-6708"]}}]}}


def test_js_libraries(tmp_path):
    from js_libraries import check_js_libraries
    root = tmp_path / "site"
    (root / "js").mkdir(parents=True)
    cdn = "https://cdn.jsdelivr.net/npm/dompurify@3.4.16/dist/purify.min.js"
    (root / "index.html").write_text(
        f'<script src="{cdn}"></script>\n<script src="{cdn}"></script>\n'
        '<script src="https://unpkg.com/d3@7"></script>\n', encoding="utf-8")
    (root / "js" / "lib.js").write_text("/*! jQuery v3.4.1 | (c) */\n",
                                        encoding="utf-8")
    (root / "js" / "jquery-3.4.1.min.js").write_text("", encoding="utf-8")
    asked = []

    def osv(pkg, ver):
        asked.append((pkg, ver))
        return [{"id": "GHSA-cg2g-xh64-v4q7", "summary": "bypass",
                 "database_specific": {"severity": "CRITICAL"},
                 "affected": [{"ranges": [{"events": [
                     {"introduced": "3.4.4"}, {"fixed": "3.4.17"}]}]}]}]

    findings = []
    check_js_libraries(root, findings, osv=osv, repo=FAKE_RETIRE)
    got = {(f.rule, f.key, f.status) for f in findings}
    assert asked == [("dompurify", "3.4.16")] * 2
    assert ("dep:GHSA-cg2g-xh64-v4q7", "dompurify@3.4.16", "fail") in got
    assert ("supply:js-version-range", "d3@7", "advisory") in got
    assert ("dep:GHSA-gxr4-xjj5-5px2", "jquery@3.4.1", "fail") in got
    # 3.4.1 is not below 1.9.0; the same library twice in a file is one
    # finding; the filename's ".min" is not part of the version.
    assert not any(f.rule == "dep:CVE-2012-6708" for f in findings)
    assert sorted(f.where for f in findings if f.key == "jquery@3.4.1") == \
        ["js/jquery-3.4.1.min.js", "js/lib.js"]
    assert len(findings) == 4
    assert all(f.owasp == "A03:2025 · ASVS V15" for f in findings)


def test_js_library_lookup_failure_is_reported(tmp_path):
    from js_libraries import check_js_libraries
    root = tmp_path / "site"
    root.mkdir()
    (root / "index.html").write_text(
        '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">'
        '</script>', encoding="utf-8")

    def down(pkg, ver):
        raise OSError("no network")

    findings = []
    check_js_libraries(root, findings, osv=down, repo={})
    assert [f.rule for f in findings] == ["tool:osv"]


def test_meta_csp_found(site):
    from check_security import meta_csp_pages
    assert meta_csp_pages(site) == []
    (site / "good.html").write_text(GOOD_PAGE.replace(
        "<title>", '<meta http-equiv="Content-Security-Policy" '
        "content=\"default-src 'self'\"><title>"), encoding="utf-8")
    assert meta_csp_pages(site) == ["good.html"]


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
    assert "Fixed since the last run" in text
    assert f"- `{lang.id}` no lang" in text
    assert "literals only" in text


def test_fixed_list_survives_a_second_render(tmp_path):
    # The pass step renders, adds the note, re-runs and renders again before
    # committing. The second render must still compare with the committed one.
    repo = tmp_path / "explorer"
    repo.mkdir()
    git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True,
                                    capture_output=True)
    git("init", "-q")
    git("config", "user.email", "t@example.org")
    git("config", "user.name", "t")
    report = repo / "security-accessibility-checks.md"
    lang = Finding("accessibility", "fail", "axe:html-has-lang", "no lang",
                   where="/ html-has-lang", wcag="3.1.1")
    render(tmp_path, [lang], {"manual": MANUAL}, report)
    git("add", "-A")
    git("commit", "-qm", "report")
    render(tmp_path, [], {"manual": MANUAL}, report)
    text = render(tmp_path, [], {"manual": MANUAL}, report)
    assert "Status: passing" in text and f"- `{lang.id}` no lang" in text


def test_no_manual_review_no_pass(tmp_path):
    text = render(tmp_path, [], {}, tmp_path / "r.md")
    assert "Status: not passing" in text
    assert "manual review not done" in text


def test_note_only_when_passing(tmp_path):
    page = tmp_path / "index.html"
    page.write_text(GOOD_PAGE, encoding="utf-8")
    report = tmp_path / "r.md"

    render(tmp_path, [Finding("validity", "fail", "r", "t")], {"manual": MANUAL},
           report)
    r = subprocess.run([sys.executable, str(SCRIPTS / "add_page_note.py"),
                        str(page), "--report", str(report)],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "not adding" in r.stderr

    render(tmp_path, [], {"manual": MANUAL}, report)
    for _ in range(2):  # re-running replaces, never duplicates
        run("add_page_note.py", page, "--report", report)
    text = page.read_text(encoding="utf-8")
    assert len(BLOCK.findall(text)) == 1
    assert text.index("explorer-checks:note") < text.index("</footer>")
    assert "30 October 2026" in text
    assert "Meets WCAG 2.2 Level AA accessibility" in text
    assert "<a " not in BLOCK.search(text).group(0)  # the report is not linked
    note = BLOCK.search(text).group(0).lower()
    assert "security" not in note and "validity" not in note  # not published
    assert "## Standards met" in report.read_text(encoding="utf-8")

    run("add_page_note.py", page, "--remove")
    assert "explorer-checks" not in page.read_text(encoding="utf-8")


def test_note_on_page_without_footer_or_body(tmp_path):
    # HTML lets a page leave out </body>; the covid explorer does.
    page = tmp_path / "index.html"
    bare = "<!doctype html><html lang=en><title>t</title><main>m</main>\n<script></script>\n"
    page.write_text(bare, encoding="utf-8")
    report = tmp_path / "r.md"
    render(tmp_path, [], {"manual": MANUAL}, report)
    for _ in range(2):
        run("add_page_note.py", page, "--report", report)
    text = page.read_text(encoding="utf-8")
    assert len(BLOCK.findall(text)) == 1
    assert text.index("</main>") < text.index("<footer>") < text.index("<script>")

    run("add_page_note.py", page, "--remove")
    assert page.read_text(encoding="utf-8") == bare


def test_note_stays_where_the_owner_moved_it(tmp_path):
    page = tmp_path / "index.html"
    page.write_text(GOOD_PAGE, encoding="utf-8")
    report = tmp_path / "r.md"
    render(tmp_path, [], {"manual": MANUAL}, report)
    run("add_page_note.py", page, "--report", report)
    # The owner moves the block to the top of <main>, indented.
    text = page.read_text(encoding="utf-8")
    block = BLOCK.search(text).group(0)
    moved = "".join("    " + line for line in block.splitlines(True))
    page.write_text(BLOCK.sub("", text).replace("<main>", "<main>\n" + moved),
                    encoding="utf-8")
    before = page.read_text(encoding="utf-8")
    run("add_page_note.py", page, "--report", report)
    assert page.read_text(encoding="utf-8") == before


def test_note_at_top_and_moving_it(tmp_path):
    page = tmp_path / "index.html"
    page.write_text(GOOD_PAGE.replace("<body>", '<body><header>Site</header>'),
                    encoding="utf-8")
    report = tmp_path / "r.md"
    render(tmp_path, [], {"manual": MANUAL}, report)
    note = ("add_page_note.py", page, "--report", report)

    run(*note, "--position", "top")
    text = page.read_text(encoding="utf-8")
    assert text.index("<main>") < text.index("explorer-checks:note") < \
        text.index("<h1>")
    assert "margin:0 0 1em" in text

    run(*note)  # a re-run without --position leaves it at the top
    text = page.read_text(encoding="utf-8")
    assert len(BLOCK.findall(text)) == 1
    assert text.index("explorer-checks:note") < text.index("<h1>")
    assert "margin:0 0 1em" in text

    run(*note, "--position", "bottom")  # and --position moves it
    text = page.read_text(encoding="utf-8")
    assert len(BLOCK.findall(text)) == 1
    assert text.index("<footer>") < text.index("explorer-checks:note") < \
        text.index("</footer>")
    assert "margin:1em 0 0" in text


def test_note_at_top_without_main(tmp_path):
    page = tmp_path / "index.html"
    page.write_text("<!doctype html><html lang=en><title>t</title>"
                    "<body><h1>t</h1></body></html>\n", encoding="utf-8")
    report = tmp_path / "r.md"
    render(tmp_path, [], {"manual": MANUAL}, report)
    run("add_page_note.py", page, "--report", report, "--position", "top")
    text = page.read_text(encoding="utf-8")
    assert text.index("<body>") < text.index("<aside aria-label=") < \
        text.index("<h1>")
    run("add_page_note.py", page, "--remove")
    assert "aside" not in page.read_text(encoding="utf-8")


def test_note_is_small_but_never_below_10pt(tmp_path):
    page = tmp_path / "index.html"
    page.write_text(GOOD_PAGE, encoding="utf-8")
    report = tmp_path / "r.md"
    render(tmp_path, [], {"manual": MANUAL}, report)
    run("add_page_note.py", page, "--report", report, "--position", "top")
    # 0.8333rem is 10pt and 1rem 12pt at the default text size; rem, not px,
    # so it still grows when a reader enlarges text.
    assert "font-size:clamp(0.8333rem, 0.875em, 1rem)" in \
        page.read_text(encoding="utf-8")


def test_print_gives_the_snippet_and_where_without_changing_the_page(tmp_path):
    page = tmp_path / "index.html"
    page.write_text(GOOD_PAGE.replace("<body>", "<body><header>Site</header>"),
                    encoding="utf-8")
    before = page.read_text(encoding="utf-8")
    report = tmp_path / "r.md"
    render(tmp_path, [], {"manual": MANUAL}, report)
    note = ("add_page_note.py", page, "--report", report)

    out = run(*note, "--position", "top", "--print").stdout
    assert page.read_text(encoding="utf-8") == before
    assert "start of <main>" in out and "<main>" in out
    assert "<!-- explorer-checks:note -->" in out
    assert "<!-- /explorer-checks:note -->" in out
    assert "Keep the two marker comments" in out

    # What --print says to do is exactly what the script would do.
    line = int(out.split("as a new line ", 1)[1].split(",", 1)[0])
    run(*note, "--position", "top")
    after = page.read_text(encoding="utf-8").split("\n")
    assert after[line - 1] == "<!-- explorer-checks:note -->"

    # With a note already there, it says which lines to replace.
    out = run(*note, "--print").stdout
    assert out.startswith(f"Replace lines {line} to ")
