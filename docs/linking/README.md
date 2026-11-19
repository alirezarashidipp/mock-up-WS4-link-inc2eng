# Linking incidents to engagements

Run `python linking.py` from the project root. The sole data input is `data/output/engagement_candidates.xlsx`. Configure the provider in the project-root `.env`. [Connection settings](../../.env.example)

With `LLM_PROVIDER=openai`, set `OPENAI_API_KEY` and `OPENAI_MODEL`. With `LLM_PROVIDER=azure`, set `AZURE_OPENAI_DEPLOYMENT` to your deployment name. Linking uses the configured tenant, client ID and client secret to obtain a Microsoft Entra token for `AZURE_OPENAI_TOKEN_SCOPE`, then calls the configured endpoint and API version. Both paths reuse one client per run. Each incident request uses `chat.completions.parse` with the YAML prompt, the `LinkingDecision` response schema and `LLM_TEMPERATURE`. [Connection code](../../app/linking/llm_connection.py) · [Request code](../../app/linking/decision.py)

The supplier is already known. Each request contains one incident (74 source fields) and all its distinct engagement records (22 source fields each). The model assesses every supplied engagement independently. Local candidate numbers associate the response with its original rows even if the model returns assessments in another order. Rows with identical engagement inputs within an incident share an assessment. [Input fields](input-fields.md) · [Prompt](../../app/linking/prompt.yml) · [Schema](../../app/linking/schema.py)

## Reading the CSV

`data/output/engagement_links.csv` is a comma-separated UTF-8 file with a BOM. It retains the active candidate sheet's rows, columns, order and source IDs as text. Eight assessment columns follow the source columns. They start blank and fill in as each incident finishes.

| Added column, in order | Meaning |
| --- | --- |
| `incident_evidence_citation` | Zero or more excerpts from the incident relevant to this engagement. |
| `engagement_evidence_citation` | Zero or more excerpts from this engagement's record. |
| `incident_evidence__citation_strength` | Scored once per incident and repeated on its rows. How precisely the incident identifies the affected service and scope needed to find the appropriate engagements. `UNSUPPORTED` means no usable service clues, `WEAK` means broad clues, `MODERATE` means relevant details with a material gap, and `STRONG` means specific identifying details. |
| `engagement_evidence__citation_strength` | Quality of this engagement record alone. `UNSUPPORTED` means no usable scope, `WEAK` means generic scope, `MODERATE` means an identifiable service with material scope gaps, and `STRONG` means a specific service and scope. An unrelated engagement can still score `STRONG`. |
| `link_rationale` | Why this engagement is supported, contradicted or unresolved. For ambiguous alternatives, the rationale explains what evidence would distinguish them. |
| `link_decision` | `LINKED` when the evidence supports this particular engagement's involvement. `POSSIBLY_LINKED` when a concrete service match leaves involvement unresolved. `NOT_LINKED` when scope conflicts or there is no service-specific support. |
| `link_decision_confidence_reason` | One sentence identifying the evidence, conflict or gap that warrants the confidence level for this decision. |
| `link_decision_confidence` | `LOW`, `MEDIUM` or `HIGH` confidence in this pair's decision. A clear lack of usable evidence can support high confidence in `NOT_LINKED`. |

Both citation fields contain lists of verbatim excerpts in the form `column_name: excerpt` in the model response. The CSV stores one excerpt per line in a quoted field and writes `[]` for an empty list. A header-only candidate sheet produces a header-only CSV with zero model calls.

## Resuming a run

Linking saves all rows for an incident together before the next request. A blank `link_decision` marks a pending candidate. Run `python linking.py` again to resume. The CSV headers, source values and row order must match the input workbook and current output schema.

Completed incidents are skipped even if the model or prompt changes. For a fresh assessment, archive the CSV and its pending snapshot if present.

If another program prevents replacement, close it and rerun. A completed snapshot named `engagement_links.csv.pending` is recovered before sending more requests. An interrupted request whose response has not reached disk is retried. Only one Linking process can write to a given output at a time.

## Two services or two alternatives

If an investigation records both an EC2 hosting failure and a Direct Connect disruption, and each engagement covers one of those services, both rows can be `LINKED`. If the incident records only “AWS connectivity lost” and two network engagements differ by an unspecified region, both rows can be `POSSIBLY_LINKED`. Each rationale identifies the unresolved regional scope.
