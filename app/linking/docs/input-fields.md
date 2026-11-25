# Linking input contract and field reference

Linking reads `data/output/engagement_candidates.csv`. The entry point calls `read_candidates()` to get the headers and raw rows, then `read_cases()` to check and group them while retaining their source positions. [Entry point](../../../linking.py) · [Candidate file reader](../read_cases.py) · [Linking guide](README.md)

## From candidate file rows to a model request

The request JSON contains these three properties in the order shown.

| Property | Content |
| --- | --- |
| `incident` | A list of the 76 selected incident fields. Each entry contains its source `column_name`, English `definition` and source `value`. |
| `field_definitions` | Its `engagement` object contains the English definitions for the 22 selected engagement columns. |
| `engagements` | A table with one shared `columns` list and one array in `rows` per distinct candidate in this batch, up to 80. |

The field lists in `INCIDENT_FIELDS` and `ENGAGEMENT_FIELDS` determine selection and order. The two YAML files supply the definitions for those fields. An incident field with a missing value still carries its name and definition, with `value` set to `null`. Every engagement row follows the order in `engagements.columns`, including `null` cells. [Selected fields](../fields.py) · [Request builder](../decision.py)

This example shows the first three columns of the `engagements` table for one incident.

```json
{
  "columns": ["candidate_number", "ENGAGEMENT_ID", "ENGAGEMENT_NAME"],
  "rows": [
    [1, "ENG1", "Card payment processing"],
    [2, "ENG2", "Payroll processing"],
    [3, "ENG3", "Office network support"]
  ]
}
```

`ENGAGEMENT_ID`, `THIRD_PARTY_ID`, `COUPA_THIRD_PARTY_ID` and the selected BGI IDs are included in the model input. The model returns the supplied `candidate_number` to identify each assessment. The application uses that number to attach the result to the corresponding source rows.

## Candidate file requirements

| Requirement | Current handling |
| --- | --- |
| First row contains headers | The CSV reader uses header names exactly as read. Empty or repeated names raise an error. |
| `incident_id` header | Required. Each candidate sent for assessment must have a nonblank value. |
| `ENGAGEMENT_ID` or `ENG.ENGAGEMENT_ID` header | Required. A matched row must have a nonblank engagement ID. An incident-only row must have an empty engagement ID. |
| `finding_status` | `MATCHED` rows are candidates. `NO_MATCH` and `INVALID_NAME` rows keep their original positions and receive no assessment. A missing status column supports older candidate-only files. |
| Additional selected fields | A missing column contributes `null` to the request for that field. |
| Linking output columns in the input | `read_cases()` reserves the eight assessment column names for the output. |
| Row width | Every row with cells must have exactly as many cells as the header, even if they are all empty. A shorter or longer row raises an error. |
| Empty rows | A physical blank line or a full-width row of empty cells keeps its position in the output and receives no assessment. |
| Header-only candidate file | Produces a header-only CSV and makes zero model requests when the required headers are present. |

Header names and identifiers are used as recorded. If Finding uses a custom status header, pass its name as `finding_status_column` to `linking.main()`. The linking reader performs no supplier-name cleaning or alias replacement. The field names below are case-sensitive. [Input reader and checks](../read_cases.py)

When a supplier header collides with an incident header or a Finding detail column, Finding prefixes the supplier header with `ENG.`. For every selected engagement field, Linking first checks for `ENG.<field>` and uses that header when present. Otherwise it uses the unprefixed field. The model receives the canonical name, such as `ENGAGEMENT_NAME`, even when the candidate file column is `ENG.ENGAGEMENT_NAME`. [Finding output headers](../../finding/save_csv.py) · [Engagement column selection](../read_cases.py)

## Grouping, duplicates and source positions

Candidate rows are grouped by the recorded `incident_id`, following the order in which matched incidents first appear. All 76 selected incident values must agree across that incident's candidate rows. A difference raises an error before model processing. This comparison occurs before whitespace-only values are converted to `null`, so an empty cell and a whitespace string in otherwise repeated incident data can trigger a mismatch.

