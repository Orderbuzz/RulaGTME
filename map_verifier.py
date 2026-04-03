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

    known_time_markers = ["march", "q2", "q3", "q4", "next week", "full year"]

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


def verify_map(evidence: Dict[str, Any]) -> Dict[str, Any]:
    text = evidence["text"]
    text_lower = text.lower()

    retrieved_context = retrieve_relevant_rubric(text)

    campaigns = _extract_campaigns(text)
    timeline = _extract_timeline(text)
    quarters = _infer_quarters(text)

    buyer_commitment = any(
        phrase in text_lower for phrase in [
            "we're excited to move forward",
            "they'd commit",
            "they want to do",
            "she's in",
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
            "going to send the map doc tomorrow",
            "no commitment to specific campaigns yet",
        ]
    )

    next_step_present = any(
        phrase in text_lower for phrase in [
            "let's set up a call next week",
            "going to send the map doc tomorrow",
        ]
    )

    buyer_authored = _buyer_authored(evidence["source_type"], evidence["source_role"])

    score = 0
    reasons = []
    follow_up_actions = []

    if buyer_authored:
        score += 3
        reasons.append("Buyer-authored evidence is stronger than internal seller summaries.")
    else:
        reasons.append("Evidence is secondhand and should not be treated as fully verified.")

    if buyer_commitment:
        score += 3
        reasons.append("Evidence contains clear commitment language.")

    if campaigns:
        score += 2
        reasons.append("Specific campaign types were referenced.")

    if timeline:
        score += 2
        reasons.append("Evidence includes a timeline or milestone timing.")

    if quarters:
        score += 1
        reasons.append(f"Commitment appears to cover {quarters} quarter(s).")

    if next_step_present:
        score += 1
        reasons.append("There is a concrete next step.")

    if exploratory_language:
        score -= 3
        reasons.append("Language is exploratory rather than committed.")

    if unresolved_dependency:
        score -= 2
        reasons.append("A dependency remains unresolved before the MAP can be counted.")

    if score >= 7 and buyer_authored:
        verdict = "verified"
        confidence = "high"
    elif score >= 4:
        verdict = "needs_review"
        confidence = "medium"
    else:
        verdict = "not_verified"
        confidence = "low"

    if not buyer_authored:
        follow_up_actions.append("Obtain buyer-authored confirmation via email or shared MAP document.")
    if not campaigns:
        follow_up_actions.append("Capture explicit campaign types before counting toward quota.")
    if not quarters:
        follow_up_actions.append("Clarify the number of quarters committed.")
    if unresolved_dependency:
        follow_up_actions.append("Resolve dependency or secure final buyer approval before verification.")

    return {
        "account": evidence["account"],
        "source_type": evidence["source_type"],
        "committer": evidence["source_author"],
        "committer_role": evidence["source_role"],
        "structured_extraction": {
            "campaigns": campaigns,
            "timeline_markers": timeline,
            "quarters_committed": quarters,
            "buyer_commitment_language": buyer_commitment,
            "next_step_present": next_step_present,
            "buyer_authored": buyer_authored,
            "exploratory_language": exploratory_language,
            "unresolved_dependency": unresolved_dependency,
        },
        "retrieved_rubric_context": retrieved_context,
        "score": score,
        "confidence": confidence,
        "verdict": verdict,
        "follow_up_actions": follow_up_actions,
        "reasons": reasons,
    }
