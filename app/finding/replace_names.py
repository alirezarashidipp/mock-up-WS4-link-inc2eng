import yaml

from .clean_names import clean_name


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
        if name:
            name = replacements.get(name, name)
        updated.append((row, name))
    return updated
