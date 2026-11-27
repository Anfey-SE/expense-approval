"""
Generate Project_24I-3112_24I-3097_24I-0761_C.pdf
Uses Playwright to render the combined report HTML and print to PDF.
Embeds screenshots as base64 inline images.
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
    """Encode image as base64 data URI."""
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

        # Image: ![alt](path)
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
                html_lines.append(f'<div class="screenshot"><img src="data:{mime};base64,{b64}" alt="{alt}" style="max-width:100%;border:1px solid #ccc;border-radius:4px;margin:8px 0;"><p class="caption">{alt}</p></div>')
            else:
                html_lines.append(f'<p><em>[Image not found: {rel_path}]</em></p>')
            continue

        # Table rows
        if line.startswith("|"):
            if not in_table:
                html_lines.append('<table>')
                in_table = True
                table_header_done = False
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if all(re.match(r"^[-:]+$", c) for c in cells if c):
                table_header_done = True
                continue
            tag = "th" if not table_header_done else "td"
            # Inline format cells
            proc_cells = []
            for c in cells:
                c = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", c)
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

        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            content = m.group(2)
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
            content = re.sub(r"`(.+?)`", r"<code>\1</code>", content)
            html_lines.append(f"<h{level}>{content}</h{level}>")
            continue

        if re.match(r"^---+$", line.strip()):
            html_lines.append("<hr>")
            continue

        if not line.strip():
            html_lines.append("")
            continue

        # Blockquote
        if line.startswith("> "):
            inner = line[2:]
            inner = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", inner)
            inner = re.sub(r"`(.+?)`", r"<code>\1</code>", inner)
            html_lines.append(f"<blockquote>{inner}</blockquote>")
            continue

        # List items
        if re.match(r"^\s*[-*]\s+", line):
            inner = re.sub(r"^\s*[-*]\s+", "", line)
            inner = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", inner)
            inner = re.sub(r"`(.+?)`", r"<code>\1</code>", inner)
            inner = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", inner)
            html_lines.append(f"<li>{inner}</li>")
            continue

        if re.match(r"^\s*- \[.\]", line):
            inner = re.sub(r"^\s*- \[.\]\s*", "", line)
            inner = re.sub(r"`(.+?)`", r"<code>\1</code>", inner)
            html_lines.append(f"<li>{inner}</li>")
            continue

        # Paragraph
        line2 = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        line2 = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line2)
        line2 = re.sub(r"`(.+?)`", r"<code>\1</code>", line2)
        line2 = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", line2)
        if line2.strip():
            html_lines.append(f"<p>{line2}</p>")

    if in_table:
        html_lines.append("</table>")
    if in_code:
        html_lines.append("</code></pre>")
    return "\n".join(html_lines)

print("Converting markdown to HTML...")
html_body = md_to_html(md_text)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SE3002 SQE Final Project Report — Group 24I-3112/24I-3097/24I-0761 Section C</title>
<style>
  @page {{ size: A4; margin: 18mm 16mm 20mm 16mm; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 10.5px; line-height: 1.55; color: #1a1a1a; }}
  h1 {{ font-size: 19px; color: #1565C0; border-bottom: 2.5px solid #1565C0; padding-bottom: 5px; margin-top: 20px; page-break-before: auto; }}
  h2 {{ font-size: 15px; color: #1565C0; margin-top: 15px; border-bottom: 1px solid #90CAF9; padding-bottom: 3px; }}
  h3 {{ font-size: 12px; color: #0D47A1; margin-top: 10px; }}
  h4, h5, h6 {{ font-size: 10.5px; color: #1976D2; margin-top: 7px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 9.5px; margin: 7px 0; page-break-inside: avoid; }}
  th, td {{ border: 1px solid #BBDEFB; padding: 3px 5px; text-align: left; vertical-align: top; }}
  th {{ background: #E3F2FD; font-weight: bold; color: #0D47A1; }}
  tr:nth-child(even) {{ background: #F8FBFF; }}
  code {{ background: #F5F5F5; padding: 1px 3px; border-radius: 2px; font-family: 'Courier New', monospace; font-size: 9.5px; color: #C62828; }}
  pre {{ background: #1E1E1E; color: #D4D4D4; padding: 7px 10px; border-radius: 4px; font-size: 8.5px; border-left: 3px solid #1565C0; page-break-inside: avoid; overflow: hidden; }}
  pre code {{ background: none; padding: 0; color: #D4D4D4; font-size: 8.5px; }}
  blockquote {{ border-left: 4px solid #1565C0; margin: 5px 0; padding: 4px 10px; background: #E8F5E9; color: #1B5E20; font-size: 10px; }}
  hr {{ border: none; border-top: 1px solid #BBDEFB; margin: 14px 0; }}
  li {{ margin: 2px 0; }}
  p {{ margin: 3px 0; }}
  strong {{ color: #0D47A1; }}
  .screenshot {{ margin: 10px 0; page-break-inside: avoid; text-align: center; }}
  .screenshot img {{ max-width: 95%; max-height: 280px; object-fit: contain; }}
  .caption {{ font-size: 9px; color: #555; font-style: italic; margin-top: 3px; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

with open(TEMP_HTML, "w", encoding="utf-8") as f:
    f.write(html)
print(f"HTML written ({len(html):,} bytes)")

from playwright.sync_api import sync_playwright
print("Generating PDF via Playwright...")
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"file:///{TEMP_HTML}".replace("\\", "/"))
    page.wait_for_load_state("networkidle")
    page.pdf(
        path=str(OUT_PDF),
        format="A4",
        margin={"top": "18mm", "right": "16mm", "bottom": "20mm", "left": "16mm"},
        print_background=True,
        display_header_footer=True,
        header_template='<div style="font-size:8px;color:#888;width:100%;text-align:center;padding-top:5px;">SE3002 SQE Final Project — Group 24I-3112 / 24I-3097 / 24I-0761 — Section C</div>',
        footer_template='<div style="font-size:8px;color:#888;width:100%;text-align:center;padding-bottom:5px;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>',
    )
    browser.close()

TEMP_HTML.unlink()
size = OUT_PDF.stat().st_size
print(f"PDF generated: {OUT_PDF}")
print(f"PDF size: {size:,} bytes ({size/1024/1024:.2f} MB)")
