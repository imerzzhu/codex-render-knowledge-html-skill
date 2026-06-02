# HTML Design Rules

Use these rules when generating or revising the `presentation-longform` HTML output.

## Visual Direction

- Build an editorial long page for presentation and reading, not a dashboard.
- Use a strong first viewport with the title and subtitle, then let the user scroll into the content.
- Keep the palette balanced: dark ink, warm accent, teal action color, restrained gold labels, and light paper surfaces.
- Avoid decorative blobs, stock-like backgrounds, and card-heavy landing-page composition.

## Layout

- Output must be a single HTML file with inline CSS and inline JavaScript.
- Desktop layout: sticky tool bar, left table of contents, main reading column.
- Mobile layout: single column, table of contents above content, no horizontal scrolling.
- Fixed-format controls such as search fields, buttons, checkboxes, and tag chips must not resize the layout unexpectedly.
- Use `overflow-wrap: anywhere` or equivalent on user text so long words and URLs cannot break the page.

## Interaction

Required controls:

- Reading progress bar.
- Search with highlighted matches.
- Tag filtering.
- Collapsible sections.
- Checklist state persisted through `localStorage`.
- Copy button per item.
- Print button with print-friendly CSS.

The page must work from a local `file://` URL without a server.

## Accessibility

- Use semantic `header`, `main`, `aside`, `section`, `ul`, and `li` elements.
- Keep visible focus states provided by browser defaults or custom styles.
- Buttons must be real `<button>` elements, not clickable text.
- Links must be human-readable and safe. Reject unsupported URL schemes.

## Print

- Hide interactive controls in print.
- Keep section cards from breaking awkwardly when possible.
- Use black text on white background for print.
- Do not depend on background images or external fonts.

## Final QA

- Search for accidental external dependencies: `script src=`, `link href=`, CDN URLs.
- Check desktop and mobile screenshots for clipped text, overlapping controls, blank output, and unreadable contrast.
- Verify search, tag filtering, section collapse, checkbox persistence, copy buttons, and print button all respond in a browser.
