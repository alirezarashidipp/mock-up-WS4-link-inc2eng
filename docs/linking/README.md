# Linking incidents to engagements

Run `python linking.py` from the project root with `data/output/engagement_candidates.xlsx` as the sole data input. Configure the OpenAI or Azure OpenAI connection in the project-root `.env`. [Connection settings](../../.env.example)

Finding filters the incidents and saves each matching incident and engagement together. Linking groups these rows by their nonblank `incident_id` and reads the incident details and candidate engagements from the same workbook. [Finding guide](../finding/README.md) · [Workbook reader](../../app/linking/read_cases.py)

For each incident with candidates, one LLM request compares all supplied engagements. The request includes 74 original incident fields, 22 source fields per engagement and their English definitions. Classification outputs and finder metadata stay local. Missing or blank values are sent as JSON `null`. Zero values are preserved. [Source field lists](../../app/linking/fields.py) · [Decision prompt](../../app/linking/prompt.yml)

The response schema orders the fields as `candidates`, `incident_evidence_strength`, `decision_reason`, `link_decision`, `linked_strength`, `linked_strength_reason` and `confidence`. [Output field definitions](../../app/linking/schema.py)

The code assigns each engagement a `candidate_number`, starting at 1 within each incident. The model ranks every plausible candidate and returns its `candidate_number`, `incident_citation`, `engagement_citation` and `rationale`. Each citation contains the exact field name and a verbatim source excerpt in the form `column_name: source text`. The code resolves each number to the original record and copies its `ENGAGEMENT_ID` into the result.

`data/output/engagement_links.xlsx` contains one row per distinct incident in the candidate workbook. Its base columns are `incident_id`, `link_decision`, `selected_engagement_id`, `confidence`, `decision_reason`, `incident_evidence_strength`, `linked_strength` and `linked_strength_reason`. Candidate columns expand to fit the largest returned ranking. Each rank adds `candidate_N_engagement_id` and `candidate_N_rationale`, whose cell contains the rationale followed by both citations.

| Decision | Meaning |
| --- | --- |
| `LINKED` | Evidence distinguishes one engagement, ranked first by the model. |
| `NOT_LINKED` | The evidence leaves several plausible options, is insufficient for selection, or rules out the supplied options. |

For `LINKED`, the code fills `selected_engagement_id` from the first-ranked candidate's source record. For `NOT_LINKED`, it leaves the selection blank. Each model decision has one overall `confidence` tag (`LOW`, `MEDIUM` or `HIGH`). High confidence is valid for a well-supported decision to leave an incident unlinked.

`incident_evidence_strength` assesses the quality and sufficiency of the incident evidence for identifying the affected service and its scope. `UNSUPPORTED` means usable evidence is absent, `WEAK` means the evidence is indirect or ambiguous, `MODERATE` means relevant evidence has a material gap or conflict, and `STRONG` means clear, specific evidence supports the service context. `decision_reason` explains the decision, confidence and evidence limitations.

`linked_strength` assesses the evidence connecting the selected engagement's scope to the affected service. `WEAK` means limited, indirect support, `MODERATE` means relevant service or scope evidence with a remaining gap, and `STRONG` means clear, specific and consistent evidence with no unresolved material conflict. `linked_strength_reason` explains the chosen tag in one sentence. Both fields are populated for `LINKED` and are JSON `null`, displayed as blank cells in Excel, for `NOT_LINKED`.

An incident with zero matches has no row in the candidate workbook or the linking output. A candidate workbook containing only headers produces a header-only output with zero model calls.
