from .clean_incidents import clean_name
from .match_rows import EXACT_COLUMNS


def clean_suppliers(rows):
    suppliers = []
    for row in rows:
        names = {}
        for column in EXACT_COLUMNS:
            name = clean_name(row[column])
            names[column] = name
        suppliers.append((row, names))
    return suppliers
