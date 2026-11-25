import csv

from .fields import ENGAGEMENT_FIELDS, INCIDENT_FIELDS
from .save_results import OUTPUT_COLUMNS


# Incident work notes can exceed the CSV parser's default field size.
csv.field_size_limit(max(csv.field_size_limit(), 2**31 - 1))


def read_candidates(candidates_file):
    with open(candidates_file, encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        headers = next(reader, [])
        rows = list(reader)
    return headers, rows


def read_cases(rows, headers, finding_status_column="finding_status"):
    if not headers or not all(headers) or len(headers) != len(set(headers)):
        raise ValueError("The candidate file contains blank or duplicate headers.")
    if any(name in headers for name in OUTPUT_COLUMNS):
        raise ValueError("The candidate file already contains a linking output column.")
    engagement_columns = {}
    for field in ENGAGEMENT_FIELDS:
        prefixed = "ENG." + field
        engagement_columns[field] = prefixed if prefixed in headers else field

    if "incident_id" not in headers or engagement_columns["ENGAGEMENT_ID"] not in headers:
        raise ValueError("The candidate file requires incident_id and ENGAGEMENT_ID.")

    cases = {}
    for row_number, values in enumerate(rows, start=2):
        if values and len(values) != len(headers):
            raise ValueError(f"Candidate CSV row {row_number} has the wrong number of fields.")
        if all(value is None or value == "" for value in values):
            continue
        row = dict(zip(headers, values))
        engagement_id = row[engagement_columns["ENGAGEMENT_ID"]]
        missing_engagement_id = engagement_id is None or not str(engagement_id).strip()
        status = row.get(finding_status_column, "MATCHED")
        if status in ("NO_MATCH", "INVALID_NAME"):
            if not missing_engagement_id:
                raise ValueError(f"{status} row {row_number} contains an ENGAGEMENT_ID.")
            continue
        if status != "MATCHED":
            raise ValueError(f"Unknown Finding status {status!r} in candidate row {row_number}.")

        incident_id = row["incident_id"]
        missing_incident_id = incident_id is None or not str(incident_id).strip()
        if missing_incident_id or missing_engagement_id:
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
        _, source_row_numbers = candidates[record_key]
        source_row_numbers.append(row_number)
    return cases
