# Linking rules

## Code rules

- One incident can contain multiple engagement candidates.
- Each supplied `candidate_number` must appear exactly once in the response.
- Candidate numbers must be between `1` and `candidate_count`.
- Results are mapped by candidate number regardless of response order.
- Every candidate receives the same `incident_evidence_citation_strength` for its incident.
- Each decision must be `LINKED`, `POSSIBLY_LINKED`, `NOT_LINKED` or `INSUFFICIENT_EVIDENCE`.
- If any candidates are `LINKED`, exactly one distinct candidate receives `strongest_link = YES` and a one-sentence `strongest_link_rational`. Both fields are blank on other candidates and when there are no confirmed links.
- Duplicate source rows of the same candidate receive the same assessment.

[Response checks](../decision.py) · [Schema](../schema.py) · [Row grouping](../read_cases.py)

## Prompt rules

- Identify which engagements cover the service involved in the incident. Gather relevant excerpts from the incident and each candidate, then rate the quality of each source.
- Assess each candidate on its own evidence. Eliminating other candidates provides no evidence for the candidate that remains.
- `LINKED` requires defensible service evidence from both the incident and that engagement. Several candidates can qualify.
- `POSSIBLY_LINKED` requires a concrete service fit and a material gap or conflict that prevents confirmation.
- `NOT_LINKED` requires evidence that excludes the candidate, such as a clear supplier identity conflict or incompatible service scope. Recognise the search alias recorded by Finding when comparing suppliers.
- `INSUFFICIENT_EVIDENCE` applies when the records cannot establish a concrete service fit or exclude the candidate. A supplier name alone falls here.
- Explain each decision in `link_rationale` and assess confidence in that decision.
- After all decisions, select the sole confirmed link or the confirmed candidate with the strongest evidence. If the leaders are tied, choose the lowest local `candidate_number` among those leaders and explain the equal support and ordering in the selection sentence.

[Prompt](../prompt.yml) · [Full Linking guide](README.md)
