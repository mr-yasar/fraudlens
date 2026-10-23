"""
Generate Visual 02: FraudLens AI - Real-Time Transaction Risk and Security Workflow
Outputs:
- project_report/assets/presentation_visuals/fraudlens_realtime_risk_workflow.png (1920x1080)
- project_report/assets/presentation_visuals/fraudlens_realtime_risk_workflow.svg
- project_report/assets/fraudlens_realtime_risk_workflow.png
- project_report/assets/fraudlens_realtime_risk_workflow.svg
"""

import os
import shutil
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUT_DIR = Path("project_report/assets/presentation_visuals")
OUT_DIR.mkdir(parents=True, exist_ok=True)
PNG_PATH = OUT_DIR / "fraudlens_realtime_risk_workflow.png"
SVG_PATH = OUT_DIR / "fraudlens_realtime_risk_workflow.svg"

ALT_DIR = Path("project_report/assets")
ALT_PNG_PATH = ALT_DIR / "fraudlens_realtime_risk_workflow.png"
ALT_SVG_PATH = ALT_DIR / "fraudlens_realtime_risk_workflow.svg"

def draw_vector_icon(ax, icon_type, cx, cy, size=16, color="#38bdf8", zorder=5):
    r = size / 2.0
    if icon_type == "lightning":
        pts = [
            (cx - 0.2*r, cy + r), (cx + 0.6*r, cy + 0.1*r), (cx + 0.05*r, cy + 0.05*r),
            (cx + 0.35*r, cy - r), (cx - 0.6*r, cy - 0.05*r), (cx - 0.05*r, cy - 0.05*r)
        ]
        ax.add_patch(patches.Polygon(pts, closed=True, fc=color, ec="none", zorder=zorder))
    elif icon_type == "shield":
        pts = [
            (cx - 0.8*r, cy + 0.8*r), (cx + 0.8*r, cy + 0.8*r), (cx + 0.8*r, cy + 0.1*r),
            (cx, cy - 0.9*r), (cx - 0.8*r, cy + 0.1*r)
        ]
        ax.add_patch(patches.Polygon(pts, closed=True, fc=color, ec="none", zorder=zorder))
        ax.add_patch(patches.Circle((cx, cy + 0.15*r), 0.3*r, fc="#060a17", ec="none", zorder=zorder+1))
    elif icon_type == "phone":
        ax.add_patch(patches.FancyBboxPatch((cx - 0.6*r, cy - 0.9*r), 1.2*r, 1.8*r, boxstyle="round,pad=0,rounding_size=3", fc=color, ec="none", zorder=zorder))
        ax.add_patch(patches.Rectangle((cx - 0.45*r, cy - 0.65*r), 0.9*r, 1.3*r, fc="#060a17", zorder=zorder+1))
        ax.add_patch(patches.Circle((cx, cy - 0.77*r), 0.08*r, fc=color, ec="none", zorder=zorder+2))
    elif icon_type == "chart":
        ax.add_patch(patches.Rectangle((cx - 0.7*r, cy - 0.7*r), 0.35*r, 0.7*r, fc=color, zorder=zorder))
        ax.add_patch(patches.Rectangle((cx - 0.2*r, cy - 0.7*r), 0.35*r, 1.1*r, fc=color, zorder=zorder))
        ax.add_patch(patches.Rectangle((cx + 0.3*r, cy - 0.7*r), 0.35*r, 1.4*r, fc=color, zorder=zorder))
    elif icon_type == "check":
        pts = [(cx - 0.6*r, cy), (cx - 0.15*r, cy - 0.5*r), (cx + 0.65*r, cy + 0.6*r)]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, lw=2.5, zorder=zorder)

