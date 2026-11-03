# Explorer checks

A Claude Code skill that checks an Internet Archive explorer (a Wayback or
archive.org collection explorer such as
[federal-pandemic-record-covid19](https://github.com/internetarchivecanada/federal-pandemic-record-covid19))
three ways:

| Check | Automated | Reviewed by Claude |
|---|---|---|
| **Code validity** | HTML parsing (html5lib), JSON, Python (ruff), the project's own tests, local links, JavaScript errors and failed requests on load | — |
| **Code security** | credential patterns, markup sinks (`innerHTML` and kin), bandit, pip-audit, live response headers | every sink traced to its data, plus [a checklist](skills/explorer-checks/references/security-review.md) |
| **Accessibility** | axe-core against WCAG 2.2 A/AA in headless Chromium, 320 px reflow, focus visibility | the AA criteria axe cannot settle, in [a checklist](skills/explorer-checks/references/wcag-manual-review.md) |

It writes `security-accessibility-checks.md` into the explorer's repository,
on a branch, with a pull request. While anything is open, the report lists
each item with a recommended fix. Re-run after fixing, as often as it takes.
Once all three checks pass, the skill adds a dated note to the explorer's
page that links to the report:

> Checked for accessibility (WCAG 2.2 AA), security and code validity on
> 30 October 2026; no open issues. Read the report.

The note says what was checked and when, not "WCAG conformant". Automated
tools plus a code review cannot establish full conformance, and the report
says so. A later run that stops passing removes the note.

## Install

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
python3 install.py
```

`install.py` copies the skill to `~/.claude/skills/explorer-checks/`. Run it
again after pulling changes; `python3 install.py --check` says whether
that's needed.

## Use

In Claude Code, from any directory:

> Run explorer checks on https://github.com/internetarchivecanada/federal-pandemic-record-covid19

Claude clones the explorer into `~/explorer-checks/<repo>/`, runs the
checks, reviews what the tools cannot decide, and asks before pushing
anything to the explorer's repository. It never merges. That is the
explorer owners' call.

The scripts also run on their own, which is useful for a quick look at a
checkout:

```bash
python3 skills/explorer-checks/scripts/run_checks.py <checkout> --page mockup/
```

## How a run works

[SKILL.md](skills/explorer-checks/SKILL.md) is the procedure Claude
follows. In short:

1. **Check out** the explorer on branch `explorer-checks`, from an
   up-to-date `main`.
2. **Run** `run_checks.py`, which writes `findings.json`. Each finding is
   `fail`, `review` (a tool cannot decide) or `advisory`.
3. **Review**: Claude resolves every `review` item, works both checklists
   in the browser, and adds what the tools missed, in `review.json`.
4. **Report**: `render_report.py` writes the report into the explorer, and
   Claude opens or updates the PR.
5. **Fix and re-run**, with Claude applying the recommended fixes if asked.
   Finding ids are stable across runs, so the report lists what was fixed
   since last time.
6. **On a pass**, `add_page_note.py` adds the note, and one more run
   confirms the page still passes with it.

A check passes only with no `fail` items, no unresolved `review` items and,
for security and accessibility, a completed manual checklist. A tool that
did not run produces a finding, so it cannot pass silently.

## Example

[examples/covid19-trial-2026-10-30.md](examples/covid19-trial-2026-10-30.md)
is the trial run against the Federal Pandemic Record mockup at commit
`b88bae6d66`. The manual review in it is partial (security in full,
accessibility on the keyboard and labelling items), so it shows the format
and is not a complete audit. It was not pushed to that repository.

## Tests

```bash
python3 -m pytest
```
