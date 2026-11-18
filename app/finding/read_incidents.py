from .read_files import read_table


def read_incidents(input_dir):
    path = input_dir / "CLASSIFIED_INCIDENTS.csv"
    return read_table(path, ["class", "classified_supplier_name"])
