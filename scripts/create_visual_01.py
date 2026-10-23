"""
Generate Visual 01: FraudLens AI - Premium Project Overview & Architecture Pipeline
Outputs:
- project_report/assets/presentation_visuals/fraudlens_project_overview.png (1920x1080)
- project_report/assets/presentation_visuals/fraudlens_project_overview.svg
- project_report/assets/fraudlens_project_overview.png
- project_report/assets/fraudlens_project_overview.svg
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
PNG_PATH = OUT_DIR / "fraudlens_project_overview.png"
SVG_PATH = OUT_DIR / "fraudlens_project_overview.svg"

ALT_DIR = Path("project_report/assets")
ALT_PNG_PATH = ALT_DIR / "fraudlens_project_overview.png"
ALT_SVG_PATH = ALT_DIR / "fraudlens_project_overview.svg"

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
    elif icon_type == "user":
        ax.add_patch(patches.Circle((cx, cy + 0.35*r), 0.45*r, fc=color, ec="none", zorder=zorder))
        pts = [
            (cx - 0.8*r, cy - 0.8*r), (cx + 0.8*r, cy - 0.8*r),
            (cx + 0.6*r, cy - 0.15*r), (cx - 0.6*r, cy - 0.15*r)
        ]
        ax.add_patch(patches.Polygon(pts, closed=True, fc=color, ec="none", zorder=zorder))
    elif icon_type == "gear":
        ax.add_patch(patches.Circle((cx, cy), 0.8*r, fc=color, ec="none", zorder=zorder))
        ax.add_patch(patches.Circle((cx, cy), 0.4*r, fc="#060a17", ec="none", zorder=zorder+1))
    elif icon_type == "chart":
        ax.add_patch(patches.Rectangle((cx - 0.7*r, cy - 0.7*r), 0.35*r, 0.7*r, fc=color, zorder=zorder))
        ax.add_patch(patches.Rectangle((cx - 0.2*r, cy - 0.7*r), 0.35*r, 1.1*r, fc=color, zorder=zorder))
        ax.add_patch(patches.Rectangle((cx + 0.3*r, cy - 0.7*r), 0.35*r, 1.4*r, fc=color, zorder=zorder))
    elif icon_type == "check":
        pts = [(cx - 0.6*r, cy), (cx - 0.15*r, cy - 0.5*r), (cx + 0.65*r, cy + 0.6*r)]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, lw=2.5, zorder=zorder)

def create_visual_01():
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
    ax.add_patch(patches.Circle((960, 1080), 700, fc="#0284c7", alpha=0.04, zorder=0))
    ax.add_patch(patches.Circle((250, 250), 500, fc="#4f46e5", alpha=0.03, zorder=0))
    ax.add_patch(patches.Circle((1700, 250), 500, fc="#059669", alpha=0.03, zorder=0))

    # -------------------------------------------------------------------------
    # 1. HEADER SECTION
    # -------------------------------------------------------------------------
    draw_pill(50, 1022, 530, 26, "ENTERPRISE EXPLAINABLE AI (XAI) PLATFORM  •  HIGH-THROUGHPUT FRAUD DEFENSE", 
              bg="#0a1d38", fg="#38bdf8", border="#0284c7", fontsize=8.5, bold=True)

    ax.text(50, 980, "FRAUDLENS AI — SYSTEM OVERVIEW & ARCHITECTURE",
            fontsize=22.5, fontweight="bold", color="#ffffff", family="DejaVu Sans", zorder=3)

    ax.text(50, 948, "End-to-End Real-Time Pipeline: Ingestion  -->  ML Tournament  -->  Decoupled 0-100 Risk Engine  -->  TreeSHAP  -->  Gatekeeper Action",
            fontsize=11.2, color="#94a3b8", family="DejaVu Sans", zorder=3)

    # Right Telemetry Badges
    kpis = [
        ("INFERENCE SLA", "< 4.80 ms", "#10b981", "#064e3b", "lightning"),
        ("MODEL RECALL", "100.0%", "#38bdf8", "#0c4a6e", "shield"),
        ("ROC-AUC SCORE", "0.998 / 1.000", "#a855f7", "#3b0764", "chart"),
        ("TEST SUITE", "385 / 385 (100%)", "#fbbf24", "#451a03", "check")
    ]
    for idx, (label, val, col_fg, col_bg, icon_name) in enumerate(kpis):
        kx = 1200 + idx * 168
        draw_card(kx, 940, 156, 70, bg="#0d1830", border=col_bg, lw=1.2, radius=8)
        draw_vector_icon(ax, icon_name, kx + 22, 976, size=14, color=col_fg)
        ax.text(kx + 38, 976, label, ha="left", va="center", fontsize=7.8, fontweight="bold", color="#64748b", family="DejaVu Sans", zorder=3)
        ax.text(kx + 78, 954, val, ha="center", va="center", fontsize=13.0, fontweight="bold", color=col_fg, family="DejaVu Sans", zorder=3)

    ax.plot([50, 1870], [925, 925], color="#1e293b", lw=1.2, zorder=2)

    # -------------------------------------------------------------------------
    # 2. CORE HORIZONTAL 5-STAGE PIPELINE (Y: 410 to 905)
    # -------------------------------------------------------------------------
    stages = [
        {
            "num": "01",
            "phase": "INGESTION & AUDIT",
            "title": "Data Ingestion & Cleanse",
            "accent": "#38bdf8",
            "bg_accent": "#082f49",
            "points": [
                ("Live Payment Ingestion", "UPI, IMPS, Cards, NetBanking streams"),
                ("11-Step Data Integrity", "Automated schema & null constraint audit"),
                ("Zero Target Leakage", "Systematic purge of IDs & target proxies"),
                ("Behavioral Engineering", "26 derived ratios (spending surge, vel, sin/cos)"),
                ("63-Dimensional Matrix", "StandardScaler + OneHotEncoder pipeline")
            ],
            "footer_kpi": "Transformation Latency: 0.90 ms"
        },
        {
            "num": "02",
            "phase": "ML TOURNAMENT",
            "title": "Supervised ML Tournament",
            "accent": "#00d2ff",
            "bg_accent": "#042f2e",
            "points": [
                ("Active Champion Model", "XGBoost (250 trees, depth 5, eta=0.035)"),
                ("Imbalance Compensation", "scale_pos_weight = 17.315 (1:17.3 ratio)"),
                ("Tournament Benchmark", "Evaluated RF (300t), LR (L2), Stacking"),
                ("Perfect Fraud Recall", "100.0% Recall on 4,000 test transactions"),
                ("Probabilistic Output", "Continuous Fraud Likelihood: P in [0.0, 1.0]")
            ],
            "footer_kpi": "Model Inference: 1.15 ms"
        },
        {
            "num": "03",
            "phase": "RISK ENGINE",
            "title": "Decoupled 0-100 Risk Engine",
            "accent": "#fbbf24",
            "bg_accent": "#451a03",
            "points": [
                ("Decoupled from ML Prob", "S = clamp[0, 100](sum S_dimensions)"),
                ("S_ML (0 to 60 pts)", "Piecewise continuous ML curve mapping"),
                ("S_Amount (-4 to 18 pts)", "Deviation vs 30d baseline mean (rebate: -4)"),
                ("S_Velocity (0 to 20 pts)", "1-hour burst frequency acceleration"),
                ("S_Env & Novelty (0 to 25 pts)", "New device, geo jump >50km, nocturnal hr"),
                ("Priority Floor Override", "If P >= 0.70 or Surge >= 50x -> Enforce S >= 75")
            ],
            "footer_kpi": "Scoring Latency: 0.38 ms"
        },
        {
            "num": "04",
            "phase": "EXPLAINABILITY",
            "title": "Real-Time TreeSHAP (XAI)",
            "accent": "#a855f7",
            "bg_accent": "#3b0764",
            "points": [
                ("Black-Box Elimination", "Meets GDPR Article 22 & RBI directives"),
                ("Polynomial Recursion", "O(T * L * D^2) executes in 1.08 milliseconds"),
                ("Axiomatic Exactness", "Local Accuracy: f(x) = phi_0 + sum phi_i(x)"),
                ("Waterfall Attributions", "Spending Surge: +0.420 | Unseen Dev: +0.210"),
                ("Forensic Plain-Language", "Evidence-grounded rationale synthesis")
            ],
            "footer_kpi": "Attribution Latency: 1.08 ms"
        },
        {
            "num": "05",
            "phase": "GATEKEEPER",
            "title": "Pre-Auth Gatekeeper Action",
            "accent": "#10b981",
            "bg_accent": "#064e3b",
            "points": [
                ("LOW RISK (0-30): ALLOW", "Instant clear (<4.8ms), frictionless payment"),
                ("MED RISK (31-70): REVIEW", "Interactive SMS OTP challenge (15m window)"),
                ("HIGH RISK (71-100): BLOCK", "Immediate decline, fund freeze, card lock"),
                ("Autonomous Case Docket", "Automated incident docket & SAR filing"),
                ("Immutable Audit Ledger", "SHA-256 tamper-evident database commit")
            ],
            "footer_kpi": "Total Clearance: 4.80 ms"
        }
    ]

    card_w = 344
    card_h = 490
    card_y = 415

    for i, stg in enumerate(stages):
        card_x = 50 + i * (card_w + 25)
        
        draw_card(card_x, card_y, card_w, card_h, bg="#0d1830", border="#1e2d4d", lw=1.5, radius=12)
        
        # Header strip inside card (top 74px)
        header_rect = patches.FancyBboxPatch(
            (card_x, card_y + card_h - 74), card_w, 74,
            boxstyle="round,pad=0,rounding_size=12",
            fc=stg["bg_accent"], ec="none", zorder=3
        )
        ax.add_patch(header_rect)
        ax.add_patch(patches.Rectangle((card_x, card_y + card_h - 74), card_w, 20, fc=stg["bg_accent"], ec="none", zorder=3))

        # Nested Phase Badge
        draw_pill(card_x + 14, card_y + card_h - 28, 140, 20, f"STAGE {stg['num']} • {stg['phase']}", 
                  bg="#060a17", fg=stg["accent"], border=stg["accent"], fontsize=7.5, bold=True, zorder=4)
        
        # Stage Title
        ax.text(card_x + 16, card_y + card_h - 54, stg["title"],
                fontsize=12.2, fontweight="bold", color="#ffffff", family="DejaVu Sans", zorder=4)

        # Bullet points
        py = card_y + card_h - 100
        for title_b, desc_b in stg["points"]:
            ax.add_patch(patches.Circle((card_x + 20, py - 3), 3.5, fc=stg["accent"], ec="none", zorder=4))
            ax.text(card_x + 32, py, title_b, fontsize=9.8, fontweight="bold", color="#f1f5f9", family="DejaVu Sans", zorder=4)
            ax.text(card_x + 32, py - 18, desc_b, fontsize=8.6, color="#94a3b8", family="DejaVu Sans", zorder=4)
            py -= 42

        # Card Footer Divider & Latency KPI
        ax.plot([card_x + 14, card_x + card_w - 14], [card_y + 44, card_y + 44], color="#1e2d4d", lw=1, zorder=3)
        
        draw_pill(card_x + 16, card_y + 12, card_w - 32, 24, stg["footer_kpi"], 
                  bg="#060a17", fg=stg["accent"], border="#1e2d4d", fontsize=9.0, bold=True, zorder=4)

        if i < len(stages) - 1:
            ax.annotate(
                "", xy=(card_x + card_w + 21, card_y + card_h/2),
                xytext=(card_x + card_w + 4, card_y + card_h/2),
                arrowprops=dict(arrowstyle="-|>", lw=2.4, color=stg["accent"], mutation_scale=15),
                zorder=5
            )

    # -------------------------------------------------------------------------
    # 3. BOTTOM MULTI-TENANT PERSONA WORKFLOWS (Y: 40 to 370)
    # -------------------------------------------------------------------------
    ax.text(50, 372, "MULTI-TENANT PERSONA WORKSPACE & GOVERNANCE ECOSYSTEM", 
            fontsize=13.5, fontweight="bold", color="#ffffff", family="DejaVu Sans", zorder=3)
    ax.text(50, 352, "Strict Role-Based Access Control (RBAC)  •  Zero Customer Data Leakage  •  Full SOC Auditing Telemetry",
            fontsize=10.0, color="#64748b", family="DejaVu Sans", zorder=3)

    personas = [
        {
            "role": "ROLE: CUSTOMER",
            "title": "Frictionless Checkout & Adaptive SMS OTP",
            "icon_type": "user",
            "accent": "#10b981",
            "bg": "#0a1f18",
            "items": [
                ("94.5% Baseline Clean Clearance", "Sub-5ms seamless approval with zero false declines."),
                ("Step-Up Security Push", "Slide-down smartphone SMS OTP banner for review-tier holds."),
                ("Transparent Safety Receipts", "Plain-language summaries of payment security checks."),
                ("PCI-DSS / GDPR Tenant Scoping", "Zero access to external customer accounts or telemetry.")
            ]
        },
        {
            "role": "ROLE: INVESTIGATOR",
            "title": "Forensic Command Center & AI Copilot",
            "icon_type": "shield",
            "accent": "#38bdf8",
            "bg": "#08263e",
            "items": [
                ("3-Panel Case Command", "Live Telemetry, WebSocket radar stream, and dossier workspace."),
                ("Autonomous AI Copilot", "Google Gemini 1.5 Pro & xAI Grok-2 forensic kill-chain synthesis."),
                ("Game-Theoretic Waterfall", "Exact TreeSHAP feature attributions with interactive radar graphs."),
                ("One-Click FinCEN SAR Filing", "Pre-drafted regulatory Suspicious Activity Reports in seconds.")
            ]
        },
        {
            "role": "ROLE: ADMINISTRATOR",
            "title": "Model Lab, Concept Drift & Audit Ledger",
            "icon_type": "gear",
            "accent": "#a855f7",
            "bg": "#210f38",
            "items": [
                ("Real-Time Model Lab", "Live candidate tournament benchmarking and challenger hot-swapping."),
                ("Automated Drift Surveillance", "Population Stability Index (PSI > 0.25 triggers retrain alert)."),
                ("29-Merchant Surveillance", "Live fleet risk tracking across Tamil Nadu & Karnataka retailers."),
                ("Immutable Cryptographic Ledger", "Tamper-evident SHA-256 hashed state logs (SQLite WAL Mode).")
            ]
        }
    ]

    p_w = 584
    p_h = 285
    p_y = 48

    for j, p in enumerate(personas):
        px = 50 + j * (p_w + 34)
        draw_card(px, p_y, p_w, p_h, bg="#0d1830", border=p["accent"], lw=1.2, radius=10)
        
        draw_pill(px + 16, p_y + p_h - 36, 160, 22, p["role"], bg=p["bg"], fg=p["accent"], border=p["accent"], fontsize=8.0, bold=True, zorder=4)
        draw_vector_icon(ax, p["icon_type"], px + 26, p_y + p_h - 58, size=18, color=p["accent"])
        ax.text(px + 44, p_y + p_h - 58, p["title"], fontsize=12.0, fontweight="bold", color="#ffffff", family="DejaVu Sans", zorder=4)

        item_y = p_y + p_h - 96
        for title_i, desc_i in p["items"]:
            ax.text(px + 20, item_y, f"[+] {title_i}:", fontsize=9.8, fontweight="bold", color=p["accent"], family="DejaVu Sans", zorder=4)
            ax.text(px + 20, item_y - 17, desc_i, fontsize=9.0, color="#cbd5e1", family="DejaVu Sans", zorder=4)
            item_y -= 43

        draw_pill(px + 16, p_y + 12, p_w - 32, 22, "ACCESS CONTROL: ENFORCED VIA JWT SCOPE", bg="#060a17", fg="#64748b", border="#1e2d4d", fontsize=8.0, bold=False, zorder=4)

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(PNG_PATH, dpi=100, facecolor=fig.get_facecolor(), edgecolor="none")
    fig.savefig(SVG_PATH, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)

    shutil.copy2(PNG_PATH, ALT_PNG_PATH)
    shutil.copy2(SVG_PATH, ALT_SVG_PATH)

    print("Success: Visual 01 refined successfully.")

if __name__ == "__main__":
    create_visual_01()
