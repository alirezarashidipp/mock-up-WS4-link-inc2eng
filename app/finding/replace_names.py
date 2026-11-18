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


def replace_supplier_names(suppliers, replacements):
    updated = []
    for row, names in suppliers:
        search_names = {}
        for column, name in names.items():
            search_names[column] = replacements.get(name, name)
        updated.append((row, search_names))
    return updated
