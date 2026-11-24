from .read_files import read_table


def read_incidents(input_dir, fields):
    path = input_dir / "CLASSIFIED_INCIDENTS.csv"
    return read_table(path, [fields["classification"], fields["supplier"]])
