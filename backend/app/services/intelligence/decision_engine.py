"""Model Decision Engine — Autonomous AI Routing (Gemini-First Architecture).

Sections 1, 2, 3, 4, 5, 6, 20, 28, 31 compliance:
- DO NOT hard-code rigid model maps (Simple -> Gemini, Complex -> Grok).
- Gemini receives the question first and determines what intelligence is required.
- Model Choices:
  1. Primary: Gemini 3.6
  2. Deep Reasoning Escalation: Gemini 3.7 (rare, justified by actual reasoning difficulty)
  3. Complementary AI #1: Grok (independent review, challenging assumptions, alternative views)
  4. Complementary AI #2: Mistral (3rd engine, independent challenger, alternate reasoning)
  5. FORBIDDEN: Gemini 3.8 (strictly blocked and prohibited)
- Decisions: DIRECT_ANSWER | ESCALATE_GEMINI_3_7 | CALL_GROK | CALL_MISTRAL | CALL_BOTH
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from backend.app.services.intelligence.manipulation_guard import ManipulationAssessment

logger = logging.getLogger("fraudlens.intelligence.decision_engine")


class RoutingAction(str, Enum):
    DIRECT_ANSWER      = "DIRECT_ANSWER"        # Gemini 3.6 answers directly
    ESCALATE_GEMINI_3_7 = "ESCALATE_GEMINI_3_7"  # Deep reasoning escalation
    CALL_GROK          = "CALL_GROK"            # xAI Grok independent review
    CALL_MISTRAL       = "CALL_MISTRAL"          # Mistral AI independent review
    CALL_BOTH          = "CALL_BOTH"            # Gemini 3.7 + Grok combined review & synthesis


@dataclass
class RoutingDecision:
    action: RoutingAction
    rationale: str
    complexity_level: str  # "LOW", "MODERATE", "HIGH", "EXTREME"
    intent: str
    requires_evidence: bool
    requires_grok_challenge: bool
    model_chain: List[str]


class ModelDecisionEngine:
    """Evaluates incoming queries to determine the optimal intelligence pipeline."""

    @classmethod
    def evaluate(
        cls,
        query: str,
        manipulation: ManipulationAssessment,
        user_role: Optional[str] = None,
        context_hint: Optional[str] = None,
        force_provider: Optional[str] = None,
    ) -> RoutingDecision:
        """Autonomous evaluation of query intent, complexity, and intelligence requirement.

        Honors explicit user override if requested, otherwise uses Gemini-first autonomous routing.
        """
        q_lower = query.lower().strip()

        # Deep reasoning signals (genuinely heavy/complex reasoning warrants Gemini 3.7)
        deep_reasoning_triggers = [
            r"\b(?:multi-step|step-by-step|deep\s+forensic|contradictory|conflicting\s+signals)\b",
            r"\b(?:waterfall\s+decomposition|game-theoretic|shapley\s+math|shap\s+waterfall)\b",
            r"\b(?:statistical\s+divergence|z-score\s+deviation|roc-auc\s+tradeoff)\b",
            r"\b(?:cross-city\s+velocity|botnet\s+correlation|cluster\s+graph)\b",
            r"\b(?:audit\s+trail\s+adjudication|regulatory\s+sar\s+justification)\b",
        ]

        # Independent challenge signals (Grok/Mistral complementary review)
        grok_challenge_triggers = [
            r"\b(?:second\s+opinion|alternative\s+view|challenge|cross-model|verify\s+conclusion)\b",
            r"\b(?:disagree|devil's\s+advocate|opposing\s+argument|red\s+team)\b",
            r"\b(?:is\s+the\s+model\s+wrong|false\s+decline\s+risk|dispute\s+adjudication)\b",
        ]

        # Mistral-specific triggers (alternative perspective / French AI / 3rd opinion)
        mistral_triggers = [
            r"\b(?:mistral|alternative\s+ai|third\s+opinion|another\s+perspective)\b",
            r"\b(?:french\s+ai|open\s+source\s+view|independent\s+llm)\b",
        ]

        has_deep_trigger    = any(re.search(pat, q_lower) for pat in deep_reasoning_triggers)
        has_grok_trigger    = any(re.search(pat, q_lower) for pat in grok_challenge_triggers)
        has_mistral_trigger = any(re.search(pat, q_lower) for pat in mistral_triggers)

        # ── 1. EXPLICIT PROVIDER OVERRIDE (User-Selected MANUAL MODES) ──
        if force_provider and force_provider.lower().strip() not in ("auto", "none", ""):
            fp = force_provider.lower().strip()

            if fp == "grok":
                return RoutingDecision(
                    action=RoutingAction.CALL_GROK,
                    rationale="User explicitly selected xAI Grok manual engine.",
                    complexity_level="MODERATE",
                    intent="user_specified",
                    requires_evidence=True,
                    requires_grok_challenge=True,
                    model_chain=["grok-2"],
                )

            elif fp == "mistral":
                return RoutingDecision(
                    action=RoutingAction.CALL_MISTRAL,
                    rationale="User explicitly selected Mistral AI manual engine.",
                    complexity_level="MODERATE",
                    intent="user_specified",
                    requires_evidence=True,
                    requires_grok_challenge=False,
                    model_chain=["open-mistral-7b"],
                )

            elif fp in ("gemini_deep", "gemini-3.7", "gemini_3.7"):
                return RoutingDecision(
                    action=RoutingAction.ESCALATE_GEMINI_3_7,
                    rationale="User explicitly requested Gemini 3.7 Deep Reasoning engine.",
                    complexity_level="HIGH",
                    intent="user_specified",
                    requires_evidence=True,
                    requires_grok_challenge=False,
                    model_chain=["gemini-3.7-flash"],
                )

            elif fp == "gemini":
                # In Gemini manual mode: use Gemini 3.7 only for genuinely heavy reasoning, else 3.6 default
                if has_deep_trigger:
                    return RoutingDecision(
                        action=RoutingAction.ESCALATE_GEMINI_3_7,
                        rationale="Gemini manual mode: Heavy/complex forensic query routed to Gemini 3.7 Deep Reasoning.",
                        complexity_level="HIGH",
                        intent="user_specified",
                        requires_evidence=True,
                        requires_grok_challenge=False,
                        model_chain=["gemini-3.7-flash"],
                    )
                return RoutingDecision(
                    action=RoutingAction.DIRECT_ANSWER,
                    rationale="Gemini manual mode: Standard inquiry handled by primary Gemini 3.6.",
                    complexity_level="LOW",
                    intent="user_specified",
                    requires_evidence=True,
                    requires_grok_challenge=False,
                    model_chain=["gemini-3.6-flash"],
                )

        # ── 2. AUTONOMOUS REASONING & COMPLEXITY ASSESSMENT (AUTO MODE) ──

        # Adversarial / manipulation requires independent review
        if manipulation.is_manipulative or manipulation.is_prompt_injection:
            return RoutingDecision(
                action=RoutingAction.CALL_BOTH if has_deep_trigger else RoutingAction.CALL_GROK,
                rationale="Manipulative or forced conclusion detected: Grok independent adversarial review engaged.",
                complexity_level="HIGH",
                intent="adversarial_defense",
                requires_evidence=True,
                requires_grok_challenge=True,
                model_chain=["gemini-3.6-flash", "grok-2", "gemini-3.6-flash"],
            )

        # Explicit Mistral request
        if has_mistral_trigger:
            return RoutingDecision(
                action=RoutingAction.CALL_MISTRAL,
                rationale="Mistral AI requested as alternative independent intelligence engine.",
                complexity_level="MODERATE",
                intent="mistral_independent_review",
                requires_evidence=True,
                requires_grok_challenge=False,
                model_chain=["open-mistral-7b"],
            )

        # Combined Deep Reasoning + Independent Review (Section 7 criteria)
        if has_deep_trigger and has_grok_trigger:
            return RoutingDecision(
                action=RoutingAction.CALL_BOTH,
                rationale="Complex multi-step forensic query with request for independent challenge: Gemini 3.7 + Grok deployed.",
                complexity_level="EXTREME",
                intent="forensic_multi_llm_synthesis",
                requires_evidence=True,
                requires_grok_challenge=True,
                model_chain=["gemini-3.7-flash", "grok-2", "gemini-3.7-flash"],
            )

        # Gemini 3.7 Escalation (Section 5: rare, justified by true reasoning difficulty)
        if has_deep_trigger:
            return RoutingDecision(
                action=RoutingAction.ESCALATE_GEMINI_3_7,
                rationale="High reasoning complexity (TreeSHAP math, multi-step forensic evidence): Escalated to Gemini 3.7.",
                complexity_level="HIGH",
                intent="deep_forensic_reasoning",
                requires_evidence=True,
                requires_grok_challenge=False,
                model_chain=["gemini-3.7-flash"],
            )

        # Grok Review (Section 6: independent second opinion or challenge)
        if has_grok_trigger:
            return RoutingDecision(
                action=RoutingAction.CALL_GROK,
                rationale="Request for independent second opinion or alternative interpretation: Delegated to xAI Grok.",
                complexity_level="MODERATE",
                intent="independent_verification",
                requires_evidence=True,
                requires_grok_challenge=True,
                model_chain=["grok-2"],
            )

        # Default Primary: Gemini 3.6 (Section 3: primary brain)
        return RoutingDecision(
            action=RoutingAction.DIRECT_ANSWER,
            rationale="Standard domain inquiry: Handled directly and swiftly by primary Gemini 3.6.",
            complexity_level="LOW",
            intent="standard_assistance",
            requires_evidence=True,
            requires_grok_challenge=False,
            model_chain=["gemini-3.6-flash"],
        )
