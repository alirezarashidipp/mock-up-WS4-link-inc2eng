# Project instructions

Keep the stage-one entry point in `finding.py` at the project root. Use plain functions under `app/finding/`. In `main()`, show the steps for reading each source, selecting incident rows, cleaning names, applying alias replacements, matching and saving.

Preserve original source values in the candidate workbook. Change supplier exceptions in `config/supplier_aliases.yml`. Keep code, definitions, documentation and output labels in English. Update `docs/current-state.md` when behaviour changes.

The implemented workflow ends at the Excel candidate workbook. Both inputs share the cleaning rules in `app/finding/clean_incidents.py`. Match types and column priorities live in `app/finding/match_rows.py`. Keep the README run instructions aligned with `finding.py`. Check changes with a small pair of synthetic inputs and inspect the resulting workbook.
