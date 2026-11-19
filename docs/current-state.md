# Incident-to-engagement linking

The accountable supplier is already named in the classified incident. The product question is which of that supplier's engagements cover the service or services involved. Both stages run from the project root and write to `data/output/`.

| Stage guide | Command | Output | One row per |
| --- | --- | --- | --- |
| [Finding candidates](finding/README.md) | `python finding.py` | `engagement_candidates.xlsx` | Incident and matching engagement record |
| [Linking incidents](linking/README.md) | `python linking.py` | `engagement_links.csv` | Source row in the candidate workbook |

Linking reads only the candidate workbook for incident and engagement data. One model request contains 74 incident fields and 22 source fields per candidate. [Input column reference](linking/input-fields.md)

Each candidate receives one decision based on the incident and that engagement's own scope. Multiple engagements can be `LINKED` when each has supporting evidence. A concrete service match with unresolved involvement is `POSSIBLY_LINKED`. Incompatible scope or a supplier name alone yields `NOT_LINKED`. The rationale identifies the decisive fact, conflict or missing detail.

The CSV preserves every candidate row and source column in order and adds eight assessment columns. A blank decision means the incident is pending. Linking saves the entire incident before the next request and resumes from the CSV on rerun. [Output columns and recovery](linking/README.md)

`STRONGEST_LINKED` identifies the sole confirmed engagement or the one with uniquely strongest evidence of involvement. Equally supported confirmed leaders remain `LINKED`. The prompt prioritises recorded findings, accounts for material conflicts and treats repeated claims as one account. Source strength and confidence in the selected decision are assessed separately.
