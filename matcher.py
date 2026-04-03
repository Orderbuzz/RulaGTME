from typing import List, Dict, Any, Tuple
from schemas import AccountProfile, ValuePropMatch

VALUE_PROPS = [
    {
        "id": "total_cost_of_care_reduction",
        "name": "Total cost of care reduction",
        "description": (
            "Employer-sponsored health insurance costs are rising ~6% annually. "
            "Rula reduces total behavioral health spend by driving utilization through a "
            "high-quality, in-network provider network."
        ),
    },
    {
        "id": "eap_upgrade",
        "name": "EAP upgrade",
        "description": (
            "Most Employee Assistance Programs underdeliver on continuity and depth of care. "
            "Rula replaces or supplements EAPs with a model that drives real engagement and ongoing treatment."
        ),
    },
    {
        "id": "workforce_productivity",
        "name": "Workforce productivity",
        "description": (
            "Mental health conditions drive absenteeism, presenteeism, and turnover, costing employers "
            "significant productivity loss. Rula helps employees get care faster, return to work sooner, "
            "and stay engaged."
        ),
    },
    {
        "id": "employee_access_experience",
        "name": "Employee access & experience",
        "description": (
            "Many employees can't find affordable, quality mental health care through their current benefits. "
            "Rula provides easy, fast access to a large provider network with no long wait times."
        ),
    },
]

PRIORITY_HEALTH_PLANS = {"anthem", "aetna", "cigna"}


def _safe_lower(value: str | None) -> str:
    return (value or "").lower()


def assess_icp_fit(account: AccountProfile) -> Tuple[bool, float, List[str]]:
    industry = _safe_lower(account.industry)
    health_plan = _safe_lower(account.health_plan)

    score = 0
    reasons: List[str] = []

    # Health systems > 3,000 employees
    if "health system" in industry and (account.us_employees or 0) > 3000:
        score += 4
        reasons.append("Account matches ICP: health system with more than 3,000 employees.")

    # Universities > 3,000 employees
    if "university" in industry and (account.us_employees or 0) > 3000:
        score += 4
        reasons.append("Account matches ICP: university with more than 3,000 employees.")

    # Large employers with priority plans
    if (account.us_employees or 0) > 3000 and health_plan in PRIORITY_HEALTH_PLANS:
        score += 3
        reasons.append(
            f"Account matches ICP: large employer aligned to a priority health plan ({account.health_plan})."
        )

    # Secondary near-ICP logic for realism
    if score == 0:
        if (account.us_employees or 0) > 3000:
            score += 1
            reasons.append("Large employer, but not clearly in a core ICP segment.")
        elif "education" in industry:
            score += 1
            reasons.append("Education-related employer, but below the ideal size threshold.")
        elif "healthcare" in industry or "senior living" in industry:
            score += 1
            reasons.append("Healthcare-adjacent employer, but not a direct core ICP match.")

    confidence = min(0.95, 0.45 + (score * 0.1))
    is_icp = score >= 3

    return is_icp, round(confidence, 2), reasons


