"""Search ENG_ALL for the supplier names in test_input.csv using the project's Finding stage."""

import sys

# Import the project read-only, including when this script is launched without -B.
sys.dont_write_bytecode = True

import argparse
import csv
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory


EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL_DIR.parent))
import finding


def write_test_incidents(names_file, incidents_file, incident_fields):
    """Give each input name its own incident ID and map it to the configured supplier field."""
    with names_file.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source, strict=True)
        header = next(reader, [])
        if header not in (["claasified_supplier_name"], ["classified_supplier_name"]):
            raise ValueError(f"{names_file.name} must have one column named claasified_supplier_name or classified_supplier_name.")

        with incidents_file.open("w", encoding="utf-8-sig", newline="") as target:
            writer = csv.writer(target)
            writer.writerow([incident_fields["identifier"], incident_fields["classification"], incident_fields["supplier"]])
            for number, row in enumerate(reader, start=1):
                if not row:
                    continue
                if len(row) != 1:
                    raise ValueError(f"{names_file.name}, line {reader.line_num}: expected one supplier name. Quote names containing commas.")
                writer.writerow([f"EVAL-{number:04d}", "SUPPLIER", row[0]])


def run_evaluation(engagement_file):
    engagement_file = Path(engagement_file).resolve()
    report = EVAL_DIR / "finding_report.csv"
    if not engagement_file.is_file():
        raise FileNotFoundError(f"Engagement CSV not found at {engagement_file}. Use --eng-all to specify its location.")
    if engagement_file.suffix.lower() != ".csv" or engagement_file == report.resolve():
        raise ValueError("Choose an engagement CSV different from finding_report.csv.")

    incident_fields = finding.read_columns(finding.COLUMNS)["incident"]
    with TemporaryDirectory(prefix=".finding-", dir=EVAL_DIR) as directory:
        work = Path(directory)
        write_test_incidents(EVAL_DIR / "test_input.csv", work / "CLASSIFIED_INCIDENTS.csv", incident_fields)
        # Finding reads both input filenames from one directory. Link the reference, or copy it on Windows
        # when creating a symbolic link is unavailable.
        reference = work / "ENG_ALL.csv"
        try:
            reference.symlink_to(engagement_file)
        except OSError:
            copyfile(engagement_file, reference)

        completed_report = work / report.name
        print(f"Searching {engagement_file}")
        finding.main(input_dir=work, output_file=completed_report)
        completed_report.replace(report)
    print(f"Report: {report}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eng-all", type=Path, default=finding.INPUT / "ENG_ALL.csv",
                        help="Engagement CSV to search (default: data/input/ENG_ALL.csv in the project).")
    args = parser.parse_args()
    try:
        run_evaluation(args.eng_all)
    except (OSError, ValueError, csv.Error) as error:
        sys.exit(str(error))
