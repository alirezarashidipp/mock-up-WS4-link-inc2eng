# Finding evaluator

Double-click **Open Finding.cmd** in this folder on Windows. It starts or reopens the local frontend using the project’s Python environment.

Type a supplier name and press **Enter**, or click **Run Finding**. The form searches `data/input/ENG_ALL.csv` automatically each time and displays the results below the search box. If the file is added while the page is open, press **Enter** again.

**Match summary** shows the engagement ID, original matched value, match type and matched field. **All columns** shows the full Finding row in source order. Results are paginated at 50 rows per page.

The default address is [127.0.0.1:8765](http://127.0.0.1:8765/). With the default server running, opening `index.html` directly also lets you type a name and submit it to that frontend. **Change reference** lets you choose another CSV for the current tab. The alternative default filename `data/input/ALL_ENG.csv` is also recognised.

Finding reads the current column and alias configurations and applies the project's cleaning, matching and deduplication rules. Selected CSV data and search results are processed in memory. The evaluator writes no CSV files.

| Outcome | Result |
| --- | --- |
| MATCHED | One row per retained incident–engagement pair. |
| NO_MATCH | The search name was usable and no engagement matched. |
| INVALID_NAME | Cleaning or alias replacement left an empty search name. |
| SKIPPED | Finding skips a blank supplier name or the whole name Unknown. |

To use a reference stored elsewhere as the default on every search:

```powershell
.\.venv\Scripts\python.exe .\eval_finding\run_finding.py --eng-all "D:\exports\ALL_ENG.csv"
```

Use `--port` to choose a different local port or `--no-browser` to print the address without opening a tab. The service listens on the local computer only.
