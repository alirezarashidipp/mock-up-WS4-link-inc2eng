import json

from .fields import INCIDENT_FIELDS, ENGAGEMENT_FIELDS
from .llm_connection import request_temperature
from .schema import LinkingDecision
from .validation import check_decision


def source_values(row, fields):
    values = {}
    for field in fields:
        value = row.get(field)
        if isinstance(value, str) and not value.strip():
            value = None
        values[field] = value
    return values


def request_decision(client, model, incident, engagements, definitions, prompt):
    incident = source_values(incident, INCIDENT_FIELDS)
    engagements = [source_values(row, ENGAGEMENT_FIELDS) for row in engagements]
    payload = {
        "field_definitions": {
            "incident": {field: definitions["incident"][field] for field in INCIDENT_FIELDS},
            "engagement": {field: definitions["engagement"][field] for field in ENGAGEMENT_FIELDS},
        },
        "incident": incident,
        "engagements": engagements,
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
    return check_decision(message.parsed, incident, engagements)
