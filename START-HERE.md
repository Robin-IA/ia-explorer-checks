# Start here

**Explorer checks looks at an Internet Archive explorer and tells you
whether its code is valid, whether it is secure, and whether people using
a keyboard, a screen reader or a small screen can use it (WCAG 2.2 Level
AA). It writes a report listing everything to fix, with the fix, and asks
before it changes anything.**

- **This page** is the recipe. Follow it top to bottom the first time.
- **[README.md](README.md)** is the reference: what each check covers, the
  standards and tools behind it, and how a run works.
- **[SKILL.md](skills/explorer-checks/SKILL.md)** is the procedure Claude
  follows, step by step.

You do not need to be a programmer. Setup takes about 10 minutes the first
time. After that, you ask Claude in plain English.

## Contents

1. [Before you start](#before-you-start)
2. [One-time setup](#one-time-setup)
3. [Checking an explorer](#checking-an-explorer)
4. [What comes back](#what-comes-back)
5. [Fixing, passing and handing over](#fixing-passing-and-handing-over)
6. [Every time after the first](#every-time-after-the-first)
7. [When something goes wrong](#when-something-goes-wrong)
8. [Where things are](#where-things-are)

---

## Before you start

- **A Mac with Claude Code and the command-line tools installed.** If you
  don't have them yet, follow
  [Technical Setup: GitHub, Claude, CLI Tools](https://docs.google.com/document/d/1x5VglCkcNSHvLq-YVyvTxlEEyYqVgNexNtGWucY4wl0/edit?usp=sharing).
- **Membership of the `internetarchivecanada` GitHub organization.** The
  copy of this tool you clone is a private repository there, and so are
  some explorers. If you are not a member, ask an organization admin on Slack for an
  invite, giving your @archive.org address. The invite arrives by email.
- **The GitHub CLI, signed in**, so Claude can open pull requests for you.
  It is only needed at the end, when you choose to push a report.

**Check you are ready.** Open Terminal (**Cmd + Space**, type `Terminal`,
press **Return**) and run:

```bash
claude --version
git --version
python3 --version
gh auth status
```

- The first three print a version number.
- `gh auth status` says you are logged in to github.com. If it doesn't, run
  `gh auth login` and follow the prompts.
- "command not found" means that tool is not installed yet: go back to the
  setup document.

## One-time setup

Copy and run these one at a time. The first two get the tool:

```bash
git clone https://github.com/internetarchivecanada/accessibility-security-checker.git ~/accessibility-security-checker
```

```bash
cd ~/accessibility-security-checker
```

A "Repository not found" error means you are not in the organization yet;
see [Before you start](#before-you-start).

Next, install what the checks run. The second command downloads a copy of
Chromium that the accessibility check drives; it takes a minute or two:

```bash
python3 -m pip install -r requirements.txt
```

```bash
python3 -m playwright install chromium
```

Last, install the skill into Claude Code, so it works from any folder:

```bash
python3 install.py
```

It prints where it installed the skill. Setup is done.

## Checking an explorer

Start Claude Code in any folder:

```bash
claude
```

Then ask for a check, giving the explorer's GitHub address or its live
address:

> Run explorer checks on https://github.com/internetarchivecanada/federal-pandemic-record-covid19

Claude copies the explorer to `~/explorer-checks/<repo>/` on your Mac,
runs the automated checks against every view of the page, and then does
the half no tool can: it reads the code that turns data into markup, tabs
through the page, and looks at it at 320 px wide and at 200% zoom. Expect
a first run to take a while.

All of this happens on your Mac. Nothing reaches the explorer's repository
at this stage.

## What comes back

Claude tells you:

1. **The status**, passing or not, and how many items must be fixed in
   each of the three checks.
2. **Every must-fix item**, one line each: what is wrong, in plain words,
   and the fix. For example: "Search box has no visible label → add a
   `<label for="q">`".
3. **What it could not check**, such as an app that would not start or a
   page behind a login. A check that did not run did not pass.
4. **Where the report is**: `~/explorer-checks/<repo>/security-accessibility-checks.md`.

Then it asks what you want next:

- **Apply the fixes.** Claude makes them, one commit per check, re-runs,
  and shows you the new report.
- **Push the report as it stands**, so the explorer's owners can fix it
  themselves.
- **Stop.** The report stays on your Mac, and nothing has changed in the
  explorer's repository.

Each yes covers one step only. Claude asks again before the next one.

## Fixing, passing and handing over

**Fixes.** If you say yes, Claude applies the recommended fixes and checks
the ones that change behaviour (focus, keyboard, contrast) in a browser.
Some things are not Claude's to decide, such as removing a feature or
changing a data source. Those stay in the report for the owners.

**Passing.** A check passes when nothing must be fixed, every item a tool
could not decide has been resolved by Claude, and the manual checklist is
complete. When all three pass, Claude shows you the statement it would put
on the explorer's page and asks before adding it:

> Meets WCAG 2.2 Level AA accessibility (and WCAG 2.1 AA and 2.0 AA),
> checked 3 November 2026 by automated tests and manual review. Also
> passes security and code validity checks. Read the report.

You choose where it goes: at the **bottom**, in the page's footer, or at
the **top**, as the first thing in the main content, below the header.
You can move it later by asking Claude to.

**Pushing.** Before anything goes to GitHub, Claude tells you what will go:
the branch, the commits, the repository. On your yes it pushes a branch
called `explorer-checks` and opens a pull request.

**Handing over.** The review and merge are yours, or the explorer owners'.
Read the changes, look at the page, and merge. Claude never merges and
never pushes to `main`.

## Every time after the first

**Re-run** after fixes, after any change to the explorer, or to re-date a
passing report:

> Re-run the explorer checks on federal-pandemic-record-covid19

A re-run updates the same report, the same branch and the same pull
request, and lists what was fixed since the last one.

**Update the tool** now and then. The checks are kept current against new
standards and new vulnerabilities, and you get those changes by pulling:

```bash
cd ~/accessibility-security-checker
```

```bash
git pull
```

```bash
python3 install.py --check
```

If it says "out of date", run `python3 install.py` again.

## When something goes wrong

| What you see | What to do |
|---|---|
| "Repository not found" when cloning | You are not in the `internetarchivecanada` organization yet. See [Before you start](#before-you-start). |
| `No module named ...` | Setup was skipped or ran with a different Python. Run the `pip install` line from [One-time setup](#one-time-setup) again. |
| "Executable doesn't exist" about Chromium | Run `python3 -m playwright install chromium`. |
| A report item starting `tool:` | A checker did not run, for example with no network. The check cannot pass until it does. Fix the cause and re-run. |
| Claude says an app would not start | Explorers that are Flask apps need their own setup. The report says what could not be checked. Start the app as its README says, then re-run. |
| `gh` says you are not logged in | Run `gh auth login`. |
| Claude doesn't recognise the request | Run `python3 install.py --check` in `~/accessibility-security-checker`, and install again if it is out of date. |

**Reporting problems.** Open an issue on
[Robin-IA/ia-explorer-checks](https://github.com/Robin-IA/ia-explorer-checks/issues),
the source repository. The copy in `internetarchivecanada` follows it and
does not take issues.

## Where things are

| What | Where |
|---|---|
| This tool | `~/accessibility-security-checker` |
| The installed skill | `~/.claude/skills/explorer-checks` |
| Explorers you have checked | `~/explorer-checks/<repo>/` |
| The report for one explorer | `~/explorer-checks/<repo>/security-accessibility-checks.md` |
| The security checklist | [skills/explorer-checks/references/security-review.md](skills/explorer-checks/references/security-review.md) |
| The accessibility checklist | [skills/explorer-checks/references/wcag-manual-review.md](skills/explorer-checks/references/wcag-manual-review.md) |
| A finished, passing report | [Federal Pandemic Record](https://github.com/internetarchivecanada/federal-pandemic-record-covid19/blob/main/security-accessibility-checks.md) |
