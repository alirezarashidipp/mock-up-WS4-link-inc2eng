from pathlib import Path

from app.finding.clean_rows import clean_aliases, clean_incidents, clean_suppliers
from app.finding.match_rows import find_candidates
from app.finding.read_files import read_aliases, read_incidents, read_suppliers
from app.finding.save_excel import save_candidates


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "data/input"
OUTPUT = ROOT / "data/output/engagement_candidates.xlsx"
ALIASES = ROOT / "config/supplier_aliases.yml"


def main(input_dir=INPUT, output_file=OUTPUT):
    incident_headers, incidents = read_incidents(input_dir)
    supplier_headers, suppliers = read_suppliers(input_dir)
    aliases = read_aliases(ALIASES)

    aliases = clean_aliases(aliases)
    incidents = clean_incidents(incidents, aliases)
    suppliers = clean_suppliers(suppliers, aliases)

    candidates = find_candidates(incidents, suppliers)
    save_candidates(output_file, incident_headers, supplier_headers, candidates)
    print(f"Selected {len(incidents)} incidents. Saved {len(candidates)} candidate rows to {output_file}.")


if __name__ == "__main__":
    main()
