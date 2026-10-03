"""
Full Report Generation Script for FraudLens AI.
Builds the comprehensive university project report (approx 50-52 pages)
in both DOCX and HTML formats, and converts to PDF.
"""

import sys
import os
from pathlib import Path

# Verify python-docx is available
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

print("python-docx successfully imported.")
