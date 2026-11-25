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
6. Keep the strongest match for each incident–engagement pair and one status row for each selected incident with zero candidates.
7. Save all results in `engagement_candidates.csv` and print the counts.

Paths are relative to the project root in `finding.py`. Python callers can supply `input_dir`, `output_file` and `columns_file` to `main()`. [Entry point](../../../finding.py)

## Input files and formats

The column mapping identifies the role of each input and output header. The `candidate.status` setting names the status column, which defaults to `finding_status`. Linking uses its documented headers by default. [Column mapping](../../../config/finding_columns.yml)

| Input | Location | Required headers |
| --- | --- | --- |
| Incidents | `data/input/CLASSIFIED_INCIDENTS.csv` | `class`, `classified_supplier_name` |
| Engagements | `data/input/ENG_ALL.csv` | Engagement identifier and at least one header in `search_columns_eng` |

For example, a mapping can search these three engagement fields.

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

The selector requires `class` to equal `SUPPLIER` exactly. It skips rows where `classified_supplier_name` is blank, contains only whitespace or equals `Unknown` after trimming surrounding whitespace and ignoring case. The check uses the whole source name, so `Unknown Ventures` remains eligible. Filtered rows produce no output. A selected incident whose only name is `Solutions Ltd` receives `INVALID_NAME` because cleaning removes every word. [Selector](../select_incidents.py)

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

For each configured field with a usable value, Finding keeps the cleaned words for whole-word and fuzzy comparisons. It also keeps a copy without spaces for full-name equality and longer substring searches. The original source row supplies the candidate's output values. [Reference cleaning](../clean_suppliers.py)

At matching time, Finding removes spaces from the cleaned incident name after alias replacement. The length of this query determines the substring rule and whether fuzzy matching is available. The candidate file's `standardised_supplier_name` retains the readable spaces from the earlier step.

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
| 1 | The query equals the entire cleaned reference field with spaces removed | `EXACT` |
| 2 | For 1–4 characters, the query equals one word in the cleaned reference field. For 5 or more, it occurs anywhere in the field with spaces removed. | `SUBSTRING` |
| 3 | A query of at least 5 characters reaches the fuzzy similarity threshold against adjacent reference words | `FUZZY` |

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
| An identifier is missing or blank | Finding uses the corresponding source row's position as its identity. Linking requires both IDs on each matched row. |

Pairs appear in the order of their first match, even when a later record supplies the strongest match. For example, if incident `I01` matches `E07` by both `FUZZY` and `EXACT`, its output contains one `E07` row with `EXACT`. A match between `I02` and `E07` has its own output row. [Deduplication rules in code](../deduplicate_candidates.py)

## Output candidate file

The output is `data/output/engagement_candidates.csv`, a UTF-8 CSV with a BOM and a header row. Columns appear in this order.

1. All incident columns in input order.
2. All engagement columns in input order.
3. Four matching details followed by the Finding status.

| Added column | Contents |
| --- | --- |
| `standardised_supplier_name` | Cleaned incident supplier name after alias replacement |
| `matched_supplier_column` | Original ENG_ALL field producing the retained match |
| `match_type` | `EXACT`, `SUBSTRING` or `FUZZY` |
| `found_name_in_source` | Full original value from that engagement field |
| `finding_status` | `MATCHED`, `NO_MATCH` or `INVALID_NAME` |

An engagement header receives the prefix `ENG.` when it conflicts with an incident header or an added column. Any remaining combined-header conflict is rejected. CSV quoting preserves commas, quotes and embedded newlines. Source values are preserved as loaded, including leading zeros in identifiers.

Each run writes one CSV. A `MATCHED` row holds one retained engagement. A selected incident with a usable search name and zero candidates gets one `NO_MATCH` row. A selected incident whose search name is empty after cleaning and alias replacement gets one `INVALID_NAME` row. Both incident-only rows preserve the incident source values, leave every engagement cell empty, and leave `matched_supplier_column`, `match_type` and `found_name_in_source` empty. `NO_MATCH` retains the standardised search name.

If an incident ID repeats, any real match takes precedence over an incident-only row. When every occurrence misses, Finding retains the first usable search name, or the first selected row if all names are invalid. With zero selected incidents the CSV contains only its headers. [CSV writer](../save_csv.py)

## Interpreting results and limitations

| Situation | Current behavior |
| --- | --- |
| `PINGidentity` versus `Ping Identity` | Whitespace-insensitive equality can produce `EXACT`. |
| `Microsfot` versus `Microsoft Ltd` | The fuzzy pass can produce `FUZZY`. |
| `IBM` versus `IBN` | The query is too short for the fuzzy pass. |
| `BT` versus `btartbox` | The alias changes the query to `britishtelecom`. This pair produces zero matches. |
| `ICE` versus `ICE Data Services`, or `INE` versus `UK-INE` | Each query is a complete word after cleaning. Both pairs produce `SUBSTRING`. |
| `ICE` versus `Office Supplies`, `INE` versus `Online`, or `XY` versus `XYartbox` | Each query occurs inside a longer word. These pairs produce zero matches. |
| Several services from one supplier | All distinct matching engagement IDs become candidates. |
| An abbreviation outside the alias file | Finding searches for the cleaned abbreviation using the rules for its length. |

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
