import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import yaml

from finding import COLUMNS, main, read_columns


def write_table(path, headers, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


class FindingTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.folder = Path(directory.name)
        self.columns_file = COLUMNS
        self.use_columns(read_columns(COLUMNS))
        self.output = self.folder / "candidates.csv"
        self.invalid = self.folder / "candidates_invalid_names.csv"

    def use_columns(self, columns):
        self.incident = columns["incident"]
        self.engagement = columns["engagement"]
        self.candidate = columns["candidate"]
        self.status = columns["invalid_name_report"]["status"]
        self.extra_field = self.engagement["original"] + "_notes"

    def run_finding(self, incidents, engagements):
        write_table(self.folder / "CLASSIFIED_INCIDENTS.csv",
                    [self.incident["identifier"], self.incident["classification"], self.incident["supplier"]], incidents)
        write_table(self.folder / "ENG_ALL.csv",
                    [self.engagement["identifier"], self.engagement["original"], self.engagement["normalised"], self.extra_field],
                    engagements)
        main(self.folder, self.output, columns_file=self.columns_file)
        return read_rows(self.output)

    def test_strongest_method_per_pair_and_first_record_on_ties(self):
        incidents = [
            ("I1", "SUPPLIER", "Microsoft"), ("I2", "SUPPLIER", "Microsoft"),
            ("I1", "SUPPLIER", "Microsoft"),
        ]
        engagements = [
            ("01", "Microsfot", "", "early fuzzy"),
            ("02", "Microsfot", "Microsoft UK", "substring"),
            ("01", "Microsoft UK", "Microsoft Ltd.", "first exact"),
            ("01", "Microsoft", "", "later exact"),
            ("03", "Microsfot", "", "fuzzy"),
            ("04", "Microsoft", "Microsoft", "exact tie across fields"),
            ("05", "Microsoft UK", "Microsoft US", "substring tie across fields"),
        ]
        rows = self.run_finding(incidents, engagements)
        for incident_id in ("I1", "I2"):
            actual = [(row[self.engagement["identifier"]], row[self.candidate["method"]], row[self.candidate["source_value"]],
                       row[self.candidate["source_field"]], row[self.extra_field])
                      for row in rows if row[self.incident["identifier"]] == incident_id]
            self.assertEqual(actual, [
                ("01", "EXACT", "Microsoft Ltd.", self.engagement["normalised"], "first exact"),
                ("02", "SUBSTRING", "Microsoft UK", self.engagement["normalised"], "substring"),
                ("03", "FUZZY", "Microsfot", self.engagement["original"], "fuzzy"),
                ("04", "EXACT", "Microsoft", self.engagement["original"], "exact tie across fields"),
                ("05", "SUBSTRING", "Microsoft US", self.engagement["normalised"], "substring tie across fields"),
            ])

    def test_shared_cleaning_and_incident_only_alias(self):
        incidents = [
            ("I1", "SUPPLIER", "B.T."), ("I2", "SUPPLIER", "North & Star 24 Holdings"),
        ]
        engagements = [
            ("01", "British Telecom", "", ""), ("02", "British Telecommunications Ltd.", "", ""),
            ("03", "btartbox", "BT", ""), ("04", "North-and-Star 24 Solution Ltd.", "", ""),
        ]
        rows = self.run_finding(incidents, engagements)
        actual = [(row[self.incident["supplier"]], row[self.candidate["search_name"]],
                   row[self.engagement["identifier"]], row[self.candidate["method"]]) for row in rows]
        self.assertEqual(actual, [
            ("B.T.", "british telecom", "01", "EXACT"),
            ("B.T.", "british telecom", "02", "SUBSTRING"),
            ("North & Star 24 Holdings", "north star 24", "04", "EXACT"),
        ])
        self.assertEqual(rows[-1][self.candidate["source_value"]], "North-and-Star 24 Solution Ltd.")

    def test_invalid_names_report_and_rerun(self):
        incidents = [
            ("I1", "SUPPLIER", "Holding Solutions Ltd."), ("I2", "SUPPLIER", "  "),
            ("I3", "HSBC", "Solutions"), ("I4", "SUPPLIER", "Unmatched"),
        ]
        self.assertEqual(self.run_finding(incidents, []), [])
        self.assertEqual(read_rows(self.invalid), [
            {self.incident["identifier"]: "I1", self.incident["supplier"]: "Holding Solutions Ltd.",
             self.status: "invalid name"},
            {self.incident["identifier"]: "I2", self.incident["supplier"]: "  ", self.status: "invalid name"},
        ])
        self.run_finding([("I1", "SUPPLIER", "Usable")], [])
        self.assertEqual(read_rows(self.invalid), [])

    def test_all_headers_can_be_renamed(self):
        columns = read_columns(COLUMNS)
        for section, fields in columns.items():
            for role in fields:
                fields[role] = f"{section} {role}"
        self.columns_file = self.folder / "columns.yml"
        self.columns_file.write_text(yaml.safe_dump(columns), encoding="utf-8")
        self.use_columns(columns)

        incidents = [("01", "SUPPLIER", "B.T."), ("02", "SUPPLIER", "Ltd")]
        engagements = [("003", "BT", "British Telecom", "original value")]
        rows = self.run_finding(incidents, engagements)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][self.incident["identifier"]], "01")
        self.assertEqual(rows[0][self.engagement["identifier"]], "003")
        self.assertEqual(rows[0][self.candidate["method"]], "EXACT")
        self.assertEqual(rows[0][self.candidate["search_name"]], "british telecom")
        self.assertEqual(rows[0][self.candidate["source_field"]], self.engagement["normalised"])
        self.assertEqual(rows[0][self.candidate["source_value"]], "British Telecom")
        self.assertEqual(read_rows(self.invalid), [
            {self.incident["identifier"]: "02", self.incident["supplier"]: "Ltd", self.status: "invalid name"},
        ])
