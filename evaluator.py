from typing import List, Tuple

from schemas import AccountProfile, ValuePropMatch


GENERIC_EMAIL_PHRASES = [
    "hope you're well",
    "hope you are well",
    "just reaching out",
    "checking in",
    "wanted to reach out",
    "wanted to see",
    "employee wellbeing",
    "mental health is important",
]

WEAK_DISCOVERY_PATTERNS = [
    "what are your priorities",
    "what are your goals",
    "how are you thinking about",
    "tell me about",
    "would love to learn more",
]

TOP_MATCH_KEYWORDS = {
    "total_cost_of_care_reduction": [
        "utilization",
        "spend",
        "cost",
        "plan value",
        "benefits strategy",
        "cost efficiency",
        "benefit tradeoffs",
    ],
    "eap_upgrade": [
        "eap",
        "continuity",
        "engagement",
        "first touch",
        "replace",
        "supplement",
        "ongoing care",
    ],
    "workforce_productivity": [
        "absenteeism",
        "turnover",
        "retention",
        "productivity",
        "performance",
        "attendance",
        "workforce stability",
        "operational strain",
    ],
    "employee_access_experience": [
        "access",
        "providers",
        "speed to care",
        "follow through",
        "follow-through",
        "care experience",
        "use the benefit",
        "find and use care",
    ],
}


def _safe_lower(value: str | None) -> str:
    return (value or "").lower()


def _count_filled_fields(account: AccountProfile) -> int:
    return sum([
        bool(account.industry),
        bool(account.us_employees),
        bool(account.contact),
        bool(account.title),
        bool(account.health_plan and _safe_lower(account.health_plan) != "unknown"),
        bool(account.notes),
    ])


def _specificity_hits(account: AccountProfile, email_text: str) -> int:
    hits = 0

    if account.company and _safe_lower(account.company) in email_text:
        hits += 1

    if account.industry:
        industry_terms = [t.strip() for t in _safe_lower(account.industry).replace("/", " ").split() if len(t.strip()) > 3]
        if any(term in email_text for term in industry_terms):
            hits += 1

    if account.title and _safe_lower(account.title) in email_text:
        hits += 1

    if account.notes:
        notes = _safe_lower(account.notes)

        note_markers = [
            "midwest",
            "student employees",
            "merger",
            "benefits programs",
            "field-based",
            "limited internet access",
            "turnover",
            "24/7 operations",
            "distribution centers",
            "eap",
            "limited benefits budget",
            "cnas",
            "lpns",
        ]

        if any(marker in notes and marker in email_text for marker in note_markers):
            hits += 1

    if account.health_plan and _safe_lower(account.health_plan) != "unknown":
        if _safe_lower(account.health_plan) in email_text:
            hits += 1

    return hits


def _check_unsupported_claims(account: AccountProfile, email_text: str) -> List[str]:
    reasons = []

    # Your dataset does not tell us self-insured status
    if "self-insured" in email_text or "self insured" in email_text:
        reasons.append("possible_unsupported_claim")

    # Don't let the email claim EAP context unless the notes support it
    if "eap" in email_text and "eap" not in _safe_lower(account.notes):
        reasons.append("possible_unsupported_claim")

    # Don’t overstate plan economics when the plan is unknown
    if (account.health_plan is None or _safe_lower(account.health_plan) == "unknown") and (
        "plan value" in email_text or "in-network utilization" in email_text
    ):
        reasons.append("possible_unsupported_claim")

    return reasons


def _questions_align_to_match(top_match_id: str, discovery_questions: List[str]) -> bool:
    joined = " ".join(discovery_questions).lower()
    keywords = TOP_MATCH_KEYWORDS.get(top_match_id, [])
    return any(keyword in joined for keyword in keywords)


def _count_weak_questions(discovery_questions: List[str]) -> int:
    weak_count = 0
    for q in discovery_questions:
        q_lower = q.lower()
        if any(pattern in q_lower for pattern in WEAK_DISCOVERY_PATTERNS):
            weak_count += 1
    return weak_count


def evaluate_output(
    account: AccountProfile,
    matches: List[ValuePropMatch],
    email_body: str,
    discovery_questions: List[str],
) -> Tuple[float, bool, List[str]]:
    score = 8.5
    review_reasons: List[str] = []

    email_text = _safe_lower(email_body)
    filled_fields = _count_filled_fields(account)

    # -------------------------
    # Sparse data risk
    # -------------------------
    if filled_fields <= 3:
        score -= 1.2
        review_reasons.append("sparse_data")

    # -------------------------
    # Unsupported claims
    # -------------------------
    unsupported = _check_unsupported_claims(account, email_text)
    if unsupported:
        score -= 2.0
        review_reasons.extend(unsupported)

    # -------------------------
    # Generic email language
    # -------------------------
    generic_hits = sum(1 for phrase in GENERIC_EMAIL_PHRASES if phrase in email_text)
    if generic_hits >= 2:
        score -= 1.5
        review_reasons.append("generic_email_risk")
    elif generic_hits == 1:
        score -= 0.7
        review_reasons.append("slightly_generic_email")

    # -------------------------
    # Specificity check
    # -------------------------
    specificity = _specificity_hits(account, email_text)
    if specificity == 0:
        score -= 1.8
        review_reasons.append("low_specificity")
    elif specificity == 1:
        score -= 0.8
        review_reasons.append("limited_specificity")

    # -------------------------
    # Discovery question count
    # -------------------------
    if len(discovery_questions) < 3:
        score -= 1.5
        review_reasons.append("insufficient_discovery_questions")

    # -------------------------
    # Weak discovery questions
    # -------------------------
    weak_questions = _count_weak_questions(discovery_questions)
    if weak_questions >= 2:
        score -= 1.5
        review_reasons.append("weak_discovery_questions")
    elif weak_questions == 1:
        score -= 0.8
        review_reasons.append("partially_weak_discovery_questions")

    # -------------------------
    # Match alignment
    # -------------------------
    if matches:
        top_match_id = matches[0].value_prop_id
        if not _questions_align_to_match(top_match_id, discovery_questions):
            score -= 1.2
            review_reasons.append("questions_weakly_aligned_to_match")

    # -------------------------
    # Email length check
    # -------------------------
    word_count = len(email_body.split())
    if word_count < 70:
        score -= 0.8
        review_reasons.append("email_too_short")
    elif word_count > 155:
        score -= 0.8
        review_reasons.append("email_too_long")

    # -------------------------
    # Final normalization
    # -------------------------
    # Deduplicate reasons while preserving order
    deduped_reasons = []
    for reason in review_reasons:
        if reason not in deduped_reasons:
            deduped_reasons.append(reason)

    score = max(1.0, min(10.0, round(score, 1)))
    review_required = score < 7.5 or len(deduped_reasons) > 0

    return score, review_required, deduped_reasons
