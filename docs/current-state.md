# Current state

Stage one runs locally with Python. Install dependencies with `python -m pip install -r requirements.txt` and run `python finding.py` from the project root.

`finding.py` coordinates four modules in `app/finding/`. `read_files.py` reads the inputs, `clean_rows.py` filters incidents and standardises names, `match_rows.py` finds candidate records, and `save_excel.py` writes the workbook.

Place CLASSIFIED_INCIDENTS.csv and one RAW_SPS_SUPPLIER_DETAIL.csv or RAW_SPS_SUPPLIER_DETAIL.xlsx in data/input. CSV inputs use UTF-8 and commas. Excel input uses the active worksheet. The first row contains headers, including the literal ENG ID in supplier detail.

Only SUPPLIER incidents with a usable classified_supplier_name enter matching. Both sides are lowercased. Semicolons and parentheses become spaces, repeated whitespace collapses, and whole-name aliases from the YAML file are applied.

Each incident is compared with each supplier row. Exact equality takes priority within that row. Otherwise the incident name must occur within a supplier field. The first matching column in the relevant priority list wins. Different supplier rows can produce both exact and partial candidates for one incident. Unmatched incidents produce no candidate rows.

data/output/engagement_candidates.xlsx contains both original records followed by the standardised name, matching column and match type. Each run replaces the previous workbook. The INC and ENG dictionaries in config document the input fields. ENG definitions are provisional descriptions based on the supplied headers.

Stage two (LLM engagement selection) is pending. The existing LLM connection module is independent of this stage.
