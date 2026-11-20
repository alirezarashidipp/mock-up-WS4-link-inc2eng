import csv
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


OUTPUT_COLUMNS = (
    "incident_evidence_citation", "engagement_evidence_citation",
    "incident_evidence_citation_strength", "engagement_evidence_citation_strength",
    "link_rationale", "link_decision", "link_decision_confidence_reason", "link_decision_confidence",
    "strongest_link", "strongest_link_rational",
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
    previous_columns = OUTPUT_COLUMNS[:-2]
    previous_headers = [*headers, *previous_columns]
    legacy_columns = [name.replace("_citation_strength", "__citation_strength") for name in previous_columns]
    legacy_headers = [*headers, *legacy_columns]
    with saved.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        saved_headers = next(reader, None)
        if saved_headers not in (output_headers, previous_headers, legacy_headers):
            raise ValueError(f"{saved.name} has different headers. Use a separate output for this input.")
        rows = list(reader)
    if len(rows) != len(source_rows):
        raise ValueError(f"{saved.name} has a different row count from the candidate workbook.")
    for number, (row, source) in enumerate(zip(rows, source_rows), start=2):
        if len(row) != len(saved_headers) or row[:len(headers)] != source:
            raise ValueError(f"{saved.name} differs from the candidate workbook at row {number}.")
    if saved_headers != output_headers:
        if any(any(row[len(headers):]) for row in rows):
            raise ValueError(f"{saved.name} contains assessments under the previous decision rules. "
                             "Use a separate output CSV to assess this workbook under the current rules.")
        for row in rows:
            row.extend(["", ""])
        save_progress(path, output_headers, rows)
    elif saved == pending:
        pending.replace(path)
    return rows


def unfinished_cases(cases, rows, source_width):
    unfinished = []
    for incident, candidates in cases.values():
        decisions = []
        strongest_count = 0
        for _, row_numbers in candidates.values():
            number = row_numbers[0]
            values = rows[number - 2][source_width:]
            if any(rows[other - 2][source_width:] != values for other in row_numbers[1:]):
                raise ValueError(f"Conflicting saved assessments for the candidate at CSV row {number}.")
            if not any(values):
                continue
            assessment = dict(zip(OUTPUT_COLUMNS, values))
            decision = assessment["link_decision"]
            if decision not in ("LINKED", "POSSIBLY_LINKED", "NOT_LINKED", "INSUFFICIENT_EVIDENCE"):
                raise ValueError(f"Invalid saved decision at CSV row {number}.")
            flag = assessment["strongest_link"]
            reason = assessment["strongest_link_rational"]
            if flag == "YES" and decision == "LINKED" and reason.strip():
                strongest_count += 1
            elif flag or reason:
                raise ValueError(f"Invalid saved strongest link at CSV row {number}.")
            decisions.append(decision)
        if not decisions:
            unfinished.append((incident, candidates))
        elif len(decisions) != len(candidates):
            raise ValueError(f"Partial saved incident {incident['incident_id']}.")
        elif "LINKED" in decisions and strongest_count != 1:
            raise ValueError(f"Invalid strongest link selection for incident {incident['incident_id']}.")
    return unfinished
