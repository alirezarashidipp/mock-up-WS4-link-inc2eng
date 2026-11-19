def contains_quote(record, field, quote):
    value = record.get(field)
    return value is not None and bool(quote.strip()) and quote in str(value)


def check_candidates(decision, incident, engagements):
    candidates = []
    seen_ids = set()
    for candidate in decision.candidates:
        eng_id = candidate.engagement_id
        records = [row for row in engagements if row["ENGAGEMENT_ID"] == eng_id]
        if not records or eng_id in seen_ids:
            raise ValueError("The model returned an unknown or repeated ENGAGEMENT_ID.")
        if not candidate.rationale.strip():
            raise ValueError("The model omitted a candidate rationale.")
        if not contains_quote(incident, candidate.incident_field, candidate.incident_quote):
            raise ValueError("An incident citation could not be verified.")
        if not any(contains_quote(row, candidate.engagement_field, candidate.engagement_quote) for row in records):
            raise ValueError("An engagement citation could not be verified.")

        rationale = (
            f"{candidate.rationale.strip()}\n"
            f'INC.{candidate.incident_field}: "{candidate.incident_quote}"\n'
            f'{eng_id}.{candidate.engagement_field}: "{candidate.engagement_quote}"'
        )
        candidates.append({"engagement_id": eng_id, "rationale": rationale})
        seen_ids.add(eng_id)
    return candidates


def check_decision(decision, incident, engagements):
    candidates = check_candidates(decision, incident, engagements)
    status = decision.link_decision
    selected = decision.selected_engagement_id
    if status == "LINKED":
        if not candidates or selected != candidates[0]["engagement_id"]:
            raise ValueError("A linked decision must select its first ranked engagement.")
    elif selected is not None:
        raise ValueError("An unresolved decision must leave the selection empty.")
    if status == "AMBIGUOUS" and len(candidates) < 2:
        raise ValueError("An ambiguous decision requires at least two plausible engagements.")
    if status == "NO_SUITABLE_CANDIDATE" and candidates:
        raise ValueError("An unsuitable candidate cannot appear on the shortlist.")
    if not decision.decision_reason.strip():
        raise ValueError("The model omitted its decision reason.")

    return {
        "link_decision": status,
        "selected_engagement_id": selected,
        "confidence": decision.confidence,
        "decision_reason": decision.decision_reason.strip(),
        "candidates": candidates,
    }
