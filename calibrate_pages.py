"""Fine-tune layout and font size/margins to achieve EXACTLY 9 PAGES in IEEE PDF."""

from pathlib import Path
import pymupdf
from playwright.sync_api import sync_playwright

HTML_PATH = Path("FraudLens_AI_Research_Paper/FraudLens_AI_Research_Paper_Source/FraudLens_AI_IEEE_Research_Paper.html")
PDF_PATH = Path("FraudLens_AI_Research_Paper/FraudLens_AI_IEEE_Research_Paper.pdf")

with open(HTML_PATH, "r", encoding="utf-8") as f:
    template_html = f.read()

def test_settings(font_size, line_height, top_margin, bottom_margin, table_padding, fig_margin):
    # Adjust CSS in template_html
    css_mods = template_html
    css_mods = css_mods.replace("margin-top: 18mm;", f"margin-top: {top_margin}mm;")
    css_mods = css_mods.replace("margin-bottom: 20mm;", f"margin-bottom: {bottom_margin}mm;")
    css_mods = css_mods.replace("font-size: 9.7pt;\n    line-height: 1.18;", f"font-size: {font_size}pt;\n    line-height: {line_height};")
    css_mods = css_mods.replace("padding: 2.2pt 3pt;", f"padding: {table_padding}pt 2.5pt;")
    css_mods = css_mods.replace("margin: 8pt 0 10pt 0;", f"margin: {fig_margin}pt 0;")

    temp_html = Path("FraudLens_AI_Research_Paper/FraudLens_AI_Research_Paper_Source/temp_test.html")
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(css_mods)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file:///{temp_html.resolve().as_posix()}", wait_until="networkidle")
        page.pdf(
            path=str(PDF_PATH),
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
            margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"}
        )
        browser.close()

    doc = pymupdf.open(str(PDF_PATH))
    total_pages = len(doc)
    p9_chars = len(doc[8].get_text().strip()) if total_pages >= 9 else 0
    p8_chars = len(doc[7].get_text().strip()) if total_pages >= 8 else 0
    print(f"font={font_size}pt, lh={line_height}, top={top_margin}mm, bot={bottom_margin}mm, tbl_pad={table_padding}pt -> Pages={total_pages}, P8_chars={p8_chars}, P9_chars={p9_chars}")
    doc.close()
    return total_pages, p9_chars, css_mods

# Test configurations
configs = [
    (9.4, 1.15, 16, 18, 1.8, 6),
    (9.3, 1.14, 16, 18, 1.8, 6),
    (9.2, 1.13, 16, 17, 1.6, 5),
    (9.1, 1.12, 15, 16, 1.5, 5),
    (9.25, 1.14, 16, 17, 1.7, 5),
]

for cfg in configs:
    pages, p9_chars, css_mods = test_settings(*cfg)
    if pages == 9:
        print(f"\nSUCCESS! Found configuration yielding exactly 9 pages with {p9_chars} chars on page 9!")
        with open(HTML_PATH, "w", encoding="utf-8") as f:
            f.write(css_mods)
        break
