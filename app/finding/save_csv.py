import csv


def candidate_headers(incident_headers, supplier_headers, fields):
    details = [fields["search_name"], fields["source_field"], fields["method"], fields["source_value"]]
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


def save_candidates(path, incident_headers, supplier_headers, candidates, fields):
    headers = candidate_headers(incident_headers, supplier_headers, fields)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(candidates)


def save_invalid_names(path, invalid_incidents, incident_fields, status_column):
    id_column = incident_fields["identifier"]
    name_column = incident_fields["supplier"]
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow([id_column, name_column, status_column])
        for row in invalid_incidents:
            writer.writerow([row.get(id_column), row[name_column], "invalid name"])
