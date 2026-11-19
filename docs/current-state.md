# Incident-to-engagement linking

Both stages run from the project root and write to `data/output/`.

| Stage guide | Command | Output | One row per |
| --- | --- | --- | --- |
| [Finding candidates](finding/README.md) | `python finding.py` | `engagement_candidates.xlsx` | Incident and matching engagement record |
| [Linking incidents](linking/README.md) | `python linking.py` | `engagement_links.xlsx` | Eligible incident, including those with zero candidates |
