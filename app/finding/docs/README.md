# Finding candidate engagements

Finding retrieves engagement records for incidents already attributed to a named supplier. A supplier can provide several services under different `ENGAGEMENT_ID` values, so one incident can produce many candidate rows. Linking subsequently compares the affected service with each candidate's recorded scope. [Project guide](../../../README.md) · [Linking guide](../../linking/docs/README.md)

## Run and data flow

Install the dependencies using the project guide, then run this command from the project root.

```powershell
.\.venv\Scripts\python.exe finding.py
```

The entry point performs these steps in order.

1. Load the CSV column mappings and whole-name supplier aliases from YAML.
2. Read the incident CSV and select supplier-attributed rows.
3. Clean incident supplier names and apply whole-name aliases.
4. Read ENG_ALL and clean the available fields listed in `engagement.search_columns_eng`.
5. Compare each selected incident with every engagement record and yield each matching field.
6. Deduplicate the matches by incident and engagement ID, keeping the strongest row for each pair.
7. Save the candidates, write the invalid-name report and print the counts.

Paths are relative to the project root in `finding.py`. Python callers can supply `input_dir`, `output_file` and `columns_file` to `main()`. [Entry point](../../../finding.py)

## Input files and formats

Edit the values in [finding_columns.yml](../../../config/finding_columns.yml) to match your CSV headers. The keys identify each column's role. The invalid-name report reuses the incident identifier and supplier headers. The examples below use the default mapping. Linking expects its documented headers when consuming Finding output.

| Input | Location | Required headers |
| --- | --- | --- |
| Incidents | `data/input/CLASSIFIED_INCIDENTS.csv` | `class`, `classified_supplier_name` |
| Engagements | `data/input/ENG_ALL.csv` | Engagement identifier and at least one header in `search_columns_eng` |

The default engagement mapping uses three search fields.

```yaml
engagement:
  identifier: ENGAGEMENT_ID
  search_columns_eng:
    - THIRD_PARTY_NAME
    - THIRD_PARTY_NORMALISED_NAME
    - PRAD_NAME
```

List one or more distinct, nonblank CSV headers. Add a header to search it, remove it to stop searching it, or move it up to give it priority in a same-row tie. Finding skips headers absent from a particular CSV and reports an error if none of the configured search fields are present.

Finding carries all supplied source columns into its output. The subsequent Linking stage also needs a nonblank `incident_id` and `ENGAGEMENT_ID` on each candidate row. Finding checks the engagement identifier header but allows an individual identifier to be blank.

CSV files use comma separators and UTF-8, with or without a BOM. Incident headers occupy the first row. ENG_ALL supports two layouts.

| Layout | Field names | Engagement records |
| --- | --- | --- |
| Horizontal | First row | Following rows |
| Vertical | First column | Following columns |

The engagement reader first looks for all required names in the first row. Otherwise it checks the first column, discards completely empty field rows, and transposes when all required names appear there. Short vertical rows are padded with empty values.

Header spelling and case must match. Blank or duplicate headers are rejected. Completely empty data rows are skipped. A nonempty row with a different number of fields from the headers is rejected. [Table reader](../read_files.py) · [Engagement reader](../read_suppliers.py)

## Incident selection and shared name cleaning

The selector requires `class` to equal `SUPPLIER` exactly. It skips rows where `classified_supplier_name` is blank, contains only whitespace or equals `Unknown` after trimming surrounding whitespace and ignoring case. The check uses the whole source name, so `Unknown Ventures` remains eligible. Filtered rows produce no output. A selected name such as `Solutions Ltd` that becomes empty during cleaning goes to the invalid-name report. [Selector](../select_incidents.py)

The incident name and each configured engagement search field use the following rules.

1. Convert the supplier name to lowercase.
2. Delete periods, treat `&` as the word `and`, and replace each configured separator with a space.
3. Split on whitespace and remove matching whole words.
4. Join retained words with single spaces.

