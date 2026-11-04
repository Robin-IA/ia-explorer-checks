# WCAG 2.2 AA: what you check by hand

axe-core covers roughly a third of WCAG's success criteria, and only
partly. These are the AA criteria it cannot settle. Each one is a likely
problem for an explorer, with its facets, histograms, result lists and
"load more" buttons.

Record each in `review.json` under `manual.accessibility` as `pass`,
`fail` or `n/a`, with the item name exactly as written here. A `fail`
also needs a finding in `findings` with a concrete fix: the file, the
element, and the change.

Do these in the browser, on every page checked. Use the keyboard alone for
the keyboard items.

## Content

- **1.1.1 Non-text content**: images, icons and charts have alt text
  that says what they show. A histogram or chart needs a text equivalent:
  a caption with the key numbers, or a visually hidden table. Decorative
  images use `alt=""`. Thumbnail alt text from item titles is fine;
  filenames are not.
- **1.3.1 Info and relationships**: headings are real headings in a
  sensible order. Lists are lists. Data tables have `<th>` and scope. Facet
  groups are `fieldset` and `legend`, or have an accessible group name.
- **1.3.2 Meaningful sequence**: the DOM order reads sensibly with CSS
  turned off. Check this where a grid or flex layout reorders things.
- **1.4.1 Use of color**: nothing is conveyed by colour alone, such as
  chart series, active facet or selected tab, without a second cue.
- **1.4.11 Non-text contrast**: input borders, focus rings, chart bars
  and icon buttons are 3:1 against their background.
- **1.4.4 Resize text / 1.4.12 Text spacing**: at 200% zoom nothing is
  cut off or overlaps.
- **2.4.4 Link purpose**: "view", "more" and "Wayback" links say what they
  lead to in context, or carry an `aria-label` that does.
- **2.4.6 Headings and labels**: they describe their section or input.
- **3.1.1 Language of page**: `lang` is set and correct. Content in another
  language (translated documents, non-English titles) carries its own
  `lang` where the language is known (3.1.2).

## Operation

- **2.1.1 Keyboard**: everything works from the keyboard: facets,
  sort, tabs, the histogram if it filters, "load more", dialogs.
  Clickable `div`s and `span`s are the usual failure.
- **2.1.2 No keyboard trap**: focus can leave every widget, including
  modals and embedded players.
- **2.4.1 Bypass blocks**: a skip link, or landmarks (`main`, `nav`) a
  screen reader can jump between.
- **2.4.3 Focus order**: tabbing follows reading order. After "load
  more" or a filter change, focus is not lost to the top of the page.
- **2.4.7 Focus visible**: resolve the script's focus finding by
  looking. Every focused control shows a clear indicator.
- **2.4.11 Focus not obscured**: sticky headers and footers do not hide
  the focused element.
- **2.5.8 Target size**: small controls (facet checkboxes, pagination,
  close buttons) are at least 24×24 CSS px, or spaced so a 24 px circle
  fits.
- **2.2.2 Pause, stop, hide**: anything that moves or auto-updates for
  more than 5 seconds can be paused.

## Understanding and robustness

- **3.2.2 On input**: changing a select or checkbox does not move focus
  or navigate unexpectedly. Live filtering of results is fine.
- **3.3.2 Labels or instructions**: the search box and every filter
  have a visible label, not only a placeholder.
- **4.1.2 Name, role, value**: custom widgets (tabs, toggles,
  expanders) expose their role and state: `aria-selected`,
  `aria-expanded`, `aria-pressed`. axe checks that each `role="tab"` has
  a name; whether the selected state follows the visible tab is yours.
- **4.1.3 Status messages**: result counts and "loading" or "no results"
  messages are announced through `role="status"` or `aria-live="polite"`,
  without moving focus. This is the most common explorer failure.

## Media (only if the explorer plays audio or video)

- **1.2.2 Captions** for prerecorded video with speech, and **1.2.1** a
  transcript for audio-only. For archived media the explorer did not make,
  record whether captions exist and are exposed. Mark the item `fail` only
  if the explorer has captions and hides them.

## Scope note for the report

The pass is for the pages checked, on the date checked. Write the pages
into the report's header (the script does) and nothing more general.
