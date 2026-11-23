# Finding candidate engagements

Finding retrieves engagement records for incidents already attributed to a named supplier. A supplier can provide several services under different `ENGAGEMENT_ID` values, so one incident can produce many candidate rows. Linking subsequently compares the affected service with each candidate's recorded scope. [Project guide](../../../README.md) · [Linking guide](../../linking/docs/README.md)

## Run and data flow

Install the dependencies using the project guide, then run this command from the project root.

```powershell
.\.venv\Scripts\python.exe finding.py
```

The entry point performs these steps in order.

1. Load and clean the supplier aliases from YAML.
2. Read the incident CSV and select supplier-attributed rows.
3. Clean incident supplier names and apply whole-name aliases.
4. Read ENG_ALL and prepare its two supplier-name comparison fields.
5. Compare each selected incident with every engagement record.
6. Save one candidate per matching incident and engagement ID, write the invalid-name report and print the counts.

Paths are relative to the project root in `finding.py`. Python callers can supply `input_dir` and `output_file` to `main()`. The alias path remains the project configuration path. [Entry point](../../../finding.py)

## Input files and formats

| Input | Location | Required headers |
| --- | --- | --- |
| Incidents | `data/input/CLASSIFIED_INCIDENTS.csv` | `class`, `classified_supplier_name` |
| Engagements | Exactly one of `data/input/ENG_ALL.csv` and `data/input/ENG_ALL.xlsx` | `ENGAGEMENT_ID`, `THIRD_PARTY_NAME`, `THIRD_PARTY_NORMALISED_NAME` |

Finding carries all supplied source columns into its output. The subsequent Linking stage also needs a nonblank `incident_id` and `ENGAGEMENT_ID` on each candidate row. Finding checks the engagement identifier header but allows an individual identifier to be blank.

CSV files use comma separators and UTF-8, with or without a BOM. Incident headers occupy the first row. ENG_ALL supports two layouts.

| Layout | Field names | Engagement records |
| --- | --- | --- |
| Horizontal | First row | Following rows |
| Vertical | First column | Following columns |

The engagement reader first looks for all required names in the first row. Otherwise it checks the first column, discards completely empty field rows, and transposes when all required names appear there. Short vertical rows are padded with empty values. Excel input uses the active worksheet and cached formula results.

Header spelling and case must match. Blank or duplicate headers are rejected. Completely empty data rows are skipped. A nonempty row with a different number of fields from the headers is rejected. Supplying both engagement files, or neither, produces an error. [Table reader](../read_files.py) · [Engagement reader](../read_suppliers.py)

## Incident selection and shared name cleaning

The selector requires `class` to equal `SUPPLIER` exactly. An incident with an empty or whitespace-only name, or one whose name becomes empty during cleaning, goes to the invalid-name report. [Selector](../select_incidents.py)

The incident name and both engagement name fields use the following rules.

1. Convert the supplier name to lowercase.
2. Delete periods, treat `&` as the word `and`, and replace each configured separator with a space.
3. Split on whitespace and remove matching whole words.
4. Join retained words with single spaces.

| Set | Current contents |
| --- | --- |
| `STOP_WORDS` | `a`, `an`, `and`, `of`, `on`, `the`, `holding`, `holdings`, `llm`, `partners`, `solution`, `solutions` |
| `LEGAL_SUFFIXES` | `company`, `corp`, `corporation`, `inc`, `incorporated`, `limited`, `llc`, `llp`, `ltd`, `plc` |
| `SPECIAL_CHARACTERS` | Semicolons, commas, colon, Arabic semicolon and comma, round/square/curly brackets, hyphen/en dash/em dash, underscore, slash, backslash, vertical bar, and straight/curly double quotation marks |

Listed words are removed wherever they appear. Digits and apostrophes are retained. For example, `A.B.C. & Studio 24 Ltd.` becomes `abc studio 24`. [Shared cleaning rules](../clean_incidents.py)

## Whole-name aliases

Exceptions live in `config/supplier_aliases.yml`. Both keys and replacement values pass through the same cleaning function when loaded.

```yaml
gcp: Google Cloud Platform
azure: Microsoft
bt: British Telecom
```

An alias applies once to a whole, nonempty cleaned incident name. `GCP` becomes `google cloud platform`, while `gcp support` retains both words. A later entry takes precedence when keys clean to the same name. [Alias file](../../../config/supplier_aliases.yml) · [Replacement functions](../replace_names.py)

## Engagement name preparation

