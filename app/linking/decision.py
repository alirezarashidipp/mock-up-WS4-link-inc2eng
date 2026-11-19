import json

from .fields import INCIDENT_FIELDS, ENGAGEMENT_FIELDS
from .llm_connection import request_temperature
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


def attach_engagement_ids(decision, engagements):
    for candidate in decision["candidates"]:
        candidate_number = candidate.pop("candidate_number")
        if not 1 <= candidate_number <= len(engagements):
            raise ValueError("The model selected a candidate_number outside the supplied options.")
        source = engagements[candidate_number - 1]
        candidate["engagement_id"] = source["ENGAGEMENT_ID"]

    decision["selected_engagement_id"] = None
    if decision["link_decision"] == "LINKED":
        if not decision["candidates"]:
            raise ValueError("A LINKED decision requires a ranked candidate.")
        if decision["linked_strength"] is None or not (decision["linked_strength_reason"] or "").strip():
            raise ValueError("A LINKED decision requires linked_strength and its reason.")
        first_candidate = decision["candidates"][0]
        decision["selected_engagement_id"] = first_candidate["engagement_id"]
    else:
        decision["linked_strength"] = None
        decision["linked_strength_reason"] = None
    return decision


def request_decision(client, model, incident, engagements, definitions, prompt):
    incident = source_values(incident, INCIDENT_FIELDS)
    numbered_engagements = number_engagements(engagements)
    payload = {
        "field_definitions": {
            "incident": {field: definitions["incident"][field] for field in INCIDENT_FIELDS},
            "engagement": {field: definitions["engagement"][field] for field in ENGAGEMENT_FIELDS},
        },
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
        temperature=request_temperature(),
        store=False,
    )
    if not response.choices:
        raise ValueError("The model returned no linking decision.")
    message = response.choices[0].message
    if message.refusal or message.parsed is None:
        raise ValueError("The model returned no structured linking decision.")
    decision = message.parsed.model_dump()
    return attach_engagement_ids(decision, engagements)
