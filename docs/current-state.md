# Incident-to-engagement linking

Both stages run from the project root and write to `data/output/`.

| Stage guide | Command | Output | One row per |
| --- | --- | --- | --- |
| [Finding candidates](finding/README.md) | `python finding.py` | `engagement_candidates.xlsx` | Incident and matching engagement record |
| [Linking incidents](linking/README.md) | `python linking.py` | `engagement_links.xlsx` | Distinct incident in the candidate workbook |

Linking reads incident and engagement records from `data/output/engagement_candidates.xlsx`. The model ranks every plausible supplied candidate and returns `LINKED` or `NOT_LINKED`, decision confidence and incident evidence strength. For `LINKED`, it also gives the strength of the selected link and a one-sentence explanation. The code copies engagement IDs from the source records and creates Excel columns for all returned ranks.
