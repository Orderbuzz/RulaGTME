import json
import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI

from schemas import AccountProfile, ValuePropMatch

load_dotenv()

client = None
if os.getenv("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


VALUE_PROP_SUMMARIES = {
    "total_cost_of_care_reduction": {
        "short": "reducing total behavioral health spend by improving in-network utilization",
        "diagnostic_focus": "utilization, spend, plan value, and benefit tradeoffs",
    },
    "eap_upgrade": {
        "short": "replacing or supplementing an underperforming EAP with a model that drives ongoing engagement",
        "diagnostic_focus": "continuity of care, engagement beyond first touch, and whether the current model is enough",
    },
    "workforce_productivity": {
        "short": "improving workforce performance by helping employees access care faster and stay engaged at work",
        "diagnostic_focus": "absenteeism, turnover, performance friction, and workforce strain",
    },
    "employee_access_experience": {
        "short": "making it easier for employees to access affordable, quality mental health care quickly",
        "diagnostic_focus": "where access breaks down, which populations struggle most, and whether employees can actually use the benefit",
    },
}


def _safe_lower(value: str | None) -> str:
    return (value or "").lower()


def _first_name(contact: str | None) -> str | None:
    if not contact:
        return None
    return contact.split()[0].strip()


def _generate_subject_line(account: AccountProfile, top_match: ValuePropMatch) -> str:
    company = account.company

    if top_match.value_prop_id == "total_cost_of_care_reduction":
        return f"{company}: behavioral health cost and utilization"
    if top_match.value_prop_id == "eap_upgrade":
        return f"{company}: rethinking mental health support beyond EAP"
    if top_match.value_prop_id == "workforce_productivity":
        return f"{company}: mental health and workforce performance"
    return f"{company}: improving mental health access for employees"


def _build_personalization_hooks(account: AccountProfile) -> List[str]:
    hooks = []

    industry = _safe_lower(account.industry)
    notes = _safe_lower(account.notes)

    if account.industry:
        hooks.append(account.industry)

    if account.us_employees:
        if account.us_employees >= 10000:
            hooks.append("large employee population")
        elif account.us_employees >= 3000:
            hooks.append("scaled workforce")
        else:
            hooks.append("smaller employee population")

    if "midwest" in notes:
        hooks.append("multi-site footprint across the Midwest")
    if "student employees" in notes:
        hooks.append("mixed staff and student employee population")
    if "merger" in notes or "integrating two separate benefits programs" in notes:
        hooks.append("benefits integration after a recent merger")
    if "field-based" in notes:
        hooks.append("field-based workforce")
    if "limited internet access" in notes:
        hooks.append("limited internet access during shifts")
    if "high-turnover" in notes or "turnover" in notes:
        hooks.append("high-turnover workforce")
    if "24/7 operations" in notes:
        hooks.append("24/7 operations")
    if "distribution centers" in notes:
        hooks.append("distributed workforce across many sites")
    if "eap" in notes:
        hooks.append("existing EAP model")
    if "limited benefits budget" in notes:
        hooks.append("tight benefits budget")

    # Soft industry-specific hooks
    if "health system" in industry:
        hooks.append("complex care-focused workforce")
    if "university" in industry:
        hooks.append("large mixed employee population")
    if "logistics" in industry or "transportation" in industry:
        hooks.append("operational workforce")
    if "forestry" in industry or "natural resources" in industry:
        hooks.append("hard-to-reach employee population")

    # dedupe while preserving order
    deduped = []
    for h in hooks:
        if h not in deduped:
            deduped.append(h)

    return deduped[:3]


def _build_context_translation(account: AccountProfile, top_match: ValuePropMatch) -> str:
    notes = _safe_lower(account.notes)
    industry = _safe_lower(account.industry)

    if top_match.value_prop_id == "workforce_productivity":
        if "high-turnover" in notes or "turnover" in notes:
            return "mental health support may be showing up less as a standalone benefit issue and more through turnover and day-to-day workforce strain"
        if "24/7 operations" in notes or "distribution centers" in notes:
            return "delayed access to care may be creating downstream performance and attendance friction across an operational workforce"
        if "field-based" in notes:
            return "care access may be harder to translate into consistent workforce support for employees who are not desk-based"
        return "mental health support may be closely tied to attendance, engagement, and workforce performance"

    if top_match.value_prop_id == "total_cost_of_care_reduction":
        if "merger" in notes or "benefits programs" in notes:
            return "behavioral health may be worth evaluating not just as a support offering, but as part of broader benefits efficiency and utilization strategy"
        if account.us_employees and account.us_employees >= 10000:
            return "at this scale, behavioral health value tends to matter more when employees actually use high-quality in-network care"
        return "behavioral health may be worth evaluating through a utilization and plan-value lens"

    if top_match.value_prop_id == "eap_upgrade":
        if "eap" in notes and "modernizing" in notes:
            return "the question may be less whether support exists, and more whether the current model is deep enough to drive ongoing care"
        if "eap" in notes:
            return "the current support model may be useful for first-touch help, but not necessarily for sustained engagement"
        return "traditional mental health support models often struggle to create real continuity of care"

    # employee_access_experience
    if "limited internet access" in notes:
        return "mental health support may break down less at the benefits level and more at the point where employees actually try to access care"
    if "student employees" in notes:
        return "mixed employee populations often make it harder to deliver a consistent mental health experience across different groups"
    if "distribution centers" in notes or "nationwide" in notes or "midwest" in notes:
        return "distributed workforces often have the benefit on paper but uneven real-world access across sites and populations"
    if "education" in industry or "university" in industry:
        return "the bigger question may be whether employees can actually find and use care quickly when they need it"
    return "employees may have support available, but still struggle to find and use care quickly in practice"


def _build_discovery_questions(
    account: AccountProfile,
    top_match: ValuePropMatch,
    second_match: ValuePropMatch | None = None,
) -> List[str]:
    notes = _safe_lower(account.notes)
    industry = _safe_lower(account.industry)

    if top_match.value_prop_id == "workforce_productivity":
        diagnosis = "Is mental health showing up more internally as an absenteeism issue, a turnover issue, or both?"
        segmentation = "Are there specific workforce segments where access to support is harder to translate into day-to-day performance or retention?"
        decision = "When you think about mental health support, are you optimizing more for employee experience or workforce stability?"

        if "24/7 operations" in notes or "distribution centers" in notes:
            segmentation = "Are certain sites or operating environments harder to support consistently from a mental health access standpoint?"
        elif "field-based" in notes:
            segmentation = "Do field-based employees experience different barriers to getting support than more centralized teams?"
        elif "cnas" in notes or "lpns" in notes:
            segmentation = "Are there particular care roles where stress, turnover, or absenteeism makes mental health support more operationally important?"

        return [diagnosis, segmentation, decision]

    if top_match.value_prop_id == "total_cost_of_care_reduction":
        diagnosis = "How much visibility do you have today into behavioral health utilization versus broader spend?"
        segmentation = "Is the bigger opportunity right now improving employee uptake of care or improving how the plan captures value from existing coverage?"
        decision = "As you think about behavioral health, are you optimizing more for cost efficiency, benefit competitiveness, or employee experience?"

        if "merger" in notes or "benefits programs" in notes:
            segmentation = "Has the merger changed how you're evaluating behavioral health across the combined benefits structure?"

        return [diagnosis, segmentation, decision]

    if top_match.value_prop_id == "eap_upgrade":
        diagnosis = "How far does engagement typically go today beyond the first EAP interaction?"
        segmentation = "Are you evaluating mental health support more as a short-term employee resource or as something that should drive ongoing care?"
        decision = "Would your team be more likely to replace the current model entirely or layer something stronger alongside it?"

        if "modernizing" in notes:
            decision = "As you modernize the current program, are you thinking more about replacing the existing model or strengthening it around continuity of care?"

        return [diagnosis, segmentation, decision]

    # employee_access_experience
    diagnosis = "Where does access tend to break down today: finding providers, speed to care, or employees actually following through?"
    segmentation = "Are there specific employee populations that have a harder time accessing support consistently?"
    decision = "Is the bigger priority right now improving the care experience itself or improving utilization of the benefit you already offer?"

    if "student employees" in notes:
        segmentation = "Do staff and student employee populations experience mental health access differently today?"
    elif "limited internet access" in notes:
        segmentation = "Do employees working in lower-connectivity environments struggle more to actually use available support?"
    elif "distribution centers" in notes or "nationwide" in notes or "midwest" in notes:
        segmentation = "Are certain sites or geographies harder to support consistently than others?"

    return [diagnosis, segmentation, decision]


def generate_fallback_email(
    account: AccountProfile,
    is_icp: bool,
    icp_reasons: List[str],
    matches: List[ValuePropMatch],
) -> Dict[str, Any]:
    top_match = matches[0]
    second_match = matches[1] if len(matches) > 1 else None
    first_name = _first_name(account.contact)
    hooks = _build_personalization_hooks(account)
    translation = _build_context_translation(account, top_match)

    greeting = f"Hi {first_name}," if first_name else "Hi,"
    company = account.company
    hook_text = ", ".join(hooks) if hooks else "your current workforce and benefits context"

    secondary_line = ""
    if second_match:
        secondary_line = (
            f" There may also be a fit around {second_match.value_prop_name.lower()}, depending on where your team is feeling the most pressure."
        )

    icp_line = ""
    if is_icp:
        icp_line = " Given the scale and profile of the organization, it felt worth reaching out."

    if top_match.value_prop_id == "total_cost_of_care_reduction":
        body = (
            f"{greeting}\n\n"
            f"I’m reaching out because {company}'s {hook_text} suggests {translation}. "
            f"For larger employers, behavioral health tends to matter more when the conversation shifts from offering support to driving better in-network utilization and plan value.{icp_line}"
            f"{secondary_line}\n\n"
            f"Worth comparing notes on how your team is thinking about behavioral health today?"
        )

    elif top_match.value_prop_id == "eap_upgrade":
        body = (
            f"{greeting}\n\n"
            f"I’m reaching out because {company}'s {hook_text} suggests {translation}. "
            f"In a lot of organizations, the gap isn’t whether support exists — it’s whether the model is deep enough to create ongoing engagement rather than one-time usage."
            f"{secondary_line}\n\n"
            f"Curious whether that’s something your team is evaluating right now."
        )

    elif top_match.value_prop_id == "workforce_productivity":
        body = (
            f"{greeting}\n\n"
            f"I’m reaching out because {company}'s {hook_text} suggests {translation}. "
            f"For operational workforces, mental health often shows up not just as a benefits issue, but through attendance, retention, and overall workforce consistency."
            f"{secondary_line}\n\n"
            f"Would it be useful to compare notes on whether that’s showing up for your team?"
        )

    else:
        body = (
            f"{greeting}\n\n"
            f"I’m reaching out because {company}'s {hook_text} suggests {translation}. "
            f"A lot of organizations have mental health benefits in place, but still run into friction when employees actually try to find and use care."
            f"{secondary_line}\n\n"
            f"Curious whether access or follow-through is more of the issue on your side."
        )

    questions = _build_discovery_questions(account, top_match, second_match)
    subject = _generate_subject_line(account, top_match)

    return {
        "email_subject": subject,
        "email_body": body,
        "discovery_questions": questions,
    }


def generate_with_llm(
    account: AccountProfile,
    is_icp: bool,
    icp_reasons: List[str],
    matches: List[ValuePropMatch],
) -> Dict[str, Any]:
    if client is None:
        return generate_fallback_email(account, is_icp, icp_reasons, matches)

    top_match = matches[0]
    second_match = matches[1] if len(matches) > 1 else None

    prompt_payload = {
        "account": account.model_dump(),
        "icp": {
            "is_icp": is_icp,
            "reasons": icp_reasons,
        },
        "top_value_prop": top_match.model_dump(),
        "secondary_value_prop": second_match.model_dump() if second_match else None,
        "value_prop_definitions": VALUE_PROP_SUMMARIES,
        "target_discovery_question_structure": [
            "diagnosis question",
            "segmentation question",
            "decision-criteria question",
        ],
    }

    system_prompt = """
system_prompt = """
You are writing outbound emails for an AE selling Rula to benefits and HR leaders.

Write:
1. one first-touch email
2. exactly 3 discovery questions

The message should feel relevant, emotionally intelligent, commercially aware, and naturally written by a sharp AE.

EMAIL GOAL:
Earn a reply by showing a strong point of view based on the account context.

EMAIL STRUCTURE:
1. Opening
- Begin with one natural, conversational observation tied to the account
- It should feel like something you would say out loud, not write in a report
- Use soft language when appropriate (e.g., "I’d imagine", "I’d guess")
- Do NOT list attributes or restate structured data (no "University, large population...")
- Do NOT sound analytical or overly formal
- Let the sentence breathe slightly — avoid overly compressed phrasing

2. Interpretation
- Translate that observation into one likely business, workforce, or benefits problem
- Add light nuance (e.g., “especially across different groups”, “in practice”)
- Keep it grounded and human
- Do not over-explain

3. Reframe
- Introduce the top matched value proposition indirectly
- Focus on how this shows up in real life, not abstract value
- Stay focused on ONE wedge only

4. Close
- End with one low-friction, curiosity-driven question
- Should feel easy to respond to
- No pressure language
- No CTA asking for time or a meeting

TONE:
- human
- slightly conversational
- warm but not soft
- confident but not loud
- commercially aware
- low-pressure
- natural rhythm (not robotic or overly structured)

STYLE RULES:
- 75–120 words
- Use contractions (e.g., "I’d", "doesn’t", "isn’t")
- Prefer "teams" over "organizations"
- Prefer "people" over "employees" when natural
- Add light connective language for flow (e.g., "especially", "in practice", "across the board")
- Avoid sounding too perfect or overly edited
- The email should feel like a thoughtful note, not a template

DO NOT:
- invent facts
- assume self-insured status unless explicitly stated
- assume EAP dissatisfaction unless explicitly supported
- explain multiple value props
- summarize the whole account
- sound like a consultant, product page, or AI system

DO NOT USE THESE PHRASES:
- "hope you're well"
- "noticed"
- "worth comparing notes"
- "how your team is thinking about"
- "behavioral health value"
- "it felt worth reaching out"
- "depending on where your team is feeling the most pressure"
- "I wanted to reach out"
- "there may be a fit around"
- "open to learning more"
- "just reaching out"

DISCOVERY QUESTION RULES:
Write exactly 3 strong AE discovery questions.

Question 1 = diagnosis
- what is actually happening?

Question 2 = segmentation
- where is the issue most visible?

Question 3 = decision criteria
- how is the buyer evaluating the tradeoff?

DISCOVERY QUESTION CONSTRAINTS:
- Must test the top matched value proposition
- Must reflect account context when possible
- One clean idea per question
- No generic questions
- No "what are your priorities?"
- No vague, broad questions

VALUE PROP GUIDANCE:
- Workforce productivity → absenteeism, turnover, workforce strain
- Total cost → utilization, spend efficiency, tradeoffs
- EAP → engagement depth, continuity, replace vs supplement
- Access → where access breaks down, who struggles, follow-through

OUTPUT:
Return valid JSON with:
{
  "email_subject": "...",
  "email_body": "...",
  "discovery_questions": ["...", "...", "..."]
}
"""
Return valid JSON with exactly these keys:
{
  "email_subject": "...",
  "email_body": "...",
  "discovery_questions": ["...", "...", "..."]
}
"""

    user_prompt = f"Generate the outreach and discovery questions using this input:\n{json.dumps(prompt_payload, indent=2)}"

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0.4,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content
    parsed = json.loads(content)

    questions = parsed.get("discovery_questions", [])
    if not isinstance(questions, list) or len(questions) < 3:
        questions = _build_discovery_questions(account, top_match, second_match)

    return {
        "email_subject": parsed.get("email_subject", _generate_subject_line(account, top_match)),
        "email_body": parsed.get("email_body", ""),
        "discovery_questions": questions[:3],
    }
