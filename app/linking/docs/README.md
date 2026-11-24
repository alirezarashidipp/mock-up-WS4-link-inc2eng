# Linking incidents to engagements

The incident has already been attributed to a known supplier. Finding retrieves candidate engagements by supplier name. Linking checks which engagements cover the supplier service, component or activity that caused or contributed to the incident, then records a decision and its evidence on every original candidate row.

## Inputs, configuration and output

| Resource | Location | Purpose |
| --- | --- | --- |
| Candidate file | `data/output/engagement_candidates.csv` | Sole source of incident and engagement records |
| System prompt | `app/linking/prompt.yml` | Evidence rules and decision instructions |
| Response schema | `app/linking/schema.py` | Required response structure, labels and field definitions |
| Incident definitions | `config/incident_columns.yml` | Descriptions of the 76 incident fields |
| Engagement definitions | `config/engagement_columns.yml` | Descriptions of the 22 engagement fields |
| Connection settings | Project-root `.env` | Provider, credentials, model or deployment, and temperature |
| Result | `data/output/engagement_links.csv` | Original source rows and columns followed by eight assessment columns |

Paths above are relative to the project root. The entry point resolves its default paths from its own location. The [input field reference](input-fields.md) gives the complete field definitions and candidate file requirements. [Finding documentation](../../finding/docs/README.md)

## Run Linking

Install the project's dependencies using the setup commands in the root README, place the candidate file at the input location, and configure the provider. Run this command from the project root. [Project setup](../../../README.md)

```powershell
.\.venv\Scripts\python.exe linking.py
```

Linking reads UTF-8 CSV candidate files. Headers must be populated and unique, and must exclude the eight assessment column names. Each populated row requires an `incident_id` and an `ENGAGEMENT_ID`. A header-only candidate file produces a header-only CSV with zero model calls.

The GPT-5.1 configuration requested for this project uses these settings, alongside the API key in the local environment.

```dotenv
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-5.1
LLM_TEMPERATURE=0.1
```

The application reads the model and temperature from configuration on each run. `LLM_PROVIDER` defaults to `openai` when absent. Model or deployment and temperature values must be supplied. Existing process environment values take precedence over values loaded from `.env`. [Settings template](../../../.env.example) · [Connection implementation](../llm_connection.py)

