from .read_files import read_table


def read_suppliers(input_dir, fields):
    csv_file = input_dir / "ENG_ALL.csv"
    return read_table(csv_file, [fields["identifier"]], allow_vertical_headers=True,
                      search_columns=fields["search_columns_eng"])
