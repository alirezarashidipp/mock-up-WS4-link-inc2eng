from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell


from .save_csv import candidate_headers


def save_candidates(path, incident_headers, supplier_headers, candidates):
    headers = candidate_headers(incident_headers, supplier_headers)
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet("Engagement candidates")
    sheet.freeze_panes = "A2"
    sheet.append(headers)
    for row in candidates:
        cells = []
        for value in row:
            cell = WriteOnlyCell(sheet, value=value)
            if isinstance(value, str):
                cell.data_type = "s"
            cells.append(cell)
        sheet.append(cells)
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)
