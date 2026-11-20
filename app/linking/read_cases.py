from .fields import ENGAGEMENT_FIELDS, INCIDENT_FIELDS


def read_cases(rows, headers):
    engagement_columns = {}
    for field in ENGAGEMENT_FIELDS:
        prefixed = "ENG." + field
        engagement_columns[field] = prefixed if prefixed in headers else field

    if "incident_id" not in headers or engagement_columns["ENGAGEMENT_ID"] not in headers:
        raise ValueError("The candidate file requires incident_id and ENGAGEMENT_ID.")

    cases = {}
    for row_number, values in enumerate(rows, start=2):
        if all(value is None or value == "" for value in values):
            continue
        row = dict(zip(headers, values))
        incident_id = row["incident_id"]
        engagement_id = row[engagement_columns["ENGAGEMENT_ID"]]
        if incident_id is None or not str(incident_id).strip() or engagement_id is None or not str(engagement_id).strip():
            raise ValueError(f"Missing incident_id or ENGAGEMENT_ID in candidate row {row_number}.")

        incident = {field: row.get(field) for field in INCIDENT_FIELDS}
        if incident_id not in cases:
            cases[incident_id] = (incident, {})
        stored_incident, candidates = cases[incident_id]
        if stored_incident != incident:
            raise ValueError(f"Incident fields differ between candidate rows for {incident_id}.")

        engagement = {field: row.get(column) for field, column in engagement_columns.items()}
        record_key = tuple(engagement.values())
        if record_key not in candidates:
            candidates[record_key] = (engagement, [])
        candidates[record_key][1].append(row_number)
    return cases
