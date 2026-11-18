from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell


def save_candidates(path, incident_headers, supplier_headers, candidates):
    details = ["standardised_supplier_name", "matched_supplier_column", "match_type"]
    headers = list(incident_headers)
    for column in supplier_headers:
        label = column
        if column in incident_headers or column in details:
            label = "ENG." + column
        headers.append(label)
    headers.extend(details)
    if len(set(headers)) != len(headers):
        raise ValueError("The combined output contains conflicting column names.")

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
