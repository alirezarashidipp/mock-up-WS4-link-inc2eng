from .clean_names import clean_name


def clean_suppliers(rows):
    suppliers = []
    for row in rows:
        names = {}
        for column in ("THIRD_PARTY_NORMALISED_NAME", "THIRD_PARTY_NAME"):
            name = clean_name(row[column])
            names[column] = (name, name.replace(" ", ""))
        suppliers.append((row, names))
    return suppliers