Within an incident, an engagement is identified by the complete tuple of its 22 selected values. Identical tuples share one candidate and one model assessment. Their original row positions are retained, and the assessment is written to every matching position. Records with the same `ENGAGEMENT_ID` but different selected values are separate candidates.

Distinct engagements keep their order of first appearance. Linking sends them in batches of up to 80, repeating the same incident data in every request. Candidate numbers start at 1 in each batch. The application maps each returned `candidate_number` to a candidate within that batch and then to its original CSV rows, regardless of response order. [Grouping and duplicate handling](../read_cases.py) · [Response mapping](../validate_response.py)

For example, suppose rows 2 and 5 contain the same incident and identical engagement values, row 3 contains a different engagement for that incident, and row 4 belongs to another incident. The first incident is sent once with two candidates. Rows 2 and 5 receive the same assessment, row 3 receives the second assessment, and row 4 keeps its original position in the final CSV.

## Values sent to the model

An empty cell, a whitespace-only value or an absent optional column becomes JSON `null`. Nonblank source strings keep their original content. CSV fields, including identifiers with leading zeros, are read as text.

The request includes `classified_supplier_name` and Finding's `standardised_supplier_name` as supplier selection context. The CSV also retains `class`, `matched_supplier_column`, `match_type` and `found_name_in_source` from the candidate file.

The request includes the raw source fields `supplier_name` and `unlisted_supplier_name`. It omits upstream classification outputs such as `recorded_cause`, `supplier_product_or_service` and `supplier_name_confidence` because they are outside `INCIDENT_FIELDS`. The CSV retains all original candidate file columns, including any extra fields. [Request field selection](../decision.py) · [CSV preservation](../../../linking.py)

## Incident fields

These 76 definitions reproduce the selected entries in the incident YAML. The wording provides source-field context. In this Linking stage, `incident_id` is included in the model payload as well as used locally for grouping. [Incident definitions](../../../config/incident_columns.yml)

