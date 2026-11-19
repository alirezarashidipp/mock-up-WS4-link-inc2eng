from .read_files import read_table


def read_suppliers(input_dir):
    csv_file = input_dir / "ENG_ALL.csv"
    excel_file = input_dir / "ENG_ALL.xlsx"
    files = [path for path in (csv_file, excel_file) if path.is_file()]
    if len(files) != 1:
        raise ValueError(f"Provide one ENG_ALL.csv or ENG_ALL.xlsx in {input_dir}.")
    required_columns = ["ENGAGEMENT_ID", "THIRD_PARTY_NAME", "THIRD_PARTY_NORMALISED_NAME"]
    return read_table(files[0], required_columns, allow_vertical_headers=True)
