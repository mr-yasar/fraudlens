"""Render PDF using Playwright Chromium and inspect page count using PyMuPDF."""

from pathlib import Path
import pymupdf
from playwright.sync_api import sync_playwright

HTML_PATH = Path("FraudLens_AI_Research_Paper/FraudLens_AI_Research_Paper_Source/FraudLens_AI_IEEE_Research_Paper.html").resolve()
PDF_PATH = Path("FraudLens_AI_Research_Paper/FraudLens_AI_IEEE_Research_Paper.pdf").resolve()

print(f"Loading HTML from: {HTML_PATH}")
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"file:///{HTML_PATH.as_posix()}", wait_until="networkidle")
    
    # Generate PDF with A4 dimensions
    page.pdf(
        path=str(PDF_PATH),
        format="A4",
        print_background=True,
        prefer_css_page_size=True,
        margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"}
    )
    browser.close()

print(f"Generated PDF at: {PDF_PATH}")

# Inspect with PyMuPDF
doc = pymupdf.open(str(PDF_PATH))
page_count = len(doc)
print(f"Total Pages in PDF: {page_count}")
for i in range(page_count):
    page = doc[i]
    rect = page.rect
    print(f"Page {i+1}: Width={rect.width:.1f}pt, Height={rect.height:.1f}pt")
doc.close()
