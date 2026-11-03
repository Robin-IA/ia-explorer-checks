"""Add, refresh or remove the "checked" note on an explorer page.

    python add_page_note.py <page.html> --report <explorer>/security-accessibility-checks.md
                            --report-url https://github.com/<org>/<repo>/blob/main/security-accessibility-checks.md
    python add_page_note.py <page.html> --remove

It refuses to add the note unless the report says passing. The note names
the accessibility standards met, the date they were checked and how, and
links to the report, whose "Standards met" and "What a pass means"
sections give the detail and the limits. A run that stops passing should
remove the note, since an out-of-date claim is worse than none.

The note sits between marker comments, so re-running replaces it in place.
It goes at the end of <footer> if the page has one. Otherwise it goes in a
<footer> of its own, just after </main>, else just before </body>, else at
the end of the file: HTML lets a page leave out </body>, and some explorers
do. Its own <footer> keeps the note inside a landmark. It inherits the
page's text colour, so its contrast is whatever the page's contrast already
is, and the page has just passed.
"""

import argparse
import datetime
import pathlib
import re
import sys

from render_report import ALSO_MET, STANDARD, previous_open

START, END = "<!-- explorer-checks:note -->", "<!-- /explorer-checks:note -->"
BLOCK = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)

NOTE = """{start}
<p class="explorer-checks-note" style="font-size:0.875em;margin:1em 0 0">
  Meets {standard} accessibility (and {also}), checked
  <time datetime="{iso}">{human}</time> by automated tests and manual review.
  Also passes security and code validity checks.
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
    note = NOTE.format(start=START, end=END, standard=STANDARD, also=ALSO_MET,
                       iso=day.isoformat(), human=f"{day.day} {day:%B %Y}",
                       url=args.report_url)

    text, where = place(text, note)
    page.write_text(text, encoding="utf-8", newline="")
    print(f"note added to {page} ({where})")
    return 0


def place(text, note):
    low = text.lower()
    i = low.rfind("</footer>")
    if i != -1:
        return text[:i] + note + text[i:], "end of <footer>"
    note = note.replace(START + "\n", START + "\n<footer>\n").replace(
        "\n" + END, "\n</footer>\n" + END)
    i = low.rfind("</main>")
    if i != -1:
        i += len("</main>")
        return text[:i] + "\n" + note.rstrip("\n") + text[i:], "after </main>"
    i = low.rfind("</body>")
    if i != -1:
        return text[:i] + note + text[i:], "before </body>"
    return text.rstrip("\n") + "\n" + note, "end of file"


if __name__ == "__main__":
    sys.exit(main())
