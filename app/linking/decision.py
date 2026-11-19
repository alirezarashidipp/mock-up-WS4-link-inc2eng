import json

from .fields import INCIDENT_FIELDS, ENGAGEMENT_FIELDS
from .schema import LinkingDecision


def source_values(row, fields):
    values = {}
    for field in fields:
        value = row.get(field)
        if isinstance(value, str) and not value.strip():
            value = None
        values[field] = value
    return values


def number_engagements(engagements):
    numbered = []
    for candidate_number, engagement in enumerate(engagements, start=1):
        values = source_values(engagement, ENGAGEMENT_FIELDS)
        values["candidate_number"] = candidate_number
        numbered.append(values)
    return numbered


def assessments_by_number(decision, candidate_count):
    assessments = {}
    for candidate in decision.assessments:
        number = candidate.candidate_number
        if not 1 <= number <= candidate_count or number in assessments:
            raise ValueError(f"Unknown or repeated candidate_number {number}.")
        assessment = candidate.model_dump()
        assessment["incident_evidence_strength"] = decision.incident_evidence_strength
        if candidate.link_decision == "LINKED":
            if not candidate.linked_strength or not (candidate.linked_strength_reason or "").strip():
                raise ValueError(f"Missing link strength or reason for candidate {number}.")
        else:
            assessment["linked_strength"] = None
            assessment["linked_strength_reason"] = None
        assessments[number] = assessment
    if len(assessments) != candidate_count:
        raise ValueError("The model omitted a candidate assessment.")
    return assessments


def request_decision(client, model, incident, engagements, definitions, prompt, temperature):
    incident = source_values(incident, INCIDENT_FIELDS)
    numbered_engagements = number_engagements(engagements)
    payload = {
        "field_definitions": definitions,
        "incident": incident,
        "engagements": numbered_engagements,
    }
    response = client.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False, default=str)},
        ],
        response_format=LinkingDecision,
        temperature=temperature,
        store=False,
    )
    if not response.choices:
        raise ValueError("The model returned no linking decision.")
    message = response.choices[0].message
    if message.refusal or message.parsed is None:
        raise ValueError("The model returned no structured linking decision.")
    return assessments_by_number(message.parsed, len(engagements))
