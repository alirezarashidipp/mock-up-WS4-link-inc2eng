import csv

from openpyxl import load_workbook


def read_table(path, required_columns):
    if path.suffix == ".xlsx":
        workbook = load_workbook(path, read_only=True, data_only=True)
        try:
            values = list(workbook.active.values)
        finally:
            workbook.close()
    else:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            values = list(csv.reader(stream))

    if not values:
        raise ValueError(f"{path.name} is empty.")
    headers = list(values[0])
    if not all(headers) or len(set(headers)) != len(headers):
        raise ValueError(f"{path.name} contains blank or duplicate column names.")
    for column in required_columns:
        if column not in headers:
            raise ValueError(f"{path.name} is missing column {column}.")

    rows = []
    for number, values_row in enumerate(values[1:], start=2):
        if not any(value is not None and value != "" for value in values_row):
            continue
        if len(values_row) != len(headers):
            raise ValueError(f"{path.name} row {number} has the wrong number of fields.")
        rows.append(dict(zip(headers, values_row)))
    return headers, rows
