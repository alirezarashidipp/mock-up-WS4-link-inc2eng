# Current state

Stage one runs locally with Python. Install dependencies with `python -m pip install -r requirements.txt` and run `python finding.py` from the project root.

The stage-one steps are visible in `finding.py`. Their implementations are in `app/finding/`.

| Step | Module |
| --- | --- |
| Read incident rows | `read_incidents.py` |
| Select eligible incidents | `select_incidents.py` |
| Clean incident supplier names | `clean_incidents.py` |
| Load and apply the YAML name replacements | `replace_names.py` |
| Read engagement records from `ENG_ALL` | `read_suppliers.py` |
| Clean the two third-party name fields | `clean_suppliers.py` |
| Find matching candidate records | `match_rows.py` |
| Save the Excel workbook | `save_excel.py` |

Both input readers use `read_files.py` for table parsing.

Place `CLASSIFIED_INCIDENTS.csv` and exactly one of `ENG_ALL.csv` or `ENG_ALL.xlsx` in `data/input/`. CSV inputs use UTF-8 and commas. Excel input uses the active worksheet. The incident file has headers in its first row. The engagement file accepts headers in the first row or field names down the first column with one engagement in each subsequent column. It requires `ENGAGEMENT_ID` and both third-party name fields. All additional source fields, including engagement name, description and management hierarchy, are copied into each matching output row.

Only `SUPPLIER` incidents with a usable `classified_supplier_name` enter matching. Incident names use three lists in `app/finding/clean_incidents.py`.

- `SPECIAL_CHARACTERS` become spaces before word removal.
- `STOP_WORDS` removes whole words such as `the`, `of`, `holding`, `partners`, `llm` and `solutions`.
- `LEGAL_SUFFIXES` removes corporate designators such as `plc`, `llc`, `corporation`, `inc` and `ltd`. They are matched as whole words anywhere in the name, including forms with a trailing period such as `Inc.`.

The incident cleaner lowercases the text and collapses whitespace. Whole-name YAML replacements apply after cleaning. For example, the cleaned incident name `gcp` maps to `google cloud platform`. An incident whose name becomes empty produces no candidates.

Engagement names use lowercase text with all whitespace removed for comparison. Punctuation, legal suffixes and words such as `the` remain part of the engagement name. The incident search name is also compared without whitespace. For example, incident `PingIdentity` matches engagement `Ping Identity` exactly. The normalized field can have the older spelling `THIRD_PARTY_NORMALISED_NAME`. If both spellings exist, the finder uses `THIRD_PARTY_NORMALIZED_NAME` and preserves all source fields in the workbook.

| Check order for one engagement | First field | Second field | Output label |
| --- | --- | --- | --- |
| Full equality | `THIRD_PARTY_NAME` | Normalized field | `EXACT` |
| Incident name occurs literally anywhere in the engagement name | Normalized field | `THIRD_PARTY_NAME` | `PARTIAL` |
| Fuzzy comparison | Normalized field | `THIRD_PARTY_NAME` | `PARTIAL` |

Fuzzy comparisons use the `fuzzy-match` library and normalized Levenshtein similarity. The compact incident name must contain at least five characters. A score of at least 0.72 against a contiguous sequence of engagement-name words qualifies as a partial match. Literal substring checks apply even to shorter names, so `BT` can match `DEBT`. The first successful check produces one row for that incident and engagement. Different engagements can produce both exact and partial candidates for one incident.

`data/output/engagement_candidates.xlsx` contains both original records followed by `standardised_supplier_name`, `matched_supplier_column`, `match_type` and `found_name_in_source`. The last field copies the full source cell selected by the matcher, preserving its casing, punctuation and spacing. When a supplier header overlaps an incident header, the supplier header gets an `ENG.` prefix. Each run replaces the previous workbook. The INC and ENG dictionaries in `config/` document the input fields. ENG definitions are provisional descriptions based on the supplied headers.

Stage two (LLM engagement selection) is pending. The existing LLM connection module is independent of this stage.
