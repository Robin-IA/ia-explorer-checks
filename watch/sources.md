# Watch list

What the weekly watch reads to decide whether the checks need changing. Each
source names what to look at and what in this repository it could change.
A change goes in as an issue labelled `watch`; nothing is edited directly.
Each run's sources, results and issues are recorded in
[watch-history.md](watch-history.md).

The watch looks at the eight days before the run, so one late run does not
open a gap. It reads the endpoint given here, not the page, where there is
one: pages change layout, and several of these refuse scripted requests.

## What the checks pin or cite

Compare each source against these before deciding a change is needed.

| In the checks | Where |
|---|---|
| axe-core version | `AXE_VERSION` in `skills/explorer-checks/scripts/check_browser.py` |
| Tool versions (html5lib, playwright, ruff, bandit, pip-audit) | `requirements.txt` |
| The browser the browser check runs | the Chromium bundled with the installed `playwright` (`python3 -m playwright install chromium`), not the user's Chrome |
| OWASP Top 10 and ASVS tags per rule | `OWASP` table in `skills/explorer-checks/scripts/common.py` |
| Security checklist, including the AISVS version and chapters on its AI items | `skills/explorer-checks/references/security-review.md` |
| Accessibility standard and checklist | `STANDARD` in `scripts/render_report.py`, `references/wcag-manual-review.md` |
| Header checks | `check_headers` in `scripts/check_security.py` |
| Credential patterns | `scripts/check_security.py` |

## Checklist and reference standards

| Source | Read | Could change |
|---|---|---|
| [OWASP Top 10:2025](https://owasp.org/Top10/2025/) | commits to [OWASP/Top10](https://github.com/OWASP/Top10): `gh api repos/OWASP/Top10/commits` | category names or CWE lists behind the tags |
| [OWASP ASVS](https://github.com/OWASP/ASVS) | `gh api repos/OWASP/ASVS/releases` and commits | chapter names behind the tags; a new release |
| [OWASP AISVS](https://github.com/OWASP/AISVS) | `gh api repos/OWASP/AISVS/releases` and commits | chapter names behind the AI items in the security checklist (cited as 1.0; v1.01 was released 2026-10-16); a new release |
| [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/) | `gh api repos/OWASP/www-project-secure-headers/commits` | headers to check, recommended values, headers now deprecated |
| [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) | `gh api repos/OWASP/CheatSheetSeries/commits`, then the changed cheat sheets | fixes recommended in the checklist (XSS, DOM XSS, CSP, SSRF, CSRF, file upload) |
| [MDN Web Security](https://developer.mozilla.org/en-US/docs/Web/Security) | [MDN blog feed](https://developer.mozilla.org/en-US/blog/rss.xml) | browser security features and deprecations |
| [Xygeni: OWASP Top 10 2025 explained](https://xygeni.io/blog/owasp-top-10-2025-explained-for-developers/) | background only, not watched | — |

## Vulnerability feeds

Explorers are static sites and small Flask apps. An advisory matters when it
touches something an explorer is likely to use (jQuery, D3, Leaflet,
Chart.js, Bootstrap, Flask, Werkzeug, Jinja2, requests, SQLite) or a tool the
checks run. **The checks' own browser counts:** the browser check loads
explorer pages, and what they pull in, in Chromium, so an exploited Chromium
or Chrome bug is in scope even though no explorer ships a browser. Not every advisory is a change to the checks: one that pip-audit
already reports needs nothing.

| Source | Read | Could change |
|---|---|---|
| [GitHub Advisory Database](https://github.com/advisories) | `gh api "/advisories?ecosystem=pip&published=>=<date>"` and `ecosystem=npm` | a library the checks should flag that pip-audit does not see, such as front-end JavaScript loaded from a CDN |
| [OSV.dev](https://osv.dev/) ([API](https://google.github.io/osv.dev/api/)) | `POST https://api.osv.dev/v1/query` for a named package and version | the same, for a package the GitHub feed does not cover |
| [Retire.js](https://github.com/RetireJS/retire.js) | `gh api repos/RetireJS/retire.js/commits?path=repository/jsrepository.json` | outdated JavaScript libraries; whether the checks should run it on vendored scripts |
| [CISA Known Exploited Vulnerabilities](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) | [JSON feed](https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json), entries with `dateAdded` in the window. Include entries whose `product` is Chromium or Chrome (vendor Google) | anything on an explorer's stack that is being exploited now; for a Chromium entry, whether the Playwright the checks pin has a Chromium with the fix (see [The checks' own browser](#the-checks-own-browser)) |
| [Wordfence Intelligence](https://www.wordfence.com/products/wordfence-intelligence/) ([data feed](https://www.wordfence.com/?p=32739)) | the page, if it loads | WordPress only. No explorer uses WordPress yet; record that it was skipped unless one does |

## The checks' own browser

The browser check drives the Chromium build that Playwright bundles, not an
installed Chrome, so its engine changes only when Playwright does. Chrome's
weekly stable releases are not watched: most are security fixes that change
nothing in the checks. An exploited Chromium bug reaches the watch through
the CISA feed above, and this source says whether a Playwright release
brings a Chromium with the fix.

| Source | Read | Could change |
|---|---|---|
| [Playwright for Python](https://github.com/microsoft/playwright-python/releases) | `gh api repos/microsoft/playwright-python/releases`; each release's notes list its **Browser Versions** | the `playwright` floor in `requirements.txt` and the install step in SETUP.md, when a release brings a Chromium the checks need (a security fix, or one an exploited bug calls for); breaking changes to what the browser check calls |

A Chromium release only fixes a bug from its build onward: a newer major
version is not proof of a fix if it was built before the bug was reported.
When it matters, compare the fixed Chrome version in the advisory with the
version Playwright lists, and say in the issue which it is.

## Reference scanners for benchmarking

Not news. The watch reads their changes for scoring rules the checks should
match.

| Source | Read | Could change |
|---|---|---|
| [Mozilla HTTP Observatory](https://developer.mozilla.org/en-US/observatory) | commits and releases of [mdn/mdn-http-observatory](https://github.com/mdn/mdn-http-observatory), including its scoring rubric | header checks and what counts as a pass |
| [Security Headers](https://securityheaders.com/) | the page, if it loads | header checks |
| [Qualys SSL Labs](https://www.ssllabs.com/ssltest/) | the page, if it loads | TLS, which the checks leave to the host; note only |

## Accessibility

The checks are half accessibility, so the watch reads these too.

| Source | Read | Could change |
|---|---|---|
| [axe-core](https://github.com/dequelabs/axe-core) | `gh api repos/dequelabs/axe-core/releases` | `AXE_VERSION`; rules added, removed or retagged |
| [W3C WAI news](https://www.w3.org/WAI/news/) | [feed](https://www.w3.org/WAI/feed.xml) | the standard named in the report (WCAG 2.2, WCAG 3 drafts) |
| [WCAG](https://github.com/w3c/wcag) | `gh api repos/w3c/wcag/releases` | errata to criteria the checklist cites |

## Endpoint notes

Checked 2026-11-03:

- The Wordfence pages and Security Headers answer scripted requests with a
  bot challenge (HTTP 202 and 403). If one does not load, say so in the run
  summary; do not count it as "no news".
- `owasp.org/Top10/2025/` redirects to `top10.owasp.org/2025/`, and the
  Secure Headers page to `owasp.org/projects/secure-headers-project`.
