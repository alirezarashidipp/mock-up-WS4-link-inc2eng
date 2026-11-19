from pathlib import Path
from tempfile import NamedTemporaryFile

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter


DECISION_COLUMNS = [
    "incident_id",
    "link_decision",
    "selected_engagement_id",
    "confidence",
    "decision_reason",
]


def save_results(path, results):
    path = Path(path)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Linking decisions"

    headers = DECISION_COLUMNS.copy()
    for rank in range(1, 4):
        headers.append(f"candidate_{rank}_engagement_id")
        headers.append(f"candidate_{rank}_rationale")
    sheet.append(headers)

    for column, header in enumerate(headers, start=1):
        sheet.cell(1, column).font = Font(bold=True)
        width = len(header) + 6
        if header.endswith(("reason", "rationale")):
            width = 65
        sheet.column_dimensions[get_column_letter(column)].width = width

    for row_number, result in enumerate(results, start=2):
        values = [result[column] for column in DECISION_COLUMNS]
        candidates = result["candidates"]
        if len(candidates) > 3:
            raise ValueError("An incident can have at most three ranked candidates.")
        for candidate in candidates:
            values.append(candidate["engagement_id"])
            values.append(candidate["rationale"])

        for column, value in enumerate(values, start=1):
            if isinstance(value, str) and len(value) > 32767:
                raise ValueError(f"{headers[column - 1]} exceeds the Excel cell text limit.")
            cell = sheet.cell(row_number, column, value)
            if isinstance(value, str):
                cell.data_type = "s"
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    sheet.freeze_panes = "B2"
    sheet.auto_filter.ref = sheet.dimensions
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, suffix=".xlsx", delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        workbook.save(temporary_path)
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)
