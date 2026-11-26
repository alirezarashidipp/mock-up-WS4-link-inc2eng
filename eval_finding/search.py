"""Run the project's Finding steps for one supplier, keeping inputs and results in memory."""

from contextlib import nullcontext
from pathlib import Path

import finding
from app.finding.read_files import read_table
from app.finding.save_csv import candidate_headers


class ReferenceCSV:
    """Let Finding's path-based reader use a text stream already opened by the caller."""

    def __init__(self, stream, filename):
        path = Path(filename)
        self.stream = stream
        self.name = path.name
        self.suffix = path.suffix

    def open(self, *, encoding, newline):
        return nullcontext(self.stream)


def search_supplier(raw_name, reference, reference_name="ENG_ALL.csv"):
    if not isinstance(raw_name, str):
        raise ValueError("Enter a supplier name as text.")

    config = finding.read_columns(finding.COLUMNS)
    incident_fields = config["incident"]
    engagement_fields = config["engagement"]
    candidate_fields = config["candidate"]
    incident_id = incident_fields["identifier"]
    supplier_name = incident_fields["supplier"]
    classification = incident_fields["classification"]
    engagement_id = engagement_fields["identifier"]
    search_fields = engagement_fields["search_columns_eng"]

    incident = {incident_id: "EVAL-0001", classification: "SUPPLIER", supplier_name: raw_name}
    incident_headers = list(incident)
    selected = finding.select_incidents([incident], classification, supplier_name)
    incidents = finding.clean_incidents(selected, supplier_name)
    replacements = finding.read_replacements(finding.ALIASES)
    incidents = finding.replace_incident_names(incidents, replacements)

    source = ReferenceCSV(reference, reference_name)
    engagement_headers, engagements = read_table(
        source, [engagement_id], allow_vertical_headers=True, search_columns=search_fields
    )
    headers = candidate_headers(incident_headers, engagement_headers, candidate_fields)
    suppliers = finding.clean_suppliers(engagements, search_fields)
    matches = finding.find_matches(incidents, suppliers, incident_id, engagement_id, engagement_headers)
    rows = finding.deduplicate_candidates(matches)

    # The CSV writer renders padding from a ragged vertical input as empty cells.
    rows = [["" if value is None else value for value in row] for row in rows]
    status = rows[0][-1] if rows else "SKIPPED"
    id_position = len(incident_headers) + engagement_headers.index(engagement_id)
    return {
        "supplier_name": raw_name,
        "search_name": incidents[0][1] if incidents else "",
        "status": status,
        "headers": headers,
        "rows": rows,
        "match_count": len(rows) if status == "MATCHED" else 0,
        "reference": source.name,
        "columns": {**candidate_fields, "id": headers[id_position]},
    }
