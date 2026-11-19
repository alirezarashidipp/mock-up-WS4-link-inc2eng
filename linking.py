from pathlib import Path

import yaml

from app.linking.decision import request_decision
from app.linking.read_cases import read_cases
from app.linking.save_results import save_results
from app.linking.llm_connection import llm_connection


ROOT = Path(__file__).resolve().parent
PROMPT_FILE = ROOT / "app/linking/prompt.yml"
INCIDENTS = ROOT / "data/input/CLASSIFIED_INCIDENTS.csv"
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
    for source in ("incident", "engagement"):
        path = ROOT / "config" / f"{source}_columns.yml"
        with path.open(encoding="utf-8-sig") as stream:
            definitions[source] = yaml.safe_load(stream)["definitions"]
    return definitions


def no_candidates(incident):
    return {
        "incident_id": incident["incident_id"],
        "link_decision": "NO_CANDIDATES",
        "selected_engagement_id": None,
        "confidence": None,
        "decision_reason": "The finder returned no engagement candidates for this incident.",
        "candidates": [],
    }


def link_incidents(cases, definitions, prompt):
    if not any(engagements for _, engagements in cases):
        return [no_candidates(incident) for incident, _ in cases]

    results = []
    with llm_connection() as (client, model):
        for incident, engagements in cases:
            if not engagements:
                results.append(no_candidates(incident))
                continue
            decision = request_decision(client, model, incident, engagements, definitions, prompt)
            decision["incident_id"] = incident["incident_id"]
            results.append(decision)
    return results


def main(incident_file=INCIDENTS, candidates_file=CANDIDATES, output_file=OUTPUT):
    cases = read_cases(incident_file, candidates_file)
    definitions = read_definitions()
    prompt = read_prompt(PROMPT_FILE)
    results = link_incidents(cases, definitions, prompt)
    save_results(output_file, results)
    print(f"Saved {len(results)} incident decisions to {output_file}.")


if __name__ == "__main__":
    main()
