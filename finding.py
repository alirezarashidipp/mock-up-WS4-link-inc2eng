from pathlib import Path

from app.finding.clean_incidents import clean_incidents
from app.finding.clean_suppliers import clean_suppliers
from app.finding.match_rows import find_candidates
from app.finding.read_incidents import read_incidents
from app.finding.read_suppliers import read_suppliers
from app.finding.replace_names import read_replacements, replace_incident_names
from app.finding.save_excel import save_candidates
from app.finding.select_incidents import select_incidents


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "data/input"
OUTPUT = ROOT / "data/output/engagement_candidates.xlsx"
ALIASES = ROOT / "config/supplier_aliases.yml"


def main(input_dir=INPUT, output_file=OUTPUT):
    replacements = read_replacements(ALIASES)

    incident_headers, incidents = read_incidents(input_dir)
    incidents = select_incidents(incidents)
    incidents = clean_incidents(incidents)
    incidents = replace_incident_names(incidents, replacements)

    supplier_headers, suppliers = read_suppliers(input_dir)
    suppliers = clean_suppliers(suppliers)

    candidates = find_candidates(incidents, suppliers)
    save_candidates(output_file, incident_headers, supplier_headers, candidates)
    print(f"Selected {len(incidents)} incidents. Saved {len(candidates)} candidate rows to {output_file}.")


if __name__ == "__main__":
    main()
