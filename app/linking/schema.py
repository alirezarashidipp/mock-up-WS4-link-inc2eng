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
        description="How clearly this engagement record describes its service and scope. UNSUPPORTED for no usable scope, WEAK for generic or ambiguous scope, MODERATE for identifiable service with a material gap or conflict, STRONG for specific service and scope with no unresolved material conflict. An unrelated engagement can have STRONG source evidence."
    )
    link_rationale: str = Field(
        description="In one or two sentences, explain the evidence connecting the affected service to this engagement's scope and any material gap or conflict. For STRONGEST_LINKED, identify the distinguishing evidence or explain that this is the sole confirmed link."
    )
    link_decision: Literal["STRONGEST_LINKED", "LINKED", "POSSIBLY_LINKED", "NOT_LINKED"] = Field(
        description="STRONGEST_LINKED for the sole confirmed link or the uniquely best-supported confirmed link. LINKED for other confirmed links, including ties for strongest. POSSIBLY_LINKED for a concrete service fit with plausible involvement that a material gap or unresolved conflicting account prevents confirming. NOT_LINKED for incompatible scope or no service-specific support."
    )
    link_decision_confidence_reason: str = Field(
        min_length=1,
        description="One sentence identifying the evidence, conflict or gap that warrants the confidence level for this decision."
    )
    link_decision_confidence: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description="Confidence in the appropriateness of this pair's decision. LOW for substantial doubt, MEDIUM for meaningful doubt, HIGH for little remaining doubt. Any justified label, including POSSIBLY_LINKED or NOT_LINKED, can receive HIGH. These are qualitative judgments."
    )


class LinkingDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    assessments: list[EngagementAssessment] = Field(
        description="One assessment for every supplied candidate_number. At most one distinct candidate may be STRONGEST_LINKED."
    )
    incident_evidence__citation_strength: Literal["UNSUPPORTED", "WEAK", "MODERATE", "STRONG"] = Field(
        description="How useful the incident alone is for identifying relevant engagements. UNSUPPORTED for no usable service clues, WEAK for broad or ambiguous clues, MODERATE for relevant details with a material gap or conflict, STRONG for specific service and scope details with no unresolved material conflict."
    )
