from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RankedCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    engagement_id: str
    rationale: str
    incident_field: str
    incident_quote: str
    engagement_field: str
    engagement_quote: str


class LinkingDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    candidates: list[RankedCandidate] = Field(max_length=3)
    link_decision: Literal["LINKED", "AMBIGUOUS", "INSUFFICIENT_EVIDENCE", "NO_SUITABLE_CANDIDATE"]
    selected_engagement_id: str | None
    confidence: Literal["LOW", "MEDIUM", "HIGH"]
    decision_reason: str
