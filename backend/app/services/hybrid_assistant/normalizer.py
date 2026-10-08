"""Query Normalization, Typo Correction, and Entity Extraction Layer.

Implements Phases 08 and 09 of the 24-Phase Chatbot Remodel:
- Token normalization (casing, punctuation, whitespace, slang)
- Domain spell correction (e.g. shapp -> shap, xg boost -> xgboost)
- Strict regex entity extraction (Transaction IDs, Customer IDs/names, Case IDs)
- Relative reference & intent clue identification (e.g. why, highest, compare)
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from backend.app.services.hybrid_assistant.taxonomy import EntityBundle


# Common domain typo & variation correction dictionary
SPELL_CORRECTIONS = {
    r"\bshapp\b": "shap",
    r"\bshaap\b": "shap",
    r"\bxg\s*boost\b": "xgboost",
    r"\brandom\s*forests?\b": "random forest",
    r"\blogistic\s*regressions?\b": "logistic regression",
    r"\bmonisa\b": "monisha",
    r"\bmonish\b": "monisha",
    r"\bmohanaa\b": "mohana",
    r"\bsowmya\b": "sowmiya",
    r"\bprobablity\b": "probability",
    r"\bprobabilty\b": "probability",
    r"\btransction\b": "transaction",
    r"\btranscations?\b": "transaction",
    r"\btxns?\b": "transaction",
    r"\btxs?\b": "transaction",
    r"\binvestgator\b": "investigator",
    r"\binvestgations?\b": "investigation",
    r"\bexplaintion\b": "explanation",
    r"\bexplaination\b": "explanation",
    r"\balgos?\b": "algorithm",
    r"\brbca\b": "rbac",
    r"\bsarr\b": "sar",
    r"\bwater fall\b": "waterfall",
    r"\bpre auth\b": "pre-auth",
    r"\bpreauthorization\b": "pre-auth",
    r"\bstep up\b": "step-up",
    r"\bnovamart\b": "novamart fresh",
    r"\baurelia\b": "aurelia gold house",
}

# Domain synonym canonicalization map
SYNONYM_REPLACEMENTS = {
    r"\bwhy\s+is\s+it\s+high\b": "why is this high risk",
    r"\bwhy\s+high\b": "why is this high risk",
    r"\brisk\?\b": "what is risk score",
    r"\bwhat\s+is\s+shap\?\b": "what is shap",
    r"\bhow\s+admin\s+works\b": "what is the purpose of the admin module",
    r"\bhow\s+investigator\s+works\b": "what is the fraud investigator role",
}

# Regex entity extractors
TX_PATTERN = re.compile(r"\b(TX(?:N)?(?:_|-)?(?:[A-Za-z0-9_]{3,36}))\b", re.IGNORECASE)
CUST_ID_PATTERN = re.compile(r"\b(CUST(?:_|-)?(?:[A-Za-z0-9_]{3,24}))\b", re.IGNORECASE)
CASE_ID_PATTERN = re.compile(r"\b(CASE(?:_|-)?(?:[A-Za-z0-9_]{3,24}))\b", re.IGNORECASE)
KNOWN_CUSTOMERS = ["monisha", "mohana", "sowmiya"]
KNOWN_MERCHANTS = [
    "novamart fresh", "dailymart supermarket", "naturebasket",
    "circuitbay electronics", "electroworld", "techgizmo",
    "fashionfirst boutique", "trendz apparel", "stylehub",
    "spicegarden bistro", "foodexpress", "curryleaf cafe",
    "fasttrack travels", "skyway airlines", "railexpress",
    "cinemagic multiplex", "playzone gaming", "streamhub",
    "medicare plus", "apollo pharmacy", "healthfirst",
    "aurelia gold house", "diamondcraft", "luxegems",
    "bharat petroleum", "indianoil auto", "hp fuelstop",
    "powergrid electric", "aquapure water", "gasline corp"
]


def normalize_query_text(raw_query: str) -> str:
    """Normalize text by lowercasing, stripping extra whitespace, and fixing typos."""
    if not raw_query:
        return ""
    
    text = raw_query.strip().lower()

    # Apply spell correction patterns
    for pattern, replacement in SPELL_CORRECTIONS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Check for direct phrase canonical replacements
    for pattern, replacement in SYNONYM_REPLACEMENTS.items():
        if re.search(pattern, text, flags=re.IGNORECASE):
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Strip trailing punctuation (?, ., !) and normalize whitespace
    text = text.rstrip(" ?.!").strip()
    text = re.sub(r"[\s\t\n]+", " ", text).strip()
    return text


def extract_entities(query: str, conversation_context: Optional[Dict[str, Any]] = None) -> EntityBundle:
    """Extract validated entities and semantic clues from the normalized query string."""
    norm_query = normalize_query_text(query)
    bundle = EntityBundle()

    # 1. Transaction IDs
    for match in TX_PATTERN.finditer(query):
        val = match.group(1).upper()
        if val not in bundle.transaction_ids:
            bundle.transaction_ids.append(val)

    # Context inheritance: If query asks "why is it high risk" or "explain it" and has context
    if not bundle.transaction_ids and conversation_context:
        ctx_tx = conversation_context.get("last_transaction_id") or conversation_context.get("current_tx_id")
        if ctx_tx:
            bundle.transaction_ids.append(str(ctx_tx).upper())

    # 2. Customer IDs and Names
    for match in CUST_ID_PATTERN.finditer(query):
        val = match.group(1).upper()
        if val not in bundle.customer_ids:
            bundle.customer_ids.append(val)

    for cname in KNOWN_CUSTOMERS:
        if re.search(rf"\b{cname}\b", norm_query, re.IGNORECASE):
            if cname.capitalize() not in bundle.customer_names:
                bundle.customer_names.append(cname.capitalize())

    # Context inheritance for customer
    if not bundle.customer_ids and not bundle.customer_names and conversation_context:
        ctx_cust = conversation_context.get("last_customer_id")
        if ctx_cust:
            bundle.customer_ids.append(str(ctx_cust).upper())

    # 3. Case IDs
    for match in CASE_ID_PATTERN.finditer(query):
        val = match.group(1).upper()
        if val not in bundle.case_ids:
            bundle.case_ids.append(val)

    # 4. Merchant Names
    for mname in KNOWN_MERCHANTS:
        if mname in norm_query:
            if mname not in bundle.merchant_names:
                bundle.merchant_names.append(mname)

    # 5. Amounts
    amt_matches = re.finditer(r"(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:₹|rs|rupees|inr)?", query, re.IGNORECASE)
    for m in amt_matches:
        num_str = m.group(1).replace(",", "")
        try:
            val = float(num_str)
            if val > 0:
                bundle.amounts.append(val)
        except ValueError:
            pass

    # 6. Risk Level references
    if re.search(r"\bhigh\s*risk\b|\bcritical\b", norm_query):
        bundle.risk_levels.append("HIGH")
    if re.search(r"\bmedium\s*risk\b|\bmoderate\b", norm_query):
        bundle.risk_levels.append("MEDIUM")
    if re.search(r"\blow\s*risk\b|\bsafe\b", norm_query):
        bundle.risk_levels.append("LOW")

    # 7. Semantic Clues
    bundle.is_why_question = bool(re.search(r"\b(why|reason|explain|what caused|factors)\b", norm_query))
    bundle.is_ranking_request = bool(re.search(r"\b(highest|top|most|worst|rank|highest-risk)\b", norm_query))
    bundle.is_comparison_request = bool(re.search(r"\b(compare|difference between|versus|vs)\b", norm_query))

    bundle.raw_entities = {
        "transaction_count": len(bundle.transaction_ids),
        "customer_count": len(bundle.customer_ids) + len(bundle.customer_names),
        "has_target_object": bool(bundle.transaction_ids or bundle.customer_ids or bundle.case_ids),
    }

    return bundle
