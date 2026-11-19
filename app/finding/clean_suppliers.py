def clean_suppliers(rows):
    suppliers = []
    for row in rows:
        names = {}
        for column in ("THIRD_PARTY_NORMALISED_NAME", "THIRD_PARTY_NAME"):
            value = row[column]
            text = "" if value is None else str(value)
            names[column] = "".join(text.lower().split())
        suppliers.append((row, names))
    return suppliers
