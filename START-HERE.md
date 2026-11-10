# Start here

> **Already set up? [Start the Skill here](#2-choose-your-situation)** (or
> using the Claude app's **Code** tab, type `/explorer-checks` and your
> project's GitHub address)

**The accessibility and security checker looks at your website, such as
an explorer, and tells you whether its code is valid, whether it is
secure, and whether people using a keyboard, a screen reader or a small
screen can use it (WCAG 2.2 Level AA). You run it on your own project:
before you publish it, to catch problems first, or after, to check what is
already live. It writes a report of everything to fix, with the fix, and
asks before it changes anything.**

This is meant to be a turnkey process to leverage tools to check for
accessibility and security issues. Once set up, you just chat with Claude!

- **This page** is the recipe. Follow it top to bottom the first time.
- **[README.md](README.md)** is the reference: what each check covers and
  the standards and tools behind it.
- **[SKILL.md](skills/explorer-checks/SKILL.md)** is the procedure Claude
  follows.
- **[Feedback form](https://github.com/internetarchivecanada/accessibility-security-checker/issues/new?template=feedback.yml)**:
  tell us about a problem or a suggestion.

## Contents

1. [Set up, once](#1-set-up-once)
2. [Choose your situation](#2-choose-your-situation)
3. [What comes back](#3-what-comes-back)
4. [Fixes, the pull request, and merging](#4-fixes-the-pull-request-and-merging)
5. [Every time after the first](#5-every-time-after-the-first)
6. [When something goes wrong](#6-when-something-goes-wrong)
7. [Where things are](#7-where-things-are)

---

## 1. Set up, once

**Follow [SETUP.md](SETUP.md).** It takes you from a Mac with nothing
installed to one that's ready: Claude and GitHub, the latest Python, the
checker's own packages and browser, and a check that everything is there.

The quickest way is to let Claude do it. Clone this repository (SETUP.md,
step 0 says how), open it as the project folder in Claude Desktop's
**Code** tab, and ask:

> Read SETUP.md and set me up. Run `check_setup.py` first, and ask me before each install.

You're ready when `check_setup.py` ends with **"Everything the checks
need is here."** Every repository with a skill has its own SETUP.md,
because each one needs different software.

## 2. Choose your situation

You run the checker on **your own** project. Claude needs its GitHub
address. You don't connect the project to the checker: Claude reaches it
through your GitHub sign-in, so it can check any repository you can see.

**No project of your own yet?** Practise on the public Federal Pandemic
Record explorer,
`https://github.com/internetarchivecanada/federal-pandemic-record-covid19`.
When Claude asks what to do at the end, choose **Stop**, so nothing is
sent to someone else's repository.

### A. My website is already published

Start a new session in the **Code** tab. Type `/explorer-checks`, then a
space, then your project's addresses: the GitHub repository, and the live
page so the checks can read the live site's security headers:

> /explorer-checks https://github.com/internetarchivecanada/my-explorer, live at https://internetarchivecanada.github.io/my-explorer/

If `/explorer-checks` doesn't come up when you type `/`, ask in plain
words instead: "Run explorer checks on …". If neither works, the skill is
not installed or not up to date: finish [SETUP.md](SETUP.md) (section 1).

### B. My website is not published yet

Check it **before** you publish, as the last step before it goes live.

**Nothing has to be public to be checked.** Claude copies the repository
to your Mac and serves the pages there, on your own machine. You don't
need to turn on GitHub Pages, and a private repository is fine.

1. Make sure the project is on GitHub, in a private repository if you
   like. If it is only a folder on your Mac, ask Claude: "Connect this
   folder to a new **private** repo in the internetarchivecanada
   organization" (see
   [Start your own new project](https://github.com/internetarchivecanada/ia-admin/blob/main/docs/install-claude-code.md#5-start-your-own-new-project)).
2. Start a new session and give the repository address:

   > /explorer-checks https://github.com/internetarchivecanada/my-explorer — not published yet

3. Fix what it finds (section 4) until it passes.
4. **Then publish.** Once it is live, re-run with the live address
   (situation A). The live site's response headers are the one thing that
   can't be checked before publishing. Those findings are advisory, so the
   re-run doesn't change whether it passes.

**A note on GitHub Pages and private repositories.** On most GitHub plans,
a Pages site is public even when its repository is private, so don't turn
on Pages until you are ready for it to be public. The checks flag a
private repository that serves a Pages site.

### What happens next, in either situation

Claude copies your project to `~/explorer-checks/<repo>/` on your Mac and
runs the automated checks against every view of the page. Then it does
the half no tool can: it reads the code that turns data into markup, tabs
through the page, and looks at it 320 px wide and at 200% zoom. A first
run takes a while.

All of this happens on your Mac. **Nothing reaches your repository yet.**

## 3. What comes back

Claude tells you:

1. **The status**, passing or not, and how many items must be fixed in
   each of the three checks.
2. **Every must-fix item**, one line each: what is wrong, in plain words,
   and the fix. For example: "Search box has no visible label → add a
   `<label for="q">`".
3. **What it could not check**, such as an app that would not start or a
   page behind a login. A check that did not run did not pass.
4. **Where the report is**: `~/explorer-checks/<repo>/security-accessibility-checks.md`.

Then it asks what you want to do next:

- **Apply the fixes.** Claude makes them, one commit per check, re-runs,
  and shows you the new report.
- **Send the report as it stands**, so you, or the project's owners, can
  fix things another way.
- **Stop.** The report stays on your Mac, and nothing changes in your
  repository.

Each yes covers one step. Claude asks again before the next one.

## 4. Fixes, the pull request, and merging

**Fixes.** If you say yes, Claude applies the recommended fixes and checks
the ones that change behaviour (focus, keyboard, contrast) in a browser.
Some decisions aren't Claude's to make, such as removing a feature or
changing a data source. Those stay in the report for you.

**Passing.** A check passes when nothing must be fixed, every item a tool
could not decide has been resolved, and the manual checklist is complete.
When all three pass, Claude shows you the statement it would put on your
page, and asks before adding it:

> Meets WCAG 2.2 Level AA accessibility (and WCAG 2.1 AA and 2.0 AA),
> checked November 3, 2026 by automated tests and manual review.

The statement does not link to the report. The report is filed in your
explorer's repository for your review, as the tool's output.

You choose how it's added:

- **Bottom**: Claude puts it in the page's footer.
- **Top**: Claude puts it as the first thing in the main content, below
  the header.
- **I'll paste it in myself**: Claude gives you the code, the file, and
  exactly where it goes ("directly after the line `<main id="content">`").
  You paste it into your own copy, save, commit, and then ask Claude to
  re-run so the report confirms the page still passes with it.

At the top or the bottom, the statement is in small print, between 10 and
12 points, so it's noticeable without crowding the page, and it still
grows when a reader enlarges text. You can move it later by asking
Claude.

**The pull request.** Before anything goes to GitHub, Claude tells you
what will go: the branch, the changes, the repository. On your yes, it
sends a branch called `explorer-checks` to your repository and opens a
**pull request**: a proposed change that waits for someone to accept it.
The report goes in the pull request as a file, along with any fixes and
the page statement (unless you're pasting the statement in yourself), so
there is one thing to review. You need permission
to make changes in the repository. If you don't have it, ask its owners.

**Merging: getting the changes into your explorer.** Claude never merges.
That's yours to do, or the owners':

1. Open the pull request link Claude gives you.
2. Read the **Conversation** tab, then **Files changed** to see each
   change. `security-accessibility-checks.md` is the report.
3. If your project is published from `main` (GitHub Pages usually is),
   merging publishes the changes. To look first, ask Claude: "Serve the
   `explorer-checks` branch so I can look at it in the browser."
4. Click **Merge pull request**, then **Confirm merge**. If it isn't your
   project, add the owners as reviewers instead and let them merge.
5. Something changed on `main` after the check? Re-run (section 5) before
   merging. A report describes the version it checked.

## 5. Every time after the first

**Re-run** at any time: after fixes, after any change to the site, before
each publication, or to re-date a passing report:

> /explorer-checks re-run on my-explorer

A re-run updates the same report, branch and pull request, and lists what
was fixed since last time.

**Keep the checker up to date.** The checks are kept current with new
standards and new vulnerabilities. Every few weeks, ask Claude in the
`accessibility-security-checker` project folder:

> Update the checker: follow SETUP.md, section 6.

That pulls the latest checks, updates Python and the packages, and
reinstalls the skill if it changed.

## 6. When something goes wrong

| What you see | What to do |
|---|---|
| "Repository not found" | You are not in the `internetarchivecanada` organization yet, or the project's address is wrong. See [Get a GitHub account](https://github.com/internetarchivecanada/ia-admin/blob/main/docs/github-account.md). |
| "GitHub CLI authentication required" | Click **Install and authenticate**, then **Authorize**. |
| Anything about Python, packages, Chromium, `gh` or certificates | Ask Claude: "Run `.venv/bin/python check_setup.py` and fix what it reports, following SETUP.md." [SETUP.md, section 7](SETUP.md#7-when-something-goes-wrong) lists each error and its fix. |
| A report item starting `tool:` | A checker did not run, for example with no network. The check can't pass until it does. Fix the cause and re-run. |
| Claude says an app would not start | Explorers that are Flask apps need their own setup. Start the app as its README says, then re-run. The report says what it couldn't check. |
| Pushing fails with "permission denied" | You can't make changes in that repository. Ask its owners for write access, or choose **Stop** and send them the report. |
| `/explorer-checks` doesn't come up | In `~/projects/accessibility-security-checker`, run `.venv/bin/python install.py`, then start a new Claude session. |

**Feedback, or a problem with the checker?** Use the
**[feedback form](https://github.com/internetarchivecanada/accessibility-security-checker/issues/new?template=feedback.yml)**.
It takes a minute: what happened or what you'd like, and optionally your
name, email and the project you were checking. It opens an issue on
[the mirror in `internetarchivecanada`](https://github.com/internetarchivecanada/accessibility-security-checker/issues),
where only Internet Archive staff can see it, and goes straight to the
maintainer. Still leave out passwords and tokens.

## 7. Where things are

| What | Where |
|---|---|
| The checker | `~/projects/accessibility-security-checker` |
| The installed skill | `~/.claude/skills/explorer-checks` |
| Projects you have checked | `~/explorer-checks/<repo>/` |
| The report for one project | `~/explorer-checks/<repo>/security-accessibility-checks.md` |
| The security checklist | [skills/explorer-checks/references/security-review.md](skills/explorer-checks/references/security-review.md) |
| The accessibility checklist | [skills/explorer-checks/references/wcag-manual-review.md](skills/explorer-checks/references/wcag-manual-review.md) |
| A finished, passing report | [Federal Pandemic Record](https://github.com/internetarchivecanada/federal-pandemic-record-covid19/blob/main/security-accessibility-checks.md) |
