"""The browser pass: load each page in headless Chromium and run axe-core.

    python check_browser.py <repo> --out browser.json
        [--base-url http://localhost:5000] [--page mockup/] [--page about/]

It writes two kinds of finding from one load per page:

- **accessibility**: axe-core against WCAG 2.0/2.1/2.2 A and AA, plus a
  320 px reflow check (1.4.10) and a focus-visibility check (2.4.7). Those
  two are the cheap ones axe does not do.
- **validity**: uncaught exceptions, console errors, failed requests, and
  JavaScript files that do not compile.

With no --base-url, the repository root is served on a free local port.
That is right for a static explorer, and it tests the checked-out branch, so
a re-run after fixes tests the fixes. An app (Flask and the like) has to be
started first, per its README, and its address passed as --base-url.
"""

import argparse
import functools
import http.server
import pathlib
import tempfile
import threading
import urllib.parse
import urllib.request

from playwright.sync_api import sync_playwright

from common import Finding, read_text, rel, repo_files, write_findings

AXE_VERSION = "4.10.3"
AXE_URL = f"https://cdn.jsdelivr.net/npm/axe-core@{AXE_VERSION}/axe.min.js"
AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa",
            "best-practice"]

# Pages are discovered from the repository's HTML, minus places that hold
# HTML that is not a page anyone visits.
NOT_PAGES = {"tests", "test", "templates", "fixtures", "docs", "examples"}
MAX_PAGES = 25

FOCUS_STEPS = 20


def axe_source():
    cache = pathlib.Path(tempfile.gettempdir()) / "explorer-checks"
    cache.mkdir(exist_ok=True)
    path = cache / f"axe-{AXE_VERSION}.min.js"
    if not path.exists():
        # B310 is urlopen with an open scheme; fixed https URL.
        with urllib.request.urlopen(AXE_URL, timeout=60) as r:  # nosec B310
            path.write_bytes(r.read())
    return path.read_text(encoding="utf-8")


def discover_pages(root):
    pages = []
    for path in repo_files(root, {".html", ".htm"}):
        parts = path.relative_to(root).parts
        if any(p in NOT_PAGES for p in parts[:-1]):
            continue
        text = read_text(path) or ""
        if "{%" in text or "<html" not in text.lower():
            continue  # a template or a fragment, not a page
        pages.append(rel(root, path))
    return pages


