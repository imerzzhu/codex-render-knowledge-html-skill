#!/usr/bin/env python3
"""Render knowledge checklists into a self-contained interactive HTML page."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


CHECKBOX_RE = re.compile(r"^\[(?P<mark>[ xX])\]\s+(?P<text>.*)$")
HASH_TAG_RE = re.compile(r"(?<!\S)#([\w-]+)", re.UNICODE)
TAG_SPLIT_RE = re.compile(r"[,，、\s]+")


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = normalize_tag(value)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def normalize_tag(value: Any) -> str:
    text = str(value).strip().lstrip("#").strip()
    text = re.sub(r"\s+", "-", text)
    return text


def split_tags(raw: str) -> list[str]:
    return dedupe([part for part in TAG_SPLIT_RE.split(raw.strip()) if part])


def strip_inline_tags(text: str) -> tuple[str, list[str]]:
    tags = HASH_TAG_RE.findall(text)
    clean = HASH_TAG_RE.sub("", text)
    clean = re.sub(r"\s{2,}", " ", clean).strip()
    return clean, dedupe(tags)


def parse_list_item(text: str) -> dict[str, Any]:
    checked = False
    match = CHECKBOX_RE.match(text.strip())
    if match:
        checked = match.group("mark").lower() == "x"
        text = match.group("text")
    clean_text, tags = strip_inline_tags(text)
    return {"text": clean_text, "checked": checked, "tags": tags}


def parse_markdown(markdown: str) -> dict[str, Any]:
    """Parse a pragmatic Markdown subset into the normalized knowledge schema."""

    markdown = markdown.lstrip("\ufeff")
    title = ""
    subtitle = ""
    top_tags: list[str] = []
    sections: list[dict[str, Any]] = []
    current_section: dict[str, Any] | None = None
    pending_paragraph: list[str] = []

    def ensure_section(default_title: str = "Overview") -> dict[str, Any]:
        nonlocal current_section
        if current_section is None:
            current_section = {"title": default_title, "items": [], "tags": []}
            sections.append(current_section)
        return current_section

    def flush_paragraph() -> None:
        nonlocal pending_paragraph
        if not pending_paragraph:
            return
        text, tags = strip_inline_tags(" ".join(pending_paragraph))
        if text:
            ensure_section()["items"].append({"text": text, "checked": False, "tags": tags})
            top_tags.extend(tags)
        pending_paragraph = []

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            continue

        if stripped.startswith("# "):
            flush_paragraph()
            if not title:
                title = stripped[2:].strip()
            continue

        if stripped.startswith("## "):
            flush_paragraph()
            section_title, section_tags = strip_inline_tags(stripped[3:].strip())
            current_section = {"title": section_title, "items": [], "tags": section_tags}
            sections.append(current_section)
            top_tags.extend(section_tags)
            continue

        if stripped.startswith(">") and not sections and not subtitle:
            subtitle = stripped.lstrip(">").strip()
            continue

        metadata_match = re.match(r"^(tags?|标签)\s*[:：]\s*(.+)$", stripped, re.IGNORECASE)
        if metadata_match:
            tags = split_tags(metadata_match.group(2))
            if current_section is not None:
                current_section["tags"] = dedupe(current_section.get("tags", []) + tags)
            top_tags.extend(tags)
            continue

        subtitle_match = re.match(r"^(subtitle|副标题)\s*[:：]\s*(.+)$", stripped, re.IGNORECASE)
        if subtitle_match and not subtitle:
            subtitle = subtitle_match.group(2).strip()
            continue

        list_match = re.match(r"^(?:[-*+]|\d+[.)])\s+(.+)$", stripped)
        if list_match:
            flush_paragraph()
            item = parse_list_item(list_match.group(1))
            ensure_section()["items"].append(item)
            top_tags.extend(item["tags"])
            continue

        pending_paragraph.append(stripped)

    flush_paragraph()

    if not title:
        title = "Knowledge Showcase"
    if not sections:
        sections.append({"title": "Overview", "items": [], "tags": []})

    data = {"title": title, "subtitle": subtitle, "tags": dedupe(top_tags), "sections": sections}
    return normalize_knowledge(data, require_sections=False)


def normalize_item(raw_item: Any) -> dict[str, Any]:
    if isinstance(raw_item, str):
        clean_text, tags = strip_inline_tags(raw_item)
        return {"text": clean_text, "checked": False, "tags": tags}

    if not isinstance(raw_item, dict):
        raise ValueError("section items must be strings or objects")

    text = str(raw_item.get("text", "")).strip()
    if not text:
        raise ValueError("each item requires text")

    clean_text, inline_tags = strip_inline_tags(text)
    tags = dedupe(list(raw_item.get("tags", [])) + inline_tags)
    return {
        "text": clean_text,
        "checked": bool(raw_item.get("checked", False)),
        "tags": tags,
    }


def normalize_source(raw_source: Any) -> dict[str, str]:
    if isinstance(raw_source, str):
        return {"label": raw_source, "url": raw_source}
    if not isinstance(raw_source, dict):
        raise ValueError("sources must be strings or objects")
    label = str(raw_source.get("label") or raw_source.get("title") or raw_source.get("url") or "").strip()
    url = str(raw_source.get("url") or "").strip()
    if not label:
        raise ValueError("each source requires a label or url")
    return {"label": label, "url": url}


def normalize_knowledge(data: dict[str, Any], require_sections: bool = True) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("knowledge data must be a JSON object")

    title = str(data.get("title") or "Knowledge Showcase").strip()
    subtitle = str(data.get("subtitle") or "").strip()
    raw_sections = data.get("sections")
    if require_sections and not raw_sections:
        raise ValueError("JSON input requires a non-empty sections array")
    if raw_sections is None:
        raw_sections = []
    if not isinstance(raw_sections, list):
        raise ValueError("sections must be an array")

    tags: list[str] = list(data.get("tags", []))
    sections: list[dict[str, Any]] = []
    for raw_section in raw_sections:
        if not isinstance(raw_section, dict):
            raise ValueError("each section must be an object")
        section_title = str(raw_section.get("title") or "").strip()
        if not section_title:
            raise ValueError("each section requires title")
        section_tags = dedupe(list(raw_section.get("tags", [])))
        raw_items = raw_section.get("items", [])
        if not isinstance(raw_items, list):
            raise ValueError("section items must be an array")
        items = [normalize_item(item) for item in raw_items]
        for item in items:
            tags.extend(item["tags"])
        tags.extend(section_tags)
        sections.append({"title": section_title, "items": items, "tags": section_tags})

    sources = [normalize_source(source) for source in data.get("sources", [])]
    actions = [str(action).strip() for action in data.get("actions", []) if str(action).strip()]

    return {
        "title": title,
        "subtitle": subtitle,
        "tags": dedupe(tags),
        "sections": sections,
        "sources": sources,
        "actions": actions,
    }


def load_knowledge(input_path: Path, input_format: str) -> dict[str, Any]:
    text = Path(input_path).read_text(encoding="utf-8")
    if input_format == "markdown":
        return parse_markdown(text)
    if input_format == "json":
        return normalize_knowledge(json.loads(text), require_sections=True)
    raise ValueError(f"Unsupported format: {input_format}")


def slugify_unique(title: str, used: set[str]) -> str:
    ascii_text = (
        unicodedata.normalize("NFKD", title)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    if not slug:
        slug = "section-" + hashlib.sha1(title.encode("utf-8")).hexdigest()[:8]

    candidate = slug
    suffix = 2
    while candidate in used:
        candidate = f"{slug}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def safe_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https", "mailto", "file"}:
        return url
    return "#"


def render_tag_chips(tags: list[str]) -> str:
    if not tags:
        return ""
    buttons = "\n".join(
        f'<button class="tag-chip" type="button" data-filter="{esc(tag)}">#{esc(tag)}</button>'
        for tag in tags
    )
    return f'<div class="tag-bar" aria-label="Tag filters">{buttons}</div>'


def render_item(item: dict[str, Any], section_slug: str, index: int) -> str:
    item_id = f"{section_slug}-item-{index}"
    tags = dedupe(item.get("tags", []))
    tags_attr = esc(" ".join(tags))
    tag_html = "".join(f'<span class="mini-tag">#{esc(tag)}</span>' for tag in tags)
    checked = " checked" if item.get("checked") else ""
    return f"""
              <li class="knowledge-item" data-tags="{tags_attr}" data-item-id="{esc(item_id)}">
                <label class="check-wrap">
                  <input type="checkbox" data-check-id="{esc(item_id)}"{checked}>
                  <span class="custom-check" aria-hidden="true"></span>
                </label>
                <div class="item-main">
                  <p class="item-text">{esc(item.get("text", ""))}</p>
                  <div class="item-tags">{tag_html}</div>
                </div>
                <button class="copy-item" type="button" aria-label="Copy item">Copy</button>
              </li>"""


def render_html(
    data: dict[str, Any],
    *,
    lang: str = "zh-CN",
    theme: str = "presentation-longform",
) -> str:
    if theme != "presentation-longform":
        raise ValueError("Only the presentation-longform theme is supported")

    normalized = normalize_knowledge(data, require_sections=False)
    used_slugs: set[str] = set()
    nav_links: list[str] = []
    section_cards: list[str] = []

    for section_index, section in enumerate(normalized["sections"], start=1):
        section_slug = slugify_unique(section["title"], used_slugs)
        nav_links.append(f'<a href="#{esc(section_slug)}">{esc(section["title"])}</a>')
        items_html = "\n".join(
            render_item(item, section_slug, item_index)
            for item_index, item in enumerate(section["items"], start=1)
        )
        section_tags = "".join(f'<span class="mini-tag">#{esc(tag)}</span>' for tag in section.get("tags", []))
        section_cards.append(
            f"""
          <section class="section-card" id="{esc(section_slug)}" data-section-index="{section_index}">
            <div class="section-heading">
              <div>
                <p class="section-kicker">Chapter {section_index:02d}</p>
                <h2>{esc(section["title"])}</h2>
                <div class="section-tags">{section_tags}</div>
              </div>
              <button class="section-toggle" type="button" aria-expanded="true">Collapse</button>
            </div>
            <ul class="knowledge-list">
              {items_html}
            </ul>
          </section>"""
        )

    source_html = ""
    if normalized["sources"]:
        links = "\n".join(
            f'<li><a href="{esc(safe_url(source["url"]))}" target="_blank" rel="noopener noreferrer">{esc(source["label"])}</a></li>'
            for source in normalized["sources"]
        )
        source_html = f"""
          <section class="support-block">
            <h2>Sources</h2>
            <ul>{links}</ul>
          </section>"""

    actions_html = ""
    if normalized["actions"]:
        actions = "\n".join(f"<li>{esc(action)}</li>" for action in normalized["actions"])
        actions_html = f"""
          <section class="support-block">
            <h2>Next Actions</h2>
            <ol>{actions}</ol>
          </section>"""

    tags_html = render_tag_chips(normalized["tags"])
    nav_html = "\n".join(nav_links)
    sections_html = "\n".join(section_cards)
    subtitle = normalized["subtitle"] or "A presentation-ready knowledge checklist."

    return f"""<!DOCTYPE html>
