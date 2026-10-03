"""
FraudLens AI HTML Project Report Generator.
Generates a complete, publication-grade academic report matching
Anna University / Sona College of Technology formatting specifications.
"""

import sys
import os
import re
from pathlib import Path

# Add scripts directory to path to import report_data
sys.path.insert(0, str(Path(__file__).parent))
import report_data as rd


project_root = Path("e:/fraudinvestigation")
report_dir = project_root / "project_report"
assets_dir = report_dir / "assets"
html_output_path = report_dir / "FraudLens_AI_Project_Report.html"

def format_academic_html(raw_text):
    """Formats raw text into proper academic H2 section titles, H3 subsection titles, and justified paragraphs."""
    paragraphs = raw_text.strip().split("\n\n")
    html_out = []
    for p in paragraphs:
        p_clean = p.strip()
        if not p_clean:
            continue
        lines = p_clean.split("\n")
        first_line = lines[0].strip()

        # Level 2 Heading: e.g. "1.1 OVERVIEW OF THE PROJECT", "6.2 MODULES OVERVIEW"
        if re.match(r"^(\d+\.\d+|[A-Z]\.\d+)\s+[A-Z]", first_line) and len(first_line) < 100:
            html_out.append(f'<h2 class="section-title">{first_line}</h2>')
            rem = "\n".join(lines[1:]).strip()
            if rem:
                html_out.append(f'<p>{rem.replace(chr(10), "<br>")}</p>')
        # Level 3 Heading: e.g. "1.3.1 Statistical Profiling...", "6.1.4 Stratified..."
        elif re.match(r"^\d+\.\d+\.\d+\s+[A-Za-z]", first_line) and len(first_line) < 120:
            html_out.append(f'<h3 class="subsection-title">{first_line}</h3>')
            rem = "\n".join(lines[1:]).strip()
            if rem:
                html_out.append(f'<p>{rem.replace(chr(10), "<br>")}</p>')
        else:
            p_formatted = p_clean.replace("\n", "<br>")
            html_out.append(f'<p>{p_formatted}</p>')
    return "\n".join(html_out)


def build_html():
    html = []
    html.append("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FraudLens AI — Master Academic Project Report</title>
<style>
  @page {
    size: A4;
    margin: 25mm 25mm 25mm 25mm;
    @bottom-center {
      content: counter(page);
      font-family: "Times New Roman", Times, serif;
      font-size: 11pt;
    }
  }

  body {
    font-family: "Times New Roman", Times, serif;
    font-size: 12pt;
    line-height: 1.5;
    color: #000000;
    background-color: #ffffff;
    margin: 0 auto;
    padding: 20mm;
    max-width: 210mm;
    box-sizing: border-box;
    text-align: justify;
  }

  .page-break {
    page-break-before: always;
    break-before: page;
    margin-top: 30px;
    padding-top: 20px;
  }

  /* Headings */
  h1.chapter-title {
    font-size: 16pt;
    font-weight: bold;
    text-align: center;
    text-transform: uppercase;
    margin-top: 40px;
    margin-bottom: 25px;
    color: #000000;
  }

  h2.section-title {
    font-size: 14pt;
    font-weight: bold;
    margin-top: 25px;
    margin-bottom: 12px;
    color: #000000;
  }

  h3.subsection-title {
    font-size: 12pt;
    font-weight: bold;
    margin-top: 18px;
    margin-bottom: 8px;
    color: #000000;
  }

  p {
    margin-top: 0;
    margin-bottom: 12px;
    text-indent: 0;
  }

  /* Cover & Certificate styles */
  .center-text {
    text-align: center;
  }
  .bold {
    font-weight: bold;
  }
  .italic {
    font-style: italic;
  }

  .title-page-title {
    font-size: 18pt;
    font-weight: bold;
    line-height: 1.5;
    margin-top: 40px;
    margin-bottom: 30px;
  }

  .title-page-sub {
    font-size: 14pt;
    margin-bottom: 25px;
  }

  .title-page-candidate {
    font-size: 16pt;
    font-weight: bold;
    margin-top: 30px;
    margin-bottom: 30px;
  }

  .title-page-degree {
    font-size: 16pt;
    font-weight: bold;
    line-height: 1.4;
    margin-top: 30px;
    margin-bottom: 40px;
  }

  .title-page-college {
    font-size: 16pt;
    font-weight: bold;
    line-height: 1.4;
    margin-top: 40px;
  }

  .title-page-university {
    font-size: 14pt;
    font-weight: bold;
    margin-top: 15px;
    margin-bottom: 20px;
  }

  /* Tables */
  table.academic-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
    margin-bottom: 20px;
    font-size: 10pt;
    line-height: 1.3;
  }

  table.academic-table th, table.academic-table td {
    border: 1px solid #333333;
    padding: 6px 8px;
    text-align: left;
    vertical-align: top;
  }

  table.academic-table th {
    background-color: #f1f5f9;
    font-weight: bold;
    color: #0f172a;
    text-align: center;
  }

  .table-caption {
    font-weight: bold;
    font-size: 11pt;
    margin-top: 15px;
    margin-bottom: 6px;
    text-align: left;
  }

  .figure-container {
    text-align: center;
    margin-top: 20px;
    margin-bottom: 20px;
  }

  .figure-img {
    max-width: 95%;
    height: auto;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }

  .figure-caption {
    font-weight: bold;
    font-size: 10.5pt;
    margin-top: 8px;
    margin-bottom: 15px;
    text-align: center;
  }

  /* TOC layout */
  .toc-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
  }

  .toc-dots {
    flex-grow: 1;
    border-bottom: 1px dotted #666;
    margin: 0 5px 4px 5px;
  }

  /* Code blocks */
  pre.code-block {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 3px solid #0284c7;
    padding: 10px;
    font-family: "Courier New", Courier, monospace;
    font-size: 8.5pt;
    line-height: 1.25;
    overflow-x: auto;
    margin: 10px 0;
  }

  @media print {
    body {
      padding: 0;
      max-width: 100%;
    }
  }
</style>
</head>
<body>
""")

    # --------------------------------------------------------------------------
    # COVER PAGE (APPENDIX 1)
    # --------------------------------------------------------------------------
    html.append(f"""
