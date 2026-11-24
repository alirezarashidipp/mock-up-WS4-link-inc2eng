from .read_files import read_table


def read_suppliers(input_dir, fields):
    csv_file = input_dir / "ENG_ALL.csv"
    required_columns = [fields["identifier"], fields["original"], fields["normalised"]]
    return read_table(csv_file, required_columns, allow_vertical_headers=True)
