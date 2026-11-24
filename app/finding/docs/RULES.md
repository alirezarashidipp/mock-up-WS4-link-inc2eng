# Finding rules

## Inputs and names

- Read UTF-8 CSVs from `data/input/` with unique, nonempty headers in row 1 or, for engagements, column 1. [CSV layouts and row checks](README.md#input-files-and-formats)
- In `CLASSIFIED_INCIDENTS.csv`, require `class` to equal `SUPPLIER` exactly and skip `classified_supplier_name` if blank or equal to `Unknown` after trimming and case-folding.
- `ENG_ALL.csv` requires `ENGAGEMENT_ID` and at least one `search_columns_eng` header (default order `THIRD_PARTY_NAME`, `THIRD_PARTY_NORMALISED_NAME`, `PRAD_NAME`). [Column mapping](../../../config/finding_columns.yml)
- On both sides, lowercase names, delete periods, expand `&` to `and`, replace separators with spaces and drop whole stop words and legal terms, preserving digits and apostrophes. [Cleaning lists](README.md#incident-selection-and-shared-name-cleaning)
- Apply the last matching whole-name alias once to the cleaned incident name only, then remove spaces to form and measure the query. [Aliases](../../../config/supplier_aliases.yml)

## Matching

Search each available, nonempty cleaned `search_columns_eng` field in YAML order and send its first passing match to deduplication.

| Method | Query length | Rule |
| --- | --- | --- |
| `EXACT` | 1+ | Both full cleaned names are equal without spaces. |
| `SUBSTRING` | 1–4 | Match a whole reference word (`ICE` matches `ICE Data Services` and skips `Office Supplies`). |
| `SUBSTRING` | 5+ | Match anywhere in the cleaned field without spaces, including across words. |
| `FUZZY` | 5+ | Require normalized Levenshtein similarity ≥ `0.72` against one or more consecutive cleaned reference words joined without spaces. |

## Deduplication

- Keep the strongest full row for every distinct `(incident_id, ENGAGEMENT_ID)` pair using `EXACT` > `SUBSTRING` > `FUZZY`.
- Ties go to the first matching source row, then the first tied column in `search_columns_eng` order.
- A missing or blank ID uses its source-row position for deduplication.
- Pairs stay in first-match order even when a later row wins.

## Output in `data/output/`

- `engagement_candidates.csv` preserves all original incident then engagement values and appends `standardised_supplier_name` (spaces retained), `matched_supplier_column`, `match_type` and `found_name_in_source` (original value).
- Prefix conflicting engagement headers with `ENG.` and reject remaining duplicates.
- For each selected incident with an empty query, record its ID, original name and `invalid name` in `engagement_candidates_invalid_names.csv`.
- Valid unmatched names produce no rows, and each run rewrites both UTF-8 CSVs with a BOM and headers even when empty.
