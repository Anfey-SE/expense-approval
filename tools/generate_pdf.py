"""
Academic PDF Generator for SE3002 SQE Final Project Report
FAST National University of Computer and Emerging Sciences
Generates: Project_24I-3112_24I-3097_24I-0761_C.pdf
Styling: Times New Roman, 12pt font, 1.5 line spacing, Title Page with FAST Logo, Table of Contents
"""
import os
import re
import base64
from pathlib import Path

BASE_DIR = Path(r"C:\Users\DELL\.gemini\antigravity\scratch\expense-approval")
COMBINED_MD = BASE_DIR / "docs" / "team" / "Final_Project_Report_Combined.md"
OUT_PDF = BASE_DIR / "Project_24I-3112_24I-3097_24I-0761_C.pdf"
TEMP_HTML = BASE_DIR / "docs" / "team" / "final_report_temp.html"
LOGO_PATH = BASE_DIR / "docs" / "team" / "evidence" / "fast_logo.jpg"

def get_base64_image(file_path):
    if not file_path.exists():
        return None, None
    ext = file_path.suffix.lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext[1:], "image/jpeg")
    with open(file_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return mime, data

logo_mime, logo_b64 = get_base64_image(LOGO_PATH)

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

# Filter any remaining emojis or awkward characters
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

print("Converting main markdown content to HTML...")
main_body_html = md_to_html(md_text)

# Build Title Page (Page 1)
logo_img_tag = f'<img src="data:{logo_mime};base64,{logo_b64}" alt="FAST University Logo" class="title-logo">' if logo_b64 else ''

title_page_html = f"""
<div class="title-page">
  {logo_img_tag}
  <h1 class="univ-title">National University of Computer &amp; Emerging Sciences</h1>
  <h2 class="univ-sub">Department of Computer Science / Software Engineering</h2>
  <h3 class="campus-sub">Islamabad Campus</h3>

  <div class="title-spacer-sm"></div>

  <h3 class="course-heading">SE3002: Software Quality Engineering</h3>
  <h4 class="semester-heading">Semester Project — Fall 2026</h4>

  <div class="title-spacer-sm"></div>

  <div class="project-box">
    <h2 class="project-title">Automated Testing of Expense Approval MIS</h2>
    <p class="project-sub">Comprehensive Quality Engineering Report &amp; Verification Evidence</p>
  </div>

  <div class="title-spacer-md"></div>

  <table class="members-table">
    <thead>
      <tr>
        <th>Role</th>
        <th>Member Name</th>
        <th>Roll Number</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Member 1</strong></td>
        <td>Amna Hafeez</td>
        <td>24I-3112</td>
      </tr>
      <tr>
        <td><strong>Member 2</strong></td>
        <td>Humna Attique</td>
        <td>24I-3097</td>
      </tr>
      <tr>
        <td><strong>Member 3</strong></td>
        <td>Uswa Shafiq</td>
        <td>24I-0761</td>
      </tr>
    </tbody>
  </table>

  <div class="title-spacer-sm"></div>

  <p class="section-badge"><strong>Section:</strong> SE-C</p>
  <p class="date-badge">Submission Date: Fall Semester 2026</p>
</div>
<div class="page-break"></div>
"""

# Build Table of Contents Page (Page 2)
toc_page_html = """
<div class="toc-page">
  <h1 class="toc-title">Table of Contents</h1>
  
  <table class="toc-table">
    <thead>
      <tr>
        <th style="width: 15%;">Section</th>
        <th style="width: 70%;">Topic &amp; Description</th>
        <th style="width: 15%; text-align: right;">Page</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>1.0</strong></td>
        <td><strong>System Description, Installation, and Scope</strong><br><span class="toc-sub">Project identity, baseline verification, business rules, and execution commands</span></td>
        <td style="text-align: right;">3</td>
      </tr>
      <tr>
        <td><strong>2.0</strong></td>
        <td><strong>Shared Test Management Plan and Three-Point Effort Estimation</strong><br><span class="toc-sub">5-week testing schedule, O/M/P formula estimations vs actual effort, variance analysis</span></td>
        <td style="text-align: right;">6</td>
      </tr>
      <tr>
        <td><strong>3.0</strong></td>
        <td><strong>Requirements Traceability Matrix (RTM)</strong><br><span class="toc-sub">Bidirectional mapping of 16 functional requirements and 4 business rules to test suites</span></td>
        <td style="text-align: right;">8</td>
      </tr>
      <tr>
        <td><strong>4.0</strong></td>
        <td><strong>5×5 Risk Register and Measurable Exit Criteria</strong><br><span class="toc-sub">8 product risks, 2 project risks, and verification status for EC-1, EC-2, and EC-3</span></td>
        <td style="text-align: right;">10</td>
      </tr>
      <tr>
        <td><strong>5.0</strong></td>
        <td><strong>Test Monitoring, GQM Metrics, and Completion Report</strong><br><span class="toc-sub">Goal-Question-Metric analysis, residual risk mitigations, release recommendation</span></td>
        <td style="text-align: right;">13</td>
      </tr>
      <tr>
        <td><strong>6.0</strong></td>
        <td><strong>Six-Week Progress Tracking Reports</strong><br><span class="toc-sub">Weekly progress reports from baseline establishment to final release sign-off</span></td>
        <td style="text-align: right;">17</td>
      </tr>
      <tr>
        <td><strong>7.0</strong></td>
        <td><strong>Member 1 Contribution (Amna Hafeez — 24I-3112)</strong><br><span class="toc-sub">SonarQube static analysis, JaCoCo 100% white-box unit tests, PIT custom mutation, CI gate, UC1/UC2</span></td>
        <td style="text-align: right;">21</td>
      </tr>
      <tr>
        <td><strong>8.0</strong></td>
        <td><strong>Member 2 Contribution (Humna Attique — 24I-3097)</strong><br><span class="toc-sub">OpenAPI 3.0 specification, automated EP/BVA test generator, 120 API tests, UC3/UC4 review flows</span></td>
        <td style="text-align: right;">25</td>
      </tr>
      <tr>
        <td><strong>9.0</strong></td>
        <td><strong>Member 3 Contribution (Uswa Shafiq — 24I-0761)</strong><br><span class="toc-sub">WCAG 2.1 AA accessibility audits, defensive security scans, k6 load testing, ACID recovery, UC5/UC6, RCA</span></td>
        <td style="text-align: right;">33</td>
      </tr>
      <tr>
        <td><strong>10.0</strong></td>
        <td><strong>Consolidated AI Usage and Academic Authorship Disclosures</strong><br><span class="toc-sub">Individual prompt logs, tool consultation records, and independent authorship verifications</span></td>
        <td style="text-align: right;">39</td>
      </tr>
      <tr>
        <td><strong>Appendix</strong></td>
        <td><strong>Build Traceability and Git Commit Log</strong><br><span class="toc-sub">Chronological commit and pull request merge history on master branch</span></td>
        <td style="text-align: right;">43</td>
      </tr>
    </tbody>
  </table>
</div>
<div class="page-break"></div>
"""

# Build Full Document HTML
full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SE3002 SQE Final Project Report — Group 24I-3112, 24I-3097, 24I-0761 (Section SE-C)</title>
<style>
  @page {{
    size: A4;
    margin: 22mm 20mm 22mm 20mm;
  }}
  
  body {{
    font-family: 'Times New Roman', Times, Georgia, serif;
    font-size: 12pt;
    line-height: 1.5;
    color: #111111;
    background-color: #FFFFFF;
    margin: 0;
    padding: 0;
  }}

  /* Page Breaks */
  .page-break {{
    page-break-after: always;
    break-after: page;
  }}

  /* Title Page Styling */
  .title-page {{
    text-align: center;
    padding-top: 15px;
    height: 90vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }}
  .title-logo {{
    max-width: 140px;
    max-height: 140px;
    height: auto;
    margin-bottom: 18px;
    object-fit: contain;
  }}
  .univ-title {{
    font-size: 19pt;
    font-weight: bold;
    text-transform: uppercase;
    color: #002B49;
    margin: 0 0 6px 0;
    letter-spacing: 0.5px;
  }}
  .univ-sub {{
    font-size: 14pt;
    font-weight: normal;
    color: #333333;
    margin: 0 0 4px 0;
  }}
  .campus-sub {{
    font-size: 12.5pt;
    font-style: italic;
    color: #555555;
    margin: 0 0 10px 0;
  }}
  .course-heading {{
    font-size: 14pt;
    font-weight: bold;
    color: #111111;
    margin: 8px 0 2px 0;
  }}
  .semester-heading {{
    font-size: 12.5pt;
    font-weight: normal;
    color: #444444;
    margin: 0 0 8px 0;
  }}
  .title-spacer-sm {{
    height: 16px;
  }}
  .title-spacer-md {{
    height: 24px;
  }}
  .project-box {{
    border-top: 2.5px solid #002B49;
    border-bottom: 2.5px solid #002B49;
    padding: 14px 20px;
    margin: 12px auto;
    width: 90%;
  }}
  .project-title {{
    font-size: 17pt;
    font-weight: bold;
    color: #002B49;
    text-transform: uppercase;
    margin: 0 0 6px 0;
    line-height: 1.3;
  }}
  .project-sub {{
    font-size: 12pt;
    color: #333333;
    margin: 0;
    font-style: italic;
  }}
  .members-table {{
    width: 85%;
    margin: 10px auto;
    border-collapse: collapse;
    font-size: 12pt;
    line-height: 1.4;
  }}
  .members-table th, .members-table td {{
    border: 1.5px solid #333333;
    padding: 7px 14px;
    text-align: left;
  }}
  .members-table th {{
    background-color: #EBF2F7;
    font-weight: bold;
    color: #002B49;
  }}
  .section-badge {{
    font-size: 13pt;
    font-weight: bold;
    color: #111111;
    margin: 10px 0 3px 0;
  }}
  .date-badge {{
    font-size: 11.5pt;
    color: #555555;
    margin: 0;
  }}

  /* Table of Contents Styling */
  .toc-page {{
    padding-top: 15px;
  }}
  .toc-title {{
    font-size: 18pt;
    font-weight: bold;
    color: #002B49;
    border-bottom: 2px solid #002B49;
    padding-bottom: 6px;
    margin-bottom: 18px;
    text-transform: uppercase;
  }}
  .toc-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 11.5pt;
    line-height: 1.45;
  }}
  .toc-table th, .toc-table td {{
    padding: 8px 10px;
    border-bottom: 1px solid #D2D6DC;
    vertical-align: top;
  }}
  .toc-table th {{
    background-color: #F3F4F6;
    color: #002B49;
    font-weight: bold;
    border-bottom: 2px solid #002B49;
  }}
  .toc-sub {{
    font-size: 10pt;
    color: #555555;
    font-style: italic;
  }}

  /* Main Body Headings */
  h1 {{
    font-size: 17pt;
    font-weight: bold;
    color: #002B49;
    border-bottom: 1.5px solid #002B49;
    padding-bottom: 5px;
    margin-top: 26px;
    margin-bottom: 12px;
    page-break-after: avoid;
    line-height: 1.3;
  }}
  h2 {{
    font-size: 14pt;
    font-weight: bold;
    color: #004080;
    border-bottom: 1px solid #CBD5E0;
    padding-bottom: 4px;
    margin-top: 20px;
    margin-bottom: 10px;
    page-break-after: avoid;
    line-height: 1.35;
  }}
  h3 {{
    font-size: 12.5pt;
    font-weight: bold;
    color: #222222;
    margin-top: 16px;
    margin-bottom: 8px;
    page-break-after: avoid;
  }}
  h4 {{
    font-size: 12pt;
    font-weight: bold;
    color: #333333;
    margin-top: 12px;
    margin-bottom: 6px;
    page-break-after: avoid;
  }}

  p {{
    margin-top: 0;
    margin-bottom: 10px;
    text-align: justify;
    line-height: 1.5;
  }}

  /* Tables */
  table.academic-table {{
    border-collapse: collapse;
    width: 100%;
    font-size: 11pt;
    line-height: 1.4;
    margin: 12px 0 16px 0;
    page-break-inside: avoid;
  }}
  table.academic-table th, table.academic-table td {{
    border: 1px solid #4B5563;
    padding: 6px 8px;
    text-align: left;
    vertical-align: top;
  }}
  table.academic-table th {{
    background-color: #F3F4F6;
    font-weight: bold;
    color: #002B49;
    border-bottom: 1.5px solid #1F2937;
  }}
  table.academic-table tr:nth-child(even) {{
    background-color: #FAFAFA;
  }}

  /* Code Blocks */
  code {{
    background-color: #F3F4F6;
    padding: 1px 4px;
    border-radius: 2px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 10.5pt;
    color: #8B0000;
    border: 1px solid #E5E7EB;
  }}
  pre {{
    background-color: #F8F9FA;
    color: #111827;
    padding: 10px 14px;
    border-radius: 3px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 10pt;
    line-height: 1.4;
    border-left: 3.5px solid #002B49;
    border: 1px solid #E5E7EB;
    border-left-width: 3.5px;
    border-left-color: #002B49;
    page-break-inside: avoid;
    overflow-x: hidden;
    white-space: pre-wrap;
    word-break: break-all;
    margin: 10px 0;
  }}
  pre code {{
    background: none;
    border: none;
    padding: 0;
    color: #111827;
    font-size: 10pt;
  }}

  /* Blockquotes / Notes */
  blockquote.academic-note {{
    border-left: 3.5px solid #002B49;
    margin: 12px 0;
    padding: 8px 16px;
    background-color: #F8F9FA;
    color: #1F2937;
    font-size: 11.5pt;
    line-height: 1.45;
    page-break-inside: avoid;
  }}

  hr.section-divider {{
    border: none;
    border-top: 1px solid #CBD5E0;
    margin: 22px 0;
  }}

  li.academic-li {{
    margin: 4px 0;
    line-height: 1.5;
  }}

  /* Figures */
  figure.report-figure {{
    margin: 16px 0 20px 0;
    text-align: center;
    page-break-inside: avoid;
  }}
  figure.report-figure img {{
    max-width: 95%;
    max-height: 280px;
    object-fit: contain;
    border: 1px solid #9CA3AF;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }}
  figure.report-figure figcaption {{
    font-size: 10.5pt;
    font-style: italic;
    color: #374151;
    margin-top: 6px;
    font-weight: bold;
  }}

  strong {{
    color: #002B49;
    font-weight: bold;
  }}
</style>
</head>
<body>

{title_page_html}

{toc_page_html}

<div class="report-content">
{main_body_html}
</div>

</body>
</html>"""

with open(TEMP_HTML, "w", encoding="utf-8") as f:
    f.write(full_html)

print(f"Generated HTML successfully ({len(full_html):,} bytes)")

from playwright.sync_api import sync_playwright
print("Rendering PDF via Playwright Chromium with Times New Roman & 1.5 line spacing...")
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"file:///{TEMP_HTML}".replace("\\", "/"))
    page.wait_for_load_state("networkidle")
    page.pdf(
        path=str(OUT_PDF),
        format="A4",
        margin={"top": "22mm", "right": "20mm", "bottom": "22mm", "left": "20mm"},
        print_background=True,
        display_header_footer=True,
        header_template='<div style="font-family: \'Times New Roman\', Times, serif; font-size: 8.5pt; color: #555555; width: 100%; text-align: center; padding-top: 4px;">FAST-NUCES Islamabad — SE3002 Software Quality Engineering | Section SE-C</div>',
        footer_template='<div style="font-family: \'Times New Roman\', Times, serif; font-size: 8.5pt; color: #555555; width: 100%; text-align: center; padding-bottom: 4px;">Final Quality Engineering Report | Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>',
    )
    browser.close()

TEMP_HTML.unlink()
size = OUT_PDF.stat().st_size
print(f"PDF successfully rendered: {OUT_PDF}")
print(f"Final PDF size: {size:,} bytes ({size/1024/1024:.2f} MB)")
