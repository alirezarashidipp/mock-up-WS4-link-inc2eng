# WS4 incident-to-engagement linking

This demo starts with an HSBC incident already attributed to a named supplier. One supplier can provide several services under different engagement IDs. Finding retrieves the supplier's candidate engagements. Linking compares the affected service in the incident record with the work described by each engagement.

Both stages run from the project root and write to `data/output/`.

| Stage guide | Command | Output | One row per |
| --- | --- | --- | --- |
| [Finding candidates](app/finding/docs/README.md) | `python finding.py` | `engagement_candidates.csv` | Incident and matching engagement ID |
| [Linking incidents](app/linking/docs/README.md) | `python linking.py` | `engagement_links.csv` | Source row in the candidate file |

## Run the finder

Finding reads its input and output CSV header names from [finding_columns.yml](config/finding_columns.yml). The defaults below produce the candidate format used by Linking.

1. Put `CLASSIFIED_INCIDENTS.csv` in `data/input/`. It must contain the headers `class` and `classified_supplier_name`.
2. In the same folder, supply `ENG_ALL.csv` with the engagement identifier and at least one field from `engagement.search_columns_eng`. The default list contains `THIRD_PARTY_NAME`, `THIRD_PARTY_NORMALISED_NAME` and `PRAD_NAME`. Add, remove or reorder headers in this list to choose which fields Finding searches.
3. Use UTF-8, comma-separated CSV files. The incident file has headers in the first row. For `ENG_ALL`, field names can run across the first row (one engagement per row) or down the first column (one engagement per column).

From the project root on Windows, run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe finding.py
```

For subsequent runs, use the last command.

## Read the results

Open `data/output/engagement_candidates.csv`. Finding selects rows whose `class` is exactly `SUPPLIER` and whose supplier name contains text. It skips the whole value `Unknown` regardless of case or surrounding whitespace. It applies the same cleaning rules to the incident name and every configured engagement search field, then applies whole-name YAML aliases to the incident name only. For example, `B.T.` becomes `british telecom`. The candidate file retains the original source values.

For a search name of one to four characters after alias replacement and space removal, `SUBSTRING` requires a whole word in the cleaned engagement field. For example, `ICE` matches `ICE Data Services` and skips `Office Supplies`. Queries of five or more characters can also match inside a word or across spaces. [Matching rules](app/finding/docs/README.md#matching-rules-and-priority)

The candidate CSV contains one row per matching `(incident_id, ENGAGEMENT_ID)` pair. Finding keeps the strongest match in the order `EXACT`, `SUBSTRING`, `FUZZY`. The first source record wins a tie. Each row includes four match details. [Candidate deduplication rules](app/finding/docs/README.md#candidate-deduplication)

- `standardised_supplier_name` holds the incident name used in the comparison.
- `matched_supplier_column` identifies the field that produced the retained match. When fields in the same row tie on method, the first in YAML order wins.
- `match_type` records `EXACT`, `SUBSTRING` or `FUZZY`.
- `found_name_in_source` contains the full original ENG_ALL value from the matched column.

An incident can have several candidate rows or none. Selected incidents whose names become empty during cleaning appear in `data/output/engagement_candidates_invalid_names.csv` with the status `invalid name`. Each run replaces both Finding outputs. [Finding rules and examples](app/finding/docs/README.md)

## Link incidents to engagements

1. Place the Finding output at `data/output/engagement_candidates.csv`. This candidate file supplies both the incident details and engagement records. Linking groups its rows by `incident_id`.
2. Configure the existing OpenAI or Azure OpenAI connection in the project-root `.env`. See [.env.example](.env.example) for the provider settings and `LLM_TEMPERATURE`. Use a model or deployment that supports structured outputs and the configured temperature.
3. Run `.\.venv\Scripts\python.exe linking.py` from the project root.

For example, an Amazon name match may return ten engagements across hosting, connectivity and backup. Linking sends the incident once with all ten records and assesses each pair. Its 76 incident fields include the classified supplier name and the search name after aliases. Each engagement contributes 22 fields. A clear supplier identity conflict yields `NOT_LINKED` even when services match. [LLM input columns](app/linking/docs/input-fields.md)

For each candidate, Linking gathers evidence about the affected service and the engagement's scope, rates the quality of each source, and records a decision and its rationale. `LINKED` requires defensible evidence from both records. `POSSIBLY_LINKED` requires a concrete service fit and a specific gap or conflict that prevents confirmation. `NOT_LINKED` requires evidence that excludes the candidate. `INSUFFICIENT_EVIDENCE` applies when the available information cannot establish or exclude a service fit, including when only the supplier name matches.

The prompt prioritises recorded findings, accounts for material conflicts and treats repeated claims as one account. The rationale identifies the decisive fact, conflict or missing detail. Source strength distinguishes broad clues, an identifiable service with uncertain scope, and a clearly established scope. Decision confidence is assessed separately.

Open `data/output/engagement_links.csv`. The CSV contains the original candidate rows and columns in source order, followed by eight assessment columns. The CSV is saved after each incident. Rerun with the same input to continue from the first pending incident. [Output columns and recovery](app/linking/docs/README.md)
