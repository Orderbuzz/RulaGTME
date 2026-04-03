from typing import Dict, Any, List, Optional
from map_rag import retrieve_relevant_rubric


def _extract_campaigns(text: str) -> List[str]:
    text_lower = text.lower()
    campaigns = []

    known_patterns = [
        "launch email",
        "benefits insert",
        "manager wellness toolkit",
        "email blast",
        "posters",
        "quarterly campaigns",
    ]

    for pattern in known_patterns:
        if pattern in text_lower:
            campaigns.append(pattern)

    return campaigns


def _extract_timeline(text: str) -> List[str]:
    text_lower = text.lower()
    timeline = []

    known_time_markers = ["march", "q1", "q2", "q3", "q4", "next week", "full year"]

    for marker in known_time_markers:
        if marker in text_lower:
            timeline.append(marker.upper() if marker.startswith("q") else marker)

    return timeline


def _infer_quarters(text: str) -> Optional[int]:
    text_lower = text.lower()

    if "full year" in text_lower or "quarterly campaigns for the full year" in text_lower:
        return 4

    quarter_count = 0
    for q in ["q1", "q2", "q3", "q4"]:
        if q in text_lower:
            quarter_count += 1

    return quarter_count if quarter_count > 0 else None


def _buyer_authored(source_type: str, source_role: str) -> bool:
    return source_type == "email" and "internal seller" not in source_role.lower()


def _get_evidence_tier(source_type: str, buyer_authored: bool) -> str:
    if buyer_authored:
        return "tier_1_buyer_authored"
    if source_type in {"slack", "meeting_notes"}:
        return "tier_3_internal_summary"
    return "tier_2_other"


def _get_score_band(score: int) -> str:
    if score >= 8:
        return "strong"
    if score >= 3:
        return "moderate"
    return "weak"


def verify_map(evidence: Dict[str, Any]) -> Dict[str, Any]:
    text = evidence["text"]
    text_lower = text.lower()
    source_type = evidence["source_type"]

    buyer_authored = _buyer_authored(evidence["source_type"], evidence["source_role"])
    evidence_tier = _get_evidence_tier(source_type, buyer_authored)

    retrieved_context = retrieve_relevant_rubric(text, source_type)

    campaigns = _extract_campaigns(text)
    timeline = _extract_timeline(text)
    quarters = _infer_quarters(text)

    buyer_commitment_language = any(
        phrase in text_lower for phrase in [
            "we're excited to move forward",
            "we'd like to plan",
        ]
    )

    secondhand_commitment_language = any(
        phrase in text_lower for phrase in [
            "she's in",
            "they want to do",
            "they'd commit",
        ]
    )

    exploratory_language = any(
        phrase in text_lower for phrase in [
            "interested in exploring",
            "wants to see a proposal",
            "looking at q3 at the earliest",
        ]
    )

    unresolved_dependency = any(
        phrase in text_lower for phrase in [
            "needs to get buy-in",
            "no commitment to specific campaigns yet",
        ]
    )

    buyer_confirmed_next_step = "let's set up a call next week" in text_lower
    seller_driven_next_step = "going to send the map doc tomorrow" in text_lower

    score = 0
    reasons: List[str] = []
    follow_up_actions: List[str] = []

    # Evidence quality
    if buyer_authored:
        score += 3
        reasons.append("Buyer-authored evidence is materially stronger than internal seller summaries.")
    else:
        score -= 3
        reasons.append("Evidence is secondhand and carries meaningful overstatement risk.")

    # Commitment strength
    if buyer_commitment_language:
        score += 3
        reasons.append("Evidence contains explicit buyer commitment language.")
    elif secondhand_commitment_language:
        score += 1
        reasons.append(
            "Commitment is reported secondhand and is highly susceptible to seller interpretation bias."
        )

    # Specificity
    if campaigns:
        score += 2
        reasons.append("Specific campaign types were referenced.")

    if timeline:
        score += 2
        reasons.append("Evidence includes timeline or milestone timing.")

    if quarters:
        score += 1
        reasons.append(f"Commitment appears to cover {quarters} quarter(s).")

    # Next step quality
    if buyer_confirmed_next_step:
        score += 1
        reasons.append("There is a buyer-confirmed next step.")
    elif seller_driven_next_step:
        reasons.append("There is a seller-driven next step, but it is not yet buyer-confirmed.")

    # Negative signals
    if exploratory_language:
        score -= 3
        reasons.append("Language is exploratory rather than committed.")

    if unresolved_dependency:
        score -= 2
        reasons.append("A dependency remains unresolved before the MAP can be counted.")

    # Verdict
    if score >= 7 and buyer_authored and buyer_commitment_language:
        verdict = "verified"
        confidence = "high"
    elif score >= 3:
        verdict = "needs_review"
        confidence = "medium"
    else:
        verdict = "not_verified"
        confidence = "low"

    score_band = _get_score_band(score)
    forecast_eligible = verdict == "verified"

    # Follow-up actions
    if not buyer_authored:
        follow_up_actions.append("Obtain buyer-authored confirmation via email or shared MAP document.")
    if not campaigns:
        follow_up_actions.append("Capture explicit campaign types before counting toward quota.")
    if not quarters:
        follow_up_actions.append("Clarify the number of quarters committed.")
    if unresolved_dependency:
        follow_up_actions.append("Resolve dependency or secure final buyer approval before verification.")
    if seller_driven_next_step and not buyer_confirmed_next_step:
        follow_up_actions.append("Convert seller-driven follow-up into a buyer-confirmed next step.")
    if verdict == "verified":
        follow_up_actions.append("Log MAP in structured format with campaign timeline, owner, and evidence link.")

    return {
        "account": evidence["account"],
        "source_type": evidence["source_type"],
        "committer": evidence["source_author"],
        "committer_role": evidence["source_role"],
        "evidence_tier": evidence_tier,
        "structured_extraction": {
            "campaigns": campaigns,
            "timeline_markers": timeline,
            "quarters_committed": quarters,
            "buyer_commitment_language": buyer_commitment_language,
            "secondhand_commitment_language": secondhand_commitment_language,
            "buyer_confirmed_next_step": buyer_confirmed_next_step,
            "seller_driven_next_step": seller_driven_next_step,
            "buyer_authored": buyer_authored,
            "exploratory_language": exploratory_language,
            "unresolved_dependency": unresolved_dependency,
        },
        "retrieved_rubric_context": retrieved_context,
        "score": score,
        "score_band": score_band,
        "confidence": confidence,
        "verdict": verdict,
        "forecast_eligible": forecast_eligible,
        "follow_up_actions": follow_up_actions,
        "reasons": reasons,
    }
