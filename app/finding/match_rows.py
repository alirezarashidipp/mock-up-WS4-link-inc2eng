from fuzzy_match.algorithims import levenshtein


MAX_SHORT_NAME_LENGTH = 4
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
            if len(query) > MAX_SHORT_NAME_LENGTH or query in name.split():
                yield column, "SUBSTRING"
        elif len(query) >= MIN_FUZZY_LENGTH and fuzzy_partial_match(query, name):
            yield column, "FUZZY"


def record_key(row, id_column, row_number):
    value = row.get(id_column)
    if value is None or not str(value).strip():
        # Finding also accepts standalone inputs with missing identifiers.
        return ("row", row_number)
    return str(value)


def matching_engagement_fields(query, suppliers, engagement_id_column):
    if not query:
        return
    for supplier_number, (supplier, names) in enumerate(suppliers):
        for column, method in matching_columns(query, names):
            engagement_key = record_key(supplier, engagement_id_column, supplier_number)
            yield engagement_key, supplier, column, method


def find_matches(incidents, suppliers, incident_id_column, engagement_id_column, supplier_headers=None):
    """Yield field matches. Supplying engagement headers includes the status and incident-only rows."""
    for incident_number, (incident, name) in enumerate(incidents):
        query = name.replace(" ", "")
        incident_key = record_key(incident, incident_id_column, incident_number)
        matched = False
        fields = matching_engagement_fields(query, suppliers, engagement_id_column)
        for engagement_key, supplier, column, method in fields:
            matched = True
            row = [*incident.values(), *supplier.values(), name, column, method, supplier[column]]
            if supplier_headers is not None:
                row.append("MATCHED")
            yield incident_key, engagement_key, method, row
        if not matched and supplier_headers is not None:
            status = "NO_MATCH" if name else "INVALID_NAME"
            empty_engagement = [""] * len(supplier_headers)
            row = [*incident.values(), *empty_engagement, name, "", "", "", status]
            yield incident_key, None, status, row
