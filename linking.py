from pathlib import Path

from filelock import FileLock

from app.linking.decision import request_decision
from app.linking.llm_connection import llm_connection
from app.linking.read_cases import read_candidates, read_cases
from app.linking.read_instructions import read_definitions, read_prompt
from app.linking.read_progress import pending_incidents, read_progress
from app.linking.save_results import OUTPUT_COLUMNS, apply_assessments, save_progress


ROOT = Path(__file__).resolve().parent
PROMPT_FILE = ROOT / "app/linking/prompt.yml"
CANDIDATES = ROOT / "data/output/engagement_candidates.csv"
OUTPUT = ROOT / "data/output/engagement_links.csv"


def link_incidents(cases, rows, headers, output_file):
    if not cases:
        return

    definitions = read_definitions()
    prompt = read_prompt(PROMPT_FILE)
    source_width = len(headers)
    output_headers = [*headers, *OUTPUT_COLUMNS]
    with llm_connection() as (llm_client, model, temperature):
        for incident, candidates in cases:
            candidate_records = list(candidates.values())
            engagements = [engagement for engagement, _ in candidate_records]
            assessments = request_decision(
                llm_client, model, incident, engagements, definitions, prompt, temperature
            )
            apply_assessments(rows, candidate_records, assessments, source_width)
            save_progress(output_file, output_headers, rows)
            print(f"Saved incident {incident['incident_id']} to {output_file}.", flush=True)


def main(candidates_file=CANDIDATES, output_file=OUTPUT, finding_status_column="finding_status"):
    candidates_file = Path(candidates_file)
    output_file = Path(output_file)
    if output_file.suffix.lower() != ".csv" or output_file.resolve() == candidates_file.resolve():
        raise ValueError("Choose a CSV output different from the candidate file.")
    if candidates_file.suffix.lower() != ".csv":
        raise ValueError("Choose a CSV candidate input.")

    headers, source_rows = read_candidates(candidates_file)
    cases = read_cases(source_rows, headers, finding_status_column)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(output_file) + ".lock", timeout=0):
        rows, needs_snapshot = read_progress(output_file, headers, source_rows, OUTPUT_COLUMNS)
        remaining = pending_incidents(cases, rows, len(headers), OUTPUT_COLUMNS)
        if needs_snapshot:
            save_progress(output_file, [*headers, *OUTPUT_COLUMNS], rows)
        link_incidents(remaining, rows, headers, output_file)
    print(f"Complete: {len(cases)} incidents in {output_file}.")


if __name__ == "__main__":
    main()