| Set | Current contents |
| --- | --- |
| `STOP_WORDS` | `a`, `an`, `and`, `of`, `on`, `the`, `holding`, `holdings`, `llm`, `partners`, `solution`, `solutions` |
| `LEGAL_SUFFIXES` | `company`, `corp`, `corporation`, `inc`, `incorporated`, `limited`, `llc`, `llp`, `ltd`, `plc` |
| `SPECIAL_CHARACTERS` | Semicolons, commas, colon, Arabic semicolon and comma, round/square/curly brackets, hyphen/en dash/em dash, underscore, slash, backslash, vertical bar, and straight/curly double quotation marks |

Listed words are removed wherever they appear. Digits and apostrophes are retained. For example, `A.B.C. & Studio 24 Ltd.` becomes `abc studio 24`. [Shared cleaning rules](../clean_names.py)

## Whole-name aliases

Exceptions live in `config/supplier_aliases.yml`. Both keys and replacement values pass through the same cleaning function when loaded.

```yaml
gcp: Google Cloud Platform
azure: Microsoft
bt: British Telecom
```

An alias applies once to a whole, nonempty cleaned incident name. `GCP` becomes `google cloud platform`, while `gcp support` retains both words. A later entry takes precedence when keys clean to the same name. [Alias file](../../../config/supplier_aliases.yml) · [Replacement functions](../replace_names.py)

## Engagement name preparation

For each configured field with a usable value, Finding keeps the cleaned words for fuzzy comparison and a copy without spaces for equality and substring checks. The original source row supplies the candidate's output values. [Reference cleaning](../clean_suppliers.py)

At matching time, whitespace is also removed from the incident's cleaned, replaced name. This creates the comparison query. The candidate file's `standardised_supplier_name` retains the readable spaces from the earlier step.

| Value | Example |
| --- | --- |
| Incident source name | `The North-Star (Solutions); PLC` |
| Cleaned name saved in the candidate file | `north star` |
| Query used for comparisons | `northstar` |
| Engagement source name | `North Star` |
| Engagement comparison value | `northstar` |

## Matching rules and priority

Finding compares the incident search name with each configured field in YAML order. Each matching field yields one result with its strongest method. All of these results go to candidate deduplication. [Field matching](../match_rows.py)

| Priority | Comparison | Output label |
| --- | --- | --- |
| 1 | Whole comparison strings are equal | `EXACT` |
| 2 | Incident query occurs within the reference value | `SUBSTRING` |
| 3 | Fuzzy similarity against adjacent reference words reaches the threshold | `FUZZY` |

For example, an `AXA` incident matches `THIRD_PARTY_NAME = AXA UK` by substring and `PRAD_NAME = AXA` exactly on the same engagement. The saved candidate records `EXACT`, `PRAD_NAME` and the source value `AXA`.

### Fuzzy comparison

The `fuzzy-match` library supplies normalized Levenshtein similarity. Its score is `1 - edit_distance / max(query_length, candidate_length)`, with insertion, deletion and substitution costs of one. An adjacent transposition can require two edits.

The fuzzy pass requires a query of at least five characters and similarity of at least `0.72`. It concatenates contiguous words from the cleaned reference field for comparison. Length bounds skip sequences that cannot reach the threshold. The first passing sequence establishes the match.

For example, `microsfot` compared with `microsoft` has a score of approximately `0.778`. It can match the cleaned name from `Microsoft Ltd`. The candidate file records `FUZZY`. [12 worked scenarios](matching.html)

## Candidate deduplication

The candidate CSV contains one row per matching `(incident_id, ENGAGEMENT_ID)` pair. Different engagement IDs can qualify for the same incident, and the same engagement ID can qualify for several incidents.

| Condition | Row kept in the CSV |
| --- | --- |
| A pair has matches of different types | The strongest match and its full source row. Priority is `EXACT`, then `SUBSTRING`, then `FUZZY`. |
| Several fields on the same source row tie on method | The first matching field in `search_columns_eng` order. |
| Multiple source records share the strongest match type for a pair | The first such record in input order. |
| An identifier is missing or blank | Finding uses the corresponding source row's position as its identity. Linking requires both IDs to be populated. |