For `THIRD_PARTY_NORMALISED_NAME` and `THIRD_PARTY_NAME`, Finding keeps the cleaned words for fuzzy comparison and a copy without spaces for equality and substring checks. The original source row supplies the candidate's output values. [Reference cleaning](../clean_suppliers.py)

At matching time, whitespace is also removed from the incident's cleaned, replaced name. This creates the comparison query. The candidate file's `standardised_supplier_name` retains the readable spaces from the earlier step.

| Value | Example |
| --- | --- |
| Incident source name | `The North-Star (Solutions); PLC` |
| Cleaned name saved in the candidate file | `north star` |
| Query used for comparisons | `northstar` |
| Engagement source name | `North Star` |
| Engagement comparison value | `northstar` |

## Matching rules and priority

Finding checks both fields on each engagement and keeps the strongest match for each incident and engagement ID. The fields below are listed in tie-breaking order within a source row.

| Pass | Comparison | First field | Second field | Output label |
| --- | --- | --- | --- | --- |
| 1 | Whole comparison strings are equal | `THIRD_PARTY_NAME` | `THIRD_PARTY_NORMALISED_NAME` | `EXACT` |
| 2 | Incident query occurs within the reference value | `THIRD_PARTY_NORMALISED_NAME` | `THIRD_PARTY_NAME` | `SUBSTRING` |
| 3 | Fuzzy similarity against adjacent reference words | `THIRD_PARTY_NORMALISED_NAME` | `THIRD_PARTY_NAME` | `FUZZY` |

For example, when two records for `E1` yield `FUZZY` and `EXACT`, the exact record supplies every engagement column in the output. A separate `E2` with a fuzzy match is also retained. Across equally ranked records for one ID, the first source record wins. [Matching implementation](../match_rows.py)

### Fuzzy comparison

The `fuzzy-match` library supplies normalized Levenshtein similarity. Its score is `1 - edit_distance / max(query_length, candidate_length)`, with insertion, deletion and substitution costs of one. An adjacent transposition can require two edits.

The fuzzy pass requires a query of at least five characters and similarity of at least `0.72`. It concatenates contiguous words from the cleaned reference field for comparison. Length bounds skip sequences that cannot reach the threshold. The first passing sequence establishes the match.

For example, `microsfot` compared with `microsoft` has a score of approximately `0.778`. It can match the cleaned name from `Microsoft Ltd`. The candidate file records `FUZZY`. [12 worked scenarios](matching.html)

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

An engagement header receives the prefix `ENG.` when it conflicts with an incident header or one of the four added names. Any remaining combined-header conflict is rejected. CSV quoting preserves commas, quotes and embedded newlines. Source values are preserved as loaded, including cached Excel formula values.

Pairs appear in first-encounter order while scanning incidents and then engagements. A stronger match for an existing pair replaces its row in place. All distinct matching IDs remain eligible for each incident. For standalone Finding inputs with a missing identifier, the corresponding source row serves as its own identity. Linking requires both IDs. A run with zero candidates produces a header-only candidate file. [CSV writer](../save_csv.py)

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

Removing common words can make different supplier names equal. For example, `Acme Holdings` and `Acme Solutions` both reduce to `acme`. Supplier status, geography, description and service category are carried forward. Retrieval uses the two supplier-name fields.

The implementation loads tables and candidates into memory and scans all incident–engagement pairs. The `0.72` threshold is a configured rule. A representative labelled dataset is needed to measure retrieval quality for the intended workload.

## Troubleshooting and code map

| Symptom | Check |
| --- | --- |
| Missing engagement file error | Supply exactly one supported ENG_ALL file in `data/input/`. |
| Missing-column or duplicate-header error | Inspect spelling, case, orientation and headers. |
| Wrong number of fields | Check comma quoting and CSV row width. |
| Zero candidates | Check the exact `SUPPLIER` class, cleaned name, aliases and reference fields. |
| Combined-column conflict | Resolve duplicate names remaining after the `ENG.` prefix. |
| Candidate file save failure | Close programs holding the output open and check the path. |

| Module | Responsibility |
| --- | --- |
| [read_incidents.py](../read_incidents.py), [read_suppliers.py](../read_suppliers.py), [read_files.py](../read_files.py) | Source selection and table parsing |
| [select_incidents.py](../select_incidents.py) | Incident eligibility |
| [clean_incidents.py](../clean_incidents.py), [replace_names.py](../replace_names.py) | Incident cleaning and aliases |
| [clean_suppliers.py](../clean_suppliers.py) | Reference comparison values |
| [match_rows.py](../match_rows.py) | Match order, thresholds and candidate collection |
| [save_csv.py](../save_csv.py) | Output headers and candidate file writing |
