import json
import os
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from openai import OpenAI

from schemas import AccountProfile, ValuePropMatch

load_dotenv()

client = None
if os.getenv("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


VALUE_PROP_SUMMARIES = {
    "total_cost_of_care_reduction": {
        "label": "Total cost of care reduction",
        "summary": "reducing behavioral health spend by improving access to quality in-network care and increasing real utilization",
    },
    "eap_upgrade": {
        "label": "EAP upgrade",
        "summary": "replacing or supplementing a shallow support model with one that drives stronger engagement and continuity of care",
    },
    "workforce_productivity": {
        "label": "Workforce productivity",
        "summary": "making it easier for employees to get care before stress, turnover, or absenteeism create operational drag",
    },
    "employee_access_experience": {
        "label": "Employee access & experience",
        "summary": "helping employees find and use quality mental health care quickly and without unnecessary friction",
    },
}


def _safe_lower(value: Optional[str]) -> str:
    return (value or "").lower()


def _first_name(contact: Optional[str]) -> Optional[str]:
    if not contact:
        return None
    return contact.strip().split()[0]


def _generate_subject_line(account: AccountProfile, top_match: ValuePropMatch) -> str:
    company = account.company

    if top_match.value_prop_id == "total_cost_of_care_reduction":
        return f"{company}: behavioral health access + utilization"
    if top_match.value_prop_id == "eap_upgrade":
        return f"{company}: mental health support beyond EAP"
    if top_match.value_prop_id == "workforce_productivity":
        return f"{company}: mental health and workforce stability"
    return f"{company}: mental health access for employees"


def _build_hooks(account: AccountProfile) -> List[str]:
    notes = _safe_lower(account.notes)
    industry = _safe_lower(account.industry)

    hooks: List[str] = []

    if "health system" in industry:
        hooks.append("the scale of Meridian's care footprint" if account.company == "Meridian Health Partners" else "the scale of your care footprint")
    elif "university" in industry:
        hooks.append("the mix of staff and student employees")
    elif "transportation" in industry or "logistics" in industry:
        hooks.append("the reality of a distributed operational workforce")
    elif "forestry" in industry or "natural resources" in industry:
        hooks.append("the challenge of supporting a field-based workforce")
    elif "senior living" in industry or "healthcare" in industry:
        hooks.append("the strain that comes with a high-turnover care workforce")
    elif account.industry:
        hooks.append(account.industry.lower())

    if account.us_employees:
        if account.us_employees >= 10000:
            hooks.append("the scale of the employee population")
        elif account.us_employees >= 3000:
            hooks.append("the size of the workforce")

    if "midwest" in notes:
        hooks.append("a footprint spread across the Midwest")
    if "student employees" in notes:
        hooks.append("a mixed employee population")
    if "merger" in notes or "integrating two separate benefits programs" in notes:
        hooks.append("benefits integration after a merger")
    if "field-based" in notes:
        hooks.append("a field-based workforce")
    if "limited internet access" in notes:
        hooks.append("limited internet access during shifts")
    if "high-turnover" in notes or "turnover" in notes:
        hooks.append("high-turnover roles")
    if "24/7 operations" in notes:
        hooks.append("24/7 operations")
    if "distribution centers" in notes:
        hooks.append("a workforce spread across many sites")
    if "eap" in notes:
        hooks.append("an existing EAP model")
    if "limited benefits budget" in notes:
        hooks.append("a tighter benefits budget")

    deduped: List[str] = []
    for hook in hooks:
        if hook not in deduped:
            deduped.append(hook)

    return deduped[:3]


def _build_context_translation(account: AccountProfile, top_match: ValuePropMatch) -> str:
    notes = _safe_lower(account.notes)
    industry = _safe_lower(account.industry)

    if top_match.value_prop_id == "total_cost_of_care_reduction":
        if "merger" in notes or "benefits programs" in notes:
            return "the harder question may be whether behavioral health is being evaluated as part of broader benefits efficiency, not just employee support"
        if "health system" in industry or (account.us_employees and account.us_employees >= 10000):
            return "one of the harder parts of behavioral health benefits may not be offering support, but making sure employees can actually find in-network care quickly and use it consistently"
        return "behavioral health may matter less as a coverage question and more as a utilization one"

    if top_match.value_prop_id == "eap_upgrade":
        if "modernizing" in notes and "eap" in notes:
            return "the question may be less whether support exists and more whether the current model is deep enough to drive ongoing care"
        if "eap" in notes:
            return "the current support model may be useful for first-touch help, but not necessarily for sustained engagement"
        return "traditional support models often create shallow engagement without much continuity of care"

    if top_match.value_prop_id == "workforce_productivity":
        if "high-turnover" in notes or "turnover" in notes:
            return "mental health may be showing up less as a standalone benefit issue and more through turnover and workforce strain"
        if "24/7 operations" in notes or "distribution centers" in notes:
            return "delayed access to care may be creating downstream drag across a workforce that has to stay operational"
        if "field-based" in notes:
            return "support may be harder to translate into consistent workforce stability when employees are not desk-based"
        return "mental health support may be tied more closely to attendance, retention, and day-to-day performance than it appears on paper"

    if "limited internet access" in notes:
        return "the real challenge may be less about having a benefit in place and more about whether employees can actually access care when they need it"
    if "student employees" in notes:
        return "mixed employee populations often make it harder to deliver a consistent care experience"
    if "distribution centers" in notes or "nationwide" in notes or "midwest" in notes:
        return "distributed workforces often have support on paper but uneven real-world access across sites"
    return "the gap may be less about offering support and more about whether employees can actually find and use care quickly"


def _build_discovery_questions(
    account: AccountProfile,
    top_match: ValuePropMatch,
    second_match: Optional[ValuePropMatch] = None,
) -> List[str]:
    notes = _safe_lower(account.notes)

    if top_match.value_prop_id == "total_cost_of_care_reduction":
        q1 = "Is the bigger challenge today getting employees into care quickly, or getting them to actually use the mental health benefits already in place?"
        q2 = "Do access or utilization look different across locations, teams, or employee populations?"
        q3 = "When behavioral health comes up internally, is it framed more as an employee experience issue or a broader benefits efficiency issue?"

        if "merger" in notes or "benefits programs" in notes:
            q2 = "Has the merger changed where you see the biggest gaps in access, utilization, or benefit consistency?"

        return [q1, q2, q3]

    if top_match.value_prop_id == "eap_upgrade":
        q1 = "How far does engagement typically go today beyond the first EAP interaction?"
        q2 = "Are there specific employee groups where the current support model feels too shallow or inconsistent?"
        q3 = "Would your team be more likely to replace the current model entirely or layer something stronger alongside it?"

        if "modernizing" in notes:
            q3 = "As you modernize the current program, are you thinking more about replacing the model or strengthening it around continuity of care?"

        return [q1, q2, q3]

    if top_match.value_prop_id == "workforce_productivity":
        q1 = "Is mental health showing up more as an absenteeism issue, a turnover issue, or both?"
        q2 = "Are there specific workforce segments or sites where the problem is more visible?"
        q3 = "When you evaluate mental health support, are you optimizing more for employee experience or workforce stability?"

        if "field-based" in notes:
            q2 = "Do field-based employees experience different barriers to support than more centralized teams?"
        elif "distribution centers" in notes or "24/7 operations" in notes:
            q2 = "Are certain sites or operating environments harder to support consistently than others?"

        return [q1, q2, q3]

    q1 = "Where does access tend to break down today: finding providers, speed to care, or employees actually following through?"
    q2 = "Are there specific employee populations or locations where access is harder to solve?"
    q3 = "Is the bigger priority right now improving the care experience itself or improving utilization of the benefit already in place?"

    if "student employees" in notes:
        q2 = "Do staff and student employee populations experience mental health access differently today?"
    elif "limited internet access" in notes:
        q2 = "Do employees in lower-connectivity environments have a harder time actually using available support?"

    return [q1, q2, q3]


def generate_fallback_email(
    account: AccountProfile,
    is_icp: bool,
    icp_reasons: List[str],
    matches: List[ValuePropMatch],
) -> Dict[str, Any]:
    top_match = matches[0]
    second_match = matches[1] if len(matches) > 1 else None

    first_name = _first_name(account.contact)
    greeting = f"Hi {first_name}," if first_name else "Hi,"
    company = account.company

    hooks = _build_hooks(account)
    hook_text = ", ".join(hooks) if hooks else "your current workforce and benefits context"
    translation = _build_context_translation(account, top_match)

    subject = _generate_subject_line(account, top_match)
    questions = _build_discovery_questions(account, top_match, second_match)

    if top_match.value_prop_id == "total_cost_of_care_reduction":
        body = (
            f"{greeting}\n\n"
            f"With {company}'s {hook_text}, I’d guess {translation}. "
            f"For employers at this scale, that usually shows up as a utilization issue, not just a coverage issue.\n\n"
            f"Rula helps employers improve access to quality in-network mental health care in a way that can make the benefit work harder without adding more complexity. "
            f"Is that something your team is looking at right now?"
        )

    elif top_match.value_prop_id == "eap_upgrade":
        body = (
            f"{greeting}\n\n"
            f"With {company}'s {hook_text}, I’d guess {translation}. "
            f"A lot of teams already have support in place, but the real gap is whether people actually stay engaged long enough to get meaningful care.\n\n"
            f"Rula gives employers a stronger path from first touch to ongoing treatment. "
            f"Is that something you're evaluating right now?"
        )

    elif top_match.value_prop_id == "workforce_productivity":
        body = (
            f"{greeting}\n\n"
            f"{company}'s {hook_text} makes me think {translation}. "
            f"In environments like this, delayed access to care tends to show up operationally, not just emotionally.\n\n"
            f"Rula helps employers make it easier for employees to get care quickly, which can matter when the goal is stability as much as support. "
            f"Is that a live conversation for your team?"
        )

    else:
        body = (
            f"{greeting}\n\n"
            f"With {company}'s {hook_text}, I’d guess {translation}. "
            f"For distributed or mixed employee populations, the issue is often less about whether benefits exist and more about whether people can actually use them when they need them.\n\n"
            f"Rula helps employers make care easier to access quickly through a large in-network provider base. "
            f"Is access something your team is actively trying to improve?"
        )

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
    }

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
- Begin with one specific, grounded observation tied to the account
- Use what is true from the account data
- No generic opener
- No empty pleasantries
- No fake compliments

