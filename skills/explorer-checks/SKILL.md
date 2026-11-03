---
name: explorer-checks
description: Check an Internet Archive explorer (a Wayback or archive.org collection explorer such as federal-pandemic-record-covid19) for code validity, code security and accessibility against WCAG 2.2 AA. Given the explorer's GitHub URL or live URL, it runs real tools (html5lib, ruff, bandit, pip-audit, axe-core in headless Chromium), reviews the code against written checklists, and writes security-accessibility-checks.md into the explorer repo on a branch with a pull request. The report lists every open item with a recommended fix. Re-run until it passes, at which point the skill adds a dated "checked" note to the explorer's page. Use whenever someone asks to check, audit or review an explorer's accessibility, WCAG compliance, security or code quality, or to re-run those checks after fixes.
---

# Explorer checks

Three checks, one report, re-run until it passes:

1. **Code validity**: the HTML parses, JSON loads, Python lints clean of
   real errors, the project's own tests pass, local links resolve, and the
   page loads without JavaScript errors or failed requests.
2. **Code security**: no credentials in the repository, every place a
   string becomes markup has been traced, dependencies have no known
   vulnerabilities, and the Python passes bandit.
3. **Accessibility**: axe-core finds no WCAG 2.0/2.1/2.2 A or AA violation,
   the page reflows at 320 px, focus is visible, and the manual checklist
   in `references/wcag-manual-review.md` is complete.

The scripts are the automated half. **You are the other half**, and a check
cannot pass without you. Tools cannot tell escaped data from raw data, or
whether alt text is meaningful. Most of WCAG needs a reader.

Scripts are in `scripts/` next to this file. Call them with the Python that
has `requirements.txt` installed (see the repository README).

## 1. Get the explorer

The user gives a URL. Work out the GitHub repository:

- `github.com/<org>/<repo>` → that repository.
- A live page (wayback-labs, GitHub Pages, anywhere else) → find the repo
  from the page's footer or source, or ask. Keep the live URL; it goes to
  `--live-url` for the header check.

Read `references/explorer-repos.md` before touching the checkout. Explorer
repos have more than one remote, and `main` can be stale.

Work in `~/explorer-checks/<repo>/`. Clone if it is absent, otherwise fetch
every remote. Then:

- **First run:** confirm with the user before creating anything in the
  explorer's repository, since it is probably someone else's. Then create
  branch `explorer-checks` from the up-to-date `main`.
- **Re-run:** if `explorer-checks` exists on the remote, check it out and
  pull. An open PR from it is the one to update. Do not start a second.

## 2. Serve it

- **Static explorer** (HTML + JS + data files, like the covid record):
  nothing to do. The browser check serves the repository root itself, so it
  tests this branch, fixes included.
- **App** (Flask etc.): start it as its README says, in the background, and
  pass `--base-url http://127.0.0.1:<port>/`. If it needs data that is not
  in the repo, say so in the review and check what does run.

Pick the pages. The script discovers HTML files, but an app's routes are not
files, and a static repo may hold HTML no visitor sees. Pass the real entry
points with `--page` (repeatable), for example `--page mockup/`, or
`--page ./` for the site root.

## 3. Run the automated checks

```bash
python scripts/run_checks.py ~/explorer-checks/<repo> --page <path> \
    [--base-url URL] [--live-url URL]
```

It prints a table and the path of `findings.json`. Read that whole file.
Every finding has an `id`, a `status` (`fail`, `review`, `advisory`) and a
recommended fix.

A finding whose rule starts `tool:` means a checker did not run. Fix the
cause and re-run before going on. A report missing a check reads as a pass
for that check, and it would be false.

## 4. Review: your half

Write `review.json` in the same folder as `findings.json`. Its shape is in
the docstring of `scripts/render_report.py`.

1. **Resolve every `review` finding.** Open the code at `where`, trace it,
   and give a verdict: `fail` (with what you found) or `cleared` (with the
   reason, specific enough for a colleague to check, e.g. "only `fmtN()`
   output and literals reach it" and not "looks safe"). For innerHTML
   sinks, follow `references/security-review.md`.
2. **Work through both checklists**, `references/security-review.md` and
   `references/wcag-manual-review.md`. Record each item as `pass`, `fail`
   or `n/a` with a short note in `manual.security` and
   `manual.accessibility`. Use the browser: read the page, tab through it,
   look at it at 320 px and at 200% zoom.
3. **Add your own findings** for anything the checklists turn up that no
   tool caught, as entries in `findings` with `source` set to `review`.
   Each needs a recommended fix you would actually make: the specific
   change, file and line, not a pointer to the WCAG text.

Do not clear things to reach a pass. If a finding is real but minor,
it stays `fail`; the fix is usually small.

## 5. Write the report into the explorer

```bash
python scripts/render_report.py <findings.json> --review <review.json> \
    --out ~/explorer-checks/<repo>/security-accessibility-checks.md
```

The report is at the same path whether passing or not; each run replaces it.
It records which ids were open, so the next run lists what was fixed.

Commit it on `explorer-checks`, push, and open the PR, or update it if
one exists:

```bash
gh pr create --base main --head explorer-checks \
    --title "Security and accessibility checks" --body "..."
```

The PR body gives the status line, the summary table, and the number of
must-fix items per check. Link the report file. Merging is the explorer
owners' call. Never merge it yourself, and never push to `main`.

## 6. Fixes

Ask the user whether to apply the recommended fixes now. If yes:

- One commit per finding or per small group, with the ids in the message
  (`Fix A-8498a4: add lang="en" to <html>`). The report and the history
  then tell the same story.
- Fix the cause, not the detector. A missing `lang` is fixed by adding
  `lang`, not by excluding the rule.
- Things only the owners can decide (removing a feature, changing a data
  source, rotating a credential) stay in the report. Tell the user about
  them; do not guess.

Then go back to step 3. Repeat until the report says passing, or until
only owner decisions remain.

## 7. When it passes

1. Add the note to each checked page:

   ```bash
   python scripts/add_page_note.py ~/explorer-checks/<repo>/<page>.html \
       --report ~/explorer-checks/<repo>/security-accessibility-checks.md \
       --report-url https://github.com/<org>/<repo>/blob/main/security-accessibility-checks.md
   ```

   For an app, put the note in the template that renders the footer, by
   hand, between the same marker comments.
2. **Re-run steps 3 to 5.** The note is new markup on a page that has to
   stay passing. The re-run also re-dates the report against the commit
   that carries the note.
3. Commit and push, and update the PR body to say passing.

If a later run stops passing, remove the note in the same branch
(`add_page_note.py <page> --remove`). A stale claim is worse than none.

## What to tell the user

At the end, in this order:

1. The status and the count of must-fix items per check.
2. **A bulleted list of every must-fix item**, grouped by check. Give each
   one line: what is wrong, in plain words, then how you would fix it
   ("Search box has no visible label → add a `<label for="q">`"). Take
   both from the report's titles and recommended fixes. Ids alone mean
   nothing to the reader. A count without the list makes the user ask
   what failed.
3. The PR link.
4. What you could not check, such as an app that would not start, pages
   behind a login, or npm dependencies with no npm available.

Say it plainly. A check that did not run did not pass.

If you ask whether to apply the fixes, ask after the list, so the user
knows what they are agreeing to.
