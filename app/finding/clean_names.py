STOP_WORDS = {
    "a", "an", "and", "of", "on", "the",
    "holding", "holdings", "llm", "partners", "solution", "solutions",
}

LEGAL_SUFFIXES = {
    "company", "corp", "corporation", "inc", "incorporated",
    "limited", "llc", "llp", "ltd", "plc",
}

SPECIAL_CHARACTERS = [
    ";", ",", ":", "؛", "،",
    "(", ")", "[", "]", "{", "}",
    "-", "–", "—", "_",
    "/", "\\", "|",
    '"', "“", "”",
]


def remove_symbols(name):
    name = name.replace(".", "").replace("&", " and ")
    for symbol in SPECIAL_CHARACTERS:
        name = name.replace(symbol, " ")
    return name


def remove_words(name):
    kept_words = []
    for word in name.split():
        if word in STOP_WORDS or word in LEGAL_SUFFIXES:
            continue
        kept_words.append(word)
    return " ".join(kept_words)


def clean_name(value):
    """Clean a supplier name from either source and keep word boundaries."""
    if value is None:
        return ""
    name = str(value).lower()
    name = remove_symbols(name)
    return remove_words(name)


def clean_incidents(rows):
    incidents = []
    for row in rows:
        name = clean_name(row["classified_supplier_name"])
        incidents.append((row, name))
    return incidents
