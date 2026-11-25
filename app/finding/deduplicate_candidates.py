ROW_PRIORITY = {"EXACT": 0, "SUBSTRING": 1, "FUZZY": 2, "NO_MATCH": 3, "INVALID_NAME": 4}


def deduplicate_candidates(matches):
    """Keep the strongest row per pair and one status row for each incident with no candidate."""
    best_matches = {}
    matched_incidents = set()
    for incident_key, engagement_key, result, row in matches:
        if engagement_key is not None:
            matched_incidents.add(incident_key)
        pair = (incident_key, engagement_key)
        priority = ROW_PRIORITY[result]
        if pair in best_matches and best_matches[pair][0] <= priority:
            continue
        best_matches[pair] = (priority, row)

    rows = []
    for (incident_key, engagement_key), (_, row) in best_matches.items():
        if engagement_key is None and incident_key in matched_incidents:
            continue
        rows.append(row)
    return rows
