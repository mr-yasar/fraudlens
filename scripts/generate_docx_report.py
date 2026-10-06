"""
FraudLens AI Master Academic Project Report Generator (DOCX & PDF).
Strictly conforms to Anna University / Sona College of Technology academic standards.
Generates publication-grade DOCX and PDF with exact two-pass page number synchronization.
"""

import sys
import os
import re
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import win32com.client
import pythoncom

sys.path.insert(0, str(Path(__file__).parent))
import report_data as rd

project_root = Path("e:/fraudinvestigation")
report_dir = project_root / "project_report"
assets_dir = report_dir / "assets"
docx_output_path = report_dir / "FraudLens_AI_Project_Report.docx"
pdf_output_path = report_dir / "FraudLens_AI_Project_Report.pdf"

def clean_xml_string(s):
    """Sanitize string to ensure 100% XML compatibility."""
    if not s:
        return ""
    return "".join(c for c in str(s) if ord(c) in (0x9, 0xA, 0xD) or (0x20 <= ord(c) <= 0xD7FF) or (0xE000 <= ord(c) <= 0xFFFD) or (0x10000 <= ord(c) <= 0x10FFFF))

def set_cell_background(cell, fill_hex):
    """Set the background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=60, bottom=60, left=90, right=90):
    """Set cell margins in dxa."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_page_number_to_section(section, is_roman=False, start_at_1=False, start_num=1):
    """Add centered page number field to section footer with optional numbering format."""
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.text = ""
    run = p.add_run()
    run.font.name = "Times New Roman"
    run.font.size = Pt(11)
    
    fldSimple = OxmlElement('w:fldSimple')
    fldSimple.set(qn('w:instr'), 'PAGE')
    run._r.append(fldSimple)

    sectPr = section._sectPr
    pgNumType = OxmlElement('w:pgNumType')
    if is_roman:
        pgNumType.set(qn('w:fmt'), 'lowerRoman')
    else:
        pgNumType.set(qn('w:fmt'), 'decimal')
    if start_at_1:
        pgNumType.set(qn('w:start'), str(start_num))
    sectPr.append(pgNumType)

def add_header_to_section(section, header_text):
    """Add subtle running head to section header."""
    header = section.header
    p = header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run(clean_xml_string(header_text))
    run.font.name = "Times New Roman"
    run.font.size = Pt(8.5)
    run.font.italic = True
    run.font.color.rgb = RGBColor(100, 116, 139)

