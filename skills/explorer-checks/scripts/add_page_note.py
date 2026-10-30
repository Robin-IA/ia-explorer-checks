"""Add, refresh or remove the "checked" note on an explorer page.

    python add_page_note.py <page.html> --report <explorer>/security-accessibility-checks.md
                            --report-url https://github.com/<org>/<repo>/blob/main/security-accessibility-checks.md
    python add_page_note.py <page.html> --remove

It refuses to add the note unless the report says passing. The note says
what was checked and when, and links to the report. It does not claim
conformance, because the checks cannot establish it. A run that stops
passing should remove the note, since an out-of-date claim is worse than
none.

The note sits between marker comments, so re-running replaces it in place.
It goes at the end of <footer> if the page has one, otherwise just before
</body>. It inherits the page's text colour, so its contrast is whatever the
page's contrast already is, and the page has just passed.
"""

import argparse
import datetime
import pathlib
import re
import sys

from render_report import previous_open

START, END = "<!-- explorer-checks:note -->", "<!-- /explorer-checks:note -->"
BLOCK = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)

NOTE = """{start}
<p class="explorer-checks-note" style="font-size:0.875em;margin:1em 0 0">
  Checked for accessibility (WCAG 2.2 AA), security and code validity on
  <time datetime="{iso}">{human}</time>; no open issues.
  <a href="{url}">Read the report</a>.
</p>
{end}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("--report")
    ap.add_argument("--report-url")
    ap.add_argument("--remove", action="store_true")
    args = ap.parse_args()

    page = pathlib.Path(args.page)
    text = page.read_text(encoding="utf-8")
    text = BLOCK.sub("", text)

    if args.remove:
        page.write_text(text, encoding="utf-8", newline="")
        print(f"note removed from {page}")
        return 0

    if not (args.report and args.report_url):
        sys.exit("--report and --report-url are required to add the note")
    state = previous_open(pathlib.Path(args.report))
    if not state or not state.get("passing"):
        sys.exit("the report does not say passing; not adding the note")

    day = datetime.date.fromisoformat(state["date"])
    note = NOTE.format(start=START, end=END, iso=day.isoformat(),
                       human=f"{day.day} {day:%B %Y}", url=args.report_url)

    for closing in ("</footer>", "</body>"):
        i = text.lower().rfind(closing)
        if i != -1:
            text = text[:i] + note + text[i:]
            break
    else:
        sys.exit(f"{page} has neither </footer> nor </body>; place the note "
                 f"by hand between the markers")
    page.write_text(text, encoding="utf-8", newline="")
    print(f"note added to {page} ({closing})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
