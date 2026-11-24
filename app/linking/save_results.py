import csv
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from .read_progress import pending_incidents, read_progress


OUTPUT_COLUMNS = (
    "incident_evidence_citation",
    "engagement_evidence_citation",
    "incident_evidence_citation_strength",
    "engagement_evidence_citation_strength",
    "link_rationale",
    "link_decision",
    "link_decision_confidence_reason",
    "link_decision_confidence",
)


def assessment_values(assessment):
    values = []
    for name in OUTPUT_COLUMNS:
        value = assessment[name]
        if name in ("incident_evidence_citation", "engagement_evidence_citation"):
            value = "\n".join(value) or "[]"
        values.append("" if value is None else value)
    return values


def apply_assessments(rows, candidate_records, assessments, source_width):
    """Write each numbered assessment onto all the source rows it represents."""
    for number, (_, row_numbers) in enumerate(candidate_records, start=1):
        values = assessment_values(assessments[number])
        for row_number in row_numbers:
            rows[row_number - 2][source_width:] = values


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
        # If another program has locked the CSV, the completed snapshot is available on restart.
        pending.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def load_progress(path, headers, source_rows):
    """Open or initialise an output snapshot for callers using the CSV helpers directly."""
    rows, needs_snapshot = read_progress(path, headers, source_rows, OUTPUT_COLUMNS)
    if needs_snapshot:
        save_progress(path, [*headers, *OUTPUT_COLUMNS], rows)
    return rows


def unfinished_cases(cases, rows, source_width):
    return pending_incidents(cases, rows, source_width, OUTPUT_COLUMNS)
