# Render Knowledge HTML Codex Skill

`render-knowledge-html` is a Codex skill for turning knowledge checklists, learning paths, method notes, retrospectives, tool comparisons, and presentation-ready summaries into a polished self-contained interactive HTML page.

The generated HTML works as a single local file. It includes inline CSS and JavaScript, with no CDN, build step, or external runtime.

## What It Generates

- Presentation-style longform page.
- Premium minimalist editorial cover for direct display.
- Sticky search and print controls.
- Table of contents.
- Tag filtering.
- Collapsible sections.
- Checklist state persisted with `localStorage`.
- Copy buttons per item.
- Reading progress bar.
- Print-friendly CSS.

## Visual Direction

The default theme is a minimal presentation long page: light paper canvas, strong black typography, thin rules, restrained copper labels, and teal interaction states. It is designed to work as a real browser surface for live display, printing, and 1080x1920 graphic screenshots.

## Install

Windows PowerShell:

```powershell
$repo = "path\to\codex-render-knowledge-html-skill"
$codexSkills = Join-Path $env:USERPROFILE ".codex\skills"

New-Item -ItemType Directory -Force -Path $codexSkills | Out-Null
Copy-Item -Recurse -Force "$repo\skills\render-knowledge-html" $codexSkills
```

For a different Codex home, copy `skills/render-knowledge-html` into that environment's skills directory.

## Usage Prompt

```text
Use $render-knowledge-html to turn this knowledge checklist into a polished interactive HTML showcase.
```

## Command Line

Markdown input:

```powershell
python .\skills\render-knowledge-html\scripts\render_knowledge_html.py `
  --input .\examples\knowledge-source.md `
  --format markdown `
  --output .\output\knowledge-showcase.html `
  --lang zh-CN
```

JSON input:

```powershell
python .\skills\render-knowledge-html\scripts\render_knowledge_html.py `
  --input .\examples\knowledge-source.json `
  --format json `
  --output .\output\knowledge-showcase.html `
  --title "Knowledge Showcase" `
  --subtitle "A browser-ready guide"
```

## Markdown Example

```markdown
# AI Research Checklist
> A compact guide for source-grounded answers.

## Search Strategy
Tags: research, citation

- [ ] Verify source dates #freshness
- Prefer official documentation #primary-source
- Capture direct links

## Delivery
- Put the HTML path first #handoff
```

## JSON Example

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

## Validate

```powershell
python -m pytest tests
$validator = Join-Path $env:USERPROFILE ".codex\skills\.system\skill-creator\scripts\quick_validate.py"
python $validator ".\skills\render-knowledge-html"
```

For visual QA, generate an HTML file and open it in a browser at desktop and mobile widths. Check search, tag filtering, collapse, checklist persistence, copy, and print controls.

## Promo Example

The repository includes a structured promo source at `promo/showcase/render-knowledge-html-promo.json`. Generate it with:

```powershell
python .\skills\render-knowledge-html\scripts\render_knowledge_html.py `
  --input .\promo\showcase\render-knowledge-html-promo.json `
  --format json `
  --output .\output\promo\render-knowledge-html-showcase.html `
  --lang zh-CN
```

Capture real rendered screenshots at 1080x1920 for Douyin/Xiaohongshu-style graphic posts. Generated screenshots and HTML remain ignored local artifacts by default.

## Project Structure

```text
.
|-- promo/showcase/
|   `-- render-knowledge-html-promo.json
|-- skills/
|   `-- render-knowledge-html/
|       |-- SKILL.md
|       |-- agents/openai.yaml
|       |-- assets/.gitkeep
|       |-- references/html-design-rules.md
|       `-- scripts/render_knowledge_html.py
|-- tests/
|-- LICENSE
`-- README.md
```

## References

- [OpenAI Codex Skills](https://developers.openai.com/codex/skills)
- [OpenAI skills repository](https://github.com/openai/skills)
- [OpenAI Skills and Agents SDK](https://developers.openai.com/blog/skills-agents-sdk)

## Open Source Boundary

The MIT license applies to this repository's source code and documentation. Generated HTML pages, user-provided source notes, private paths, screenshots, and local output files are not part of the public package unless deliberately added by a contributor.
