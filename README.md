# WS4 incident-to-engagement linking

This demo starts with an HSBC incident already attributed to a named supplier. One supplier can provide several services under different engagement IDs. Finding retrieves candidate engagements by supplier name. Linking checks which of them cover the supplier service or activity implicated in the failure. The relevant engagement may be outside the candidate list.

Both stages run from the project root and write to `data/output/`.

| Stage guide | Command | Output | One row per |
| --- | --- | --- | --- |
| [Finding candidates](app/finding/docs/README.md) | `python finding.py` | `engagement_candidates.csv` | Matching incident–engagement pair, or one row for a selected incident with no candidate |
| [Linking incidents](app/linking/docs/README.md) | `python linking.py` | `engagement_links.csv` | Source row in the candidate file |

## Run the finder

Finding reads its input and output CSV header names from [finding_columns.yml](config/finding_columns.yml). The defaults below produce the candidate format used by Linking.

1. Put `CLASSIFIED_INCIDENTS.csv` in `data/input/`. It must contain the headers `class` and `classified_supplier_name`.
2. In the same folder, supply `ENG_ALL.csv` with the engagement identifier and at least one field from `engagement.search_columns_eng`, such as `THIRD_PARTY_NAME`. Add, remove or reorder headers in this list to choose which fields Finding searches.
3. Use UTF-8, comma-separated CSV files. The incident file has headers in the first row. For `ENG_ALL`, field names can run across the first row (one engagement per row) or down the first column (one engagement per column).

From the project root on Windows, run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe finding.py
```

For subsequent runs, use the last command.

## Read the results

Open `data/output/engagement_candidates.csv`. Finding selects rows whose `class` is exactly `SUPPLIER` and whose supplier name contains text. It skips the whole value `Unknown` regardless of case or surrounding whitespace. It cleans the incident name and every configured engagement search field, removing whole words such as `vendor`, `global` and `bureau`. It then applies whole-name YAML aliases to the incident name only. For example, `Vendor GCP` becomes `google` and matches `Google LLC`. The candidate file retains the original source values.

For a search name of one to four characters after alias replacement and space removal, `SUBSTRING` requires a whole word in the cleaned engagement field. For example, `ICE` matches `ICE Data Services` and skips `Office Supplies`. Queries of five or more characters can also match inside a word or across spaces. If neither `EXACT` nor `SUBSTRING` matches the field, these longer queries qualify for `FUZZY` at 50% Levenshtein similarity or higher against one or more adjacent words. [Matching rules](app/finding/docs/README.md#matching-rules-and-priority)

Finding writes one CSV. Filter its `finding_status` column to see the outcome for each selected incident.

| `finding_status` | Rows in `engagement_candidates.csv` |
| --- | --- |
| `MATCHED` | One row per matching engagement ID, with original values from both sources. |
| `NO_MATCH` | One row for an incident with a usable search name and zero matching engagements. The original incident and its search name are retained. |
| `INVALID_NAME` | One row when the selected incident has an empty search name after cleaning and alias replacement. The original incident is retained. |

For both incident-only statuses, the engagement fields and match details are empty except for the search name when available. On a matched row, Finding keeps the strongest method in the order `EXACT`, `SUBSTRING`, `FUZZY`. The first source record wins a tie. [Candidate deduplication rules](app/finding/docs/README.md#candidate-deduplication)

- `standardised_supplier_name` holds the incident name used in the comparison.
- `matched_supplier_column` identifies the field that produced the retained match. When fields in the same row tie on method, the first in YAML order wins.
- `match_type` records `EXACT`, `SUBSTRING` or `FUZZY`.
- `found_name_in_source` contains the full original ENG_ALL value from the matched column.

## Link incidents to engagements

1. Place the Finding output at `data/output/engagement_candidates.csv`. Linking groups `MATCHED` rows by `incident_id` for assessment. It copies `NO_MATCH` and `INVALID_NAME` rows to its output in source order with eight empty assessment fields.
2. Configure the existing OpenAI or Azure OpenAI connection in the project-root `.env`. See [.env.example](.env.example) for the provider settings and `LLM_TEMPERATURE`. Use a model or deployment that supports structured outputs and the configured temperature.
3. Run `.\.venv\Scripts\python.exe linking.py` from the project root.

Linking sends up to 80 distinct engagements from one incident per request. For 100 candidates it sends the first 80, then the remaining 20, repeating the incident in each request. Both OpenAI and Azure OpenAI use a 180-second SDK request timeout.

For example, an Amazon name match may return ten engagements across hosting, connectivity and backup. Linking sends one request with the incident first, then the engagement field definitions, then all ten candidate records. Each of the 76 incident fields carries its column name, definition and value, including the classified supplier name and the search name after aliases. The request lists `candidate_number` and the 27 engagement fields once in `engagements.columns`. Each array in `engagements.rows` holds one candidate's values in that order. A clear supplier identity conflict yields `NOT_LINKED` even when services match. [LLM input columns](app/linking/docs/input-fields.md)

For each candidate, Linking gathers evidence about the supplier service implicated in the failure and the engagement's scope, rates the quality of each source, and records a decision and its rationale. `LINKED` requires defensible evidence from both records. `POSSIBLY_LINKED` requires a concrete service fit and a specific gap or conflict that prevents confirmation. `NOT_LINKED` requires evidence that excludes the candidate. `INSUFFICIENT_EVIDENCE` applies when the available information cannot establish or exclude a service fit, including when only the supplier name matches.

The prompt prioritises recorded findings, accounts for material conflicts and treats repeated claims as one account. The rationale identifies the decisive fact, conflict or missing detail. Incident evidence strength reflects how clearly the incident record identifies the supplier service implicated in the failure. A downstream impact alone is `WEAK`. Decision confidence is assessed separately.

Open `data/output/engagement_links.csv`. The CSV contains the original candidate rows and columns in source order, followed by eight assessment columns. The CSV is saved after each incident. Rerun with the same input to continue from the first pending incident. [Output columns and recovery](app/linking/docs/README.md)