def style_paragraph(p, space_before=0, space_after=2.5, line_spacing=1.28, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing

def add_body_paragraph(doc, text, bold_prefix=""):
    p = doc.add_paragraph()
    style_paragraph(p)
    if bold_prefix:
        r_pre = p.add_run(clean_xml_string(bold_prefix))
        r_pre.font.name = "Times New Roman"
        r_pre.font.size = Pt(12)
        r_pre.font.bold = True
    
    r = p.add_run(clean_xml_string(text))
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    return p

def add_chapter_title(doc, chapter_num, title):
    p = doc.add_paragraph()
    style_paragraph(p, space_before=20, space_after=14, align=WD_ALIGN_PARAGRAPH.CENTER)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(clean_xml_string(f"CHAPTER {chapter_num}\n{title.upper()}"))
    r.font.name = "Times New Roman"
    r.font.size = Pt(16)
    r.font.bold = True

def add_section_title(doc, text):
    p = doc.add_paragraph()
    style_paragraph(p, space_before=14, space_after=5, align=WD_ALIGN_PARAGRAPH.LEFT)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(clean_xml_string(text))
    r.font.name = "Times New Roman"
    r.font.size = Pt(13.5)
    r.font.bold = True

def add_subsection_title(doc, text):
    p = doc.add_paragraph()
    style_paragraph(p, space_before=10, space_after=3, align=WD_ALIGN_PARAGRAPH.LEFT)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(clean_xml_string(text))
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r.font.bold = True

def add_academic_text(doc, raw_text):
    """Parses text blocks into properly styled section headings, subsections, and body text."""
    paragraphs = raw_text.strip().split("\n\n")
    for p in paragraphs:
        p_clean = clean_xml_string(p.strip())
        if not p_clean:
            continue
        lines = p_clean.split("\n")
        first_line = lines[0].strip()

        # Level 2 Heading: e.g. "1.1 OVERVIEW OF THE PROJECT", "6.2 MODULES OVERVIEW"
        if re.match(r"^(\d+\.\d+|[A-Z]\.\d+)\s+[A-Z]", first_line) and len(first_line) < 100:
            add_section_title(doc, first_line)
            rem = "\n".join(lines[1:]).strip()
            if rem:
                add_body_paragraph(doc, rem)
        # Level 3 Heading: e.g. "1.3.1 Statistical Profiling...", "6.1.4 Stratified..."
        elif re.match(r"^\d+\.\d+\.\d+\s+[A-Za-z]", first_line) and len(first_line) < 120:
            add_subsection_title(doc, first_line)
            rem = "\n".join(lines[1:]).strip()
            if rem:
                add_body_paragraph(doc, rem)
        else:
            add_body_paragraph(doc, p_clean)

def add_image_figure(doc, img_name, caption, width_in=4.7):
    img_path = assets_dir / img_name
    if not img_path.exists():
        print(f"Warning: Image {img_path} not found!")
        return

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run()
    run.add_picture(str(img_path), width=Inches(width_in))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(10)
    p_cap.paragraph_format.keep_with_next = True
    r_cap = p_cap.add_run(clean_xml_string(caption))
    r_cap.font.name = "Times New Roman"
    r_cap.font.size = Pt(10)
    r_cap.font.bold = True

def create_styled_table(doc, caption, headers, rows, col_widths=None):
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_cap.paragraph_format.space_before = Pt(10)
    p_cap.paragraph_format.space_after = Pt(3)
    p_cap.paragraph_format.keep_with_next = True
    r_cap = p_cap.add_run(clean_xml_string(caption))
    r_cap.font.name = "Times New Roman"
    r_cap.font.size = Pt(10.5)
    r_cap.font.bold = True

    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Format Header Row
    hdr_cells = table.rows[0].cells
    for i, header_text in enumerate(headers):
        hdr_cells[i].text = clean_xml_string(header_text)
        set_cell_background(hdr_cells[i], "F1F5F9")
        set_cell_margins(hdr_cells[i], top=70, bottom=70, left=90, right=90)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        for run in p.runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(9.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(15, 23, 42)

    # Repeat header row on subsequent pages
    trPr = table.rows[0]._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))

    # Format Data Rows
    for r_idx, row_data in enumerate(rows):
        row_cells = table.rows[r_idx + 1].cells
        r_trPr = table.rows[r_idx + 1]._tr.get_or_add_trPr()
        r_trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

        for c_idx, cell_value in enumerate(row_data):
            row_cells[c_idx].text = clean_xml_string(str(cell_value))
            set_cell_margins(row_cells[c_idx], top=35, bottom=35, left=65, right=65)
            p = row_cells[c_idx].paragraphs[0]
            p.paragraph_format.space_before = Pt(0.5)
            p.paragraph_format.space_after = Pt(0.5)
            p.paragraph_format.line_spacing = 1.0
            for run in p.runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(9)
                if c_idx == 0:
                    run.font.bold = True

    # Apply Column Widths if provided
    if col_widths and len(col_widths) == len(headers):
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = width

    # Set table borders
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="333333"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="333333"/>'
        f'<w:left w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        f'<w:right w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
        f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def build_docx_tree(page_map=None):
    """
    Builds the complete DOCX document.
    page_map: optional dictionary mapping heading/table/figure keys to measured page numbers.
    """
    doc = Document()

    # SECTION 1: FRONT MATTER (Cover, Bonafide Cert, Abstract, Ack, TOC, LOT, LOF)
    section1 = doc.sections[0]
    section1.top_margin = Inches(1.0)
    section1.bottom_margin = Inches(1.0)
    section1.left_margin = Inches(1.0)
    section1.right_margin = Inches(1.0)
    section1.page_width = Inches(8.27)
    section1.page_height = Inches(11.69)
    add_page_number_to_section(section1, is_roman=True, start_at_1=True, start_num=1)

    # 1. COVER PAGE (Page i)
    p_title = doc.add_paragraph()
    style_paragraph(p_title, space_before=40, space_after=18, align=WD_ALIGN_PARAGRAPH.CENTER)
    r = p_title.add_run(rd.FRONT_MATTER["project_title"])
    r.font.name = "Times New Roman"
    r.font.size = Pt(18)
    r.font.bold = True

    p_rep = doc.add_paragraph()
    style_paragraph(p_rep, space_before=14, space_after=14, align=WD_ALIGN_PARAGRAPH.CENTER)
    r = p_rep.add_run("A PROJECT REPORT")
    r.font.name = "Times New Roman"
    r.font.size = Pt(14)
    r.font.bold = True

    p_sub = doc.add_paragraph()
    style_paragraph(p_sub, space_before=10, space_after=12, align=WD_ALIGN_PARAGRAPH.CENTER)
    r = p_sub.add_run("Submitted by")
    r.font.name = "Times New Roman"
    r.font.size = Pt(14)
    r.font.italic = True

    # Candidate 1 & Candidate 2
    p_cand = doc.add_paragraph()
    style_paragraph(p_cand, space_before=10, space_after=16, align=WD_ALIGN_PARAGRAPH.CENTER)
    cands = rd.FRONT_MATTER.get("candidates", [])
    for idx, c in enumerate(cands):
        r_name = p_cand.add_run(f"{c['name']}\n")
        r_name.font.name = "Times New Roman"
        r_name.font.size = Pt(15)
        r_name.font.bold = True
        sep = "\n\n" if idx < len(cands) - 1 else ""
        r_reg = p_cand.add_run(f"Reg.No.: {c['reg_no']}{sep}")
        r_reg.font.name = "Times New Roman"
        r_reg.font.size = Pt(13)

    p_part = doc.add_paragraph()
    style_paragraph(p_part, space_before=12, space_after=14, align=WD_ALIGN_PARAGRAPH.CENTER)
    r = p_part.add_run("in partial fulfillment for the award of the degree of")
    r.font.name = "Times New Roman"
    r.font.size = Pt(14)
    r.font.italic = True

    p_deg = doc.add_paragraph()
    style_paragraph(p_deg, space_before=10, space_after=20, align=WD_ALIGN_PARAGRAPH.CENTER)
    r = p_deg.add_run(f"{rd.FRONT_MATTER['degree']}\nIN\n{rd.FRONT_MATTER['branch']}")
    r.font.name = "Times New Roman"
    r.font.size = Pt(16)
    r.font.bold = True

    p_col = doc.add_paragraph()
    style_paragraph(p_col, space_before=24, space_after=4, align=WD_ALIGN_PARAGRAPH.CENTER)
    r = p_col.add_run(rd.FRONT_MATTER["college_autonomous"])
    r.font.name = "Times New Roman"
    r.font.size = Pt(16)
    r.font.bold = True

    p_uni = doc.add_paragraph()
    style_paragraph(p_uni, space_before=4, space_after=16, align=WD_ALIGN_PARAGRAPH.CENTER)
    r = p_uni.add_run(f"{rd.FRONT_MATTER['university']}\n{rd.FRONT_MATTER['month_year']}")
    r.font.name = "Times New Roman"
    r.font.size = Pt(14)
    r.font.bold = True

    # 2. BONAFIDE CERTIFICATE (Page ii)
    doc.add_page_break()
    p_bcol = doc.add_paragraph()
    style_paragraph(p_bcol, space_before=30, space_after=4, align=WD_ALIGN_PARAGRAPH.CENTER)
    r = p_bcol.add_run(rd.FRONT_MATTER["college_autonomous"])
    r.font.name = "Times New Roman"
    r.font.size = Pt(16)
    r.font.bold = True

    p_buni = doc.add_paragraph()
    style_paragraph(p_buni, space_before=4, space_after=30, align=WD_ALIGN_PARAGRAPH.CENTER)
    r = p_buni.add_run(f"AFFILIATED TO {rd.FRONT_MATTER['university']}")
    r.font.name = "Times New Roman"
    r.font.size = Pt(13)
    r.font.bold = True

    p_bcert = doc.add_paragraph()
    style_paragraph(p_bcert, space_before=20, space_after=60, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    r1 = p_bcert.add_run('Certified that this project report "')
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(12)
    r2 = p_bcert.add_run(rd.FRONT_MATTER["project_title"])
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(12)
    r2.font.bold = True
    cands_str = f"{cands[0]['name']} , {cands[1]['name']} (Reg. No. {cands[0]['reg_no']},{cands[1]['reg_no']})"
    r3 = p_bcert.add_run(f'" is the bonafide work of "{cands_str}" who carried out the project work under my supervision.')
    r3.font.name = "Times New Roman"
    r3.font.size = Pt(12)

    table_bsig = doc.add_table(rows=1, cols=2)
    table_bsig.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_hod = table_bsig.rows[0].cells[0]
    c_sup = table_bsig.rows[0].cells[1]
    c_hod.width = Inches(3.2)
    c_sup.width = Inches(3.2)

    p_h = c_hod.paragraphs[0]
    style_paragraph(p_h, align=WD_ALIGN_PARAGRAPH.LEFT)
    r = p_h.add_run(f"SIGNATURE\n\n\n{rd.FRONT_MATTER['hod_name']}\nHEAD OF THE DEPARTMENT\n{rd.FRONT_MATTER['hod_designation']}\n{rd.FRONT_MATTER['full_address']}")
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)

    p_s = c_sup.paragraphs[0]
    style_paragraph(p_s, align=WD_ALIGN_PARAGRAPH.RIGHT)
    r = p_s.add_run(f"SIGNATURE\n\n\n{rd.FRONT_MATTER['supervisor_name']}\nSUPERVISOR\n{rd.FRONT_MATTER['supervisor_designation']}\n{rd.FRONT_MATTER['full_address']}")
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)

    # 3. ABSTRACT (Page iii & iv)
    doc.add_page_break()
    p_abs_title = doc.add_paragraph()
    style_paragraph(p_abs_title, space_before=16, space_after=14, align=WD_ALIGN_PARAGRAPH.CENTER)
    r = p_abs_title.add_run("ABSTRACT")
    r.font.name = "Times New Roman"
    r.font.size = Pt(16)
    r.font.bold = True

    for para in rd.ABSTRACT_TEXT.strip().split("\n\n"):
        p = doc.add_paragraph()
        style_paragraph(p, space_before=0, space_after=3.5, line_spacing=1.25)
        r = p.add_run(clean_xml_string(para.strip()))
        r.font.name = "Times New Roman"
        r.font.size = Pt(11.5)

    # 4. ACKNOWLEDGEMENT (Page v)
    doc.add_page_break()
    p_ack_title = doc.add_paragraph()
    style_paragraph(p_ack_title, space_before=16, space_after=14, align=WD_ALIGN_PARAGRAPH.CENTER)
    r = p_ack_title.add_run("ACKNOWLEDGEMENT")
    r.font.name = "Times New Roman"
    r.font.size = Pt(16)
    r.font.bold = True

    for para in rd.ACKNOWLEDGEMENT_TEXT.strip().split("\n\n"):
        p = doc.add_paragraph()
        style_paragraph(p, space_before=0, space_after=2.5, line_spacing=1.28)
        r = p.add_run(clean_xml_string(para.strip()))
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)

    # 5. TABLE OF CONTENTS (Page vi & vii)
    doc.add_page_break()
    p_toc_title = doc.add_paragraph()
    style_paragraph(p_toc_title, space_before=16, space_after=14, align=WD_ALIGN_PARAGRAPH.CENTER)
    r = p_toc_title.add_run("TABLE OF CONTENTS")
    r.font.name = "Times New Roman"
    r.font.size = Pt(16)
    r.font.bold = True

    # Complete TOC schema with 6.1.4 and 6.1.6 included
    toc_schema = [
        ("CHAPTER", "TITLE", "PAGE NO"),
        ("", "ABSTRACT", "abstract"),
        ("", "ACKNOWLEDGEMENT", "ack"),
        ("", "LIST OF TABLES", "lot"),
        ("", "LIST OF FIGURES", "lof"),
        ("1", "INTRODUCTION", "ch1"),
        ("", "  1.1 Overview of the Project", "ch1_1"),
        ("", "  1.2 Objective of the Project", "ch1_2"),
        ("", "  1.3 Literature Review", "ch1_3"),
        ("2", "SYSTEM ANALYSIS", "ch2"),
        ("", "  2.1 Problem Definition", "ch2_1"),
        ("", "  2.2 Existing System", "ch2_2"),
        ("", "  2.3 Proposed System", "ch2_3"),
        ("3", "SYSTEM STUDY", "ch3"),
        ("", "  3.1 Feasibility Study", "ch3_1"),
        ("", "    3.1.1 Economic Feasibility", "ch3_1_1"),
        ("", "    3.1.2 Technical Feasibility", "ch3_1_2"),
        ("", "    3.1.3 Performance Feasibility", "ch3_1_3"),
        ("4", "SYSTEM REQUIREMENTS", "ch4"),
        ("", "  4.1 Hardware Requirements", "ch4_1"),
        ("", "  4.2 Software Requirements", "ch4_2"),
        ("5", "SYSTEM DESIGN", "ch5"),
        ("", "  5.1 System Architecture", "ch5_1"),
        ("", "  5.2 Class Diagram", "ch5_2"),
        ("", "  5.3 Use Case Diagram", "ch5_3"),
        ("", "  5.4 Flow Diagram", "ch5_4"),
        ("", "  5.5 Sequence Diagram", "ch5_5"),
        ("", "  5.6 Database Design", "ch5_6"),
        ("", "    5.6.1 Table Design", "ch5_6_1"),
        ("", "    5.6.2 ER Diagrams", "ch5_6_2"),
        ("", "    5.6.3 Data Flow Diagrams", "ch5_6_3"),
        ("6", "PROPOSED ALGORITHM IMPLEMENTATION", "ch6"),
        ("", "  6.1 Project Description", "ch6_1"),
        ("", "    6.1.1 Dataset Specification & Integrity Audit", "ch6_1_1"),
        ("", "    6.1.2 Preprocessing, Imputation & Scaling", "ch6_1_2"),
        ("", "    6.1.3 Behavioral Feature Engineering", "ch6_1_3"),
        ("", "    6.1.4 Stratified Data Splitting & Leakage Auditing", "ch6_1_4"),
        ("", "    6.1.5 Class Imbalance Mitigation Strategy", "ch6_1_5"),
        ("", "    6.1.6 Supervised Machine Learning Architectures", "ch6_1_6"),
        ("", "    6.1.7 Decoupled Multi-Factor Risk Scoring", "ch6_1_7"),
        ("", "    6.1.8 Explainable AI via TreeSHAP", "ch6_1_8"),
        ("", "  6.2 Modules Overview", "ch6_2"),
        ("", "  6.3 Module Description (6.3.1 - 6.3.10)", "ch6_3"),
        ("7", "RESULTS AND DISCUSSION", "ch7"),
        ("", "  7.1 Results and Discussion", "ch7_1"),
        ("", "    7.1.1 ML Model Performance Comparison", "ch7_1_1"),
        ("", "    7.1.2 Confusion Matrix Analysis", "ch7_1_2"),
        ("", "    7.1.3 Global & Local TreeSHAP Attributions", "ch7_1_3"),
        ("", "    7.1.4 Pre-Authorization Latency Profile", "ch7_1_4"),
        ("8", "SYSTEM TESTING", "ch8"),
        ("", "  8.1 Testing Methodology", "ch8_1"),
        ("", "  8.2 Unit Testing", "ch8_2"),
        ("", "  8.3 Integration Testing", "ch8_3"),
        ("", "  8.4 Validation Testing", "ch8_4"),
        ("", "  8.5 Testing Report", "ch8_5"),
        ("9", "CONCLUSION AND FUTURE ENHANCEMENT", "ch9"),
        ("", "  9.1 Conclusion", "ch9_1"),
        ("", "  9.2 Future Enhancement", "ch9_2"),
        ("", "APPENDIX", "appendix"),
        ("", "  A.1 Core Source Code Excerpts", "app_a1"),
        ("", "  A.2 Application Screenshots Ecosystem", "app_a2"),
        ("", "REFERENCES", "references"),
    ]

    t_toc = doc.add_table(rows=len(toc_schema), cols=3)
    t_toc.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_toc.rows[0].cells[0].text = "CHAPTER"
    t_toc.rows[0].cells[1].text = "TITLE"
    t_toc.rows[0].cells[2].text = "PAGE NO"
    t_toc.rows[0].cells[0].width = Inches(1.1)
    t_toc.rows[0].cells[1].width = Inches(4.5)
    t_toc.rows[0].cells[2].width = Inches(0.8)

    for i in range(3):
        r = t_toc.rows[0].cells[i].paragraphs[0].runs[0]
        r.font.name = "Times New Roman"
        r.font.size = Pt(10.5)
        r.font.bold = True

    for idx, (ch, tit, key) in enumerate(toc_schema[1:], 1):
        row = t_toc.rows[idx]
        row.cells[0].text = ch
        row.cells[1].text = tit
        pg_val = str(page_map.get(key, "1")) if page_map else "1"
        row.cells[2].text = pg_val
        row.cells[0].width = Inches(1.1)
        row.cells[1].width = Inches(4.5)
        row.cells[2].width = Inches(0.8)
        row.cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

        for c_idx in range(3):
            p = row.cells[c_idx].paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(9.5)
                if ch or tit in ["ABSTRACT", "ACKNOWLEDGEMENT", "LIST OF TABLES", "LIST OF FIGURES", "APPENDIX", "REFERENCES"]:
                    r.font.bold = True

    # 6. LIST OF TABLES (Page viii)
    doc.add_page_break()
    p_lot_title = doc.add_paragraph()
    style_paragraph(p_lot_title, space_before=16, space_after=14, align=WD_ALIGN_PARAGRAPH.CENTER)
    r = p_lot_title.add_run("LIST OF TABLES")
    r.font.name = "Times New Roman"
    r.font.size = Pt(16)
    r.font.bold = True

    lot_schema = [
        ("Table 1.1", "Comparative Literature Survey of Fraud Detection Methodologies", "table_1_1"),
        ("Table 3.1", "Economic Feasibility Cost-Benefit and ROI Analysis", "table_3_1"),
        ("Table 4.1", "Hardware Infrastructure Specifications", "table_4_1"),
        ("Table 4.2", "Software Environment & Runtime Dependencies", "table_4_2"),
        ("Table 5.1", "Relational Database Schema Specifications (20 Entities)", "table_5_1"),
        ("Table 6.1", "Master Dataset Attribute & Domain Specifications (57 Features)", "table_6_1"),
        ("Table 6.2", "Preprocessing Transformation & Imputation Strategy", "table_6_2"),
        ("Table 6.3", "Machine Learning Model Hyperparameters & Architecture", "table_6_3"),
        ("Table 6.4", "Multi-Factor Risk Scoring Point Allocation Matrix", "table_6_4"),
        ("Table 6.5", "Global Top-15 Feature Importance Attributions via TreeSHAP", "table_6_5"),
        ("Table 6.6", "Pre-Authorization Three-Tier Decision Matrix & Actions", "table_6_6"),
        ("Table 7.1", "Comprehensive ML Model Performance Comparison", "table_7_1"),
        ("Table 7.2", "Confusion Matrix Metrics across Test & Deployment Splits", "table_7_2"),
        ("Table 7.3", "Sub-5 Millisecond Pre-Authorization Latency Breakdown", "table_7_3"),
        ("Table 8.1", "Formal Software Verification & Validation Test Report (30 Cases)", "table_8_1"),
    ]

    t_lot = doc.add_table(rows=len(lot_schema) + 1, cols=3)
    t_lot.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_lot.rows[0].cells[0].text = "TABLE NO."
    t_lot.rows[0].cells[1].text = "TITLE"
    t_lot.rows[0].cells[2].text = "PAGE NO"
    t_lot.rows[0].cells[0].width = Inches(1.3)
    t_lot.rows[0].cells[1].width = Inches(4.3)
    t_lot.rows[0].cells[2].width = Inches(0.8)

    for i in range(3):
        r = t_lot.rows[0].cells[i].paragraphs[0].runs[0]
        r.font.name = "Times New Roman"
        r.font.size = Pt(10.5)
        r.font.bold = True

    for idx, (tno, tit, key) in enumerate(lot_schema, 1):
        row = t_lot.rows[idx]
        row.cells[0].text = tno
        row.cells[1].text = tit
        pg_val = str(page_map.get(key, "1")) if page_map else "1"
        row.cells[2].text = pg_val
        row.cells[0].width = Inches(1.3)
        row.cells[1].width = Inches(4.3)
        row.cells[2].width = Inches(0.8)
        row.cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

        for c_idx in range(3):
            p = row.cells[c_idx].paragraphs[0]
            p.paragraph_format.space_before = Pt(1.5)
            p.paragraph_format.space_after = Pt(1.5)
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(9.5)

    # 7. LIST OF FIGURES (Page ix)
    doc.add_page_break()
    p_lof_title = doc.add_paragraph()
    style_paragraph(p_lof_title, space_before=16, space_after=14, align=WD_ALIGN_PARAGRAPH.CENTER)
    r = p_lof_title.add_run("LIST OF FIGURES")
    r.font.name = "Times New Roman"
    r.font.size = Pt(16)
    r.font.bold = True

    lof_schema = [
        ("Figure 5.1", "FraudLens AI Multi-Tier System Architecture", "fig_5_1"),
        ("Figure 5.2", "Core Domain UML Class Diagram", "fig_5_2"),
        ("Figure 5.3", "UML Use Case Diagram for User Roles", "fig_5_3"),
        ("Figure 5.4", "Pre-Authorization & Autonomous Decision System Flow", "fig_5_4"),
        ("Figure 5.5", "Pre-Authorization Step-Up Verification Sequence Diagram", "fig_5_5"),
        ("Figure 5.6", "FraudLens AI Relational Entity-Relationship (ER) Diagram", "fig_5_6"),
        ("Figure 5.7", "Data Flow Diagram (DFD) Level 0 — Context Diagram", "fig_5_7"),
        ("Figure 5.8", "Data Flow Diagram (DFD) Level 1 — Process Decomposition", "fig_5_8"),
        ("Figure 6.1", "End-to-End Machine Learning & Feature Pipeline Workflow", "fig_6_1"),
        ("Figure 6.2", "Multi-Factor Additive Risk Scoring Architecture & Tiers", "fig_6_2"),
        ("Figure 6.3", "Local TreeSHAP Feature Attribution Waterfall for Flagged Transaction", "fig_6_3"),
        ("Figure 6.4", "Pre-Authorization Mobile SMS OTP Verification Lifecycle", "fig_6_4"),
        ("Figure 7.1", "ROC and Precision-Recall Curves on Test Split", "fig_7_1"),
        ("Figure 7.2", "Confusion Matrix Heatmaps across Test & Active Validation Splits", "fig_7_2"),
        ("Figure 7.3", "Global Top-15 Feature Importance Ranking via TreeSHAP", "fig_7_3"),
        ("Figure 7.4", "Sub-5 Millisecond Pre-Authorization Latency Breakdown Profile", "fig_7_4"),
        ("Figure A.1", "FraudLens AI Application Interface Ecosystem (4 Panels)", "fig_a1"),
    ]

    t_lof = doc.add_table(rows=len(lof_schema) + 1, cols=3)
    t_lof.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_lof.rows[0].cells[0].text = "FIGURE NO."
    t_lof.rows[0].cells[1].text = "TITLE"
    t_lof.rows[0].cells[2].text = "PAGE NO"
    t_lof.rows[0].cells[0].width = Inches(1.3)
    t_lof.rows[0].cells[1].width = Inches(4.3)
    t_lof.rows[0].cells[2].width = Inches(0.8)

    for i in range(3):
        r = t_lof.rows[0].cells[i].paragraphs[0].runs[0]
        r.font.name = "Times New Roman"
        r.font.size = Pt(10.5)
        r.font.bold = True

    for idx, (fno, tit, key) in enumerate(lof_schema, 1):
        row = t_lof.rows[idx]
        row.cells[0].text = fno
        row.cells[1].text = tit
        pg_val = str(page_map.get(key, "1")) if page_map else "1"
        row.cells[2].text = pg_val
        row.cells[0].width = Inches(1.3)
        row.cells[1].width = Inches(4.3)
        row.cells[2].width = Inches(0.8)
        row.cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

        for c_idx in range(3):
            p = row.cells[c_idx].paragraphs[0]
            p.paragraph_format.space_before = Pt(1.5)
            p.paragraph_format.space_after = Pt(1.5)
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(9.5)

    # --------------------------------------------------------------------------
    # SECTION 2: REPORT BODY (CHAPTER 1 TO REFERENCES)
    # Starts at Arabic Page 1 with Running Header
    # --------------------------------------------------------------------------
    body_section = doc.add_section(docx.enum.section.WD_SECTION.NEW_PAGE)
    body_section.top_margin = Inches(1.0)
    body_section.bottom_margin = Inches(1.0)
    body_section.left_margin = Inches(1.0)
    body_section.right_margin = Inches(1.0)
    body_section.page_width = Inches(8.27)
    body_section.page_height = Inches(11.69)
    body_section.header.is_linked_to_previous = False
    body_section.footer.is_linked_to_previous = False
    add_header_to_section(body_section, "FraudLens AI: Explainable AI-Based Financial Fraud & Risk Detection System")
    add_page_number_to_section(body_section, is_roman=False, start_at_1=True, start_num=1)

    # CHAPTER 1: INTRODUCTION
    add_chapter_title(doc, "1", "INTRODUCTION")
    add_academic_text(doc, rd.CH1_OVERVIEW)
    add_academic_text(doc, rd.CH1_OBJECTIVES)
    add_academic_text(doc, rd.CH1_LITERATURE)

    # Table 1.1
    t1_1_rows = [
        (r["author"], r["method"], r["context"], r["finding"], r["limitation"], r["relevance"])
        for r in rd.TABLE_1_1_DATA
    ]
    create_styled_table(
        doc,
        "Table 1.1: Comparative Literature Survey of Prominent Financial Fraud Detection Methodologies",
        ["Author / Year", "Methodology", "Context / Domain", "Key Finding", "Major Limitation", "Relevance to FraudLens AI"],
        t1_1_rows,
        [Inches(1.0), Inches(1.1), Inches(1.0), Inches(1.3), Inches(1.1), Inches(1.0)]
    )

    add_academic_text(doc, rd.RESEARCH_GAP_TEXT)

    # CHAPTER 2: SYSTEM ANALYSIS
    doc.add_page_break()
    add_chapter_title(doc, "2", "SYSTEM ANALYSIS")
    add_academic_text(doc, rd.CH2_TEXT)

    # CHAPTER 3: SYSTEM STUDY
    doc.add_page_break()
    add_chapter_title(doc, "3", "SYSTEM STUDY")
    add_academic_text(doc, rd.CH3_TEXT)

    # Table 3.1
    create_styled_table(
        doc,
        "Table 3.1: Economic Feasibility Cost-Benefit and ROI Analysis",
        ["Operational Cost / Benefit Dimension", "Description & Implementation Baseline", "Estimated Value", "Horizon"],
        rd.TABLE_3_1_DATA,
        [Inches(2.0), Inches(2.6), Inches(1.0), Inches(0.9)]
    )

    # CHAPTER 4: SYSTEM REQUIREMENTS
    doc.add_page_break()
    add_chapter_title(doc, "4", "SYSTEM REQUIREMENTS")
    add_academic_text(doc, rd.CH4_TEXT)

    # Table 4.1
    create_styled_table(
        doc,
        "Table 4.1: Minimum & Recommended Hardware Infrastructure Specifications",
        ["Hardware Component", "Minimum Specification", "Recommended Development", "Production Deployment"],
        rd.TABLE_4_1_DATA,
        [Inches(1.5), Inches(1.6), Inches(1.6), Inches(1.8)]
    )

    # Table 4.2
    create_styled_table(
        doc,
        "Table 4.2: Production Software Environment & Library Dependencies",
        ["Software Component", "Version / Specification", "Operational Role"],
        rd.TABLE_4_2_DATA,
        [Inches(1.8), Inches(2.7), Inches(2.0)]
    )

    # CHAPTER 5: SYSTEM DESIGN
    doc.add_page_break()
    add_chapter_title(doc, "5", "SYSTEM DESIGN")
    add_academic_text(doc, rd.CH5_TEXT)

    add_image_figure(doc, "fig_5_1_system_architecture.png", "Figure 5.1: FraudLens AI Multi-Tier System Architecture")
    add_image_figure(doc, "fig_5_2_class_diagram.png", "Figure 5.2: Core Domain UML Class Diagram")
    add_image_figure(doc, "fig_5_3_use_case_diagram.png", "Figure 5.3: UML Use Case Diagram for User Roles")
    add_image_figure(doc, "fig_5_4_flow_diagram.png", "Figure 5.4: Pre-Authorization & Autonomous Decision System Flow")
    add_image_figure(doc, "fig_5_5_sequence_diagram.png", "Figure 5.5: Pre-Authorization Step-Up Verification Sequence Diagram")

    # Table 5.1
    create_styled_table(
        doc,
        "Table 5.1: Relational Database Schema Specifications (20 Relational Entities)",
        ["Table Name", "Columns, Keys & Constraints", "Row Count", "Operational Description"],
        rd.TABLE_5_1_DATA,
        [Inches(1.3), Inches(3.0), Inches(0.7), Inches(1.5)]
    )

    add_image_figure(doc, "fig_5_6_er_diagram.png", "Figure 5.6: FraudLens AI Relational Entity-Relationship (ER) Diagram")
    add_image_figure(doc, "fig_5_7_dfd_level_0.png", "Figure 5.7: Data Flow Diagram (DFD) Level 0 — Context Diagram")
    add_image_figure(doc, "fig_5_8_dfd_level_1.png", "Figure 5.8: Data Flow Diagram (DFD) Level 1 — Process Decomposition")

    # CHAPTER 6: PROPOSED ALGORITHM IMPLEMENTATION
    doc.add_page_break()
    add_chapter_title(doc, "6", "PROPOSED ALGORITHM IMPLEMENTATION")
    add_academic_text(doc, rd.CH6_TEXT)

    # Table 6.1
    create_styled_table(
        doc,
        "Table 6.1: Master Dataset Attribute & Domain Specifications (Sample of 41 of 57 Attributes)",
        ["Attribute Name", "Data Type & Constraint", "Sample Value", "Domain Definition & Operational Usage"],
        rd.TABLE_6_1_DATA,
        [Inches(1.8), Inches(1.6), Inches(1.1), Inches(2.0)]
    )

    add_image_figure(doc, "fig_6_1_ml_pipeline_workflow.png", "Figure 6.1: End-to-End Machine Learning & Feature Pipeline Workflow")

    # Table 6.2
    create_styled_table(
        doc,
        "Table 6.2: Preprocessing Transformation & Imputation Strategy",
        ["Pipeline Stage", "Target Features", "Transformation Method", "Mathematical & Architectural Rationale"],
        rd.TABLE_6_2_DATA,
        [Inches(1.5), Inches(1.6), Inches(1.7), Inches(1.7)]
    )

    # Table 6.3
    create_styled_table(
        doc,
        "Table 6.3: Machine Learning Model Hyperparameters & Architecture",
        ["Model Architecture", "Model Family", "Tuned Hyperparameters", "Architectural Rationale"],
        rd.TABLE_6_3_DATA,
        [Inches(1.4), Inches(1.6), Inches(2.1), Inches(1.4)]
    )

    add_image_figure(doc, "fig_6_2_risk_scoring_matrix.png", "Figure 6.2: Multi-Factor Additive Risk Scoring Architecture & Tiers")

    # Table 6.4
    create_styled_table(
        doc,
        "Table 6.4: Multi-Factor Risk Scoring Point Allocation Matrix",
        ["Risk Scoring Dimension", "Point Allocation Range", "Deterministic Mathematical Formulation & Triggers"],
        rd.TABLE_6_4_DATA,
        [Inches(2.0), Inches(1.4), Inches(3.1)]
    )

    add_image_figure(doc, "fig_6_3_shap_waterfall.png", "Figure 6.3: Local TreeSHAP Feature Attribution Waterfall for Flagged Transaction")

    # Table 6.5
    create_styled_table(
        doc,
        "Table 6.5: Global Top-15 Feature Importance Attributions via TreeSHAP",
        ["Rank", "Engineered Feature Name", "Mean |SHAP|", "Mean SHAP", "Operational Interpretation"],
        rd.TABLE_6_5_DATA,
        [Inches(0.6), Inches(2.2), Inches(1.0), Inches(1.0), Inches(1.7)]
    )

    add_image_figure(doc, "fig_6_4_mobile_otp_lifecycle.png", "Figure 6.4: Pre-Authorization Mobile SMS OTP Verification Lifecycle")

    # Table 6.6
    create_styled_table(
        doc,
        "Table 6.6: Pre-Authorization Three-Tier Decision Matrix & Operational Directives",
        ["Decision Tier", "Score Boundary", "Trigger Conditions", "Operational Directive"],
        rd.TABLE_6_6_DATA,
        [Inches(1.3), Inches(1.3), Inches(2.0), Inches(1.9)]
    )

    # CHAPTER 7: RESULTS AND DISCUSSION
    doc.add_page_break()
    add_chapter_title(doc, "7", "RESULTS AND DISCUSSION")
    add_academic_text(doc, rd.CH7_TEXT)

    # Table 7.1
    create_styled_table(
        doc,
        "Table 7.1: Comprehensive Machine Learning Model Performance Comparison (Test Split)",
        ["Model Architecture", "Accuracy", "Precision", "Recall", "F1-Score", "F2-Score", "ROC-AUC", "PR-AUC", "FPR", "FNR", "Status"],
        rd.TABLE_7_1_DATA,
        [Inches(1.3), Inches(0.5), Inches(0.5), Inches(0.5), Inches(0.5), Inches(0.5), Inches(0.6), Inches(0.6), Inches(0.4), Inches(0.4), Inches(1.1)]
    )

    add_image_figure(doc, "fig_7_1_roc_pr_curves.png", "Figure 7.1: ROC and Precision-Recall Curves on Test Split")

    # Table 7.2
    create_styled_table(
        doc,
        "Table 7.2: Confusion Matrix Metrics across Master Test & Active Validation Splits",
        ["Evaluation Corpus Partition", "True Neg (TN)", "False Pos (FP)", "False Neg (FN)", "True Pos (TP)", "Precision", "Recall", "F1-Score", "Accuracy"],
        rd.TABLE_7_2_DATA,
        [Inches(2.0), Inches(0.6), Inches(0.6), Inches(0.6), Inches(0.6), Inches(0.7), Inches(0.7), Inches(0.6), Inches(0.6)]
    )

    add_image_figure(doc, "fig_7_2_confusion_matrices.png", "Figure 7.2: Confusion Matrix Heatmaps across Test & Active Validation Splits")
    add_image_figure(doc, "fig_7_3_feature_importance.png", "Figure 7.3: Global Top-15 Feature Importance Ranking via TreeSHAP")

    # Table 7.3
    create_styled_table(
        doc,
        "Table 7.3: Sub-5 Millisecond Pre-Authorization Latency Breakdown Profile",
        ["Pre-Authorization Architectural Phase", "Execution Latency", "Implementation Details"],
        rd.TABLE_7_3_DATA,
        [Inches(2.3), Inches(1.1), Inches(3.2)]
    )

    add_image_figure(doc, "fig_7_4_latency_profile.png", "Figure 7.4: Sub-5 Millisecond Pre-Authorization Latency Breakdown Profile")

    # CHAPTER 8: SYSTEM TESTING
    doc.add_page_break()
    add_chapter_title(doc, "8", "SYSTEM TESTING")
    add_academic_text(doc, rd.CH8_TEXT)

    # Table 8.1
    create_styled_table(
        doc,
        "Table 8.1: Formal Software Verification & Validation Test Report (30 Representative Cases)",
        ["Test Case ID", "Module", "Input Condition / Test Stimulus", "Expected System Response", "Observed Result", "Status"],
        rd.TABLE_8_1_DATA,
        [Inches(1.0), Inches(1.0), Inches(1.6), Inches(1.4), Inches(1.1), Inches(0.6)]
    )

    # CHAPTER 9: CONCLUSION AND FUTURE ENHANCEMENT
    doc.add_page_break()
    add_chapter_title(doc, "9", "CONCLUSION AND FUTURE ENHANCEMENT")
    add_academic_text(doc, rd.CH9_TEXT)

    # APPENDIX
    doc.add_page_break()
    add_chapter_title(doc, "A", "APPENDIX")
    add_academic_text(doc, rd.APPENDIX_TEXT)
    add_image_figure(doc, "fig_app_screenshots.png", "Figure A.1: FraudLens AI Application Interface Ecosystem (4 Panels)")

    # REFERENCES
    doc.add_page_break()
    p_ref_title = doc.add_paragraph()
    style_paragraph(p_ref_title, space_before=20, space_after=14, align=WD_ALIGN_PARAGRAPH.CENTER)
    r = p_ref_title.add_run("REFERENCES")
    r.font.name = "Times New Roman"
    r.font.size = Pt(16)
    r.font.bold = True

    for ref in rd.REFERENCES_DATA:
        p = doc.add_paragraph()
        style_paragraph(p, space_before=0, space_after=2, line_spacing=1.18, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.3)
        r = p.add_run(clean_xml_string(ref))
        r.font.name = "Times New Roman"
        r.font.size = Pt(10.5)

    return doc

