from .match_rows import EXACT_COLUMNS


def clean_name(value):
    if value is None:
        return ""
    name = str(value).lower()
    for symbol in [";", "(", ")"]:
        name = name.replace(symbol, " ")
    words = name.split()
    return " ".join(words)


def clean_aliases(entries):
    aliases = {}
    for original, replacement in entries.items():
        name = clean_name(original)
        aliases[name] = clean_name(replacement)
    return aliases


def clean_incidents(rows, aliases):
    """Keep supplier incidents and pair each source row with its search name."""
    incidents = []
    for row in rows:
        if row["class"] != "SUPPLIER":
            continue
        name = clean_name(row["classified_supplier_name"])
        if name:
            search_name = aliases.get(name, name)
            incidents.append((row, search_name))
    return incidents


def clean_suppliers(rows, aliases):
    suppliers = []
    for row in rows:
        names = {}
        for column in EXACT_COLUMNS:
            name = clean_name(row[column])
            names[column] = aliases.get(name, name)
        suppliers.append((row, names))
    return suppliers
