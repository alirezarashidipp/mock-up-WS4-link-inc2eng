from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EngagementAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    candidate_number: int = Field(ge=1, description="Number assigned to this engagement in the request.")
    incident_evidence: list[str] = Field(
        description="Zero or more incident excerpts supporting or challenging this link, each as 'column_name: verbatim excerpt'."
    )
    engagement_evidence: list[str] = Field(
        description="Zero or more excerpts from this candidate's source record, each as 'column_name: verbatim excerpt'."
    )
    link_rationale: str = Field(
        description="Explain the connection between the affected service and this engagement's scope, including material gaps or conflicts."
    )
    link_decision: Literal["LINKED", "NOT_LINKED"] = Field(
        description="LINKED if the evidence supports this particular engagement's involvement. Otherwise NOT_LINKED."
    )
    linked_strength: Literal["WEAK", "MODERATE", "STRONG"] | None = Field(
        description="For LINKED: WEAK for indirect distinguishing support, MODERATE for a supported link with a gap, STRONG for specific consistent support. Null for NOT_LINKED."
    )
    linked_strength_reason: str | None = Field(
        description="For LINKED, one sentence explaining the link strength using the recorded evidence. Null for NOT_LINKED."
    )
    llm_confidence: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description="Confidence in this pair's decision: LOW for substantial doubt, MEDIUM for meaningful doubt, HIGH for little remaining doubt."
    )


class LinkingDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    assessments: list[EngagementAssessment] = Field(
        description="One independent assessment for every supplied candidate_number, including unlinked candidates."
    )
    incident_evidence_strength: Literal["UNSUPPORTED", "WEAK", "MODERATE", "STRONG"] = Field(
        description="How useful the incident alone is for identifying the relevant engagement(s): UNSUPPORTED for no service clues, WEAK for broad clues, MODERATE for relevant details with a material gap, STRONG for specific identifying details."
    )
