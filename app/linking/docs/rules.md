# Linking rules

## Code rules

- Each request contains one incident and up to 80 distinct engagement candidates.
- Each supplied `candidate_number` must appear exactly once in the response.
- Candidate numbers run from 1 to the number of candidates in the current batch.
- Results are mapped by candidate number regardless of response order.
- Every candidate receives the same `incident_evidence_citation_strength` for its incident.
- Each decision must be `LINKED`, `POSSIBLY_LINKED`, `NOT_LINKED` or `INSUFFICIENT_EVIDENCE`.
- Duplicate source rows of the same candidate receive the same assessment.

[Response checks](../validate_response.py) · [Schema](../schema.py) · [Row grouping](../read_cases.py)

## Prompt rules

- Supplier attribution is established. Identify which engagements cover the supplier service, component or activity implicated in the failure. Gather excerpts from each source and rate its evidence.
- The relevant engagement may be outside the list. Zero, one or several candidates may be confirmed.
- Assess each candidate on its own evidence, even a sole candidate. Eliminating other candidates supplies no evidence for the one that remains.
- `LINKED` requires defensible service evidence from both the incident and that engagement. Several candidates can qualify.
- `POSSIBLY_LINKED` requires a concrete service fit and a material gap or conflict that prevents confirmation.
- `NOT_LINKED` requires evidence that excludes the candidate, such as a clear supplier identity conflict or incompatible service scope. Recognise the search alias recorded by Finding when comparing suppliers.
- `INSUFFICIENT_EVIDENCE` applies when the records cannot establish a concrete service fit or exclude the candidate. A supplier name alone falls here.
- Explain each decision in `link_rationale` and assess confidence in that decision.

[Prompt](../prompt.yml) · [Full Linking guide](README.md)
