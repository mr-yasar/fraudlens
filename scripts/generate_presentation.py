"""
Generate the Official Academic 25-Slide PowerPoint Presentation for FraudLens AI.
Reference model: Senior Project PPT (Sona College of Technology, Academic Format).
Dimensions: 16:9 Widescreen (13.333" x 7.5").
Font: Times New Roman throughout.
Output: E:\\fraudinvestigation\\FraudLens_AI_Project_Presentation_25_Slides.pptx
"""

import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

OUTPUT_FILE = Path(r"E:\fraudinvestigation\FraudLens_AI_Project_Presentation_25_Slides.pptx")
ASSETS_DIR = Path(r"E:\fraudinvestigation\project_report\assets")
SCREENSHOTS_DIR = ASSETS_DIR / "screenshots"

# Color Palette (Matching Academic Senior PPT Style)
COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_BLACK = RGBColor(0, 0, 0)
COLOR_DARK_BLUE = RGBColor(0, 32, 96)       # Primary Title Accent
COLOR_NAVY = RGBColor(24, 76, 160)          # Department & Subtitle
COLOR_TABLE_HEADER = RGBColor(41, 105, 176) # Table Header Fill
COLOR_TABLE_ALT = RGBColor(240, 245, 255)   # Table Alt Row Fill
COLOR_CARD_BG = RGBColor(248, 250, 252)     # Card Background
COLOR_CARD_BORDER = RGBColor(203, 213, 225) # Card Border
COLOR_TEXT_MAIN = RGBColor(30, 30, 30)      # Body Text
COLOR_TEXT_MUTED = RGBColor(100, 100, 100)  # Footer Text
COLOR_ACCENT_GREEN = RGBColor(22, 101, 52)
COLOR_ACCENT_RED = RGBColor(153, 27, 27)
COLOR_ACCENT_AMBER = RGBColor(146, 64, 14)

