# WS4 incident-to-engagement candidate finder

This Python demo finds engagement records for supplier-caused incidents. Stage one writes the name matches to Excel. Stage two sends each incident and its candidate engagements to the configured LLM and writes a separate decision workbook.

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

An incident can have several candidate rows or none. Each run replaces the previous workbook. For cleaning rules, column priorities, and the module layout, see [Current state](docs/current-state.md).

## Link incidents to engagements

1. Include a unique, nonblank `incident_id` for each eligible incident and run the finder on the current inputs.
2. Configure the existing OpenAI or Azure OpenAI connection in the project-root `.env`. See [.env.example](.env.example) for the provider settings and `LLM_TEMPERATURE`. Use a model or deployment that supports structured outputs and the configured temperature.
3. Run `.\.venv\Scripts\python.exe linking.py` from the project root.

The two lists in [fields.py](app/linking/fields.py) name every source column sent to the LLM. Edit [prompt.yml](app/linking/prompt.yml) to change the linking instructions. The [Pydantic schema](app/linking/schema.py) defines the structured response fields.

Open `data/output/engagement_links.xlsx`. Each eligible incident gets one row. Each of the three rank slots has an engagement ID and a rationale with a field and excerpt from each source. The top three limit applies to the response. All candidate engagements for the incident go into the comparison. The separate `selected_engagement_id` holds the first-ranked ID only when the model can choose one. Read `decision_reason` alongside the overall `confidence` tag to understand a selection or abstention. An incident with zero candidates gets a local `NO_CANDIDATES` row.
