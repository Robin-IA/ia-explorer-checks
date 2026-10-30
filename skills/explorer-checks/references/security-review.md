# Security review checklist

Record each item in `review.json` under `manual.security` as `pass`,
`fail` or `n/a` with a note. Use the item names as written here, so reports
compare across explorers.

## Resolving an innerHTML (or other sink) finding

An explorer renders text it did not write: archive.org titles and
descriptions, Wayback page text, CDX fields, filenames, the URL's query
string. Any of those can contain `<img src=x onerror=...>`. For each sink:

1. Read the whole expression that is assigned, not just the line.
2. For every interpolated value (`${...}`, `+ x +`), find where it comes
   from. Values from functions that return numbers or fixed strings are
   safe. **Values from data are not**, unless they pass through an
   escaping function first.
3. Check the escaping function. A correct one replaces `&` first, then
   `<`, `>`, `"` and `'`. If a value goes into an attribute, the quotes
   matter. If it goes into `href` or `src`, check the scheme too, because
   `javascript:` survives escaping.
4. Verdict:
   - **cleared**: name the function or the literal source, for example
     "every data field goes through `esc()` (index.html:140), which
     escapes &<>\"'".
   - **fail**: name the unescaped field. The fix is an `esc()` helper at
     that point, or building the node with `textContent`. Give the exact
     line to change.

URL parameters that are read back into the page (`?q=`) are the classic
reflected-XSS route on a static site. Check them specifically.

## Checklist

- **No secrets**: no credentials in the code, history excepted only if
  the scanner covered it. Check `git log -p -S` for any key-shaped string a
  finding mentions, and check config files the scanner skipped.
- **Untrusted data is escaped**: every sink resolved as above.
- **URLs from data are safe**: links built from data (`href=${d.url}`)
  allow only `http(s):` or a known Wayback/archive.org prefix.
- **Third-party code is pinned**: CDN scripts name an exact version.
  Integrity hashes are advisory, not required.
- **No mixed content**: nothing loaded over `http:`.
- **Server input is validated** (apps only): query parameters reaching SQL
  use bound parameters, never f-strings. Paths built from input cannot
  escape their folder (`..`). Flask `debug` is off in the served config.
- **Dependencies have no known vulnerabilities**: pip-audit result, or
  npm audit if there is a `package.json`.
- **Errors do not leak**: tracebacks, file paths and SQL do not reach the
  page in the served configuration.
- **Scope of writes** (apps with upload or contribution features): uploads
  check type and size, and contributed text is escaped where it is shown.

Mark items `n/a` when they truly do not apply (no server, no uploads), and
say why in the note.
