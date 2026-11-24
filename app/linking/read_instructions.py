from pathlib import Path

import yaml

from .fields import ENGAGEMENT_FIELDS, INCIDENT_FIELDS


CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def read_prompt(path):
    with path.open(encoding="utf-8-sig") as stream:
        settings = yaml.safe_load(stream)
    prompt = settings.get("system_prompt") if isinstance(settings, dict) else None
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError(f"{path.name} requires a nonblank system_prompt.")
    return prompt


def read_definitions(config_dir=CONFIG_DIR):
    definitions = {}
    for source, fields in (("incident", INCIDENT_FIELDS), ("engagement", ENGAGEMENT_FIELDS)):
        path = config_dir / f"{source}_columns.yml"
        with path.open(encoding="utf-8-sig") as stream:
            available = yaml.safe_load(stream)["definitions"]
        definitions[source] = {field: available[field] for field in fields}
    return definitions
