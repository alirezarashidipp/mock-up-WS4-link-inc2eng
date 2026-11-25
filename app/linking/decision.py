import json

from .fields import INCIDENT_FIELDS, ENGAGEMENT_FIELDS
from .schema import LinkingDecision
from .validate_response import assessments_by_number


MAX_ENGAGEMENTS_PER_REQUEST = 80


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
    incident_fields = build_incident_fields(incident, definitions["incident"])
    assessments = {}
    incident_strength = None
    batch_prompt = prompt
    for start in range(0, len(engagements), MAX_ENGAGEMENTS_PER_REQUEST):
        batch = engagements[start:start + MAX_ENGAGEMENTS_PER_REQUEST]
        payload = {
            "incident": incident_fields,
            "field_definitions": {"engagement": definitions["engagement"]},
            "engagements": build_engagement_table(batch),
        }
        decision = _request_batch(client, model, payload, batch_prompt, temperature)
        if incident_strength is None:
            incident_strength = decision.incident_evidence_citation_strength
            batch_prompt = (
                f"{prompt}\nThe incident evidence strength was already rated {incident_strength}. "
                "Use and return that same incident rating for this batch."
            )
        batch_assessments = assessments_by_number(decision, len(batch), incident_strength)
        for local_number, assessment in batch_assessments.items():
            number = start + local_number
            assessment["candidate_number"] = number
            assessments[number] = assessment
    return assessments


def _request_batch(client, model, payload, prompt, temperature):
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
    return message.parsed
