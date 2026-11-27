# Linking incidents to engagements

The incident has already been attributed to a known supplier. Finding retrieves candidate engagements by supplier name. Linking checks which engagements cover the supplier service, component or activity that caused or contributed to the incident, then records a decision and its evidence on every original candidate row.

## Inputs, configuration and output

| Resource | Location | Purpose |
| --- | --- | --- |
| Candidate file | `data/output/engagement_candidates.csv` | Sole source of incident and engagement records |
| System prompt | `app/linking/prompt.yml` | Evidence rules and decision instructions |
| Response schema | `app/linking/schema.py` | Required response structure, labels and field definitions |
| Incident definitions | `config/incident_columns.yml` | Descriptions of the 76 incident fields |
| Engagement definitions | `config/engagement_columns.yml` | Descriptions of the 27 engagement fields |
| Connection settings | Project-root `.env` | Provider, credentials, model or deployment, and temperature |
| Result | `data/output/engagement_links.csv` | Original source rows and columns followed by eight assessment columns |

Paths above are relative to the project root. The entry point resolves its default paths from its own location. The [input field reference](input-fields.md) gives the complete field definitions and candidate file requirements. [Finding documentation](../../finding/docs/README.md)

## Run Linking

Install the project's dependencies using the setup commands in the root README, place the candidate file at the input location, and configure the provider. Run this command from the project root. [Project setup](../../../README.md)

```powershell
.\.venv\Scripts\python.exe linking.py
```

