# WS4 incident-to-engagement linking

This demo starts with an HSBC incident already attributed to a named supplier. One supplier can provide several services under different engagement IDs. Finding retrieves the supplier's candidate engagements. Linking compares the affected service in the incident record with the work described by each engagement.

Both stages run from the project root and write to `data/output/`.

| Stage guide | Command | Output | One row per |
| --- | --- | --- | --- |
| [Finding candidates](app/finding/docs/README.md) | `python finding.py` | `engagement_candidates.xlsx` | Incident and matching engagement record |
| [Linking incidents](app/linking/docs/README.md) | `python linking.py` | `engagement_links.csv` | Source row in the candidate workbook |

## Run the finder

1. Put `CLASSIFIED_INCIDENTS.csv` in `data/input/`. It must contain the headers `class` and `classified_supplier_name`.
2. In the same folder, supply either `ENG_ALL.csv` or `ENG_ALL.xlsx`. The required fields are `ENGAGEMENT_ID`, `THIRD_PARTY_NAME` and `THIRD_PARTY_NORMALISED_NAME`. Other engagement fields are carried into the output.
3. Use UTF-8, comma-separated CSV files. The incident file has headers in the first row. For `ENG_ALL`, field names can run across the first row (one engagement per row) or down the first column (one engagement per column). For Excel, use the active worksheet.

From the project root on Windows, run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe finding.py
```

For subsequent runs, use the last command.

## Read the results

Open `data/output/engagement_candidates.xlsx`. The finder selects incidents whose `class` is exactly `SUPPLIER` and whose supplier name contains usable text after cleaning. Incident names use the configured whole-name aliases. Engagement name fields use only lowercase text and whitespace removal for comparison. The workbook retains the original source values.

For each incident and engagement, the finder tries full equality (`EXACT`) first. It then checks for a literal substring and finally tries fuzzy matching for eligible names. Both partial checks try the normalized field first and produce `PARTIAL`. Each matching pair contributes one workbook row with the original columns from both files and four additional fields.

- `standardised_supplier_name` holds the incident name used in the comparison.
- `matched_supplier_column` identifies the first supplier column that matched in priority order.
- `match_type` records `EXACT` or `PARTIAL`.
- `found_name_in_source` contains the full original ENG_ALL value from the matched column.

An incident can have several candidate rows or none. Each run replaces the previous workbook. The stage guide covers cleaning rules, column priorities and worked examples. [Finding guide](app/finding/docs/README.md)

## Link incidents to engagements

1. Place the Finding output at `data/output/engagement_candidates.xlsx`. This workbook supplies both the incident details and engagement records. Linking groups its rows by `incident_id`.
2. Configure the existing OpenAI or Azure OpenAI connection in the project-root `.env`. See [.env.example](.env.example) for the provider settings and `LLM_TEMPERATURE`. Use a model or deployment that supports structured outputs and the configured temperature.
3. Run `.\.venv\Scripts\python.exe linking.py` from the project root.

For example, an Amazon name match may return ten engagements across hosting, connectivity and backup. Linking sends the incident once with all ten records and assesses each pair. Each request contains 74 incident fields and 22 source fields per engagement. [LLM input columns](app/linking/docs/input-fields.md)

Each candidate receives a decision based on the incident and its own scope. Several engagements can be `LINKED` when each has supporting evidence. A concrete service match with unresolved involvement is `POSSIBLY_LINKED`. Incompatible scope or a supplier name alone yields `NOT_LINKED`. `STRONGEST_LINKED` identifies the sole confirmed engagement or the one with uniquely strongest evidence. Equally supported confirmed leaders remain `LINKED`.

The prompt prioritises recorded findings, accounts for material conflicts and treats repeated claims as one account. The rationale identifies the decisive fact, conflict or missing detail. Source strength and confidence in the selected decision are assessed separately.

Open `data/output/engagement_links.csv`. The CSV contains the original candidate rows and columns in source order, plus eight assessment columns with single-underscore names. All rows for one incident are saved together before the next request. If a run stops, run `python linking.py` again with the same input to continue. A blank `link_decision` on a candidate row means it is pending. [Output columns and recovery](app/linking/docs/README.md)
