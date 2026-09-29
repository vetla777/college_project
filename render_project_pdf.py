"""Render PROJECT_DOCUMENT.md as a review-ready PDF and editable HTML."""

from __future__ import annotations

import argparse
import html
import re
from datetime import date
from pathlib import Path

from markdown_it import MarkdownIt
from weasyprint import HTML


ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = ROOT / "PROJECT_DOCUMENT.md"
DEFAULT_HTML = ROOT / "PROJECT_DOCUMENT_review.html"
DEFAULT_PDF = ROOT / "PROJECT_DOCUMENT_review.pdf"


def slugify(value: str) -> str:
    """Create a stable, URL-safe anchor from a heading."""
    value = re.sub(r"[`*_~]", "", value)
    value = re.sub(r"\s+", "-", value.strip().lower())
    return re.sub(r"[^a-z0-9-]+", "", value)


def inline_html(tokens: list, index: int = 0) -> tuple[str, int]:
    """Render markdown-it inline tokens recursively."""
    output: list[str] = []
    while index < len(tokens):
        token = tokens[index]
        if token.type == "inline":
            child_output, index = inline_html(token.children or [], index + 1)
            output.append(child_output)
        elif token.type == "softbreak":
            output.append("\n")
        elif token.type == "hardbreak":
            output.append("<br>")
        elif token.type == "text":
            output.append(html.escape(token.content))
        elif token.type == "code_inline":
            output.append(f'<code>{html.escape(token.content)}</code>')
        elif token.type == "em":
            output.append(f"<em>{inline_html(tokens, index + 1)[0]}</em>")
            index += 1
        elif token.type == "strong":
            output.append(f"<strong>{inline_html(tokens, index + 1)[0]}</strong>")
            index += 1
        elif token.type == "s":
            output.append(f"<del>{inline_html(tokens, index + 1)[0]}</del>")
            index += 1
        elif token.type == "link_open":
            href = token.attrGet("href", "")
            title = token.attrGet("title")
            title_attr = f' title="{html.escape(title)}"' if title else ""
            output.append(f'<a href="{html.escape(href, quote=True)}"{title_attr}>')
            index += 1
            child_output, index = inline_html(tokens, index)
            output.append(child_output)
            output.append("</a>")
        elif token.type == "link_close":
            output.append("</a>")
            index += 1
        elif token.type == "html_inline":
            # The source document contains no unsafe HTML; retain harmless inline tags.
            output.append(token.content)
        else:
            index += 1
    return "".join(output), index


def render_tokens(tokens: list) -> str:
    """Render the markdown token stream into print-friendly HTML."""
    output: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.type == "heading_open":
            level = int(token.tag[1])
            inline, index = inline_html(tokens, index + 1)
            output.append(f'<h{level}>{inline}</h{level}>')
        elif token.type == "paragraph_open":
            inline, index = inline_html(tokens, index + 1)
            output.append(f"<p>{inline}</p>")
        elif token.type == "fence" or token.type == "code_block":
            output.append(f'<pre><code>{html.escape(token.content.rstrip())}</code></pre>')
        elif token.type == "bullet_list_open":
            output.append("<ul>")
            index += 1
        elif token.type == "bullet_list_close":
            output.append("</ul>")
        elif token.type == "ordered_list_open":
            start = token.attrGet("start", "1")
            output.append(f'<ol start="{html.escape(start)}">')
            index += 1
        elif token.type == "ordered_list_close":
            output.append("</ol>")
        elif token.type == "list_item_open":
            output.append("<li>")
            index += 1
        elif token.type == "list_item_close":
            output.append("</li>")
        elif token.type == "table_open":
            output.append('<div class="table-wrap"><table>')
            index += 1
        elif token.type == "thead_open":
            output.append("<thead>")
            index += 1
        elif token.type == "tbody_open":
            output.append("<tbody>")
            index += 1
        elif token.type == "tr_open":
            output.append("<tr>")
            index += 1
        elif token.type == "th_open":
            output.append("<th>")
            index += 1
        elif token.type == "th_close":
            output.append("</th>")
            index += 1
        elif token.type == "td_open":
            output.append("<td>")
            index += 1
        elif token.type == "td_close":
            output.append("</td>")
            index += 1
        elif token.type == "hr":
            output.append("<hr>")
            index += 1
        elif token.type == "blockquote_open":
            output.append('<div class="callout">')
            index += 1
        elif token.type == "blockquote_close":
            output.append("</div>")
            index += 1
        elif token.type == "html_block":
            output.append(token.content)
            index += 1
        else:
            index += 1

    # Convert markdown table rows into their corresponding table rows. The token
    # stream above intentionally leaves table cells to a second pass so cells can
    # contain inline emphasis and links.
    table_open = 0
    for pos, token in enumerate(tokens):
        if token.type != "table_open":
            continue
        # This branch is not reached in normal execution; the loop above emits
        # an empty table wrapper. Replace it with a complete table when parsing.
        table_open += 1
    return "".join(output)


