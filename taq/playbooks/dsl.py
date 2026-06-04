from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml

from taq.core.exceptions import PlaybookError


class PlaybookDefinition:
    def __init__(self, name: str, version: str, description: str = "", trigger: dict | None = None, steps: list[dict] | None = None):
        self.name = name
        self.version = version
        self.description = description
        self.trigger = trigger or {}
        self.steps = steps or []

    def validate(self):
        if not self.name:
            raise PlaybookError("Playbook must have a name")
        if not self.steps:
            raise PlaybookError(f"Playbook '{self.name}' has no steps")
        for i, step in enumerate(self.steps):
            if "id" not in step:
                raise PlaybookError(f"Step {i} in '{self.name}' is missing 'id'")
            if "type" not in step:
                raise PlaybookError(f"Step '{step['id']}' in '{self.name}' is missing 'type'")

    def to_dict(self) -> dict:
        import hashlib
        return {
            "id": hashlib.md5(self.name.encode()).hexdigest()[:12],
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "trigger_type": self.trigger.get("type"),
            "accepts": self.trigger.get("accepts", []),
            "steps": self.steps,
        }


def parse_yaml(path: str | Path) -> PlaybookDefinition:
    path = Path(path)
    if not path.exists():
        raise PlaybookError(f"Playbook file not found: {path}")
    with open(path) as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise PlaybookError(f"Invalid YAML in {path}: {e}")
    if not isinstance(data, dict):
        raise PlaybookError(f"Playbook file must contain a mapping")
    pb = PlaybookDefinition(
        name=str(data.get("name", "")),
        version=str(data.get("version", "1.0")),
        description=str(data.get("description", "")),
        trigger=data.get("trigger", {}) or {},
        steps=data.get("steps", []) or [],
    )
    pb.validate()
    return pb


def parse_dict(data: dict) -> PlaybookDefinition:
    pb = PlaybookDefinition(
        name=str(data.get("name", "")),
        version=str(data.get("version", "1.0")),
        description=str(data.get("description", "")),
        trigger=data.get("trigger", {}) or {},
        steps=data.get("steps", []) or [],
    )
    pb.validate()
    return pb
