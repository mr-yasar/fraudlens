"""Calibrate layout to achieve EXACTLY 9.0 pages in IEEE PDF."""

from pathlib import Path
import pymupdf
from playwright.sync_api import sync_playwright

HTML_PATH = Path("FraudLens_AI_Research_Paper/FraudLens_AI_Research_Paper_Source/paper_9pages.html")
PDF_PATH = Path("FraudLens_AI_Research_Paper/FraudLens_AI_IEEE_Research_Paper.pdf")

with open(HTML_PATH, "r", encoding="utf-8") as f:
    template_html = f.read()

def test_config(font_size, line_height, top_margin, bottom_margin, table_padding, fig_size):
    html = template_html
    html = html.replace("margin-top: 15mm;", f"margin-top: {top_margin}mm;")
    html = html.replace("margin-bottom: 15mm;", f"margin-bottom: {bottom_margin}mm;")
    html = html.replace("font-size: 9.35pt;\n    line-height: 1.15;", f"font-size: {font_size}pt;\n    line-height: {line_height};")
    html = html.replace("max-width: 82% !important;", f"max-width: {fig_size}% !important;")

    temp_html = Path("FraudLens_AI_Research_Paper/FraudLens_AI_Research_Paper_Source/temp_9page.html")
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html)

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
    p10_chars = len(doc[9].get_text().strip()) if total_pages >= 10 else 0
    doc.close()
    print(f"font={font_size}pt, lh={line_height}, top={top_margin}mm, bot={bottom_margin}mm, fig1={fig_size}% -> Pages={total_pages}, P9_chars={p9_chars}, P10_chars={p10_chars}")
    return total_pages, p9_chars, html

configs = [
    # font_size, line_height, top_margin, bottom_margin, table_padding, fig_size
    (9.40, 1.155, 15, 15, 1.8, 80),
    (9.45, 1.160, 15, 15, 1.8, 80),
    (9.50, 1.165, 15, 15, 1.8, 80),
    (9.35, 1.150, 15, 15, 1.8, 80),
    (9.30, 1.145, 15, 15, 1.8, 80),
    (9.40, 1.155, 16, 16, 1.8, 82),
    (9.35, 1.150, 16, 16, 1.8, 82),
    (9.25, 1.140, 15, 15, 1.8, 82),
    (9.20, 1.135, 15, 15, 1.8, 80),
    (9.30, 1.140, 16, 16, 1.8, 80),
]

if __name__ == "__main__":
    best_html = None
    for cfg in configs:
        pages, p9_chars, html_mod = test_config(*cfg)
        if pages == 9 and p9_chars > 3500:
            print(f"\nSUCCESS! EXACTLY 9 PAGES with {p9_chars} chars on Page 9!")
            best_html = html_mod
            target_html = Path("FraudLens_AI_Research_Paper/FraudLens_AI_Research_Paper_Source/FraudLens_AI_IEEE_Research_Paper.html")
            with open(target_html, "w", encoding="utf-8") as f:
                f.write(best_html)
            break
        elif pages == 9:
            print(f"Found 9 pages with {p9_chars} chars.")
            best_html = html_mod
            target_html = Path("FraudLens_AI_Research_Paper/FraudLens_AI_Research_Paper_Source/FraudLens_AI_IEEE_Research_Paper.html")
            with open(target_html, "w", encoding="utf-8") as f:
                f.write(best_html)
