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

## 2026-11-10: weekly task

Window 2026-11-02 to 2026-11-10.

| Source | Result | Outcome |
|---|---|---|
| OWASP Top 10 | read: no commits in the window | none |
| OWASP ASVS | read: one CI dependency bump (2026-11-04); v5.0.0 still the stable release | none |
| OWASP AISVS | read: research folders and wiki references removed (2026-11-08), a level fix (2026-11-04); v1.01 still the latest release, and the checklist cites it since #39 | none |
| OWASP Secure Headers | read: statistics and dashboard syncs only | none |
| OWASP Cheat Sheet Series | read: since the 2026-11-09 run, obsolete HTTP RFC references replaced with RFC 9110 in the CSRF, Error Handling and Session Management sheets (2026-11-10; the checks cite no RFC) and dependency bumps. The SSRF deny-list change is already in the checklist (#30); the other window commits (Docker, Kubernetes, multi-tenant, MCP, LLM prompt injection, NPM, Node.js CSRF, SQLi and LDAP dedup) do not affect the checks | none |
| MDN blog feed | read: no entries in the window (newest 2026-06-15) | none |
| Xygeni: OWASP Top 10 2025 explained | not read: background only, not watched | none |
| GitHub Advisory Database (pip, npm) | read: 28 pip and 34 npm advisories (GPUStack, compose-lint, GeoNode, fastapi-code-generator, node-forge, mongoose, isomorphic-git, Claude Code's Edit tool and others); none in the explorer stack or the tools the checks run | none |
| OSV.dev | not read: answers only queries for a named package and version, and none was needed; `js_libraries.py` queries it live | none |
| Retire.js | read: dojox (2026-11-09) and lodash, next, protobufjs (2026-11-06) updates to `jsrepository.json`, which `js_libraries.py` reads live | none |
| CISA KEV | read: 13 added. CVE-2026-125350, Google Chromium use-after-free in XML (2026-11-10), is the browser the checks run; the rest (Outlook, Openwave, Cisco BroadWorks, Barracuda, GPUStack, OpenSSH, FreeSwitch, Aspera Faspex, SonicWall, Apple, WordPress core) are not on the explorer stack | [#43](https://github.com/Robin-IA/ia-explorer-checks/issues/43) Raise the Playwright floor to one whose Chromium fixes CVE-2026-125350 |
| Wordfence | not read: HTTP 202 bot challenge; WordPress only | none |
| Playwright for Python | read: 1.65.0 (2026-11-09) bundles Chromium 158.0.8127.18; fixed Chrome is 157.0.8103.50, but 158.0.8127.18 was built before CVE-2026-125350 was reported, so not proof of the fix. 1.64.1 bundles 156.0.8078.4, not fixed | covered by [#43](https://github.com/Robin-IA/ia-explorer-checks/issues/43), left open for a decision |
| Git security advisories | read: GHSA-vp2w-7xxj-jvxr, CVE-2026-111760 (2026-11-10), recursive clones can run code; fixed in 2.56.1 and backports 2.50.2 to 2.55.1, with five more CVEs (unborn HEAD path traversal, merge heap overflow and others). Homebrew's `git` is still 2.56.0 | [#41](https://github.com/Robin-IA/ia-explorer-checks/issues/41) Never clone or update explorer submodules; [#42](https://github.com/Robin-IA/ia-explorer-checks/issues/42) Require Git 2.56.1 or a patched backport in SETUP.md |
| Mozilla HTTP Observatory | read: dependency bumps only; no release since 1.7.2; no scoring change | none |
| securityheaders.com | not read: HTTP 403 | none |
| SSL Labs | not read: a test form with no news; TLS is left to the host | none |
| axe-core releases | read: 4.14.0 (2026-10-05) is still the latest, and it matches `AXE_VERSION` | none |
| W3C WAI feed | read: no entries in the window (newest 2026-09-25) | none |
| WCAG | read: no releases. Since the 2026-11-09 run, a typo fix in the touch target explanation (2026-11-09); F114 for 1.4.13 is covered by #31 | none |
| `requirements.txt` floors | read: latest html5lib 1.1, playwright 1.65.0, ruff 0.17.4, bandit 1.9.4, pip-audit 2.10.1, pytest 9.2.0; all above the floors | none |

## 2026-11-10: manual check

After Chrome's 2026-11-09 stable update, which the weekly run of the same
day did not read. Not a full watch: only the sources below.

| Source | Result | Outcome |
|---|---|---|
| [Chrome Releases: Stable Channel Update for Desktop](https://chromereleases.googleblog.com/2026/11/stable-channel-update-for-desktop_018223192.html), 2026-11-09 | read (in a browser: the page's text is built by script and a plain fetch returns none): 157.0.8103.50, 9 security fixes, 7 high; Google says CVE-2026-125350 (use after free in XML) is exploited in the wild | The checks ran Chromium 156.0.8078.4 (Playwright 1.64.1), before the fix. Nothing watched the checks' own browser, so [sources.md](sources.md) now reads Playwright releases and counts Chromium entries in the CISA feed |
| Playwright for Python releases | read: 1.65.0 (2026-11-09) bundles Chromium 158.0.8127.18, built before CVE-2026-125350 was reported (2026-11-06), so it is not proof of the fix | none yet; the next weekly run reads this source |

## 2026-11-09: weekly task

Window 2026-11-01 to 2026-11-09.

| Source | Result | Outcome |
|---|---|---|
| OWASP Top 10 | read: no commits in the window | none |
| OWASP ASVS | read: one CI dependency bump; v5.0.0 still the stable release | none |
| OWASP AISVS | read: v1.01 (2026-10-16) is current, and the checklist and README cite 1.0. Chapter titles are the same in both versions. Window commits removed research folders | [#29](https://github.com/Robin-IA/ia-explorer-checks/issues/29) Cite AISVS 1.01 instead of 1.0 for the AI checklist items |
| OWASP Secure Headers | read: statistics syncs only | none |
| OWASP Cheat Sheet Series | read: SSRF deny-list adds IPv4-mapped IPv6 and NAT64 ranges and says to normalize before comparing (2026-11-08). XSS and SameSite edits of 2026-11-01 were already covered by #7 and #8; "escape every rendered value by default" is already in the checklist. Node.js CSRF, NPM "project you did not write", Docker, Kubernetes, multi-tenant, MCP, LLM prompt injection and SQLi/LDAP dedup do not affect the checks | [#30](https://github.com/Robin-IA/ia-explorer-checks/issues/30) Normalize IPv4-mapped and NAT64 addresses in the SSRF checklist item |
| MDN blog feed | read: no entries in the window (newest 2026-06-15) | none |
| GitHub Advisory Database (pip, npm) | read: 5 pip and 8 npm advisories (GeoNode, stanza, banks, elo, sd-jwt and others); none in the explorer stack | none |
| OSV.dev | not read: answers only queries for a named package and version, and none was needed. `js_libraries.py` already queries it live | none |
| Retire.js | read: new lodash, next and protobufjs advisories (2026-11-06) and a dojox split. `js_libraries.py` reads `jsrepository.json` live, so they are picked up without a change | none |
| CISA KEV | read: three added (SonicWall SSLVPN, Apple CVE-2024-27834, WordPress core); none on the explorer stack the checks cover | none |
| Wordfence | not read: HTTP 202 bot challenge; WordPress only | none |
| Mozilla HTTP Observatory | read: dependency bumps only; no release since 1.7.2; no scoring change | none |
| securityheaders.com | not read: HTTP 403 | none |
| SSL Labs | not read: a test form with no news; TLS is left to the host | none |
| axe-core releases | read: 4.14.0 (2026-10-05) is still the latest, and it matches `AXE_VERSION` | none |
| W3C WAI feed | read: no entries in the window (newest 2026-09-25) | none |
| WCAG | read: no releases. Commits on 2026-11-02 add failure technique F114 for 1.4.13 Content on hover or focus, which the manual checklist does not cover. F13 now also counts as a 1.3.3 failure. Understanding edits to 2.5.8, 3.3.1, 3.3.2, 3.3.9 and 4.1.2 | [#31](https://github.com/Robin-IA/ia-explorer-checks/issues/31) Add 1.4.13 Content on hover or focus to the manual WCAG checklist |
| `requirements.txt` floors | read: latest html5lib 1.1, playwright 1.64.1, ruff 0.17.4, bandit 1.9.4, pip-audit 2.10.1, pytest 9.2.0; all above the floors | none |

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