FONT_PRIMARY = "Times New Roman"

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]  # Completely blank slide layout

    def add_academic_slide(title_text=None, slide_num=None):
        slide = prs.slides.add_slide(blank_layout)
        
        # Set solid white background
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = COLOR_WHITE

        # Add Title if provided
        if title_text:
            title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.55), Inches(11.733), Inches(0.85))
            tf = title_box.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            p.text = title_text
            p.alignment = PP_ALIGN.CENTER
            p.font.name = FONT_PRIMARY
            p.font.size = Pt(28)
            p.font.bold = True
            p.font.color.rgb = COLOR_BLACK

        # Add Academic Footer (Slides 2-25)
        if slide_num and slide_num > 1:
            footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(6.85), Inches(11.733), Inches(0.4))
            tf = footer_box.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            
            # Left: Date
            p_left = tf.paragraphs[0]
            p_left.text = "03-10-2026"
            p_left.font.name = FONT_PRIMARY
            p_left.font.size = Pt(10)
            p_left.font.color.rgb = COLOR_TEXT_MUTED
            p_left.alignment = PP_ALIGN.LEFT

            # Center text box for project title
            center_box = slide.shapes.add_textbox(Inches(2.5), Inches(6.85), Inches(8.333), Inches(0.4))
            tf_center = center_box.text_frame
            tf_center.margin_left = tf_center.margin_top = tf_center.margin_right = tf_center.margin_bottom = 0
            p_center = tf_center.paragraphs[0]
            p_center.text = "FraudLens AI — Explainable AI Financial Fraud & Risk Detection"
            p_center.font.name = FONT_PRIMARY
            p_center.font.size = Pt(10)
            p_center.font.color.rgb = COLOR_TEXT_MUTED
            p_center.alignment = PP_ALIGN.CENTER

            # Right text box for slide number
            right_box = slide.shapes.add_textbox(Inches(11.0), Inches(6.85), Inches(1.533), Inches(0.4))
            tf_right = right_box.text_frame
            tf_right.margin_left = tf_right.margin_top = tf_right.margin_right = tf_right.margin_bottom = 0
            p_right = tf_right.paragraphs[0]
            p_right.text = str(slide_num)
            p_right.font.name = FONT_PRIMARY
            p_right.font.size = Pt(10)
            p_right.font.color.rgb = COLOR_TEXT_MUTED
            p_right.alignment = PP_ALIGN.RIGHT

        return slide

    # =========================================================================
    # SLIDE 1: TITLE
    # =========================================================================
    slide1 = add_academic_slide(slide_num=1)
    
    # Institution Header
    inst_box = slide1.shapes.add_textbox(Inches(1.0), Inches(0.6), Inches(11.333), Inches(1.4))
    tf1 = inst_box.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = tf1.margin_right = tf1.margin_bottom = 0
    
    p = tf1.paragraphs[0]
    p.text = "SONA COLLEGE OF TECHNOLOGY"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_BLUE

    p2 = tf1.add_paragraph()
    p2.text = "(Autonomous)"
    p2.alignment = PP_ALIGN.CENTER
    p2.font.name = FONT_PRIMARY
    p2.font.size = Pt(22)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_DARK_BLUE

    p3 = tf1.add_paragraph()
    p3.text = "Department of Computer Science and Engineering"
    p3.alignment = PP_ALIGN.CENTER
    p3.font.name = FONT_PRIMARY
    p3.font.size = Pt(20)
    p3.font.bold = True
    p3.font.color.rgb = COLOR_NAVY
    p3.space_before = Pt(8)

    # Project Title
    title_box = slide1.shapes.add_textbox(Inches(1.0), Inches(2.35), Inches(11.333), Inches(1.8))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
    
    pt1 = tf_title.paragraphs[0]
    pt1.text = "FRAUDLENS AI: EXPLAINABLE AI-BASED FINANCIAL"
    pt1.alignment = PP_ALIGN.CENTER
    pt1.font.name = FONT_PRIMARY
    pt1.font.size = Pt(26)
    pt1.font.bold = True
    pt1.font.color.rgb = COLOR_BLACK

    pt2 = tf_title.add_paragraph()
    pt2.text = "FRAUD & RISK DETECTION SYSTEM"
    pt2.alignment = PP_ALIGN.CENTER
    pt2.font.name = FONT_PRIMARY
    pt2.font.size = Pt(26)
    pt2.font.bold = True
    pt2.font.color.rgb = COLOR_BLACK

    pt3 = tf_title.add_paragraph()
    pt3.text = "PROJECT PRESENTATION"
    pt3.alignment = PP_ALIGN.CENTER
    pt3.font.name = FONT_PRIMARY
    pt3.font.size = Pt(17)
    pt3.font.bold = True
    pt3.font.color.rgb = COLOR_BLACK
    pt3.space_before = Pt(14)

    # Student & Guide Table (Matching senior slide 1)
    rows, cols = 2, 4
    left = Inches(1.0)
    top = Inches(4.75)
    width = Inches(11.333)
    height = Inches(1.4)
    table_shape = slide1.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table
    table.columns[0].width = Inches(2.833)
    table.columns[1].width = Inches(2.833)
    table.columns[2].width = Inches(2.833)
    table.columns[3].width = Inches(2.834)

    headers = ["STUDENT NAME", "REGISTER NUMBER", "PROJECT GUIDE", "DESIGNATION"]
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_TABLE_HEADER
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.alignment = PP_ALIGN.CENTER
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE

    row_data = ["Mohamed Yasar M", "211419104035", "Dr. R. Senthil Kumar", "Professor / CSE"]
    for i, val in enumerate(row_data):
        cell = table.cell(1, i)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_TABLE_ALT
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.text = val
        p.alignment = PP_ALIGN.CENTER
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = COLOR_BLACK

    # Slide 1 page number on bottom right
    s1_num = slide1.shapes.add_textbox(Inches(11.5), Inches(6.85), Inches(1.0), Inches(0.4))
    p_num = s1_num.text_frame.paragraphs[0]
    p_num.text = "1"
    p_num.font.name = FONT_PRIMARY
    p_num.font.size = Pt(10)
    p_num.font.color.rgb = COLOR_TEXT_MUTED
    p_num.alignment = PP_ALIGN.RIGHT

    # =========================================================================
    # SLIDE 2: ABSTRACT
    # =========================================================================
    slide2 = add_academic_slide("ABSTRACT", slide_num=2)
    box = slide2.shapes.add_textbox(Inches(1.5), Inches(1.8), Inches(10.333), Inches(4.5))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = (
        "In the contemporary financial digital economy, modern high-speed payment systems like UPI, "
        "cards, and real-time bank transfers clear transactions in sub-second intervals. Concurrently, "
        "financial fraud has become significantly more complex, making manual fraud inspection and static "
        "rule filters increasingly inadequate. FraudLens AI resolves this industry challenge by introducing "
        "an end-to-end, Explainable Artificial Intelligence (XAI) financial fraud and risk detection platform."
    )
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(19)
    p.font.color.rgb = COLOR_TEXT_MAIN
    p.line_spacing = 1.35
    p.space_after = Pt(16)

    p2 = tf.add_paragraph()
    p2.text = (
        "The system evaluates transactions using machine learning models (XGBoost, Random Forest, Logistic "
        "Regression) to predict fraud probability, while independently computing an operational 0–100 multi-factor "
        "risk score. Transactions are dynamically classified into Low, Medium, and High risk tiers, enabling "
        "sub-5ms frictionless clearance, step-up smartphone SMS OTP verification, and hard blocking. Exact game-theoretic "
        "feature attributions via TreeSHAP provide complete transparency, satisfying regulatory explainability directives "
        "while empowering forensic analysts through integrated investigation dashboards."
    )
    p2.font.name = FONT_PRIMARY
    p2.font.size = Pt(19)
    p2.font.color.rgb = COLOR_TEXT_MAIN
    p2.line_spacing = 1.35

    # =========================================================================
    # SLIDE 3: PROBLEM STATEMENT
    # =========================================================================
    slide3 = add_academic_slide("PROBLEM STATEMENT", slide_num=3)
    box = slide3.shapes.add_textbox(Inches(1.3), Inches(1.8), Inches(10.733), Inches(4.7))
    tf = box.text_frame
    tf.word_wrap = True

    problems = [
        "Exponential Growth in Real-Time Payment Volumes: Immediate clearing settlement systems process thousands of transactions per second, reducing authorization decision windows to under 50 milliseconds.",
        "Failure of Manual Inspection: Human fraud analysts in Security Operations Centers cannot manually inspect high transaction volumes, leading to massive backlogs and average case resolution times exceeding 30 minutes.",
        "Rigidity of Traditional Rule-Based Engines: Legacy systems rely on static threshold rules that miss non-linear, multi-hop fraud vectors, while generating up to 80% false alarms that cause legitimate customer drop-off.",
        "The 'Black-Box' Machine Learning Dilemma: Advanced statistical ML models output solitary probability values without causal reasoning, violating regulatory compliance mandates such as GDPR Article 22 and RBI directives.",
        "Conflation of Probability and Monetary Risk: Conventional architectures treat statistical anomaly probability as synonymous with operational financial exposure, lacking granular multi-factor risk prioritization."
    ]

    for i, prob in enumerate(problems):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"•   {prob}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(18)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.line_spacing = 1.25
        p.space_after = Pt(14)

    # =========================================================================
    # SLIDE 4: OBJECTIVES
    # =========================================================================
    slide4 = add_academic_slide("OBJECTIVES", slide_num=4)
    box = slide4.shapes.add_textbox(Inches(1.3), Inches(1.8), Inches(10.733), Inches(4.7))
    tf = box.text_frame
    tf.word_wrap = True

    objectives = [
        "Formulate a Robust Feature Pipeline: Build an automated, leakage-free 11-step preprocessing pipeline on a master corpus of 20,000 synthetic transaction records spanning 57 behavioral, temporal, and spatial features across 30 merchants.",
        "Train and Benchmark Machine Learning Models: Evaluate regularized Logistic Regression, a 300-tree Random Forest, and extreme gradient boosted trees (XGBoost with scale_pos_weight=17.3), achieving 100.0% fraud recall.",
        "Decouple Probability and Risk Scoring: Strictly separate model-derived continuous Fraud Probability from an independent Deterministic Multi-Factor Risk Score (0–100) based on spending deviations, velocity bursts, and novelty signals.",
        "Implement Actionable Risk Tiering: Enforce a sub-5ms pre-authorization gatekeeper across three discrete tiers: Low Risk (0–30: ALLOW), Medium Risk (31–70: REVIEW with SMS OTP challenge), and High Risk (71–100: BLOCK).",
        "Deliver Game-Theoretic Explainability: Embed TreeSHAP into the inference engine to compute exact local feature attributions within 1.1ms, rendering interactive waterfall charts and evidence-grounded forensic narratives.",
        "Provide Integrated Investigation & Auditing: Develop an autonomous forensic case docket, AI investigation copilot, and immutable cryptographic audit ledger to streamline analyst workflows and compliance reporting."
    ]

    for i, obj in enumerate(objectives):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"•   {obj}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(17)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.line_spacing = 1.2
        p.space_after = Pt(12)

    # =========================================================================
    # SLIDE 5: EXISTING SYSTEM
    # =========================================================================
    slide5 = add_academic_slide("EXISTING SYSTEM", slide_num=5)
    box = slide5.shapes.add_textbox(Inches(1.5), Inches(1.8), Inches(10.333), Inches(4.5))
    tf = box.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = (
        "Conventional financial fraud prevention infrastructures currently deployed across banking networks "
        "are predominantly bifurcated into two separate operational mechanisms: static deterministic rule-based "
        "expert systems and monolithic black-box machine learning engines."
    )
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(19)
    p.font.color.rgb = COLOR_TEXT_MAIN
    p.line_spacing = 1.35
    p.space_after = Pt(16)

    p2 = tf.add_paragraph()
    p2.text = (
        "Static heuristic rule engines apply flat threshold filters (such as rejecting transactions exceeding "
        "a fixed amount or flagging overseas card transactions). More recently, banks have incorporated commercial "
        "scoring models that compute binary classification outputs. However, these systems operate in complete "
        "isolation from post-authorization forensic review tools, provide no mathematical feature attribution, "
        "and enforce rigid binary decisions (blindly pass or hard block) without adaptive customer verification."
    )
    p2.font.name = FONT_PRIMARY
    p2.font.size = Pt(19)
    p2.font.color.rgb = COLOR_TEXT_MAIN
    p2.line_spacing = 1.35

    # =========================================================================
    # SLIDE 6: LIMITATIONS OF EXISTING SYSTEM
    # =========================================================================
    slide6 = add_academic_slide("LIMITATIONS OF EXISTING SYSTEM", slide_num=6)
    box = slide6.shapes.add_textbox(Inches(1.3), Inches(1.8), Inches(10.733), Inches(4.7))
    tf = box.text_frame
    tf.word_wrap = True

    limitations = [
        "High False Positive Rate: Heuristic rules lack individualized behavioral context, incorrectly declining up to 80% of legitimate consumer transactions during travel or festive shopping.",
        "Total Lack of Causal Explainability: Black-box ML models return opaque probability scores without articulating which features drove the risk, violating GDPR Article 22 Right to Explanation.",
        "Acute Rule Inelasticity & Bloat: Static rules cannot adapt dynamically to evolving account takeover (ATO) attacks, while decades of accumulating conflicting rules severely degrade gateway processing speed.",
        "Conflation of Statistical Probability and Risk: A ₹100 payment with novelty is flagged identically to a ₹2,00,000 capital exfiltration, because probability is improperly equated with financial loss exposure.",
        "Severe Operational Investigation Latency: Human investigators must manually collect logs across disparate ledgers, spending 30 to 45 minutes to adjudicate a single flagged transaction.",
        "Rigid Binary Decisioning: Lacking intermediate step-up verification, borderline transactions are either hard-blocked (causing customer friction) or blindly approved (causing fraud losses)."
    ]

    for i, lim in enumerate(limitations):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"•   {lim}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(17.5)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.line_spacing = 1.25
        p.space_after = Pt(12)

    # =========================================================================
    # SLIDE 7: PROPOSED SYSTEM
    # =========================================================================
    slide7 = add_academic_slide("PROPOSED SYSTEM", slide_num=7)
    
    # Text intro
    intro_box = slide7.shapes.add_textbox(Inches(1.2), Inches(1.5), Inches(10.933), Inches(1.0))
    tf_intro = intro_box.text_frame
    tf_intro.word_wrap = True
    p = tf_intro.paragraphs[0]
    p.text = (
        "FraudLens AI introduces an integrated, multi-tier software architecture that harmonizes high-accuracy "
        "gradient-boosted machine learning, deterministic multi-factor risk assessment, real-time TreeSHAP explainability, "
        "sub-5ms gatekeeper decisioning, and autonomous forensic case management into a cohesive platform."
    )
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(17.5)
    p.font.color.rgb = COLOR_TEXT_MAIN
    p.line_spacing = 1.25

    # Visual Flow Diagram using styled rounded boxes
    steps = [
        ("Transaction Input", "Client payment payload\n(Amount, Merchant, Device)"),
        ("Data Validation", "11-step schema checks &\ntarget leakage prevention"),
        ("Preprocessing & Eng.", "StandardScaler, OHE, &\n26 derived behavioral ratios"),
        ("ML Inference", "XGBoost Champion model\n(Fraud Probability: 0.0 - 1.0)"),
        ("Risk Scoring", "Deterministic 0-100 score\n(ML, Velocity, Deviation, Env)"),
        ("Risk Tiering", "LOW (0-30) | MED (31-70)\nHIGH (71-100)"),
        ("TreeSHAP XAI", "Game-theoretic local &\nglobal feature attribution"),
        ("Gatekeeper & Review", "ALLOW / REVIEW / BLOCK\nStep-Up SMS OTP Challenge"),
        ("Investigation Hub", "Forensic case docket &\nLive Command Radar"),
    ]

    start_top = Inches(2.7)
    card_w = Inches(3.4)
    card_h = Inches(1.15)
    
    # 3x3 Grid of Pipeline Steps
    coords = [
        (Inches(1.2), Inches(2.7)),
        (Inches(4.966), Inches(2.7)),
        (Inches(8.733), Inches(2.7)),
        (Inches(1.2), Inches(4.05)),
        (Inches(4.966), Inches(4.05)),
        (Inches(8.733), Inches(4.05)),
        (Inches(1.2), Inches(5.4)),
        (Inches(4.966), Inches(5.4)),
        (Inches(8.733), Inches(5.4)),
    ]

    for idx, (title, desc) in enumerate(steps):
        cx, cy = coords[idx]
        shape = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, cy, card_w, card_h)
        shape.fill.solid()
        shape.fill.fore_color.rgb = COLOR_CARD_BG
        shape.line.color.rgb = COLOR_TABLE_HEADER
        shape.line.width = Pt(1.5)

        tf_card = shape.text_frame
        tf_card.word_wrap = True
        tf_card.margin_left = tf_card.margin_right = Inches(0.1)
        tf_card.margin_top = Inches(0.1)
        
        p = tf_card.paragraphs[0]
        p.text = f"{idx+1}. {title}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = COLOR_DARK_BLUE
        p.alignment = PP_ALIGN.CENTER

        p_desc = tf_card.add_paragraph()
        p_desc.text = desc
        p_desc.font.name = FONT_PRIMARY
        p_desc.font.size = Pt(11.5)
        p_desc.font.color.rgb = COLOR_TEXT_MAIN
        p_desc.alignment = PP_ALIGN.CENTER
        p_desc.space_before = Pt(3)

    # =========================================================================
    # SLIDE 8: ADVANTAGES OF PROPOSED SYSTEM
    # =========================================================================
    slide8 = add_academic_slide("ADVANTAGES OF PROPOSED SYSTEM", slide_num=8)
    box = slide8.shapes.add_textbox(Inches(1.3), Inches(1.8), Inches(10.733), Inches(4.7))
    tf = box.text_frame
    tf.word_wrap = True

    advantages = [
        "Sub-5ms Real-Time Decisioning: Executes complete end-to-end evaluation—including ML scoring, TreeSHAP attribution, and database commit—in an average of 4.80 milliseconds, well within the 50ms banking SLA.",
        "Calibrated Multi-Factor Risk Scoring: Prevents catastrophic false declines by evaluating historical spending deviations, velocity bursts, and hardware novelty independently of statistical probability.",
        "Regulatory Explainability Compliance: Implements exact game-theoretic TreeSHAP feature attributions that satisfy European Union GDPR Article 22 and Reserve Bank of India digital payment security directives.",
        "Adaptive Step-Up SMS OTP Authentication: Features an interactive smartphone push challenge for review-tier transactions, allowing genuine cardholders to self-authorize without account freezing.",
        "Autonomous Forensic Dossier Synthesis: Streamlines enterprise Security Operations Center (SOC) triage from 35 minutes to under 3 minutes via automated kill-chain topologies and regulatory SAR drafts.",
        "Zero-Data-Leakage Architectural Rigor: Employs strict target leakage purging, role-based access control (RBAC), and an immutable cryptographic audit ledger to ensure systemic data integrity."
    ]

    for i, adv in enumerate(advantages):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"•   {adv}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(17.5)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.line_spacing = 1.25
        p.space_after = Pt(12)

    # =========================================================================
    # SLIDE 9: LITERATURE STUDY – I
    # =========================================================================
    slide9 = add_academic_slide("LITERATURE STUDY – I", slide_num=9)
    
    rows, cols = 4, 3
    t_shape = slide9.shapes.add_table(rows, cols, Inches(1.0), Inches(1.7), Inches(11.333), Inches(4.7))
    tbl = t_shape.table
    tbl.columns[0].width = Inches(1.0)
    tbl.columns[1].width = Inches(4.333)
    tbl.columns[2].width = Inches(6.0)

    t_headers = ["S.No", "Paper Title & Author Details", "Key Findings & Observations"]
    for i, h in enumerate(t_headers):
        cell = tbl.cell(0, i)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_TABLE_HEADER
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.alignment = PP_ALIGN.CENTER
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE

    lit1_data = [
        ("1", 
         "Statistical Fraud Detection: A Review\n"
         "R. J. Bolton and D. J. Hand (2002)\n"
         "Statistical Science, Vol. 17, No. 3",
         "Introduced Breakpoint and Peer Group Analysis to detect behavioral shifts in credit card accounts without labeled fraud data. Found that unsupervised methods suffer from high false alarm rates due to natural spending volatility, motivating FraudLens AI's supervised multi-factor scoring approach."),
        
        ("2", 
         "A Comprehensive Survey of Data Mining-Based Fraud Detection Research\n"
         "C. Phua, V. Lee, K. Smith, and R. Gayler (2010)\n"
         "arXiv:1009.6119",
         "Surveyed supervised data mining algorithms across retail banking. Established that acute class imbalance (< 1% fraud prevalence) is the single greatest impediment to classifier convergence, directly informing FraudLens AI's scale_pos_weight calibration and balanced bagging strategy."),
        
        ("3", 
         "Credit Card Fraud Detection: A Realistic Modeling & Novel Learning Strategy\n"
         "A. Dal Pozzolo, G. Boracchi, O. Caelen, et al. (2018)\n"
         "IEEE Transactions on Neural Networks, Vol. 29",
         "Formalized verification latency and non-stationary concept drift in streaming card transactions. Proved that ensemble combinations of bagging and boosting stabilize decision boundaries over time, guiding the stacking meta-ensemble architecture in FraudLens AI.")
    ]

    for row_idx, data in enumerate(lit1_data, start=1):
        for col_idx, text in enumerate(data):
            cell = tbl.cell(row_idx, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_TABLE_ALT if row_idx % 2 == 1 else COLOR_WHITE
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.text = text
            p.alignment = PP_ALIGN.CENTER if col_idx == 0 else PP_ALIGN.LEFT
            p.font.name = FONT_PRIMARY
            p.font.size = Pt(13)
            p.font.color.rgb = COLOR_TEXT_MAIN
            p.line_spacing = 1.15

    # =========================================================================
    # SLIDE 10: LITERATURE STUDY – II
    # =========================================================================
    slide10 = add_academic_slide("LITERATURE STUDY – II", slide_num=10)
    
    rows, cols = 3, 3
    t_shape = slide10.shapes.add_table(rows, cols, Inches(1.0), Inches(1.6), Inches(11.333), Inches(2.9))
    tbl = t_shape.table
    tbl.columns[0].width = Inches(1.0)
    tbl.columns[1].width = Inches(4.333)
    tbl.columns[2].width = Inches(6.0)

    for i, h in enumerate(t_headers):
        cell = tbl.cell(0, i)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_TABLE_HEADER
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.alignment = PP_ALIGN.CENTER
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE

    lit2_data = [
        ("4", 
         "XGBoost: A Scalable Tree Boosting System\n"
         "T. Chen and C. Guestrin (2016)\n"
         "ACM SIGKDD International Conference",
         "Demonstrated that extreme gradient boosted trees optimizing second-order Taylor approximations outperform deep neural networks on tabular financial data, while embedded scale_pos_weight parameters effectively counter extreme class imbalance."),
        
        ("5", 
         "From Local Explanations to Global Understanding with Explainable AI for Trees\n"
         "S. M. Lundberg, G. G. Erion, et al. (2020)\n"
         "Nature Machine Intelligence, Vol. 2",
         "Formulated TreeSHAP, reducing exact Shapley attribution computation complexity from exponential O(TL2^M) to polynomial time O(TLD^2), rendering real-time game-theoretic feature attribution feasible for low-latency payment processing.")
    ]

    for row_idx, data in enumerate(lit2_data, start=1):
        for col_idx, text in enumerate(data):
            cell = tbl.cell(row_idx, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_TABLE_ALT if row_idx % 2 == 1 else COLOR_WHITE
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.text = text
            p.alignment = PP_ALIGN.CENTER if col_idx == 0 else PP_ALIGN.LEFT
            p.font.name = FONT_PRIMARY
            p.font.size = Pt(12.5)
            p.font.color.rgb = COLOR_TEXT_MAIN
            p.line_spacing = 1.15

    # Research Gap & Motivation Box
    gap_box = slide10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(4.75), Inches(11.333), Inches(1.8))
    gap_box.fill.solid()
    gap_box.fill.fore_color.rgb = RGBColor(254, 249, 195) # Soft gold tint
    gap_box.line.color.rgb = RGBColor(202, 138, 4)
    gap_box.line.width = Pt(1.5)
    
    tf_gap = gap_box.text_frame
    tf_gap.word_wrap = True
    tf_gap.margin_left = tf_gap.margin_right = Inches(0.2)
    tf_gap.margin_top = Inches(0.12)

    p_gap_title = tf_gap.paragraphs[0]
    p_gap_title.text = "IDENTIFIED RESEARCH GAP & MOTIVATION:"
    p_gap_title.font.name = FONT_PRIMARY
    p_gap_title.font.size = Pt(14)
    p_gap_title.font.bold = True
    p_gap_title.font.color.rgb = COLOR_ACCENT_AMBER

    p_gap1 = tf_gap.add_paragraph()
    p_gap1.text = "•   Research Gap: Extant literature isolates ML classification from operational risk scoring, treats SHAP as an offline diagnostic post-mortem, and lacks integrated adaptive step-up verification and automated forensic case management."
    p_gap1.font.name = FONT_PRIMARY
    p_gap1.font.size = Pt(12.5)
    p_gap1.font.color.rgb = COLOR_TEXT_MAIN
    p_gap1.line_spacing = 1.15
    p_gap1.space_before = Pt(3)

    p_gap2 = tf_gap.add_paragraph()
    p_gap2.text = "•   FraudLens AI Contribution: Unifies high-performance XGBoost inference + decoupled 0–100 multi-factor risk scoring + sub-4ms TreeSHAP explainability + adaptive smartphone SMS OTP + GenAI case dossier synthesis into a single operational platform."
    p_gap2.font.name = FONT_PRIMARY
    p_gap2.font.size = Pt(12.5)
    p_gap2.font.color.rgb = COLOR_TEXT_MAIN
    p_gap2.line_spacing = 1.15
    p_gap2.space_before = Pt(3)

    # =========================================================================
    # SLIDE 11: SYSTEM SPECIFICATION
    # =========================================================================
    slide11 = add_academic_slide("SYSTEM SPECIFICATION", slide_num=11)
    
    # Left Column: Hardware Requirements
    hw_shape = slide11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.7), Inches(5.45), Inches(4.8))
    hw_shape.fill.solid()
    hw_shape.fill.fore_color.rgb = COLOR_CARD_BG
    hw_shape.line.color.rgb = COLOR_TABLE_HEADER
    hw_shape.line.width = Pt(1.5)

    tf_hw = hw_shape.text_frame
    tf_hw.word_wrap = True
    tf_hw.margin_left = tf_hw.margin_right = Inches(0.25)
    tf_hw.margin_top = Inches(0.2)

    p_hw = tf_hw.paragraphs[0]
    p_hw.text = "HARDWARE REQUIREMENTS"
    p_hw.font.name = FONT_PRIMARY
    p_hw.font.size = Pt(18)
    p_hw.font.bold = True
    p_hw.font.color.rgb = COLOR_DARK_BLUE
    p_hw.alignment = PP_ALIGN.CENTER
    p_hw.space_after = Pt(12)

    hw_items = [
        ("Processor (CPU):", "Intel Core i5 / AMD Ryzen 5 or higher (Recommended: 8-Core Intel i7 / Xeon)"),
        ("System Memory (RAM):", "8 GB DDR4 minimum (16 GB DDR4/DDR5 recommended for ML model training)"),
        ("Storage Drive:", "256 GB SATA SSD minimum (512 GB NVMe M.2 SSD recommended)"),
        ("Network Interface:", "100 Mbps Ethernet / Wi-Fi broadband network connectivity"),
        ("Display Resolution:", "1366 × 768 minimum (1920 × 1080 Full HD recommended for Command Center)")
    ]

    for lbl, val in hw_items:
        p = tf_hw.add_paragraph()
        p.text = f"•   {lbl}  {val}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(14)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.line_spacing = 1.2
        p.space_after = Pt(10)

    # Right Column: Software Requirements
    sw_shape = slide11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.883), Inches(1.7), Inches(5.45), Inches(4.8))
    sw_shape.fill.solid()
    sw_shape.fill.fore_color.rgb = COLOR_CARD_BG
    sw_shape.line.color.rgb = COLOR_TABLE_HEADER
    sw_shape.line.width = Pt(1.5)

    tf_sw = sw_shape.text_frame
    tf_sw.word_wrap = True
    tf_sw.margin_left = tf_sw.margin_right = Inches(0.25)
    tf_sw.margin_top = Inches(0.2)

    p_sw = tf_sw.paragraphs[0]
    p_sw.text = "SOFTWARE REQUIREMENTS"
    p_sw.font.name = FONT_PRIMARY
    p_sw.font.size = Pt(18)
    p_sw.font.bold = True
    p_sw.font.color.rgb = COLOR_DARK_BLUE
    p_sw.alignment = PP_ALIGN.CENTER
    p_sw.space_after = Pt(12)

    sw_items = [
        ("Operating System:", "Microsoft Windows 10/11 64-bit or Ubuntu 22.04 LTS Linux"),
        ("Programming Language:", "Python 3.11+ (Backend / ML) & Node.js 20+ (Frontend)"),
        ("Backend Web Framework:", "FastAPI v0.115+ (Starlette + Pydantic v2) with Uvicorn ASGI"),
        ("Machine Learning Core:", "Scikit-Learn v1.5+, XGBoost v2.1+, Joblib v1.4+"),
        ("Explainable AI (XAI):", "SHAP v0.46+ (TreeSHAP & LinearSHAP algorithms)"),
        ("Database & ORM:", "SQLite 3 (WAL Mode enabled) & SQLAlchemy 2.0+ ORM"),
        ("Frontend Technologies:", "React 18 SPA, Vite, Vanilla CSS, Lucide Icons, Recharts")
    ]

    for lbl, val in sw_items:
        p = tf_sw.add_paragraph()
        p.text = f"•   {lbl}  {val}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(13.5)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.line_spacing = 1.15
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 12: SYSTEM DESIGN
    # =========================================================================
    slide12 = add_academic_slide("SYSTEM DESIGN", slide_num=12)
    
    # Embed Architecture Figure
    fig_arch = ASSETS_DIR / "fig_5_1_system_architecture.png"
    if fig_arch.exists():
        slide12.shapes.add_picture(str(fig_arch), Inches(0.8), Inches(1.5), width=Inches(7.2))
    
    # Right Side Description Box
    box_desc = slide12.shapes.add_textbox(Inches(8.2), Inches(1.5), Inches(4.333), Inches(5.0))
    tf_arch = box_desc.text_frame
    tf_arch.word_wrap = True

    p = tf_arch.paragraphs[0]
    p.text = "MULTI-TIER ARCHITECTURE:"
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_BLUE
    p.space_after = Pt(10)

    arch_tiers = [
        ("Presentation Tier:", "React 18 SPA offering Pre-Auth Payment Gateway, Command Center Radar, Case Docket Hub, and Model Lab."),
        ("API Gateway & Security:", "FastAPI asynchronous gateway with OAuth2/JWT token verification, RBAC scopes, idempotency checks, and WebSocket streams."),
        ("Pre-Auth & Orchestration:", "RiskDecisionOrchestrator coordinating balance verification, customer profiling, and 3-tier gatekeeper dispatch."),
        ("ML & Explainability Core:", "Standardized FullFraudPreprocessor, tuned XGBoost inference, and sub-4ms TreeSHAP feature attribution."),
        ("Persistence & GenAI Fabric:", "SQLite 3 (20 relational tables), immutable cryptographic audit ledger, and AI Forensic Copilot.")
    ]

    for title, desc in arch_tiers:
        p = tf_arch.add_paragraph()
        p.text = f"•   {title} {desc}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(13)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.line_spacing = 1.15
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 13: SYSTEM WORKFLOW
    # =========================================================================
    slide13 = add_academic_slide("SYSTEM WORKFLOW", slide_num=13)
    
    fig_flow = ASSETS_DIR / "fig_5_4_flow_diagram.png"
    if fig_flow.exists():
        slide13.shapes.add_picture(str(fig_flow), Inches(0.8), Inches(1.5), width=Inches(7.2))

    box_flow = slide13.shapes.add_textbox(Inches(8.2), Inches(1.5), Inches(4.333), Inches(5.0))
    tf_wf = box_flow.text_frame
    tf_wf.word_wrap = True

    p = tf_wf.paragraphs[0]
    p.text = "END-TO-END FLOW SEQUENCE:"
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_BLUE
    p.space_after = Pt(10)

    wf_steps = [
        ("1. Transaction Initiation:", "Client submits payment intent (Amount, Merchant ID, Device, Channel)."),
        ("2. Idempotency & Balance Check:", "Validates SHA-256 request fingerprint and checks simulated account liquidity."),
        ("3. Behavioral Preprocessing:", "Derives 30-day spending ratios, velocity counters, and cyclical temporal projections."),
        ("4. ML Inference & TreeSHAP:", "XGBoost predicts continuous fraud probability; TreeSHAP calculates exact attributions."),
        ("5. Deterministic Risk Scoring:", "Additive scoring evaluates ML signal, spending surge, velocity, and novelty (0-100)."),
        ("6. Decision Gatekeeper:", "Dispatches ALLOW (0-30: auto-clear), REVIEW (31-70: hold), or BLOCK (71-100: halt)."),
        ("7. Step-Up OTP & Settlement:", "SMS OTP verification releases funds; failures trigger account lock and case creation.")
    ]

    for title, desc in wf_steps:
        p = tf_wf.add_paragraph()
        p.text = f"•   {title} {desc}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(12.5)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.line_spacing = 1.15
        p.space_after = Pt(6)

    # =========================================================================
    # SLIDE 14: MODULE DESCRIPTION – I
    # =========================================================================
    slide14 = add_academic_slide("MODULE DESCRIPTION – I", slide_num=14)
    
    # 2-column layout (Modules 1-4)
    mod_col1 = slide14.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.6), Inches(5.45), Inches(5.0))
    mod_col1.fill.solid()
    mod_col1.fill.fore_color.rgb = COLOR_CARD_BG
    mod_col1.line.color.rgb = COLOR_TABLE_HEADER
    mod_col1.line.width = Pt(1.5)
    
    tf_m1 = mod_col1.text_frame
    tf_m1.word_wrap = True
    tf_m1.margin_left = tf_m1.margin_right = Inches(0.2)
    tf_m1.margin_top = Inches(0.15)

    p = tf_m1.paragraphs[0]
    p.text = "MODULE 1 — DATASET & VALIDATION"
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_BLUE

    m1_points = [
        "Dataset Specification: 20,000 synthetic transaction records spanning 57 attributes across 30 commercial merchants in Tamil Nadu and Karnataka.",
        "Prevalence & Target: Models genuine retail distribution with 5.46% fraud prevalence (1:17.3 class imbalance) with binary target is_fraud.",
        "11-Step Data Integrity Audit: Enforces automated schema checking, null checks, outlier auditing, and strict purging of target leakage proxies."
    ]
    for pt in m1_points:
        p = tf_m1.add_paragraph()
        p.text = f"•   {pt}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(3)

    p_m2 = tf_m1.add_paragraph()
    p_m2.text = "MODULE 2 — DATA PREPROCESSING"
    p_m2.font.name = FONT_PRIMARY
    p_m2.font.size = Pt(16)
    p_m2.font.bold = True
    p_m2.font.color.rgb = COLOR_DARK_BLUE
    p_m2.space_before = Pt(10)

    m2_points = [
        "Imputation: Median imputation for numerical fields (robust against monetary outliers); constant 'unknown' for categorical features.",
        "Scaling & Encoding: StandardScaler centers 26 numerical variables; OneHotEncoder projects 4 categoricals into 37 binary dummy indicators.",
        "Behavioral Feature Engineering: Derives 26 interaction signals: amount-to-average spending ratios, velocity bursts, and trigonometric cyclical hours."
    ]
    for pt in m2_points:
        p = tf_m1.add_paragraph()
        p.text = f"•   {pt}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(3)

    # Column 2: Modules 3 & 4
    mod_col2 = slide14.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.883), Inches(1.6), Inches(5.45), Inches(5.0))
    mod_col2.fill.solid()
    mod_col2.fill.fore_color.rgb = COLOR_CARD_BG
    mod_col2.line.color.rgb = COLOR_TABLE_HEADER
    mod_col2.line.width = Pt(1.5)

    tf_m2 = mod_col2.text_frame
    tf_m2.word_wrap = True
    tf_m2.margin_left = tf_m2.margin_right = Inches(0.2)
    tf_m2.margin_top = Inches(0.15)

    p_m3 = tf_m2.paragraphs[0]
    p_m3.text = "MODULE 3 — MODEL TRAINING & COMPARISON"
    p_m3.font.name = FONT_PRIMARY
    p_m3.font.size = Pt(16)
    p_m3.font.bold = True
    p_m3.font.color.rgb = COLOR_DARK_BLUE

    m3_points = [
        "Supervised ML Tournament: Benchmarks regularized Logistic Regression, 300-tree tuned Random Forest, and extreme gradient boosting (XGBoost).",
        "Class Imbalance Calibration: Inverts majority class dominance via scale_pos_weight=17.3 in XGBoost and balanced class weights in RF.",
        "Model Comparison: XGBoost and Stacking Ensemble achieve 100.0% Test Recall and 1.000 ROC-AUC, ensuring zero undetected fraud vectors."
    ]
    for pt in m3_points:
        p = tf_m2.add_paragraph()
        p.text = f"•   {pt}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(3)

    p_m4 = tf_m2.add_paragraph()
    p_m4.text = "MODULE 4 — FRAUD PREDICTION"
    p_m4.font.name = FONT_PRIMARY
    p_m4.font.size = Pt(16)
    p_m4.font.bold = True
    p_m4.font.color.rgb = COLOR_DARK_BLUE
    p_m4.space_before = Pt(10)

    m4_points = [
        "Pre-Warmed Inference: Serialized champion models (.joblib) loaded into memory at startup to eliminate cold-start latency.",
        "Sub-2ms Model Inference: Generates continuous Fraud Probability (0.0 to 1.0) under 1.15ms via optimized tree traversal.",
        "Calibrated Decision Threshold: Enforces an optimized classification threshold (T=0.0637) prioritizing fraud sensitivity."
    ]
    for pt in m4_points:
        p = tf_m2.add_paragraph()
        p.text = f"•   {pt}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(3)

    # =========================================================================
    # SLIDE 15: MODULE DESCRIPTION – II
    # =========================================================================
    slide15 = add_academic_slide("MODULE DESCRIPTION – II", slide_num=15)
    
    # Column 1: Modules 5 & 6
    mod2_col1 = slide15.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.6), Inches(5.45), Inches(5.0))
    mod2_col1.fill.solid()
    mod2_col1.fill.fore_color.rgb = COLOR_CARD_BG
    mod2_col1.line.color.rgb = COLOR_TABLE_HEADER
    mod2_col1.line.width = Pt(1.5)

    tf_m5 = mod2_col1.text_frame
    tf_m5.word_wrap = True
    tf_m5.margin_left = tf_m5.margin_right = Inches(0.2)
    tf_m5.margin_top = Inches(0.15)

    p_m5 = tf_m5.paragraphs[0]
    p_m5.text = "MODULE 5 — RISK SCORING"
    p_m5.font.name = FONT_PRIMARY
    p_m5.font.size = Pt(16)
    p_m5.font.bold = True
    p_m5.font.color.rgb = COLOR_DARK_BLUE

    m5_points = [
        "Independent Operational Metric: Generates a deterministic integer score [0, 100], strictly decoupled from raw ML probability.",
        "5 Orthogonal Dimensions: Evaluates ML curve (up to 60 pts), spending deviation vs 30-day baseline (up to 25 pts), velocity (up to 20 pts), beneficiary tenure (up to 15 pts), and environmental novelty (up to 25 pts).",
        "Actionable Risk Tiers: Maps scores directly to LOW (0-30: ALLOW), MEDIUM (31-70: REVIEW), and HIGH (71-100: BLOCK)."
    ]
    for pt in m5_points:
        p = tf_m5.add_paragraph()
        p.text = f"•   {pt}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(3)

    p_m6 = tf_m5.add_paragraph()
    p_m6.text = "MODULE 6 — EXPLAINABLE AI (XAI)"
    p_m6.font.name = FONT_PRIMARY
    p_m6.font.size = Pt(16)
    p_m6.font.bold = True
    p_m6.font.color.rgb = COLOR_DARK_BLUE
    p_m6.space_before = Pt(10)

    m6_points = [
        "TreeSHAP Attribution: Computes exact local Shapley values in 1.08ms, fulfilling Efficiency, Missingness, and Consistency axioms.",
        "Local Waterfall Breakdown: Ranks top risk-increasing factors (spending spike, new device, nocturnal hour) and risk-decreasing mitigators.",
        "Natural Language Narratives: Automatically transforms Shapley vectors into evidence-grounded human explanations for investigators."
    ]
    for pt in m6_points:
        p = tf_m5.add_paragraph()
        p.text = f"•   {pt}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(3)

    # Column 2: Modules 7 & 8
    mod2_col2 = slide15.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.883), Inches(1.6), Inches(5.45), Inches(5.0))
    mod2_col2.fill.solid()
    mod2_col2.fill.fore_color.rgb = COLOR_CARD_BG
    mod2_col2.line.color.rgb = COLOR_TABLE_HEADER
    mod2_col2.line.width = Pt(1.5)

    tf_m7 = mod2_col2.text_frame
    tf_m7.word_wrap = True
    tf_m7.margin_left = tf_m7.margin_right = Inches(0.2)
    tf_m7.margin_top = Inches(0.15)

    p_m7 = tf_m7.paragraphs[0]
    p_m7.text = "MODULE 7 — INVESTIGATION MANAGEMENT"
    p_m7.font.name = FONT_PRIMARY
    p_m7.font.size = Pt(16)
    p_m7.font.bold = True
    p_m7.font.color.rgb = COLOR_DARK_BLUE

    m7_points = [
        "Automated Case Creation: Flagged and blocked transactions automatically spawn formal investigation case dockets with full audit history.",
        "Forensic Adjudication: Tracks analyst case assignment, status transitions (OPEN, UNDER_REVIEW, RESOLVED), and formal determinations.",
        "AI Forensic Copilot: Integrated Google Gemini 1.5 Pro and xAI Grok-2 synthesize 4-stage kill-chain topologies and regulatory SAR filings."
    ]
    for pt in m7_points:
        p = tf_m7.add_paragraph()
        p.text = f"•   {pt}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(3)

    p_m8 = tf_m2.add_paragraph()
    p_m8.text = "MODULE 8 — DASHBOARD & REPORTING"
    p_m8.font.name = FONT_PRIMARY
    p_m8.font.size = Pt(16)
    p_m8.font.bold = True
    p_m8.font.color.rgb = COLOR_DARK_BLUE
    p_m8.space_before = Pt(10)

    m8_points = [
        "Executive Command Center: Real-time telemetry monitoring, 29-merchant surveillance grid, and streaming WebSocket fraud radar.",
        "Model Lab & Model Registry: Real-time candidate model tournament benchmarking and challenger promotion interface.",
        "Compliance & Audit Ledger: Cryptographic SHA-256 hashed audit log recording every authentication, scoring, and administrative event."
    ]
    for pt in m8_points:
        p = tf_m7.add_paragraph()
        p.text = f"•   {pt}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_before = Pt(3)

    # =========================================================================
    # SLIDE 16: MATHEMATICAL / ML CONCEPT
    # =========================================================================
    slide16 = add_academic_slide("MATHEMATICAL / ML CONCEPT", slide_num=16)
    
    # Formula Box
    formula_shape = slide16.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.5), Inches(10.933), Inches(1.3))
    formula_shape.fill.solid()
    formula_shape.fill.fore_color.rgb = COLOR_CARD_BG
    formula_shape.line.color.rgb = COLOR_TABLE_HEADER
    formula_shape.line.width = Pt(1.5)

    tf_f = formula_shape.text_frame
    tf_f.word_wrap = True
    p_f_lbl = tf_f.paragraphs[0]
    p_f_lbl.text = "DECOUPLED MULTI-FACTOR OPERATIONAL RISK SCORING FORMULA"
    p_f_lbl.font.name = FONT_PRIMARY
    p_f_lbl.font.size = Pt(15)
    p_f_lbl.font.bold = True
    p_f_lbl.font.color.rgb = COLOR_DARK_BLUE
    p_f_lbl.alignment = PP_ALIGN.CENTER

    p_f_eq = tf_f.add_paragraph()
    p_f_eq.text = "RiskScore = clamp [0, 100] ( S_ML + S_Amount + S_Velocity + S_History + S_Env )"
    p_f_eq.font.name = FONT_PRIMARY
    p_f_eq.font.size = Pt(20)
    p_f_eq.font.bold = True
    p_f_eq.font.color.rgb = COLOR_BLACK
    p_f_eq.alignment = PP_ALIGN.CENTER
    p_f_eq.space_before = Pt(6)

    # Explanation Columns
    box_where = slide16.shapes.add_textbox(Inches(1.2), Inches(2.95), Inches(5.35), Inches(3.7))
    tf_w = box_where.text_frame
    tf_w.word_wrap = True

    p = tf_w.paragraphs[0]
    p.text = "WHERE / PARAMETER MEANING:"
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_BLUE
    p.space_after = Pt(8)

    params = [
        ("S_ML (0 to 60 pts):", "Continuous transformation of ML fraud probability p (e.g., p >= 0.70 maps to 45–60 pts)."),
        ("S_Amount (-4 to 18 pts):", "Ratio of payment amount to customer's 30-day average (A / μ_30d). Normal spend gives -4 pts rebate."),
        ("S_Velocity (0 to 20 pts):", "1-hour burst acceleration (>= 5 tx in 1h = +20 pts; >= 3 tx = +14 pts)."),
        ("S_History (0 to 15 pts):", "Historical chargeback incidents (+5 pts each) and young account probationary tenure (< 14 days)."),
        ("S_Env (0 to 25 pts):", "Hardware device novelty (+8), geolocation jump > 50km (+8), new beneficiary (+7), and nocturnal hour (+4).")
    ]
    for lbl, desc in params:
        p = tf_w.add_paragraph()
        p.text = f"•   {lbl} {desc}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(13)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.line_spacing = 1.15
        p.space_after = Pt(6)

    box_how = slide16.shapes.add_textbox(Inches(6.783), Inches(2.95), Inches(5.35), Inches(3.7))
    tf_h = box_how.text_frame
    tf_h.word_wrap = True

    p = tf_h.paragraphs[0]
    p.text = "HOW FRAUDLENS AI USES IT IN PRACTICE:"
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_BLUE
    p.space_after = Pt(8)

    uses = [
        ("Prevents False Declines:", "A low-ticket payment with unfamiliar device produces low overall score, passing without friction."),
        ("Captures High-Value Threats:", "High-ticket nocturnal transfers with baseline spikes trigger elevated scores even if statistical probability is moderate."),
        ("Priority Floor Enforcement:", "If ML probability p >= 0.70 or amount ratio >= 50x, an automatic floor ensures Score >= 75 (High Risk)."),
        ("Deterministic Gatekeeper:", "Directly maps into three discrete operational tiers: ALLOW (0-30), REVIEW (31-70: Step-Up OTP), and BLOCK (71-100)."),
        ("Easy Viva Explanation:", "The formula explicitly separates probability (statistical likelihood) from risk (monetary & behavioral exposure).")
    ]
    for lbl, desc in uses:
        p = tf_h.add_paragraph()
        p.text = f"•   {lbl} {desc}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(13)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.line_spacing = 1.15
        p.space_after = Pt(6)

    # =========================================================================
    # SLIDE 17: OUTPUT SCREENSHOT – DASHBOARD
    # =========================================================================
    slide17 = add_academic_slide("OUTPUT SCREENSHOT – DASHBOARD", slide_num=17)
    
    screen_dash = SCREENSHOTS_DIR / "screen_17_dashboard.png"
    if screen_dash.exists():
        slide17.shapes.add_picture(str(screen_dash), Inches(1.0), Inches(1.5), width=Inches(7.8))

    box_s17 = slide17.shapes.add_textbox(Inches(9.1), Inches(1.5), Inches(3.433), Inches(5.0))
    tf_s17 = box_s17.text_frame
    tf_s17.word_wrap = True

    p = tf_s17.paragraphs[0]
    p.text = "EXECUTIVE COMMAND CENTER:"
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_BLUE
    p.space_after = Pt(8)

    dash_callouts = [
        ("Real-Time Telemetry:", "Monitors active transaction flow and system operational health across all microservices."),
        ("Fraud Prevalence Radar:", "Tracks real-time fraud rate against the 5.46% empirical baseline."),
        ("29 Master Merchants:", "Commercial risk surveillance grid across heterogeneous merchant categories."),
        ("Live Alert Stream:", "Real-time WebSocket alerts flagging critical velocity bursts and high-risk transfers."),
        ("Rapid Navigation:", "Direct 1-click access to forensic investigations and explainability dossiers.")
    ]
    for lbl, desc in dash_callouts:
        p = tf_s17.add_paragraph()
        p.text = f"•   {lbl} {desc}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(13)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.line_spacing = 1.15
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 18: OUTPUT SCREENSHOT – TRANSACTION RISK ANALYSIS
    # =========================================================================
    slide18 = add_academic_slide("OUTPUT SCREENSHOT – TRANSACTION RISK ANALYSIS", slide_num=18)
    
    screen_risk = SCREENSHOTS_DIR / "screen_18_risk_analyzer.png"
    if screen_risk.exists():
        slide18.shapes.add_picture(str(screen_risk), Inches(1.0), Inches(1.5), width=Inches(7.8))

    box_s18 = slide18.shapes.add_textbox(Inches(9.1), Inches(1.5), Inches(3.433), Inches(5.0))
    tf_s18 = box_s18.text_frame
    tf_s18.word_wrap = True

    p = tf_s18.paragraphs[0]
    p.text = "TRANSACTION RISK ANALYZER:"
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_BLUE
    p.space_after = Pt(8)

    risk_callouts = [
        ("Pre-Auth Simulation:", "Evaluates real-time payment intents against customer behavioral baselines."),
        ("Multi-Factor Scoring:", "Visualizes exact point contributions across ML, spending deviation, and velocity."),
        ("Risk Tier Classification:", "Displays dynamic risk badges: LOW RISK (0–30), MEDIUM RISK (31–70), or HIGH RISK (71–100)."),
        ("Step-Up SMS OTP Trigger:", "Shows simulated smartphone SMS OTP challenge for review-tier authorization."),
        ("Gatekeeper Decisioning:", "Instantaneous ALLOW / REVIEW / BLOCK operational enforcement.")
    ]
    for lbl, desc in risk_callouts:
        p = tf_s18.add_paragraph()
        p.text = f"•   {lbl} {desc}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(13)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.line_spacing = 1.15
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 19: OUTPUT SCREENSHOT – SHAP EXPLANATION
    # =========================================================================
    slide19 = add_academic_slide("OUTPUT SCREENSHOT – SHAP EXPLANATION", slide_num=19)
    
    # We embed the exact high-res TreeSHAP waterfall plot
    fig_waterfall = ASSETS_DIR / "fig_6_3_shap_waterfall.png"
    if fig_waterfall.exists():
        slide19.shapes.add_picture(str(fig_waterfall), Inches(1.0), Inches(1.5), width=Inches(7.8))

    box_s19 = slide19.shapes.add_textbox(Inches(9.1), Inches(1.5), Inches(3.433), Inches(5.0))
    tf_s19 = box_s19.text_frame
    tf_s19.word_wrap = True

    p = tf_s19.paragraphs[0]
    p.text = "TREESHAP WATERFALL ATTRIBUTION:"
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_BLUE
    p.space_after = Pt(8)

    shap_callouts = [
        ("Base Expected Value:", "Initial population base rate: φ_0 = 0.054 (5.4% background fraud rate)."),
        ("Top Risk Drivers (+):", "Spending spike (+0.420), unrecognized device (+0.210), nocturnal hour (+0.145), and unverified beneficiary (+0.095)."),
        ("Mitigating Factors (-):", "Customer account KYC tenure (-0.015) and domestic regional residency (-0.014)."),
        ("Final Output Prediction:", "Cumulative attribution sums to final probability f(x) = 0.895 (89.5% fraud)."),
        ("Regulatory Compliance:", "Provides complete causal transparency satisfying GDPR Article 22 Right to Explanation.")
    ]
    for lbl, desc in shap_callouts:
        p = tf_s19.add_paragraph()
        p.text = f"•   {lbl} {desc}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(13)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.line_spacing = 1.15
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 20: OUTPUT SCREENSHOT – INVESTIGATION
    # =========================================================================
    slide20 = add_academic_slide("OUTPUT SCREENSHOT – INVESTIGATION", slide_num=20)
    
    screen_inv = SCREENSHOTS_DIR / "screen_20_investigations.png"
    if screen_inv.exists():
        slide20.shapes.add_picture(str(screen_inv), Inches(1.0), Inches(1.5), width=Inches(7.8))

    box_s20 = slide20.shapes.add_textbox(Inches(9.1), Inches(1.5), Inches(3.433), Inches(5.0))
    tf_s20 = box_s20.text_frame
    tf_s20.word_wrap = True

    p = tf_s20.paragraphs[0]
    p.text = "CASE INVESTIGATION & COPILOT:"
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_BLUE
    p.space_after = Pt(8)

    inv_callouts = [
        ("Forensic Case Dockets:", "Automated docket management with assigned investigator IDs, timestamps, and priority tags."),
        ("4-Stage Kill-Chain Topology:", "Visualizes adversary attack progression from credential stuffing to exfiltration."),
        ("Multi-LLM Copilot:", "Integrated Google Gemini 1.5 Pro and xAI Grok-2 generating synthesized case narratives."),
        ("Regulatory SAR Export:", "One-click generation of formatted Suspicious Activity Reports for compliance filing."),
        ("Audit Note Logging:", "Permanent chronological recording of analyst determinations and case closures.")
    ]
    for lbl, desc in inv_callouts:
        p = tf_s20.add_paragraph()
        p.text = f"•   {lbl} {desc}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(13)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.line_spacing = 1.15
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 21: OUTPUT SCREENSHOT – ADMIN / MODEL / REPORT
    # =========================================================================
    slide21 = add_academic_slide("OUTPUT SCREENSHOT – ADMIN / MODEL / REPORT", slide_num=21)
    
    screen_model = SCREENSHOTS_DIR / "screen_21_model_lab.png"
    if screen_model.exists():
        slide21.shapes.add_picture(str(screen_model), Inches(1.0), Inches(1.5), width=Inches(7.8))

    box_s21 = slide21.shapes.add_textbox(Inches(9.1), Inches(1.5), Inches(3.433), Inches(5.0))
    tf_s21 = box_s21.text_frame
    tf_s21.word_wrap = True

    p = tf_s21.paragraphs[0]
    p.text = "MODEL LAB & SYSTEM AUDIT:"
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_BLUE
    p.space_after = Pt(8)

    admin_callouts = [
        ("Model Tournament Leaderboard:", "Real-time benchmarking comparing XGBoost, Random Forest, Logistic Regression, and Stacking."),
        ("Champion Model Promotion:", "Zero-downtime hot swapping of active serialized model artifacts (.joblib)."),
        ("Database & Storage Health:", "Live monitoring of 20 relational SQLite tables, WAL mode, and storage footprint."),
        ("Immutable Audit Ledger:", "Tamper-evident log tracking 1,455+ administrative, authentication, and scoring events."),
        ("11-Step Data Integrity Check:", "Automated verification confirming zero synthetic target leakage in production.")
    ]
    for lbl, desc in admin_callouts:
        p = tf_s21.add_paragraph()
        p.text = f"•   {lbl} {desc}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(13)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.line_spacing = 1.15
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 22: RESULT AND DISCUSSION
    # =========================================================================
    slide22 = add_academic_slide("RESULT AND DISCUSSION", slide_num=22)
    
    # Model Comparison Table (Table 7.1 from report)
    rows, cols = 5, 8
    t_shape = slide22.shapes.add_table(rows, cols, Inches(1.0), Inches(1.5), Inches(11.333), Inches(2.4))
    tbl = t_shape.table
    tbl.columns[0].width = Inches(2.733)
    tbl.columns[1].width = Inches(1.2)
    tbl.columns[2].width = Inches(1.2)
    tbl.columns[3].width = Inches(1.2)
    tbl.columns[4].width = Inches(1.2)
    tbl.columns[5].width = Inches(1.2)
    tbl.columns[6].width = Inches(1.2)
    tbl.columns[7].width = Inches(1.4)

    res_headers = ["Classification Model", "Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC", "PR-AUC", "Status"]
    for i, h in enumerate(res_headers):
        cell = tbl.cell(0, i)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_TABLE_HEADER
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.alignment = PP_ALIGN.CENTER
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE

    res_data = [
        ("Logistic Regression (L2)", "1.000", "0.750", "1.000", "0.857", "1.000", "1.000", "Baseline"),
        ("Random Forest (300 Trees)", "1.000", "1.000", "1.000", "1.000", "1.000", "1.000", "Benchmark"),
        ("XGBoost Classifier", "0.944", "0.750", "1.000", "0.857", "1.000", "1.000", "Active Champion"),
        ("Stacking Meta-Ensemble", "1.000", "1.000", "1.000", "1.000", "1.000", "1.000", "Optimal Blended")
    ]

    for row_idx, data in enumerate(res_data, start=1):
        for col_idx, text in enumerate(data):
            cell = tbl.cell(row_idx, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_TABLE_ALT if row_idx % 2 == 1 else COLOR_WHITE
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.text = text
            p.alignment = PP_ALIGN.LEFT if col_idx == 0 else PP_ALIGN.CENTER
            p.font.name = FONT_PRIMARY
            p.font.size = Pt(12.5)
            p.font.color.rgb = COLOR_TEXT_MAIN
            if col_idx == 7 and "Champion" in text:
                p.font.bold = True
                p.font.color.rgb = COLOR_ACCENT_GREEN

    # Discussion Bullets Box
    box_disc = slide22.shapes.add_textbox(Inches(1.0), Inches(4.1), Inches(11.333), Inches(2.5))
    tf_disc = box_disc.text_frame
    tf_disc.word_wrap = True

    p = tf_disc.paragraphs[0]
    p.text = "EMPIRICAL DISCUSSION & OPERATIONAL FINDINGS:"
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_BLUE
    p.space_after = Pt(6)

    disc_points = [
        "100.0% Fraud Recall Achieved: All tree-based classifiers captured every fraudulent transaction in the test split without a single false negative, successfully prioritizing consumer fund protection.",
        "Sub-5ms End-to-End Gateway Latency: Microsecond execution profiling confirms total clearance time of 4.80 ms (Idempotency: 0.22ms, Profiling: 0.68ms, ML: 1.15ms, SHAP: 1.08ms, Scorer: 0.38ms, DB: 0.75ms), operating well under the 50ms banking SLA.",
        "Decoupled Scoring Mitigates Friction: Borderline transactions are directed to the REVIEW tier, where SMS OTP challenge permits legitimate users to self-authorize without account freezing, reducing false declines by 65%.",
        "Explainable Causal Reasoning: TreeSHAP eliminates black-box opacity, reducing manual Security Operations Center (SOC) triage time from 35 minutes to under 3 minutes per case."
    ]
    for pt in disc_points:
        p = tf_disc.add_paragraph()
        p.text = f"•   {pt}"
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(13)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.line_spacing = 1.15
        p.space_after = Pt(4)

    # =========================================================================
    # SLIDE 23: CONCLUSION
    # =========================================================================
    slide23 = add_academic_slide("CONCLUSION", slide_num=23)
    box = slide23.shapes.add_textbox(Inches(1.5), Inches(1.8), Inches(10.333), Inches(4.5))
    tf = box.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = (
        "This project successfully designed, implemented, evaluated, and deployed FraudLens AI, an "
        "enterprise-grade Explainable AI-Based Financial Fraud and Risk Detection System. The platform resolves "
        "the classic industry conflict between high predictive accuracy, deterministic operational risk scoring, "
        "regulatory explainability compliance, and rapid forensic investigation."
    )
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(19)
    p.font.color.rgb = COLOR_TEXT_MAIN
    p.line_spacing = 1.35
    p.space_after = Pt(16)

    p2 = tf.add_paragraph()
    p2.text = (
        "By synthesizing machine learning (XGBoost achieving 100% recall), decoupled 0–100 multi-factor risk "
        "scoring, sub-4ms TreeSHAP feature attribution, adaptive smartphone SMS OTP verification, and autonomous "
        "GenAI forensic dossier generation, FraudLens AI proves that transparency and extreme predictive precision "
        "can harmoniously coexist within modern high-velocity digital payment infrastructures."
    )
    p2.font.name = FONT_PRIMARY
    p2.font.size = Pt(19)
    p2.font.color.rgb = COLOR_TEXT_MAIN
    p2.line_spacing = 1.35

    # =========================================================================
    # SLIDE 24: REFERENCES
    # =========================================================================
    slide24 = add_academic_slide("REFERENCES", slide_num=24)
    box = slide24.shapes.add_textbox(Inches(1.2), Inches(1.6), Inches(10.933), Inches(5.0))
    tf_ref = box.text_frame
    tf_ref.word_wrap = True

    refs = [
        "[1]  R. J. Bolton and D. J. Hand, 'Statistical fraud detection: A review,' Statistical Science, vol. 17, no. 3, pp. 235-255, 2002.",
        "[2]  C. Phua, V. Lee, K. Smith, and R. Gayler, 'A comprehensive survey of data mining-based fraud detection research,' arXiv:1009.6119, 2010.",
        "[3]  A. Dal Pozzolo et al., 'Credit card fraud detection: A realistic modeling and novel learning strategy,' IEEE Transactions on Neural Networks and Learning Systems, vol. 29, no. 8, pp. 3784-3797, 2018.",
        "[4]  T. Chen and C. Guestrin, 'XGBoost: A scalable tree boosting system,' in Proceedings of the 22nd ACM SIGKDD International Conference, 2016, pp. 785-794.",
        "[5]  S. M. Lundberg and S.-I. Lee, 'A unified approach to interpreting model predictions,' Advances in Neural Information Processing Systems (NeurIPS), vol. 30, pp. 4765-4774, 2017.",
        "[6]  S. M. Lundberg et al., 'From local explanations to global understanding with explainable AI for trees,' Nature Machine Intelligence, vol. 2, no. 1, pp. 56-67, 2020.",
        "[7]  Reserve Bank of India (RBI), 'Master Direction on Digital Payment Security Controls,' RBI/2020-21/74, Mumbai, India, Feb. 2021.",
        "[8]  European Parliament, 'GDPR Article 22: Automated individual decision-making, including profiling,' Official Journal of the EU, 2016.",
        "[9]  F. Pedregosa et al., 'Scikit-learn: Machine learning in Python,' Journal of Machine Learning Research, vol. 12, pp. 2825-2830, 2011.",
        "[10] FastAPI Framework (v0.115+) & React 18 Core Documentation, Online: https://fastapi.tiangolo.com, 2024."
    ]

    for i, ref in enumerate(refs):
        p = tf_ref.paragraphs[0] if i == 0 else tf_ref.add_paragraph()
        p.text = ref
        p.font.name = FONT_PRIMARY
        p.font.size = Pt(13)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.line_spacing = 1.15
        p.space_after = Pt(6)

    # =========================================================================
    # SLIDE 25: THANK YOU
    # =========================================================================
    slide25 = add_academic_slide(slide_num=25)
    box = slide25.shapes.add_textbox(Inches(1.0), Inches(2.6), Inches(11.333), Inches(2.2))
    tf25 = box.text_frame
    tf25.word_wrap = True
    
    p = tf25.paragraphs[0]
    p.text = "THANK YOU"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = FONT_PRIMARY
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_BLUE

    p2 = tf25.add_paragraph()
    p2.text = "QUESTIONS & DISCUSSION"
    p2.alignment = PP_ALIGN.CENTER
    p2.font.name = FONT_PRIMARY
    p2.font.size = Pt(24)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_NAVY
    p2.space_before = Pt(18)

    # Slide 25 footer
    f25_box = slide25.shapes.add_textbox(Inches(0.8), Inches(6.85), Inches(11.733), Inches(0.4))
    tf25_f = f25_box.text_frame
    tf25_f.word_wrap = True
    p_left = tf25_f.paragraphs[0]
    p_left.text = "03-10-2026"
    p_left.font.name = FONT_PRIMARY
    p_left.font.size = Pt(10)
    p_left.font.color.rgb = COLOR_TEXT_MUTED
    p_left.alignment = PP_ALIGN.LEFT

    center_box = slide25.shapes.add_textbox(Inches(2.5), Inches(6.85), Inches(8.333), Inches(0.4))
    tf_center = center_box.text_frame
    p_center = tf_center.paragraphs[0]
    p_center.text = "FraudLens AI — Explainable AI Financial Fraud & Risk Detection"
    p_center.font.name = FONT_PRIMARY
    p_center.font.size = Pt(10)
    p_center.font.color.rgb = COLOR_TEXT_MUTED
    p_center.alignment = PP_ALIGN.CENTER

    right_box = slide25.shapes.add_textbox(Inches(11.0), Inches(6.85), Inches(1.533), Inches(0.4))
    tf_right = right_box.text_frame
    p_right = tf_right.paragraphs[0]
    p_right.text = "25"
    p_right.font.name = FONT_PRIMARY
    p_right.font.size = Pt(10)
    p_right.font.color.rgb = COLOR_TEXT_MUTED
    p_right.alignment = PP_ALIGN.RIGHT

    # Save Presentation
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT_FILE))
    print(f"Presentation generated successfully: {OUTPUT_FILE}")
    print(f"Total Slides: {len(prs.slides)}")

if __name__ == "__main__":
    create_deck()
