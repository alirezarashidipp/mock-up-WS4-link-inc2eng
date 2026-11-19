from pathlib import Path
from tempfile import NamedTemporaryFile

from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter


OUTPUT_COLUMNS = (
    "incident_evidence", "engagement_evidence", "incident_evidence_strength", "link_rationale",
    "link_decision", "linked_strength", "linked_strength_reason", "llm_confidence",
)


def append_headers(sheet, headers):
    if any(name in headers for name in OUTPUT_COLUMNS):
        raise ValueError("The candidate sheet already contains a linking output column.")
    first_column = len(headers) + 1
    for column, name in enumerate(OUTPUT_COLUMNS, start=first_column):
        sheet.cell(1, column, name).font = Font(bold=True)
        sheet.column_dimensions[get_column_letter(column)].width = 60 if name in (
            "incident_evidence", "engagement_evidence", "link_rationale", "linked_strength_reason"
        ) else len(name) + 6
    return first_column


def write_assessment(sheet, row_numbers, first_column, assessment):
    for column, name in enumerate(OUTPUT_COLUMNS, start=first_column):
        value = assessment[name]
        if name in ("incident_evidence", "engagement_evidence"):
            value = "\n".join(value) or "[]"
        if value is None:
            continue
        if len(value) > 32767:
            raise ValueError(f"{name} exceeds the Excel cell text limit.")
        for row in row_numbers:
            cell = sheet.cell(row, column, value)
            cell.data_type = "s"
            cell.alignment = Alignment(vertical="top", wrap_text=True)


def save_results(workbook, path):
    path = Path(path)
    workbook.active.auto_filter.ref = workbook.active.dimensions
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, suffix=".xlsx", delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        workbook.save(temporary_path)
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)
