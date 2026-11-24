from .clean_names import clean_name


def clean_suppliers(rows, search_columns):
    suppliers = []
    for row in rows:
        names = {}
        for column in search_columns:
            name = clean_name(row.get(column))
            if name:
                names[column] = (name, name.replace(" ", ""))
        suppliers.append((row, names))
    return suppliers
