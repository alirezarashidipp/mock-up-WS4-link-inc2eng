from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


LinkDecision = Literal["LINKED", "POSSIBLY_LINKED", "NOT_LINKED", "INSUFFICIENT_EVIDENCE"]


class EngagementAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    candidate_number: int = Field(ge=1, description="Number assigned to this engagement in the request.")
    incident_evidence_citation: list[str] = Field(
        description="Zero or more incident excerpts supporting or challenging this link, each as 'column_name: verbatim excerpt'."
    )
    engagement_evidence_citation: list[str] = Field(
        description="Zero or more excerpts from this candidate's source record, each as 'column_name: verbatim excerpt'."
    )
    engagement_evidence_citation_strength: Literal["UNSUPPORTED", "WEAK", "MODERATE", "STRONG"] = Field(
        description=(
            "Rate this engagement's own scope. UNSUPPORTED means no usable service clue. "
            "WEAK gives only a broad category, e.g. IT support. MODERATE identifies the service but a gap or "
            "conflict changes what it could cover, e.g. WAN support for selected branches without saying which. "
            "STRONG establishes the covered service and scope without material conflict, e.g. WAN support for all UK branches. Missing irrelevant "
            "details do not lower the rating. An unrelated engagement can have STRONG evidence."
        )
    )
    link_decision: LinkDecision = Field(
        description=(
            "Assess this candidate independently. "
            "Use LINKED when evidence from both records connects its documented scope "
            "to the supplier service implicated in the failure. "
            "Use NOT_LINKED when the evidence rules this candidate out. "
            "Use POSSIBLY_LINKED for a concrete service fit with a specific material gap or conflict. "
            "Use INSUFFICIENT_EVIDENCE when the records establish neither a concrete fit nor an exclusion."
        )
    )
    link_rationale: str = Field(
        min_length=1,
        description="In one or two English sentences, explain the decisive evidence, exclusion or material gap for this candidate's decision."
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

    incident_evidence_citation_strength: Literal["UNSUPPORTED", "WEAK", "MODERATE", "STRONG"] = Field(
        description=(
            "Using the incident record alone, rate how clearly it identifies the supplier service, "
            "component or activity implicated in the failure. "
            "Use UNSUPPORTED when there is no usable service clue. "
            "Use WEAK for a broad symptom or downstream impact. "
            "Use MODERATE when a specific supplier service is implicated but a material detail "
            "is missing or disputed. "
            "Use STRONG when the record clearly establishes the implicated service and its material scope."
        )
    )
    assessments: list[EngagementAssessment] = Field(
        description=(
            "Return exactly one assessment for every supplied candidate_number, including excluded "
            "and uncertain candidates. A complete response may contain zero LINKED assessments."
        )
    )