<html lang="{esc(lang)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(normalized["title"])}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #19212f;
      --muted: #627083;
      --line: #d9e0ea;
      --paper: #fffdf8;
      --paper-strong: #ffffff;
      --accent: #d65f3a;
      --accent-dark: #9e3f28;
      --teal: #0c7a74;
      --gold: #c7912f;
      --shadow: 0 24px 70px rgba(24, 33, 47, .13);
      --radius: 8px;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        linear-gradient(180deg, rgba(255, 253, 248, .98), rgba(247, 250, 252, .98)),
        radial-gradient(circle at top left, rgba(214, 95, 58, .13), transparent 36rem);
      font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
      line-height: 1.62;
    }}
    .reading-progress {{
      position: fixed;
      top: 0;
      left: 0;
      z-index: 20;
      height: 4px;
      width: 0;
      background: linear-gradient(90deg, var(--accent), var(--teal));
      box-shadow: 0 0 18px rgba(214, 95, 58, .45);
    }}
    .hero {{
      min-height: 72vh;
      display: grid;
      align-items: end;
      padding: 72px max(24px, 8vw) 56px;
      background:
        linear-gradient(135deg, rgba(25, 33, 47, .94), rgba(38, 58, 70, .9)),
        linear-gradient(45deg, rgba(214, 95, 58, .24), rgba(12, 122, 116, .24));
      color: #fff;
    }}
    .hero-inner {{ max-width: 1060px; }}
    .eyebrow {{
      margin: 0 0 18px;
      color: #f0bd8a;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    h1 {{
      max-width: 980px;
      margin: 0;
      font-size: clamp(42px, 7vw, 92px);
      line-height: .98;
      letter-spacing: 0;
    }}
    .hero p {{
      max-width: 760px;
      margin: 24px 0 0;
      color: rgba(255, 255, 255, .84);
      font-size: 20px;
    }}
    .toolbar {{
      position: sticky;
      top: 0;
      z-index: 10;
      display: grid;
      grid-template-columns: minmax(220px, 1fr) auto auto;
      gap: 12px;
      align-items: center;
      padding: 14px max(18px, 6vw);
      border-bottom: 1px solid var(--line);
      background: rgba(255, 253, 248, .92);
      backdrop-filter: blur(14px);
    }}
    .search-field {{
      width: 100%;
      min-height: 42px;
      padding: 10px 14px;
      color: var(--ink);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--paper-strong);
      font: inherit;
    }}
    .toolbar-button, .section-toggle, .copy-item, .tag-chip {{
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: #fff;
      color: var(--ink);
      font: inherit;
      cursor: pointer;
    }}
    .toolbar-button, .section-toggle, .copy-item {{ padding: 8px 12px; }}
    .page-shell {{
      display: grid;
      grid-template-columns: 240px minmax(0, 1fr);
      gap: 42px;
      width: min(1180px, calc(100% - 44px));
      margin: 0 auto;
      padding: 44px 0 76px;
    }}
    .toc {{
      position: sticky;
      top: 86px;
      align-self: start;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(255, 255, 255, .72);
    }}
    .toc h2 {{
      margin: 0 0 12px;
      font-size: 14px;
      color: var(--muted);
    }}
    .toc a {{
      display: block;
      padding: 8px 0;
      color: var(--ink);
      text-decoration: none;
      border-top: 1px solid rgba(217, 224, 234, .7);
    }}
    .content-flow {{ min-width: 0; }}
    .tag-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 24px;
    }}
    .tag-chip {{
      padding: 7px 10px;
      color: var(--teal);
      border-color: rgba(12, 122, 116, .22);
    }}
    .tag-chip.is-active {{
      color: #fff;
      background: var(--teal);
      border-color: var(--teal);
    }}
    .section-card, .support-block {{
      margin-bottom: 30px;
      padding: clamp(22px, 4vw, 40px);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--paper-strong);
      box-shadow: var(--shadow);
    }}
    .section-heading {{
      display: flex;
      gap: 20px;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 22px;
    }}
    .section-kicker {{
      margin: 0 0 8px;
      color: var(--gold);
      font-size: 13px;
      font-weight: 700;
    }}
    .section-heading h2, .support-block h2 {{
      margin: 0;
      font-size: clamp(26px, 4vw, 44px);
      line-height: 1.08;
      letter-spacing: 0;
    }}
    .knowledge-list {{
      list-style: none;
      display: grid;
      gap: 12px;
      margin: 0;
      padding: 0;
    }}
    .knowledge-item {{
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) auto;
      gap: 14px;
      align-items: start;
      padding: 16px;
      border: 1px solid rgba(217, 224, 234, .86);
      border-radius: var(--radius);
      background: linear-gradient(180deg, #fff, #fbfcfe);
    }}
    .knowledge-item.is-hidden, .section-card.is-hidden {{ display: none; }}
    .check-wrap input {{ position: absolute; opacity: 0; pointer-events: none; }}
    .custom-check {{
      display: inline-grid;
      place-items: center;
      width: 22px;
      height: 22px;
      margin-top: 3px;
      border: 2px solid var(--teal);
      border-radius: 6px;
    }}
    .check-wrap input:checked + .custom-check {{
      background: var(--teal);
      box-shadow: inset 0 0 0 4px #fff;
    }}
    .item-text {{
      margin: 0;
      overflow-wrap: anywhere;
      font-size: 17px;
    }}
    .item-tags, .section-tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 8px;
    }}
    .mini-tag {{
      display: inline-flex;
      padding: 2px 7px;
      border-radius: 999px;
      background: rgba(12, 122, 116, .1);
      color: var(--teal);
      font-size: 12px;
    }}
    mark {{
      padding: 0 3px;
      border-radius: 4px;
      background: rgba(199, 145, 47, .25);
      color: inherit;
    }}
    .section-card.is-collapsed .knowledge-list {{ display: none; }}
    .support-block ul, .support-block ol {{ margin-bottom: 0; }}
    @media (max-width: 820px) {{
      .hero {{ min-height: 58vh; padding: 56px 22px 38px; }}
      .hero p {{ font-size: 17px; }}
      .toolbar {{ grid-template-columns: 1fr; }}
      .page-shell {{ grid-template-columns: 1fr; width: min(100% - 28px, 680px); gap: 22px; }}
      .toc {{ position: relative; top: auto; }}
      .section-heading {{ display: block; }}
      .section-toggle {{ margin-top: 14px; }}
      .knowledge-item {{ grid-template-columns: auto minmax(0, 1fr); }}
      .copy-item {{ grid-column: 2; justify-self: start; }}
    }}
    @media print {{
      .reading-progress, .toolbar, .toc, .copy-item, .section-toggle, .tag-bar {{ display: none !important; }}
      body {{ background: #fff; color: #111; }}
      .hero {{ min-height: auto; padding: 32px 0; color: #111; background: #fff; }}
      .hero p {{ color: #333; }}
      .page-shell {{ display: block; width: 100%; padding: 0; }}
      .section-card, .support-block {{ break-inside: avoid; box-shadow: none; border-color: #bbb; }}
    }}
  </style>
</head>
<body>
  <div class="reading-progress" aria-hidden="true"></div>
  <header class="hero">
    <div class="hero-inner">
      <p class="eyebrow">Interactive Knowledge Showcase</p>
      <h1>{esc(normalized["title"])}</h1>
      <p>{esc(subtitle)}</p>
    </div>
  </header>
  <div class="toolbar" role="region" aria-label="Knowledge controls">
    <input id="knowledge-search" class="search-field" type="search" placeholder="Search this knowledge page">
    <button id="clear-filters" class="toolbar-button" type="button">Clear</button>
    <button id="print-page" class="toolbar-button" type="button">Print</button>
  </div>
  <main class="page-shell">
    <aside class="toc" aria-label="Table of contents">
      <h2>Contents</h2>
      {nav_html}
    </aside>
    <div class="content-flow">
      {tags_html}
      {sections_html}
      {actions_html}
      {source_html}
    </div>
  </main>
  <script>
    const storagePrefix = "renderKnowledgeHtml:" + location.pathname + ":";
    const searchInput = document.getElementById("knowledge-search");
    const clearButton = document.getElementById("clear-filters");
    const progress = document.querySelector(".reading-progress");
    let activeTag = "";

    function escapeHtml(value) {{
      return value.replace(/[&<>"']/g, char => ({{
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }}[char]));
    }}

    function updateProgress() {{
      const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
      const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      const percent = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
      progress.style.width = percent + "%";
    }}

    function applyHighlight(element, query) {{
      if (!element.dataset.originalText) {{
        element.dataset.originalText = element.textContent;
      }}
      const original = element.dataset.originalText;
      if (!query) {{
        element.innerHTML = escapeHtml(original);
        return;
      }}
      const escapedQuery = query.replace(/[.*+?^${{}}()|[\\]\\\\]/g, "\\\\$&");
      const regex = new RegExp("(" + escapedQuery + ")", "ig");
      element.innerHTML = escapeHtml(original).replace(regex, "<mark>$1</mark>");
    }}

    function applyFilters() {{
      const query = searchInput.value.trim().toLowerCase();
      document.querySelectorAll(".section-card").forEach(section => {{
        let visibleCount = 0;
        section.querySelectorAll(".knowledge-item").forEach(item => {{
          const text = item.textContent.toLowerCase();
          const tags = (item.dataset.tags || "").split(" ").filter(Boolean);
          const matchesText = !query || text.includes(query);
          const matchesTag = !activeTag || tags.includes(activeTag);
          const visible = matchesText && matchesTag;
          item.classList.toggle("is-hidden", !visible);
          const textNode = item.querySelector(".item-text");
          applyHighlight(textNode, query);
          if (visible) visibleCount += 1;
        }});
        section.classList.toggle("is-hidden", visibleCount === 0);
      }});
    }}

    document.querySelectorAll("[data-filter]").forEach(button => {{
      button.addEventListener("click", () => {{
        activeTag = activeTag === button.dataset.filter ? "" : button.dataset.filter;
        document.querySelectorAll("[data-filter]").forEach(other => {{
          other.classList.toggle("is-active", activeTag && other.dataset.filter === activeTag);
        }});
        applyFilters();
      }});
    }});

    document.querySelectorAll("[data-check-id]").forEach(input => {{
      const key = storagePrefix + input.dataset.checkId;
      const stored = localStorage.getItem(key);
      if (stored !== null) input.checked = stored === "true";
      input.addEventListener("change", () => localStorage.setItem(key, input.checked ? "true" : "false"));
    }});

    document.querySelectorAll(".section-toggle").forEach(button => {{
      button.addEventListener("click", () => {{
        const section = button.closest(".section-card");
        const collapsed = section.classList.toggle("is-collapsed");
        button.textContent = collapsed ? "Expand" : "Collapse";
        button.setAttribute("aria-expanded", collapsed ? "false" : "true");
      }});
    }});

    document.querySelectorAll(".copy-item").forEach(button => {{
      button.addEventListener("click", async () => {{
        const text = button.closest(".knowledge-item").querySelector(".item-text").textContent;
        try {{
          await navigator.clipboard.writeText(text);
          button.textContent = "Copied";
          setTimeout(() => button.textContent = "Copy", 1200);
        }} catch {{
          const area = document.createElement("textarea");
          area.value = text;
          document.body.appendChild(area);
          area.select();
          document.execCommand("copy");
          area.remove();
        }}
      }});
    }});

    searchInput.addEventListener("input", applyFilters);
    clearButton.addEventListener("click", () => {{
      searchInput.value = "";
      activeTag = "";
      document.querySelectorAll("[data-filter]").forEach(button => button.classList.remove("is-active"));
      applyFilters();
    }});
    document.getElementById("print-page").addEventListener("click", () => window.print());
    addEventListener("scroll", updateProgress, {{ passive: true }});
    updateProgress();
  </script>
</body>
</html>
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a knowledge checklist into one interactive HTML file.")
    parser.add_argument("--input", required=True, type=Path, help="Input Markdown or JSON file")
    parser.add_argument("--format", required=True, choices=["markdown", "json"], help="Input format")
    parser.add_argument("--output", required=True, type=Path, help="Output HTML file")
    parser.add_argument("--title", help="Override the page title")
    parser.add_argument("--subtitle", help="Override the page subtitle")
    parser.add_argument("--lang", default="zh-CN", choices=["zh-CN", "en-US"], help="HTML language")
    parser.add_argument("--theme", default="presentation-longform", choices=["presentation-longform"])
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        data = load_knowledge(args.input, args.format)
        if args.title:
            data["title"] = args.title
        if args.subtitle:
            data["subtitle"] = args.subtitle
        output_html = render_html(data, lang=args.lang, theme=args.theme)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_html, encoding="utf-8", newline="\n")
    except Exception as exc:  # pragma: no cover - CLI surface
        print(f"render-knowledge-html: {exc}", file=sys.stderr)
        return 1
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
