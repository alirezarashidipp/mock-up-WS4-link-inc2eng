# Finding candidate engagements

Finding starts with an HSBC incident already attributed to a supplier. It uses the supplier name from that classification to retrieve candidate engagements. A supplier may deliver several services under different `ENGAGEMENT_ID` values.

Run `python finding.py` from the project root. Place `CLASSIFIED_INCIDENTS.csv` and either `ENG_ALL.csv` or `ENG_ALL.xlsx` in `data/input/`.

The finder selects incidents with `class = SUPPLIER` and a usable `classified_supplier_name`. It lowercases that supplier name, replaces listed symbols with spaces, removes stop words and legal suffixes, and applies whole-name aliases. For the two third-party name fields in `ENG_ALL`, it lowercases the source text and removes whitespace. [Cleaning rules](../../app/finding/clean_incidents.py) · [Supplier aliases](../../config/supplier_aliases.yml)

For each incident and engagement record, the first successful supplier-name comparison determines the reported match.

| Comparison order | First engagement field | Second engagement field | Output label |
| --- | --- | --- | --- |
| 1. Full name equality | `THIRD_PARTY_NAME` | `THIRD_PARTY_NORMALISED_NAME` | `EXACT` |
| 2. The incident's supplier name occurs within a third-party name | `THIRD_PARTY_NORMALISED_NAME` | `THIRD_PARTY_NAME` | `PARTIAL` |
| 3. Fuzzy match against adjacent whole words | `THIRD_PARTY_NORMALISED_NAME` | `THIRD_PARTY_NAME` | `PARTIAL` |

The fuzzy comparison requires at least five characters in the incident name after whitespace removal and a Levenshtein similarity of at least 0.72. [Matching code](../../app/finding/match_rows.py) · [12 worked examples](matching.html)

`data/output/engagement_candidates.xlsx` has one worksheet, `Engagement candidates`, with one row per matching incident and engagement record. The original source values appear alongside the search name (`standardised_supplier_name`), the matched column (`matched_supplier_column`), the match label (`match_type`) and the value as recorded in `ENG_ALL` (`found_name_in_source`). An incident with zero matches contributes zero rows.

For example, if Amazon matches ten engagement records for one incident, Finding writes ten rows. Linking compares the incident evidence with the service described in each of those records. [Linking guide](../linking/README.md)
