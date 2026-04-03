from typing import List, Dict
from map_data import MAP_RUBRIC


def retrieve_relevant_rubric(evidence_text: str, source_type: str, top_k: int = 3) -> List[Dict[str, str]]:
    text = evidence_text.lower()
    source = source_type.lower()

    scored = []
    for item in MAP_RUBRIC:
        score = 0
        item_id = item["id"]
        content = item["content"].lower()

        shared_keywords = [
            "move forward",
            "campaign",
            "quarter",
            "q2",
            "q3",
            "q4",
            "march",
            "next step",
            "finalize",
            "proposal",
            "interested",
            "exploring",
            "buy-in",
            "full year",
        ]

        for keyword in shared_keywords:
            if keyword in text and keyword in content:
                score += 1

        if source == "email" and item_id == "strong_commitment_signals":
            score += 2

        if source in {"slack", "meeting_notes"} and item_id in {"weak_commitment_signals", "verification_risk"}:
            score += 3

        if "buy-in" in text or "exploring" in text or "proposal" in text:
            if item_id == "weak_commitment_signals":
                score += 3

        if any(q in text for q in ["q2", "q3", "q4", "full year"]):
            if item_id in {"map_definition", "strong_commitment_signals"}:
                score += 2

        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored[:top_k]]
