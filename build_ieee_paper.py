"""FraudLens AI IEEE Research Paper Generator & Verifier.
Generates:
1. High-fidelity IEEE A4 2-column HTML template and stylesheet
2. PDF rendering via Playwright with exact 9-page balancing
3. DOCX generation via python-docx
4. Automated verification suite:
   - Strictly 0 occurrences of prohibited chatbot acronym/terms
   - Verifies citation ordering [1]-[25]
   - Audits page count == 9
   - Verifies author details against supplied document
5. Validation and Research Integrity Report
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
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

OUTPUT_DIR = Path("FraudLens_AI_Research_Paper")
SOURCE_DIR = OUTPUT_DIR / "FraudLens_AI_Research_Paper_Source"
FIGURES_DIR = SOURCE_DIR / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SOURCE_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. MANUSCRIPT TEXT CONTENT DEFINITION
# -----------------------------------------------------------------------------

TITLE = "FraudLens AI: Explainable AI-Based Financial Fraud and Risk Detection System"

AUTHORS = [
    {
        "name": "Mohana Priya S",
        "dept": "Department of Computer Science and Engineering",
        "institution": "Sona College of Technology (Autonomous)",
        "affiliation_extra": "(Affiliated to Anna University, Chennai)",
        "location": "Salem, Tamil Nadu, India",
        "email": "mohanapriya.s@sonatech.ac.in",
    },
    {
        "name": "Monisha S",
        "dept": "Department of Computer Science and Engineering",
        "institution": "Sona College of Technology (Autonomous)",
        "affiliation_extra": "(Affiliated to Anna University, Chennai)",
        "location": "Salem, Tamil Nadu, India",
        "email": "monisha.s@sonatech.ac.in",
    },
]

ABSTRACT = (
    "In the modern digital economy, instantaneous payment rails such as real-time card clearing, "
    "merchant point-of-sale gateways, and rapid digital settlement services have dramatically accelerated "
    "financial transaction velocity. Concurrently, these platforms have catalyzed sophisticated, automated "
    "fraud syndicates deploying distributed credential attacks, velocity burst evasion, and account takeover botnets. "
    "Traditional fraud prevention systems suffer from a severe trade-off: deterministic rule-based engines produce "
    "excessive false-positive friction, while black-box machine learning models obscure the causal factors behind "
    "high-risk classifications, violating regulatory transparency directives such as the European Union General "
    "Data Protection Regulation (GDPR) Article 22. This paper presents FraudLens AI, an enterprise-grade, "
    "explainable artificial intelligence financial fraud detection and risk intelligence platform. "
    "FraudLens AI integrates an 11-step leakage-audited preprocessing pipeline that transforms raw transaction "
    "parameters into 63 model-ready numerical and categorical signals. A supervised classifier tournament evaluates "
    "regularized Logistic Regression, Random Forest, and Extreme Gradient Boosting (XGBoost) with class-imbalance "
    "calibration, alongside a soft-voting stacking ensemble. Evaluated on a 20,000-transaction benchmark dataset "
    "comprising 30 heterogeneous merchants across 10 commercial categories with a 5.46% fraud rate, the champion "
    "XGBoost model achieves a test recall of 1.000, precision of 0.750, ROC-AUC of 1.000, and PR-AUC of 1.000, "
    "capturing all fraudulent transfers while maintaining low operational friction. "
    "Crucially, the system decouples model fraud probability (0.0–1.0) from an independent deterministic 0–100 risk score "
    "evaluating spending baseline surges, velocity bursts, beneficiary integrity, and environmental hardware novelties. "
    "TreeSHAP calculates exact, polynomial-time Shapley attributions in 1.1 ms, rendering interactive waterfall "
    "decompositions and customer-safe natural language summaries. Operational safety is reinforced by a context-aware "
    "conversational security assistant enforcing strict read-only safeguards, server-side data isolation, and live tool "
    "execution. Comprehensive empirical verification across 385 automated software test cases confirms sub-5ms "
    "pre-authorization decisioning, zero data leakage, and rigorous tenant boundary integrity."
)

INDEX_TERMS = [
    "Financial fraud detection",
    "explainable artificial intelligence (XAI)",
    "TreeSHAP",
    "gradient boosting",
    "risk assessment",
    "context-aware conversational assistant",
    "class imbalance",
    "pre-authorization security",
]

# Section texts, detailed and academic
# We will construct the complete text blocks for all sections
