# -*- coding: utf-8 -*-
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


def _safe_lower(value: Optional[str]) -> str:
    return (value or "").lower()


def _first_name(contact: Optional[str]) -> Optional[str]:
    if not contact:
        return None
    return contact.split()[0].strip()


def _generate_subject_line(account: AccountProfile, top_match: ValuePropMatch) -> str:
    company = account.company

    if top_match.value_prop_id == "total_cost_of_care_reduction":
        return f"{company}: behavioral health access + utilization"
    if top_match.value_prop_id == "eap_upgrade":
        return f"{company}: mental health support beyond EAP"
    if top_match.value_prop_id == "workforce_productivity":
        return f"{company}: mental health and workforce stability"
    return f"{company}: improving mental health access for employees"


def _build_personalization_hooks(account: AccountProfile) -> List[str]:
    hooks: List[str] = []

    industry = _safe_lower(account.industry)
    notes = _safe_lower(account.notes)

    if "health system" in industry:
        hooks.append("the scale of your care footprint")
    elif "university" in industry:
        hooks.append("the mix of staff and student employees")
    elif "transportation" in industry or "logistics" in industry:
        hooks.append("the reality of a distributed operational workforce")
    elif "forestry" in industry or "natural resources" in industry:
        hooks.append("the challenge of supporting a field-based workforce")
    elif "senior living" in industry or "healthcare" in industry:
        hooks.append("the strain that comes with a high-turnover care workforce")
    elif account.industry:
        hooks.append(account.industry)

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

    if top_match.value_prop_id == "workforce_productivity":
        if "high-turnover" in notes or "turnover" in notes:
            return "mental health may be showing up less as a standalone benefit issue and more through turnover and workforce strain"
        if "24/7 operations" in notes or "distribution centers" in notes:
            return "delayed access to care may be creating downstream drag across a workforce that has to stay operational"
        if "field-based" in notes:
            return "support may be harder to translate into consistent workforce stability when people are not desk-based"
        return "mental health support may be tied more closely to attendance, retention, and day-to-day performance than it looks on paper"

    if top_match.value_prop_id == "total_cost_of_care_reduction":
        if "merger" in notes or "benefits programs" in notes:
            return "the harder question may be whether behavioral health is being evaluated as part of broader benefits efficiency, not just employee support"
        if account.us_employees and account.us_employees >= 10000:
            return "one of the harder parts of behavioral health benefits may not be offering support, but making sure people can actually find in-network care quickly and use it consistently"
        return "behavioral health may matter less as a coverage question and more as a utilization one"

    if top_match.value_prop_id == "eap_upgrade":
        if "eap" in notes and "modernizing" in notes:
            return "the question may be less whether support exists and more whether the current model is deep enough to drive ongoing care"
        if "eap" in notes:
            return "the current support model may be useful for first-touch help, but not necessarily for sustained engagement"
        return "traditional support models often create shallow engagement without much continuity of care"

    if "limited internet access" in notes:
        return "the real challenge may be less about having a benefit in place and more about whether people can actually access care when they need it"
    if "student employees" in notes:
        return "mixed employee populations often make it harder to deliver a consistent experience across different groups"
    if "distribution centers" in notes or "nationwide" in notes or "midwest" in notes:
        return "distributed workforces often have support on paper but uneven real-world access across sites"
    if "education" in industry or "university" in industry:
        return "the bigger question may be whether people can actually find and use care quickly when they need it"
    return "the gap may be less about offering support and more about whether people can actually find and use care quickly"


def _build_discovery_questions(
    account: AccountProfile,
    top_match: ValuePropMatch,
) -> List[str]:
    notes = _safe_lower(account.notes)

    if top_match.value_prop_id == "workforce_productivity":
        q1 = "Is mental health showing up more as an absenteeism issue, a turnover issue, or both?"
        q2 = "Are there specific workforce segments or sites where the problem is more visible?"
        q3 = "When you evaluate mental health support, are you optimizing more for employee experience or workforce stability?"

        if "field-based" in notes:
            q2 = "Do field-based employees experience different barriers to support than more centralized teams?"
        elif "distribution centers" in notes or "24/7 operations" in notes:
            q2 = "Are certain sites or operating environments harder to support consistently than others?"
        elif "cnas" in notes or "lpns" in notes:
            q2 = "Are there particular care roles where stress, turnover, or absenteeism makes mental health support more operationally important?"

        return [q1, q2, q3]

    if top_match.value_prop_id == "total_cost_of_care_reduction":
        q1 = "Is the bigger challenge today getting people into care quickly, or getting them to actually use the mental health benefits already in place?"
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

    q1 = "Where does access tend to break down today: finding providers, speed to care, or people actually following through?"
    q2 = "Are there specific employee populations or locations where access is harder to solve?"
    q3 = "Is the bigger priority right now improving the care experience itself or improving utilization of the benefit already in place?"

    if "student employees" in notes:
        q2 = "Do staff and student employee populations experience mental health access differently today?"
    elif "limited internet access" in notes:
        q2 = "Do people in lower-connectivity environments have a harder time actually using available support?"
    elif "distribution centers" in notes or "nationwide" in notes or "midwest" in notes:
        q2 = "Are certain sites or geographies harder to support consistently than others?"

    return [q1, q2, q3]