def serve(root):
    handler = functools.partial(_QuietHandler, directory=str(root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/"


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def check_page(context, url, axe, findings):
    # Findings name the path, never the full URL: a locally served page gets
    # a new port every run, and the port would change every finding's id.
    here = urllib.parse.urlsplit(url).path or "/"
    page = context.new_page()
    errors, failed = [], []
    page.on("pageerror", lambda e: errors.append(("exception", str(e))))
    page.on("console", lambda m: m.type == "error" and
            errors.append(("console", m.text)))
    page.on("requestfailed", lambda r: failed.append(
        (r.url, r.failure or "failed")))
    page.on("response", lambda r: r.status >= 400 and failed.append(
        (r.url, f"HTTP {r.status}")))
    try:
        page.goto(url, wait_until="networkidle", timeout=90_000)
    except Exception as e:
        findings.append(Finding(
            "validity", "fail", "page:load", f"Page did not load: {e}"[:200],
            where=here, fix="Make the page load; nothing else on it was "
            "checked.", source="playwright"))
        page.close()
        return
    page.wait_for_timeout(1000)

    origin = urllib.parse.urlsplit(url)[:2]
    base = "{}://{}".format(*origin)
    for kind, text in dict.fromkeys(errors):
        text = text.replace(base, "")
        findings.append(Finding(
            "validity", "fail", f"page:{kind}",
            f"JavaScript {kind} on load", where=here, evidence=text[:300],
            fix="Fix the error; it may leave part of the page unrendered "
                "for every visitor.",
            source="chromium", key=text[:120]))
    for req_url, why in dict.fromkeys(failed):
        own = urllib.parse.urlsplit(req_url)[:2] == origin
        shown = req_url.replace(base, "")
        findings.append(Finding(
            "validity", "fail" if own else "advisory", "page:request",
            f"Request failed ({why}): {shown}"[:200], where=here,
            key=shown,
            fix="Fix the path or ship the file." if own else
                "A third-party resource failed; check it is still served, "
                "or vendor it.",
            source="chromium"))

    page.add_script_tag(content=axe)
    run_axe(page, here, {"type": "tag", "values": AXE_TAGS}, "", findings)
    # A page with a dark theme is two pages as far as contrast goes, and
    # whichever the visitor's system prefers is the one they get. Only the
    # colour rules are re-run; nothing else changes with the scheme.
    if page.evaluate(HAS_DARK_JS):
        page.emulate_media(color_scheme="dark")
        run_axe(page, here, {"type": "rule", "values": DARK_RULES}, "dark",
                findings)
        page.emulate_media(color_scheme="light")

    check_focus(page, here, findings)
    page.close()

    narrow = context.new_page()
    narrow.set_viewport_size({"width": 320, "height": 640})
    narrow.goto(url, wait_until="networkidle", timeout=90_000)
    overflow = narrow.evaluate(
        "() => document.documentElement.scrollWidth - window.innerWidth")
    if overflow > 1:
        findings.append(Finding(
            "accessibility", "fail", "reflow:320",
            "Page scrolls sideways at 320 px wide", where=here,
            evidence=f"{overflow}px wider than the viewport",
            fix="Let content wrap at narrow widths: max-width:100% on media "
                "and tables in a scrolling container, no fixed widths over "
                "320px. Data tables may scroll inside their own container.",
            source="explorer-checks", wcag="1.4.10"))
    narrow.close()


DARK_RULES = ["color-contrast", "link-in-text-block"]
HAS_DARK_JS = """() => [...document.styleSheets].some(sheet => {
  try {
    return [...sheet.cssRules].some(r =>
      r.media && /prefers-color-scheme:\\s*dark/.test(r.media.mediaText));
  } catch (e) { return false }  // a cross-origin sheet (Google Fonts)
})"""


def run_axe(page, here, run_only, scheme, findings):
    result = page.evaluate(
        "o => axe.run(document, {runOnly: o, "
        "resultTypes: ['violations', 'incomplete']})", run_only)
    suffix = f" ({scheme} mode)" if scheme else ""
    for kind in ("violations", "incomplete"):
        for v in result[kind]:
            wcag = ", ".join(_criteria(v["tags"]))
            status = ("review" if kind == "incomplete"
                      else "fail" if wcag else "advisory")
            targets = [" ".join(map(str, n["target"])) for n in v["nodes"]]
            findings.append(Finding(
                "accessibility", status, f"axe:{v['id']}",
                v["help"] + suffix, where=f"{here} {v['id']}{suffix}",
                evidence=f"{len(targets)} element(s): " +
                         "; ".join(targets[:5]) +
                         (f"\n{v['nodes'][0].get('failureSummary', '')}"
                          if v["nodes"] else ""),
                fix=f"{v['description']} See {v['helpUrl']}",
                source=f"axe-core {AXE_VERSION}", wcag=wcag, key=kind))


FOCUS_JS = """() => {
  const el = document.activeElement;
  if (!el || el === document.body) return null;
  const pick = s => [s.outlineStyle, s.outlineWidth, s.outlineColor,
                     s.boxShadow, s.backgroundColor, s.borderColor,
                     s.textDecorationLine, s.color].join('|');
  const focused = pick(getComputedStyle(el));
  const label = el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') +
    ' "' + (el.innerText || el.value || el.getAttribute('aria-label') || '')
      .trim().slice(0, 40) + '"';
  el.blur();
  const plain = pick(getComputedStyle(el));
  el.focus();
  return {label, same: focused === plain};
}"""


def check_focus(page, here, findings):
    """Tab through the first elements and flag any whose style does not
    change when focused. A review item: the indicator may be drawn by a
    parent or a pseudo-element, which only a look can tell."""
    invisible = []
    for _ in range(FOCUS_STEPS):
        page.keyboard.press("Tab")
        state = page.evaluate(FOCUS_JS)
        if state and state["same"]:
            invisible.append(state["label"])
    if invisible:
        findings.append(Finding(
            "accessibility", "review", "focus:no-style-change",
            "Focused elements look the same as unfocused ones", where=here,
            evidence="; ".join(dict.fromkeys(invisible))[:400],
            fix="Look at each in a browser with the keyboard. If there is "
                "no visible indicator, add :focus-visible { outline: 2px "
                "solid; outline-offset: 2px } and never outline: none "
                "without a replacement.",
            source="explorer-checks", wcag="2.4.7"))


def check_js_syntax(context, root, findings):
    page = context.new_page()
    for path in repo_files(root, {".js"}):
        text = read_text(path)
        if text is None or "import " in text and "export " in text:
            continue  # ES modules do not compile as a function body
        err = page.evaluate(
            "src => { try { new Function(src); return null } "
            "catch (e) { return e.name + ': ' + e.message } }", text)
        if err and err.startswith("SyntaxError"):
            findings.append(Finding(
                "validity", "fail", "js:syntax",
                "JavaScript file does not compile", where=rel(root, path),
                evidence=err, fix="Fix the syntax error.",
                source="chromium"))
    page.close()


def _criteria(tags):
    """axe writes success criteria as tags like 'wcag143' -> '1.4.3'."""
    out = []
    for t in tags:
        digits = t[4:]
        if t.startswith("wcag") and digits.isdigit() and len(digits) >= 3:
            out.append(f"{digits[0]}.{digits[1]}.{digits[2:]}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--out", required=True)
    ap.add_argument("--base-url")
    ap.add_argument("--page", action="append", default=[],
                    help="path under the base URL; repeatable")
    args = ap.parse_args()
    root = pathlib.Path(args.repo).resolve()

    server = None
    base = args.base_url
    if not base:
        server, base = serve(root)
    # "./" is the base URL itself. An empty --page means the same thing, but
    # it would show in the report as no page at all.
    pages = [p or "./" for p in args.page] or discover_pages(root) or ["./"]
    capped = len(pages) > MAX_PAGES
    pages = pages[:MAX_PAGES]

    findings = []
    axe = axe_source()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        for path in pages:
            check_page(context, urllib.parse.urljoin(base, path), axe,
                       findings)
        check_js_syntax(context, root, findings)
        browser.close()
    if server:
        server.shutdown()

    meta = {"check": "browser", "pages": pages, "axe": AXE_VERSION,
            "served_locally": server is not None, "capped": capped}
    write_findings(args.out, findings, meta)
    print(f"browser: {len(pages)} page(s), {len(findings)} finding(s)")


if __name__ == "__main__":
    main()
