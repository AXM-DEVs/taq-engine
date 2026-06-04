from __future__ import annotations

from pathlib import Path
from typing import Optional

from taq.playbooks.dsl import parse_yaml, parse_dict, PlaybookDefinition


class Playbook:
    def __init__(self, playbook_id: str, name: str, version: str, description: str = "", trigger_type: str | None = None, accepts: list[str] | None = None, steps: list[dict] | None = None):
        self.id = playbook_id
        self.name = name
        self.version = version
        self.description = description
        self.trigger_type = trigger_type
        self.accepts = accepts or []
        self.steps = steps or []

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "version": self.version,
            "description": self.description, "trigger_type": self.trigger_type,
            "accepts": self.accepts, "steps": self.steps,
            "created_at": "", "updated_at": "",
        }


class PlaybookRegistry:
    def __init__(self):
        self._playbooks: dict[str, Playbook] = {}
        self._names: dict[str, str] = {}

    def register(self, playbook: Playbook):
        self._playbooks[playbook.id] = playbook
        self._names[playbook.name] = playbook.id

    def register_from_dict(self, data: dict) -> Playbook:
        import hashlib
        pb_def = parse_dict(data)
        pb = Playbook(
            playbook_id=hashlib.md5(pb_def.name.encode()).hexdigest()[:12],
            name=pb_def.name, version=pb_def.version,
            description=pb_def.description, trigger_type=pb_def.trigger.get("type"),
            accepts=pb_def.trigger.get("accepts", []), steps=pb_def.steps,
        )
        self.register(pb)
        return pb

    def register_from_yaml(self, path: str | Path) -> Playbook:
        pb_def = parse_yaml(path)
        return self.register_from_dict(pb_def.to_dict())

    def load_directory(self, path: str | Path):
        path = Path(path)
        if not path.exists():
            return
        for yaml_file in path.glob("*.yaml"):
            try:
                self.register_from_yaml(yaml_file)
            except Exception as e:
                import logging
                logging.warning(f"Failed to load playbook {yaml_file}: {e}")

    def get(self, playbook_id: str) -> Optional[Playbook]:
        return self._playbooks.get(playbook_id)

    def get_by_name(self, name: str) -> Optional[Playbook]:
        pid = self._names.get(name)
        return self._playbooks.get(pid) if pid else None

    def list_playbooks(self) -> list[dict]:
        return [pb.to_dict() for pb in self._playbooks.values()]

    def delete(self, playbook_id: str):
        pb = self._playbooks.pop(playbook_id, None)
        if pb:
            self._names.pop(pb.name, None)


playbook_registry = PlaybookRegistry()