Linking reads comma-separated UTF-8 CSV files with or without a BOM. The header must include `incident_id` and either `ENGAGEMENT_ID` or `ENG.ENGAGEMENT_ID`. Each populated row must match the header width. Rows marked `MATCHED` require both IDs. Rows marked `NO_MATCH` or `INVALID_NAME` have an empty engagement ID and are copied to the output with eight empty assessment fields. A file containing only these rows or only headers requires zero model calls. Older candidate files without a Finding status column are read as before, with both IDs required on populated rows. [Candidate file requirements](input-fields.md#candidate-file-requirements)

Linking loads the provider settings only when an incident needs assessment. Set `LLM_PROVIDER` to `openai` (the default) or `azure`. Supply a model or deployment and a temperature it supports. The settings template leaves the model blank and shows `LLM_TEMPERATURE=0.7`. Existing process environment values take precedence over `.env`. [Settings template](../../../.env.example) · [Connection implementation](../llm_connection.py)

| Provider | Required variables |
| --- | --- |
| OpenAI | `OPENAI_API_KEY`, `OPENAI_MODEL`, `LLM_TEMPERATURE` |
| Azure OpenAI | `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_OPENAI_TOKEN_SCOPE`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_DEPLOYMENT`, `LLM_TEMPERATURE` |

Azure uses `EnvironmentCredential` and a bearer-token provider for Microsoft Entra authentication. The deployment setting is the name configured on the Azure resource. Both provider paths reuse one client per run, configure a 180-second SDK request timeout and permit one SDK retry for eligible request failures.

## Processing one incident

1. `read_candidates()` reads the CSV and returns its headers and rows in source order.
2. `read_cases()` checks the Finding status and groups candidate rows by `incident_id`. The 76 selected incident values must agree across the candidate rows of that incident.
3. Within each incident, group engagement rows with identical values across the 27 selected engagement fields. Keep distinct records in order of first appearance.
4. Restore saved progress and select incidents with blank assessments.
5. Send up to 80 distinct candidates per request. Each batch repeats the incident and field definitions and numbers its candidates from 1.
6. Check that each local candidate number appears exactly once. After the first batch, append its incident evidence rating to the system prompt and ask the model to return that rating for the remaining batches.
7. Match each assessment by its local number to its candidate in that batch and then to the candidate's original rows.
8. After all batches for the incident succeed, save the complete CSV snapshot before requesting the next incident.

Requests run sequentially. For 100 distinct candidates, the first request carries 80 and the second carries 20. Identical engagement inputs share one assessment even when their rows are separated in the candidate file. An engagement ID repeated with different selected field values produces separate candidates. [Reader](../read_cases.py) · [Request and response mapping](../decision.py)

## What the model receives and returns

The request starts with the `incident` list, followed by `field_definitions` and then `engagements`. Each of the 76 incident entries gives the `column_name`, its English `definition` and the source `value`. An incident citation uses the column name and an excerpt from that value.

The engagement definitions appear once in `field_definitions.engagement`. The `engagements.columns` list starts with `candidate_number`, followed by the 27 selected engagement field names. Each array in `engagements.rows` holds one candidate's values in that order. Across both records, missing or whitespace-only values become JSON `null`. Other values retain their source content, including `incident_id` and `ENGAGEMENT_ID`.

The abbreviated JSON example shows the user message for synthetic incident `inc2`. It includes three incident fields and four engagement rows, each with a local `candidate_number` and five source values. [Example request (JSON)](llm-request-example.json)

The OpenAI SDK call uses `chat.completions.parse` with `response_format=LinkingDecision`, the configured model and temperature, and `store=False`.

Every response contains an `incident_evidence_citation_strength` and an `assessments` list covering every candidate in that request, even when none is `LINKED`. Each assessment supplies its local number, both citation lists, engagement evidence strength, decision, rationale and confidence with its explanation. The local number maps the assessment to its CSV rows. The writer repeats the first response's incident rating on all assessed rows for that incident. [Response schema](../schema.py)

## Decision rules

The relevant engagement may be outside the supplied list. Zero, one or several candidates can be confirmed. For each candidate, including a sole candidate, the prompt applies the first supported rule in the order below. [One-sentence rules](rules.md)

| Label | Required interpretation |
| --- | --- |
| `NOT_LINKED` | The records exclude the candidate, for example through a clearly different supplier or incompatible service scope. |
| `LINKED` | The incident implicates a supplier service, component or activity in the failure, the engagement's documented scope covers it, and the records resolve any material conflict. |
| `POSSIBLY_LINKED` | A concrete service fit and plausible involvement, with a material gap or unresolved contradictory account preventing confirmation. |
| `INSUFFICIENT_EVIDENCE` | The available information is too sparse or generic to establish a concrete service fit or exclude the candidate. A supplier-name match alone falls here. |


Finding's `classified_supplier_name` and `standardised_supplier_name` explain how the candidate was selected. For example, a candidate file can record Azure as the classified name and microsoft as its search name. Accept this alias. A missing name or different spelling alone does not establish an identity conflict. A confirmed link requires service evidence from both sides. Eliminating other candidates provides no evidence for the remaining one.

## Evidence, strength and confidence

The prompt gives confirmed findings more weight than suspicion and asks the model to retain negation and material counterevidence. Recorded timing and explicit corrections can establish that an account has been superseded. Column order, text length, repetition and incident severity provide no extra evidence weight. Copies of a claim count as one account. Geography and dates matter when they affect recorded service coverage.

Source values supply facts. Field definitions explain meaning. The prompt instructs the model to ignore instructions embedded in record text and to leave absent facts unknown. Citations are short, contiguous excerpts copied from the named field in the incident or the current engagement. [System prompt](../prompt.yml)

The two source-strength ratings describe how useful each source is for this linking task.

| Strength | Incident evidence | Engagement evidence |
| --- | --- | --- |
| `UNSUPPORTED` | No usable clue about the supplier service, component or activity implicated in the failure | No usable service scope |
| `WEAK` | Only a broad symptom or downstream impact, such as 20 minutes of failed card payments | Only a broad category, such as IT support |
| `MODERATE` | A specific supplier service is implicated, but a material detail is missing or disputed, such as which branch's WAN circuit failed | The service is identifiable, but coverage is unclear, such as WAN support for unspecified branches |
| `STRONG` | The incident establishes the implicated service and its material scope, such as a failure traced to the supplier's WAN circuit at the London branch | Coverage is clear, such as WAN support for all UK branches |

Missing details lower the rating only when they could change the service or scope described by that source. The incident rating uses the incident record alone. The model rates each engagement's scope separately. A precise description of an unrelated service can earn `STRONG` and accompany `NOT_LINKED`.

Decision confidence expresses how appropriate the chosen label is for the available evidence. `LOW` means substantial doubt remains, `MEDIUM` means meaningful doubt remains, and `HIGH` means little remaining doubt. Clearly established uncertainty can justify `POSSIBLY_LINKED` with `HIGH` confidence. These values are qualitative judgments. Measured accuracy requires comparison with reviewed reference decisions.

## CSV columns

The comma-separated CSV uses UTF-8 with a BOM. It preserves every source row, column and their order as text, including duplicate rows and fully blank rows. Fully blank source rows and Finding's `NO_MATCH` and `INVALID_NAME` rows retain blank assessments. Pending candidate rows have eight empty assessment fields until their incident is evaluated. [LLM output columns (HTML)](output-columns.html)

| Added column, in order | Meaning and representation |
| --- | --- |
| `incident_evidence_citation` | List of incident excerpts relevant to this candidate |
| `engagement_evidence_citation` | List of excerpts from this candidate's engagement |
| `incident_evidence_citation_strength` | Shared incident rating from the source-strength rubric |
| `engagement_evidence_citation_strength` | This engagement's rating from the source-strength rubric |
| `link_rationale` | One or two sentences explaining this candidate's decision and any decisive evidence, gap or conflict |
| `link_decision` | One of the four decision labels |
| `link_decision_confidence_reason` | One sentence explaining the confidence level for this decision |
| `link_decision_confidence` | `LOW`, `MEDIUM` or `HIGH` |

Citation lists become newline-separated `column_name: verbatim excerpt` values in one CSV field. An empty list becomes `[]`. The CSV writer quotes values containing commas, quotes or newlines. Read the file with a CSV parser to retain these fields correctly. The underlying CSV retains source IDs as text; spreadsheet import settings determine whether a viewer interprets them as numbers. [CSV writer](../save_results.py)

## Worked decision examples

These synthetic cases illustrate the decision rules.

| Recorded situation | Candidate result |
| --- | --- |
| Incident names a failed London router. Only one candidate's scope covers that London router service. | `LINKED` because the engagement covers the failed router. |
| The incident identifies a failure in the supplier's hosting service and a failure in its WAN service. One engagement covers the affected hosting site and another covers the failed circuit. | Both are `LINKED` on the evidence for their respective services. |
| Both records support two engagements, with one directly identifying the affected component and the other having broader supported scope. | Both are `LINKED`. |
| The affected service matches two regional engagements, but the incident's region is unknown. | Both can be `POSSIBLY_LINKED`. Their rationales identify the missing region. |
| The incident is explicitly limited to London and the engagement's service coverage explicitly excludes London. | `NOT_LINKED` with a scope-conflict explanation. |
| The supplier's WAN circuit failed. The two retrieved engagements are expressly limited to payroll and office printing. | Both are `NOT_LINKED`. Each scope excludes the failed service. |
| The supplier is known, but the incident gives no usable service clue and the only common fact is the supplier name. | Each candidate receives `INSUFFICIENT_EVIDENCE`. |

## Saving and resuming

On a fresh run, the CSV starts with all source rows and blank assessment columns. Once all batches for one incident succeed, the writer creates a temporary snapshot in the output directory, flushes and synchronises it to disk, replaces `engagement_links.csv.pending`, then atomically replaces `engagement_links.csv`. Processing the next incident starts after this save succeeds.

If a request or validation fails, saved incidents remain available and the run stops. On resume, all batches for the unfinished incident run again. If an external program prevents final replacement, a completed `.pending` snapshot remains available for recovery.

Rerun with the same input to continue. Linking reads the `.pending` snapshot first if it exists. An invalid pending snapshot stops the run even if the main CSV is valid. The saved header, row count and source values must match the input and expected output columns. A candidate is complete when all eight output cells contain a value and the decision label is recognised. Duplicate rows for the same candidate must have identical outputs. An incident with both complete and pending candidates raises an error. Only fully pending incidents are sent to the model.

A `.lock` file coordinates access to the output path through `FileLock`. A second process attempting to use the same output fails immediately while the lock is held.

Completed assessments remain completed when the prompt or model settings change. For a fresh assessment, choose a different output path through `main()`, or archive the existing CSV and any pending snapshot. From Python running in the project root, a separate output can be selected as follows.

```python
from pathlib import Path
from linking import main

main(output_file=Path("data/output/engagement_links_review.csv"))
```

## Checks and failure handling

| Reported condition | Meaning and next action |
| --- | --- |
| Blank or duplicate headers, or existing output columns in the candidate CSV | Supply the original candidate CSV with unique source headers. |
| Missing incident or engagement ID | Populate the required ID in each nonblank candidate row. |
| Incident fields differ between rows | Resolve conflicting copies of that incident's selected fields. |
| Missing connection settings or invalid temperature text | Check the required environment values. Temperature is parsed with `float()`. |
| Azure authentication failed | Check tenant, application credentials, token scope and network configuration. |
| Model returned no structured decision | Inspect the provider failure or refusal and rerun when resolved. |
| Unknown, repeated or omitted candidate number | The response cannot be mapped completely. The current incident remains pending. |
| Saved headers, row count or source values differ | Restore the matching input, or use a separate output for the intended dataset. |
| Partial saved incident or invalid saved assessment | Restore a consistent checkpoint or start a separate output. |
| Output replacement fails | Close the program holding the CSV, then rerun to recover the pending snapshot. |

Pydantic checks the response structure, field types and allowed labels. The validator requires exactly one assessment per local candidate number and a nonblank `link_rationale` for every decision. A `LINKED` assessment must also pass two evidence checks.

- At least one incident excerpt must contain non-whitespace text. The engagement citation list may be empty. Extra blank entries in either list are allowed.
- The first batch's incident rating, the current batch's incident rating and the candidate's engagement rating must all be `WEAK`, `MODERATE` or `STRONG`. Two different supported incident ratings pass this check.

The other three decisions can have two empty citation lists. The code does not compare quotations with the source CSV or verify the service fit. [Response validator](../validate_response.py)

All source rows and snapshots are held in memory, and each incident save rewrites the full CSV. Long source fields can still reach model context or output limits within a batch of 80. Eligible request failures can trigger an SDK retry. Semantic validation errors stop the run.

The Linking tests use synthetic CSVs and a mocked model client to exercise candidate mapping, validation, serialization and recovery. Provider compatibility requires a live request. Decision quality requires cases with reviewed reference decisions. [Linking tests](../../../tests/test_linking.py)

## Implementation map

| File | Responsibility |
| --- | --- |
| [linking.py](../../../linking.py) | Coordinate reading, resuming, requesting and saving each incident |
| [read_cases.py](../read_cases.py) | Open the candidate CSV and group its records with their source row positions |
| [fields.py](../fields.py) | Select and order model input fields |
| [read_instructions.py](../read_instructions.py) | Load the prompt and definitions for the selected model inputs |
| [llm_connection.py](../llm_connection.py) | Read settings, authenticate and manage the provider client |
| [decision.py](../decision.py) | Send the incident and engagement table and receive a structured response |
| [validate_response.py](../validate_response.py) | Check the candidate numbers and required citations and index the assessments |
| [schema.py](../schema.py) | Define structured response fields and rubrics |
| [prompt.yml](../prompt.yml) | Define evidence and decision instructions |
| [read_progress.py](../read_progress.py) | Restore saved rows and select the pending incidents |
| [save_results.py](../save_results.py) | Map assessments onto the source rows and manage the output CSV snapshots |
