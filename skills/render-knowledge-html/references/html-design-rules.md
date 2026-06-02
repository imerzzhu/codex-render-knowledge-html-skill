# HTML Design Rules

Use these rules when generating or revising the `presentation-longform` HTML output.

## Visual Direction

- Build an editorial long page for presentation and reading, not a dashboard.
- Default to a premium minimalist international UI style: Swiss editorial hierarchy, strong typography, disciplined spacing, and quiet product controls.
- Use a light paper canvas with black ink, thin lines, restrained copper accents, and teal only for interaction/state.
- Use Apple-inspired glass material sparingly for navigation, controls, and content surfaces: translucent light fills, blur, subtle saturation, inset highlights, and soft shadows.
- Use rounded, continuous edges by default. Prefer pill controls, softly rounded cards, and curved checklist boxes over sharp rectangular corners.
- Keep glass effects behind readable text only when contrast remains strong; if the content looks washed out, increase the surface opacity before adding more blur.
- Use a strong first viewport with the title, subtitle, and compact metadata. The first screen should feel like a designed publication cover, not a generic SaaS hero.
- Avoid decorative blobs, heavy gradients, dark tech backgrounds, stock-like backgrounds, fake metrics, and card-heavy landing-page composition.
- Treat the HTML itself as the product screenshot: real search, tags, checklist, copy, and print controls should be visible and refined.

## Layout

- Output must be a single HTML file with inline CSS and inline JavaScript.
- Desktop layout: sticky tool bar, left table of contents, main reading column.
- Mobile layout: single column, table of contents above content, no horizontal scrolling.
- Fixed-format controls such as search fields, buttons, checkboxes, and tag chips must not resize the layout unexpectedly.
- Use `overflow-wrap: anywhere` or equivalent on user text so long words and URLs cannot break the page.
- Prefer thin borders and small shadows over thick panels. Cards can frame content, but they should read as refined paper surfaces, not dense dashboard tiles.
- Maintain generous vertical rhythm. If a page feels busy, reduce decoration before reducing whitespace.

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

## Promo Screenshot Rules

- For Douyin/Xiaohongshu-style graphic promotion, capture real rendered HTML at `1080x1920`.
- Do not fake the product surface in a separate mockup unless the user explicitly requests an illustration.
- Keep the screenshot readable at phone size: large hero title, visible controls, and at least one real section/item area.
- If multiple screenshots are needed, use a carousel rhythm: cover, feature detail, usage/install.

## Final QA

- Search for accidental external dependencies: `script src=`, `link href=`, CDN URLs.
- Check desktop and mobile screenshots for clipped text, overlapping controls, blank output, and unreadable contrast.
- Verify search, tag filtering, section collapse, checkbox persistence, copy buttons, and print button all respond in a browser.
