# WS4 incident-to-engagement candidate finder

This Python demo takes incidents already classified as supplier-caused and finds engagement records to review. Stage one runs locally and writes an Excel workbook. LLM-based selection of the final engagement is pending.

## Run the finder

1. Put `CLASSIFIED_INCIDENTS.csv` in `data/input/`. It must contain the headers `class` and `classified_supplier_name`.
2. In the same folder, supply either `ENG_ALL.csv` or `ENG_ALL.xlsx`. The required fields are `ENGAGEMENT_ID`, `THIRD_PARTY_NAME` and `THIRD_PARTY_NORMALIZED_NAME`. The older spelling `THIRD_PARTY_NORMALISED_NAME` is also accepted. If both spellings exist, the finder searches the Z spelling. Other engagement fields are carried into the output.
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
