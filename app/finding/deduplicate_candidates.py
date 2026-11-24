MATCH_PRIORITY = {"EXACT": 0, "SUBSTRING": 1, "FUZZY": 2}


def deduplicate_candidates(matches):
    """Keep the strongest row for each pair in first-seen order. The first equal match wins."""
    best_matches = {}
    for incident_key, engagement_key, match_type, row in matches:
        pair = (incident_key, engagement_key)
        priority = MATCH_PRIORITY[match_type]
        if pair in best_matches and best_matches[pair][0] <= priority:
            continue
        best_matches[pair] = (priority, row)
    return [row for _, row in best_matches.values()]
