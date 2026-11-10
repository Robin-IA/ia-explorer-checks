# Explorer checks

> **Source and mirror.** This is developed at
> [Robin-IA/ia-explorer-checks](https://github.com/Robin-IA/ia-explorer-checks).
> [internetarchivecanada/accessibility-security-checker](https://github.com/internetarchivecanada/accessibility-security-checker)
> is a read-only **mirror** of it, following its `main`: open pull requests
> on the Robin-IA source, not on the mirror.

> **Checking an explorer? Start with the
> [explorer design checker](https://github.com/internetarchivecanada/explorer-design-checker)**
> (`/explorer-design-checker`). It checks the explorer against the
> explorer best practices first, then runs this checker last, after the
> design fixes are in. This checker also stands alone: run it by itself
> on any web project, or to re-check an explorer after a change.

A Claude Code skill that checks a web project for **code validity**,
**security** and **accessibility** (WCAG 2.2 Level AA). It writes the
result as a report, shows you what needs fixing, and asks before it
changes anything. Once a project passes, it can put a dated statement of
the result on the project's page.

**New here? Read [START-HERE.md](START-HERE.md)**, the step-by-step recipe
for setting it up and checking your first explorer. This README is the
reference.

**Feedback or a problem?** Use the
[feedback form](https://github.com/internetarchivecanada/accessibility-security-checker/issues/new?template=feedback.yml).
It opens an issue on the internetarchivecanada mirror, which only
Internet Archive staff can see, and goes straight to the maintainer.

## What it is for

Today it checks Internet Archive **explorers**: static sites and small
Flask apps that present a Wayback or archive.org collection, such as
[federal-pandemic-record-covid19](https://github.com/internetarchivecanada/federal-pandemic-record-covid19).
The checklists are written for what explorers do: render archive.org
titles and Wayback text they did not write, filter with facets, draw
histograms, and link out to the Wayback Machine. Most of it applies to any
small web project. Pointing it at something that is not an explorer works,
but expect a few checklist items to be `n/a` and a few gaps.

## What it does

| Check | Automated | Reviewed by Claude |
|---|---|---|
| **Code validity** | HTML parsing (html5lib), JSON, Python (ruff), the project's own tests, local links, JavaScript errors and failed requests on load | — |
| **Code security** | credential patterns, markup sinks (`innerHTML` and kin), bandit, pip-audit, front-end JavaScript from a CDN or kept in the repo (OSV and Retire.js), unpinned requirements and workflow actions, third-party hosts each page contacts, Pages on a private repo, live response headers; every item tagged with its OWASP Top 10:2025 category and ASVS 5.0.0 chapter | every sink traced to its data, plus [a checklist](skills/explorer-checks/references/security-review.md) |
| **Accessibility** | axe-core against WCAG 2.2 A/AA in headless Chromium, 320 px reflow, focus visibility | the AA criteria axe cannot settle, in [a checklist](skills/explorer-checks/references/wcag-manual-review.md) |

The tools do the half they can. Claude does the other half: it traces each
place data becomes markup, reads the page, tabs through it, and looks at it
at 320 px and 200% zoom. A check passes only when both halves are complete.

Each run produces three things:

- **A report**, `security-accessibility-checks.md`, written into a local
  checkout of the explorer and pushed to its repository, in a pull
  request, when you say so. While anything is open, it lists each item with a
  recommended fix: the file, the element and the change. Finding ids are
  stable, so each report also lists what was fixed since the last one.
- **Fixes**, if you want them, one commit per check.
- **A statement on the explorer's page**, once all three checks pass:

  > Meets WCAG 2.2 Level AA accessibility (and WCAG 2.1 AA and 2.0 AA),
  > checked November 3, 2026 by automated tests and manual review.

  The statement names the accessibility standards and the date checked.
  Security and code validity must pass too, but are not published on the
  page. It does not link
  to the report: the report is filed in the explorer's repository for your
  review, as the tool's output, and is not part of the page. The report's "Standards met" section says how they were checked
  and that this is a self-assessment: automated tools plus a code review
  find most problems, not all of them, and testing with people who use
  assistive technology is still worth doing. A later run that stops
  passing removes the statement.

  You choose how it's added: Claude puts it at the **bottom** (in the
  footer) or the **top** (first in the main content, below the header),
  or gives you the code and its exact place to **paste it in yourself**.
  It's set in small print, held between 10 and 12 points.

**Re-run it at any time**: after fixes, after any change to the explorer,
or to re-date a passing report. A re-run updates the same report, the same
branch and the same pull request.

## It asks before changing anything

The explorer is usually someone else's, and the person running the skill
may not be its owner. So the skill works in a local checkout and asks at
each step that reaches anyone else:

1. It checks the explorer and writes the report **locally**, then shows
   you the result: the status, every must-fix item in plain words with
   its fix, and what it could not check.
2. It asks what you want next: **apply the fixes**, **push the report as
   it stands** for the owners to fix, or **stop** with nothing changed
   upstream.
3. If it applies fixes, it re-runs and shows you the new report before
   asking again.
4. On a pass, it shows you the wording of the page statement and asks
   before adding it, and whether it goes at the **top** of the page or the
   **bottom**.
5. Before any push, it says what will go (branch, commits, repository) and
   waits for a yes. Then it opens the pull request, or updates the
   existing one.
6. It ends by handing over. **Review and merge are yours, or the
   owners'**: read the diff, check the fixes on the page, and merge. The
   skill never merges and never pushes to `main`.

A yes covers one step, not the rest of the run.

## Install

Internet Archive staff can clone the mirror, named
`accessibility-security-checker`, in the internetarchivecanada organization:

```bash
git clone https://github.com/internetarchivecanada/accessibility-security-checker.git
cd accessibility-security-checker
```

The mirror's code is read-only and follows `main` of the source
repository, [Robin-IA/ia-explorer-checks](https://github.com/Robin-IA/ia-explorer-checks),
so open pull requests there. Staff feedback goes to the mirror's own
issues, through the [feedback form](https://github.com/internetarchivecanada/accessibility-security-checker/issues/new?template=feedback.yml), where only
Internet Archive staff can see it. Anyone outside the organization can
open an issue on the source repository, which is public.

**[SETUP.md](SETUP.md)** covers the rest: Python 3.10 or newer (3.12 or
newer recommended), the packages in their own virtual environment, and the
browser. Point Claude at it, or in short:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
.venv/bin/python check_setup.py
.venv/bin/python install.py
```

`check_setup.py` lists anything missing, with the fix. `install.py`
copies the skill to `~/.claude/skills/explorer-checks/` and records which
Python ran it, so the skill runs its checks with the same environment.
Run it again after pulling changes; `install.py --check` says whether
that's needed.

## Run it

In Claude Code, from any directory, give it the explorer's GitHub URL or
its live URL:

> Run explorer checks on https://github.com/internetarchivecanada/federal-pandemic-record-covid19

or, after fixes or changes:

> Re-run the explorer checks on federal-pandemic-record-covid19

Asking to check or audit an explorer's accessibility, WCAG compliance,
security or code quality also starts it. Claude clones the explorer into
`~/explorer-checks/<repo>/` and goes from there.

The scripts also run on their own, which is useful for a quick look at a
checkout. They produce findings only, with no review, report or
pull request:

```bash
.venv/bin/python skills/explorer-checks/scripts/run_checks.py <checkout> --page mockup/
```

## How a run works

[SKILL.md](skills/explorer-checks/SKILL.md) is the procedure Claude
follows. In short:

1. **Check out** the explorer locally on branch `explorer-checks`, from an
   up-to-date `main`, or the existing branch on a re-run.
2. **Run** `run_checks.py` against every view of the page. It writes
   `findings.json`, where each finding is `fail`, `review` (a tool cannot
   decide) or `advisory`.
3. **Review**: Claude resolves every `review` item, works both checklists
   in the browser, and adds what the tools missed, in `review.json`.
4. **Report**: `render_report.py` writes the report into the local
   checkout, and Claude shows you what needs fixing.
5. **Fix and re-run** if you say so.
6. **On a pass**, and if you say so, `add_page_note.py` adds the
   statement, at the top of the main content or in the footer as you
   choose, and one more run confirms the page still passes with it.
7. **Push and open the PR** when you say so, then hand over for review
   and merge.
8. **Or file issues** instead of a PR: one per must-fix item, each asked
   about first, labelled `checker`, `bug`, `fix` and `accessibilitysec`, with an
   **Instructions for Claude** section for whoever fixes it.
9. **Write a validation report**, `explorer-validation-report.md`: what
   each finding is, and whether it is accessibility, security, code
   validity, or a missing best-practice element.

A check passes only with no `fail` items, no unresolved `review` items and,
for security and accessibility, a completed manual checklist. A tool that
did not run produces a finding, so it cannot pass silently.

## Example

The Federal Pandemic Record explorer has a passing report:
[security-accessibility-checks.md](https://github.com/internetarchivecanada/federal-pandemic-record-covid19/blob/main/security-accessibility-checks.md).
It is the first full run, from the first report (not passing) on
1 November 2026, through the fixes, to passing on 3 November. It was
re-run on 5 November after each change to the page. The page carries the
dated note, and the report shows the finished form: standards met, the
completed manual checklists, the sinks cleared on review and why, and
what was fixed between runs. It arrived through
[internetarchivecanada/federal-pandemic-record-covid19#7](https://github.com/internetarchivecanada/federal-pandemic-record-covid19/pull/7),
and the later re-runs came in with the changes that prompted them.

[examples/covid19-trial-2026-10-30.md](examples/covid19-trial-2026-10-30.md)
is the earlier trial run against the same explorer's mockup at commit
`b88bae6d66`. Its manual review is partial (security in full,
accessibility on the keyboard and labelling items only), so it shows a
report that is not passing, not a complete audit. It was never pushed to
that repository.

## What the checks draw on

### Standards

| Resource | Used for |
|---|---|
| [WCAG 2.2](https://www.w3.org/TR/WCAG22/) (W3C Recommendation), with [Understanding WCAG 2.2](https://www.w3.org/WAI/WCAG22/Understanding/) and the [quick reference](https://www.w3.org/WAI/WCAG22/quickref/) | The accessibility standard, Level A and AA. The [manual checklist](skills/explorer-checks/references/wcag-manual-review.md) is organized by success criterion. |
| WCAG 2.1 and 2.0 | Met by meeting 2.2, apart from 4.1.1 Parsing, which the validity check covers. |
| [Section 508](https://www.section508.gov/develop/applicability-conformance/) and [EN 301 549](https://www.etsi.org/deliver/etsi_en/301500_301599/301549/03.02.01_60/en_301549v030201p.pdf) clause 9 | Named in a passing report. They adopt WCAG 2.0 AA and 2.1 AA for web content, so the checks need nothing extra for them. |
| [OWASP Top 10:2025](https://top10.owasp.org/2025/) | The risk category (`A01`–`A10`) on every security finding and checklist item. |
| [OWASP ASVS 5.0.0](https://github.com/OWASP/ASVS/releases/tag/v5.0.0_release) | The chapter (`V1`–`V17`) on every security finding and item. Chapters rather than requirement numbers, because the numbers move between versions. A report states that this is not an ASVS verification at any level. |
| [OWASP AISVS](https://github.com/OWASP/AISVS) 1.0 | The chapter on the AI items in the security checklist. |
| [CWE](https://cwe.mitre.org/) | The weaknesses behind some security rules (for example CWE-79 cross-site scripting and CWE-798 hard-coded credentials). |

### Guidance behind the recommended fixes

| Resource | Used for |
|---|---|
| [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) | Fixes for XSS, DOM XSS, CSP, SSRF, CSRF and file upload in the [security checklist](skills/explorer-checks/references/security-review.md). |
| [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/) | Which response headers the live-site check looks for, and their recommended values. |
| [Mozilla HTTP Observatory](https://developer.mozilla.org/en-US/observatory) | A reference for what counts as passing on headers. |

### Tools the checks run

| Tool | Check |
|---|---|
| [axe-core](https://github.com/dequelabs/axe-core), pinned in `AXE_VERSION` in `check_browser.py`, run in headless Chromium through [Playwright](https://playwright.dev/python/) | Accessibility, plus JavaScript errors and failed requests on load |
| [html5lib](https://github.com/html5lib/html5lib-python) | HTML parsing (validity) |
| [ruff](https://docs.astral.sh/ruff/) | Python errors (validity) |
| [bandit](https://github.com/PyCQA/bandit) | Python security |
| [pip-audit](https://github.com/pypa/pip-audit) | Known vulnerabilities in Python dependencies |
| [OSV.dev](https://osv.dev/) and [Retire.js](https://github.com/RetireJS/retire.js) | Known vulnerabilities in front-end JavaScript from a CDN or kept in the repository |

Minimum versions are in [requirements.txt](requirements.txt).
[watch/sources.md](watch/sources.md) lists the feeds that are read each
week to keep all of this current. It also has a table of where each pinned
version and cited standard lives in the code.

## Keeping the checks current

Every Monday, a scheduled task in the maintainer's Claude desktop app
reads the sources in
[watch/sources.md](watch/sources.md): OWASP standards, vulnerability feeds,
reference scanners, axe-core and WCAG. It compares what changed against what
the checks pin and cite. Each change the checks need becomes an issue
labelled `watch`. The task does not edit the checks itself. To watch
something else, add it to that file.

[watch/watch-history.md](watch/watch-history.md) records each run: the
date, the window, every source read or not read, and the issues that came
of it. The task adds its entry in a pull request of its own, and manual
checks are recorded there too.

Installing the skill does not install the watch. You get the checks as
of your last pull, so pull and re-run `install.py` to pick up what the
watch has changed.

## Tests

```bash
.venv/bin/python -m pytest
```

## Credits

Built by Robin Fay, Project Manager, Digital Collections, Democracy's
Library.

### How it was built

Robin built it with [Claude Code](https://claude.com/claude-code), working
with Claude Opus 5.5, between 30 October and 5 November 2026. Robin
decided what the checks should cover, chose the standards, and reviewed
and merged every change. Claude wrote the code, the checklists and the
documentation. Each commit names Claude as co-author.

It is a Claude Code skill, in three parts:

- **A procedure**, [SKILL.md](skills/explorer-checks/SKILL.md), that Claude
  follows on each run.
- **Python scripts** for the automated half: they run the tools, collect
  findings, write the report and add the page note.
- **Two checklists**, for the half only a reader can do.

It was built against a real explorer,
[federal-pandemic-record-covid19](https://github.com/internetarchivecanada/federal-pandemic-record-covid19).
Each run on it showed something the skill missed or got wrong: views the
browser never opened, a content security policy that blocked axe, a
"fixed" list that vanished on a second render, a page with no `<footer>`.
Each became a fix and a test here, until that explorer passed.

Every change after the first commit came through a pull request from a
branch, with the tests run before it was merged. Some came from the
weekly watch (see [Keeping the checks current](#keeping-the-checks-current)).
Its first run found four, among them an axe-core four minor releases out
of date and front-end JavaScript that nothing was checking.
