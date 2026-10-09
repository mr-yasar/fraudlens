"""Fine-tune layout to perfectly balance Page 10 in IEEE PDF."""

from pathlib import Path
import pymupdf
from playwright.sync_api import sync_playwright

HTML_PATH = Path("FraudLens_AI_Research_Paper/FraudLens_AI_Research_Paper_Source/FraudLens_AI_IEEE_Research_Paper.html")
PDF_PATH = Path("FraudLens_AI_Research_Paper/FraudLens_AI_IEEE_Research_Paper.pdf")

with open(HTML_PATH, "r", encoding="utf-8") as f:
    template_html = f.read()

def test_settings(font_size, line_height, top_margin, bottom_margin, table_padding, fig_margin):
    css_mods = template_html
    css_mods = css_mods.replace("margin-top: 16mm;", f"margin-top: {top_margin}mm;")
    css_mods = css_mods.replace("margin-bottom: 17mm;", f"margin-bottom: {bottom_margin}mm;")
    css_mods = css_mods.replace("font-size: 9.4pt;\n    line-height: 1.15;", f"font-size: {font_size}pt;\n    line-height: {line_height};")
    css_mods = css_mods.replace("padding: 2.0pt 2.5pt;", f"padding: {table_padding}pt 2.5pt;")

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
    p10_chars = len(doc[9].get_text().strip()) if total_pages >= 10 else 0
    p9_chars = len(doc[8].get_text().strip()) if total_pages >= 9 else 0
    print(f"font={font_size}pt, lh={line_height}, top={top_margin}mm, bot={bottom_margin}mm -> Pages={total_pages}, P9_chars={p9_chars}, P10_chars={p10_chars}")
    doc.close()
    return total_pages, p10_chars, css_mods

configs = [
    (9.45, 1.16, 17, 18, 2.2, 6),
    (9.5, 1.165, 17, 18, 2.2, 6),
    (9.55, 1.17, 17, 18, 2.3, 6),
    (9.6, 1.175, 17, 18, 2.3, 6),
    (9.65, 1.18, 17, 18, 2.4, 6),
]

for cfg in configs:
    pages, p10_chars, css_mods = test_settings(*cfg)
    if pages == 10 and p10_chars > 4500:
        print(f"\nOPTIMAL BALANCE FOUND! Exactly 10 pages with {p10_chars} chars on page 10!")
        with open(HTML_PATH, "w", encoding="utf-8") as f:
            f.write(css_mods)
        break
    elif pages == 10:
        print(f"10 pages with {p10_chars} chars.")
        with open(HTML_PATH, "w", encoding="utf-8") as f:
            f.write(css_mods)