2. Interpretation
- Translate that observation into one likely business, workforce, or benefits problem
- Keep it tight
- Do not over-explain
- Do not repeat the account facts back in a robotic way

3. Reframe
- Introduce the top matched value proposition indirectly, as a lens
- Focus on why it matters in practice
- Keep to one core wedge
- Do not stack multiple value props in the same email

4. Close
- End with one low-friction, curiosity-driven question
- No hard CTA
- No calendar ask
- No pressure language

TONE:
- concise
- human
- warm but not soft
- confident but not loud
- commercially aware
- low-pressure
- natural, not over-personalized
- never sound like a product page, consultant memo, or AI summary

STYLE RULES:
- Keep the email between 75 and 120 words
- Use simple, direct language
- Make the email sound like it was written to one person, not to a segment
- One sharp observation, one implication, one clean ask
- The email should feel like a thoughtful note, not a campaign template

DO NOT:
- invent facts
- assume self-insured status unless explicitly stated
- assume EAP dissatisfaction unless explicitly supported
- explain every possible angle
- summarize the whole account strategy
- use abstract phrases when a concrete one would work better

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
- identify what is actually happening
- force a directional answer when possible

Question 2 = segmentation
- identify where the issue is worst
- focus on location, population, or workforce segment

Question 3 = decision criteria
- identify how the buyer is evaluating the problem or tradeoff
- make them choose between real priorities when possible

