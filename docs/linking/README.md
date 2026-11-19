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
| `incident_evidence__citation_strength` | Scored once per incident and repeated on its rows. `UNSUPPORTED` means no usable service clues, `WEAK` means broad or ambiguous clues, `MODERATE` means relevant details with a material gap or conflict, and `STRONG` means specific service and scope details with no unresolved material conflict. |
| `engagement_evidence__citation_strength` | Quality of this engagement record alone. `UNSUPPORTED` means no usable scope, `WEAK` means generic or ambiguous scope, `MODERATE` means an identifiable service with a material gap or conflict, and `STRONG` means specific service and scope with no unresolved material conflict. An unrelated engagement can still score `STRONG`. |
| `link_rationale` | Why this engagement is supported, contradicted or unresolved. For ambiguous alternatives, the rationale explains what evidence would distinguish them. |
| `link_decision` | `STRONGEST_LINKED` for the sole confirmed engagement or one whose involvement has uniquely strongest evidence. `LINKED` for other confirmed links, including ties for strongest. `POSSIBLY_LINKED` for a concrete service fit with unresolved involvement. `NOT_LINKED` for incompatible scope or no service-specific support. |
| `link_decision_confidence_reason` | One sentence identifying the evidence, conflict or gap that warrants the confidence level for this decision. |
| `link_decision_confidence` | Qualitative confidence in the chosen label. `LOW` means substantial doubt, `MEDIUM` meaningful doubt, and `HIGH` little remaining doubt. Clearly established uncertainty can support `HIGH` confidence in `POSSIBLY_LINKED`. |

Each citation is a contiguous excerpt from the named field in the incident or current engagement. The prompt prioritises confirmed findings, preserves negation and material counterevidence, and treats copied claims as one account. Superseded accounts require recorded timing or corrections supporting that interpretation. The rationale names only gaps that could change the decision. The CSV stores one `column_name: excerpt` per line and writes `[]` for an empty list. A header-only candidate sheet produces a header-only CSV with zero model calls.

Input values supply evidence, while field definitions explain meaning. Embedded instructions are ignored. Each link requires its own service evidence. Eliminating other candidates supplies no support for the remaining candidate. Source strength and decision confidence are assessed separately using the schema.

## Resuming a run

Linking saves all rows for an incident together before the next request. A blank `link_decision` marks a pending candidate. Run `python linking.py` again to resume. The CSV headers, source values and row order must match the input workbook and current output schema.

Completed incidents are skipped even if the model or prompt changes. For a fresh assessment, archive the CSV and its pending snapshot if present.

If another program prevents replacement, close it and rerun. A completed snapshot named `engagement_links.csv.pending` is recovered before sending more requests. An interrupted request whose response has not reached disk is retried. Only one Linking process can write to a given output at a time.

## Two services or two alternatives

If an investigation records both an EC2 hosting failure and a Direct Connect disruption, and each engagement covers one of those services, both rows can be `LINKED`. If the incident records only “AWS connectivity lost” and two network engagements differ by an unspecified region, both rows can be `POSSIBLY_LINKED`. Each rationale identifies the unresolved regional scope.
