# WS4 incident-to-engagement candidate finder

This Python demo takes incidents already classified as supplier-caused and finds engagement records to review. Stage one runs locally and writes an Excel workbook. LLM-based selection of the final engagement is pending.

## Run the finder

1. Put `CLASSIFIED_INCIDENTS.csv` in `data/input/`. It must contain the headers `class` and `classified_supplier_name`.
2. In the same folder, supply exactly one of `RAW_SPS_SUPPLIER_DETAIL.csv` or `RAW_SPS_SUPPLIER_DETAIL.xlsx`. It must contain `ENG ID`, `SUPPLIER_TRADING_NAME`, `SUPPLIER_NORMALISED_BUSINESS_NAME`, `SUPPLIER_ALTERNATE_NAME`, `SUPPLIER_NAME`, and `SUPPLIER_DNB_MATCHED_BUSINESS_NAME`.
3. Use comma-separated UTF-8 CSV files, or put the supplier table on the active Excel worksheet. The first row holds the column headers.

From the project root on Windows, run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe finding.py
```

For subsequent runs, use the last command.

## Read the results

Open `data/output/engagement_candidates.xlsx`. The finder selects incidents whose `class` is exactly `SUPPLIER` and whose supplier name contains usable text after cleaning. It cleans the five supplier name fields with the same rules and applies whole-name replacements from [supplier_aliases.yml](config/supplier_aliases.yml).

For each incident and supplier row, the finder tries full equality (`EXACT`) first, then checks whether the incident name occurs anywhere within a supplier field (`PARTIAL`). Each matching pair contributes one workbook row with the original columns from both files and three additional fields:

- `standardised_supplier_name` holds the incident name used in the comparison.
- `matched_supplier_column` identifies the first supplier column that matched in priority order.
- `match_type` records `EXACT` or `PARTIAL`.

An incident can have several candidate rows or none. Each run replaces the previous workbook. For cleaning rules, column priorities, and the module layout, see [Current state](docs/current-state.md).
