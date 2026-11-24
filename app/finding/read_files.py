import csv
from itertools import zip_longest


def missing_column_message(headers, required_columns, search_columns):
    for column in required_columns:
        if column not in headers:
            return f"is missing column {column}."
    if search_columns and not any(column in headers for column in search_columns):
        return f"requires at least one configured search column ({', '.join(search_columns)})."
    return ""


def read_table(path, required_columns, allow_vertical_headers=False, search_columns=()):
    if path.suffix.lower() != ".csv":
        raise ValueError(f"Expected a CSV input, got {path.name}.")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        values = list(csv.reader(stream))

    if not values:
        raise ValueError(f"{path.name} is empty.")
    missing = missing_column_message(values[0], required_columns, search_columns)
    if allow_vertical_headers and missing:
        field_rows = [row for row in values if any(value not in (None, "") for value in row)]
        first_column = [row[0] for row in field_rows]
        if not missing_column_message(first_column, required_columns, search_columns):
            values = list(zip_longest(*field_rows, fillvalue=None))
            missing = ""
    headers = list(values[0])
    if not all(headers) or len(set(headers)) != len(headers):
        raise ValueError(f"{path.name} contains blank or duplicate column names.")
    if missing:
        raise ValueError(f"{path.name} {missing}")

    rows = []
    for number, values_row in enumerate(values[1:], start=2):
        if not any(value is not None and value != "" for value in values_row):
            continue
        if len(values_row) != len(headers):
            raise ValueError(f"{path.name} row {number} has the wrong number of fields.")
        rows.append(dict(zip(headers, values_row)))
    return headers, rows
