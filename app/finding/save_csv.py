import csv


def candidate_headers(incident_headers, supplier_headers):
    details = ["standardised_supplier_name", "matched_supplier_column", "match_type", "found_name_in_source"]
    headers = list(incident_headers)
    for column in supplier_headers:
        label = column
        if column in incident_headers or column in details:
            label = "ENG." + column
        headers.append(label)
    headers.extend(details)
    if len(set(headers)) != len(headers):
        raise ValueError("The combined output contains conflicting column names.")
    return headers


def save_candidates(path, incident_headers, supplier_headers, candidates):
    headers = candidate_headers(incident_headers, supplier_headers)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(candidates)