def create_visual_02():
    # 16:9 Canvas (1920 x 1080 px at 100 dpi)
    fig, ax = plt.subplots(figsize=(19.2, 10.8), dpi=100)
    fig.patch.set_facecolor("#060a17")
    ax.set_facecolor("#060a17")
    ax.set_xlim(0, 1920)
    ax.set_ylim(0, 1080)
    ax.axis("off")

    def draw_card(x, y, w, h, bg="#0d1830", border="#1e2d4d", lw=1.5, radius=12, shadow=True):
        if shadow:
            s_box = patches.FancyBboxPatch(
                (x + 2, y - 3), w, h,
                boxstyle=f"round,pad=0,rounding_size={radius}",
                fc="#02040a", ec="none", alpha=0.55, zorder=1
            )
            ax.add_patch(s_box)
        box = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad=0,rounding_size={radius}",
            fc=bg, ec=border, lw=lw, zorder=2
        )
        ax.add_patch(box)
        return box

    def draw_pill(x, y, w, h, text, bg="#1e293b", fg="#94a3b8", border="none", fontsize=9.0, bold=True, zorder=4):
        p = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad=0,rounding_size={h/2}",
            fc=bg, ec=border if border != "none" else bg, lw=1, zorder=zorder
        )
        ax.add_patch(p)
        ax.text(
            x + w/2, y + h/2, text,
            ha="center", va="center", fontsize=fontsize,
            fontweight="bold" if bold else "normal", color=fg,
            family="DejaVu Sans", zorder=zorder+1
        )

    # Ambient Background Glows
    ax.add_patch(patches.Circle((960, 1080), 750, fc="#0284c7", alpha=0.035, zorder=0))
    ax.add_patch(patches.Circle((200, 200), 500, fc="#ef4444", alpha=0.025, zorder=0))
    ax.add_patch(patches.Circle((1750, 600), 550, fc="#10b981", alpha=0.03, zorder=0))

    # -------------------------------------------------------------------------
    # 1. HEADER SECTION
    # -------------------------------------------------------------------------
    draw_pill(50, 1022, 540, 26, "TRANSACTION ADJUDICATION LIFECYCLE  •  REAL-TIME FORENSIC DECISION PATH", 
              bg="#0a1d38", fg="#38bdf8", border="#0284c7", fontsize=8.5, bold=True)

    ax.text(50, 980, "FRAUDLENS AI — TRANSACTION RISK & SECURITY WORKFLOW",
            fontsize=20.0, fontweight="bold", color="#ffffff", family="DejaVu Sans", zorder=3)

    ax.text(50, 948, "Live Payment Scoring Journey: Ingestion  -->  Dual Evaluation (ML & Risk)  -->  TreeSHAP Breakdown  -->  Action Gatekeeper",
            fontsize=11.2, color="#94a3b8", family="DejaVu Sans", zorder=3)

    # Right Transaction Context Badges
    ctx_items = [
        ("TRANSACTION ID", "TX-849201-IND", "#ffffff", "#1e293b"),
        ("PAYMENT AMOUNT", "Rs. 84,500.00", "#f87171", "#450a0a"),
        ("MERCHANT ENTITY", "Aurelia Gold House", "#fbbf24", "#451a03"),
        ("TIMING / WINDOW", "02:41 IST (Night)", "#c084fc", "#3b0764")
    ]
    for idx, (label, val, col_fg, col_bg) in enumerate(ctx_items):
        cx = 1180 + idx * 172
        draw_card(cx, 940, 158, 70, bg="#0d1830", border=col_bg, lw=1.2, radius=8)
        ax.text(cx + 79, 976, label, ha="center", va="center", fontsize=7.8, fontweight="bold", color="#64748b", family="DejaVu Sans", zorder=3)
        ax.text(cx + 79, 954, val, ha="center", va="center", fontsize=12.0, fontweight="bold", color=col_fg, family="DejaVu Sans", zorder=3)

    ax.plot([50, 1870], [925, 925], color="#1e293b", lw=1.2, zorder=2)

    # -------------------------------------------------------------------------
    # 2. COLUMN 1: STEP-BY-STEP ADJUDICATION ENGINE (Left: X 50 to 650, Y 45 to 905)
    # -------------------------------------------------------------------------
    col1_w = 600
    col1_x = 50

    draw_pill(col1_x, 885, 230, 24, "SECTION A: 4-STAGE PIPELINE FLOW", bg="#0c2340", fg="#38bdf8", border="#0284c7", fontsize=8.5, bold=True)
    ax.text(col1_x + 245, 897, "|   Sequential Verification Architecture", fontsize=10.5, color="#64748b", family="DejaVu Sans", zorder=3)

    flow_steps = [
        {
            "step": "STEP 01",
            "title": "Payment Initiation & Idempotency Audit",
            "accent": "#38bdf8",
            "bg": "#082f49",
            "y": 685,
            "h": 185,
            "items": [
                ("Inbound Payment Intent", "Amount: Rs. 84,500.00 | Channel: UPI QR | Device: SM-G998B"),
                ("Customer Profile (CUST-4029)", "30-Day Historical Spending Mean: mu = Rs. 3,200.00"),
                ("Spending Surge Factor", "A / mu_30d = 26.4x baseline average (Critical anomaly flag)"),
                ("SHA-256 Idempotency Cache", "Fingerprint verified in 0.22ms (Eliminates duplicate replays)")
            ]
        },
        {
            "step": "STEP 02",
            "title": "Dual-Metric Assessment (ML & Decoupled Risk)",
            "accent": "#fbbf24",
            "bg": "#451a03",
            "y": 480,
            "h": 185,
            "items": [
                ("Metric 1: ML Fraud Likelihood", "P = 0.895 (89.5% probability via XGBoost champion)"),
                ("Metric 2: Deterministic Score", "S = 88 / 100 (HIGH RISK TIER: 71 to 100 points)"),
                ("Additive Dimension Points", "S_ML: 54pts | S_Amt: +18pts | S_Vel: +8pts | S_Env: +8pts"),
                ("Priority Floor Enforced", "P >= 0.70 triggers automatic safety override: S >= 75 pts")
            ]
        },
        {
            "step": "STEP 03",
            "title": "Game-Theoretic TreeSHAP Attribution",
            "accent": "#a855f7",
            "bg": "#3b0764",
            "y": 275,
            "h": 185,
            "items": [
                ("Base Expected Value (phi_0)", "phi_0 = 0.054 (5.46% background population fraud rate)"),
                ("Primary Risk Driver (+)", "Spending surge (26.4x spike): +0.420 attribution impact"),
                ("Environmental Risk Drivers (+)", "Unrecognized hardware: +0.210 | Nocturnal hour: +0.145"),
                ("Mitigating KYR Factor (-)", "Long-standing account history (>180 days): -0.015 rebate")
            ]
        },
        {
            "step": "STEP 04",
            "title": "3-Tier Pre-Auth Gatekeeper Adjudication",
            "accent": "#ef4444",
            "bg": "#450a0a",
            "y": 55,
            "h": 200,
            "items": [
                ("LOW RISK (0-30): ALLOW", "Clear immediately in <4.8ms with frictionless customer pass"),
                ("MED RISK (31-70): REVIEW", "Hold funds; dispatch 6-digit SMS OTP to registered mobile"),
                ("HIGH RISK (71-100): BLOCK", "CURRENT OUTCOME (Score: 88) -> Hard decline & card lock"),
                ("Forensic Escalation", "Spawns Case Docket #2026-0941 & FinCEN SAR draft in SOC")
            ]
        }
    ]

    for st in flow_steps:
        sy = st["y"]
        sh = st["h"]
        draw_card(col1_x, sy, col1_w, sh, bg="#0d1830", border=st["accent"], lw=1.2, radius=10)
        
        draw_pill(col1_x + 16, sy + sh - 28, 80, 20, st["step"], bg=st["bg"], fg=st["accent"], border=st["accent"], fontsize=8.0, bold=True)
        ax.text(col1_x + 105, sy + sh - 18, st["title"], fontsize=11.5, fontweight="bold", color="#ffffff", family="DejaVu Sans", zorder=4)

        cy = sy + sh - 55
        for b_title, b_desc in st["items"]:
            ax.add_patch(patches.Circle((col1_x + 22, cy - 2), 3, fc=st["accent"], ec="none", zorder=4))
            ax.text(col1_x + 34, cy, b_title + ":", fontsize=9.5, fontweight="bold", color=st["accent"], family="DejaVu Sans", zorder=4)
            ax.text(col1_x + 34, cy - 16, b_desc, fontsize=8.8, color="#cbd5e1", family="DejaVu Sans", zorder=4)
            cy -= 36

        if st["step"] != "STEP 04":
            ax.annotate(
                "", xy=(col1_x + col1_w/2, sy - 15),
                xytext=(col1_x + col1_w/2, sy - 2),
                arrowprops=dict(arrowstyle="-|>", lw=2.2, color=st["accent"], mutation_scale=14),
                zorder=5
            )

    # -------------------------------------------------------------------------
    # 3. COLUMN 2: ALGORITHMIC PSEUDOCODE BLOCK (Center: X 680 to 1270, Y 45 to 905)
    # -------------------------------------------------------------------------
    col2_x = 680
    col2_w = 590
    col2_y = 55
    col2_h = 850

    draw_card(col2_x, col2_y, col2_w, col2_h, bg="#0a1224", border="#38bdf8", lw=1.5, radius=12)

    # Code Editor Window Header Bar
    ax.add_patch(patches.FancyBboxPatch(
        (col2_x, col2_y + col2_h - 40), col2_w, 40,
        boxstyle="round,pad=0,rounding_size=12",
        fc="#101d3b", ec="none", zorder=3
    ))
    ax.add_patch(patches.Rectangle((col2_x, col2_y + col2_h - 40), col2_w, 15, fc="#101d3b", ec="none", zorder=3))

    ax.add_patch(patches.Circle((col2_x + 20, col2_y + col2_h - 20), 5, fc="#ef4444", zorder=4))
    ax.add_patch(patches.Circle((col2_x + 36, col2_y + col2_h - 20), 5, fc="#f59e0b", zorder=4))
    ax.add_patch(patches.Circle((col2_x + 52, col2_y + col2_h - 20), 5, fc="#10b981", zorder=4))

    ax.text(col2_x + 75, col2_y + col2_h - 20, "fraudlens_preauth_adjudication_protocol.py", 
            ha="left", va="center", fontsize=9.5, fontweight="bold", color="#94a3b8", family="DejaVu Sans", zorder=4)

    draw_pill(col2_x + col2_w - 145, col2_y + col2_h - 30, 130, 20, "LATENCY: 4.80 ms", 
              bg="#070d1e", fg="#38bdf8", border="#0284c7", fontsize=8.0, bold=True)

    pseudocode = [
        ("BEGIN", "#f43f5e", True, 0),
        ("  INPUT: PaymentPayload p, CustomerProfile C, ModelSuite M", "#94a3b8", False, 0),
        ("  OUTPUT: Decision D in {ALLOW, REVIEW, BLOCK}, Shapley phi", "#94a3b8", False, 0),
        ("", "", False, 0),
        ("  // Stage 1: Idempotency & Feature Transformation", "#64748b", False, 0),
        ("  hash_id = SHA256(p.tx_id || p.amount || p.timestamp)", "#38bdf8", False, 0),
        ("  IF IsDuplicate(hash_id) THEN RETURN CachedResult(hash_id)", "#fbbf24", False, 0),
        ("  x = FullFraudPreprocessor.transform(p, C)  // 63-dim dense", "#f1f5f9", False, 0),
        ("", "", False, 0),
        ("  // Stage 2: Machine Learning Inference (1.15 ms)", "#64748b", False, 0),
        ("  P_fraud = XGBoostChampion.predict_proba(x)[1]", "#00d2ff", True, 0),
        ("", "", False, 0),
        ("  // Stage 3: Game-Theoretic TreeSHAP Attribution (1.08 ms)", "#64748b", False, 0),
        ("  phi = TreeSHAPExplainer.calculate_attributions(x)", "#c084fc", False, 0),
        ("  ASSERT P_fraud == (phi_0 + sum(phi))  // Local efficiency", "#94a3b8", False, 0),
        ("", "", False, 0),
        ("  // Stage 4: Decoupled Multi-Factor Risk Scoring", "#64748b", False, 0),
        ("  S_raw = S_ML(P_fraud) + S_Amount(p.amt, C.avg)", "#f1f5f9", False, 0),
        ("        + S_Velocity(C.vel_1h) + S_Env(p.device, p.geo)", "#f1f5f9", False, 0),
        ("  S = clamp(S_raw, 0, 100)", "#f1f5f9", False, 0),
        ("", "", False, 0),
        ("  // Stage 5: Safety Floor Priority Override", "#64748b", False, 0),
        ("  IF (P_fraud >= 0.70) OR (p.amt / C.avg >= 50.0) THEN", "#fbbf24", True, 0),
        ("    S = max(S, round(75.0 + P_fraud * 20.0))  // Enforce High", "#fbbf24", False, 2),
        ("  END IF", "#fbbf24", False, 0),
        ("", "", False, 0),
        ("  // Stage 6: 3-Tier Pre-Authorization Gatekeeper", "#64748b", False, 0),
        ("  IF S <= 30 AND P_fraud < 0.50 THEN", "#10b981", True, 0),
        ("    D = ALLOW; p.status = 'APPROVED'", "#10b981", False, 2),
        ("  ELSE IF S <= 70 OR (0.50 <= P_fraud < 0.85) THEN", "#fbbf24", True, 0),
        ("    D = REVIEW; TriggerStepUpSMS_OTP(C.phone)", "#fbbf24", False, 2),
        ("  ELSE", "#ef4444", True, 0),
        ("    D = BLOCK; p.status = 'REJECTED'", "#ef4444", False, 2),
        ("    AutoOpenCaseDocket(p, P_fraud, S, phi)", "#ef4444", False, 2),
        ("  END IF", "#ef4444", False, 0),
        ("", "", False, 0),
        ("  // Stage 7: Tamper-Evident Audit Commit (0.75 ms)", "#64748b", False, 0),
        ("  CommitAuditLedger(SHA256(p || D || S || Timestamp))", "#38bdf8", False, 0),
        ("  RETURN (D, P_fraud, S, phi)", "#f43f5e", True, 0),
        ("END", "#f43f5e", True, 0)
    ]

    code_y = col2_y + col2_h - 70
    for line_idx, (text, col, is_bold, indent) in enumerate(pseudocode, start=1):
        if text != "":
            ax.text(col2_x + 18, code_y, f"{line_idx:02d}", ha="left", va="center", fontsize=8.5, color="#334155", family="Courier New", zorder=4)
            ax.text(col2_x + 50 + indent*6, code_y, text, ha="left", va="center", fontsize=9.0, fontweight="bold" if is_bold else "normal", color=col, family="Courier New", zorder=4)
        code_y -= 19.5

    # -------------------------------------------------------------------------
    # 4. COLUMN 3: REAL-TIME OPERATIONAL PANELS (Right: X 1300 to 1870, Y 45 to 905)
    # -------------------------------------------------------------------------
    col3_x = 1300
    col3_w = 570

    # Panel 3.1: Customer Smartphone Slide-Down SMS OTP Challenge (Y: 625 to 905)
    p1_y = 625
    p1_h = 280
    draw_card(col3_x, p1_y, col3_w, p1_h, bg="#0d1830", border="#fbbf24", lw=1.5, radius=12)

    draw_pill(col3_x + 16, p1_y + p1_h - 32, 190, 22, "OPERATIONAL ARTIFACT 01", bg="#451a03", fg="#fbbf24", border="#fbbf24", fontsize=8.0, bold=True)
    draw_vector_icon(ax, "phone", col3_x + 224, p1_y + p1_h - 21, size=16, color="#fbbf24")
    ax.text(col3_x + 246, p1_y + p1_h - 21, "Customer Step-Up SMS OTP View", fontsize=11.5, fontweight="bold", color="#ffffff", family="DejaVu Sans", zorder=4)

    # Smartphone Mockup Box
    phone_box = patches.FancyBboxPatch(
        (col3_x + 20, p1_y + 20), col3_w - 40, p1_h - 65,
        boxstyle="round,pad=0,rounding_size=10",
        fc="#070e1e", ec="#253b66", lw=1.2, zorder=3
    )
    ax.add_patch(phone_box)

    # SMS Push Banner Inside Smartphone
    draw_card(col3_x + 36, p1_y + 115, col3_w - 72, 70, bg="#132347", border="#38bdf8", lw=1.2, radius=8)
    draw_vector_icon(ax, "shield", col3_x + 55, p1_y + 158, size=16, color="#38bdf8")
    ax.text(col3_x + 74, p1_y + 168, "FraudLens Bank Shield  •  SMS Security Verification", fontsize=9.0, fontweight="bold", color="#38bdf8", family="DejaVu Sans", zorder=4)
    ax.text(col3_x + 74, p1_y + 150, "Review Alert: High-value Rs. 84,500.00 transfer at Aurelia Gold.", fontsize=8.5, color="#cbd5e1", family="DejaVu Sans", zorder=4)
    ax.text(col3_x + 74, p1_y + 132, "One-Time Password: [ 7 3 9 - 2 0 4 ]  (Valid for 14:59)", fontsize=9.5, fontweight="bold", color="#fbbf24", family="DejaVu Sans", zorder=4)

    draw_pill(col3_x + 36, p1_y + 70, 240, 32, "VERIFY & AUTHORIZE PAYMENT", bg="#064e3b", fg="#34d399", border="#10b981", fontsize=9.0, bold=True)
    draw_pill(col3_x + 294, p1_y + 70, 240, 32, "DENY & FREEZE CARD INSTANTLY", bg="#450a0a", fg="#f87171", border="#ef4444", fontsize=9.0, bold=True)
    
    ax.text(col3_x + col3_w/2, p1_y + 40, "Self-Authorization eliminates 65% of false declines without customer account lockouts.", 
            ha="center", va="center", fontsize=8.2, color="#64748b", family="DejaVu Sans", zorder=4)

    # Panel 3.2: TreeSHAP Feature Attribution Waterfall (Y: 340 to 605)
    p2_y = 340
    p2_h = 265
    draw_card(col3_x, p2_y, col3_w, p2_h, bg="#0d1830", border="#a855f7", lw=1.5, radius=12)

    draw_pill(col3_x + 16, p2_y + p2_h - 32, 190, 22, "OPERATIONAL ARTIFACT 02", bg="#3b0764", fg="#c084fc", border="#a855f7", fontsize=8.0, bold=True)
    ax.text(col3_x + 220, p2_y + p2_h - 21, "TreeSHAP Local Attribution Waterfall", fontsize=11.5, fontweight="bold", color="#ffffff", family="DejaVu Sans", zorder=4)

    waterfall_items = [
        ("Spending Surge vs Baseline (26.4x)", "+0.420", 0.420, "#ef4444"),
        ("Unrecognized Hardware Device ID", "+0.210", 0.210, "#f87171"),
        ("Nocturnal Transaction Hour (02:41 IST)", "+0.145", 0.145, "#fbbf24"),
        ("Geographical Velocity Jump (310 km)", "+0.095", 0.095, "#f59e0b"),
        ("Young Beneficiary Account (< 24h)", "+0.040", 0.040, "#eab308"),
        ("Cardholder KYC Tenure (> 180 Days)", "-0.015", -0.015, "#10b981")
    ]

    wy = p2_y + p2_h - 65
    max_bar_w = 170
    for label_w, val_str, val_num, col_w in waterfall_items:
        ax.text(col3_x + 20, wy, label_w, fontsize=8.8, color="#e2e8f0", family="DejaVu Sans", zorder=4)
        ax.text(col3_x + 360, wy, val_str, ha="right", fontsize=9.2, fontweight="bold", color=col_w, family="DejaVu Sans", zorder=4)
        
        bar_len = abs(val_num) / 0.45 * max_bar_w
        ax.add_patch(patches.FancyBboxPatch((col3_x + 375, wy - 4), bar_len, 10, boxstyle="round,pad=0,rounding_size=3", fc=col_w, ec="none", zorder=4))
        wy -= 32

    ax.plot([col3_x + 20, col3_x + col3_w - 20], [p2_y + 36, p2_y + 36], color="#1e2d4d", lw=1, zorder=3)
    ax.text(col3_x + 20, p2_y + 20, "phi_0 = 0.054  +  sum(phi_i) = 0.841   ==>   Final Model P = 0.895 (100% Attributed)", 
            fontsize=8.5, fontweight="bold", color="#38bdf8", family="DejaVu Sans", zorder=4)

    # Panel 3.3: SOC Forensic Case Docket & SAR Auto-Export (Y: 55 to 320)
    p3_y = 55
    p3_h = 265
    draw_card(col3_x, p3_y, col3_w, p3_h, bg="#0d1830", border="#ef4444", lw=1.5, radius=12)

    draw_pill(col3_x + 16, p3_y + p3_h - 32, 190, 22, "OPERATIONAL ARTIFACT 03", bg="#450a0a", fg="#f87171", border="#ef4444", fontsize=8.0, bold=True)
    draw_vector_icon(ax, "shield", col3_x + 218, p3_y + p3_h - 21, size=16, color="#ef4444")
    ax.text(col3_x + 238, p3_y + p3_h - 21, "SOC Forensic Docket & SAR Export", fontsize=11.5, fontweight="bold", color="#ffffff", family="DejaVu Sans", zorder=4)

    # Docket Metadata Grid
    doc_y = p3_y + p3_h - 60
    ax.text(col3_x + 20, doc_y, "CASE DOCKET: CASE-2026-0941", fontsize=9.0, fontweight="bold", color="#ffffff", family="DejaVu Sans", zorder=4)
    draw_pill(col3_x + 245, doc_y - 8, 105, 20, "CRITICAL P1", bg="#450a0a", fg="#f87171", border="#ef4444", fontsize=7.8, bold=True)
    draw_pill(col3_x + 360, doc_y - 8, 190, 20, "STATUS: REJECTED / LOCKED", bg="#0f172a", fg="#fbbf24", border="#f59e0b", fontsize=7.6, bold=True)

    # Kill-chain attack progression strip
    kc_box = patches.FancyBboxPatch(
        (col3_x + 20, doc_y - 56), col3_w - 40, 38,
        boxstyle="round,pad=0,rounding_size=6",
        fc="#091326", ec="#1e2d4d", lw=1, zorder=3
    )
    ax.add_patch(kc_box)
    ax.text(col3_x + 26, doc_y - 32, "ATTACK KILL-CHAIN TOPOLOGY (Synthesized by Multi-LLM Copilot):", fontsize=7.6, fontweight="bold", color="#64748b", family="DejaVu Sans", zorder=4)
    ax.text(col3_x + 26, doc_y - 48, "1. Credential Stuffing  -->  2. Unseen Hardware  -->  3. Midnight Surge (26x)  -->  4. Exfiltration", fontsize=7.8, fontweight="bold", color="#38bdf8", family="DejaVu Sans", zorder=4)

    # FinCEN SAR Filing Narrative Box
    sar_box = patches.FancyBboxPatch(
        (col3_x + 20, p3_y + 48), col3_w - 40, 68,
        boxstyle="round,pad=0,rounding_size=6",
        fc="#141e33", ec="#253b66", lw=1, zorder=3
    )
    ax.add_patch(sar_box)
    ax.text(col3_x + 26, p3_y + 102, "REGULATORY SUSPICIOUS ACTIVITY REPORT (SAR) AUTO-DRAFT:", fontsize=7.8, fontweight="bold", color="#fbbf24", family="DejaVu Sans", zorder=4)
    ax.text(col3_x + 26, p3_y + 86, "'Subject CUST-4029 initiated abnormal Rs. 84,500 bullion purchase at 02:41 IST from anomalous", fontsize=8.0, color="#cbd5e1", family="DejaVu Sans", zorder=4)
    ax.text(col3_x + 26, p3_y + 70, " Bengaluru IP (310km jump). XGBoost P=0.895, Risk=88/100. Fund transfer halted immediately.'", fontsize=8.0, color="#cbd5e1", family="DejaVu Sans", zorder=4)
    ax.text(col3_x + 26, p3_y + 56, "Audit Chain Hash: SHA256[9b2d8e41a...7f1a]  •  Committed to SQLite WAL Mode Ledger", fontsize=7.6, color="#10b981", family="DejaVu Sans", zorder=4)

    ax.text(col3_x + 20, p3_y + 18, "Triage Duration: 2.8 mins (reduced from 35 mins industry baseline) via Autonomous AI Copilot.", 
            fontsize=8.0, color="#94a3b8", family="DejaVu Sans", zorder=4)

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(PNG_PATH, dpi=100, facecolor=fig.get_facecolor(), edgecolor="none")
    fig.savefig(SVG_PATH, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)

    shutil.copy2(PNG_PATH, ALT_PNG_PATH)
    shutil.copy2(SVG_PATH, ALT_SVG_PATH)

    print("Success: Visual 02 refined successfully.")

if __name__ == "__main__":
    create_visual_02()
