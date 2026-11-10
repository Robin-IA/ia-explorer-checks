---
name: explorer-checks
description: Check an Internet Archive explorer (a Wayback or archive.org collection explorer such as federal-pandemic-record-covid19) for code validity, code security and accessibility against WCAG 2.2 AA. Given the explorer's GitHub URL or live URL, it runs real tools (html5lib, ruff, bandit, pip-audit, axe-core in headless Chromium), reviews the code against written checklists, and writes security-accessibility-checks.md, which lists every open item with a recommended fix. It works in a local checkout and shows the user what needs fixing before anything leaves the machine; it applies fixes, pushes a branch, opens a pull request or files issues (labelled checker, bug, fix and accessibilitysec, each with Instructions for Claude) only after asking about each, and never merges. Every run ends with explorer-validation-report.md, which says whether each finding is accessibility, security, code validity or a missing best-practice element. Re-run at any time; once all three checks pass it adds, with permission, a dated accessibility statement to the explorer's page; security and code validity results are never published on the page. Use whenever someone asks to check, audit or review an explorer's accessibility, WCAG compliance, security or code quality, or to re-run those checks after fixes.
---

# Explorer checks

Three checks, one report, re-run until it passes:

1. **Code validity**: the HTML parses, JSON loads, Python lints clean of
   real errors, the project's own tests pass, local links resolve, and the
   page loads without JavaScript errors or failed requests.
2. **Code security**: no credentials in the repository, every place a
   string becomes markup has been traced, dependencies are pinned and have
   no known vulnerabilities, the Python passes bandit, and the checklist in
   `references/security-review.md` is complete. Every finding and item
   names its OWASP Top 10:2025 category and ASVS 5.0.0 chapter.
3. **Accessibility**: axe-core finds no WCAG 2.0/2.1/2.2 A or AA violation,
   the page reflows at 320 px, focus is visible, and the manual checklist
   in `references/wcag-manual-review.md` is complete.

**Ask before every change that reaches someone else.** The explorer is
probably not the user's, and the person running this may not be its owner.
Cloning, checking and writing the report happen locally without asking.
Applying fixes, adding the page note, pushing a branch and opening or
updating a pull request each wait for the user's yes, given after they
have seen what it covers. A yes covers that one step, not the rest of the
run. Never merge, and never push to `main`.

The scripts are the automated half. **You are the other half**, and a check
cannot pass without you. Tools cannot tell escaped data from raw data, or
whether alt text is meaningful. Most of WCAG needs a reader.

Scripts are in `scripts/` next to this file. Run them with the Python
recorded at install, which has the packages they need:

```bash
PY="$(cat ~/.claude/skills/explorer-checks/PYTHON)"
```

`"$PY"` in the commands below is that Python. If `PYTHON` is missing, or
a script fails with `No module named …`, setup is incomplete: stop and
point the user to `SETUP.md` in the checker's repository. Do not
`pip install` into some other Python to get past it.

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

- **First run:** create a local branch `explorer-checks` from the
  up-to-date `main`. It stays local until step 6.
- **Re-run:** if `explorer-checks` exists on the remote, check it out and
  pull. An open PR from it is the one to update. Do not start a second.
  A re-run can come at any time (after fixes, after an unrelated change
  to the explorer, or just to re-date a passing report), and it follows
  the same steps.

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

**Pass every view.** axe checks only what is shown, so an explorer with
tabs or views that show and hide sections has parts no tool has seen.
If the page opens a view from the URL (`#pages`, `?view=pages`), pass one
`--page` per view: `--page ./ --page ./#pages --page ./#about`. If it
cannot, say so in the review and check the hidden views by hand.

## 3. Run the automated checks

```bash
"$PY" scripts/run_checks.py ~/explorer-checks/<repo> --page <path> \
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

## 5. Write the report, locally

```bash
"$PY" scripts/render_report.py <findings.json> --review <review.json> \
    --out ~/explorer-checks/<repo>/security-accessibility-checks.md
