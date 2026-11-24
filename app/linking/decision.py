import json

from .fields import INCIDENT_FIELDS, ENGAGEMENT_FIELDS
from .schema import LinkingDecision
from .validate_response import assessments_by_number


def source_value(record, field):
    value = record.get(field)
    if isinstance(value, str) and not value.strip():
        return None
    return value


def build_incident_fields(incident, definitions):
    fields = []
    for name in INCIDENT_FIELDS:
        fields.append({
            "column_name": name,
            "definition": definitions[name],
            "value": source_value(incident, name),
        })
    return fields


def build_engagement_table(engagements):
    columns = ["candidate_number", *ENGAGEMENT_FIELDS]
    rows = []
    for candidate_number, engagement in enumerate(engagements, start=1):
        values = [source_value(engagement, field) for field in ENGAGEMENT_FIELDS]
        rows.append([candidate_number, *values])
    return {"columns": columns, "rows": rows}


def request_decision(client, model, incident, engagements, definitions, prompt, temperature):
    payload = {
        "incident": build_incident_fields(incident, definitions["incident"]),
        "field_definitions": {"engagement": definitions["engagement"]},
        "engagements": build_engagement_table(engagements),
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
