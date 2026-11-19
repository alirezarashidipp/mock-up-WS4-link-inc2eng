# Linking incidents to engagements

Run `python linking.py` from the project root after [finding candidates](../finding/README.md). Linking reads `data/input/CLASSIFIED_INCIDENTS.csv` and `data/output/engagement_candidates.xlsx` from the same inputs. Each eligible incident must have a unique, nonblank `incident_id`. Configure the OpenAI or Azure OpenAI connection in the project-root `.env`. [Connection settings](../../.env.example)

Before contacting the model, linking checks candidate rows against the current eligible incidents and their classified supplier names. [Workbook reader](../../app/linking/read_cases.py)

For each incident with candidates, one LLM request compares all supplied engagements. The request includes 74 original incident fields, 22 source fields per engagement and their English definitions. Classification outputs and finder metadata stay local. Missing or blank values are sent as JSON `null`. Zero values are preserved. [Source field lists](../../app/linking/fields.py) · [Decision prompt](../../app/linking/prompt.yml)

`data/output/engagement_links.xlsx` contains one row per eligible incident. The model ranks up to three engagements. Each ranked ID has a rationale with the field name and a verbatim excerpt from both the incident and the engagement. [Output field definitions](../../app/linking/schema.py)

| Decision | Meaning |
| --- | --- |
| `LINKED` | Evidence distinguishes one engagement. Its first-ranked ID fills `selected_engagement_id`. |
| `AMBIGUOUS` | Two or more engagements are plausible and the evidence does not distinguish a winner. |
| `INSUFFICIENT_EVIDENCE` | Missing information prevents a choice. |
| `NO_SUITABLE_CANDIDATE` | The available evidence rules out all supplied engagements. |
| `NO_CANDIDATES` | The finder returned zero candidates. Linking writes this outcome locally. |

`selected_engagement_id` is blank for every outcome other than `LINKED`. Each model decision has one overall `confidence` tag (`LOW`, `MEDIUM` or `HIGH`) and a `decision_reason` explaining the choice or abstention. The local `NO_CANDIDATES` row has a blank confidence.
