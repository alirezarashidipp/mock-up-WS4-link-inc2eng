from .clean_names import clean_name


def clean_suppliers(rows, fields):
    suppliers = []
    for row in rows:
        names = {}
        for column in (fields["normalised"], fields["original"]):
            name = clean_name(row[column])
            names[column] = (name, name.replace(" ", ""))
        suppliers.append((row, names))
    return suppliers
