from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RankedCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    engagement_id: str = Field(
        description="Exact ENGAGEMENT_ID from this candidate's supplied engagement record."
    )
    rationale: str = Field(
        description="Explain how the incident and engagement evidence support this rank and identify any important conflict."
    )
    incident_field: str = Field(
        description="Exact name of the incident field from which incident_quote was copied."
    )
    incident_quote: str = Field(
        description="Short verbatim excerpt from incident_field that bears on this candidate's fit."
    )
    engagement_field: str = Field(
        description="Exact name of the field in this candidate's engagement record from which engagement_quote was copied."
    )
    engagement_quote: str = Field(
        description="Short verbatim excerpt from engagement_field that bears on this candidate's fit."
    )


class LinkingDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    candidates: list[RankedCandidate] = Field(
        max_length=3,
        description=(
            "Up to three distinct supplied engagements, strongest evidence first. "
            "Return an empty list if none is plausible with evidence from both records."
        ),
    )
    link_decision: Literal["LINKED", "AMBIGUOUS", "INSUFFICIENT_EVIDENCE", "NO_SUITABLE_CANDIDATE"] = Field(
        description=(
            "LINKED when evidence distinguishes one engagement. AMBIGUOUS when two or more are plausible "
            "with no clear winner. INSUFFICIENT_EVIDENCE when missing information prevents a decision. "
            "NO_SUITABLE_CANDIDATE when the evidence rules out all supplied engagements."
        )
    )
    selected_engagement_id: str | None = Field(
        description="ENGAGEMENT_ID of the first-ranked candidate for LINKED. Use null for every other decision."
    )
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description=(
            "Confidence in the overall decision, including a decision to leave the incident unlinked. "
            "HIGH indicates clear direct evidence, MEDIUM indirect or incomplete support, and LOW material uncertainty."
        )
    )
    decision_reason: str = Field(
        description=(
            "Explain why an engagement was selected or why the incident was left unlinked, and why the "
            "confidence tag fits. Address the closest alternative when present."
        )
    )
