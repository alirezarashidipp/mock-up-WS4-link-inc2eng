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

An incident can have several candidate rows or none. Each run replaces the previous workbook. The stage guide covers cleaning rules, column priorities and worked examples. [Finding guide](docs/finding/README.md)

## Link incidents to engagements

1. Place the Finding output at `data/output/engagement_candidates.xlsx`. This workbook supplies both the incident details and engagement records. Linking groups its rows by `incident_id`.
2. Configure the existing OpenAI or Azure OpenAI connection in the project-root `.env`. See [.env.example](.env.example) for the provider settings and `LLM_TEMPERATURE`. Use a model or deployment that supports structured outputs and the configured temperature.
3. Run `.\.venv\Scripts\python.exe linking.py` from the project root.

The linking guide explains which fields reach the model, how it ranks candidates and what each decision means. [Linking guide](docs/linking/README.md)

All candidate engagements for an incident go into one comparison. The code numbers them from 1, and the model returns every plausible candidate in rank order with a rationale and citations. The code resolves those numbers to the original engagement records and copies their IDs into the output.

Open `data/output/engagement_links.xlsx`. Each distinct incident in the candidate workbook gets one row. Candidate columns expand to fit the largest returned ranking. Each rank has a source engagement ID and a rationale containing both citations. The decision is `LINKED` or `NOT_LINKED`. For `LINKED`, the code fills `selected_engagement_id` from the first-ranked record. `confidence` assesses the decision, while `incident_evidence_strength` assesses the incident evidence. `decision_reason` explains both. A `LINKED` decision also includes `linked_strength` (`WEAK`, `MODERATE` or `STRONG`) and a one-sentence `linked_strength_reason` explaining the evidence connecting the selected engagement to the affected service. These two columns are blank for `NOT_LINKED`.
