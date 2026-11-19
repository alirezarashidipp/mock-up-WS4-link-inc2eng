# Linking rules

## Code rules

- One incident can contain multiple engagement candidates.
- Each supplied `candidate_number` must appear exactly once in the response.
- Candidate numbers must be between `1` and `candidate_count`.
- Results are mapped by candidate number regardless of response order.
- Every candidate receives the same `incident_evidence_citation_strength` for its incident.
- Each decision must be `STRONGEST_LINKED`, `LINKED`, `POSSIBLY_LINKED` or `NOT_LINKED`.
- At most one distinct candidate per incident can be `STRONGEST_LINKED`.
- The sole confirmed link must be `STRONGEST_LINKED`.
- Duplicate source rows of the same candidate receive the same assessment.

[Response checks](../decision.py) · [Schema](../schema.py) · [Row grouping](../read_cases.py)

## Prompt rules

- Each confirmed link requires service evidence from the incident and that engagement.
- Multiple engagements can be confirmed when each has supporting evidence.
- Among several confirmed links, a uniquely strongest candidate receives `STRONGEST_LINKED`.
- Equally supported leaders remain `LINKED`.
- A concrete service fit with unresolved plausible involvement receives `POSSIBLY_LINKED`.
- Incompatible scope or absent service-specific support receives `NOT_LINKED`.
- Every decision includes source citations when available, a rationale and a confidence explanation.
- Strength rates source evidence, while confidence rates the appropriateness of the chosen decision.

[Prompt](../prompt.yml) · [Full Linking guide](README.md)
