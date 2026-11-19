# Incident-to-engagement linking

Run these commands from the project root. Both workbooks are written to `data/output/`.

| Command | Output | One row per |
| --- | --- | --- |
| `python finding.py` | `engagement_candidates.xlsx` | Incident and matching engagement record |
| `python linking.py` | `engagement_links.xlsx` | Eligible incident, including those with zero candidates |

## Finding candidates

Place `CLASSIFIED_INCIDENTS.csv` and one `ENG_ALL.csv` or `ENG_ALL.xlsx` in `data/input/`. The finder selects rows with `class = SUPPLIER` and a usable `classified_supplier_name`. It cleans incident names and applies [supplier aliases](../config/supplier_aliases.yml). Engagement names receive only lowercase and whitespace removal.

| Match | First engagement field | Second engagement field |
| --- | --- | --- |
| `EXACT` | `THIRD_PARTY_NAME` | `THIRD_PARTY_NORMALISED_NAME` |
| `PARTIAL` (substring, then fuzzy) | `THIRD_PARTY_NORMALISED_NAME` | `THIRD_PARTY_NAME` |

Fuzzy matching requires at least five incident-name characters and a similarity of 0.72 or higher. The workbook includes `ENGAGEMENT_ID`, the original source fields, the matching column and its original value in `found_name_in_source`. [12 worked examples](scenarios/matching.html)

## Selecting an engagement

Linking requires a unique, nonblank `incident_id` and the candidate workbook from the same inputs. Eligibility and checks for a stale candidate workbook run locally. For each eligible incident with candidates, the LLM receives the 74 raw incident fields and 22 source fields per engagement listed in [fields.py](../app/linking/fields.py), together with their YAML definitions. Classification outputs and finder metadata stay outside the request. Missing or blank values appear as JSON `null`; zero values retain their source meaning.

The model compares all candidates in one request and ranks up to three distinct engagement IDs. Each rationale cites fields and excerpts from both sources.

Only `LINKED` fills `selected_engagement_id`. Other model decisions are `AMBIGUOUS`, `INSUFFICIENT_EVIDENCE` and `NO_SUITABLE_CANDIDATE`. Each model decision includes a confidence tag (`LOW`, `MEDIUM` or `HIGH`) and a reason. An incident with no candidates gets `NO_CANDIDATES` locally and a blank confidence.

The [connection module](../app/linking/llm_connection.py) reads OpenAI or Azure settings from the project-root `.env`. The [YAML prompt](../app/linking/prompt.yml) defines the decision instructions, the [Pydantic schema](../app/linking/schema.py) defines the response, and [validation](../app/linking/validation.py) checks IDs and quoted evidence before export.
