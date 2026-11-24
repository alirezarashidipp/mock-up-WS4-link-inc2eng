from .read_files import read_table


def read_suppliers(input_dir):
    csv_file = input_dir / "ENG_ALL.csv"
    required_columns = ["ENGAGEMENT_ID", "THIRD_PARTY_NAME", "THIRD_PARTY_NORMALISED_NAME"]
    return read_table(csv_file, required_columns, allow_vertical_headers=True)
