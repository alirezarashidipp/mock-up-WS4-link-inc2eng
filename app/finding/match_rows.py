from fuzzy_match.algorithims import levenshtein


MIN_FUZZY_LENGTH = 5
MIN_FUZZY_SIMILARITY = 0.72
MATCH_PRIORITY = {"EXACT": 0, "SUBSTRING": 1, "FUZZY": 2}


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
    """Yield each matching column once, using its strongest method."""
    for column in ("THIRD_PARTY_NAME", "THIRD_PARTY_NORMALISED_NAME"):
        _, compact_name = names[column]
        if query == compact_name:
            yield column, "EXACT"

    for column in ("THIRD_PARTY_NORMALISED_NAME", "THIRD_PARTY_NAME"):
        name, compact_name = names[column]
        if not name or query == compact_name:
            continue
        if query in compact_name:
            yield column, "SUBSTRING"
        elif len(query) >= MIN_FUZZY_LENGTH and fuzzy_partial_match(query, name):
            yield column, "FUZZY"


def record_key(row, id_column, row_number):
    value = row.get(id_column)
    if value is None or not str(value).strip():
        # Finding also accepts standalone inputs with missing identifiers.
        return ("row", row_number)
    return str(value)


def find_candidates(incidents, suppliers):
    best_matches = {}
    for incident_number, (incident, name) in enumerate(incidents):
        query = name.replace(" ", "")
        if not query:
            continue
        incident_key = record_key(incident, "incident_id", incident_number)
        for supplier_number, (supplier, names) in enumerate(suppliers):
            for column, match_type in matching_columns(query, names):
                engagement_key = record_key(supplier, "ENGAGEMENT_ID", supplier_number)
                pair = (incident_key, engagement_key)
                priority = MATCH_PRIORITY[match_type]
                if pair in best_matches and best_matches[pair][0] <= priority:
                    continue
                row = list(incident.values())
                row.extend(supplier.values())
                row.extend([name, column, match_type, supplier[column]])
                best_matches[pair] = (priority, row)
    return [row for _, row in best_matches.values()]
