EXACT_COLUMNS = [
    "SUPPLIER_TRADING_NAME",
    "SUPPLIER_NORMALISED_BUSINESS_NAME",
    "SUPPLIER_ALTERNATE_NAME",
    "SUPPLIER_NAME",
    "SUPPLIER_DNB_MATCHED_BUSINESS_NAME",
]
PARTIAL_COLUMNS = [
    "SUPPLIER_ALTERNATE_NAME",
    "SUPPLIER_NAME",
    "SUPPLIER_NORMALISED_BUSINESS_NAME",
    "SUPPLIER_DNB_MATCHED_BUSINESS_NAME",
    "SUPPLIER_TRADING_NAME",
]


def match_name(name, supplier_names):
    for column in EXACT_COLUMNS:
        if name == supplier_names[column]:
            return column, "EXACT"
    for column in PARTIAL_COLUMNS:
        if name in supplier_names[column]:
            return column, "PARTIAL"
    return None


def find_candidates(incidents, suppliers):
    candidates = []
    for incident, name in incidents:
        if not name:
            continue
        for supplier, supplier_names in suppliers:
            match = match_name(name, supplier_names)
            if match is None:
                continue
            column, match_type = match
            row = list(incident.values())
            row.extend(supplier.values())
            row.extend([name, column, match_type])
            candidates.append(row)
    return candidates
