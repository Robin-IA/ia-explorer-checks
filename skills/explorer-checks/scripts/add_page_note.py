"""Add, refresh or remove the "checked" note on an explorer page.

    python add_page_note.py <page.html> --report <explorer>/security-accessibility-checks.md
                            --report-url https://github.com/<org>/<repo>/blob/main/security-accessibility-checks.md
                            [--position top|bottom] [--print]
    python add_page_note.py <page.html> --remove

It refuses to add the note unless the report says passing. The note names
the accessibility standards met, the date they were checked and how, and
links to the report, whose "Standards met" and "What a pass means"
sections give the detail and the limits. A run that stops passing should
remove the note, since an out-of-date claim is worse than none.

The note sits between marker comments, so re-running replaces it in place,
keeping its indentation and any wrapper it was given. An owner can move the
block by hand, and later runs leave it there. --position moves it.

--position bottom (the default the first time): at the end of <footer> if
the page has one. Otherwise in a <footer> of its own, just after </main>,
else just before </body>, else at the end of the file: HTML lets a page
leave out </body>, and some explorers do.

--position top: the first thing inside <main>, so it sits below the page's
header and skip link rather than ahead of them. With no <main>, it goes
just after <body> in an <aside> labelled for what it is. With neither, it
goes at the bottom instead, and says so.

Either way the note stays inside a landmark, which axe's region rule
requires. It inherits the page's text colour, so its contrast is whatever
the page's contrast already is, and the page has just passed.

Its size is small but readable: 0.875em of the text around it, kept between
10 and 12 points (13.3 to 16 px at the browser's default text size). The
limits are in rem, so the note still grows when a reader enlarges text.

--print changes nothing. It prints the note and exactly where it would go
(file, line, and the line before it), for an owner who would rather paste
it in by hand. The marker comments are part of what to paste: they let a
later run refresh the date, or take the note down if the page stops
passing.
"""

import argparse
import datetime
import pathlib
import re
import sys

from render_report import ALSO_MET, STANDARD, previous_open

SIZE = "clamp(0.8333rem, 0.875em, 1rem)"   # 10pt to 12pt, scaling with text
START, END = "<!-- explorer-checks:note -->", "<!-- /explorer-checks:note -->"
BLOCK = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)

NOTE = """{start}
<p class="explorer-checks-note" style="font-size:{size};margin:{margin}">
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
    ap.add_argument("--position", choices=("top", "bottom"),
                    help="where to put the note; moves an existing one")
    ap.add_argument("--remove", action="store_true")
    ap.add_argument("--print", action="store_true", dest="show",
                    help="print the note and where it goes; change nothing")
    args = ap.parse_args()

    page = pathlib.Path(args.page)
    text = page.read_text(encoding="utf-8")
    old = BLOCK.search(text)

    if args.remove:
        text = BLOCK.sub("", text)
        page.write_text(text, encoding="utf-8", newline="")
        print(f"note removed from {page}")
        return 0

    if not (args.report and args.report_url):
        sys.exit("--report and --report-url are required to add the note")
    state = previous_open(pathlib.Path(args.report))
    if not state or not state.get("passing"):
        sys.exit("the report does not say passing; not adding the note")

    day = datetime.date.fromisoformat(state["date"])
    position = args.position or "bottom"
    note = NOTE.format(start=START, end=END, standard=STANDARD, also=ALSO_MET,
                       iso=day.isoformat(), human=f"{day.day} {day:%B %Y}",
                       url=args.report_url, size=SIZE,
                       margin="0 0 1em" if position == "top" else "1em 0 0")

    if old and not args.position:
        text, where = replace(text, old, note), "kept in place"
    else:
        text = BLOCK.sub("", text)
        place_at = place_top if position == "top" else place
        text, where = place_at(text, note)
    if args.show:
        print(paste_instructions(page, text, where, replacing=bool(old)))
        return 0
    page.write_text(text, encoding="utf-8", newline="")
    print(f"note added to {page} ({where})")
    return 0


ASIDE = '<aside aria-label="Accessibility and security checks">'
OPEN_TAG = {tag: re.compile(rf"<{tag}\b[^>]*>", re.I) for tag in ("main", "body")}


def wrap(note, open_tag):
    """The note inside open_tag and its closing tag, within the markers."""
    close = "</" + re.match(r"<(\w+)", open_tag).group(1) + ">"
    return note.replace(START + "\n", START + "\n" + open_tag + "\n").replace(
        "\n" + END, "\n" + close + "\n" + END)


def replace(text, old, note):
    """The new note where the old one was, in the old one's indentation,
    wrapper and margin."""
    if "<footer>" in old.group(0):
        note = wrap(note, "<footer>")
    elif ASIDE in old.group(0):
        note = wrap(note, ASIDE)
    if "margin:0 0 1em" in old.group(0):
        note = note.replace("margin:1em 0 0", "margin:0 0 1em")
    indent = text[text.rfind("\n", 0, old.start()) + 1:old.start()]
    if indent.strip():
        indent = ""
    lines = note.rstrip("\n").split("\n")
    note = "\n".join(lines[:1] + [indent + line for line in lines[1:]]) + "\n"
    return text[:old.start()] + note + text[old.end():]


def place(text, note):
    low = text.lower()
    i = low.rfind("</footer>")
    if i != -1:
        return text[:i] + note + text[i:], "end of <footer>"
    note = wrap(note, "<footer>")
    i = low.rfind("</main>")
    if i != -1:
        i += len("</main>")
        return text[:i] + "\n" + note.rstrip("\n") + text[i:], "after </main>"
    i = low.rfind("</body>")
    if i != -1:
        return text[:i] + note + text[i:], "before </body>"
    return text.rstrip("\n") + "\n" + note, "end of file"


def insert_after(text, m, note):
    return text[:m.end()] + "\n" + note.rstrip("\n") + text[m.end():]


def place_top(text, note):
    m = OPEN_TAG["main"].search(text)
    if m:
        return insert_after(text, m, note), "start of <main>"
    m = OPEN_TAG["body"].search(text)
    if m:
        return insert_after(text, m, wrap(note, ASIDE)), \
            "start of <body>, in an <aside>"
    text, where = place(text, note.replace("margin:0 0 1em", "margin:1em 0 0"))
    return text, f"{where}; no <main> or <body> to put it at the top of"


def paste_instructions(page, text, where, replacing):
    """What to paste and exactly where, read off the page as it would be
    after placing the note, so it matches what the script would do."""
    nl = "\n"
    m = BLOCK.search(text)
    first = text.count(nl, 0, m.start()) + 1
    block = m.group(0).rstrip(nl)
    last = first + block.count(nl)
    before = text[:m.start()].rstrip(nl).rsplit(nl, 1)[-1].strip()
    if replacing:
        how = (f"Replace lines {first} to {last} of {page} (the old note, "
               "between the explorer-checks markers) with:")
    else:
        how = (f"Paste this into {page} as a new line {first}, {where}, "
               f"directly after the line that reads:{nl}{nl}    {before}"
               f"{nl}{nl}Paste:")
    return nl.join([how, "", block, "",
                    "Keep the two marker comments: they let a later run update "
                    "the date, or take the note down if the page stops "
                    "passing. Save the file, commit it, and re-run the checks "
                    "so the report confirms the page still passes with the "
                    "note."])


if __name__ == "__main__":
    sys.exit(main())
