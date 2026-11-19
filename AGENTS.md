# Project instructions

Keep the stage-one entry point in `finding.py` at the project root. Use plain functions under `app/finding/`. In `main()`, show the steps for reading each source, selecting incident rows, cleaning names, applying alias replacements, matching and saving.

Preserve original source values in the candidate workbook. Change supplier exceptions in `config/supplier_aliases.yml`. Keep code, definitions, documentation and output labels in English. Update the relevant stage guide in `docs/finding/README.md` or `docs/linking/README.md` when behaviour changes. Keep the stage index in `docs/current-state.md` aligned with both guides.

Incident names follow the rules in `app/finding/clean_incidents.py` and use whole-name YAML aliases. For engagement name comparisons, lowercase the source text and remove whitespace. Match types and column priorities live in `app/finding/match_rows.py`.

Keep the stage-two entry point in `linking.py` and its reader, model decision and Excel writer in `app/linking/`. Compare all engagements found for each incident and return up to three ranked candidates with source evidence. Keep README commands aligned with both entry points. Verify workbook changes using synthetic inputs, and distinguish offline model-response checks from live provider tests.
