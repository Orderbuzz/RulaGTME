MAP_RUBRIC = [
    {
        "id": "map_definition",
        "title": "What a MAP is",
        "content": (
            "A MAP is an employer commitment to actively run campaigns over multiple quarters. "
            "It should specify campaign types, launch timing, and duration."
        ),
    },
    {
        "id": "strong_commitment_signals",
        "title": "Strong commitment signals",
        "content": (
            "Strong signals include buyer-authored confirmation, explicit agreement to move forward, "
            "specific campaign types, timeline by quarter or month, and a concrete next step."
        ),
    },
    {
        "id": "weak_commitment_signals",
        "title": "Weak commitment signals",
        "content": (
            "Weak signals include seller-authored notes, expressions of interest without campaign specifics, "
            "exploratory language, unresolved dependencies, and no buyer-confirmed next step."
        ),
    },
    {
        "id": "verification_risk",
        "title": "Verification risk",
        "content": (
            "MAP data is used for quota and forecasting. False positives are costly. "
            "Secondhand summaries should score lower than buyer-authored evidence."
        ),
    },
]

MAP_EVIDENCE = [
    {
        "account": "Meridian Health Partners",
        "source_type": "email",
        "source_author": "David Chen",
        "source_role": "VP, Total Rewards",
        "date": "2026-02-14",
        "text": (
            "Thanks for the presentation yesterday. We're excited to move forward with Rula. "
            "I've spoken with our benefits team and we'd like to plan for a launch email in Q2, "
            "followed by a benefits insert for open enrollment in Q3, and a manager wellness toolkit in Q4. "
            "Let's set up a call next week to finalize the calendar. Looking forward to it."
        ),
    },
    {
        "account": "TrueNorth Financial Group",
        "source_type": "meeting_notes",
        "source_author": "AE notes",
        "source_role": "Internal seller notes",
        "date": "2026-02-10",
        "text": (
            "James mentioned they're interested in exploring Rula as part of their post-merger benefits "
            "consolidation. He wants to see a proposal for how Rula could be positioned in the new unified "
            "benefits package. No commitment to specific campaigns yet, but he said 'we're definitely looking "
            "at Q3 at the earliest.' He needs to get buy-in from the integration team first."
        ),
    },
    {
        "account": "Atlas Logistics Group",
        "source_type": "slack",
        "source_author": "AE to manager",
        "source_role": "Internal seller message",
        "date": "2026-02-12",
        "text": (
            "Just got off the phone with Rachel at Atlas. She's in. They want to do a big launch in March "
            "- email blast to all 11k employees plus posters at every distribution center. She said they'd "
            "commit to quarterly campaigns for the full year. Going to send the MAP doc tomorrow."
        ),
    },
]
