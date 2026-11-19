# Linking incidents to engagements

Run `python linking.py` from the project root. The sole data input is `data/output/engagement_candidates.xlsx`. Configure the provider in the project-root `.env`. [Connection settings](../../.env.example)

With `LLM_PROVIDER=openai`, set `OPENAI_API_KEY` and `OPENAI_MODEL`. With `LLM_PROVIDER=azure`, set `AZURE_OPENAI_DEPLOYMENT` to your deployment name. Linking uses the configured tenant, client ID and client secret to obtain a Microsoft Entra token for `AZURE_OPENAI_TOKEN_SCOPE`, then calls the configured endpoint and API version. Both paths reuse one client per run. Each incident request uses `chat.completions.parse` with the YAML prompt, the `LinkingDecision` response schema and `LLM_TEMPERATURE`. [Connection code](../../app/linking/llm_connection.py) · [Request code](../../app/linking/decision.py)

The supplier is already known. Each request contains one incident (74 source fields) and all its distinct engagement records (22 source fields each). The model assesses every supplied engagement independently. Local candidate numbers associate the response with its original rows even if the model returns assessments in another order. Rows with identical engagement inputs within an incident share an assessment. [Input fields](input-fields.md) · [Prompt](../../app/linking/prompt.yml) · [Schema](../../app/linking/schema.py)

## Reading the workbook

`data/output/engagement_links.xlsx` has one sheet, `Linking decisions`. It retains the active candidate sheet's original rows, columns, order and source IDs. Eight columns follow the source columns.

| Added column, in order | Meaning |
| --- | --- |
| `incident_evidence` | Zero or more excerpts from the incident relevant to this engagement. |
| `engagement_evidence` | Zero or more excerpts from this engagement's record. |
| `incident_evidence_strength` | Scored once per incident and repeated on its rows. How precisely the incident identifies the affected service and scope needed to find the appropriate engagements. `UNSUPPORTED` means no usable service clues, `WEAK` means broad clues, `MODERATE` means relevant details with a material gap, and `STRONG` means specific identifying details. |
| `link_rationale` | Why this engagement is supported, contradicted or unresolved. For ambiguous alternatives, the rationale explains what evidence would distinguish them. |
| `link_decision` | `LINKED` when the evidence supports this particular engagement's involvement. `NOT_LINKED` when the supplied evidence cannot establish that link, including when it rules the engagement out. |
| `linked_strength` | For `LINKED`, `WEAK` for limited indirect support, `MODERATE` for relevant support with a gap, or `STRONG` for clear and consistent support. Blank for `NOT_LINKED`. |
| `linked_strength_reason` | For `LINKED`, one sentence explaining the strength. Blank for `NOT_LINKED`. |
| `llm_confidence` | `LOW`, `MEDIUM` or `HIGH` confidence in this pair's decision. A clear lack of usable evidence can support high confidence in `NOT_LINKED`. |

Both evidence fields are lists in JSON. Excel displays each `column_name: verbatim excerpt` on its own line in the corresponding cell and shows `[]` for an empty list. A header-only candidate sheet produces a header-only output with zero model calls.

## Two services or two alternatives

If an investigation records both an EC2 hosting failure and a Direct Connect disruption, and each engagement covers one of those services, both rows can be `LINKED`. If the incident records only “AWS connectivity lost” and two network engagements differ by an unspecified region, both rows can be `NOT_LINKED`. Each rationale identifies the unresolved regional scope.
