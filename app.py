import json
import streamlit as st

from schemas import AccountProfile, ProspectOutput
from matcher import rule_based_match
from generator import generate_with_llm
from evaluator import evaluate_output


st.set_page_config(page_title="Rula Prospecting Agent", layout="wide")
st.title("Rula Prospecting Agent Prototype")

st.write(
    "This prototype takes a structured account profile, checks ICP fit, matches the most relevant "
    "Rula value propositions, generates a first-touch email and discovery questions, and flags outputs "
    "that may need human review."
)


@st.cache_data
def load_sample_accounts():
    with open("data/sample_accounts.json", "r") as f:
        return json.load(f)


sample_accounts = load_sample_accounts()
company_names = [a["company"] for a in sample_accounts]

selected_company = st.selectbox("Choose a sample account", company_names)
selected_account_raw = next(a for a in sample_accounts if a["company"] == selected_company)
account = AccountProfile(**selected_account_raw)

with st.expander("Account Profile", expanded=True):
    st.json(account.model_dump())

run_clicked = st.button("Run Prospecting Agent")

if run_clicked:
    match_result = rule_based_match(account)
    matches = match_result["matched_value_props"]

    generation = generate_with_llm(
        account=account,
        is_icp=match_result["is_icp"],
        icp_reasons=match_result["icp_reasons"],
        matches=matches,
    )

    quality_score, review_required, review_reasons = evaluate_output(
        account=account,
        matches=matches,
        email_body=generation["email_body"],
        discovery_questions=generation["discovery_questions"],
    )

    output = ProspectOutput(
        is_icp=match_result["is_icp"],
        icp_confidence=match_result["icp_confidence"],
        icp_reasons=match_result["icp_reasons"],
        matched_value_props=matches,
        email_subject=generation["email_subject"],
        email_body=generation["email_body"],
        discovery_questions=generation["discovery_questions"],
        quality_score=quality_score,
        review_required=review_required,
        review_reasons=review_reasons,
    )

    left, right = st.columns([1, 1.2])

    with left:
        st.subheader("ICP Assessment")
        st.write(f"**Is ICP:** {output.is_icp}")
        st.write(f"**ICP Confidence:** {output.icp_confidence}")
        if output.icp_reasons:
            st.write("**ICP Reasons**")
            for reason in output.icp_reasons:
                st.write(f"- {reason}")

        st.subheader("Matched Value Propositions")
        for idx, match in enumerate(output.matched_value_props, start=1):
            st.markdown(f"**{idx}. {match.value_prop_name}**")
            st.write(f"Confidence: {match.confidence}")
            for reason in match.reasoning:
                st.write(f"- {reason}")

        st.subheader("Evaluation")
        st.write(f"**Quality Score:** {output.quality_score}/10")
        st.write(f"**Review Required:** {output.review_required}")
        if output.review_reasons:
            st.write("**Review Reasons**")
            for reason in output.review_reasons:
                st.write(f"- {reason}")

    with right:
        st.subheader("Generated Email")
        st.write(f"**Subject:** {output.email_subject}")
        st.write(output.email_body)

        st.subheader("Discovery Questions")
        for question in output.discovery_questions:
            st.write(f"- {question}")

    with st.expander("Structured Output JSON"):
        st.json(output.model_dump())