| Field | Definition |
| --- | --- |
| `incident_id` | Unique identifier of the incident, preserved locally to associate its original source data with its classification result. |
| `incident_description` | A detailed incident narrative describing symptoms, timing, impact, and investigation context. |
| `configuration_item_name` | The application, service, or configuration item associated with the incident. |
| `incident_assignment_group_name` | The support group assigned to the incident, which does not by itself establish causal responsibility. |
| `incident_business_impact` | Recorded effects of the incident on business services, transactions, customers, or regions. |
| `incident_category` | The high-level incident category recorded in the source system. |
| `incident_cause_details` | Recorded details about suspected or established incident causes. |
| `incident_caused_change_order_id` | The identifier of a change order linked in the source system as a possible or recorded cause of the incident. |
| `incident_close_code` | The code or label used to categorize how the incident was closed. |
| `incident_closed_datetime` | The recorded date and time when the incident was closed; the time zone is not specified here. |
| `incident_created_datetime` | The recorded date and time when the incident record was created; the time zone is not specified here. |
| `incident_disruption_flag` | The recorded flag indicating whether the incident is associated with a disruption. |
| `incident_disruption_name` | The name or label of the disruption associated with the incident. |
| `incident_duration_minutes` | The recorded incident duration in minutes, preserved as source text. |
| `incident_impacted_business_service_name` | The business service recorded as affected by the incident. |
| `incident_impacted_location_name` | The location or locations recorded as affected by the incident. |
| `incident_last_modified_datetime` | The recorded date and time of the incident record's latest update, which does not by itself establish when a cause was confirmed. |
| `incident_open_datetime` | The recorded date and time when the incident was opened; the time zone is not specified here. |
| `incident_parent_id` | The identifier of the parent incident linked to this incident. |
| `incident_resolution_description` | The recorded description or label of the incident resolution, which does not by itself establish who caused the incident. |
| `incident_resolution_notes` | Free-text incident resolution notes that may also describe contributing causes. |
| `incident_severity_code` | The severity code recorded for the incident; its scale is not defined here. |
| `incident_short_description` | A short summary of the reported incident and its main symptoms. |
| `incident_status` | The incident's recorded lifecycle status. |
| `incident_subcategory` | The more specific incident category recorded beneath the main category. |
| `major_incident_findings` | Recorded findings from the major-incident investigation. |
| `major_incident_summary` | A narrative summary of the major incident, including key events, symptoms, and impact. |
| `problem_id` | The identifier of the problem record associated with the incident. |
| `problem_summary` | A short summary of the problem linked to the incident. |
| `problem_close_datetime` | The recorded date and time when the problem record was closed; the time zone is not specified here. |
| `problem_close_notes` | Problem closure notes that may summarize the investigation, root cause, and conclusions. |
| `problem_configuration_item_name` | The application, service, or configuration item associated with the problem record. |
| `problem_description` | A description of the underlying problem, its symptoms, and investigation context. |
| `problem_last_modified_datetime` | The recorded date and time of the problem record's latest update, which does not by itself establish when a cause was confirmed. |
| `problem_open_datetime` | The recorded date and time when the problem record was opened; the time zone is not specified here. |
| `problem_related_incident_id` | The identifier of an incident linked from the problem record. |
| `problem_resolution_description` | A description or label of the resolution recorded for the underlying problem. |
| `problem_resolution_details` | Detailed resolution information recorded for the problem, which may describe proposed or completed actions. |
| `problem_risk_details` | Recorded information about risks associated with the problem or its resolution. |
| `problem_root_cause` | The root-cause explanation recorded on the problem record, including any stated mechanism or contributing conditions. |
| `problem_ticket_status` | The lifecycle status recorded for the linked problem ticket. |
| `problem_workaround` | A temporary workaround recorded for the problem; the source text determines whether it was proposed or applied. |
| `problem_cause_notes` | Investigation notes recorded on the problem about causal findings, suspected causes, or supporting observations. |
| `root_cause_id` | The identifier of the root-cause investigation task associated with the problem. |
| `root_cause_business_service_name` | The business service associated with the root-cause investigation task. |
| `root_cause_first_reported_by_incident_id` | The incident identifier recorded as the first report associated with the root-cause investigation task. |
| `root_cause_impact_code` | The impact code recorded on the root-cause investigation task; its scale is not defined here. |
| `root_cause_priority_code` | The priority code or label recorded on the root-cause investigation task; its scale is not defined here. |
| `root_cause_status_code` | The recorded lifecycle status code or label of the root-cause investigation task. |
| `root_cause_active_flag` | The recorded flag indicating whether the root-cause investigation task is active. |
| `root_cause_technology_owning_org_l2_name` | The level-two technology organization recorded as owning the root-cause task, without implying causal responsibility. |
| `root_cause_assignment_group_name` | The support group assigned to the root-cause task, which does not by itself establish causal responsibility. |
| `root_cause_category` | The category recorded for the root-cause investigation task. |
| `root_cause_code` | The recorded root-cause category or label, interpreted alongside the supporting narrative rather than as proof of responsibility. |
| `root_cause_notes` | The explanation of the root cause, contributing conditions, and causal mechanism recorded on the root-cause investigation task. |
| `root_cause_close_code` | The code or label describing the closure outcome of the root-cause investigation task. |
| `root_cause_close_notes` | Closure notes for the root-cause task that may include findings, resolution details, and preventive recommendations. |
| `root_cause_configuration_item_name` | The application, service, or configuration item associated with the root-cause investigation task. |
| `root_cause_description` | The detailed description of the issue, investigation, and work covered by the root-cause task. |
| `root_cause_fix_notes` | Recorded fix instructions, corrective actions, or preventive recommendations for the root-cause task; the text determines whether actions were proposed or completed. |
| `root_cause_read_across_action_flag` | The recorded flag for read-across actions concerning similar services or systems. |
| `root_cause_read_across_details` | Recorded details about applying root-cause findings or corrective actions to similar services or systems. |
| `root_cause_short_description` | A short summary of the root-cause investigation task and the issue it addresses. |
| `root_cause_type` | The type of task recorded for the root-cause investigation. |
| `unlisted_supplier_name` | A supplier name recorded outside the listed supplier selection; its presence alone does not establish accountable supplier identity. |
| `supplier_name` | The supplier name recorded in the source; its presence alone does not establish causal responsibility or the identity of the accountable supplier. |
| `root_cause_urgency_code` | The urgency code or label recorded on the root-cause investigation task; its scale is not defined here. |
| `incident_additional_comments` | Additional comments recorded for the incident, including context, communications, or follow-up information. |
| `incident_comments_and_work_notes` | Combined comments and work notes recorded for the incident, potentially including communications, operational updates, and investigation observations. |
| `incident_work_notes` | Work-log notes recorded for the incident, potentially including operational updates, investigation observations, and impact details. |
| `problem_comments_and_work_notes` | Combined comments and work notes recorded for the problem, potentially including investigation updates, communications, and progress details. |
| `problem_task_work_notes` | Work notes recorded for a problem task, potentially including investigation observations, actions, and progress. |
| `problem_task_work_notes_list` | A collection of work notes associated with the problem task, preserved in its source text format. |
| `euc_load_date` | The data-load date or timestamp recorded in the source extract; it does not by itself date the incident, causal findings, or restoration. |
| `classified_supplier_name` | Accountable supplier name exactly as recorded, without shortening, expansion, or normalization; Unknown if unresolved; null for other classes. |
| `standardised_supplier_name` | Supplier name used by Finding after cleaning and applying the configured whole-name alias. |

