import csv

import yaml
from openpyxl import load_workbook

from .match_rows import EXACT_COLUMNS


def read_incidents(input_dir):
    path = input_dir / "CLASSIFIED_INCIDENTS.csv"
    return read_table(path, ["class", "classified_supplier_name"])


def read_suppliers(input_dir):
    csv_file = input_dir / "RAW_SPS_SUPPLIER_DETAIL.csv"
    excel_file = input_dir / "RAW_SPS_SUPPLIER_DETAIL.xlsx"
    files = [path for path in (csv_file, excel_file) if path.is_file()]
    if len(files) != 1:
        raise ValueError(f"Provide one RAW_SPS_SUPPLIER_DETAIL.csv or .xlsx in {input_dir}.")
    return read_table(files[0], ["ENG ID", *EXACT_COLUMNS])


def read_aliases(path):
    with path.open(encoding="utf-8-sig") as stream:
        return yaml.safe_load(stream) or {}


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
