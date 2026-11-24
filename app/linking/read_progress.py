import csv
from typing import get_args

from .schema import LinkDecision


def read_progress(path, headers, source_rows, output_columns):
    """Return the rows and whether they need a new or recovered output snapshot."""
    # A blank CSV line needs an empty cell for each source column in the output.
    source_rows = [row or [""] * len(headers) for row in source_rows]
    pending = path.with_name(path.name + ".pending")
    saved = pending if pending.exists() else path
    if not saved.exists():
        rows = [row + [""] * len(output_columns) for row in source_rows]
        return rows, True

    rows = read_saved_rows(saved, headers, source_rows, output_columns)
    return rows, saved == pending


def read_saved_rows(path, source_headers, source_rows, output_columns):
    csv.field_size_limit(max(csv.field_size_limit(), 2**31 - 1))
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        headers = next(reader, None)
        if headers != source_headers + list(output_columns):
            raise ValueError(f"{path.name} has different headers. Use a separate output for this input.")
        rows = list(reader)

    if len(rows) != len(source_rows):
        raise ValueError(f"{path.name} has a different row count from the candidate CSV.")
    source_width = len(source_headers)
    for number, (row, source) in enumerate(zip(rows, source_rows), start=2):
        if len(row) != len(headers) or row[:source_width] != source:
            raise ValueError(f"{path.name} differs from the candidate CSV at row {number}.")
    return rows


def saved_candidate_state(rows, row_numbers, source_width, output_columns):
    first_number = row_numbers[0]
    values = rows[first_number - 2][source_width:]
    for number in row_numbers[1:]:
        if rows[number - 2][source_width:] != values:
            raise ValueError(f"Conflicting saved assessments for the candidate at CSV row {first_number}.")
    if not any(values):
        return "pending"

    assessment = dict(zip(output_columns, values))
    if assessment["link_decision"] not in get_args(LinkDecision):
        raise ValueError(f"Invalid saved decision at CSV row {first_number}.")
    if "" in values:
        raise ValueError(f"Incomplete saved assessment at CSV row {first_number}.")
    return "complete"


def pending_incidents(cases, rows, source_width, output_columns):
    unfinished = []
    for incident, candidates in cases.values():
        states = set()
        for _, row_numbers in candidates.values():
            state = saved_candidate_state(rows, row_numbers, source_width, output_columns)
            states.add(state)
        if len(states) > 1:
            raise ValueError(f"Partial saved incident {incident['incident_id']}.")
        if "complete" not in states:
            unfinished.append((incident, candidates))
    return unfinished
