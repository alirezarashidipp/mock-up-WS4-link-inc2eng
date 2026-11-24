import csv
import json
from contextlib import nullcontext
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from pydantic import ValidationError

import linking
from app.linking.fields import ENGAGEMENT_FIELDS, INCIDENT_FIELDS
from app.linking.schema import EngagementAssessment


EXPECTED_COLUMNS = [
    "incident_evidence_citation", "engagement_evidence_citation",
    "incident_evidence_citation_strength", "engagement_evidence_citation_strength",
    "link_rationale", "link_decision", "link_decision_confidence_reason", "link_decision_confidence",
]
SOURCE_HEADERS = ["incident_id", "incident_description", "ENG.ENGAGEMENT_ID", "ENGAGEMENT_NAME", "extra"]


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        csv.writer(stream).writerows(rows)


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.reader(stream))


def assessment(number, decision="NOT_LINKED"):
    return {
        "candidate_number": number,
        "incident_evidence_citation": [],
        "engagement_evidence_citation": [],
        "engagement_evidence_citation_strength": "WEAK",
        "link_decision": decision,
        "link_rationale": "The documented service scope explains the decision.",
        "link_decision_confidence_reason": "The scope is recorded.",
        "link_decision_confidence": "MEDIUM",
    }


class LinkingTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.input = Path(directory.name) / "candidates.csv"
        self.output = Path(directory.name) / "links.csv"
        self.client = Mock()
        connection = nullcontext((self.client, "offline-model", 0.1))
        connection_patch = patch.object(linking, "llm_connection", return_value=connection)
        self.connect = connection_patch.start()
        self.addCleanup(connection_patch.stop)

    def return_assessments(self, *responses):
        responses = iter(responses)

        def parse(**request):
            assessments = next(responses)
            parsed = request["response_format"](
                incident_evidence_citation_strength="STRONG", assessments=assessments
            )
            message = SimpleNamespace(refusal=None, parsed=parsed)
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

        self.client.chat.completions.parse.side_effect = parse

    def test_reader_returns_headers_and_raw_rows(self):
        note = "First line, with a comma\n" + "x" * 150_000
        headers = ["reference", "note"]
        rows = [["0007", note], [], ["0008", ""]]
        write_csv(self.input, [headers, *rows])
        self.assertEqual(linking.read_candidates(self.input), (headers, rows))

    def test_decisions_follow_candidate_number_and_original_rows(self):
        incident = "WAN outage at a branch. Monitoring raised an alert."
        network = ["001", incident, "01", "WAN", "first, row"]
        monitoring = ["001", incident, "02", "Monitoring", "first copy"]
        regional = ["001", incident, "03", "Regional WAN", ""]
        other = ["002", "Supplier mentioned", "04", "Other", ""]
        source = [network, other, monitoring, [""] * len(SOURCE_HEADERS),
                  monitoring[:-1] + ["second copy"], regional]
        write_csv(self.input, [SOURCE_HEADERS, *source])
        affected = assessment(1, "LINKED")
        affected["incident_evidence_citation"] = ["incident_description: WAN outage"]
        affected["engagement_evidence_citation"] = ["ENGAGEMENT_NAME: WAN"]
        self.return_assessments(
            [assessment(3, "POSSIBLY_LINKED"), assessment(2, "NOT_LINKED"), affected],
            [assessment(1, "INSUFFICIENT_EVIDENCE")],
        )

        linking.main(self.input, self.output)
        linking.main(self.input, self.output)

        rows = read_csv(self.output)
        self.assertEqual(rows[0], SOURCE_HEADERS + EXPECTED_COLUMNS)
        self.assertEqual([row[:len(SOURCE_HEADERS)] for row in rows[1:]], source)
        decision_index = rows[0].index("link_decision")
        self.assertEqual([row[decision_index] for row in rows[1:]],
                         ["LINKED", "INSUFFICIENT_EVIDENCE", "NOT_LINKED", "", "NOT_LINKED", "POSSIBLY_LINKED"])
        self.assertEqual(rows[3][len(SOURCE_HEADERS):], rows[5][len(SOURCE_HEADERS):])
        self.assertEqual(rows[4][len(SOURCE_HEADERS):], [""] * len(EXPECTED_COLUMNS))
        calls = self.client.chat.completions.parse.call_args_list
        self.assertEqual(len(calls), 2)
        payload = json.loads(calls[0].kwargs["messages"][1]["content"])
        self.assertEqual(list(payload), ["incident", "field_definitions", "engagements"])
        definitions = linking.read_definitions()
        source_incident = {"incident_id": "001", "incident_description": incident}
        expected_fields = [
            {"column_name": name, "definition": definitions["incident"][name], "value": source_incident.get(name)}
            for name in INCIDENT_FIELDS
        ]
        self.assertEqual(payload["incident"], expected_fields)
        self.assertEqual(payload["field_definitions"], {"engagement": definitions["engagement"]})
        empty_fields = [None] * (len(ENGAGEMENT_FIELDS) - 2)
        self.assertEqual(payload["engagements"], {
            "columns": ["candidate_number", *ENGAGEMENT_FIELDS],
            "rows": [
                [1, "01", "WAN", *empty_fields],
                [2, "02", "Monitoring", *empty_fields],
                [3, "03", "Regional WAN", *empty_fields],
            ],
        })
        self.connect.assert_called_once()

    def test_linked_without_evidence_stops_only_the_current_incident(self):
        first = ["001", "Supplier mentioned", "01", "Support", ""]
        second = ["002", "WAN outage", "02", "Monitoring", ""]
        write_csv(self.input, [SOURCE_HEADERS, first, second])
        unsupported_link = assessment(1, "LINKED")
        unsupported_link["engagement_evidence_citation"] = ["ENGAGEMENT_NAME: Monitoring"]
        self.return_assessments([assessment(1, "INSUFFICIENT_EVIDENCE")], [unsupported_link])
        with self.assertRaisesRegex(ValueError, "LINKED candidate 1 needs evidence from both records"):
            linking.main(self.input, self.output)
        saved = read_csv(self.output)
        self.assertEqual(saved[1][saved[0].index("link_decision")], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(saved[2][len(SOURCE_HEADERS):], [""] * len(EXPECTED_COLUMNS))

        self.return_assessments([assessment(1)])
        linking.main(self.input, self.output)
        call = self.client.chat.completions.parse.call_args
        payload = json.loads(call.kwargs["messages"][1]["content"])
        values = {field["column_name"]: field["value"] for field in payload["incident"]}
        self.assertEqual(values["incident_id"], "002")
        self.assertEqual(self.client.chat.completions.parse.call_count, 3)

    def test_model_schema_accepts_the_current_fields_only(self):
        record = assessment(1)
        self.assertEqual(EngagementAssessment(**record).model_dump(), record)
        self.assertEqual(set(EngagementAssessment.model_json_schema()["properties"]), set(record))
        with self.assertRaises(ValidationError):
            EngagementAssessment(**record, extra_field="unexpected")

    def test_resume_requests_only_the_pending_incident(self):
        done = ["001", "WAN outage", "01", "WAN", ""]
        pending = ["002", "Supplier mentioned", "02", "Support", ""]
        write_csv(self.input, [SOURCE_HEADERS, done, pending])
        previous = ["[]", "[]", "WEAK", "WEAK", "Earlier rationale", "POSSIBLY_LINKED", "Unclear", "LOW"]
        write_csv(self.output, [SOURCE_HEADERS + EXPECTED_COLUMNS, done + previous,
                                pending + [""] * len(EXPECTED_COLUMNS)])
        self.return_assessments([assessment(1, "INSUFFICIENT_EVIDENCE")])

        linking.main(self.input, self.output)
        linking.main(self.input, self.output)

        request = self.client.chat.completions.parse
        request.assert_called_once()
        payload = json.loads(request.call_args.kwargs["messages"][1]["content"])
        values = {field["column_name"]: field["value"] for field in payload["incident"]}
        self.assertEqual(values["incident_id"], "002")
        headers, first, second = read_csv(self.output)
        self.assertEqual(headers, SOURCE_HEADERS + EXPECTED_COLUMNS)
        self.assertEqual(first, done + previous)
        self.assertEqual(second[headers.index("link_decision")], "INSUFFICIENT_EVIDENCE")

    def test_empty_input(self):
        write_csv(self.input, [SOURCE_HEADERS])
        linking.main(self.input, self.output)
        self.assertEqual(read_csv(self.output), [SOURCE_HEADERS + EXPECTED_COLUMNS])
        self.connect.assert_not_called()

    def test_physical_blank_lines_keep_their_positions_on_resume(self):
        record = ["001", "Supplier mentioned", "01", "Service", ""]
        write_csv(self.input, [SOURCE_HEADERS, [], record, []])
        self.return_assessments([assessment(1, "INSUFFICIENT_EVIDENCE")])
        linking.main(self.input, self.output)
        linking.main(self.input, self.output)
        headers, before, assessed, after = read_csv(self.output)
        self.assertEqual(before, [""] * len(headers))
        self.assertEqual(after, before)
        self.assertEqual(assessed[:len(SOURCE_HEADERS)], record)
        self.client.chat.completions.parse.assert_called_once()

    def test_assessment_columns_are_reserved(self):
        write_csv(self.input, [SOURCE_HEADERS + ["link_decision"]])
        with self.assertRaisesRegex(ValueError, "linking output column"):
            linking.main(self.input, self.output)
        self.assertFalse(self.output.exists())

    def test_invalid_candidate_numbers_leave_the_whole_incident_pending(self):
        source = [["001", "WAN outage", "01", "WAN", ""], ["001", "WAN outage", "02", "Monitoring", ""]]
        write_csv(self.input, [SOURCE_HEADERS, *source])
        for numbers in ([1], [1, 1], [1, 3]):
            with self.subTest(numbers=numbers):
                self.return_assessments([assessment(number) for number in numbers])
                with self.assertRaisesRegex(ValueError, "candidate"):
                    linking.main(self.input, self.output)
                self.assertEqual(read_csv(self.output)[1:], [row + [""] * len(EXPECTED_COLUMNS) for row in source])

    def test_resume_rejects_an_unexpected_header_before_writing(self):
        write_csv(self.input, [SOURCE_HEADERS])
        original = [SOURCE_HEADERS + EXPECTED_COLUMNS + ["unexpected_column"]]
        write_csv(self.output, original)
        with self.assertRaisesRegex(ValueError, "different headers"):
            linking.main(self.input, self.output)
        self.assertEqual(read_csv(self.output), original)
        self.connect.assert_not_called()

    def test_completed_pending_snapshot_is_recovered_before_a_request(self):
        source = ["001", "WAN outage", "01", "WAN", ""]
        write_csv(self.input, [SOURCE_HEADERS, source])
        columns = SOURCE_HEADERS + EXPECTED_COLUMNS
        completed = ["[]", "[]", "STRONG", "WEAK", "Limited scope", "NOT_LINKED", "Unclear", "LOW"]
        pending = self.output.with_suffix(".csv.pending")
        write_csv(self.output, [columns, source + [""] * len(EXPECTED_COLUMNS)])
        write_csv(pending, [columns, source + completed])
        linking.main(self.input, self.output)
        self.assertEqual(read_csv(self.output), [columns, source + completed])
        self.assertFalse(pending.exists())
        self.connect.assert_not_called()

    def test_invalid_pending_decision_preserves_the_existing_output(self):
        source = ["001", "WAN outage", "01", "WAN", ""]
        write_csv(self.input, [SOURCE_HEADERS, source])
        columns = SOURCE_HEADERS + EXPECTED_COLUMNS
        original = [columns, source + [""] * len(EXPECTED_COLUMNS)]
        write_csv(self.output, original)
        invalid = ["[]", "[]", "STRONG", "WEAK", "Limited scope", "typo", "Unclear", "LOW"]
        pending = self.output.with_suffix(".csv.pending")
        write_csv(pending, [columns, source + invalid])
        with self.assertRaisesRegex(ValueError, "Invalid saved decision"):
            linking.main(self.input, self.output)
        self.assertEqual(read_csv(self.output), original)
        self.assertTrue(pending.exists())
        self.connect.assert_not_called()