def render_markdown(markdown_text: str) -> str:
    """Convert the source Markdown to the HTML used by WeasyPrint."""
    md = MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": True})
    md.enable(["table", "strikethrough"])
    tokens = md.parse(markdown_text)

    # markdown-it emits table rows as tokens. Build the table structure in a
    # dedicated pass because cell content can contain nested inline tokens.
    output: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.type == "table_open":
            output.append('<div class="table-wrap"><table>')
            index += 1
            continue
        if token.type == "thead_open":
            output.append("<thead>")
            index += 1
            continue
        if token.type == "tbody_open":
            output.append("<tbody>")
            index += 1
            continue
        if token.type == "tr_open":
            output.append("<tr>")
            index += 1
            continue
        if token.type in {"th_open", "td_open"}:
            output.append(f"<{token.tag}>")
            index += 1
            continue
        if token.type in {"th_close", "td_close"}:
            output.append(f"</{token.tag[0:-5]}>")
            index += 1
            continue
        if token.type == "table_close":
            output.append("</tbody></table></div>")
            index += 1
            continue
        if token.type == "thead_close":
            output.append("</thead>")
            index += 1
            continue
        if token.type == "tbody_close":
            output.append("</tbody>")
            index += 1
            continue

        if token.type == "inline":
            output.append(inline_html(tokens, index + 1)[0])
            index += 1
        elif token.type == "heading_open":
            level = int(token.tag[1])
            output.append(f"<h{level}>{inline_html(tokens, index + 1)[0]}</h{level}>")
            index += 1
        elif token.type == "paragraph_open":
            output.append(f"<p>{inline_html(tokens, index + 1)[0]}</p>")
            index += 1
        elif token.type in {"fence", "code_block"}:
            output.append(f'<pre><code>{html.escape(token.content.rstrip())}</code></pre>')
            index += 1
        elif token.type == "bullet_list_open":
            output.append("<ul>")
            index += 1
        elif token.type == "bullet_list_close":
            output.append("</ul>")
            index += 1
        elif token.type == "ordered_list_open":
            output.append(f'<ol start="{html.escape(token.attrGet("start", "1"))}">')
            index += 1
        elif token.type == "ordered_list_close":
            output.append("</ol>")
            index += 1
        elif token.type == "list_item_open":
            output.append("<li>")
            index += 1
        elif token.type == "list_item_close":
            output.append("</li>")
            index += 1
        elif token.type == "hr":
            output.append("<hr>")
            index += 1
        elif token.type == "blockquote_open":
            output.append('<div class="callout">')
            index += 1
        elif token.type == "blockquote_close":
            output.append("</div>")
            index += 1
        elif token.type == "html_block":
            output.append(token.content)
            index += 1
        else:
            index += 1

    return "".join(output)


def source_sections(markdown_text: str) -> list[str]:
    """Return the document body starting at section 1, excluding the cover."""
    lines = markdown_text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("## 1."):
            return lines[index:]
    return lines


