def select_incidents(rows):
    selected = []
    for row in rows:
        if row["class"] != "SUPPLIER":
            continue
        supplier_name = row["classified_supplier_name"]
        if supplier_name and supplier_name.strip():
            selected.append(row)
    return selected
