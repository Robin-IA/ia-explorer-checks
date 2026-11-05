# Watch history

What was consulted to keep the checks current, when, and what came of it.
Newest first. [sources.md](sources.md) says what to read; this file says
what was read.

Each entry gives the date, who ran it (the weekly task or a manual
check), the window, and one row per source:

- **read**: read, with what was there.
- **not read**: did not load or was skipped, with why. Not the same as
  "no news".

Issues filed are linked from the row that led to them. Entries are added,
never edited.

## 2026-11-05: manual check

While writing the README's list of sources. Not a full watch: only the
sources below.

| Source | Result | Outcome |
|---|---|---|
| Every resource linked from the README's "What the checks draw on" | read: all returned 200 | `OWASP/ASVS/releases/tag/v5.0.0` returned 404; the release tag is `v5.0.0_release`, and the README links that |
| [OWASP AISVS](https://github.com/OWASP/AISVS) releases | read: v1.0 and v1.01, both 2026-10-16 | The security checklist cites 1.0. Nothing read AISVS, so it was added to [sources.md](sources.md) ([#13](https://github.com/Robin-IA/ia-explorer-checks/pull/13)), and the next weekly run should raise the version |

## 2026-11-03: weekly task

Window 2026-10-26 to 2026-11-03. First run.

| Source | Result | Outcome |
|---|---|---|
| axe-core releases | read: 4.14.0 (2026-10-05); the checks pinned 4.10.3 | [#5](https://github.com/Robin-IA/ia-explorer-checks/issues/5) Update axe-core from 4.10.3 to 4.14.0 |
| Retire.js | read: DOMPurify advisories below 3.4.17 (2026-10-29), Highcharts batch (2026-10-30) | [#6](https://github.com/Robin-IA/ia-explorer-checks/issues/6) Check CDN and vendored JavaScript versions against known advisories |
| OWASP Cheat Sheet Series | read: XSS cheat sheet's CSS-context rewrite and CSRF cheat sheet's SameSite correction (both 2026-11-01); other commits were links, dependency bumps and cloud or C guidance | [#7](https://github.com/Robin-IA/ia-explorer-checks/issues/7) Treat CSS contexts separately when clearing an XSS sink; [#8](https://github.com/Robin-IA/ia-explorer-checks/issues/8) Require SameSite to be set explicitly |
| OWASP Top 10 | read: no commits in the window | none |
| OWASP ASVS | read: a Persian translation and a rebuild of the unstable "latest" release; v5.0.0 still the stable release | none |
| OWASP Secure Headers | read: statistics syncs only | none |
| MDN blog feed | read: no entries in the window | none |
| W3C WAI feed | read: no entries in the window | none |
| WCAG | read: wording edits to Understanding 2.5.8, 3.3.2 and 4.1.2; no errata | none |
| Mozilla HTTP Observatory | read: 1.7.2, a redirect-handling fix; no scoring change | none |
| GitHub Advisory Database (pip, npm) | read: nothing in the explorer stack beyond the Highcharts batch | covered by #6 |
| CISA KEV | read: nothing in the explorer stack | none |
| `requirements.txt` floors | read: minimum versions, none below the floor | none |
| Wordfence | not read: HTTP 202 bot challenge; WordPress only | — |
| securityheaders.com | not read: HTTP 403 | — |
| SSL Labs | not read: a test form with no news; TLS is left to the host | — |
| OSV.dev | not read: answers only queries for a named package and version, and none was needed | — |
