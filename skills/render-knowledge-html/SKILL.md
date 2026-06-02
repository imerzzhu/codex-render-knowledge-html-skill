---
name: render-knowledge-html
description: Use when turning Codex answers, knowledge checklists, learning paths, method notes, tool comparisons, step guides, retrospectives, or presentation-ready summaries into a polished self-contained interactive HTML file for browser display, sharing, printing, or live presentation. Use this for Markdown or JSON knowledge content when the user wants a refined visual artifact instead of plain text.
---

# Render Knowledge HTML

## Overview

Use this skill to convert structured knowledge into a single presentation-style HTML page with built-in search, tag filtering, collapsible sections, checklist state, copy buttons, reading progress, and print styling.

The output must be self-contained: no CDN, no external CSS, no external JavaScript, no build step.

## Default Workflow

1. Decide the input form:
   - Use Markdown when the user gives normal prose, bullet lists, learning notes, or a Codex-style answer.
   - Use JSON when the content is already structured or when exact tests/reuse matter.
2. Write the source content to a descriptive local file, such as `knowledge-source.md` or `knowledge-source.json`.
3. Run the renderer:

   ```powershell
   $skillDir = "path\to\render-knowledge-html"
   python (Join-Path $skillDir "scripts\render_knowledge_html.py") `
     --input "path\to\knowledge-source.md" `
     --format markdown `
     --output "path\to\knowledge-showcase.html" `
     --lang zh-CN
   ```

4. Open the generated HTML in a browser when visual quality matters. Check desktop and mobile widths for overflow, clipped text, broken controls, and unreadable spacing.
5. In the final response, put the absolute HTML path first so the user can open it immediately.

## Input Contracts

Markdown supports:

- `# Title`
- first `> Blockquote` as subtitle
- `## Section` headings
- `Tags: tag-one, tag-two`
- bullet items, including `- [ ] task`, `- [x] done`, and inline tags such as `#source-check`

JSON supports:

```json
{
  "title": "Knowledge Title",
  "subtitle": "Optional subtitle",
  "tags": ["method", "checklist"],
  "sections": [
    {
      "title": "Section Title",
      "tags": ["phase-1"],
      "items": [
        "Simple item",
        {"text": "Checked item", "checked": true, "tags": ["done"]}
      ]
    }
  ],
  "sources": [
    {"label": "OpenAI Codex Skills", "url": "https://developers.openai.com/codex/skills"}
  ],
  "actions": ["Open the HTML in a browser"]
}
```

## Renderer Commands

Markdown:

```powershell
python .\scripts\render_knowledge_html.py `
  --input .\input.md `
  --format markdown `
  --output .\output\showcase.html
```

JSON:

```powershell
python .\scripts\render_knowledge_html.py `
  --input .\input.json `
  --format json `
  --output .\output\showcase.html `
  --title "Override Title" `
  --subtitle "Override subtitle"
```

Supported options:

- `--lang zh-CN|en-US`
- `--theme presentation-longform`
- `--title`
- `--subtitle`

## Quality Rules

- Preserve the user's meaning. Do not invent facts, citations, metrics, or sources to make the page look richer.
- Keep section titles short enough for a table of contents.
- Prefer 4-8 sections for display pages. Split very long lists into coherent sections.
- Keep tags short and functional; use them for filtering, not decoration.
- Do not add external web assets unless the user explicitly asks and the final HTML no longer needs to be self-contained.
- Read `references/html-design-rules.md` before changing the visual template or interaction behavior.

## Resources

- `scripts/render_knowledge_html.py`: Markdown/JSON to single-file HTML renderer.
- `references/html-design-rules.md`: visual, responsive, interaction, and print requirements for the presentation-longform theme.
