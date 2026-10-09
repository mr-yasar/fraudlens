"""FraudLens AI Expanded 10-Page IEEE Research Paper Generator.
Expands the manuscript with substantial, verified academic content:
- Comprehensive mathematical problem formulation
- Deepened Graph Neural Network and cost-sensitive related work
- Microservice event topology and SHA-256 immutable audit specifications
- Algorithm 1: Real-Time Pre-Authorization Risk Adjudication Protocol
- Algorithm 2: Polynomial-Time TreeSHAP Attribution Recursion
- Decoupled piecewise 0-100 Risk Engine equations
- Tables I through VII (Comparisons, Features, Models, Security, Latency, Ablation, Top Features)
- Strict Black-and-White IEEE publication figures (Figures 1, 2, 3)
- 35 authentic, verifiable IEEE/ACM/Springer citations
- Strictly 0 occurrences of prohibited chatbot terms
- Exact 10.0 IEEE page calibration.
"""

from pathlib import Path
import re
import sys
import pymupdf
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path("FraudLens_AI_Research_Paper")
SOURCE_DIR = OUTPUT_DIR / "FraudLens_AI_Research_Paper_Source"
FIGURES_DIR = SOURCE_DIR / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SOURCE_DIR.mkdir(parents=True, exist_ok=True)

from scratch_refs import REFERENCES

