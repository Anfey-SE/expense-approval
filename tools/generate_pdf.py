"""
Academic PDF Generator for SE3002 SQE Final Project Report
FAST National University of Computer and Emerging Sciences
Generates: Project_24I-3112_24I-3097_24I-0761_C.pdf
"""
import os
import re
import base64
from pathlib import Path

BASE_DIR = Path(r"C:\Users\DELL\.gemini\antigravity\scratch\expense-approval")
COMBINED_MD = BASE_DIR / "docs" / "team" / "Final_Project_Report_Combined.md"
OUT_PDF = BASE_DIR / "Project_24I-3112_24I-3097_24I-0761_C.pdf"
TEMP_HTML = BASE_DIR / "docs" / "team" / "final_report_temp.html"

def encode_image(rel_path):
    img_path = BASE_DIR / rel_path
    if not img_path.exists():
        return None, None
    ext = img_path.suffix.lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext[1:], "image/png")
    with open(img_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return mime, data

with open(COMBINED_MD, "r", encoding="utf-8") as f:
    md_text = f.read()

# Filter any remaining emojis or awkward steric characters
emoji_replacements = {
    '✅': '[Passed]',
    '🔄': '[In Progress]',
    '⚠️': '[Accepted]',
    '❌': '[Failed]',
    '✓': '[Passed]',
    '✗': '[Failed]',
    '✕': '[x]',
    '🟢': '[Approved]',
    '🎯': '',
    '👉': '',
    '📸': 'Figure: ',
    '🎉': '',
    '⚡': '',
    '🔥': '',
    '🚀': '',
}
for k, v in emoji_replacements.items():
    md_text = md_text.replace(k, v)

# Clean excessive asterisks (e.g. *** or ****)
md_text = re.sub(r'\*{3,}', '**', md_text)

def md_to_html(text):
    lines = text.split("\n")
    html_lines = []
    in_code = False
    in_table = False
    table_header_done = False

    for line in lines:
        if line.startswith("```"):
            if in_code:
                html_lines.append("</code></pre>")
                in_code = False
            else:
                lang = line[3:].strip()
                html_lines.append(f'<pre><code class="{lang}">')
                in_code = True
            continue

        if in_code:
            safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html_lines.append(safe)
            continue

        # Image parsing: ![alt](path)
        img_match = re.match(r"!\[([^\]]*)\]\(([^\)]+)\)", line.strip())
        if img_match:
            if in_table:
                html_lines.append("</table>")
                in_table = False
                table_header_done = False
            alt = img_match.group(1)
            rel_path = img_match.group(2)
            mime, b64 = encode_image(rel_path)
            if mime and b64:
                html_lines.append(
                    f'<figure class="report-figure">'
                    f'<img src="data:{mime};base64,{b64}" alt="{alt}">'
                    f'<figcaption>{alt}</figcaption>'
                    f'</figure>'
                )
            else:
                html_lines.append(f'<p class="missing-image">[Figure: {alt} ({rel_path})]</p>')
            continue

        # Table parsing
        if line.startswith("|"):
            if not in_table:
                html_lines.append('<table class="academic-table">')
                in_table = True
                table_header_done = False
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if all(re.match(r"^[-:]+$", c) for c in cells if c):
                table_header_done = True
                continue
            tag = "th" if not table_header_done else "td"
            proc_cells = []
            for c in cells:
                c = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", c)
                c = re.sub(r"\*(.+?)\*", r"<em>\1</em>", c)
                c = re.sub(r"`(.+?)`", r"<code>\1</code>", c)
                c = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", c)
                proc_cells.append(c)
            row = "<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in proc_cells) + "</tr>"
            html_lines.append(row)
            continue
        else:
            if in_table:
                html_lines.append("</table>")
                in_table = False
                table_header_done = False

        # Headings
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            content = m.group(2)
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
            content = re.sub(r"`(.+?)`", r"<code>\1</code>", content)
            html_lines.append(f"<h{level}>{content}</h{level}>")
            continue

        # Horizontal rule
        if re.match(r"^---+$", line.strip()):
            html_lines.append('<hr class="section-divider">')
            continue

        # Empty line
        if not line.strip():
            html_lines.append("")
            continue

        # Blockquote
        if line.startswith("> "):
            inner = line[2:]
            inner = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", inner)
            inner = re.sub(r"\*(.+?)\*", r"<em>\1</em>", inner)
            inner = re.sub(r"`(.+?)`", r"<code>\1</code>", inner)
            html_lines.append(f'<blockquote class="academic-note">{inner}</blockquote>')
            continue

        # Unordered list items
        if re.match(r"^\s*[-*]\s+", line):
            inner = re.sub(r"^\s*[-*]\s+", "", line)
            inner = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", inner)
            inner = re.sub(r"\*(.+?)\*", r"<em>\1</em>", inner)
            inner = re.sub(r"`(.+?)`", r"<code>\1</code>", inner)
            inner = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", inner)
            html_lines.append(f'<li class="academic-li">{inner}</li>')
            continue

        # Task list items
        if re.match(r"^\s*- \[.\]", line):
            inner = re.sub(r"^\s*- \[.\]\s*", "", line)
            inner = re.sub(r"`(.+?)`", r"<code>\1</code>", inner)
            html_lines.append(f'<li class="academic-li">{inner}</li>')
            continue

        # Standard paragraph
        p = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        p = re.sub(r"\*(.+?)\*", r"<em>\1</em>", p)
        p = re.sub(r"`(.+?)`", r"<code>\1</code>", p)
        p = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", p)
        if p.strip():
            html_lines.append(f"<p>{p}</p>")

    if in_table:
        html_lines.append("</table>")
    if in_code:
        html_lines.append("</code></pre>")
    return "\n".join(html_lines)

print("Converting markdown to academic HTML document...")
html_body = md_to_html(md_text)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SE3002 SQE Final Project Report — Group 24i-3112, 24i-3097, 24i-0761 (Section C)</title>
<style>
  @page {{
    size: A4;
    margin: 22mm 18mm 22mm 18mm;
  }}
  body {{
    font-family: 'Segoe UI', Arial, Helvetica, sans-serif;
    font-size: 10pt;
    line-height: 1.6;
    color: #1A202C;
    background-color: #FFFFFF;
  }}
  h1 {{
    font-size: 18pt;
    font-weight: 700;
    color: #1A365D;
    border-bottom: 2px solid #2B6CB0;
    padding-bottom: 6px;
    margin-top: 24px;
    margin-bottom: 12px;
    page-break-after: avoid;
  }}
  h2 {{
    font-size: 14pt;
    font-weight: 700;
    color: #2B6CB0;
    border-bottom: 1px solid #CBD5E0;
    padding-bottom: 4px;
    margin-top: 20px;
    margin-bottom: 10px;
    page-break-after: avoid;
  }}
  h3 {{
    font-size: 11.5pt;
    font-weight: 600;
    color: #2D3748;
    margin-top: 14px;
    margin-bottom: 8px;
    page-break-after: avoid;
  }}
  h4 {{
    font-size: 10.5pt;
    font-weight: 600;
    color: #4A5568;
    margin-top: 10px;
    margin-bottom: 6px;
    page-break-after: avoid;
  }}
  p {{
    margin-top: 0;
    margin-bottom: 8px;
    text-align: justify;
  }}
  table.academic-table {{
    border-collapse: collapse;
    width: 100%;
    font-size: 9pt;
    margin: 10px 0 14px 0;
    page-break-inside: avoid;
    box-shadow: 0 0 0 1px #CBD5E0;
  }}
  table.academic-table th, table.academic-table td {{
    border: 1px solid #E2E8F0;
    padding: 5px 7px;
    text-align: left;
    vertical-align: top;
  }}
  table.academic-table th {{
    background-color: #EDF2F7;
    font-weight: 700;
    color: #1A365D;
    border-bottom: 2px solid #CBD5E0;
  }}
  table.academic-table tr:nth-child(even) {{
    background-color: #F8FAFC;
  }}
  code {{
    background-color: #F1F5F9;
    padding: 1px 4px;
    border-radius: 3px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 9pt;
    color: #991B1B;
    border: 1px solid #E2E8F0;
  }}
  pre {{
    background-color: #1E293B;
    color: #F8FAFC;
    padding: 10px 14px;
    border-radius: 4px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 8.5pt;
    line-height: 1.45;
    border-left: 4px solid #2B6CB0;
    page-break-inside: avoid;
    overflow-x: hidden;
    white-space: pre-wrap;
    word-break: break-all;
    margin: 8px 0;
  }}
  pre code {{
    background: none;
    border: none;
    padding: 0;
    color: #F8FAFC;
    font-size: 8.5pt;
  }}
  blockquote.academic-note {{
    border-left: 4px solid #2B6CB0;
    margin: 10px 0;
    padding: 6px 14px;
    background-color: #F1F5F9;
    color: #2D3748;
    font-size: 9.5pt;
    page-break-inside: avoid;
  }}
  hr.section-divider {{
    border: none;
    border-top: 1px solid #CBD5E0;
    margin: 18px 0;
  }}
  li.academic-li {{
    margin: 3px 0;
  }}
  figure.report-figure {{
    margin: 14px 0 18px 0;
    text-align: center;
    page-break-inside: avoid;
  }}
  figure.report-figure img {{
    max-width: 95%;
    max-height: 290px;
    object-fit: contain;
    border: 1px solid #CBD5E0;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }}
  figure.report-figure figcaption {{
    font-size: 8.5pt;
    font-style: italic;
    color: #4A5568;
    margin-top: 5px;
    font-weight: 500;
  }}
  strong {{
    color: #1A365D;
    font-weight: 600;
  }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

with open(TEMP_HTML, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Academic HTML generated ({len(html):,} bytes)")

from playwright.sync_api import sync_playwright
print("Rendering PDF via Playwright Chromium...")
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"file:///{TEMP_HTML}".replace("\\", "/"))
    page.wait_for_load_state("networkidle")
    page.pdf(
        path=str(OUT_PDF),
        format="A4",
        margin={"top": "20mm", "right": "18mm", "bottom": "20mm", "left": "18mm"},
        print_background=True,
        display_header_footer=True,
        header_template='<div style="font-family: Arial, sans-serif; font-size: 8pt; color: #718096; width: 100%; text-align: center; padding-top: 4px;">FAST-NUCES Islamabad — SE3002 Software Quality Engineering (Fall 2026) | Group 24i-3112, 24i-3097, 24i-0761</div>',
        footer_template='<div style="font-family: Arial, sans-serif; font-size: 8pt; color: #718096; width: 100%; text-align: center; padding-bottom: 4px;">Section C — Final Quality Engineering Report | Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>',
    )
    browser.close()

TEMP_HTML.unlink()
size = OUT_PDF.stat().st_size
print(f"PDF successfully rendered: {OUT_PDF}")
print(f"Final PDF size: {size:,} bytes ({size/1024/1024:.2f} MB)")
