from pathlib import Path

import yaml

from app.finding.clean_incidents import clean_incidents
from app.finding.clean_suppliers import clean_suppliers
from app.finding.deduplicate_candidates import deduplicate_candidates
from app.finding.match_rows import find_matches
from app.finding.read_incidents import read_incidents
from app.finding.read_suppliers import read_suppliers
from app.finding.replace_names import read_replacements, replace_incident_names
from app.finding.save_csv import save_candidates, save_invalid_names
from app.finding.select_incidents import select_incidents


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "data/input"
OUTPUT = ROOT / "data/output/engagement_candidates.csv"
ALIASES = ROOT / "config/supplier_aliases.yml"
COLUMNS = ROOT / "config/finding_columns.yml"


def read_columns(path):
    with Path(path).open(encoding="utf-8-sig") as stream:
        columns = yaml.safe_load(stream)
    required = {
        "incident": ("identifier", "classification", "supplier"),
        "engagement": ("identifier",),
        "candidate": ("search_name", "source_field", "method", "source_value"),
        "invalid_name_report": ("status",),
    }
    for section, roles in required.items():
        fields = columns.get(section) if isinstance(columns, dict) else None
        if not isinstance(fields, dict):
            raise ValueError(f"Missing column mapping for {section}.")
        for role in roles:
            header = fields.get(role)
            if not isinstance(header, str) or not header.strip():
                raise ValueError(f"Provide a CSV header for {section}.{role}.")
        if len({fields[role] for role in roles}) != len(roles):
            raise ValueError(f"Duplicate CSV headers in {section}.")
    search_columns = columns["engagement"].get("search_columns_eng")
    if not isinstance(search_columns, list) or not search_columns:
        raise ValueError("Provide a nonempty list for engagement.search_columns_eng.")
    if any(not isinstance(name, str) or not name.strip() for name in search_columns):
        raise ValueError("Each entry in search_columns_eng must be a nonblank CSV header.")
    if len(search_columns) != len(set(search_columns)):
        raise ValueError("Duplicate CSV headers in search_columns_eng.")

    incident = columns["incident"]
    if columns["invalid_name_report"]["status"] in (incident["identifier"], incident["supplier"]):
        raise ValueError("Invalid-name report headers must be distinct.")
    return columns


def main(input_dir=INPUT, output_file=OUTPUT, columns_file=COLUMNS):
    output_file = Path(output_file)
    if output_file.suffix.lower() != ".csv":
        raise ValueError("Choose a CSV candidate output.")

    columns = read_columns(columns_file)
    incident_fields = columns["incident"]
    engagement_fields = columns["engagement"]
    replacements = read_replacements(ALIASES)

    incident_headers, incidents = read_incidents(input_dir, incident_fields)
    incidents = select_incidents(incidents, incident_fields["classification"])
    incidents = clean_incidents(incidents, incident_fields["supplier"])
    incidents = replace_incident_names(incidents, replacements)

    supplier_headers, suppliers = read_suppliers(input_dir, engagement_fields)
    suppliers = clean_suppliers(suppliers, engagement_fields["search_columns_eng"])

    matches = find_matches(incidents, suppliers, incident_fields["identifier"], engagement_fields["identifier"])
    candidates = deduplicate_candidates(matches)
    save_candidates(output_file, incident_headers, supplier_headers, candidates, columns["candidate"])

    invalid_incidents = [row for row, name in incidents if not name]
    invalid_file = output_file.with_name(f"{output_file.stem}_invalid_names.csv")
    save_invalid_names(invalid_file, invalid_incidents, incident_fields, columns["invalid_name_report"]["status"])
    print(f"Selected {len(incidents)} supplier incidents. Saved {len(candidates)} candidate rows to {output_file}.")
    print(f"Invalid supplier names: {len(invalid_incidents)}. Report: {invalid_file}.")


if __name__ == "__main__":
    main()