DISCOVERY QUESTION CONSTRAINTS:
- every question must test the top matched value proposition
- questions must reflect the account context when possible
- one clean idea per question
- no generic survey questions
- no "what are your priorities?"
- no "tell me about your goals"
- no vague, broad questions that could apply to any company

VALUE PROP GUIDANCE:
- If the top value prop is workforce productivity, ask about absenteeism, turnover, workforce strain, performance, or stability
- If the top value prop is total cost of care reduction, ask about utilization, spend visibility, plan efficiency, or benefits tradeoffs
- If the top value prop is EAP upgrade, ask about continuity of care, engagement after first touch, and replace vs supplement
- If the top value prop is employee access & experience, ask where access breaks down, which populations struggle, and whether employees can actually use the benefit

OUTPUT:
Return valid JSON with exactly these keys:
{
  "email_subject": "...",
  "email_body": "...",
  "discovery_questions": ["...", "...", "..."]
}
"""

    user_prompt = f"""
Write one first-touch email and exactly 3 discovery questions.

Use the account data below.
Lead with the top matched value proposition only.
Stay grounded in the actual facts provided.
Make the email sound human, specific, and low-pressure.

Input:
{json.dumps(prompt_payload, indent=2)}
"""

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
    if not isinstance(questions, list) or len(questions) != 3:
        questions = _build_discovery_questions(account, top_match, second_match)

    return {
        "email_subject": parsed.get("email_subject", _generate_subject_line(account, top_match)),
        "email_body": parsed.get("email_body", generate_fallback_email(account, is_icp, icp_reasons, matches)["email_body"]),
        "discovery_questions": questions,
    }
