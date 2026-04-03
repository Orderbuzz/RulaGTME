README_part2.md` (MAP Verification System)

```markdown
# Part 2 — MAP Verification System

## Overview

The MAP Verification System converts unstructured evidence into:

- Structured campaign commitments
- Confidence scoring
- Evidence quality classification
- Forecast eligibility decisions

---

## Problem

MAP commitments are currently captured via:

- Emails
- Slack messages
- Meeting notes

This creates:

- Inconsistent structure
- High subjectivity
- Risk of pipeline inflation

The core challenge:

> **Distinguishing real commitments from optimistic interpretation**

---

## Approach

The system is a risk-aware verification engine, 

It operates in three stages:

---

### 1. Extract (Structure the Evidence)

Convert raw text into:

- Campaign types
- Timeline markers
- Number of quarters
- Commitment signals
- Next-step signals

---

### 2. Score (Evaluate Commitment Strength)

Scoring considers:

#### Positive Signals
- Buyer-authored confirmation
- Explicit commitment language
- Campaign specificity
- Timeline clarity

#### Negative Signals
- Exploratory language
- Unresolved dependencies
- Seller-authored summaries

Key principle:

> **Secondhand evidence is penalized more than specificity is rewarded**

---

### 3. Decide (Operational Output)

Each MAP is classified as:

- `verified`
- `needs_review`
- `not_verified`

Additional outputs:

- `confidence`
- `score_band` (strong / moderate / weak)
- `evidence_tier` (buyer vs internal)
- `forecast_eligible` (True / False)

---

## Evidence Tiers

- **Tier 1:** Buyer-authored (email, document)
- **Tier 2:** Mixed / unclear
- **Tier 3:** Internal seller summaries (Slack, notes)

---

## Why this matters

The system is designed around a core reality:

> **The highest-risk failure mode is not missing MAPs — it is over-counting them**

A rep can recover a missed MAP.  
Finance cannot recover from inflated pipeline.

---

## Example Outcomes

### Meridian Health Partners
- Buyer-authored email
- Clear campaign plan (Q2–Q4)
- Explicit next step

→ `verified`  
→ `forecast_eligible = True`

---

### TrueNorth Financial Group
- Exploratory language
- No campaign commitment
- Dependency on internal buy-in

→ `not_verified`

---

### Atlas Logistics Group
- Strong plan details
- BUT secondhand (Slack from AE)
- No buyer-authored confirmation

→ `needs_review`  
→ `forecast_eligible = False`

---

## RAG Design

The system uses retrieval to ground scoring against:

- MAP definition
- Strong vs weak signals
- Forecast risk considerations

This ensures:

- Consistency
- Auditability
- Reduced hallucination risk

---

## Future State: Better Capture System

Current capture is unstructured by default.

Recommended flow:

1. AE uploads artifact (email / note / Slack)
2. System auto-extracts:
   - campaigns
   - timeline
   - quarters
3. AE confirms or edits
4. MAP only becomes `verified` when:
   - buyer-authored evidence exists
   - required fields are complete

Goal:

> **Improve data quality without adding friction at the moment of commitment**