```

The report is at the same path whether passing or not; each run replaces it.
It records which ids were open, so the next run lists what was fixed.

Commit it on the local `explorer-checks` branch. Do not push yet.

## 6. Show the user, then ask

Tell the user, in this order:

1. The status and the count of must-fix items per check. On a pass, the
   accessibility standards met and the date checked, as the report's
   "Standards met" section gives them.
2. **A bulleted list of every must-fix item**, grouped by check. Give each
   one line: what is wrong, in plain words, then how you would fix it
   ("Search box has no visible label → add a `<label for="q">`"). Take
   both from the report's titles and recommended fixes. Ids alone mean
   nothing to the reader. A count without the list makes the user ask
   what failed.
3. What you could not check, such as an app that would not start, pages
   behind a login, npm dependencies with no npm available, or the host a
   self-hosted explorer runs on. A check that did not run did not pass.
4. Where the report is on disk.

Then ask what to do next. The choices are:

- **Apply the fixes** (step 7), then come back here with the new report.
- **Push the report as it stands** and open a PR (step 9), so the owners
  can fix it themselves.
- **File issues** (step 10): one issue per must-fix item in the explorer's
  repository, each asked about before it is filed, so the owners can fix
  them later.
- **Stop.** The report stays on this machine, and nothing has changed in
  the explorer's repository.

Ask after the list, so the user knows what they are agreeing to. On a
pass, the question is whether to add the page note (step 8).

## 7. Fixes (only on a yes)

Work one check at a time, in this order: validity (if anything failed),
then security, then accessibility. For each:

1. Run that check's script on its own, so the fixes start from what is
   there now, not from the last report:

   ```bash
   "$PY" scripts/check_validity.py <repo> --out <dir>/validity.json
   "$PY" scripts/check_security.py <repo> --out <dir>/security.json [--live-url URL]
   "$PY" scripts/check_browser.py  <repo> --out <dir>/browser.json --page <path>
   ```

   `check_browser.py` carries the accessibility checks.
2. Apply that check's fixes, and verify them in the browser where they
   change behaviour (focus, keyboard, contrast).
3. **One local commit for the check**, listing each finding's id and its
   fix in the message body (`Fix S-cd5758: escape …`). The report and the
   history then tell the same story.

Throughout:

- Fix the cause, not the detector. A missing `lang` is fixed by adding
  `lang`, not by excluding the rule.
- Things only the owners can decide (removing a feature, changing a data
  source, rotating a credential) stay in the report. Tell the user about
  them; do not guess.

Then go back to step 3 and re-run all three checks together, write the
report (step 5) and show the user again (step 6). Repeat until the report
says passing, until only owner decisions remain, or until the user stops.

The report lists what was fixed by comparing with the report as last
committed. If that is not the run to compare with, pass
`--since <commit>` to `render_report.py`.

## 8. When it passes: the page note (only on a yes)

The note puts a public statement on the explorer's page: the accessibility
standards met and the date checked. All three checks must pass before it
goes on, but it says nothing about security or code validity. Those
results are not published on the page, in the note or anywhere else: do
not add a security or validity claim to the page, its About page or its
footer, and remove one if you find it. It does not link to the report: the report is filed in
the explorer's repository for the owner's review, as the run's output, and
is not part of the page. Show the user the wording, then ask how they want
it added. Three choices:

- **Bottom** (the default): in the page's footer, where readers look for
  this kind of statement.
- **Top**: the first thing in the main content, below the header and skip
  link, where every visitor sees it.
- **I'll paste it in myself**: the owner adds it to their own code. You
  give them the code and say exactly where it goes.

At either position the note is small but readable: 0.875em of the
surrounding text, held between 10 and 12 points
(`clamp(0.8333rem, 0.875em, 1rem)`), in rem so it still grows when a
reader enlarges text. Do not make it smaller.

If the page already carries the note, it stays where it is unless the user
asks to move it.

**Top or bottom.** Add the note to each checked page:

```bash
"$PY" scripts/add_page_note.py ~/explorer-checks/<repo>/<page>.html     --report ~/explorer-checks/<repo>/security-accessibility-checks.md     --position bottom   # or top
```

Leave `--position` off on a re-run to keep the note where it is; pass it
to move the note. Then **re-run steps 3 to 5.** The note is new markup on
a page that has to stay passing, and the re-run also re-dates the report
against the commit that carries the note.

**I'll paste it in myself.** Ask whether they want it at the top or the
bottom, then run the same command with `--print` added. It changes
nothing, and prints the code and where it goes: the file, the line
number, and the line it follows (or, if a note is already there, which
lines to replace). Give the user, for each page:

1. The file to open, in their own copy of the explorer.
2. Where to put it, in words they can find: "directly after the line
   `<main id="content">`, near line 6". Line numbers drift as files
   change, so lead with the line it follows.
3. The code, in one fenced `html` block they can copy whole, marker
   comments included.
4. What to do next: save, commit and push as they usually do, and then
   ask for a re-run, so the report confirms the page still passes with
   the note. Until that re-run, the report does not cover the note.

For an **app** (Flask and the like), the page is a template: find the
template that renders the main content or footer, and give the
instructions for that file. A template's markup can differ from what
`--print` reads in the served page, so read the template and name the
spot yourself.

When they paste it themselves, leave the note out of your own commits:
the pull request carries the report and any fixes only. Say so before
pushing.

**On a later run,** the markers let the script refresh the date or take
the note down. If a run stops passing, remove the note in the same branch
(`add_page_note.py <page> --remove`) and tell the user you have. A stale
claim is worse than none. The removal goes out with the next push.

## 9. Push and open the PR (only on a yes)

Before pushing, say what will go: the branch, the commits on it (the
report, any fixes, the note) and the repository. On a yes, push
`explorer-checks` and open the PR, or update it if one exists:

```bash
gh pr create --base main --head explorer-checks \
    --title "Security and accessibility checks" --body "..."