## Engagement fields

Each candidate row starts with its local `candidate_number`, followed by the values of these 22 source fields in the order shown. Definitions reproduce the selected entries in the engagement YAML. [Engagement definitions](../../../config/engagement_columns.yml)

| Field | Definition |
| --- | --- |
| `ENGAGEMENT_ID` | Identifier assigned to the engagement. |
| `ENGAGEMENT_NAME` | Name of the engagement. |
| `ENGAGEMENT_DESCRIPTION_TEXT` | Description of the work or services covered by the engagement. |
| `THIRD_PARTY_ID` | Identifier assigned to the third party in the engagement record. |
| `COUPA_THIRD_PARTY_ID` | Identifier of the third party in Coupa. |
| `THIRD_PARTY_NAME` | Third-party name recorded for the engagement. |
| `THIRD_PARTY_NORMALISED_NAME` | Standardised name of the third party. |
| `THIRD_PARTY_TYPE_NAME` | Type of third party recorded for the engagement. |
| `THIRD_PARTY_STATUS_NAME` | Status of the third party. |
| `SERVICE_CATEGORY_L1_NAME` | Name of the level-one service category. |
| `PRIMARY_BENEFICIARY_COUNTRY_TERRITORY_ISO_NAME` | Country or territory name recorded for the primary beneficiary. |
| `MANAGING_BGI_NAME` | Name of the managing BGI for the engagement. |
| `MANAGING_BGI_L1_ID` | Identifier at level one of the managing BGI hierarchy. |
| `MANAGING_BGI_L1_NAME` | Name at level one of the managing BGI hierarchy. |
| `MANAGING_BGI_L2_ID` | Identifier at level two of the managing BGI hierarchy. |
| `MANAGING_BGI_L2_NAME` | Name at level two of the managing BGI hierarchy. |
| `MANAGING_BGI_L3_ID` | Identifier at level three of the managing BGI hierarchy. |
| `MANAGING_BGI_L3_NAME` | Name at level three of the managing BGI hierarchy. |
| `MANAGING_BGI_L4_ID` | Identifier at level four of the managing BGI hierarchy. |
| `MANAGING_BGI_L4_NAME` | Name at level four of the managing BGI hierarchy. |
| `MANAGING_BGI_L5_ID` | Identifier at level five of the managing BGI hierarchy. |
| `MANAGING_BGI_L5_NAME` | Name at level five of the managing BGI hierarchy. |
