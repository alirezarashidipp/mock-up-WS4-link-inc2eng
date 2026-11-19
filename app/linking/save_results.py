import csv
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


OUTPUT_COLUMNS = (
    "incident_evidence_citation", "engagement_evidence_citation",
    "incident_evidence_citation_strength", "engagement_evidence_citation_strength",
    "link_rationale", "link_decision", "link_decision_confidence_reason", "link_decision_confidence",
)


def assessment_values(assessment):
    values = []
    for name in OUTPUT_COLUMNS:
        value = assessment[name]
        if name in ("incident_evidence_citation", "engagement_evidence_citation"):
            value = "\n".join(value) or "[]"
        values.append("" if value is None else value)
    return values


def save_progress(path, headers, rows):
    pending = path.with_name(path.name + ".pending")
    stream = NamedTemporaryFile(dir=path.parent, mode="w", encoding="utf-8-sig", newline="",
                                suffix=".tmp", delete=False)
    temporary = Path(stream.name)
    try:
        with stream:
            writer = csv.writer(stream)
            writer.writerow(headers)
            writer.writerows(rows)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(pending)
        # If Excel has locked the CSV, the completed snapshot is available on restart.
        pending.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def load_progress(path, headers, source_rows):
    pending = path.with_name(path.name + ".pending")
    saved = pending if pending.exists() else path
    output_headers = [*headers, *OUTPUT_COLUMNS]
    if not saved.exists():
        rows = [row + [""] * len(OUTPUT_COLUMNS) for row in source_rows]
        save_progress(path, output_headers, rows)
        return rows

    csv.field_size_limit(max(csv.field_size_limit(), 2**31 - 1))
    legacy_columns = [column.replace("_citation_strength", "__citation_strength") for column in OUTPUT_COLUMNS]
    legacy_headers = [*headers, *legacy_columns]
    with saved.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        saved_headers = next(reader, None)
        if saved_headers not in (output_headers, legacy_headers):
            raise ValueError(f"{saved.name} has different headers. Use a separate output for this input.")
        rows = list(reader)
    if len(rows) != len(source_rows):
        raise ValueError(f"{saved.name} has a different row count from the candidate workbook.")
    for number, (row, source) in enumerate(zip(rows, source_rows), start=2):
        if len(row) != len(output_headers) or row[:len(headers)] != source:
            raise ValueError(f"{saved.name} differs from the candidate workbook at row {number}.")
    if saved_headers == legacy_headers:
        save_progress(path, output_headers, rows)
    elif saved == pending:
        pending.replace(path)
    return rows


def unfinished_cases(cases, rows, source_width):
    decision_column = source_width + OUTPUT_COLUMNS.index("link_decision")
    unfinished = []
    for incident, candidates in cases.values():
        decisions = set()
        for _, row_numbers in candidates.values():
            for number in row_numbers:
                row = rows[number - 2]
                decision = row[decision_column]
                if decision not in ("", "STRONGEST_LINKED", "LINKED", "POSSIBLY_LINKED", "NOT_LINKED") or (not decision and any(row[source_width:])):
                    raise ValueError(f"Invalid saved assessment at CSV row {number}.")
                decisions.add(decision)
        if "" in decisions:
            if len(decisions) > 1:
                raise ValueError(f"Partial saved incident {incident['incident_id']}.")
            unfinished.append((incident, candidates))
    return unfinished