def measure_pages_with_word():
    """
    Open the initial document in Microsoft Word via COM,
    measures exact page numbers for all sections, tables, figures,
    and returns a precise mapping.
    """
    pythoncom.CoInitialize()
    word = None
    page_map = {}
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(str(docx_output_path.resolve()), ReadOnly=True)
        
        total_pages = doc.ComputeStatistics(2)
        print(f"Pass 1: Total Word Document Pages = {total_pages}")
        
        # Mapping rules for Section 2 (Body)
        body_patterns = [
            ("CHAPTER 1\nINTRODUCTION", "ch1"),
            ("1.1 OVERVIEW OF THE PROJECT", "ch1_1"),
            ("1.2 OBJECTIVE OF THE PROJECT", "ch1_2"),
            ("1.3 LITERATURE REVIEW", "ch1_3"),
            ("CHAPTER 2\nSYSTEM ANALYSIS", "ch2"),
            ("2.1 PROBLEM DEFINITION", "ch2_1"),
            ("2.2 EXISTING SYSTEM", "ch2_2"),
            ("2.3 PROPOSED SYSTEM", "ch2_3"),
            ("CHAPTER 3\nSYSTEM STUDY", "ch3"),
            ("3.1 FEASIBILITY STUDY", "ch3_1"),
            ("3.1.1 Economic Feasibility", "ch3_1_1"),
            ("3.1.2 Technical Feasibility", "ch3_1_2"),
            ("3.1.3 Performance Feasibility", "ch3_1_3"),
            ("CHAPTER 4\nSYSTEM REQUIREMENTS", "ch4"),
            ("4.1 HARDWARE REQUIREMENTS", "ch4_1"),
            ("4.2 SOFTWARE REQUIREMENTS", "ch4_2"),
            ("CHAPTER 5\nSYSTEM DESIGN", "ch5"),
            ("5.1 SYSTEM ARCHITECTURE", "ch5_1"),
            ("5.2 Class Diagram", "ch5_2"),
            ("5.3 Use Case Diagram", "ch5_3"),
            ("5.4 Flow Diagram", "ch5_4"),
            ("5.5 Sequence Diagram", "ch5_5"),
            ("5.6 DATABASE DESIGN", "ch5_6"),
            ("5.6.1 Table Design", "ch5_6_1"),
            ("5.6.2 ER Diagrams", "ch5_6_2"),
            ("5.6.3 Data Flow Diagrams", "ch5_6_3"),
            ("CHAPTER 6\nPROPOSED ALGORITHM IMPLEMENTATION", "ch6"),
            ("6.1 Project Description", "ch6_1"),
            ("6.1.1 Dataset Specification", "ch6_1_1"),
            ("6.1.2 Preprocessing", "ch6_1_2"),
            ("6.1.3 Behavioral", "ch6_1_3"),
            ("6.1.4 Stratified Data Splitting", "ch6_1_4"),
            ("6.1.5 Class Imbalance", "ch6_1_5"),
            ("6.1.6 Supervised Machine Learning", "ch6_1_6"),
            ("6.1.7 Decoupled Multi-Factor", "ch6_1_7"),
            ("6.1.8 Explainable AI via TreeSHAP", "ch6_1_8"),
            ("6.2 MODULES OVERVIEW", "ch6_2"),
            ("6.3 MODULE DESCRIPTION", "ch6_3"),
            ("CHAPTER 7\nRESULTS AND DISCUSSION", "ch7"),
            ("7.1 RESULTS AND DISCUSSION", "ch7_1"),
            ("7.1.1 Machine Learning Model", "ch7_1_1"),
            ("7.1.2 Confusion Matrix Analysis", "ch7_1_2"),
            ("7.1.3 Global and Local Feature Attribution", "ch7_1_3"),
            ("7.1.4 Pre-Authorization Latency", "ch7_1_4"),
            ("CHAPTER 8\nSYSTEM TESTING", "ch8"),
            ("8.1 TESTING", "ch8_1"),
            ("8.2 UNIT TESTING", "ch8_2"),
            ("8.3 INTEGRATION TESTING", "ch8_3"),
            ("8.4 VALIDATION TESTING", "ch8_4"),
            ("8.5 TESTING REPORT", "ch8_5"),
            ("CHAPTER 9\nCONCLUSION AND FUTURE ENHANCEMENT", "ch9"),
            ("9.1 CONCLUSION", "ch9_1"),
            ("9.2 FUTURE ENHANCEMENT", "ch9_2"),
            ("A.1 SELECTED CORE SOURCE CODE EXCERPTS", "app_a1"),
            ("A.2 APPLICATION INTERFACE ECOSYSTEM", "app_a2"),
            ("Figure A.1", "fig_a1"),
            ("Table 1.1", "table_1_1"),
            ("Table 3.1", "table_3_1"),
            ("Table 4.1", "table_4_1"),
            ("Table 4.2", "table_4_2"),
            ("Table 5.1", "table_5_1"),
            ("Table 6.1", "table_6_1"),
            ("Table 6.2", "table_6_2"),
            ("Table 6.3", "table_6_3"),
            ("Table 6.4", "table_6_4"),
            ("Table 6.5", "table_6_5"),
            ("Table 6.6", "table_6_6"),
            ("Table 7.1", "table_7_1"),
            ("Table 7.2", "table_7_2"),
            ("Table 7.3", "table_7_3"),
            ("Table 8.1", "table_8_1"),
            ("Figure 5.1", "fig_5_1"),
            ("Figure 5.2", "fig_5_2"),
            ("Figure 5.3", "fig_5_3"),
            ("Figure 5.4", "fig_5_4"),
            ("Figure 5.5", "fig_5_5"),
            ("Figure 5.6", "fig_5_6"),
            ("Figure 5.7", "fig_5_7"),
            ("Figure 5.8", "fig_5_8"),
            ("Figure 6.1", "fig_6_1"),
            ("Figure 6.2", "fig_6_2"),
            ("Figure 6.3", "fig_6_3"),
            ("Figure 6.4", "fig_6_4"),
            ("Figure 7.1", "fig_7_1"),
            ("Figure 7.2", "fig_7_2"),
            ("Figure 7.3", "fig_7_3"),
            ("Figure 7.4", "fig_7_4"),
        ]

        # Scan Section 1 paragraphs (Front matter roman numerals)
        sec1_paras = doc.Sections(1).Range.Paragraphs
        for p in sec1_paras:
            t = p.Range.Text.strip()
            if not t:
                continue
            pg_rom = p.Range.Information(1)
            roman_numerals = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii"]
            rom_str = roman_numerals[pg_rom - 1] if 1 <= pg_rom <= len(roman_numerals) else str(pg_rom)
            if t == "ABSTRACT" and "abstract" not in page_map:
                page_map["abstract"] = rom_str
            elif t == "ACKNOWLEDGEMENT" and "ack" not in page_map:
                page_map["ack"] = rom_str
            elif t == "TABLE OF CONTENTS" and "toc" not in page_map:
                page_map["toc"] = rom_str
            elif t == "LIST OF TABLES" and "lot" not in page_map:
                page_map["lot"] = rom_str
            elif t == "LIST OF FIGURES" and "lof" not in page_map:
                page_map["lof"] = rom_str

        # Scan Section 2 paragraphs (Body arabic page numbers)
        sec2_paras = doc.Sections(2).Range.Paragraphs
        print(f"Scanning {sec2_paras.Count} paragraphs in Section 2 (Body)...")
        for p in sec2_paras:
            t = p.Range.Text.strip()
            if not t:
                continue
            adj_pg = p.Range.Information(1)
            
            # Check for appendix heading
            if t == "APPENDIX" and "appendix" not in page_map:
                page_map["appendix"] = adj_pg
            elif t == "REFERENCES" and "references" not in page_map:
                page_map["references"] = adj_pg
                
            for pattern, key in body_patterns:
                if key not in page_map and pattern.lower() in t.lower():
                    page_map[key] = adj_pg

        doc.Close(False)
    except Exception as e:
        print(f"Error during page measurement: {e}")
    finally:
        if word:
            word.Quit()
        pythoncom.CoUninitialize()

    return page_map

