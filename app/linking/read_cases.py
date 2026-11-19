from app.finding.read_files import read_table
from .fields import ENGAGEMENT_FIELDS, INCIDENT_FIELDS


def read_cases(candidates_file):
    headers, rows = read_table(candidates_file, ["incident_id"])

    # Finding prefixes an engagement header with ENG. when both sources use it.
    engagement_columns = {}
    for field in ENGAGEMENT_FIELDS:
        prefixed = "ENG." + field
        engagement_columns[field] = prefixed if prefixed in headers else field
    if engagement_columns["ENGAGEMENT_ID"] not in headers:
        raise ValueError(f"{candidates_file.name} is missing ENGAGEMENT_ID.")

    cases = {}
    for row in rows:
        incident_id = row["incident_id"]
        if incident_id is None or not str(incident_id).strip():
            raise ValueError(f"{candidates_file.name} contains a blank incident_id.")
        incident = {field: row.get(field) for field in INCIDENT_FIELDS}
        if incident_id not in cases:
            cases[incident_id] = (incident, [])
        stored_incident, engagements = cases[incident_id]
        if stored_incident != incident:
            raise ValueError(f"Incident fields differ between candidate rows for {incident_id}.")

        engagement = {}
        for field, column in engagement_columns.items():
            engagement[field] = row.get(column)
        engagement_id = engagement["ENGAGEMENT_ID"]
        if engagement_id is None or not str(engagement_id).strip():
            raise ValueError(f"{candidates_file.name} contains a blank ENGAGEMENT_ID for {incident_id}.")
        engagement["ENGAGEMENT_ID"] = str(engagement_id)
        if engagement not in engagements:
            engagements.append(engagement)

    return list(cases.values())
