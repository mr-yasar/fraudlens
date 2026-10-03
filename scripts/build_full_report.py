"""
FraudLens AI — Master Academic Project Report Builder.
Generates the complete 50-52 page report in HTML, DOCX, and PDF formats.
Strictly preserves institutional guidelines (Anna University / Sona College of Technology).
"""

import sys
import os
import json
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

project_root = Path("e:/fraudinvestigation")
report_dir = project_root / "project_report"
assets_dir = report_dir / "assets"
report_dir.mkdir(parents=True, exist_ok=True)

print("Starting FraudLens AI Master Project Report Generation...")
