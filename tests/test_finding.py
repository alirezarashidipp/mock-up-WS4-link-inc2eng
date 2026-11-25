import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import yaml

from app.finding.clean_suppliers import clean_suppliers
from app.finding.match_rows import find_matches
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
        self.columns_file = self.folder / "columns.yml"
        self.extra_field = "source note"
        columns = read_columns(COLUMNS)
        columns["engagement"]["search_columns_eng"] = ["name A", "name B"]
        self.use_columns(columns)
        self.output = self.folder / "output" / "engagement_candidates.csv"

    def use_columns(self, columns):
        self.columns_file.write_text(yaml.safe_dump(columns), encoding="utf-8")
        self.incident = columns["incident"]
        self.engagement = columns["engagement"]
        self.candidate = columns["candidate"]
        self.status = columns["candidate"]["status"]
        self.search_fields = self.engagement["search_columns_eng"]

    def run_finding(self, incidents, engagements, source_fields=None):
        if source_fields is None:
            source_fields = [*self.search_fields, self.extra_field]
        write_table(self.folder / "CLASSIFIED_INCIDENTS.csv",
                    [self.incident["identifier"], self.incident["classification"], self.incident["supplier"]], incidents)
        write_table(self.folder / "ENG_ALL.csv",
                    [self.engagement["identifier"], *source_fields],
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
                ("01", "EXACT", "Microsoft Ltd.", self.search_fields[1], "first exact"),
                ("02", "SUBSTRING", "Microsoft UK", self.search_fields[1], "substring"),
                ("03", "FUZZY", "Microsfot", self.search_fields[0], "fuzzy"),
                ("04", "EXACT", "Microsoft", self.search_fields[0], "exact tie across fields"),
                ("05", "SUBSTRING", "Microsoft UK", self.search_fields[0], "substring tie across fields"),
            ])

    def test_short_substring_requires_a_whole_word_in_the_matching_field(self):
        incidents = [("I1", "SUPPLIER", "ICE"), ("I2", "SUPPLIER", "INE")]
        engagements = [
            ("01", "ICE Ltd.", "", ""),
            ("02", "Office Supplies", "ICE Data Services", ""),
            ("03", "Basic East", "ICEGroup", ""),
            ("04", "Online", "UK-INE", ""),
            ("05", "Office Supplies", "Engineering", ""),
        ]
        rows = self.run_finding(incidents, engagements)
        actual = [(row[self.incident["supplier"]], row[self.engagement["identifier"]],
                   row[self.candidate["method"]], row[self.candidate["source_value"]]) for row in rows]
        self.assertEqual(actual, [
            ("ICE", "01", "EXACT", "ICE Ltd."),
            ("ICE", "02", "SUBSTRING", "ICE Data Services"),
            ("INE", "04", "SUBSTRING", "UK-INE"),
        ])

    def test_substring_length_cutoff_uses_the_cleaned_query(self):
        incidents = [
            ("I1", "SUPPLIER", "X"), ("I2", "SUPPLIER", "XY"),
            ("I3", "SUPPLIER", "Apex Ltd."), ("I4", "SUPPLIER", "Orion"),
        ]
        engagements = [
            ("01", "X Press", "", ""), ("02", "XY West", "", ""),
            ("03", "EMEA Apex", "", ""), ("04", "NorthOrionCloud", "", ""),
            ("05", "Xpress", "XYartbox", ""), ("06", "ApexCloud", "Apet", ""),
        ]
        rows = self.run_finding(incidents, engagements)
        actual = [(row[self.incident["identifier"]], row[self.engagement["identifier"]],
                   row[self.candidate["method"]]) for row in rows]
        self.assertEqual(actual, [
            ("I1", "01", "SUBSTRING"), ("I2", "02", "SUBSTRING"),
            ("I3", "03", "SUBSTRING"), ("I4", "04", "SUBSTRING"),
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

    def test_one_csv_for_matches_unmatched_and_invalid_names_in_source_order(self):
        incidents = [
            ("001", "SUPPLIER", " B.T. "), ("002", "SUPPLIER", "North Star"),
            ("003", "SUPPLIER", "Holding Solutions Ltd."), ("004", "SUPPLIER", "  "),
            ("005", "HSBC", "North Star"), ("006", "SUPPLIER", "Unknown"),
        ]
        engagements = [("010", "North Star", "", "source, value"), ("011", "", "North Star UK", "")]
        rows = self.run_finding(incidents, engagements)
        self.assertEqual([(row["incident_id"], row["ENGAGEMENT_ID"], row[self.status]) for row in rows], [
            ("001", "", "NO_MATCH"), ("002", "010", "MATCHED"), ("002", "011", "MATCHED"),
            ("003", "", "INVALID_NAME"),
        ])
        self.assertEqual(rows[0]["classified_supplier_name"], " B.T. ")
        self.assertEqual(rows[0]["standardised_supplier_name"], "british telecom")
        self.assertEqual(rows[1][self.extra_field], "source, value")
        self.assertEqual(rows[3]["classified_supplier_name"], "Holding Solutions Ltd.")
        self.assertEqual(rows[3]["standardised_supplier_name"], "")
        for row in (rows[0], rows[3]):
            for column in [*self.search_fields, self.extra_field, "matched_supplier_column",
                           "match_type", "found_name_in_source"]:
                self.assertEqual(row[column], "")
        rerun = self.run_finding([("001", "SUPPLIER", "Acme")], [])
        self.assertEqual([row[self.status] for row in rerun], ["NO_MATCH"])
        self.assertEqual(self.run_finding([("006", "SUPPLIER", "Unknown")], []), [])
        self.assertEqual(list(self.output.parent.iterdir()), [self.output])

    def test_one_outcome_per_incident_without_a_match_and_separate_blank_ids(self):
        incidents = [
            ("I1", "SUPPLIER", "Ltd"), ("I2", "SUPPLIER", "Other"),
            ("I1", "SUPPLIER", "Acme"), ("I2", "SUPPLIER", "North Star"),
            ("I3", "SUPPLIER", "Ltd"), ("I3", "SUPPLIER", "Ltd"),
            ("", "SUPPLIER", "Acme"), ("", "SUPPLIER", "Other"),
            ("I2", "SUPPLIER", "Other"),
        ]
        rows = self.run_finding(incidents, [("E1", "North Star", "", "")])
        self.assertEqual([(row["incident_id"], row["classified_supplier_name"], row[self.status])
                          for row in rows], [
            ("I1", "Acme", "NO_MATCH"), ("I2", "North Star", "MATCHED"),
            ("I3", "Ltd", "INVALID_NAME"), ("", "Acme", "NO_MATCH"), ("", "Other", "NO_MATCH"),
        ])

    def test_selection_excludes_blank_and_unknown_supplier_names(self):
        incidents = [
            ("I1", "SUPPLIER", ""), ("I2", "SUPPLIER", " \t "),
            ("I3", "SUPPLIER", "Unknown"), ("I4", "SUPPLIER", "  unKNOWN "),
            ("I5", "SUPPLIER", " Unknown Ventures "), ("I6", "supplier", "Unknown Ventures"),
        ]
        rows = self.run_finding(incidents, [("E1", "Unknown Ventures", "", "")])
        self.assertEqual([row[self.incident["identifier"]] for row in rows], ["I5"])
        self.assertEqual(rows[0][self.incident["supplier"]], " Unknown Ventures ")
        self.assertEqual(rows[0][self.status], "MATCHED")

    def test_all_headers_can_be_renamed(self):
        columns = read_columns(COLUMNS)
        for section, fields in columns.items():
            for role in fields:
                fields[role] = f"{section} {role}"
        columns["engagement"]["search_columns_eng"] = ["renamed company", "renamed supplier"]
        self.use_columns(columns)

        incidents = [("01", "SUPPLIER", "B.T."), ("02", "SUPPLIER", "Ltd")]
        engagements = [("003", "BT", "British Telecom", "original value")]
        rows = self.run_finding(incidents, engagements)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][self.incident["identifier"]], "01")
        self.assertEqual(rows[0][self.engagement["identifier"]], "003")
        self.assertEqual(rows[0][self.candidate["method"]], "EXACT")
        self.assertEqual(rows[0][self.candidate["search_name"]], "british telecom")
        self.assertEqual(rows[0][self.candidate["source_field"]], self.search_fields[1])
        self.assertEqual(rows[0][self.candidate["source_value"]], "British Telecom")
        self.assertEqual(rows[0][self.status], "MATCHED")
        self.assertEqual(rows[1][self.incident["identifier"]], "02")
        self.assertEqual(rows[1][self.status], "INVALID_NAME")

    def test_every_matching_field_reaches_deduplication_in_yaml_order(self):
        fields = ["trading name", "region name", "brand name", "legal name"]
        columns = read_columns(self.columns_file)
        columns["engagement"]["search_columns_eng"] = [fields[2], fields[1], fields[3], fields[0], "absent"]
        self.use_columns(columns)
        values = ["Microsoft Ltd.", "Microsoft UK", "Microsfot", "Microsoft Inc."]

        # The CSV order differs from the search order, and one configured header is absent.
        supplier = dict(zip(fields, values))
        supplier[self.engagement["identifier"]] = "007"
        suppliers = clean_suppliers([supplier], self.search_fields)
        incident = {self.incident["identifier"]: "I1"}
        matches = find_matches([(incident, "microsoft")], suppliers,
                               self.incident["identifier"], self.engagement["identifier"])
        raw = [(row[-3], method) for _, _, method, row in matches]
        self.assertEqual(raw, [
            (fields[2], "FUZZY"), (fields[1], "SUBSTRING"), (fields[3], "EXACT"), (fields[0], "EXACT"),
        ])

        rows = self.run_finding([("I1", "SUPPLIER", "Microsoft")], [("007", *values)], fields)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][self.candidate["method"]], "EXACT")
        self.assertEqual(rows[0][self.candidate["source_field"]], fields[3])
        self.assertEqual(rows[0][self.candidate["source_value"]], "Microsoft Inc.")

    def test_single_selected_field_ignores_matches_in_other_csv_columns(self):
        first, second = self.search_fields
        columns = read_columns(self.columns_file)
        columns["engagement"]["search_columns_eng"] = [second]
        self.use_columns(columns)
        rows = self.run_finding([("I1", "SUPPLIER", "AXA")], [
            ("01", "AXA", "Unrelated"), ("02", "Other", "AXA"),
        ], [first, second])
        self.assertEqual([row[self.engagement["identifier"]] for row in rows], ["02"])
        self.assertEqual(rows[0][self.candidate["source_field"]], second)

    def test_vertical_engagement_csv_with_one_available_search_field(self):
        write_table(self.folder / "CLASSIFIED_INCIDENTS.csv",
                    [self.incident["identifier"], self.incident["classification"], self.incident["supplier"]],
                    [("I1", "SUPPLIER", "AXA")])
        write_table(self.folder / "ENG_ALL.csv", [self.engagement["identifier"], "01"],
                    [(self.search_fields[1], "AXA UK")])
        main(self.folder, self.output, columns_file=self.columns_file)
        rows = read_rows(self.output)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][self.candidate["source_field"]], self.search_fields[1])
        self.assertEqual(rows[0][self.candidate["method"]], "SUBSTRING")

    def test_no_configured_search_field_in_csv(self):
        with self.assertRaisesRegex(ValueError, "at least one configured search column"):
            self.run_finding([], [], source_fields=[self.extra_field])

    def test_legacy_status_mapping_is_used_in_the_single_csv(self):
        columns = read_columns(self.columns_file)
        del columns["candidate"]["status"]
        columns["invalid_name_report"] = {"status": "retrieval outcome"}
        self.columns_file.write_text(yaml.safe_dump(columns), encoding="utf-8")
        rows = self.run_finding([("01", "SUPPLIER", "Acme")], [])
        self.assertEqual(rows[0]["retrieval outcome"], "NO_MATCH")
        self.assertEqual(list(self.output.parent.iterdir()), [self.output])

    def test_invalid_search_field_lists(self):
        columns = read_columns(self.columns_file)
        for value in ([], "single string", [" "], [4], ["name", "name"]):
            with self.subTest(value=value):
                columns["engagement"]["search_columns_eng"] = value
                self.columns_file.write_text(yaml.safe_dump(columns), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "search_columns_eng"):
                    read_columns(self.columns_file)