def cover_html() -> str:
    today = date.today().strftime("%d %B %Y")
    return f"""
<section class="cover">
  <div class="cover-grid">
    <div class="cover-brand">
      <div class="brand-mark"><span></span><span></span><span></span></div>
      <div class="eyebrow">DIGITAL TWIN OS · REVIEW EDITION</div>
      <h1>Smart College AI</h1>
      <p class="cover-subtitle">Project Review Document</p>
      <p class="cover-description">
        A full-stack Academic Management &amp; Digital Twin platform for students,
        faculty, and administrators.
      </p>
    </div>
    <div class="cover-facts">
      <div class="fact"><strong>Version</strong><span>2.5.0</span></div>
      <div class="fact"><strong>Backend</strong><span>Python 3</span></div>
      <div class="fact"><strong>Database</strong><span>Supabase / PostgreSQL</span></div>
      <div class="fact"><strong>Default port</strong><span>8080</span></div>
      <div class="fact"><strong>Prepared</strong><span>{today}</span></div>
    </div>
  </div>
  <div class="cover-foot">
    <span>Prepared for academic project review</span>
    <span>D:\\test\\smart-college-management</span>
  </div>
</section>
"""


def executive_html() -> str:
    return """
<section class="review-intro">
  <div class="section-kicker">REVIEW BRIEF</div>
  <h1>Executive Summary</h1>
  <p class="lead">
    Smart College AI is a browser-based academic management platform that acts as a
    digital twin of a student's academic life. It brings attendance, CGPA, fees,
    certificates, faculty information, and AI-assisted guidance into one workspace.
  </p>
  <div class="summary-grid">
    <div>
      <div class="summary-label">Students modeled</div>
      <div class="summary-value">20</div>
      <div class="summary-note">Representative records across six departments</div>
    </div>
    <div>
      <div class="summary-label">Staff modeled</div>
      <div class="summary-value">20</div>
      <div class="summary-note">HODs, faculty, deans, and officers</div>
    </div>
    <div>
      <div class="summary-label">Database objects</div>
      <div class="summary-value">9</div>
      <div class="summary-note">Supabase tables with seed data and RLS</div>
    </div>
    <div>
      <div class="summary-label">Primary interaction</div>
      <div class="summary-value">AI</div>
      <div class="summary-note">Rule-based academic guidance from live records</div>
    </div>
  </div>
  <div class="review-note">
    <strong>Review focus.</strong> Confirm the user journeys, backend contracts, data model,
    authentication behavior, AI responses, and test coverage before presenting the system.
    The default credentials and Supabase endpoint shown in this document are demonstration
    or configuration values and should be replaced before production use.
  </div>
</section>
"""


def toc_html(markdown_text: str) -> str:
    headings: list[tuple[int, str]] = []
    for line in source_sections(markdown_text).splitlines():
        match = re.match(r"^(#{2,4})\s+(.+?)\s*$", line)
        if match:
            headings.append((len(match.group(1)), match.group(2).replace("`", "")))
    items = []
    for level, heading in headings:
        anchor = slugify(heading)
        items.append(
            f'<a class="toc-link toc-{level}" href="#{anchor}">{html.escape(heading)}</a>'
        )
    return f'<nav class="toc">{"".join(items)}</nav>'


