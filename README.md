. **MAP Verification System (Part 2)**  
   Converts messy, unstructured evidence into structured commitments, confidence scores, and forecast eligibility decisions.

---

## Why this matters

Employer sales is not constrained by lead volume — it’s constrained by:

- **Prioritization quality** (who should we go after?)
- **Pipeline integrity** (which deals are real vs inflated?)

Most systems optimize for activity.

This system optimizes for:

> **Decision quality under uncertainty and incentive pressure**

---

## System Overview


Account Assignment
↓
[Part 1] Prospecting Agent
↓
First Touch + Discovery
↓
Pipeline Progression
↓
MAP Evidence Captured
↓
[Part 2] MAP Verification System
↓
Forecast Eligibility Decision


---

## Design Principles

- **Intent ≠ readiness** → prioritize based on context, not activity
- **Extraction before generation** → structure drives better outputs
- **Secondhand evidence is risky** → penalize it explicitly
- **False positives are more expensive than false negatives**
- **Systems should be auditable, not just intelligent**

---

## Tech Stack

- Python
- Streamlit (UI)
- Rule-based scoring + retrieval grounding (RAG-lite)
- Modular architecture (matcher, generator, verifier)

---

## How to Run
Part 1 — Prospecting Agent

```bash
streamlit run app.py

Part 2 — MAP Verification
streamlit run map_app.py
