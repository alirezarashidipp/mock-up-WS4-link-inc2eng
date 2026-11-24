from .clean_names import clean_name


def clean_incidents(rows, supplier_column):
    incidents = []
    for row in rows:
        name = clean_name(row[supplier_column])
        incidents.append((row, name))
    return incidents