def generate_and_export():
    print("--- STEP 1: Building Pass 1 Initial DOCX ---")
    doc_initial = build_docx_tree(page_map=None)
    doc_initial.save(str(docx_output_path))
    print(f"Initial DOCX saved at: {docx_output_path}")

    print("\n--- STEP 2: Measuring Exact Page Numbers via Word COM ---")
    page_map = measure_pages_with_word()
    print(f"Successfully mapped {len(page_map)} targets to exact pages.")
    for k, v in sorted(page_map.items()):
        print(f"  {k:15s} -> Page {v}")

    print("\n--- STEP 3: Building Pass 2 Final DOCX with True Synchronized Pages ---")
    import time as _time
    _time.sleep(3)  # Let Word COM fully release the file lock from Step 2
    # Remove the existing file to avoid PermissionError on save
    if docx_output_path.exists():
        try:
            docx_output_path.unlink()
        except Exception as _e:
            print(f"Warning: Could not delete existing DOCX: {_e}")
    doc_final = build_docx_tree(page_map=page_map)
    doc_final.save(str(docx_output_path))
    print(f"Final DOCX saved at: {docx_output_path} ({docx_output_path.stat().st_size:,} bytes)")

    print("\n--- STEP 4: Exporting Final PDF via Word COM ---")
    pythoncom.CoInitialize()
    word = None
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(str(docx_output_path.resolve()), ReadOnly=True)
        final_page_count = doc.ComputeStatistics(2)
        print(f"Final True Page Count in Word: {final_page_count} pages")
        
        # wdFormatPDF = 17
        doc.SaveAs(str(pdf_output_path.resolve()), FileFormat=17)
        doc.Close(False)
        print(f"Final PDF exported at: {pdf_output_path} ({pdf_output_path.stat().st_size:,} bytes)")
    except Exception as e:
        print(f"PDF Export Error: {e}")
    finally:
        if word:
            word.Quit()
        pythoncom.CoUninitialize()

    return page_map

if __name__ == "__main__":
    generate_and_export()
