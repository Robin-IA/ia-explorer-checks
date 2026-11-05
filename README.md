# Explorer checks

A Claude Code skill that checks an Internet Archive explorer (a Wayback or
archive.org collection explorer such as
[federal-pandemic-record-covid19](https://github.com/internetarchivecanada/federal-pandemic-record-covid19))
three ways:

| Check | Automated | Reviewed by Claude |
|---|---|---|
| **Code validity** | HTML parsing (html5lib), JSON, Python (ruff), the project's own tests, local links, JavaScript errors and failed requests on load | — |
| **Code security** | credential patterns, markup sinks (`innerHTML` and kin), bandit, pip-audit, front-end JavaScript from a CDN or kept in the repo (OSV and Retire.js), unpinned requirements and workflow actions, third-party hosts each page contacts, Pages on a private repo, live response headers; every item tagged with its OWASP Top 10:2025 category and ASVS 5.0.0 chapter | every sink traced to its data, plus [a checklist](skills/explorer-checks/references/security-review.md) |
| **Accessibility** | axe-core against WCAG 2.2 A/AA in headless Chromium, 320 px reflow, focus visibility | the AA criteria axe cannot settle, in [a checklist](skills/explorer-checks/references/wcag-manual-review.md) |

It writes `security-accessibility-checks.md` into the explorer's repository,
on a branch, with a pull request. While anything is open, the report lists
each item with a recommended fix. Re-run after fixing, as often as it takes.
Once all three checks pass, the skill adds a dated note to the explorer's
page that links to the report:

> Meets WCAG 2.2 Level AA accessibility (and WCAG 2.1 AA and 2.0 AA),
> checked 3 November 2026 by automated tests and manual review. Also passes
> security and code validity checks. Read the report.

The note names the standards and the date checked. The report's "Standards
met" section says how, and that it is a self-assessment: automated tools
plus a code review find most problems, not all of them, and testing with
people who use assistive technology is still worth doing. A later run that
stops passing removes the note.

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

Once a week, a scheduled Claude Code task reads the sources in
[watch/sources.md](watch/sources.md): OWASP standards, vulnerability feeds,
reference scanners, axe-core and WCAG. It compares what changed against what
the checks pin and cite. Each change the checks need becomes an issue
labelled `watch`. The task does not edit the checks itself. To watch
something else, add it to that file.

## Tests

```bash
python3 -m pytest
```
