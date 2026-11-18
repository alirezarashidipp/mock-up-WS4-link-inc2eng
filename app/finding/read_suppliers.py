from .match_rows import EXACT_COLUMNS
from .read_files import read_table


def read_suppliers(input_dir):
    csv_file = input_dir / "RAW_SPS_SUPPLIER_DETAIL.csv"
    excel_file = input_dir / "RAW_SPS_SUPPLIER_DETAIL.xlsx"
    files = [path for path in (csv_file, excel_file) if path.is_file()]
    if len(files) != 1:
        raise ValueError(f"Provide one RAW_SPS_SUPPLIER_DETAIL.csv or .xlsx in {input_dir}.")
    return read_table(files[0], ["ENG ID", *EXACT_COLUMNS])
