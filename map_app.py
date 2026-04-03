import streamlit as st
from map_data import MAP_EVIDENCE
from map_verifier import verify_map

st.set_page_config(page_title="Rula MAP Verifier", layout="wide")
st.title("Rula MAP Verification Prototype")

st.write(
    "This prototype uses a retrieval-grounded verification flow to turn messy MAP evidence "
    "into structured fields, a confidence score, and follow-up actions."
)

accounts = [item["account"] for item in MAP_EVIDENCE]
selected = st.selectbox("Choose evidence sample", accounts)

evidence = next(item for item in MAP_EVIDENCE if item["account"] == selected)

with st.expander("Raw Evidence", expanded=True):
    st.json(evidence)

if st.button("Run MAP Verification"):
    result = verify_map(evidence)

    left, right = st.columns([1, 1.2])

    with left:
        st.subheader("Verdict")
        st.write(f"**Account:** {result['account']}")
        st.write(f"**Verdict:** {result['verdict']}")
        st.write(f"**Confidence:** {result['confidence']}")
        st.write(f"**Score:** {result['score']}")

        st.subheader("Structured Extraction")
        st.json(result["structured_extraction"])

        st.subheader("Follow-up Actions")
        if result["follow_up_actions"]:
            for action in result["follow_up_actions"]:
                st.write(f"- {action}")
        else:
            st.write("- None")

    with right:
        st.subheader("Why")
        for reason in result["reasons"]:
            st.write(f"- {reason}")

        st.subheader("Retrieved Rubric Context")
        st.json(result["retrieved_rubric_context"])

    with st.expander("Full Structured Output"):
        st.json(result)