<div class="center-text">
  <div style="font-size: 11pt; margin-bottom: 20px;">APPENDIX 1<br>(A typical Specimen of Cover Page & Title Page)</div>
  <div class="title-page-title">{rd.FRONT_MATTER['project_title']}</div>
  <div class="title-page-sub bold">A PROJECT REPORT</div>
  <div style="font-size: 14pt; margin-bottom: 15px;" class="italic">Submitted by</div>
  <div class="title-page-candidate">{rd.FRONT_MATTER['candidate_name']}<br><span style="font-size: 14pt; font-weight: normal;">(Reg. No.: {rd.FRONT_MATTER['reg_no']})</span></div>
  <div style="font-size: 14pt; line-height: 1.5; margin-bottom: 25px;" class="italic">
    in partial fulfillment for the award of the degree<br>of
  </div>
  <div class="title-page-degree">
    {rd.FRONT_MATTER['degree']}<br>
    <span style="font-size: 14pt;">IN</span><br>
    {rd.FRONT_MATTER['branch']}
  </div>
  <div class="title-page-college">
    {rd.FRONT_MATTER['college_name']}
  </div>
  <div class="title-page-university">
    {rd.FRONT_MATTER['university']}
  </div>
  <div style="font-size: 14pt; font-weight: bold; margin-top: 25px;">
    {rd.FRONT_MATTER['month_year']}
  </div>
