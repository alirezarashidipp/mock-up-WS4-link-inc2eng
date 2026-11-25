# Try supplier names with Finding

1. Open `test_input.csv`. Replace the example `Azure` or add more names, one per row under `claasified_supplier_name`. The standard spelling `classified_supplier_name` also works. Quote a name containing a comma, for example `"Acme, Inc."`.
2. From the project root, run the script with the project Python environment.

```powershell
.\.venv\Scripts\python.exe .\eval_finding\run_finding.py
```

The default reference is `data/input/ENG_ALL.csv`. To search a CSV stored elsewhere, supply its path.

```powershell
.\.venv\Scripts\python.exe .\eval_finding\run_finding.py --eng-all "D:\exports\ENG_ALL.csv"
```

3. Open `eval_finding/finding_report.csv`. Each test row gets an ID such as `EVAL-0001`, including repeated names as separate cases. The report retains the input name, the original engagement columns, the standardised search name, the matched field and value, the match method and `finding_status`.

| Finding status | Report rows |
| --- | --- |
| `MATCHED` | One row per matching engagement ID for this test case. |
| `NO_MATCH` | One row with the test name and an empty engagement ID. |
| `INVALID_NAME` | One row when cleaning or alias replacement leaves the test name empty. |

The script calls the project’s `finding.main()` with its configured aliases, search columns, matching rules and deduplication. Finding skips blank names and the whole name `Unknown`. A successful run replaces the previous local report. Temporary inputs and output stay under `eval_finding/`.
