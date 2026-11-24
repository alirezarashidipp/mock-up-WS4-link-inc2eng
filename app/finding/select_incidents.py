def select_incidents(rows, classification_column):
    selected = []
    for row in rows:
        if row[classification_column] == "SUPPLIER":
            selected.append(row)
    return selected
