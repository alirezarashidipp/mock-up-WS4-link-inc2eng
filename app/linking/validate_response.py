def validate_assessment(candidate, incident_strength, reported_incident_strength=None):
    number = candidate.candidate_number
    if not candidate.link_rationale.strip():
        raise ValueError(f"Missing link_rationale for candidate {number}.")
    if candidate.link_decision != "LINKED":
        return

    if not any(excerpt.strip() for excerpt in candidate.incident_evidence_citation):
        raise ValueError(f"LINKED candidate {number} needs an incident citation.")
    if "UNSUPPORTED" in (incident_strength, reported_incident_strength, candidate.engagement_evidence_citation_strength):
        raise ValueError(f"LINKED candidate {number} has an unsupported evidence source.")


def assessments_by_number(decision, candidate_count, incident_strength=None):
    """Require exactly one assessment for each local candidate number."""
    assessments = {}
    if incident_strength is None:
        incident_strength = decision.incident_evidence_citation_strength
    for candidate in decision.assessments:
        number = candidate.candidate_number
        if not 1 <= number <= candidate_count or number in assessments:
            raise ValueError(f"Unknown or repeated candidate_number {number}.")
        validate_assessment(candidate, incident_strength, decision.incident_evidence_citation_strength)
        assessment = candidate.model_dump()
        assessment["incident_evidence_citation_strength"] = incident_strength
        assessments[number] = assessment

    if len(assessments) != candidate_count:
        raise ValueError("The model omitted a candidate assessment.")
    return assessments