Pairs appear in the order of their first match, even when a later record supplies the strongest match. For example, if incident `I01` matches `E07` by both `FUZZY` and `EXACT`, its output contains one `E07` row with `EXACT`. A match between `I02` and `E07` has its own output row. [Deduplication rules in code](../deduplicate_candidates.py)

## Output candidate file

The output is `data/output/engagement_candidates.csv`, a UTF-8 CSV with a BOM and a header row. Columns appear in this order.

1. All incident columns in input order.
2. All engagement columns in input order.
3. The four matching details below.

| Added column | Contents |
| --- | --- |
| `standardised_supplier_name` | Cleaned incident supplier name after alias replacement |
| `matched_supplier_column` | Original ENG_ALL field producing the retained match |
| `match_type` | `EXACT`, `SUBSTRING` or `FUZZY` |
| `found_name_in_source` | Full original value from that engagement field |

An engagement header receives the prefix `ENG.` when it conflicts with an incident header or one of the four added names. Any remaining combined-header conflict is rejected. CSV quoting preserves commas, quotes and embedded newlines. Source values are preserved as loaded, including leading zeros in identifiers.

A run with zero candidates produces a header-only candidate file. [CSV writer](../save_csv.py)

The sibling report `<output-stem>_invalid_names.csv` records `incident_id`, the original `classified_supplier_name` and `finding_status` (`invalid name`) for each selected incident with an empty cleaned name. By default this is `engagement_candidates_invalid_names.csv`. Each run refreshes the report, including a header-only report when all selected names are usable. Valid names with zero matches contribute no rows to either file.

## Interpreting results and limitations

| Situation | Current behavior |
| --- | --- |
| `PINGidentity` versus `Ping Identity` | Whitespace-insensitive equality can produce `EXACT`. |
| `Microsfot` versus `Microsoft Ltd` | The fuzzy pass can produce `FUZZY`. |
| `IBM` versus `IBN` | The query is too short for the fuzzy pass. |
| `BT` versus `btartbox` | The alias changes the query to `britishtelecom`. This pair produces zero matches. |
| `XY` versus `XYartbox` | The short name has no alias. The literal substring pass produces `SUBSTRING`. |
| Several services from one supplier | All distinct matching engagement IDs become candidates. |
| An abbreviation outside the alias file | Exact, substring and fuzzy comparisons determine the result. |

Removing common words can make different supplier names equal. For example, `Acme Holdings` and `Acme Solutions` both reduce to `acme`. Supplier status, geography, description and service category are carried forward. Retrieval uses the configured search fields.

The implementation loads tables and candidates into memory and scans all incident–engagement pairs. The `0.72` threshold is a configured rule. A representative labelled dataset is needed to measure retrieval quality for the intended workload.

## Troubleshooting and code map

| Symptom | Check |
| --- | --- |
| Missing engagement file error | Supply `data/input/ENG_ALL.csv`. |
| Missing-column or duplicate-header error | Inspect spelling, case, orientation and headers. |
| Wrong number of fields | Check comma quoting and CSV row width. |
| Zero candidates | Check the exact `SUPPLIER` class, cleaned name, aliases and reference fields. |
| Combined-column conflict | Resolve duplicate names remaining after the `ENG.` prefix. |
| Candidate file save failure | Close programs holding the output open and check the path. |

| Module | Responsibility |
| --- | --- |
| [read_incidents.py](../read_incidents.py), [read_suppliers.py](../read_suppliers.py), [read_files.py](../read_files.py) | Source selection and table parsing |
| [select_incidents.py](../select_incidents.py) | Incident eligibility |
| [clean_names.py](../clean_names.py) | Shared rules for cleaning a single supplier name |
| [clean_incidents.py](../clean_incidents.py) | Apply the shared cleaner to each incident's classified supplier name |
| [replace_names.py](../replace_names.py) | Apply whole-name aliases to incident names |
| [clean_suppliers.py](../clean_suppliers.py) | Reference comparison values |
| [match_rows.py](../match_rows.py) | Compare supplier fields and yield matches in source order |
| [deduplicate_candidates.py](../deduplicate_candidates.py) | Keep the strongest candidate per incident and engagement ID |
| [save_csv.py](../save_csv.py) | Output headers and candidate file writing |
