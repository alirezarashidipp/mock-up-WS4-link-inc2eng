from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EngagementAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    candidate_number: int = Field(ge=1, description="Number assigned to this engagement in the request.")
    incident_evidence_citation: list[str] = Field(
        description="Zero or more incident excerpts supporting or challenging this link, each as 'column_name: verbatim excerpt'."
    )
    engagement_evidence_citation: list[str] = Field(
        description="Zero or more excerpts from this candidate's source record, each as 'column_name: verbatim excerpt'."
    )
    engagement_evidence__citation_strength: Literal["UNSUPPORTED", "WEAK", "MODERATE", "STRONG"] = Field(
        description="How clearly this engagement record describes its service and scope. UNSUPPORTED for no usable scope, WEAK for generic scope, MODERATE for identifiable service with material scope gaps, STRONG for specific service and scope."
    )
    link_rationale: str = Field(
        description="Explain the connection between the affected service and this engagement's scope, including material gaps or conflicts."
    )
    link_decision: Literal["LINKED", "POSSIBLY_LINKED", "NOT_LINKED"] = Field(
        description="LINKED if the evidence supports this particular engagement's involvement. POSSIBLY_LINKED for a concrete service fit with unresolved involvement. NOT_LINKED for incompatible scope or no service-specific support."
    )
    link_decision_confidence_reason: str = Field(
        min_length=1,
        description="One sentence identifying the evidence, conflict or gap that warrants the confidence level for this decision."
    )
    link_decision_confidence: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description="Confidence in this pair's decision: LOW for substantial doubt, MEDIUM for meaningful doubt, HIGH for little remaining doubt."
    )


class LinkingDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    assessments: list[EngagementAssessment] = Field(
        description="One independent assessment for every supplied candidate_number, including unlinked candidates."
    )
    incident_evidence__citation_strength: Literal["UNSUPPORTED", "WEAK", "MODERATE", "STRONG"] = Field(
        description="How useful the incident alone is for identifying the relevant engagement(s): UNSUPPORTED for no service clues, WEAK for broad clues, MODERATE for relevant details with a material gap, STRONG for specific identifying details."
    )
