from pathlib import Path

import yaml
from filelock import FileLock
from openpyxl import load_workbook

from app.linking.decision import request_decision
from app.linking.fields import ENGAGEMENT_FIELDS, INCIDENT_FIELDS
from app.linking.read_cases import read_cases
from app.linking.save_results import OUTPUT_COLUMNS, assessment_values, load_progress, save_progress, unfinished_cases
from app.linking.llm_connection import llm_connection


ROOT = Path(__file__).resolve().parent
PROMPT_FILE = ROOT / "app/linking/prompt.yml"
CANDIDATES = ROOT / "data/output/engagement_candidates.xlsx"
OUTPUT = ROOT / "data/output/engagement_links.csv"


def read_prompt(path):
    with path.open(encoding="utf-8-sig") as stream:
        settings = yaml.safe_load(stream)
    prompt = settings.get("system_prompt") if isinstance(settings, dict) else None
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError(f"{path.name} requires a nonblank system_prompt.")
    return prompt


def read_definitions():
    definitions = {}
    for source, fields in (("incident", INCIDENT_FIELDS), ("engagement", ENGAGEMENT_FIELDS)):
        path = ROOT / "config" / f"{source}_columns.yml"
        with path.open(encoding="utf-8-sig") as stream:
            source_definitions = yaml.safe_load(stream)["definitions"]
        definitions[source] = {field: source_definitions[field] for field in fields}
    return definitions


def link_incidents(cases, rows, headers, output_file):
    if not cases:
        return

    definitions = read_definitions()
    prompt = read_prompt(PROMPT_FILE)
    source_width = len(headers)
    output_headers = [*headers, *OUTPUT_COLUMNS]
    with llm_connection() as (client, model, temperature):
        for incident, candidates in cases:
            records = list(candidates.values())
            engagements = [engagement for engagement, _ in records]
            assessments = request_decision(client, model, incident, engagements, definitions, prompt, temperature)
            for number, (_, row_numbers) in enumerate(records, start=1):
                values = assessment_values(assessments[number])
                for row_number in row_numbers:
                    rows[row_number - 2][source_width:] = values
            save_progress(output_file, output_headers, rows)
            print(f"Saved incident {incident['incident_id']} to {output_file}.", flush=True)


def read_candidates(candidates_file):
    workbook = load_workbook(candidates_file)
    try:
        sheet = workbook.active
        headers = [str(cell.value) if cell.value is not None else "" for cell in sheet[1]]
        if not all(headers) or len(headers) != len(set(headers)):
            raise ValueError("The candidate sheet contains blank or duplicate headers.")
        if any(name in headers for name in OUTPUT_COLUMNS):
            raise ValueError("The candidate sheet already contains a linking output column.")
        cases = read_cases(sheet, headers)
        source_rows = []
        for values in sheet.iter_rows(min_row=2, values_only=True):
            source_rows.append(["" if value is None else str(value) for value in values])
        return headers, source_rows, cases
    finally:
        workbook.close()


def main(candidates_file=CANDIDATES, output_file=OUTPUT):
    output_file = Path(output_file)
    if output_file.suffix.lower() != ".csv" or output_file.resolve() == Path(candidates_file).resolve():
        raise ValueError("Choose a CSV output different from the input workbook.")
    headers, source_rows, cases = read_candidates(candidates_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(output_file) + ".lock", timeout=0):
        rows = load_progress(output_file, headers, source_rows)
        remaining = unfinished_cases(cases, rows, len(headers))
        link_incidents(remaining, rows, headers, output_file)
    print(f"Complete: {len(cases)} incidents in {output_file}.")


if __name__ == "__main__":
    main()
