# Weekly watch: instructions for Claude

The weekly watch workflow (`.github/workflows/weekly-watch.yml`) gives
these instructions to Claude on a GitHub Actions runner, every Monday and
whenever someone starts it by hand from the **Actions** tab. Edit this
file to change what the watch does.

Read the week's security and accessibility news from the sources in
[sources.md](sources.md), decide whether the checks need changing, file one
GitHub issue per change needed, make the changes, record the week, and end
with a summary.

**Permission (Robin Fay, the maintainer, 2026-11-10):** "Merge the watch
list every week … and then update the accessibility-security-checker",
and "No permission needed to push and merge PRs for the accessibility and
security checkers." So this run pushes branches to, and merges its own
pull requests in, this repository. Never push to `main` directly, never
touch any other repository, never edit anything under `.github/`, and
never change the checks beyond what the open `watch` issues call for.

## Setup

- You are in a checkout of `main` on an Ubuntu runner. `gh` is
  authenticated through `GH_TOKEN` for this repository only; Python and
  the packages in `requirements.txt` are installed.
- Read `watch/sources.md`. It lists every source, the endpoint to read,
  and what in the checks each source could change, and has a table of what
  the checks pin and cite. Read those files too.
- Commits are made as `github-actions[bot]`; end every commit message with
  `Co-Authored-By: Claude <noreply@anthropic.com>`.

## Window

Today's date minus 8 days, through today. Look only at changes, releases,
advisories and feed entries dated in that window. The exception is the
first table ("What the checks pin or cite"): compare current pins against
the latest upstream every time, e.g. `AXE_VERSION` against the latest
axe-core release.

## Deciding

A change is needed only when something in the window, or a pin that has
fallen behind, would make the checks wrong, incomplete or out of date for
explorers. Explorers are static sites (HTML, JS, JSON) and small
Flask/SQLite apps on GitHub Pages or a macOS host. What counts:

- a pinned tool version is behind upstream;
- an OWASP or ASVS name or mapping the tags rely on has changed;
- a header recommendation has changed;
- a new cheat-sheet fix should replace one the checklist recommends;
- an exploited or widely relevant vulnerability is in a library explorers
  use that the checks would not catch;
- an exploited Chromium or Chrome bug (CISA KEV) is not yet fixed in the
  Chromium that the pinned Playwright bundles: compare the fixed Chrome
  version with Playwright's listed Browser Versions, and remember a newer
  build is not proof of a fix if it was built before the bug was reported;
- a Git security release whose bugs reach the person cloning explorers;
- a WCAG or axe rule change.

What does not count: an advisory pip-audit already reports; WordPress-only
items; typo commits; general news with no consequence for the checks.

Read the actual source (the commit diff, the release notes, the advisory)
before deciding, never a title alone. If a source will not load, record it
as "not read", never as "no news".

**The watch list is part of what you keep current.** If a source the
checks depend on is missing from `sources.md`, file a `watch` issue to add
it and add it in the fixes pull request like any other change.

## Filing

- First list existing issues:
  `gh issue list --label watch --state all --limit 100`. Do not file a
  duplicate; if an open issue covers it and there is new information,
  comment instead.
- One issue per change. Label `watch`, plus `accessibility` for
  accessibility items.
- Title: the change to make, e.g. "Update axe-core from 4.10.3 to 4.14.0".
- Body: what changed upstream, with the URL and date; what in the checks
  it affects (file and constant or line); the proposed change; for a
  version bump, what to test. End with
  `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
- Write for macOS users. Do not name or quote Internet Archive colleagues.

## Record the run

1. `git switch -c watch-history-<today>` from `main`.
2. Insert this run's entry in `watch/watch-history.md` directly below the
   header, above the newest entry: `## <today>: weekly task (GitHub
   Actions)` (or `manual run (GitHub Actions)` when the workflow was
   started by hand; the workflow tells you which), a line with the window,
   then a table with one row per source in `sources.md`: Source | Result
   (`read:` with what was there, or `not read:` with why) | Outcome (the
   issue or comment it led to, linked, or `none`). Do not edit earlier
   entries.
3. Commit only that file ("Watch history: <today>"), push, open a pull
   request against `main` ending with the Generated line, and merge it
   (`gh pr merge <n> --merge --delete-branch`).

If an earlier history pull request is still open, merge it first if it
merges cleanly; otherwise base nothing on it and say so in the summary.

## Make the changes

For each `watch` issue open after this run (this week's and older ones):

1. Decide whether the change is clear and contained: a version citation, a
   checklist item, a pin bump the tests cover, a watch-list source. If it
   needs a decision from the maintainer (a behaviour change to the
   scripts, a new tool, an upgrade whose fix is uncertain), leave the
   issue open, comment why (unless an earlier comment already says so and
   nothing has changed), and list it in the summary. Do not guess.
2. `git switch main && git pull --ff-only && git switch -c
   watch-<today>-fixes`. Make each change as **one commit per issue**,
   its message ending with `Fixes #<n>` and the Co-Authored-By line. Bump
   `skills/explorer-checks/VERSION` to today's date with dots plus `.1`
   (or the next number if today's already exists) when the skill changes.
3. Run `python -m pytest -q tests`. If anything fails, stop: push the
   branch, open the pull request, do not merge it, and say so.
4. In the same branch, add the week's entry to `UPDATE-HISTORY.md` (format
   in its header): **Watch review** (the run, the issues filed, the history
   entry), **Changes** (this pull request and the issues it closes),
   **VERSION**, and **Mirror**: "copied by the mirror workflow". Add the
   entry **even when nothing changed** ("Watch review: nothing to
   change"); then the branch carries only that entry.
5. Push, open the pull request (one row per commit in the body, ending
   with the Generated line), and merge it.

The internetarchivecanada mirror copies `main` by its own workflow; do not
try to push to it.

If a push or merge is refused, stop there, leave everything open, and say
exactly what is waiting.

## Summary

End with a short summary, which the workflow shows on the run's page:

1. the issues filed, each with its title and URL, plus comments added;
2. sources read with nothing that needs a change, in one line;
3. sources not read, and why;
4. the window used;
5. the history pull request, and that it was merged;
6. the changes made (the fixes pull request, the issues it closed, the
   new VERSION), and any `watch` issues left open, with why.

If nothing needs changing, say so plainly, still listing what was read
and what was not.