```

The PR body gives the status line, the summary table, and the number of
must-fix items per check, lists the fixes applied, and links the report
file.

**After an explorer design check.** When this skill runs as the last part
of `/explorer-design-checker`, the branch already carries the design
fixes and report. Open **one** pull request for both, titled "Explorer
design, accessibility and security checks", not a second one: its body
gives both checks' status lines and a table with one row per commit, so
the owner can revert any single fix with `git revert <commit>`, plus the
issues it closes and the publishing steps the design checker gives.

## 10. File issues (only on a yes, one at a time)

When the user wants issues rather than, or as well as, a pull request:

1. **Ask which repository** if it is not obvious, and give its full URL.
   Issues go to the repository the owners work in, not to a mirror.
2. **Ask about each must-fix item separately**, with AskUserQuestion (up to
   four at a time): show the title and a one-line summary of the body.
   Options: **File it**, **Skip**. File only the ones the user approves.
3. **Labels.** Every issue gets `checker`, `bug`, `fix` and
   **`accessibilitysec`**, which marks it as found by this checker
   (accessibility, security or code validity); the explorer design
   checker labels its issues `design` instead. Create any that
   are missing first:

   ```bash
   gh label create checker --repo <owner>/<repo> --color 5319E7 --description "Found by the explorer checkers"
   gh label create fix --repo <owner>/<repo> --color 0E8A16 --description "Has a recommended fix ready to apply"
   gh label create accessibilitysec --repo <owner>/<repo> --color D93F0B --description "Accessibility, security or code validity, found by the accessibility and security checker"
   ```

   (`bug` exists in every new repository.)

   **A suggestion is not a bug.** Anything that is a recommendation rather
   than a defect (an advisory the user chooses to file, or a repository
   setting) gets `suggestion` instead of `bug`, a title starting
   "Suggestion:", and the category "Suggestion":

   ```bash
   gh label create suggestion --repo <owner>/<repo> --color FBCA04 --description "A recommendation, not a defect: the owner decides"
   ```
4. **Body**, in this order:
   - **Where**: the file and line, or the page and element.
   - **What is wrong**, in plain words, with the evidence: the measured
     value, the code line, what was tested.
   - **Fix**: the exact change, as code where it helps.
   - The category: accessibility (with the WCAG criterion), security (with
     the OWASP Top 10:2025 category and ASVS chapter) or code validity.
   - **`## Instructions for Claude`**, for whoever picks the issue up with
     Claude:

     ```markdown
     ## Instructions for Claude

     When someone asks you to work on this issue:

     1. **Overview first.** Before changing anything, tell the person in two or three plain sentences what is wrong, who it affects and where it is (<file and line>).
     2. **Then how to fix it.** Describe the change in the **Fix** section above, file and line, and show the exact edit. Ask before applying it.
     3. **Apply it on a branch**, never on `main`, and open a pull request that closes this issue (`Fixes #<n>`).
     4. **Check it.** <how to confirm this particular fix: the value to measure, the key to press, the request to send>
     5. Re-run `/explorer-checks` on the branch so the report confirms the finding is gone.
     ```

     Fill in the place, the issue number (edit the issue after creating
     it if needed) and a specific check. Add anything the fixer must know
     about this repository, such as generated pages or a mirror.
   - A footer line: found by the accessibility and security checker
     (with the skill version), the date, and the commit checked.

   ```bash
   gh issue create --repo <owner>/<repo> --title "…" --body-file <file> --label checker,bug,fix,accessibilitysec
   ```

5. Give the user each issue's link.

## 11. Validation report

At the end of every run, write `explorer-validation-report.md` in the
checkout, beside `security-accessibility-checks.md`, and commit it on the
local branch. It is the short version for the owners: what was found and
what kind of problem each is.

- **Header**: the explorer, live URL, repository and commit, date, checker
  versions, pages checked.
- **Summary**: a table of must-fix counts by category: **Accessibility**,
  **Security**, **Code validity**, and **Best practices: missing element**
  if `/explorer-design-checker` ran (otherwise say it was not checked),
  with the issue numbers filed for each.
- **Findings**: one row per item: what it is in a sentence, its category
  (with the WCAG criterion or OWASP category), where, and the issue link
  or "not filed".
- **Looked at, not failing**: what was reviewed and cleared, in a few
  sentences per check, so a reader knows the passes were checked.
- **Not decided, for the owners**, and **Could not check**.

It goes out with the pull request, if there is one; otherwise it stays
local, and say where it is.

## 12. Hand over

End with:

1. The PR link and the status it carries, or the issues filed.
2. **The review and merge are the owners'.** Tell the user to read the
   diff, check the fixes on the page, and merge, or pass the PR to the
   explorer's owners if that is not them. The report's claim is about the
   commit that was checked; changes before the merge need a re-run.
3. Anything still open: owner decisions, and what could not be checked.
4. Where the validation report is.
