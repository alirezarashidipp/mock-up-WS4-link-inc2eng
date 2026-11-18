# Current state

Stage one runs locally with Python. Install dependencies with `python -m pip install -r requirements.txt` and run `python finding.py` from the project root.

The stage-one steps are visible in `finding.py`. Their implementations are in `app/finding/`.

| Step | Module |
| --- | --- |
| Read incident rows | `read_incidents.py` |
| Select eligible incidents | `select_incidents.py` |
| Clean incident supplier names | `clean_incidents.py` |
| Load and apply the YAML name replacements | `replace_names.py` |
| Read supplier records | `read_suppliers.py` |
| Clean the five supplier name fields | `clean_suppliers.py` |
| Find matching candidate records | `match_rows.py` |
| Save the Excel workbook | `save_excel.py` |

Both input readers use `read_files.py` for table parsing. Both cleaners use the same name-cleaning rules.

Place CLASSIFIED_INCIDENTS.csv and one RAW_SPS_SUPPLIER_DETAIL.csv or RAW_SPS_SUPPLIER_DETAIL.xlsx in data/input. CSV inputs use UTF-8 and commas. Excel input uses the active worksheet. The first row contains headers, including the literal ENG ID in supplier detail.

Only SUPPLIER incidents with a usable classified_supplier_name enter matching. The cleaner lowercases names from both files and replaces the separators listed in `SYMBOLS_TO_REMOVE` with spaces, including commas, brackets, dashes, slashes and double quotes. It removes the whole words `the`, `and`, `a`, `an`, `on`, `plc`, `limited`, `llc`, `company` and `solutions`, then collapses whitespace. Whole-name aliases from the YAML file apply to the cleaned names.

Each incident is compared with each supplier row. Exact equality takes priority within that row. Otherwise the incident name must occur within a supplier field. The first matching column in the relevant priority list wins. Different supplier rows can produce both exact and partial candidates for one incident. Unmatched incidents produce no candidate rows.

| Priority | `EXACT` column | `PARTIAL` column |
| --- | --- | --- |
| 1 | `SUPPLIER_TRADING_NAME` | `SUPPLIER_ALTERNATE_NAME` |
| 2 | `SUPPLIER_NORMALISED_BUSINESS_NAME` | `SUPPLIER_NAME` |
| 3 | `SUPPLIER_ALTERNATE_NAME` | `SUPPLIER_NORMALISED_BUSINESS_NAME` |
| 4 | `SUPPLIER_NAME` | `SUPPLIER_DNB_MATCHED_BUSINESS_NAME` |
| 5 | `SUPPLIER_DNB_MATCHED_BUSINESS_NAME` | `SUPPLIER_TRADING_NAME` |

For example, `The North-Star (Solutions); PLC` and `North Star Limited` both become `north star` and match exactly. The YAML maps the whole cleaned value `gcp` to `google cloud platform`. A value such as `gcp uk` keeps its original words. Partial matching uses a literal substring, so `BT` can match `DEBT`. Typo tolerance and word-boundary matching are possible future changes.

`data/output/engagement_candidates.xlsx` contains both original records followed by `standardised_supplier_name`, `matched_supplier_column` and `match_type`. When a supplier header overlaps an incident header, the supplier header gets an `ENG.` prefix. Each run replaces the previous workbook. The INC and ENG dictionaries in `config/` document the input fields. ENG definitions are provisional descriptions based on the supplied headers.

Stage two (LLM engagement selection) is pending. The existing LLM connection module is independent of this stage.
