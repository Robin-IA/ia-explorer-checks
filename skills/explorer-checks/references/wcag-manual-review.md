# WCAG 2.2 AA: what you check by hand

axe-core covers roughly a third of WCAG's success criteria, and only
partly. **Every WCAG 2.2 Level A and AA success criterion is on this list**,
so the report can say each one was reviewed. The first sections are the
likely problems for an explorer, with its facets, histograms, result lists
and "load more" buttons; "The rest of WCAG 2.2 A and AA" covers the others,
most of which are `n/a` for a typical explorer. Give the reason for every
`n/a`.

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
- **1.4.10 Reflow**: at 320 px wide (400% zoom at 1280 px) the page
  scrolls in one direction only; wide tables and charts may scroll on
  their own if they can be reached from the keyboard.
- **1.4.3 Contrast (minimum)**: settle every text element axe-core could
  not (gradients, images, overlaps) by measuring it: 4.5:1, or 3:1 for
  large text.
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
- **1.4.13 Content on hover or focus**: tooltips and popups that appear on
  hover or focus can be dismissed without moving the pointer or focus
  (Esc); the pointer can move onto them without them closing; they stay
  until dismissed or no longer relevant. Chart and histogram tooltips are
  the usual case. Test with
  [F114](https://www.w3.org/WAI/WCAG22/Techniques/failures/F114)'s
  procedure.
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
- **1.2.3 / 1.2.5 Audio description** for prerecorded video, and **1.2.4
  Captions (live)**: as with 1.2.2, for archived media record whether a
  description or captions exist and are exposed; `n/a` with no video or
  no live media.
- **1.4.2 Audio control**: nothing plays sound by itself for more than 3
  seconds, or there is a control to stop it.

## The rest of WCAG 2.2 A and AA

Less often relevant to an explorer, but each still needs a result. `n/a`
needs its reason ("no form fields", "no sign-in").

- **1.3.3 Sensory characteristics**: instructions do not depend on shape,
  colour, size, position or sound alone ("click the green bar").
- **1.3.4 Orientation**: the page works in portrait and landscape.
- **1.3.5 Identify input purpose**: fields asking for the visitor's own
  details (name, email) carry the right `autocomplete` value; `n/a` when
  there are none, which is usual.
- **1.4.5 Images of text**: text is text, not a picture of text (logos and
  scans of archived documents excepted).
- **2.1.4 Character key shortcuts**: no single-key shortcuts, or they can
  be turned off or remapped, or work only with focus on their control.
- **2.2.1 Timing adjustable**: no time limits, or the visitor can turn
  them off or extend them.
- **2.3.1 Three flashes or below threshold**: nothing flashes more than
  three times a second.
- **2.4.2 Page titled**: each page's `<title>` says what it is.
- **2.4.5 Multiple ways**: more than one way to reach each page in a set
  (navigation and search, or a list of pages); `n/a` for a single page.
- **2.5.1 Pointer gestures**: anything done with a multipoint or path
  gesture (pinch, swipe) also works with a single tap or click.
- **2.5.2 Pointer cancellation**: actions happen on release, not on
  press, or can be undone.
- **2.5.3 Label in name**: a control's accessible name contains its
  visible text, starting with it ("Copy Claim 1 citation", not "Copy
  Claim 1 as a citation").
- **2.5.4 Motion actuation**: nothing is triggered by shaking or tilting
  the device, or it can be turned off and done another way.
- **2.5.7 Dragging movements**: anything done by dragging (a range
  slider, a timeline brush) can also be done without dragging.
- **3.1.2 Language of parts**: passages in another language carry their
  own `lang` (quoted foreign-language documents, translated titles).
- **3.2.1 On focus**: focusing a control does not change the page or move
  focus by itself.
- **3.2.3 Consistent navigation**: navigation repeated across pages comes
  in the same order.
- **3.2.4 Consistent identification**: things that work the same are
  named the same across pages.
- **3.2.6 Consistent help**: help (a Feedback? link, an About page) is in
  the same place on every page that has it.
- **3.3.1 Error identification**: an input error (an unknown folder, an
  empty search) is described in text, not shown by colour alone.
- **3.3.3 Error suggestion**: where a fix is known, the error says it.
- **3.3.4 Error prevention (legal, financial, data)**: submissions that
  commit the visitor to something can be checked, corrected or reversed;
  `n/a` for read-only explorers.
- **3.3.7 Redundant entry**: information the visitor already gave in a
  process is not asked for again.
- **3.3.8 Accessible authentication (minimum)**: signing in needs no
  cognitive test (memorising, transcribing); `n/a` with no sign-in.

4.1.1 Parsing is not in WCAG 2.2; for 2.0 and 2.1 it is covered by the
code validity check.

## Scope note for the report

The pass is for the pages checked, on the date checked. Write the pages
into the report's header (the script does) and nothing more general.
