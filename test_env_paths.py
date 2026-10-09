"""Comprehensive script to generate FraudLens AI IEEE Research Paper.
Produces:
1. HTML source formatted strictly according to IEEE A4 2-column style
2. PDF generated via Playwright Chromium
3. Programmatic calibration to achieve EXACTLY 9 PAGES
4. DOCX generated via python-docx
5. Verification suite (checks 0 occurrences of prohibited terms, verifies citations, verifies page count)
"""

import os
import re
import sys
from pathlib import Path
import pymupdf
from playwright.sync_api import sync_playwright
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

OUTPUT_DIR = Path("FraudLens_AI_Research_Paper")
SOURCE_DIR = OUTPUT_DIR / "FraudLens_AI_Research_Paper_Source"
FIGURES_DIR = SOURCE_DIR / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SOURCE_DIR.mkdir(parents=True, exist_ok=True)

# Verify Figures exist
fig1_path = FIGURES_DIR / "fig1_system_architecture.png"
fig2_path = FIGURES_DIR / "fig2_transaction_workflow.png"
fig3_path = FIGURES_DIR / "fig3_explainability_workflow.png"

print("Checking figures...")
for p in [fig1_path, fig2_path, fig3_path]:
    if not p.exists():
        print(f"Warning: {p} does not exist!")
    else:
        print(f"Found: {p}")
