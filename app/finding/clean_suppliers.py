def normalized_name_column(headers):
    for column in ("THIRD_PARTY_NORMALIZED_NAME", "THIRD_PARTY_NORMALISED_NAME"):
        if column in headers:
            return column
    raise ValueError("ENG_ALL is missing THIRD_PARTY_NORMALIZED_NAME (or THIRD_PARTY_NORMALISED_NAME).")


def clean_suppliers(rows, headers):
    normalized_column = normalized_name_column(headers)
    suppliers = []
    for row in rows:
        names = {}
        for column in (normalized_column, "THIRD_PARTY_NAME"):
            value = row[column]
            words = str(value).lower().split() if value is not None else []
            names[column] = "".join(words)
        suppliers.append((row, names))
    return suppliers