| Provider | Required variables |
| --- | --- |
| OpenAI | `OPENAI_API_KEY`, `OPENAI_MODEL`, `LLM_TEMPERATURE` |
| Azure OpenAI | `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_OPENAI_TOKEN_SCOPE`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_DEPLOYMENT`, `LLM_TEMPERATURE` |

Azure uses `EnvironmentCredential` and a bearer-token provider for Microsoft Entra authentication. The deployment setting is the name configured on the Azure resource. Both provider paths reuse one client per run, configure a 60-second SDK timeout and permit one SDK retry for eligible request failures.

## Processing one incident

1. `read_candidates()` reads the CSV and returns its headers and rows in source order.
2. `read_cases()` checks those rows and groups them by `incident_id`. The 76 selected incident values must agree across all rows of that incident.
3. Within each incident, group engagement rows with identical values across the 22 selected engagement fields. Assign each distinct record a `candidate_number`, starting at 1.
4. Restore saved progress and select incidents with blank assessments.
5. Send one incident with all its distinct engagement candidates, field definitions and the system prompt.
6. Parse the response into `LinkingDecision`. Check that every candidate number appears exactly once.
7. Map each assessment back to every original row associated with that candidate. Repeat the incident evidence strength across those rows.
8. Save the complete CSV snapshot before requesting the next incident.

Requests run sequentially. All candidates for an incident travel together. Identical engagement inputs share one assessment even when their rows are separated in the candidate file. An engagement ID repeated with different selected field values produces separate candidates. The local `candidate_number` associates a response with its source rows when the model changes response order. [Reader](../read_cases.py) · [Request and response mapping](../decision.py)

## What the model receives and returns

The request contains `field_definitions`, one `incident` object with 76 selected fields, and an `engagements` table. Its `columns` list starts with `candidate_number`, followed by the 22 selected engagement field names. Each array in `rows` represents one candidate and follows that same column order. Missing or whitespace-only values become JSON `null` and keep their position. Other values retain their source content, including `incident_id` and `ENGAGEMENT_ID`.

The abbreviated JSON example shows the user message for synthetic incident `inc2`. It includes three incident fields and four engagement rows, each with a local `candidate_number` and five source values. [Example request (JSON)](llm-request-example.json)

The OpenAI SDK call uses `chat.completions.parse` with `response_format=LinkingDecision`, the configured model and temperature, and `store=False`.

The response contains one shared `incident_evidence_citation_strength` and an `assessments` list. Four candidates require four assessments, even when none is `LINKED`. Each assessment has its candidate number, citations, engagement evidence strength, decision, rationale and confidence with its explanation. The writer maps these values to eight CSV columns. [Response schema](../schema.py)

## Decision rules

The relevant engagement may be outside the supplied list. Zero, one or several candidates can be confirmed. Apply the same evidence rules when the list contains a single candidate. [One-sentence rules](rules.md)

| Label | Required interpretation |
| --- | --- |
| `LINKED` | The incident implicates a supplier service, component or activity in the failure, and the engagement's documented scope covers it. |
| `POSSIBLY_LINKED` | A concrete service fit and plausible involvement, with a material gap or unresolved contradictory account preventing confirmation. |
| `NOT_LINKED` | The records exclude the candidate, for example through a clearly different supplier or incompatible service scope. |
| `INSUFFICIENT_EVIDENCE` | The available information is too sparse or generic to establish a concrete service fit or exclude the candidate. A supplier-name match alone falls here. |


Finding's `classified_supplier_name` and `standardised_supplier_name` explain how the candidate was selected. For example, a candidate file can record Azure as the classified name and microsoft as its search name. Accept this alias. A missing name or different spelling alone does not establish an identity conflict. A confirmed link requires service evidence from both sides. Eliminating other candidates provides no evidence for the remaining one.

## Evidence, strength and confidence

The prompt asks the model to read every supplied field, prefer concrete confirmed findings over suspicion, and retain negation and material counterevidence. Recorded timing and explicit corrections can establish that an account has been superseded. Column order, text length, repetition and incident severity provide no extra evidence weight. Copies of a claim count as one account. Geography and dates matter when they affect recorded service coverage.

Source values supply facts. Field definitions explain meaning. The prompt instructs the model to ignore instructions embedded in record text and to leave absent facts unknown. Citations are short, contiguous excerpts copied from the named field in the incident or the current engagement. [System prompt](../prompt.yml)

The two source-strength ratings describe how useful each source is for this linking task.

| Strength | Incident evidence | Engagement evidence |
| --- | --- | --- |
| `UNSUPPORTED` | No usable clue about the supplier service, component or activity implicated in the failure | No usable service scope |
| `WEAK` | Only a broad symptom or downstream impact, such as 20 minutes of failed card payments | Only a broad category, such as IT support |
| `MODERATE` | A specific supplier service is implicated, but a material detail is missing or disputed, such as which branch's WAN circuit failed | The service is identifiable, but coverage is unclear, such as WAN support for unspecified branches |
| `STRONG` | The incident establishes the implicated service and its material scope, such as a failure traced to the supplier's WAN circuit at the London branch | Coverage is clear, such as WAN support for all UK branches |

Missing details lower the rating only when they could change the service or scope described by that source. Incident strength is assessed once using the incident record alone. Engagement strength is assessed separately for each candidate. A precise description of an unrelated service can earn `STRONG` and accompany `NOT_LINKED`.

Decision confidence expresses how appropriate the chosen label is for the available evidence. `LOW` means substantial doubt remains, `MEDIUM` means meaningful doubt remains, and `HIGH` means little remaining doubt. Clearly established uncertainty can justify `POSSIBLY_LINKED` with `HIGH` confidence. These values are qualitative judgments. Measured accuracy requires comparison with reviewed reference decisions.

## CSV columns

The comma-separated CSV uses UTF-8 with a BOM. It preserves every source row, column and their order as text, including duplicate rows and fully blank rows. Fully blank source rows retain blank assessments. Pending candidate rows have eight empty assessment fields.

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
| Investigation records failures in hosting and connectivity. Candidates 2 and 4 have equally strong support, ahead of candidate 1. | All three remain `LINKED` if each has defensible supporting evidence. |
| Both records support two engagements, with one directly identifying the affected component and the other having broader supported scope. | Both are `LINKED`. |
| The affected service matches two regional engagements, but the incident's region is unknown. | Both can be `POSSIBLY_LINKED`. Their rationales identify the missing region. |
| The incident is explicitly limited to London and the engagement's service coverage explicitly excludes London. | `NOT_LINKED` with a scope-conflict explanation. |
| The supplier's WAN circuit failed. The two retrieved engagements are expressly limited to payroll and office printing. | Both are `NOT_LINKED`. Each scope excludes the failed service. |
| The supplier is known, but the incident gives no usable service clue and the only common fact is the supplier name. | Each candidate receives `INSUFFICIENT_EVIDENCE`. |

## Saving and resuming

On a fresh run, the CSV starts with all source rows and blank assessment columns. After each complete incident response, the writer creates a temporary snapshot in the output directory, flushes and synchronises it to disk, replaces `engagement_links.csv.pending`, then atomically replaces `engagement_links.csv`. The next incident request starts after this save succeeds.

If a request or validation fails, saved incidents remain available and the run stops. If an external program prevents final replacement, a completed `.pending` snapshot remains available for recovery. A response interrupted before it reaches disk must be requested again.

Rerun the same command with the same input to continue. The saved header must match the source columns followed by the eight assessment columns in order. Linking checks the source rows, recovers any pending snapshot and requests only incidents with blank assessments.

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

Pydantic enforces required fields, allowed labels, types and extra-field rejection. The code checks candidate coverage. Citation fidelity and the correctness of semantic decisions require reviewing the source evidence.

All source rows and snapshots are held in memory, and each incident save rewrites the full CSV. Request size grows with all fields and candidates for an incident, so model context and output limits constrain the usable case size. The provider's eligible retry handles request failures; semantic validation errors stop the run.

Synthetic and mocked-response checks establish candidate file mapping, serialization and recovery behavior. Live provider tests establish provider compatibility and observed responses. Decision quality requires reviewed cases and explicit accuracy measurements.

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
