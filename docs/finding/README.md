# Finding candidate engagements

Run `python finding.py` from the project root. Place `CLASSIFIED_INCIDENTS.csv` and either `ENG_ALL.csv` or `ENG_ALL.xlsx` in `data/input/`.

The finder selects incidents with `class = SUPPLIER` and a usable `classified_supplier_name`. It lowercases the incident name, replaces listed symbols with spaces, removes stop words and legal suffixes, and applies whole-name aliases. For the engagement names, it lowercases the source text and removes whitespace. Original values from both files are preserved in Excel. [Cleaning rules](../../app/finding/clean_incidents.py) · [Supplier aliases](../../config/supplier_aliases.yml)

For each incident and engagement record, the first successful comparison determines the reported match.

| Comparison order | First engagement field | Second engagement field | Output label |
| --- | --- | --- | --- |
| 1. Full name equality | `THIRD_PARTY_NAME` | `THIRD_PARTY_NORMALISED_NAME` | `EXACT` |
| 2. Incident name occurs within the engagement name | `THIRD_PARTY_NORMALISED_NAME` | `THIRD_PARTY_NAME` | `PARTIAL` |
| 3. Fuzzy match against adjacent whole words | `THIRD_PARTY_NORMALISED_NAME` | `THIRD_PARTY_NAME` | `PARTIAL` |

The fuzzy comparison requires at least five characters in the incident name after whitespace removal and a Levenshtein similarity of at least 0.72. [Matching code](../../app/finding/match_rows.py) · [12 worked examples](matching.html)

`data/output/engagement_candidates.xlsx` contains one row per matching pair. Each row includes the original source columns plus `standardised_supplier_name`, `matched_supplier_column`, `match_type` and `found_name_in_source`. An incident with zero matches contributes zero rows.
