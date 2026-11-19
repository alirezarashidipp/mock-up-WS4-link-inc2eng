from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RankedCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    candidate_number: int = Field(
        ge=1,
        description="The supplied candidate_number of this engagement within the current incident's options."
    )
    incident_citation: str = Field(
        description=(
            "Evidence from the incident supporting or challenging this candidate, formatted as "
            "'column_name: verbatim source text'. Use the exact incident column name."
        )
    )
    engagement_citation: str = Field(
        description=(
            "Evidence from this candidate's engagement record, formatted as "
            "'column_name: verbatim source text'. Use the exact engagement column name."
        )
    )
    rationale: str = Field(
        description="Explain how the incident and engagement evidence support this rank and identify any important conflict."
    )


class LinkingDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    candidates: list[RankedCandidate] = Field(
        description=(
            "All plausible distinct supplied engagements identified by candidate_number, strongest evidence first. "
            "Return an empty list if none is plausible with evidence from both records."
        ),
    )
    incident_evidence_strength: Literal["UNSUPPORTED", "WEAK", "MODERATE", "STRONG"] = Field(
        description=(
            "Quality and sufficiency of the incident evidence for identifying the affected service and its scope. "
            "UNSUPPORTED means no usable evidence. WEAK means indirect or ambiguous evidence. "
            "MODERATE means relevant evidence with a material gap or conflict. "
            "STRONG means clear, specific evidence with no unresolved material conflict."
        )
    )
    decision_reason: str = Field(
        description=(
            "Explain why an engagement was selected or why the incident was left unlinked, and why the "
            "confidence tag fits. Explain how incident evidence quality affects the decision "
            "and address the closest alternative when present."
        )
    )
    link_decision: Literal["LINKED", "NOT_LINKED"] = Field(
        description=(
            "LINKED when evidence distinguishes one engagement, ranked first. NOT_LINKED when ambiguity, "
            "missing information or unsuitable options prevent selecting an engagement."
        )
    )
    linked_strength: Literal["WEAK", "MODERATE", "STRONG"] | None = Field(
        description=(
            "Strength of evidence connecting the incident's affected service to the selected engagement. "
            "WEAK means limited indirect support. MODERATE means relevant service and scope evidence with a "
            "remaining gap. STRONG means clear, specific, consistent evidence with no unresolved material conflict. "
            "Required for LINKED. Use null for NOT_LINKED."
        )
    )
    linked_strength_reason: str | None = Field(
        description=(
            "One/Two concise sentences explaining why the evidence for the selected engagement warrants linked_strength. "
            "Identify the supporting detail and any important limitation. Required for LINKED. Use null for NOT_LINKED."
        )
    )
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description=(
            "Confidence in the overall decision, including a decision to leave the incident unlinked. "
            "LOW means substantial doubt remains. MEDIUM means meaningful doubt remains but the decision is "
            "reasonably supported. HIGH means limited doubt remains about the appropriateness of the decision."
        )
    )
