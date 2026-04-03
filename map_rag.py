from typing import List, Dict
from map_data import MAP_RUBRIC


def retrieve_relevant_rubric(evidence_text: str, top_k: int = 3) -> List[Dict[str, str]]:
    text = evidence_text.lower()

    scored = []
    for item in MAP_RUBRIC:
        score = 0
        content = item["content"].lower()

        keywords = [
            "move forward", "campaign", "quarter", "q2", "q3", "q4", "march",
            "next step", "finalize", "proposal", "interested", "exploring",
            "buy-in", "slack", "email", "notes"
        ]

        for keyword in keywords:
            if keyword in text and keyword in content:
                score += 1

        if "email" in text and item["id"] == "strong_commitment_signals":
            score += 1

        if "slack" in text or "notes" in text:
            if item["id"] in {"weak_commitment_signals", "verification_risk"}:
                score += 2

        if "buy-in" in text or "exploring" in text:
            if item["id"] == "weak_commitment_signals":
                score += 2

        if "quarter" in text or "q2" in text or "q3" in text or "q4" in text:
            if item["id"] in {"map_definition", "strong_commitment_signals"}:
                score += 2

        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored[:top_k]]