def build_html(markdown_text: str) -> str:
    body = render_markdown("\n".join(source_sections(markdown_text)))
    return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Smart College AI — Project Review Document</title>
  <style>
    :root {{
      --ink: #172033;
      --muted: #647084;
      --line: #dce3ec;
      --paper: #ffffff;
      --ground: #f4f6f8;
      --navy: #17324d;
      --blue: #2367a8;
      --blue-soft: #eaf2fa;
      --green: #287a61;
      --green-soft: #e9f5f0;
      --amber: #9a6519;
      --amber-soft: #fff5df;
      --shadow: 0 8px 24px rgba(23, 50, 77, .08);
    }}
    * {{ box-sizing: border-box; }}
    html {{ background: var(--ground); }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--ground);
      font-family: "Segoe UI", Arial, sans-serif;
      font-size: 10.2pt;
      line-height: 1.52;
      font-variant-numeric: tabular-nums;
    }}
    .page {{
      width: 100%;
      max-width: 1120px;
      margin: 24px auto;
      padding: 34px 38px 42px;
      background: var(--paper);
      box-shadow: var(--shadow);
    }}
    .cover {{
      min-height: 245mm;
      margin: 0;
      padding: 48px 54px 32px;
      background: var(--navy);
      color: #fff;
      box-shadow: none;
      position: relative;
      overflow: hidden;
      page: cover;
    }}
    .cover::before {{
      content: "";
      position: absolute;
      width: 180px;
      height: 180px;
      right: -70px;
      top: -55px;
      border: 1px solid rgba(255,255,255,.18);
      border-radius: 50%;
      box-shadow: 0 0 0 28px rgba(255,255,255,.04), 0 0 0 58px rgba(255,255,255,.025);
    }}
    .cover-grid {{ position: relative; z-index: 1; display: grid; grid-template-columns: minmax(0, 1fr) 220px; gap: 50px; align-items: end; }}
    .brand-mark {{ display: flex; gap: 5px; height: 31px; align-items: end; margin-bottom: 28px; }}
    .brand-mark span {{ display: block; width: 7px; background: #75c7c0; border-radius: 2px 2px 0 0; }}
    .brand-mark span:nth-child(1) {{ height: 17px; }}
    .brand-mark span:nth-child(2) {{ height: 27px; background: #a6d6c9; }}
    .brand-mark span:nth-child(3) {{ height: 22px; background: #f0c779; }}
    .eyebrow, .section-kicker {{ font-size: 8pt; font-weight: 700; letter-spacing: .14em; color: #75c7c0; }}
    .cover h1 {{ font-size: 42pt; line-height: 1.03; margin: 12px 0 7px; letter-spacing: -.035em; }}
    .cover-subtitle {{ margin: 0; color: #dce9f5; font-size: 17pt; letter-spacing: .02em; }}
    .cover-description {{ max-width: 580px; margin: 22px 0 0; color: #c9d8e5; font-size: 11pt; line-height: 1.6; }}
    .cover-facts {{ border-left: 1px solid rgba(255,255,255,.2); padding-left: 22px; }}
    .fact {{ margin-bottom: 16px; }}
    .fact:last-child {{ margin-bottom: 0; }}
    .fact strong, .fact span {{ display: block; }}
    .fact strong {{ color: #9db7cb; font-size: 7.5pt; letter-spacing: .1em; text-transform: uppercase; font-weight: 700; }}
    .fact span {{ margin-top: 3px; color: #fff; font-size: 10pt; }}
    .cover-foot {{ position: absolute; left: 54px; right: 54px; bottom: 25px; display: flex; justify-content: space-between; color: #9db7cb; font-size: 8pt; letter-spacing: .05em; }}
    .review-intro {{ padding: 2px 0 4px; }}
    .review-intro h1, .body-section h1 {{ string-set: chapter content(); }}
    h1 {{ color: var(--navy); font-size: 23pt; line-height: 1.12; letter-spacing: -.025em; margin: 0 0 18px; }}
    h2 {{ color: var(--navy); font-size: 15pt; line-height: 1.25; margin: 34px 0 11px; padding-top: 2px; break-after: avoid; }}
    h3 {{ color: var(--blue); font-size: 11.5pt; margin: 23px 0 8px; break-after: avoid; }}
    h4 {{ color: var(--navy); font-size: 10.3pt; margin: 17px 0 6px; break-after: avoid; }}
    p {{ margin: 0 0 11px; }}
    .lead {{ font-size: 12pt; line-height: 1.65; color: #34455a; max-width: 720px; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 23px 0 20px; }}
    .summary-grid > div {{ min-height: 105px; padding: 15px 14px; border: 1px solid var(--line); border-top: 3px solid var(--blue); background: #fbfcfd; }}
    .summary-label {{ color: var(--muted); font-size: 7.5pt; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
    .summary-value {{ margin-top: 7px; color: var(--navy); font-size: 21pt; font-weight: 700; line-height: 1; }}
    .summary-note {{ margin-top: 8px; color: var(--muted); font-size: 8.3pt; line-height: 1.35; }}
    .review-note, .callout {{ padding: 13px 16px; border-left: 3px solid var(--amber); background: var(--amber-soft); color: #674b1d; font-size: 9.5pt; margin: 18px 0; break-inside: avoid; }}
    .review-note strong, .callout strong {{ color: var(--navy); }}
    .toc {{ margin: 28px 0 30px; padding: 20px 22px; border: 1px solid var(--line); background: #fbfcfd; }}
    .toc-title {{ margin: 0 0 10px; color: var(--navy); font-size: 11pt; font-weight: 700; }}
    .toc a {{ display: block; color: #394b60; text-decoration: none; padding: 4px 0; font-size: 9.3pt; }}
    .toc a:hover, .toc a:focus {{ color: var(--blue); text-decoration: underline; }}
    .toc-2 {{ padding-left: 12px; color: var(--muted); font-size: 8.7pt; }}
    .toc-3 {{ padding-left: 24px; color: var(--muted); font-size: 8.4pt; }}
    .toc-4 {{ padding-left: 36px; color: var(--muted); font-size: 8.1pt; }}
    .toc-link::after {{ content: leader("·") target-counter(attr(href), page); color: var(--muted); }}
    .body-section {{ break-before: page; }}
    .body-section:first-child {{ break-before: auto; }}
    .body-section h1 {{ margin-top: 0; padding-bottom: 12px; border-bottom: 2px solid var(--blue); }}
    .body-section h2 {{ border-bottom: 1px solid var(--line); padding-bottom: 5px; }}
    .body-section h3 {{ color: var(--navy); }}
    .body-section p, .body-section li {{ max-width: 760px; }}
    .body-section ul, .body-section ol {{ padding-left: 23px; margin: 8px 0 14px; }}
    .body-section li {{ margin: 4px 0; }}
    .body-section a {{ color: var(--blue); text-decoration: none; }}
    pre {{ margin: 12px 0 18px; padding: 13px 15px; overflow-x: auto; background: #172033; color: #e8f0f7; border-radius: 4px; font: 8.2pt/1.45 "Consolas", "Courier New", monospace; white-space: pre; }}
    code {{ padding: 1px 4px; background: #edf2f6; border-radius: 3px; color: #17324d; font: 8.6pt "Consolas", "Courier New", monospace; }}
    pre code {{ padding: 0; background: transparent; color: inherit; }}
    .table-wrap {{ width: 100%; overflow-x: auto; margin: 12px 0 18px; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 570px; font-size: 8.3pt; }}
    th, td {{ border: 1px solid var(--line); padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: var(--navy); color: #fff; font-weight: 700; }}
    tbody tr:nth-child(even) {{ background: #f7f9fb; }}
    hr {{ border: 0; border-top: 1px solid var(--line); margin: 26px 0; }}
    blockquote {{ margin: 14px 0; padding: 12px 16px; border-left: 3px solid var(--blue); background: var(--blue-soft); color: #34455a; }}
    .page:last-child {{ margin-bottom: 0; }}
    @page {{
      size: A4;
      margin: 17mm 16mm 18mm;
      @top-left {{ content: "SMART COLLEGE AI"; color: #647084; font-size: 7.5pt; font-weight: 700; letter-spacing: .1em; }}
      @top-right {{ content: string(chapter); color: #647084; font-size: 7.5pt; }}
      @bottom-left {{ content: "PROJECT REVIEW · VERSION 2.5.0"; color: #647084; font-size: 7.2pt; letter-spacing: .05em; }}
      @bottom-right {{ content: "PAGE " counter(page) " OF " counter(pages); color: #647084; font-size: 7.2pt; }}
    }}
    @page cover {{ margin: 0; @top-left {{ content: none; }} @top-right {{ content: none; }} @bottom-left {{ content: none; }} @bottom-right {{ content: none; }} }}
    h1 {{ bookmark-level: 1; }}
    h2 {{ bookmark-level: 2; }}
    h3 {{ bookmark-level: 3; }}
    @media print {{
      body {{ background: #fff; }}
      .page {{ margin: 0; box-shadow: none; }}
      a {{ color: inherit; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    {cover_html()}
    {executive_html()}
    <div class="section-kicker">DOCUMENT MAP</div>
    <h2>Contents</h2>
    {toc_html(markdown_text)}
    {body}
  </main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    args = parser.parse_args()

    markdown_text = args.source.read_text(encoding="utf-8")
    html_text = build_html(markdown_text)
    args.html.write_text(html_text, encoding="utf-8")
    HTML(string=html_text, base_url=str(args.source.parent)).write_pdf(args.pdf)
    print(f"HTML: {args.html}")
    print(f"PDF:  {args.pdf}")


if __name__ == "__main__":
    main()
