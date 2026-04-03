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
        "short": "reducing behavioral health spend by improving in-network utilization",
        "diagnostic_focus": "utilization, spend, plan value, and benefit tradeoffs",
    },
    "eap_upgrade": {
        "short": "replacing or supplementing an underperforming EAP with a model that drives ongoing engagement",
        "diagnostic_focus": "continuity of care, engagement beyond first touch, and whether the current model is enough",
    },
    "workforce_productivity": {
        "short": "improving workforce performance by helping people access care faster and stay engaged at work",
        "diagnostic_focus": "absenteeism, turnover, attendance pressure, and workforce strain",
    },
    "employee_access_experience": {
        "short": "making it easier for people to access affordable, quality mental health care quickly",
        "diagnostic_focus": "where access breaks down, which populations struggle most, and whether people can actually use the benefit",
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
        return f"Thinking about behavioral health spend at {company}"
    if top_match.value_prop_id == "eap_upgrade":
        return f"{company}: mental health support beyond EAP"
    if top_match.value_prop_id == "workforce_productivity":
        return f"How {company} is managing workforce strain"
    return f"Making mental health support easier to use at {company}"


def _opening_observation(account: AccountProfile, top_match: ValuePropMatch) -> str:
    notes = _safe_lower(account.notes)
    industry = _safe_lower(account.industry)

    if top_match.value_prop_id == "total_cost_of_care_reduction":
        if "health system" in industry and ("midwest" in notes or "hospitals" in notes or "clinics" in notes):
            return "Given the size and spread across hospitals and clinics"
        if "merger" in notes or "benefits programs" in notes:
            return "With benefits integration happening after the merger"
        if account.us_employees and account.us_employees >= 10000:
            return "At your scale"
        return "Given the size of the workforce"

    if top_match.value_prop_id == "eap_upgrade":
        if "eap" in notes and "modernizing" in notes:
            return "With an in-house EAP already in place and modernization on the table"
        if "eap" in notes:
            return "With an existing EAP already in place"
        return "Given how most support models work in practice"

    if top_match.value_prop_id == "workforce_productivity":
        if "24/7 operations" in notes and "distribution centers" in notes:
            return "With Atlas running 24/7 across 30+ distribution centers" if account.company == "Atlas Logistics Group" else "Running 24/7 operations across that many sites"
        if "field-based" in notes and "limited internet access" in notes:
            return "With so many folks working in the field and limited internet during shifts"
        if "high-turnover" in notes or "turnover" in notes:
            return "With a workforce that sees a lot of turnover"
        return "Given the reality of the workforce"

    if "student employees" in notes:
        return "Given the mix of staff and student employees"
    if "limited internet access" in notes:
        return "With limited internet access during shifts"
    if "distribution centers" in notes or "nationwide" in notes:
        return "With people spread across that many sites"
    return "Given the setup of the workforce"


def _problem_interpretation(account: AccountProfile, top_match: ValuePropMatch) -> str:
    notes = _safe_lower(account.notes)
    industry = _safe_lower(account.industry)

    if top_match.value_prop_id == "total_cost_of_care_reduction":
        if "health system" in industry:
            return "I'd imagine keeping behavioral health spend under control while still making access easy isn't straightforward"
        if "merger" in notes or "benefits programs" in notes:
            return "I'd imagine the harder part is figuring out how behavioral health fits into a more efficient combined benefits model"
        return "I'd imagine the real question is whether people are actually using the benefit in a way that creates plan value"

    if top_match.value_prop_id == "eap_upgrade":
        if "modernizing" in notes and "eap" in notes:
            return "I'd imagine the question is less whether support exists and more whether the current model is deep enough to hold up over time"
        if "eap" in notes:
            return "I'd imagine the gap is less first-touch support and more whether people actually stay engaged long enough to get meaningful care"
        return "I'd imagine the issue is whether support goes deep enough to create real continuity of care"

    if top_match.value_prop_id == "workforce_productivity":
        if "24/7 operations" in notes or "distribution centers" in notes:
            return "I'd guess even small gaps in attendance or focus can ripple quickly through operations"
        if "field-based" in notes and "limited internet access" in notes:
            return "I'd guess keeping productivity steady gets tricky when people can't easily access support that fits their day-to-day"
        if "high-turnover" in notes or "turnover" in notes:
            return "I'd imagine mental health shows up less as a benefits issue and more through turnover and day-to-day strain"
        return "I'd imagine mental health support is showing up more through attendance and retention than it does in benefits language"

    if "student employees" in notes:
        return "I'd imagine making support feel consistent across different groups isn't straightforward"
    if "limited internet access" in notes:
        return "I'd imagine the harder part is whether people can realistically access care in the moment they need it"
    if "distribution centers" in notes or "nationwide" in notes:
        return "I'd imagine access gets uneven pretty quickly across locations and schedules"
    return "I'd imagine the gap is less whether support exists and more whether people can actually use it"


def _operational_consequence_line(account: AccountProfile, top_match: ValuePropMatch, is_icp: bool) -> str:
    notes = _safe_lower(account.notes)
    industry = _safe_lower(account.industry)

    if top_match.value_prop_id == "workforce_productivity":
        if "distribution centers" in notes or "24/7 operations" in notes:
            return "That's when you start to see certain shifts run short, stronger sites absorb more load, or managers spend more time patching coverage than they should."
        if "field-based" in notes and "limited internet access" in notes:
            return "In setups like that, it usually shows up through attendance dips, uneven crew coverage, or extra load landing on the people who are still available."
        if "high-turnover" in notes or "turnover" in notes or "cnas" in notes or "lpns" in notes:
            return "That usually shows up as teams getting stretched thinner, new hires cycling through too fast, and the most reliable people carrying extra weight."
        return "That's usually where you start seeing attendance slip, coverage get uneven, or stronger teams absorb more load than they should."

    if top_match.value_prop_id == "employee_access_experience":
        if "student employees" in notes:
            return "That usually means one group can navigate support pretty easily while another drops off somewhere between searching for care and actually booking it."
        if "limited internet access" in notes:
            return "What that looks like in practice is people delaying care, dropping off mid-process, or never using the benefit when they actually need it."
        if "distribution centers" in notes or "nationwide" in notes or "midwest" in notes:
            return "What that usually creates is a benefit that looks consistent on paper but lands very differently depending on site, schedule, or geography."
        return "What that usually creates is a gap between having support available and people actually being able to use it when they need it."

    if top_match.value_prop_id == "total_cost_of_care_reduction":
        if "health system" in industry:
            return "That can leave the plan carrying more avoidable spend than it should while local teams still feel like access is inconsistent."
        if "merger" in notes or "benefits programs" in notes:
            return "That usually shows up as uneven utilization patterns, duplicated plan complexity, or a lot of uncertainty around what's actually working."
        return "That usually leaves teams looking at spend and support separately when the real issue is how the benefit gets used in practice."

    if top_match.value_prop_id == "eap_upgrade":
        if "eap" in notes and "modernizing" in notes:
            return "That usually shows up as a lot of first-touch activity without much confidence that people are actually getting to sustained care."
        if "eap" in notes:
            return "What that often creates is a support model that gets used early but doesn't carry enough continuity to change much downstream."
        return "That usually creates a support model that's easy to offer but harder to rely on when people need more than a first conversation."

    if not is_icp:
        return "That usually surfaces as uneven follow-through, local workarounds, or support that exists on paper but doesn't translate cleanly in practice."

    return "That usually surfaces as uneven adoption, inconsistent follow-through, or a benefit that doesn't land the same way across the business."


def _reframe_line(account: AccountProfile, top_match: ValuePropMatch, is_icp: bool) -> str:
    notes = _safe_lower(account.notes)

    if top_match.value_prop_id == "total_cost_of_care_reduction":
        if is_icp:
            return "The gap is usually not coverage - it's whether people find and use the right in-network care in practice."
        return "What tends to get missed is whether the benefit is actually driving the kind of utilization the plan is supposed to support."

    if top_match.value_prop_id == "eap_upgrade":
        if is_icp:
            return "The issue usually isn't whether support exists - it's whether the model is strong enough to move people from first touch into ongoing care."
        return "The issue is usually less access to a resource and more whether that resource is enough on its own."

    if top_match.value_prop_id == "workforce_productivity":
        if "field-based" in notes and "limited internet access" in notes:
            return "In setups like that, the real question is whether support is accessible enough to matter in the moment people need it."
        if "distribution centers" in notes or "24/7 operations" in notes:
            return "The real question is whether support fits the way people actually work across shifts, sites, and day-to-day operating pressure."
        return "What tends to matter is whether support is accessible enough to change what shows up operationally."

    if is_icp:
        return "In a lot of cases, the gap isn't whether support exists - it's whether people actually find and follow through with care when they need it."
    return "What tends to get in the way isn't the benefit on paper - it's whether people can realistically use it when they need it."


def _close_question(account: AccountProfile, top_match: ValuePropMatch, is_icp: bool) -> str:
    notes = _safe_lower(account.notes)

    if top_match.value_prop_id == "total_cost_of_care_reduction":
        if "merger" in notes:
            return "How are you thinking about behavioral health as part of the broader benefits integration work?"
        return "How are you currently tracking where behavioral health spend is actually coming from across your sites?"

    if top_match.value_prop_id == "eap_upgrade":
        if "modernizing" in notes:
            return "As you think about modernizing the program, what feels most in need of change right now?"
        return "How are you evaluating whether the current support model is actually enough?"

    if top_match.value_prop_id == "workforce_productivity":
        if "field-based" in notes:
            return "Have you seen this hit certain crews or roles harder than others?"
        if "distribution centers" in notes or "24/7 operations" in notes:
            return "Are there certain sites or shifts where this shows up more than others right now?"
        return "Is workforce strain showing up more through absenteeism, turnover, or something else right now?"

    if "student employees" in notes:
        return "What's been the clearest sign on your end that access isn't working the way it should?"
    return "Where does access seem to break down most today?"


def _build_discovery_questions(account: AccountProfile, top_match: ValuePropMatch) -> List[str]:
    notes = _safe_lower(account.notes)

    if top_match.value_prop_id == "workforce_productivity":
        q1 = "How are mental health challenges currently impacting attendance or turnover?"
        q2 = "Are there specific workforce segments or sites where the problem is more visible?"
        q3 = "When considering solutions, how do you weigh ease of access to mental health care against the goal of reducing absenteeism or turnover?"

        if "field-based" in notes:
            q1 = "How are mental health challenges currently impacting attendance or turnover among your field teams?"
            q2 = "Are there specific groups within your workforce where productivity strain linked to mental health is most visible?"
        elif "distribution centers" in notes or "24/7 operations" in notes:
            q1 = "How are mental health-related issues currently impacting attendance or turnover at your busiest distribution centers?"
            q2 = "Are there specific shifts or locations where workforce strain linked to mental health challenges is most visible?"
            q3 = "When evaluating mental health support options, how do you balance faster access to care with measurable improvements in workforce productivity?"

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

    subject = _generate_subject_line(account, top_match)
    opening = _opening_observation(account, top_match)
    problem = _problem_interpretation(account, top_match)
    consequence = _operational_consequence_line(account, top_match, is_icp)
    reframe = _reframe_line(account, top_match, is_icp)
    close = _close_question(account, top_match, is_icp)
    questions = _build_discovery_questions(account, top_match)

    body = (
        f"{greeting}\n\n"
        f"{opening}, {problem}.\n"
        f"{consequence}\n\n"
        f"{reframe}\n\n"
        f"{close}"
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
    fallback = generate_fallback_email(account, is_icp, icp_reasons, matches)

    if client is None:
        return fallback

    top_match = matches[0]

    prompt_payload = {
        "account": account.model_dump(),
        "icp": {
            "is_icp": is_icp,
            "reasons": icp_reasons,
        },
        "top_value_prop": top_match.model_dump(),
        "value_prop_definitions": VALUE_PROP_SUMMARIES,
        "fallback_email_style_reference": fallback,
    }

    system_prompt = """
You are writing outbound emails for an AE selling Rula to benefits and HR leaders.

Write:
1. one first-touch email
2. exactly 3 discovery questions

The message should feel relevant, emotionally intelligent, commercially aware, and naturally written by a sharp AE.

CORE RULE:
The email should sound like someone who has seen this kind of problem before - not like someone summarizing account attributes.

EMAIL GOAL:
Earn a reply by showing a strong point of view based on the account context.

TONE MODES:
If the account is strong ICP:
- be more directional
- sound confident
- make a sharper inference

If the account is not strong ICP:
- be more diagnostic
- make fewer assumptions
- probe more than pitch

EMAIL STRUCTURE:
1. Opening
- Begin with one natural, conversational observation tied to the account
- It should feel like something you would say out loud, not write in a report
- Use soft language when appropriate (e.g., "I'd imagine", "I'd guess")
- Do not list attributes or restate structured data
- Let the sentence breathe slightly

2. Interpretation
- Translate that observation into one likely business, workforce, or benefits problem
- Keep it grounded and human
- Do not over-explain

3. Operational consequence
- Describe one concrete way the problem shows up inside the business
- Make it visual and real
- Examples: shifts running short, managers patching coverage, certain teams carrying extra load, uneven follow-through, site-to-site inconsistency

4. Reframe
- Explain what the real issue usually is beneath the surface
- Introduce the top matched value proposition indirectly
- Focus on one wedge only

5. Close
- End with one low-friction, curiosity-driven question
- No meeting ask
- No pressure language

STYLE RULES:
- 85-130 words
- Use contractions
- Prefer "teams" over "organizations"
- Prefer "people" over "employees" when natural
- Keep the rhythm human, not over-edited

DO NOT:
- invent facts
- assume self-insured status unless explicitly stated
- assume EAP dissatisfaction unless explicitly supported
- explain multiple value props
- summarize the whole account
- sound like a consultant, product page, or AI system
- use "we've seen", "we often see", "many organizations", or "in situations like this"
- use "worth comparing notes"
- use "it felt worth reaching out"
- use "there may be a fit around"

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

Use the fallback example only as a style guardrail, not as a template to copy.

Input:
{json.dumps(prompt_payload, indent=2)}
"""

    try:
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

        return {
            "email_subject": parsed.get("email_subject", fallback["email_subject"]),
            "email_body": parsed.get("email_body", fallback["email_body"]),
            "discovery_questions": questions,
        }

    except Exception as e:
        print(f"LLM failed, falling back: {e}")
        return fallback
