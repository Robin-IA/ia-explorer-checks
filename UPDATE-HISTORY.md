# Update history

What changed in the checker, when, and why: each week's **watch review**,
and every change made to the checks. Newest first. Entries are added, never
edited.

- The **watch review** is the weekly reading of standards and security
  feeds ([watch/sources.md](watch/sources.md)); what it read, source by
  source, is in [watch/watch-history.md](watch/watch-history.md). This file
  records that it happened and what came of it.
- **Changes** list each merged pull request, the issues it closed, and the
  skill's `VERSION` afterwards.
- **Mirror**: this repository is developed at
  [Robin-IA/ia-explorer-checks](https://github.com/Robin-IA/ia-explorer-checks)
  and copied to
  [internetarchivecanada/accessibility-security-checker](https://github.com/internetarchivecanada/accessibility-security-checker)
  with `sync_mirror.py` after every merge, so both show the same history.
  Each entry says whether the mirror was synced.

## 2026-11-11: the watch moves to GitHub Actions

**Watch review.** No review this entry. The weekly watch now runs as a
GitHub Actions workflow instead of a scheduled task on the maintainer's
computer: Mondays at 05:00 UTC, and from the Actions tab at any time. Its
instructions moved into the repository (`watch/weekly-watch-prompt.md`).
The internetarchivecanada mirror copies `main` by its own workflow every
six hours.

**Changes**

- this PR: `.github/workflows/weekly-watch.yml`,
  `.github/workflows/mirror.yml`, `watch/weekly-watch-prompt.md`; README.

**VERSION** unchanged (2026.11.10.5): the skill did not change.

**Mirror** synced by hand, since the mirror workflow cannot copy
workflow files.

## 2026-11-10: weekly watch

**Watch review.** Weekly run, window 2026-11-02 to 2026-11-10: three
issues filed. #41 and #42 follow Git's security release (CVE-2026-111760,
recursive clones can run code, and five more); #43 follows CISA's listing
of CVE-2026-125350, an exploited Chromium bug, in the browser the checks
run. See the history entry (#44, merged).

**Changes**

- this PR: never clone or update an explorer's submodules (closes #41).
- Left open for a decision: #42 (minimum Git: Homebrew still has 2.56.0,
  which is not fixed) and #43 (no Playwright release has a Chromium
  confirmed to fix CVE-2026-125350).

**VERSION** 2026.11.10.5. **Mirror** synced after merge.

## 2026-11-10: Git added to the watch list

**Watch review.** Git's security release of 2026-11-10 (Git 2.56.1 and
backports to 2.50.2; CVE-2026-111760, recursive clones can run code)
affects the Git that clones explorers, and the watch did not read Git. The
watch list now reads Git's security advisories (this PR). Changes the
advisory calls for are left to the next watch run.

**Changes**

- this PR: watch Git's security advisories.

**VERSION** unchanged (2026.11.10.4): the watch list is not part of the skill.

**Mirror** synced after merge.

## 2026-11-10

**Watch review.** The weekly run of 2026-11-09 filed #29, #30 and #31; its
history entry was merged (#32). A manual check of Chrome's 2026-11-09
stable update (157.0.8103.50; CVE-2026-125350 exploited in the wild) found
that the watch did not read the browser the checks run (Chromium
156.0.8078.4, from Playwright 1.64.1); the watch list now reads Playwright
releases and counts Chromium entries in CISA KEV (#38). Playwright 1.65's
Chromium was built before the bug was reported, so no upgrade yet.

**Changes**

- #39: the three watch issues of 2026-11-09:
  - cite AISVS 1.01, and a model's output never gates a write on its own
    (closes #29);
  - SSRF item: normalize IPv4-mapped and NAT64 addresses before comparing
    (closes #30);
  - the manual WCAG checklist now covers every WCAG 2.2 Level A and AA
    criterion, including 1.4.13 Content on hover or focus, so the report's
    "every criterion" statement holds (closes #31).
- #38: watch the checks' own browser.
- #37: label issues `accessibilitysec`; one pull request after a design
  check; suggestions are labelled `suggestion`, not `bug`.
- #36: point explorer checks to the explorer design checker first.
- #35: file issues with Instructions for Claude; write
  `explorer-validation-report.md`; drop the closing feedback prompt.
- #34: dates in US English ("November 9, 2026").

**VERSION** 2026.11.10.4. **Mirror** synced after merge.

## 2026-11-09

**Watch review.** Weekly run, window 2026-11-01 to 2026-11-09: three
issues filed (#29, #30, #31); see the history entry (merged 2026-11-10,
#32).

**Changes**

- #33: the page note states accessibility only, not security or code
  validity.

**VERSION** 2026.11.09.1. **Mirror** synced.

## 2026-11-05 to 2026-11-06

**Watch review.** Manual check while writing the README's sources (added
OWASP AISVS to the watch list, #13); the watch history file started (#15).

**Changes**

- #10: CSS is its own context when clearing an XSS sink; SameSite must be
  set explicitly (closes #7, #8, from the 2026-11-03 watch).
- #11: check CDN and vendored JavaScript against known advisories (closes
  #6, from the 2026-11-03 watch).
- #12, #20, #22, #27: the page note stays where the owner put it, can go
  at the top or the bottom or be pasted by hand, is 10–12 pt, and does not
  link the report.
- #13, #14, #16, #17, #18, #21, #24–#26, #28: README, START-HERE and SETUP:
  purpose, sources, first-run recipe, setup check, credits, and the mirror.
- #19, #23: the mirror is `accessibility-security-checker`; staff feedback
  goes to its issues.

**VERSION** 2026.11.05.6. **Mirror** synced.

## 2026-11-03 to 2026-11-04

**Watch review.** First weekly run, window 2026-10-26 to 2026-11-03: four
issues filed (#5–#8).

**Changes**

- #1: the explorer-checks skill.
- #2: name an empty mirror instead of counting from it.
- #3: map the security checks to OWASP Top 10:2025 and ASVS 5.0.
- #4: the weekly watch list.
- #9: axe-core 4.10.3 to 4.14.0 (closes #5).

**Mirror** first synced.
