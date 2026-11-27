"""
Generate Project_24I-3112_24I-3097_24I-0761_C.pdf
Uses Playwright to render the combined report HTML and print to PDF.
"""
import os
import re
from pathlib import Path

BASE_DIR = Path(r"C:\Users\DELL\.gemini\antigravity\scratch\expense-approval")
COMBINED_MD = BASE_DIR / "docs" / "team" / "Final_Project_Report_Combined.md"
OUT_PDF = BASE_DIR / "Project_24I-3112_24I-3097_24I-0761_C.pdf"

# Read markdown
with open(COMBINED_MD, "r", encoding="utf-8") as f:
    md_text = f.read()

# Simple markdown to HTML converter (tables, headings, code, bold)
def md_to_html(text):
    lines = text.split("\n")
    html_lines = []
    in_code = False
    in_table = False

    for line in lines:
        # Code block toggle
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
            html_lines.append(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            continue

        # Table rows
        if line.startswith("|"):
            if not in_table:
                html_lines.append("<table>")
                in_table = True
            cells = [c.strip() for c in line.split("|")[1:-1]]
            # Detect separator row
            if all(re.match(r"^[-:]+$", c) for c in cells if c):
                continue
            # Detect header (first row)
            tag = "th" if not any("<td>" in h for h in html_lines[-5:]) else "td"
            # Actually determine if header by looking backwards  
            prev_non_empty = ""
            for prev in reversed(html_lines):
                if prev.strip():
                    prev_non_empty = prev
                    break
            if prev_non_empty.endswith("<table>") or prev_non_empty.endswith("</tr>") and "th" in prev_non_empty:
                tag = "th"
            else:
                tag = "td"
            row_html = "<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>"
            html_lines.append(row_html)
            continue
        else:
            if in_table:
                html_lines.append("</table>")
                in_table = False

        # Headings
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            content = m.group(2)
            html_lines.append(f"<h{level}>{content}</h{level}>")
            continue

        # Horizontal rule
        if re.match(r"^---+$", line.strip()):
            html_lines.append("<hr>")
            continue

        # Blank line -> paragraph break
        if not line.strip():
            html_lines.append("<br>")
            continue

        # Inline formatting
        line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        line = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line)
        line = re.sub(r"`(.+?)`", r"<code>\1</code>", line)
        line = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", line)  # strip links
        # Blockquotes
        if line.startswith("> "):
            line = f"<blockquote>{line[2:]}</blockquote>"
        # List items
        elif line.startswith("- ") or line.startswith("* "):
            line = f"<li>{line[2:]}</li>"
        else:
            line = f"<p>{line}</p>"
        html_lines.append(line)

    if in_table:
        html_lines.append("</table>")
    if in_code:
        html_lines.append("</code></pre>")

    return "\n".join(html_lines)

html_body = md_to_html(md_text)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SE3002 SQE Final Project Report — Group 24I-3112/24I-3097/24I-0761 Section C</title>
<style>
  @page {{ size: A4; margin: 20mm 18mm; }}
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 11px;
    line-height: 1.5;
    color: #1a1a1a;
    max-width: 100%;
  }}
  h1 {{ font-size: 20px; color: #1565C0; border-bottom: 2px solid #1565C0; padding-bottom: 6px; margin-top: 20px; }}
  h2 {{ font-size: 16px; color: #1565C0; margin-top: 16px; border-bottom: 1px solid #90CAF9; padding-bottom: 4px; }}
  h3 {{ font-size: 13px; color: #0D47A1; margin-top: 12px; }}
  h4, h5, h6 {{ font-size: 11px; color: #1976D2; margin-top: 8px; }}
  table {{
    border-collapse: collapse;
    width: 100%;
    font-size: 10px;
    margin: 8px 0;
    page-break-inside: avoid;
  }}
  th, td {{
    border: 1px solid #BBDEFB;
    padding: 4px 6px;
    text-align: left;
    vertical-align: top;
  }}
  th {{ background: #E3F2FD; font-weight: bold; color: #0D47A1; }}
  tr:nth-child(even) {{ background: #F8FBFF; }}
  code {{
    background: #F5F5F5;
    padding: 1px 4px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 10px;
    color: #C62828;
  }}
  pre {{
    background: #F5F5F5;
    padding: 8px 10px;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 9px;
    border-left: 3px solid #1565C0;
    page-break-inside: avoid;
  }}
  pre code {{
    background: none;
    padding: 0;
    color: #1a1a1a;
  }}
  blockquote {{
    border-left: 4px solid #1565C0;
    margin: 6px 0;
    padding: 4px 10px;
    background: #E8F5E9;
    color: #1B5E20;
  }}
  hr {{ border: none; border-top: 1px solid #BBDEFB; margin: 16px 0; }}
  li {{ margin: 2px 0; }}
  p {{ margin: 4px 0; }}
  strong {{ color: #0D47A1; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

# Write temp HTML
html_path = BASE_DIR / "docs" / "team" / "final_report_temp.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"HTML written to: {html_path}")

# Generate PDF
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"file:///{html_path}".replace("\\", "/"))
    page.wait_for_load_state("domcontentloaded")
    page.pdf(
        path=str(OUT_PDF),
        format="A4",
        margin={"top": "20mm", "right": "18mm", "bottom": "20mm", "left": "18mm"},
        print_background=True,
        display_header_footer=True,
        header_template='<div style="font-size:9px;color:#666;width:100%;text-align:center;">SE3002 SQE Final Project — Group 24I-3112/24I-3097/24I-0761 Section C</div>',
        footer_template='<div style="font-size:9px;color:#666;width:100%;text-align:center;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>',
    )
    browser.close()

print(f"PDF generated: {OUT_PDF}")
print(f"PDF size: {OUT_PDF.stat().st_size:,} bytes")

# Remove temp HTML
html_path.unlink()
print("Temp HTML removed.")