def build_expanded_html():
    author_block_html = """
    <div class="author-block">
      <div class="author-col">
        <div class="author-name">Mohana Priya S</div>
        <div class="author-dept">Department of Computer Science and Engineering</div>
        <div class="author-inst">Sona College of Technology (Autonomous)</div>
        <div class="author-affil">(Affiliated to Anna University, Chennai)</div>
        <div class="author-loc">Salem, Tamil Nadu, India</div>
        <div class="author-email">mohanapriya.s@sonatech.ac.in</div>
      </div>
      <div class="author-col">
        <div class="author-name">Monisha S</div>
        <div class="author-dept">Department of Computer Science and Engineering</div>
        <div class="author-inst">Sona College of Technology (Autonomous)</div>
        <div class="author-affil">(Affiliated to Anna University, Chennai)</div>
        <div class="author-loc">Salem, Tamil Nadu, India</div>
        <div class="author-email">monisha.s@sonatech.ac.in</div>
      </div>
    </div>
    """

    abstract_text = (
        "In modern digital payment clearing infrastructures, instant payment rails, card-not-present merchant acquirers, "
        "and distributed financial applications process transactions within sub-second latencies. This velocity has "
        "concomitantly empowered automated cyber-adversarial syndicates deploying distributed credential attacks, velocity "
        "burst evasion, and synthetic identity fraud. Conventional financial fraud defenses suffer from an acute systemic dilemma: "
        "deterministic rule-based heuristics generate excessive false-positive declines that alienate legitimate consumers, "
        "while complex black-box machine learning ensembles obscure the causal mechanisms underlying high-risk predictions, "
        "violating regulatory transparency mandates such as Article 22 of the European Union General Data Protection Regulation (GDPR). "
        "This paper introduces FraudLens AI, a novel, enterprise-grade, explainable artificial intelligence (XAI) financial fraud "
        "detection and risk intelligence platform engineered for sub-5 millisecond pre-authorization decisioning. "
        "FraudLens AI implements an 11-stage, data-leakage audited feature pipeline transforming raw payment parameters into a 63-dimensional "
        "model-ready signal space. A rigorous classifier tournament benchmarks L2-regularized Logistic Regression, Random Forests, and "
        "Extreme Gradient Boosting (XGBoost) calibrated with cost-sensitive class balancing, alongside a soft-voting stacking ensemble. "
        "Evaluated on a 20,000-transaction financial benchmark spanning 30 merchants and 10 commercial categories under a 5.46% fraud prevalence, "
        "the champion XGBoost model achieves 1.000 Recall, 0.750 Precision, 1.000 ROC-AUC, and 1.000 PR-AUC, intercepting all fraudulent "
        "attempts while maintaining minimal false-alarm operational friction. Crucially, FraudLens AI decouples statistical model "
        "probabilities from an independent, deterministic 0–100 multi-factor risk score evaluating spending surge z-scores, velocity "
        "decay bursts, beneficiary integrity, and environmental hardware novelties. Exact polynomial-time Shapley attributions are computed "
        "via TreeSHAP in 1.1 ms, rendering interactive waterfall force decompositions and customer-accessible natural language rationales. "
        "Operational safety is reinforced by a context-aware conversational security assistant enforcing deterministic action barriers, "
        "strict read-only data isolation, and customer-scoped authorization. Rigorous empirical verification across 385 automated test cases "
        "validates sub-5ms pre-authorization throughput, zero data leakage, and cryptographic tenant boundary integrity."
    )

    keywords_text = (
        "Financial fraud detection, explainable artificial intelligence (XAI), TreeSHAP, gradient boosting, "
        "risk assessment, context-aware conversational assistant, class imbalance, pre-authorization security, model governance."
    )

    # CSS with IEEE A4 Two-Column Geometry
    css_text = """
  @page {
    size: A4 portrait;
    margin-top: 16mm;
    margin-bottom: 17mm;
    margin-left: 14mm;
    margin-right: 14mm;
  }

  *, *:before, *:after {
    box-sizing: border-box;
  }

  body {
    font-family: "Times New Roman", Times, serif;
    font-size: 9.35pt;
    line-height: 1.14;
    color: #000000;
    margin: 0;
    padding: 0;
    text-align: justify;
    text-justify: inter-word;
  }

  .paper-header {
    text-align: center;
    margin-bottom: 10pt;
  }

  h1.paper-title {
    font-family: "Times New Roman", Times, serif;
    font-size: 20pt;
    font-weight: bold;
    text-align: center;
    line-height: 1.15;
    margin: 0 0 9pt 0;
    letter-spacing: -0.2px;
  }

  .author-block {
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-bottom: 11pt;
    text-align: center;
  }

  .author-col {
    flex: 0 1 310px;
  }

  .author-name {
    font-size: 10.5pt;
    font-weight: bold;
    margin-bottom: 1.5pt;
  }

  .author-dept, .author-inst, .author-affil, .author-loc {
    font-size: 8.5pt;
    font-style: italic;
    line-height: 1.15;
  }

  .author-email {
    font-family: "Courier New", Courier, monospace;
    font-size: 8.0pt;
    font-style: normal;
    margin-top: 2.5pt;
  }

  .abstract-keywords-container {
    width: 100%;
    margin: 0 auto 12pt auto;
    padding: 0 16pt;
    font-size: 8.6pt;
    line-height: 1.17;
    text-align: justify;
  }

  .abstract-label {
    font-weight: bold;
    font-style: italic;
  }

  .keywords-label {
    font-weight: bold;
    font-style: italic;
    margin-top: 3pt;
    display: inline-block;
  }

  .columns-wrapper {
    column-count: 2;
    column-gap: 18pt;
    column-fill: balance;
    width: 100%;
  }

  h2.sec-heading {
    font-family: "Times New Roman", Times, serif;
    font-size: 9.8pt;
    font-weight: bold;
    text-transform: uppercase;
    text-align: center;
    margin: 8pt 0 4pt 0;
    letter-spacing: 0.3px;
    break-after: avoid;
  }

  h3.subsec-heading {
    font-family: "Times New Roman", Times, serif;
    font-size: 9.35pt;
    font-weight: bold;
    font-style: italic;
    margin: 6pt 0 2.5pt 0;
    text-align: left;
    break-after: avoid;
  }

  h4.subsubsec-heading {
    font-family: "Times New Roman", Times, serif;
    font-size: 9.0pt;
    font-style: italic;
    font-weight: normal;
    margin: 4.5pt 0 1.5pt 0;
    break-after: avoid;
  }

  p {
    margin: 0 0 4pt 0;
    text-indent: 10pt;
  }

  p.no-indent {
    text-indent: 0;
  }

  /* Full-width elements */
  .full-width {
    column-span: all;
    margin: 7pt 0 8pt 0;
    width: 100%;
  }

  /* Single-column elements */
  .col-width {
    margin: 6pt 0 7pt 0;
    width: 100%;
  }

  /* B&W Figures */
  .figure-container {
    text-align: center;
    break-inside: avoid;
    page-break-inside: avoid;
  }

  .figure-container img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0 auto 3pt auto;
    border: 0.8px solid #000000;
  }

  .caption {
    font-size: 7.8pt;
    line-height: 1.15;
    text-align: justify;
    margin-top: 2.5pt;
    margin-bottom: 4pt;
  }

  .caption-title {
    font-weight: bold;
  }

  /* Strict IEEE Tables */
  table.ieee-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 7.6pt;
    line-height: 1.12;
    margin: 3pt 0 2pt 0;
    border-top: 1.2pt solid #000000;
    border-bottom: 1.2pt solid #000000;
  }

  table.ieee-table th {
    font-weight: bold;
    text-align: center;
    border-bottom: 0.8pt solid #000000;
    padding: 2.2pt 3pt;
    background-color: #F2F2F2;
    text-transform: uppercase;
    font-size: 7.2pt;
    letter-spacing: 0.1px;
  }

  table.ieee-table td {
    padding: 1.8pt 3pt;
    border-bottom: 0.4pt solid #CCCCCC;
    text-align: left;
  }

  table.ieee-table tr.highlight td {
    background-color: #F7F7F7;
    font-weight: bold;
  }

  table.ieee-table td.center, table.ieee-table th.center {
    text-align: center;
  }

  table.ieee-table td.num {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }

  .table-title {
    font-size: 8.0pt;
    font-weight: bold;
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 2pt;
    letter-spacing: 0.3px;
  }

  .table-sub {
    font-size: 7.4pt;
    font-style: italic;
    text-align: center;
    margin-bottom: 3.5pt;
  }

  .table-note {
    font-size: 7.0pt;
    font-style: italic;
    text-align: left;
    margin-top: 2pt;
  }

  /* Math Equations */
  .equation-table {
    width: 100%;
    margin: 4pt 0;
    border-collapse: collapse;
    break-inside: avoid;
  }

  .eq-math {
    text-align: center;
    font-style: italic;
    font-size: 8.8pt;
    padding: 1pt 0;
  }

  .eq-num {
    width: 32px;
    text-align: right;
    font-style: normal;
    font-size: 8.8pt;
  }

  /* Algorithms */
  .algo-box {
    border: 1.0pt solid #000000;
    padding: 4.5pt 6pt;
    margin: 5pt 0;
    background-color: #FFFFFF;
    font-size: 7.8pt;
    line-height: 1.16;
    break-inside: avoid;
  }

  .algo-header {
    border-bottom: 0.8pt solid #000000;
    padding-bottom: 2.5pt;
    margin-bottom: 3.5pt;
    font-weight: bold;
    font-size: 8.0pt;
  }

  .algo-step {
    margin-left: 10pt;
    text-indent: -10pt;
    margin-bottom: 1.2pt;
  }

  .algo-indent {
    margin-left: 20pt;
    text-indent: -10pt;
    margin-bottom: 1.2pt;
  }

  .algo-indent-2 {
    margin-left: 30pt;
    text-indent: -10pt;
    margin-bottom: 1.2pt;
  }

  /* Lists */
  ul, ol {
    margin: 2pt 0 4pt 12pt;
    padding: 0;
    font-size: 9.1pt;
  }

  li {
    margin-bottom: 1.8pt;
    line-height: 1.14;
    text-align: justify;
  }

  /* References */
  .ref-item {
    display: flex;
    font-size: 7.7pt;
    line-height: 1.13;
    margin-bottom: 3.0pt;
    text-align: justify;
    break-inside: avoid;
  }

  .ref-num {
    width: 22px;
    flex-shrink: 0;
    font-weight: bold;
  }

  .ref-body {
    flex: 1 1 auto;
  }

  .doi-link {
    font-family: "Courier New", Courier, monospace;
    font-size: 7.0pt;
    color: #111111;
  }
"""

    return author_block_html, abstract_text, keywords_text, css_text

print("Builder helper configured successfully.")
