# Security review checklist

Record each item in `review.json` under `manual.security` as `pass`,
`fail` or `n/a` with a note. Use the item names as written here, so reports
compare across explorers.

Each item names its category in the OWASP Top 10:2025 (`A01`–`A10`) and
the ASVS 5.0.0 chapter (`V1`–`V17`) that holds its requirements; AI items
name the AISVS 1.0 chapter. Chapters, not requirement numbers, because the
numbers move between versions. A finding of your own in `review.json` takes
the same tag in an `owasp` field, for example `"owasp": "A01:2025 · ASVS V8"`.

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

### Every explorer

- **No secrets** (A07 · V13): no credentials in the code, history excepted
  only if the scanner covered it. Check `git log -p -S` for any key-shaped
  string a finding mentions, and check config files the scanner skipped.
  A Flask `SECRET_KEY` comes from the environment, never the source.
- **Untrusted data is escaped** (A05 · V1): every sink resolved as above.
- **URLs from data are safe** (A05 · V1): links built from data
  (`href=${d.url}`) allow only `http(s):` or a known Wayback/archive.org
  prefix.
- **Harvested data is validated** (A08 · V2): the build checks the fields
  it writes into the site's data (dates are dates, identifiers match their
  pattern, URLs have the expected prefix) and rejects or reports a record
  that does not fit. Escaping at display is the second line, not the only
  one.
- **Third-party code is pinned** (A08 · V3): CDN scripts name an exact
  version. Integrity hashes are advisory, not required.
- **No mixed content** (A04 · V12): nothing loaded over `http:`.
- **Dependencies are pinned and maintained** (A03 · V15): requirements
  name exact versions (the `supply:unpinned` advisory); workflow actions
  are pinned to a commit (`supply:action-unpinned`); nothing depends on a
  runtime or library past its end of life, such as a Python version no
  longer receiving security fixes.
- **Dependencies have no known vulnerabilities** (A03 · V15): pip-audit
  result, or npm audit if there is a `package.json`.
- **Third parties a visitor's browser contacts** (V3): every
  `privacy:third-party` host is either needed and named in the note, or
  served from the explorer instead. Each one learns who visits which page,
  which matters for a library.
- **What Pages publishes** (A01 · V13): if the repository is private and
  serves GitHub Pages, everything in the served folder is public. Resolve
  `pages:private-repo-published`, and look at what the folder holds even
  when the repository is public: notes, data dumps and build logs go out
  with the site.

### Apps (a server, not only static files)

- **Server input is validated** (A05 · V1): query parameters reaching SQL
  use bound parameters, never f-strings. Paths built from input cannot
  escape their folder (`..`).
- **Configuration is safe to serve** (A02 · V13): Flask `debug` is off in
  the served configuration, the secret key comes from the environment, and
  the server listens only where it must (`127.0.0.1` behind a proxy, not
  `0.0.0.0`, unless that is the point).
- **Errors are handled and do not leak** (A10 · V16): tracebacks, file
  paths and SQL do not reach the page, and expected bad input gets an
  answer, not a 500. Search is the usual case: a quote or `AND` typed into
  an SQLite FTS5 `MATCH` query is a syntax error unless the term is quoted
  or the error caught.
- **Commands built from data** (A05 · V1): `subprocess` calls (ffmpeg,
  `afconvert`, Whisper, yt-dlp) take a list of arguments, never a shell
  string, and a filename or URL from harvested data cannot start with `-`
  and be read as an option. Bandit flags `shell=True`; it does not flag
  an argument that came from data.

### Apps that accept contributions or uploads

- **Who can write** (A01 · V8, CSRF V3): every route that adds, edits or
  deletes checks who is asking, and forms that change data reject
  cross-site requests (a CSRF token, or `SameSite` cookies plus an origin
  check). Reading the routes is the check: list each write route in the
  note with what protects it.
- **Fetches of submitted URLs** (A01 · V1, V5): if the server fetches a URL
  a contributor gave (a recording, a page to capture), it allows only the
  expected hosts and refuses private, loopback and link-local addresses
  after resolving the name. Otherwise a contributor can make the server
  read the network it sits on.
- **Scope of writes** (A06 · V5): uploads check type and size, stored
  names are generated rather than taken from the upload, and contributed
  text is escaped where it is shown.
- **Limits** (V2): a queue anyone can feed (transcription, harvesting) has
  limits on size, duration and rate, so one contributor cannot take the
  machine for a week.

### AI components (transcription, summaries, embeddings)

- **Model output is untrusted** (A05 · AISVS Model Behavior, Output
  Control & Safety Assurance): transcripts and generated text are escaped
  like any other data, and nothing from a model is executed or used as a
  URL without the same checks as harvested data.
- **Models are pinned** (A03 · AISVS Supply Chain Security for Models):
  downloaded weights name a revision or hash, not "latest".

Mark items `n/a` when they truly do not apply (no server, no uploads, no
model), and say why in the note.

### Not covered

The checks read the repository and the pages. They do not test the host the
explorer runs on: open ports, the service account, TLS on a reverse proxy,
backups. For a self-hosted explorer, say so under what could not be checked,
and point to the OWASP Top 10 Infrastructure Security Risks for that review.
