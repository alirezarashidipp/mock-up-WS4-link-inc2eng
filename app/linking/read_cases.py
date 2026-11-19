from app.finding.clean_incidents import clean_incidents
from app.finding.read_files import read_table
from app.finding.select_incidents import select_incidents
from .fields import ENGAGEMENT_FIELDS


def read_eligible_incidents(path):
    required = ["incident_id", "class", "classified_supplier_name"]
    headers, rows = read_table(path, required)
    selected = select_incidents(rows)
    eligible = clean_incidents(selected)

    incidents = {}
    for row, _ in eligible:
        incident_id = row["incident_id"]
        if not incident_id.strip() or incident_id in incidents:
            raise ValueError(f"{path.name} requires a unique, nonblank incident_id for each eligible incident.")
        incidents[incident_id] = row
    return headers, incidents


def read_cases(incident_file, candidates_file):
    incident_headers, incidents = read_eligible_incidents(incident_file)
    id_column = "ENG.ENGAGEMENT_ID" if "ENGAGEMENT_ID" in incident_headers else "ENGAGEMENT_ID"
    _, rows = read_table(candidates_file, ["incident_id", id_column])
    by_incident = {incident_id: [] for incident_id in incidents}

    for row in rows:
        incident_id = row["incident_id"]
        if incident_id not in incidents:
            raise ValueError(f"Candidate incident {incident_id!r} is missing or ineligible. Run finding.py again.")
        supplier = incidents[incident_id]["classified_supplier_name"]
        if "classified_supplier_name" in row and row["classified_supplier_name"] != supplier:
            raise ValueError(f"The supplier changed for {incident_id}. Run finding.py again.")
        engagement_id = row[id_column]
        if engagement_id is None or not str(engagement_id).strip():
            raise ValueError(f"The candidate workbook contains a blank ENGAGEMENT_ID for {incident_id}.")

        engagement = {}
        for field in ENGAGEMENT_FIELDS:
            column = "ENG." + field if field in incident_headers else field
            engagement[field] = row.get(column)
        engagement["ENGAGEMENT_ID"] = str(engagement_id)

        candidates = by_incident[incident_id]
        if engagement not in candidates:
            candidates.append(engagement)

    return [(incident, by_incident[incident_id]) for incident_id, incident in incidents.items()]
