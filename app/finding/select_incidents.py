def select_incidents(rows, classification_column, supplier_column):
    selected = []
    for row in rows:
        if row[classification_column] != "SUPPLIER":
            continue
        supplier_name = (row[supplier_column] or "").strip()
        if supplier_name and supplier_name.casefold() != "unknown":
            selected.append(row)
    return selected
