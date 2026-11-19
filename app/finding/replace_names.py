import yaml

from .clean_incidents import clean_name


def read_replacements(path):
    with path.open(encoding="utf-8-sig") as stream:
        entries = yaml.safe_load(stream) or {}
    replacements = {}
    for original, replacement in entries.items():
        name = clean_name(original)
        replacements[name] = clean_name(replacement)
    return replacements


def replace_incident_names(incidents, replacements):
    updated = []
    for row, name in incidents:
        search_name = replacements.get(name, name)
        updated.append((row, search_name))
    return updated
