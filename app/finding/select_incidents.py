def select_incidents(rows):
    selected = []
    for row in rows:
        if row["class"] == "SUPPLIER":
            selected.append(row)
    return selected
