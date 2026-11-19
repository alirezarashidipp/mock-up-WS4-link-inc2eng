from fuzzy_match.algorithims import levenshtein


MIN_FUZZY_LENGTH = 5
MIN_FUZZY_SIMILARITY = 0.72


def fuzzy_partial_match(query, value):
    """Compare the query with adjacent whole words from the source field."""
    words = str(value).lower().split()
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


def match_name(query, names, source_row):
    if query == names["THIRD_PARTY_NAME"]:
        return "THIRD_PARTY_NAME", "EXACT"
    for column, value in names.items():
        if query == value:
            return column, "EXACT"

    # The normalized field comes first in both partial passes.
    for column, value in names.items():
        if query in value:
            return column, "PARTIAL"

    if len(query) >= MIN_FUZZY_LENGTH:
        for column, value in names.items():
            if value and fuzzy_partial_match(query, source_row[column]):
                return column, "PARTIAL"
    return None


def find_candidates(incidents, suppliers):
    candidates = []
    for incident, name in incidents:
        query = "".join(name.split())
        if not query:
            continue
        for supplier, supplier_names in suppliers:
            match = match_name(query, supplier_names, supplier)
            if match is None:
                continue
            column, match_type = match
            row = list(incident.values())
            row.extend(supplier.values())
            row.extend([name, column, match_type])
            candidates.append(row)
    return candidates
