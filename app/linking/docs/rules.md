# Linking rules

## Code rules

- Each request contains one incident and up to 80 distinct engagement candidates.
- Each supplied `candidate_number` must appear exactly once in the response.
- Candidate numbers run from 1 to the number of candidates in the current batch.
- Results are mapped by candidate number regardless of response order.
- Every batch returns an incident rating. The first batch's rating is saved for every candidate in that incident.
- Every decision requires a nonblank `link_rationale`.
- For `LINKED`, at least one incident excerpt must contain text. The engagement citation list may be empty. Blank entries are allowed in either list.
- For `LINKED`, `UNSUPPORTED` in the first or current batch's incident rating, or in this candidate's engagement rating, causes the response to fail validation.
- Duplicate source rows of the same candidate receive the same assessment.

[Response checks](../validate_response.py) · [Schema](../schema.py) · [Row grouping](../read_cases.py)

## Prompt rules

- Supplier attribution is established. Identify which engagements cover the supplier service, component or activity implicated in the failure. Gather excerpts from each source and rate its evidence.
- The relevant engagement may be outside the list. Zero, one or several candidates may be confirmed.
- Assess each candidate on its own evidence, even a sole candidate. Eliminating other candidates supplies no evidence for the one that remains.

Apply the first supported rule in this order.

1. `NOT_LINKED` requires evidence that excludes the candidate, such as a clear supplier identity conflict or incompatible service scope. Recognise the search alias recorded by Finding when comparing suppliers.
2. `LINKED` requires defensible evidence from both records tying the incident to the documented engagement scope. Cite both sides and resolve material conflicts before confirming.
3. `POSSIBLY_LINKED` requires a concrete service fit and a material gap or conflict that prevents confirmation. Explain both the fit and the gap.
4. `INSUFFICIENT_EVIDENCE` applies when the records cannot establish a concrete service fit or exclude the candidate. A supplier name alone falls here.

Give one or two sentences explaining the decision and one sentence explaining its confidence level.

[Prompt](../prompt.yml) · [Full Linking guide](README.md)