def rule_based_match(account: AccountProfile) -> Dict[str, Any]:
    industry = _safe_lower(account.industry)
    notes = _safe_lower(account.notes)
    title = _safe_lower(account.title)
    health_plan = _safe_lower(account.health_plan)

    is_icp, icp_confidence, icp_reasons = assess_icp_fit(account)

    scores: Dict[str, Dict[str, Any]] = {
        "total_cost_of_care_reduction": {"score": 0, "reasons": []},
        "eap_upgrade": {"score": 0, "reasons": []},
        "workforce_productivity": {"score": 0, "reasons": []},
        "employee_access_experience": {"score": 0, "reasons": []},
    }

    # -------------------------
    # ICP-aware boosts
    # -------------------------
    if "health system" in industry and (account.us_employees or 0) > 3000:
        scores["total_cost_of_care_reduction"]["score"] += 2
        scores["total_cost_of_care_reduction"]["reasons"].append(
            "Health systems are a core segment for total cost of care reduction."
        )
        scores["workforce_productivity"]["score"] += 2
        scores["workforce_productivity"]["reasons"].append(
            "Health system workforces often face burnout, absenteeism, and operational strain."
        )

    if "university" in industry and (account.us_employees or 0) > 3000:
        scores["employee_access_experience"]["score"] += 3
        scores["employee_access_experience"]["reasons"].append(
            "Universities are a strong fit for improving access and experience across large mixed populations."
        )
        scores["eap_upgrade"]["score"] += 1
        scores["eap_upgrade"]["reasons"].append(
            "Universities can be a fit for EAP upgrade, but direct EAP pain is not yet confirmed."
        )

    if (account.us_employees or 0) > 3000 and health_plan in PRIORITY_HEALTH_PLANS:
        scores["total_cost_of_care_reduction"]["score"] += 1
        scores["total_cost_of_care_reduction"]["reasons"].append(
            f"Priority health plan alignment ({account.health_plan}) increases strategic fit."
        )

    # -------------------------
    # Value prop specific logic
    # -------------------------

    # Total cost of care reduction
    if account.us_employees and account.us_employees >= 10000:
        scores["total_cost_of_care_reduction"]["score"] += 2
        scores["total_cost_of_care_reduction"]["reasons"].append(
            "Very large employee population makes behavioral health spend more economically material."
        )

    if any(term in notes for term in ["integrating two separate benefits programs", "benefits programs", "modernizing", "expanded"]):
        scores["total_cost_of_care_reduction"]["score"] += 1
        scores["total_cost_of_care_reduction"]["reasons"].append(
            "Benefits change activity suggests an opening to position behavioral health value at the plan level."
        )

    # EAP upgrade
    if "eap" in notes:
        scores["eap_upgrade"]["score"] += 4
        scores["eap_upgrade"]["reasons"].append(
            "Notes explicitly reference an EAP, making EAP upgrade highly relevant."
        )

    if "eap" in notes and any(term in notes for term in ["modernizing", "replace", "supplement"]):
        scores["eap_upgrade"]["score"] += 2
        scores["eap_upgrade"]["reasons"].append(
            "The account appears open to changing or upgrading its current EAP approach."
        )

    # Workforce productivity
    if any(term in industry for term in ["logistics", "transportation", "senior living", "healthcare", "forestry", "natural resources"]):
        scores["workforce_productivity"]["score"] += 2
        scores["workforce_productivity"]["reasons"].append(
            "Industry suggests operational workforce conditions where productivity loss may matter."
        )

    if any(term in notes for term in [
        "high-turnover",
        "turnover",
        "cnas",
        "lpns",
        "field-based",
        "during shifts",
        "24/7 operations",
        "distribution centers"
    ]):
        scores["workforce_productivity"]["score"] += 4
        scores["workforce_productivity"]["reasons"].append(
            "Notes point to turnover, attendance, or operational strain where mental health affects productivity."
        )

    # Employee access & experience
    if any(term in notes for term in [
        "student employees",
        "across the midwest",
        "nationwide",
        "30+ distribution centers",
        "limited internet access",
        "small community college",
        "limited benefits budget"
    ]):
        scores["employee_access_experience"]["score"] += 3
        scores["employee_access_experience"]["reasons"].append(
            "Notes suggest fragmented, constrained, or uneven access to care."
        )

    if any(term in notes for term in ["field-based", "limited internet access during shifts", "24/7 operations"]):
        scores["employee_access_experience"]["score"] += 2
        scores["employee_access_experience"]["reasons"].append(
            "Workforce conditions suggest practical barriers to accessing care consistently."
        )

    if "director of employee wellness" in title or "director of benefits" in title or "vp, total rewards" in title:
        scores["employee_access_experience"]["score"] += 1
        scores["employee_access_experience"]["reasons"].append(
            "Buyer role suggests benefit usability and care experience may be a relevant angle."
        )

    # -------------------------
    # Sparse data handling
    # -------------------------
    non_empty_fields = sum([
        bool(account.industry),
        bool(account.us_employees),
        bool(account.contact),
        bool(account.title),
        bool(account.health_plan and account.health_plan.lower() != "unknown"),
        bool(account.notes),
    ])

    matches: List[ValuePropMatch] = []
    for vp in VALUE_PROPS:
        raw_score = scores[vp["id"]]["score"]
        if raw_score <= 0:
            continue

        confidence = min(0.95, 0.45 + (raw_score * 0.07))

        if non_empty_fields <= 3:
            confidence = min(confidence, 0.62)
            scores[vp["id"]]["reasons"].append(
                "Confidence is limited because the account profile is sparse."
            )

        matches.append(
            ValuePropMatch(
                value_prop_id=vp["id"],
                value_prop_name=vp["name"],
                confidence=round(confidence, 2),
                reasoning=scores[vp["id"]]["reasons"][:4],
            )
        )

    if not matches:
        matches.append(
            ValuePropMatch(
                value_prop_id="employee_access_experience",
                value_prop_name="Employee access & experience",
                confidence=0.5,
                reasoning=[
                    "Insufficient account detail to support a narrower hypothesis, so access & experience is the safest starting point."
                ],
            )
        )

    matches.sort(key=lambda m: m.confidence, reverse=True)

    if len(matches) > 1 and (matches[0].confidence - matches[1].confidence) < 0.10:
        matches[0].confidence = min(0.95, round(matches[0].confidence + 0.05, 2))

    return {
        "is_icp": is_icp,
        "icp_confidence": icp_confidence,
        "icp_reasons": icp_reasons,
        "matched_value_props": matches[:2],
    }
