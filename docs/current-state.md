# Incident-to-engagement linking

The accountable supplier is already named in the classified incident. The product question is which of that supplier's engagements cover the service or services involved. Both stages run from the project root and write to `data/output/`.

| Stage guide | Command | Output | One row per |
| --- | --- | --- | --- |
| [Finding candidates](finding/README.md) | `python finding.py` | `engagement_candidates.xlsx` | Incident and matching engagement record |
| [Linking incidents](linking/README.md) | `python linking.py` | `engagement_links.xlsx` | Source row in the candidate workbook |

Linking reads only the candidate workbook for incident and engagement data. One model request contains 74 incident fields and 22 source fields per candidate. [Input column reference](linking/input-fields.md)

The single `Linking decisions` sheet retains every candidate row and all source columns. Eight additional fields record evidence, its strength, the rationale, the pair's decision and confidence. Several engagements can be linked to the same incident. Each unresolved pair receives `NOT_LINKED` and a reason. [Interpreting linking decisions](linking/README.md)
