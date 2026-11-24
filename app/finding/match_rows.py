from fuzzy_match.algorithims import levenshtein


MIN_FUZZY_LENGTH = 5
MIN_FUZZY_SIMILARITY = 0.72


def fuzzy_partial_match(query, value):
    """Compare the compact query with adjacent words in a cleaned reference name."""
    words = value.split()
    for start in range(len(words)):
        candidate = ""
        for end in range(start, len(words)):
            candidate += words[end]
            if len(candidate) * MIN_FUZZY_SIMILARITY > len(query):
                break
            if len(query) * MIN_FUZZY_SIMILARITY > len(candidate):
                continue
            if levenshtein(query, candidate) >= MIN_FUZZY_SIMILARITY:
                return True
    return False


def matching_columns(query, names):
    """Yield each matching field in configured order with its strongest method."""
    for column, (name, compact_name) in names.items():
        if query == compact_name:
            yield column, "EXACT"
        elif query in compact_name:
            yield column, "SUBSTRING"
        elif len(query) >= MIN_FUZZY_LENGTH and fuzzy_partial_match(query, name):
            yield column, "FUZZY"


def record_key(row, id_column, row_number):
    value = row.get(id_column)
    if value is None or not str(value).strip():
        # Finding also accepts standalone inputs with missing identifiers.
        return ("row", row_number)
    return str(value)


def find_matches(incidents, suppliers, incident_id_column, engagement_id_column):
    """Yield every matching field with its incident key, engagement key, method and source row."""
    for incident_number, (incident, name) in enumerate(incidents):
        query = name.replace(" ", "")
        if not query:
            continue
        incident_key = record_key(incident, incident_id_column, incident_number)
        for supplier_number, (supplier, names) in enumerate(suppliers):
            for column, match_type in matching_columns(query, names):
                engagement_key = record_key(supplier, engagement_id_column, supplier_number)
                row = list(incident.values())
                row.extend(supplier.values())
                row.extend([name, column, match_type, supplier[column]])
                yield incident_key, engagement_key, match_type, row
