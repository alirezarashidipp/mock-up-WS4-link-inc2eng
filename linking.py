from pathlib import Path

import yaml
from openpyxl import load_workbook

from app.linking.decision import request_decision
from app.linking.fields import ENGAGEMENT_FIELDS, INCIDENT_FIELDS
from app.linking.read_cases import read_cases
from app.linking.save_results import append_headers, save_results, write_assessment
from app.linking.llm_connection import llm_connection


ROOT = Path(__file__).resolve().parent
PROMPT_FILE = ROOT / "app/linking/prompt.yml"
CANDIDATES = ROOT / "data/output/engagement_candidates.xlsx"
OUTPUT = ROOT / "data/output/engagement_links.xlsx"


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


def link_incidents(sheet, cases, first_column, definitions, prompt):
    if not cases:
        return

    with llm_connection() as (client, model, temperature):
        for incident, candidates in cases.values():
            records = list(candidates.values())
            engagements = [engagement for engagement, _ in records]
            assessments = request_decision(client, model, incident, engagements, definitions, prompt, temperature)
            for number, (_, rows) in enumerate(records, start=1):
                write_assessment(sheet, rows, first_column, assessments[number])


def main(candidates_file=CANDIDATES, output_file=OUTPUT):
    if Path(candidates_file).resolve() == Path(output_file).resolve():
        raise ValueError("Choose an output file different from the candidate workbook.")
    workbook = load_workbook(candidates_file)
    try:
        sheet = workbook.active
        for other in list(workbook.worksheets):
            if other is not sheet:
                workbook.remove(other)
        sheet.title = "Linking decisions"
        headers = [cell.value for cell in sheet[1]]
        if not all(headers) or len(headers) != len(set(headers)):
            raise ValueError("The candidate sheet contains blank or duplicate headers.")
        cases = read_cases(sheet, headers)
        first_column = append_headers(sheet, headers)
        definitions = read_definitions()
        prompt = read_prompt(PROMPT_FILE)
        link_incidents(sheet, cases, first_column, definitions, prompt)
        save_results(workbook, output_file)
    finally:
        workbook.close()
    print(f"Saved engagement decisions for {len(cases)} incidents to {output_file}.")


if __name__ == "__main__":
    main()