def generate_fallback_email(
    account: AccountProfile,
    is_icp: bool,
    icp_reasons: List[str],
    matches: List[ValuePropMatch],
) -> Dict[str, Any]:
    top_match = matches[0]
    first_name = _first_name(account.contact)
    greeting = f"Hi {first_name}," if first_name else "Hi,"
    company = account.company

    hooks = _build_personalization_hooks(account)
    hook_text = ", ".join(hooks) if hooks else "your current workforce and benefits context"
    translation = _build_context_translation(account, top_match)

    subject = _generate_subject_line(account, top_match)
    questions = _build_discovery_questions(account, top_match)

    if top_match.value_prop_id == "total_cost_of_care_reduction":
        body = (
            f"{greeting}\n\n"
            f"With {hook_text}, I'd guess {translation}. "
            f"For employers at this scale, that usually shows up as a utilization issue, not just a coverage issue.\n\n"
            f"Rula helps employers improve access to quality in-network mental health care in a way that can make the benefit work harder without adding more complexity. "
            f"Is that something your team is looking at right now?"
        )

    elif top_match.value_prop_id == "eap_upgrade":
        body = (
            f"{greeting}\n\n"
            f"With {hook_text}, I'd guess {translation}. "
            f"A lot of teams already have support in place, but the real gap is whether people stay engaged long enough to get meaningful care.\n\n"
            f"Rula gives employers a stronger path from first touch to ongoing treatment. "
            f"Is that something you're evaluating right now?"
        )

    elif top_match.value_prop_id == "workforce_productivity":
        body = (
            f"{greeting}\n\n"
            f"{company}'s {hook_text} makes me think {translation}. "
            f"In environments like this, delayed access to care tends to show up operationally, not just emotionally.\n\n"
            f"Rula helps employers make it easier for people to get care quickly, which can matter when the goal is stability as much as support. "
            f"Is that a live conversation for your team?"
        )

    else:
        body = (
            f"{greeting}\n\n"
            f"With {hook_text}, I'd guess {translation}. "
            f"A lot of teams have benefits in place, but still run into friction when people actually try to find and use care.\n\n"
            f"Rula helps employers make care easier to access quickly through a large in-network provider base. "
            f"Curious whether access or follow-through is more of the issue on your side."
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

    prompt_payload = {
        "account": account.model_dump(),
        "icp": {
            "is_icp": is_icp,
            "reasons": icp_reasons,
        },
        "top_value_prop": top_match.model_dump(),
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
- Begin with one natural, conversational observation tied to the account
- It should feel like something you would say out loud, not write in a report
- Use soft language when appropriate (e.g., "I'd imagine", "I'd guess")
- Do not list attributes or restate structured data
- Do not sound analytical or overly formal
- Let the sentence breathe slightly and avoid overly compressed phrasing

2. Interpretation
- Translate that observation into one likely business, workforce, or benefits problem
- Add light nuance (e.g., "especially across different groups", "in practice")
- Keep it grounded and human
- Do not over-explain

3. Reframe
- Introduce the top matched value proposition indirectly
- Focus on how this shows up in real life, not abstract value
- Stay focused on one wedge only

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
- natural rhythm

STYLE RULES:
- 75-120 words
- Use contractions
- Prefer "teams" over "organizations"
- Prefer "people" over "employees" when natural
- Add light connective language for flow
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
- Workforce productivity -> absenteeism, turnover, workforce strain
- Total cost -> utilization, spend efficiency, tradeoffs
- EAP -> engagement depth, continuity, replace vs supplement
- Access -> where access breaks down, who struggles, follow-through

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
        temperature=0.5,
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
        questions = _build_discovery_questions(account, top_match)

    fallback = generate_fallback_email(account, is_icp, icp_reasons, matches)

    return {
        "email_subject": parsed.get("email_subject", fallback["email_subject"]),
        "email_body": parsed.get("email_body", fallback["email_body"]),
        "discovery_questions": questions,
    }
