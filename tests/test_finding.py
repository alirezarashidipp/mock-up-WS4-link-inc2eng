import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from finding import main


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
        self.output = self.folder / "candidates.csv"
        self.invalid = self.folder / "candidates_invalid_names.csv"

    def run_finding(self, incidents, engagements):
        write_table(self.folder / "CLASSIFIED_INCIDENTS.csv",
                    ["incident_id", "class", "classified_supplier_name"], incidents)
        write_table(self.folder / "ENG_ALL.csv",
                    ["ENGAGEMENT_ID", "THIRD_PARTY_NAME", "THIRD_PARTY_NORMALISED_NAME", "service"],
                    engagements)
        main(self.folder, self.output)
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
            actual = [(row["ENGAGEMENT_ID"], row["match_type"], row["found_name_in_source"],
                       row["matched_supplier_column"], row["service"])
                      for row in rows if row["incident_id"] == incident_id]
            self.assertEqual(actual, [
                ("01", "EXACT", "Microsoft Ltd.", "THIRD_PARTY_NORMALISED_NAME", "first exact"),
                ("02", "SUBSTRING", "Microsoft UK", "THIRD_PARTY_NORMALISED_NAME", "substring"),
                ("03", "FUZZY", "Microsfot", "THIRD_PARTY_NAME", "fuzzy"),
                ("04", "EXACT", "Microsoft", "THIRD_PARTY_NAME", "exact tie across fields"),
                ("05", "SUBSTRING", "Microsoft US", "THIRD_PARTY_NORMALISED_NAME", "substring tie across fields"),
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
        actual = [(row["classified_supplier_name"], row["standardised_supplier_name"],
                   row["ENGAGEMENT_ID"], row["match_type"]) for row in rows]
        self.assertEqual(actual, [
            ("B.T.", "british telecom", "01", "EXACT"),
            ("B.T.", "british telecom", "02", "SUBSTRING"),
            ("North & Star 24 Holdings", "north star 24", "04", "EXACT"),
        ])
        self.assertEqual(rows[-1]["found_name_in_source"], "North-and-Star 24 Solution Ltd.")

    def test_invalid_names_report_and_rerun(self):
        incidents = [
            ("I1", "SUPPLIER", "Holding Solutions Ltd."), ("I2", "SUPPLIER", "  "),
            ("I3", "HSBC", "Solutions"), ("I4", "SUPPLIER", "Unmatched"),
        ]
        self.assertEqual(self.run_finding(incidents, []), [])
        self.assertEqual(read_rows(self.invalid), [
            {"incident_id": "I1", "classified_supplier_name": "Holding Solutions Ltd.",
             "finding_status": "invalid name"},
            {"incident_id": "I2", "classified_supplier_name": "  ", "finding_status": "invalid name"},
        ])
        self.run_finding([("I1", "SUPPLIER", "Usable")], [])
        self.assertEqual(read_rows(self.invalid), [])
