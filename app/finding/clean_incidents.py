SYMBOLS_TO_REMOVE = [
    ";", ",", ":", "؛", "،",
    "(", ")", "[", "]", "{", "}",
    "-", "–", "—", "_",
    "/", "\\", "|",
    '"', "“", "”",
]
WORDS_TO_REMOVE = {
    "the", "and", "a", "an", "on",
    "plc", "limited", "llc", "company", "solutions",
}


def remove_symbols(name):
    for symbol in SYMBOLS_TO_REMOVE:
        name = name.replace(symbol, " ")
    return name


def remove_words(name):
    kept_words = []
    for word in name.split():
        if word not in WORDS_TO_REMOVE:
            kept_words.append(word)
    return " ".join(kept_words)


def clean_name(value):
    if value is None:
        return ""
    name = str(value).lower()
    name = remove_symbols(name)
    return remove_words(name)


def clean_incidents(rows):
    incidents = []
    for row in rows:
        name = clean_name(row["classified_supplier_name"])
        if name:
            incidents.append((row, name))
    return incidents