</div>
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # TITLE PAGE (APPENDIX 1 DUPLICATE)
    # --------------------------------------------------------------------------
    html.append(f"""
<div class="center-text">
  <div class="title-page-title">{rd.FRONT_MATTER['project_title']}</div>
  <div class="title-page-sub bold">A PROJECT REPORT</div>
  <div style="font-size: 14pt; margin-bottom: 15px;" class="italic">Submitted by</div>
  <div class="title-page-candidate">{rd.FRONT_MATTER['candidate_name']}<br><span style="font-size: 14pt; font-weight: normal;">(Reg. No.: {rd.FRONT_MATTER['reg_no']})</span></div>
  <div style="font-size: 14pt; line-height: 1.5; margin-bottom: 25px;" class="italic">
    in partial fulfillment for the award of the degree<br>of
  </div>
  <div class="title-page-degree">
    {rd.FRONT_MATTER['degree']}<br>
    <span style="font-size: 14pt;">IN</span><br>
    {rd.FRONT_MATTER['branch']}
  </div>
  <div class="title-page-college">
    {rd.FRONT_MATTER['college_name']}
  </div>
  <div class="title-page-university">
    {rd.FRONT_MATTER['university']}
  </div>
  <div style="font-size: 14pt; font-weight: bold; margin-top: 25px;">
    {rd.FRONT_MATTER['month_year']}
  </div>
</div>
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # APPENDIX 2: COMPLETION CERTIFICATE
    # --------------------------------------------------------------------------
    html.append(f"""
<div class="center-text">
  <div style="font-size: 11pt; margin-bottom: 20px;">APPENDIX 2<br>(SAMPLE SHEET FOR COMPLETION CERTIFICATE)</div>
  <div style="font-size: 16pt; font-weight: bold; line-height: 1.5; margin-top: 30px;">{rd.FRONT_MATTER['college_name']}</div>
  <div style="font-size: 14pt; font-weight: bold; line-height: 1.5; margin-top: 10px; margin-bottom: 60px;">{rd.FRONT_MATTER['department']}</div>
</div>

<p style="font-size: 13pt; line-height: 1.8; margin-top: 40px; text-align: justify;">
The project report entitled <strong>&ldquo;{rd.FRONT_MATTER['project_title']}&rdquo;</strong> submitted by <strong>{rd.FRONT_MATTER['candidate_name']} (Reg. No. {rd.FRONT_MATTER['reg_no']})</strong> is completed and may be accepted for being evaluated.
</p>

<div style="margin-top: 140px; display: flex; justify-content: space-between; font-size: 12pt;">
  <div>
    <strong>Date:</strong> 03-10-2026<br>
    <strong>Place:</strong> Salem
  </div>
  <div style="text-align: right;">
    <br><br>
    <strong>Signature of the Supervisor</strong><br>
    ({rd.FRONT_MATTER['supervisor_name']})<br>
    {rd.FRONT_MATTER['supervisor_designation']}
  </div>
</div>
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # APPENDIX 3: BONAFIDE CERTIFICATE
    # --------------------------------------------------------------------------
    html.append(f"""
<div class="center-text">
  <div style="font-size: 11pt; margin-bottom: 15px;">APPENDIX 3<br>(A typical specimen of Bonafide Certificate)</div>
  <div style="font-size: 18pt; font-weight: bold; line-height: 1.4;">SONA COLLEGE OF TECHNOLOGY, SALEM</div>
  <div style="font-size: 15pt; font-weight: bold; margin-bottom: 5px;">(AUTONOMOUS)</div>
  <div style="font-size: 13pt; font-weight: bold; margin-bottom: 35px;">AFFILIATED TO ANNA UNIVERSITY : CHENNAI 600 025</div>
</div>

<p style="font-size: 12.5pt; line-height: 1.8; margin-top: 30px; text-align: justify;">
Certified that this project report <strong>&ldquo;{rd.FRONT_MATTER['project_title']}&rdquo;</strong> is the bonafide work of <strong>{rd.FRONT_MATTER['candidate_name']} (Reg. No.: {rd.FRONT_MATTER['reg_no']})</strong> who carried out the project work under my supervision.
</p>

<div style="margin-top: 130px; display: flex; justify-content: space-between; font-size: 11.5pt;">
  <div style="text-align: left; width: 48%;">
    <strong>SIGNATURE</strong><br><br><br>
    <strong>{rd.FRONT_MATTER['hod_name']}</strong><br>
    <strong>HEAD OF THE DEPARTMENT</strong><br>
    {rd.FRONT_MATTER['hod_designation']}<br>
    {rd.FRONT_MATTER['full_address']}
  </div>
  <div style="text-align: right; width: 48%;">
    <strong>SIGNATURE</strong><br><br><br>
    <strong>{rd.FRONT_MATTER['supervisor_name']}</strong><br>
    <strong>SUPERVISOR</strong><br>
    {rd.FRONT_MATTER['supervisor_designation']}<br>
    {rd.FRONT_MATTER['full_address']}
  </div>
</div>
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # ABSTRACT & ACKNOWLEDGEMENT
    # --------------------------------------------------------------------------
    html.append(f"""
<h1 class="chapter-title">ABSTRACT</h1>
<p>{rd.ABSTRACT_TEXT.strip().replace(chr(10)+chr(10), '</p><p>')}</p>
<div class="page-break"></div>

<h1 class="chapter-title">ACKNOWLEDGEMENT</h1>
<p>{rd.ACKNOWLEDGEMENT_TEXT.strip().replace(chr(10)+chr(10), '</p><p>')}</p>
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # TABLE OF CONTENTS
    # --------------------------------------------------------------------------
    html.append("""
<h1 class="chapter-title">TABLE OF CONTENTS</h1>
<table style="width: 100%; border: none; font-size: 11pt; line-height: 1.6;">
  <tr style="font-weight: bold; border-bottom: 2px solid #000;">
    <td style="width: 15%;">CHAPTER</td>
    <td style="width: 70%;">TITLE</td>
    <td style="width: 15%; text-align: right;">PAGE NO</td>
  </tr>
  <tr><td></td><td class="bold">ABSTRACT</td><td style="text-align: right;">v</td></tr>
  <tr><td></td><td class="bold">ACKNOWLEDGEMENT</td><td style="text-align: right;">vi</td></tr>
  <tr><td></td><td class="bold">LIST OF TABLES</td><td style="text-align: right;">ix</td></tr>
  <tr><td></td><td class="bold">LIST OF FIGURES</td><td style="text-align: right;">x</td></tr>
  
  <tr style="font-weight: bold; padding-top: 8px;"><td style="padding-top: 8px;">1</td><td style="padding-top: 8px;">INTRODUCTION</td><td style="padding-top: 8px; text-align: right;">1</td></tr>
  <tr><td></td><td style="padding-left: 20px;">1.1 Overview of the Project</td><td style="text-align: right;">1</td></tr>
  <tr><td></td><td style="padding-left: 20px;">1.2 Objective of the Project</td><td style="text-align: right;">2</td></tr>
  <tr><td></td><td style="padding-left: 20px;">1.3 Literature Review</td><td style="text-align: right;">4</td></tr>
  <tr><td></td><td style="padding-left: 40px;">1.3.6 Identified Research Gaps & Contributions</td><td style="text-align: right;">6</td></tr>

  <tr style="font-weight: bold; padding-top: 8px;"><td style="padding-top: 8px;">2</td><td style="padding-top: 8px;">SYSTEM ANALYSIS</td><td style="padding-top: 8px; text-align: right;">8</td></tr>
  <tr><td></td><td style="padding-left: 20px;">2.1 Problem Definition</td><td style="text-align: right;">9</td></tr>
  <tr><td></td><td style="padding-left: 20px;">2.2 Existing System</td><td style="text-align: right;">10</td></tr>
  <tr><td></td><td style="padding-left: 20px;">2.3 Proposed System</td><td style="text-align: right;">11</td></tr>

  <tr style="font-weight: bold; padding-top: 8px;"><td style="padding-top: 8px;">3</td><td style="padding-top: 8px;">SYSTEM STUDY</td><td style="padding-top: 8px; text-align: right;">12</td></tr>
  <tr><td></td><td style="padding-left: 20px;">3.1 Feasibility Study</td><td style="text-align: right;">13</td></tr>
  <tr><td></td><td style="padding-left: 40px;">3.1.1 Economic Feasibility</td><td style="text-align: right;">13</td></tr>
  <tr><td></td><td style="padding-left: 40px;">3.1.2 Technical Feasibility</td><td style="text-align: right;">13</td></tr>
  <tr><td></td><td style="padding-left: 40px;">3.1.3 Performance Feasibility</td><td style="text-align: right;">14</td></tr>

  <tr style="font-weight: bold; padding-top: 8px;"><td style="padding-top: 8px;">4</td><td style="padding-top: 8px;">SYSTEM REQUIREMENTS</td><td style="padding-top: 8px; text-align: right;">15</td></tr>
  <tr><td></td><td style="padding-left: 20px;">4.1 Hardware Requirements</td><td style="text-align: right;">16</td></tr>
  <tr><td></td><td style="padding-left: 20px;">4.2 Software Requirements</td><td style="text-align: right;">16</td></tr>

  <tr style="font-weight: bold; padding-top: 8px;"><td style="padding-top: 8px;">5</td><td style="padding-top: 8px;">SYSTEM DESIGN</td><td style="padding-top: 8px; text-align: right;">17</td></tr>
  <tr><td></td><td style="padding-left: 20px;">5.1 System Architecture</td><td style="text-align: right;">18</td></tr>
  <tr><td></td><td style="padding-left: 20px;">5.2 Class Diagram</td><td style="text-align: right;">19</td></tr>
  <tr><td></td><td style="padding-left: 20px;">5.3 Use Case Diagram</td><td style="text-align: right;">20</td></tr>
  <tr><td></td><td style="padding-left: 20px;">5.4 Flow Diagram</td><td style="text-align: right;">21</td></tr>
  <tr><td></td><td style="padding-left: 20px;">5.5 Sequence Diagram</td><td style="text-align: right;">21</td></tr>
  <tr><td></td><td style="padding-left: 20px;">5.6 Database Design</td><td style="text-align: right;">22</td></tr>
  <tr><td></td><td style="padding-left: 40px;">5.6.1 Table Design</td><td style="text-align: right;">22</td></tr>
  <tr><td></td><td style="padding-left: 40px;">5.6.2 ER Diagrams</td><td style="text-align: right;">22</td></tr>
  <tr><td></td><td style="padding-left: 40px;">5.6.3 Data Flow Diagrams</td><td style="text-align: right;">23</td></tr>

  <tr style="font-weight: bold; padding-top: 8px;"><td style="padding-top: 8px;">6</td><td style="padding-top: 8px;">PROPOSED ALGORITHM IMPLEMENTATION</td><td style="padding-top: 8px; text-align: right;">31</td></tr>
  <tr><td></td><td style="padding-left: 20px;">6.1 Project Description</td><td style="text-align: right;">30</td></tr>
  <tr><td></td><td style="padding-left: 40px;">6.1.1 Dataset Specification & Integrity Audit</td><td style="text-align: right;">30</td></tr>
  <tr><td></td><td style="padding-left: 40px;">6.1.2 Preprocessing, Imputation & Scaling</td><td style="text-align: right;">30</td></tr>
  <tr><td></td><td style="padding-left: 40px;">6.1.3 Behavioral Feature Engineering</td><td style="text-align: right;">31</td></tr>
  <tr><td></td><td style="padding-left: 40px;">6.1.5 Class Imbalance Mitigation Strategy</td><td style="text-align: right;">32</td></tr>
  <tr><td></td><td style="padding-left: 40px;">6.1.7 Decoupled Multi-Factor Risk Scoring</td><td style="text-align: right;">33</td></tr>
  <tr><td></td><td style="padding-left: 40px;">6.1.8 Explainable AI via TreeSHAP</td><td style="text-align: right;">34</td></tr>
  <tr><td></td><td style="padding-left: 20px;">6.2 Modules Overview</td><td style="text-align: right;">34</td></tr>
  <tr><td></td><td style="padding-left: 20px;">6.3 Module Description (6.3.1 - 6.3.10)</td><td style="text-align: right;">35</td></tr>

  <tr style="font-weight: bold; padding-top: 8px;"><td style="padding-top: 8px;">7</td><td style="padding-top: 8px;">RESULTS AND DISCUSSION</td><td style="padding-top: 8px; text-align: right;">44</td></tr>
  <tr><td></td><td style="padding-left: 20px;">7.1 Results and Discussion</td><td style="text-align: right;">43</td></tr>
  <tr><td></td><td style="padding-left: 40px;">7.1.1 ML Model Performance Comparison</td><td style="text-align: right;">43</td></tr>
  <tr><td></td><td style="padding-left: 40px;">7.1.2 Confusion Matrix Analysis</td><td style="text-align: right;">43</td></tr>
  <tr><td></td><td style="padding-left: 40px;">7.1.3 Global & Local TreeSHAP Attributions</td><td style="text-align: right;">44</td></tr>
  <tr><td></td><td style="padding-left: 40px;">7.1.4 Pre-Authorization Latency Profile</td><td style="text-align: right;">44</td></tr>

  <tr style="font-weight: bold; padding-top: 8px;"><td style="padding-top: 8px;">8</td><td style="padding-top: 8px;">SYSTEM TESTING</td><td style="padding-top: 8px; text-align: right;">48</td></tr>
  <tr><td></td><td style="padding-left: 20px;">8.1 Testing Methodology</td><td style="text-align: right;">49</td></tr>
  <tr><td></td><td style="padding-left: 20px;">8.2 Unit Testing</td><td style="text-align: right;">49</td></tr>
  <tr><td></td><td style="padding-left: 20px;">8.3 Integration Testing</td><td style="text-align: right;">49</td></tr>
  <tr><td></td><td style="padding-left: 20px;">8.4 Validation Testing</td><td style="text-align: right;">50</td></tr>
  <tr><td></td><td style="padding-left: 20px;">8.5 Testing Report</td><td style="text-align: right;">50</td></tr>

  <tr style="font-weight: bold; padding-top: 8px;"><td style="padding-top: 8px;">9</td><td style="padding-top: 8px;">CONCLUSION AND FUTURE ENHANCEMENT</td><td style="padding-top: 8px; text-align: right;">52</td></tr>
  <tr><td></td><td style="padding-left: 20px;">9.1 Conclusion</td><td style="text-align: right;">53</td></tr>
  <tr><td></td><td style="padding-left: 20px;">9.2 Future Enhancement</td><td style="text-align: right;">54</td></tr>

  <tr style="font-weight: bold; padding-top: 8px;"><td style="padding-top: 8px;"></td><td style="padding-top: 8px;">APPENDIX</td><td style="padding-top: 8px; text-align: right;">55</td></tr>
  <tr><td></td><td style="padding-left: 20px;">A.1 Core Source Code Excerpts</td><td style="text-align: right;">55</td></tr>
  <tr><td></td><td style="padding-left: 20px;">A.2 Application Screenshots Ecosystem</td><td style="text-align: right;">57</td></tr>

  <tr style="font-weight: bold; padding-top: 8px;"><td style="padding-top: 8px;"></td><td style="padding-top: 8px;">REFERENCES</td><td style="padding-top: 8px; text-align: right;">58</td></tr>
</table>
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # LIST OF TABLES
    # --------------------------------------------------------------------------
    html.append("""
<h1 class="chapter-title">LIST OF TABLES</h1>
<table style="width: 100%; border: none; font-size: 11pt; line-height: 1.8;">
  <tr style="font-weight: bold; border-bottom: 2px solid #000;">
    <td style="width: 20%;">TABLE NO.</td>
    <td style="width: 65%;">TITLE</td>
    <td style="width: 15%; text-align: right;">PAGE NO</td>
  </tr>
  <tr><td>Table 1.1</td><td>Comparative Literature Survey of Fraud Detection Methodologies</td><td style="text-align: right;">5</td></tr>
  <tr><td>Table 3.1</td><td>Economic Feasibility Cost-Benefit and ROI Analysis</td><td style="text-align: right;">13</td></tr>
  <tr><td>Table 4.1</td><td>Hardware Infrastructure Specifications</td><td style="text-align: right;">15</td></tr>
  <tr><td>Table 4.2</td><td>Software Environment & Runtime Dependencies</td><td style="text-align: right;">16</td></tr>
  <tr><td>Table 5.1</td><td>Relational Database Schema Specifications (20 Entities)</td><td style="text-align: right;">26</td></tr>
  <tr><td>Table 6.1</td><td>Master Dataset Attribute & Domain Specifications (57 Features)</td><td style="text-align: right;">32</td></tr>
  <tr><td>Table 6.2</td><td>Preprocessing Transformation & Imputation Strategy</td><td style="text-align: right;">34</td></tr>
  <tr><td>Table 6.3</td><td>Machine Learning Model Hyperparameters & Architecture</td><td style="text-align: right;">36</td></tr>
  <tr><td>Table 6.4</td><td>Multi-Factor Risk Scoring Point Allocation Matrix</td><td style="text-align: right;">38</td></tr>
  <tr><td>Table 6.5</td><td>Global Top-15 Feature Importance Attributions via TreeSHAP</td><td style="text-align: right;">39</td></tr>
  <tr><td>Table 6.6</td><td>Pre-Authorization Three-Tier Decision Matrix & Actions</td><td style="text-align: right;">40</td></tr>
  <tr><td>Table 7.1</td><td>Comprehensive ML Model Performance Comparison</td><td style="text-align: right;">44</td></tr>
  <tr><td>Table 7.2</td><td>Confusion Matrix Metrics across Test & Deployment Splits</td><td style="text-align: right;">45</td></tr>
  <tr><td>Table 7.3</td><td>Sub-5 Millisecond Pre-Authorization Latency Breakdown</td><td style="text-align: right;">47</td></tr>
  <tr><td>Table 8.1</td><td>Formal Software Verification & Validation Test Report (30 Cases)</td><td style="text-align: right;">49</td></tr>
</table>
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # LIST OF FIGURES
    # --------------------------------------------------------------------------
    html.append("""
<h1 class="chapter-title">LIST OF FIGURES</h1>
<table style="width: 100%; border: none; font-size: 11pt; line-height: 1.8;">
  <tr style="font-weight: bold; border-bottom: 2px solid #000;">
    <td style="width: 20%;">FIGURE NO.</td>
    <td style="width: 65%;">TITLE</td>
    <td style="width: 15%; text-align: right;">PAGE NO</td>
  </tr>
  <tr><td>Figure 5.1</td><td>FraudLens AI Multi-Tier System Architecture</td><td style="text-align: right;">18</td></tr>
  <tr><td>Figure 5.2</td><td>Core Domain UML Class Diagram</td><td style="text-align: right;">20</td></tr>
  <tr><td>Figure 5.3</td><td>UML Use Case Diagram for User Roles</td><td style="text-align: right;">21</td></tr>
  <tr><td>Figure 5.4</td><td>Pre-Authorization & Autonomous Decision System Flow</td><td style="text-align: right;">23</td></tr>
  <tr><td>Figure 5.5</td><td>Pre-Authorization Step-Up Verification Sequence Diagram</td><td style="text-align: right;">24</td></tr>
  <tr><td>Figure 5.6</td><td>FraudLens AI Relational Entity-Relationship (ER) Diagram</td><td style="text-align: right;">28</td></tr>
  <tr><td>Figure 5.7</td><td>Data Flow Diagram (DFD) Level 0 — Context Diagram</td><td style="text-align: right;">29</td></tr>
  <tr><td>Figure 5.8</td><td>Data Flow Diagram (DFD) Level 1 — Process Decomposition</td><td style="text-align: right;">30</td></tr>
  <tr><td>Figure 6.1</td><td>End-to-End Machine Learning & Feature Pipeline Workflow</td><td style="text-align: right;">35</td></tr>
  <tr><td>Figure 6.2</td><td>Multi-Factor Additive Risk Scoring Architecture & Tiers</td><td style="text-align: right;">37</td></tr>
  <tr><td>Figure 6.3</td><td>Local TreeSHAP Feature Attribution Waterfall for Flagged Transaction</td><td style="text-align: right;">39</td></tr>
  <tr><td>Figure 6.4</td><td>Pre-Authorization Mobile SMS OTP Verification Lifecycle</td><td style="text-align: right;">42</td></tr>
  <tr><td>Figure 7.1</td><td>ROC and Precision-Recall Curves on Test Split</td><td style="text-align: right;">44</td></tr>
  <tr><td>Figure 7.2</td><td>Confusion Matrix Heatmaps across Test & Active Validation Splits</td><td style="text-align: right;">45</td></tr>
  <tr><td>Figure 7.3</td><td>Global Top-15 Feature Importance Ranking via TreeSHAP</td><td style="text-align: right;">46</td></tr>
  <tr><td>Figure 7.4</td><td>Sub-5 Millisecond Pre-Authorization Latency Breakdown Profile</td><td style="text-align: right;">47</td></tr>
  <tr><td>Figure A.1</td><td>FraudLens AI Application Interface Ecosystem (4 Panels)</td><td style="text-align: right;">56</td></tr>
</table>
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # CHAPTER 1: INTRODUCTION
    # --------------------------------------------------------------------------
    html.append(f"""
<h1 class="chapter-title">CHAPTER 1<br>INTRODUCTION</h1>
{format_academic_html(rd.CH1_OVERVIEW)}
{format_academic_html(rd.CH1_OBJECTIVES)}
{format_academic_html(rd.CH1_LITERATURE)}

<div class="table-caption">Table 1.1: Comparative Literature Survey of Prominent Financial Fraud Detection Methodologies</div>
<table class="academic-table">
  <tr>
    <th style="width: 15%;">Author / Year</th>
    <th style="width: 17%;">Methodology</th>
    <th style="width: 15%;">Context / Domain</th>
    <th style="width: 20%;">Key Finding</th>
    <th style="width: 18%;">Major Limitation</th>
    <th style="width: 15%;">Relevance to FraudLens AI</th>
  </tr>
""")
    for row in rd.TABLE_1_1_DATA:
        html.append(f"""  <tr>
    <td class="bold">{row['author']}</td>
    <td>{row['method']}</td>
    <td>{row['context']}</td>
    <td>{row['finding']}</td>
    <td>{row['limitation']}</td>
    <td>{row['relevance']}</td>
  </tr>""")
    html.append(f"""</table>

{format_academic_html(rd.RESEARCH_GAP_TEXT)}
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # CHAPTER 2: SYSTEM ANALYSIS
    # --------------------------------------------------------------------------
    html.append(f"""
<h1 class="chapter-title">CHAPTER 2<br>SYSTEM ANALYSIS</h1>
{format_academic_html(rd.CH2_TEXT)}
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # CHAPTER 3: SYSTEM STUDY
    # --------------------------------------------------------------------------
    html.append(f"""
<h1 class="chapter-title">CHAPTER 3<br>SYSTEM STUDY</h1>
{format_academic_html(rd.CH3_TEXT)}

<div class="table-caption">Table 3.1: Economic Feasibility Cost-Benefit and ROI Analysis</div>
<table class="academic-table">
  <tr>
    <th style="width: 30%;">Operational Cost / Benefit Dimension</th>
    <th style="width: 40%;">Description & Implementation Baseline</th>
    <th style="width: 15%;">Estimated Value</th>
    <th style="width: 15%;">Horizon</th>
  </tr>
""")
    for item, desc, val, horizon in rd.TABLE_3_1_DATA:
        html.append(f"""  <tr>
    <td class="bold">{item}</td>
    <td>{desc}</td>
    <td style="text-align: right; font-weight: bold;">{val}</td>
    <td>{horizon}</td>
  </tr>""")
    html.append("""</table>
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # CHAPTER 4: SYSTEM REQUIREMENTS
    # --------------------------------------------------------------------------
    html.append(f"""
<h1 class="chapter-title">CHAPTER 4<br>SYSTEM REQUIREMENTS</h1>
{format_academic_html(rd.CH4_TEXT)}

<div class="table-caption">Table 4.1: Minimum & Recommended Hardware Infrastructure Specifications</div>
<table class="academic-table">
  <tr>
    <th style="width: 25%;">Hardware Component</th>
    <th style="width: 25%;">Minimum Specification</th>
    <th style="width: 25%;">Recommended Development</th>
    <th style="width: 25%;">Production Deployment</th>
  </tr>
""")
    for comp, min_s, rec_s, prod_s in rd.TABLE_4_1_DATA:
        html.append(f"""  <tr>
    <td class="bold">{comp}</td>
    <td>{min_s}</td>
    <td>{rec_s}</td>
    <td>{prod_s}</td>
  </tr>""")
    html.append("""</table>

<div class="table-caption">Table 4.2: Production Software Environment & Library Dependencies</div>
<table class="academic-table">
  <tr>
    <th style="width: 30%;">Software Component</th>
    <th style="width: 45%;">Version / Specification</th>
    <th style="width: 25%;">Operational Role</th>
  </tr>
""")
    for comp, ver, role in rd.TABLE_4_2_DATA:
        html.append(f"""  <tr>
    <td class="bold">{comp}</td>
    <td>{ver}</td>
    <td>{role}</td>
  </tr>""")
    html.append("""</table>
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # CHAPTER 5: SYSTEM DESIGN
    # --------------------------------------------------------------------------
    html.append(f"""
<h1 class="chapter-title">CHAPTER 5<br>SYSTEM DESIGN</h1>
{format_academic_html(rd.CH5_TEXT)}

<div class="figure-container">
  <img src="assets/fig_5_1_system_architecture.png" class="figure-img" alt="System Architecture">
  <div class="figure-caption">Figure 5.1: FraudLens AI Multi-Tier System Architecture</div>
</div>

<div class="figure-container">
  <img src="assets/fig_5_2_class_diagram.png" class="figure-img" alt="UML Class Diagram">
  <div class="figure-caption">Figure 5.2: Core Domain UML Class Diagram</div>
</div>

<div class="figure-container">
  <img src="assets/fig_5_3_use_case_diagram.png" class="figure-img" alt="UML Use Case Diagram">
  <div class="figure-caption">Figure 5.3: UML Use Case Diagram for User Roles</div>
</div>

<div class="figure-container">
  <img src="assets/fig_5_4_flow_diagram.png" class="figure-img" alt="System Flow Diagram">
  <div class="figure-caption">Figure 5.4: Pre-Authorization & Autonomous Decision System Flow</div>
</div>

<div class="figure-container">
  <img src="assets/fig_5_5_sequence_diagram.png" class="figure-img" alt="Sequence Diagram">
  <div class="figure-caption">Figure 5.5: Pre-Authorization Step-Up Verification Sequence Diagram</div>
</div>

<div class="table-caption">Table 5.1: Relational Database Schema Specifications (20 Relational Entities)</div>
<table class="academic-table">
  <tr>
    <th style="width: 18%;">Table Name</th>
    <th style="width: 47%;">Columns, Keys & Constraints</th>
    <th style="width: 10%;">Row Count</th>
    <th style="width: 25%;">Operational Description</th>
  </tr>
""")
    for tname, cols, rcnt, desc in rd.TABLE_5_1_DATA:
        html.append(f"""  <tr>
    <td class="bold">{tname}</td>
    <td style="font-family: monospace; font-size: 8.5pt;">{cols}</td>
    <td style="text-align: right; font-weight: bold;">{rcnt}</td>
    <td>{desc}</td>
  </tr>""")
    html.append("""</table>

<div class="figure-container">
  <img src="assets/fig_5_6_er_diagram.png" class="figure-img" alt="ER Diagram">
  <div class="figure-caption">Figure 5.6: FraudLens AI Relational Entity-Relationship (ER) Diagram</div>
</div>

<div class="figure-container">
  <img src="assets/fig_5_7_dfd_level_0.png" class="figure-img" alt="DFD Level 0">
  <div class="figure-caption">Figure 5.7: Data Flow Diagram (DFD) Level 0 — Context Diagram</div>
</div>

<div class="figure-container">
  <img src="assets/fig_5_8_dfd_level_1.png" class="figure-img" alt="DFD Level 1">
  <div class="figure-caption">Figure 5.8: Data Flow Diagram (DFD) Level 1 — Process Decomposition</div>
</div>
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # CHAPTER 6: PROPOSED ALGORITHM IMPLEMENTATION
    # --------------------------------------------------------------------------
    html.append(f"""
<h1 class="chapter-title">CHAPTER 6<br>PROPOSED ALGORITHM IMPLEMENTATION</h1>
{format_academic_html(rd.CH6_TEXT)}

<div class="table-caption">Table 6.1: Master Dataset Attribute & Domain Specifications (Sample of 41 of 57 Attributes)</div>
<table class="academic-table">
  <tr>
    <th style="width: 25%;">Attribute Name</th>
    <th style="width: 25%;">Data Type & Constraint</th>
    <th style="width: 15%;">Sample Value</th>
    <th style="width: 35%;">Domain Definition & Operational Usage</th>
  </tr>
""")
    for attr, dtype, sample, desc in rd.TABLE_6_1_DATA:
        html.append(f"""  <tr>
    <td class="bold" style="font-family: monospace; font-size: 8.5pt;">{attr}</td>
    <td>{dtype}</td>
    <td style="font-family: monospace; font-size: 8.5pt;">{sample}</td>
    <td>{desc}</td>
  </tr>""")
    html.append("""</table>

<div class="figure-container">
  <img src="assets/fig_6_1_ml_pipeline_workflow.png" class="figure-img" alt="ML Pipeline Workflow">
  <div class="figure-caption">Figure 6.1: End-to-End Machine Learning & Feature Pipeline Workflow</div>
</div>

<div class="table-caption">Table 6.2: Preprocessing Transformation & Imputation Strategy</div>
<table class="academic-table">
  <tr>
    <th style="width: 25%;">Pipeline Stage</th>
    <th style="width: 25%;">Target Features</th>
    <th style="width: 25%;">Transformation Method</th>
    <th style="width: 25%;">Mathematical & Architectural Rationale</th>
  </tr>
""")
    for stage, targets, method, rationale in rd.TABLE_6_2_DATA:
        html.append(f"""  <tr>
    <td class="bold">{stage}</td>
    <td>{targets}</td>
    <td style="font-family: monospace; font-size: 8.5pt;">{method}</td>
    <td>{rationale}</td>
  </tr>""")
    html.append("""</table>

<div class="table-caption">Table 6.3: Machine Learning Model Hyperparameters & Architecture</div>
<table class="academic-table">
  <tr>
    <th style="width: 20%;">Model Architecture</th>
    <th style="width: 25%;">Model Family</th>
    <th style="width: 35%;">Tuned Hyperparameters</th>
    <th style="width: 20%;">Architectural Rationale</th>
  </tr>
""")
    for model, fam, params, rat in rd.TABLE_6_3_DATA:
        html.append(f"""  <tr>
    <td class="bold">{model}</td>
    <td>{fam}</td>
    <td style="font-family: monospace; font-size: 8.5pt;">{params}</td>
    <td>{rat}</td>
  </tr>""")
    html.append("""</table>

<div class="figure-container">
  <img src="assets/fig_6_2_risk_scoring_matrix.png" class="figure-img" alt="Risk Scoring Architecture">
  <div class="figure-caption">Figure 6.2: Multi-Factor Additive Risk Scoring Architecture & Tiers</div>
</div>

<div class="table-caption">Table 6.4: Multi-Factor Risk Scoring Point Allocation Matrix</div>
<table class="academic-table">
  <tr>
    <th style="width: 30%;">Risk Scoring Dimension</th>
    <th style="width: 20%;">Point Allocation Range</th>
    <th style="width: 50%;">Deterministic Mathematical Formulation & Triggers</th>
  </tr>
""")
    for dim, prange, rules in rd.TABLE_6_4_DATA:
        html.append(f"""  <tr>
    <td class="bold">{dim}</td>
    <td style="font-weight: bold; text-align: center;">{prange}</td>
    <td>{rules}</td>
  </tr>""")
    html.append("""</table>

<div class="figure-container">
  <img src="assets/fig_6_3_shap_waterfall.png" class="figure-img" alt="TreeSHAP Waterfall">
  <div class="figure-caption">Figure 6.3: Local TreeSHAP Feature Attribution Waterfall for Flagged Transaction</div>
</div>

<div class="table-caption">Table 6.5: Global Top-15 Feature Importance Attributions via TreeSHAP</div>
<table class="academic-table">
  <tr>
    <th style="width: 10%;">Rank</th>
    <th style="width: 35%;">Engineered Feature Name</th>
    <th style="width: 15%;">Mean |SHAP|</th>
    <th style="width: 15%;">Mean SHAP</th>
    <th style="width: 25%;">Operational Interpretation</th>
  </tr>
""")
    for rank, feat, m_abs, m_raw, interp in rd.TABLE_6_5_DATA:
        html.append(f"""  <tr>
    <td style="text-align: center; font-weight: bold;">{rank}</td>
    <td style="font-family: monospace; font-size: 8.5pt;">{feat}</td>
    <td style="text-align: right; font-weight: bold;">{m_abs}</td>
    <td style="text-align: right;">{m_raw}</td>
    <td>{interp}</td>
  </tr>""")
    html.append("""</table>

<div class="figure-container">
  <img src="assets/fig_6_4_mobile_otp_lifecycle.png" class="figure-img" alt="Mobile OTP Lifecycle">
  <div class="figure-caption">Figure 6.4: Pre-Authorization Mobile SMS OTP Verification Lifecycle</div>
</div>

<div class="table-caption">Table 6.6: Pre-Authorization Three-Tier Decision Matrix & Operational Directives</div>
<table class="academic-table">
  <tr>
    <th style="width: 18%;">Decision Tier</th>
    <th style="width: 20%;">Score Boundary</th>
    <th style="width: 32%;">Trigger Conditions</th>
    <th style="width: 30%;">Operational Directive</th>
  </tr>
""")
    for tier, bound, cond, act in rd.TABLE_6_6_DATA:
        html.append(f"""  <tr>
    <td class="bold">{tier}</td>
    <td style="text-align: center; font-weight: bold;">{bound}</td>
    <td>{cond}</td>
    <td>{act}</td>
  </tr>""")
    html.append("""</table>
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # CHAPTER 7: RESULTS AND DISCUSSION
    # --------------------------------------------------------------------------
    html.append(f"""
<h1 class="chapter-title">CHAPTER 7<br>RESULTS AND DISCUSSION</h1>
{format_academic_html(rd.CH7_TEXT)}

<div class="table-caption">Table 7.1: Comprehensive Machine Learning Model Performance Comparison (Test Split)</div>
<table class="academic-table">
  <tr>
    <th style="width: 22%;">Model Architecture</th>
    <th style="width: 9%;">Accuracy</th>
    <th style="width: 9%;">Precision</th>
    <th style="width: 9%;">Recall</th>
    <th style="width: 9%;">F1-Score</th>
    <th style="width: 9%;">F2-Score</th>
    <th style="width: 9%;">ROC-AUC</th>
    <th style="width: 9%;">PR-AUC</th>
    <th style="width: 7%;">FPR</th>
    <th style="width: 8%;">Status</th>
  </tr>
""")
    for mod, acc, prec, rec, f1, f2, roc, pr, fpr, fnr, notes in rd.TABLE_7_1_DATA:
        html.append(f"""  <tr>
    <td class="bold">{mod}</td>
    <td style="text-align: right;">{acc}</td>
    <td style="text-align: right;">{prec}</td>
    <td style="text-align: right; font-weight: bold;">{rec}</td>
    <td style="text-align: right;">{f1}</td>
    <td style="text-align: right;">{f2}</td>
    <td style="text-align: right; font-weight: bold;">{roc}</td>
    <td style="text-align: right; font-weight: bold;">{pr}</td>
    <td style="text-align: right;">{fpr}</td>
    <td style="text-align: right;">{fnr}</td>
  </tr>""")
    html.append("""</table>

<div class="figure-container">
  <img src="assets/fig_7_1_roc_pr_curves.png" class="figure-img" alt="ROC and PR Curves">
  <div class="figure-caption">Figure 7.1: ROC and Precision-Recall Curves on Test Split</div>
</div>

<div class="table-caption">Table 7.2: Confusion Matrix Metrics across Master Test & Active Validation Splits</div>
<table class="academic-table">
  <tr>
    <th style="width: 32%;">Evaluation Corpus Partition</th>
    <th style="width: 10%;">True Neg (TN)</th>
    <th style="width: 10%;">False Pos (FP)</th>
    <th style="width: 10%;">False Neg (FN)</th>
    <th style="width: 10%;">True Pos (TP)</th>
    <th style="width: 9%;">Precision</th>
    <th style="width: 9%;">Recall</th>
    <th style="width: 10%;">ROC-AUC</th>
  </tr>
""")
    for part, tn, fp, fn, tp, prec, rec, f1, acc in rd.TABLE_7_2_DATA:
        html.append(f"""  <tr>
    <td class="bold">{part}</td>
    <td style="text-align: right;">{tn}</td>
    <td style="text-align: right;">{fp}</td>
    <td style="text-align: right; font-weight: bold; color: green;">{fn}</td>
    <td style="text-align: right; font-weight: bold;">{tp}</td>
    <td style="text-align: right;">{prec}</td>
    <td style="text-align: right; font-weight: bold;">{rec}</td>
    <td style="text-align: right;">{acc}</td>
  </tr>""")
    html.append("""</table>

<div class="figure-container">
  <img src="assets/fig_7_2_confusion_matrices.png" class="figure-img" alt="Confusion Matrices">
  <div class="figure-caption">Figure 7.2: Confusion Matrix Heatmaps across Test & Active Validation Splits</div>
</div>

<div class="figure-container">
  <img src="assets/fig_7_3_global_shap_ranking.png" class="figure-img" alt="Global SHAP Ranking">
  <div class="figure-caption">Figure 7.3: Global Top-15 Feature Importance Ranking via TreeSHAP</div>
</div>

<div class="table-caption">Table 7.3: Sub-5 Millisecond Pre-Authorization Latency Breakdown Profile</div>
<table class="academic-table">
  <tr>
    <th style="width: 45%;">Pre-Authorization Architectural Phase</th>
    <th style="width: 20%;">Execution Latency</th>
    <th style="width: 35%;">Implementation Details</th>
  </tr>
""")
    for phase, lat, details in rd.TABLE_7_3_DATA:
        html.append(f"""  <tr>
    <td class="bold">{phase}</td>
    <td style="text-align: right; font-weight: bold;">{lat}</td>
    <td>{details}</td>
  </tr>""")
    html.append("""</table>

<div class="figure-container">
  <img src="assets/fig_7_4_latency_distribution.png" class="figure-img" alt="Latency Profile">
  <div class="figure-caption">Figure 7.4: Sub-5 Millisecond Pre-Authorization Latency Breakdown Profile</div>
</div>
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # CHAPTER 8: SYSTEM TESTING
    # --------------------------------------------------------------------------
    html.append(f"""
<h1 class="chapter-title">CHAPTER 8<br>SYSTEM TESTING</h1>
{format_academic_html(rd.CH8_TEXT)}

<div class="table-caption">Table 8.1: Formal Software Verification & Validation Test Report (30 Representative Cases)</div>
<table class="academic-table">
  <tr>
    <th style="width: 14%;">Test Case ID</th>
    <th style="width: 15%;">Module</th>
    <th style="width: 25%;">Input Condition / Test Stimulus</th>
    <th style="width: 23%;">Expected System Response</th>
    <th style="width: 15%;">Observed Result</th>
    <th style="width: 8%;">Status</th>
  </tr>
""")
    for tcid, mod, stimulus, expected, observed, stat in rd.TABLE_8_1_DATA:
        html.append(f"""  <tr>
    <td class="bold" style="font-family: monospace; font-size: 8.5pt;">{tcid}</td>
    <td>{mod}</td>
    <td>{stimulus}</td>
    <td>{expected}</td>
    <td>{observed}</td>
    <td style="text-align: center; font-weight: bold; color: #16a34a;">{stat}</td>
  </tr>""")
    html.append("""</table>
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # CHAPTER 9: CONCLUSION & FUTURE ENHANCEMENT
    # --------------------------------------------------------------------------
    html.append(f"""
<h1 class="chapter-title">CHAPTER 9<br>CONCLUSION AND FUTURE ENHANCEMENT</h1>
{format_academic_html(rd.CH9_TEXT)}
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # APPENDIX
    # --------------------------------------------------------------------------
    html.append(f"""
<h1 class="chapter-title">APPENDIX</h1>
<h2 class="section-title">A.1 SELECTED CORE SOURCE CODE EXCERPTS</h2>
<p>The following commented excerpts showcase the core object-oriented modules governing preprocessing, training, risk scoring, and autonomous pre-authorization orchestration in FraudLens AI:</p>

<pre class="code-block"><code># 1. PREPROCESSING & FEATURE ENGINEERING PIPELINE (ml/preprocessing/pipeline.py)
class FullFraudPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.feature_engineer = FraudFeatureEngineer()
        self.column_transformer = None

    def fit(self, X, y=None):
        df_eng = self.feature_engineer.fit_transform(X)
        num_cols, cat_cols = self._infer_feature_types(df_eng)
        
        num_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])
        cat_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ])
        self.column_transformer = ColumnTransformer([
            ("num", num_pipeline, num_cols),
            ("cat", cat_pipeline, cat_cols),
        ])
        self.column_transformer.fit(df_eng)
        return self

    def transform(self, X):
        df_eng = self.feature_engineer.transform(X)
        return self.column_transformer.transform(df_eng)
</code></pre>

<pre class="code-block"><code># 2. IMBALANCE-AWARE MODEL TRAINING ENGINE (ml/training/trainer.py)
def train_all_models(self, X_train: np.ndarray, y_train: np.ndarray):
    n_neg = int(np.sum(y_train == 0))
    n_pos = int(np.sum(y_train == 1))
    scale_pos_weight = float(n_neg / max(1, n_pos))

    # Tuned Regularized XGBoost with Imbalance Compensation
    xgb = XGBClassifier(
        n_estimators=250, max_depth=5, learning_rate=0.035,
        subsample=0.85, colsample_bytree=0.85, reg_alpha=0.1, reg_lambda=1.0,
        scale_pos_weight=scale_pos_weight, eval_metric="logloss", random_state=42
    )
    xgb.fit(X_train, y_train)
    self.models["xgboost"] = xgb
    return self.models
</code></pre>

<pre class="code-block"><code># 3. DETERMINISTIC MULTI-FACTOR RISK SCORING ENGINE (backend/app/services/risk_scoring_service.py)
def compute_risk_score(self, fraud_probability: float, transaction_data: dict) -> RiskScoreResult:
    factors = []
    total_score = 0.0
    p = max(0.0, min(1.0, float(fraud_probability)))
    
    # 1. Model Baseline Probability Signal (Max 60 pts)
    if p >= 0.70:
        model_pts = min(60.0, 45.0 + (p - 0.70) * 50.0)
    elif p >= 0.35:
        model_pts = 25.0 + (p - 0.35) * (20.0 / 0.35)
    else:
        model_pts = p * 80.0
    total_score += model_pts

    # 2. Amount Abnormality Signal vs 30-Day Customer Baseline (Max 25 pts)
    amount_ratio = amount / (avg_amount_30d + 1e-5)
    if amount_ratio >= 8.0:
        total_score += 18.0
    elif 0.5 <= amount_ratio <= 1.4:
        total_score -= 4.0 # Consistent spending rebate

    # 3. Velocity Bursts (Max 20 pts) & 4. Environmental Novelty (Max 25 pts)
    if vel_1h >= 5.0: total_score += 20.0
    if is_new_device: total_score += 8.0
    if is_unusual_loc: total_score += 8.0
    
    final_score = int(round(min(100.0, max(0.0, total_score))))
    if p >= 0.70 and final_score < 75: final_score = max(final_score, int(75.0 + p * 20.0))
    risk_level = self.classify_risk_level(final_score)
    return RiskScoreResult(risk_score=final_score, risk_level=risk_level, risk_factors=factors)
</code></pre>

<h2 class="section-title">A.2 APPLICATION INTERFACE ECOSYSTEM</h2>
<div class="figure-container">
  <img src="assets/fig_app_screenshots.png" class="figure-img" alt="Application Interface Ecosystem">
  <div class="figure-caption">Figure A.1: FraudLens AI Application Interface Ecosystem (Command Center, Payment Gateway, SMS OTP Modal, AI Dossier)</div>
</div>
<div class="page-break"></div>
""")

    # --------------------------------------------------------------------------
    # REFERENCES
    # --------------------------------------------------------------------------
    html.append("""
<h1 class="chapter-title">REFERENCES</h1>
<div style="font-size: 11pt; line-height: 1.6;">
""")
    for ref in rd.REFERENCES_DATA:
        html.append(f"""  <p style="margin-bottom: 10px; padding-left: 28px; text-indent: -28px;">{ref}</p>""")
    html.append("""
</div>
</body>
</html>
""")

    full_html = "\n".join(html)
    with open(html_output_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"Generated complete HTML report at: {html_output_path}")

if __name__ == "__main__":
    build_html()
