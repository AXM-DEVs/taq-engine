from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from taq.core.config import config
from taq.core.exceptions import TaqError
from taq.utils.logger import get_logger

logger = get_logger(__name__)


class Investigation:
    def __init__(self, seed_type: str, seed_value: str, playbook_id: Optional[str] = None, metadata: Optional[dict] = None, user_id: Optional[str] = None):
        self.id: str = uuid4().hex[:12]
        self.seed_type = seed_type
        self.seed_value = seed_value
        self.playbook_id = playbook_id
        self.metadata = metadata or {}
        self.status: str = "pending"
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()
        self.results: dict = {}
        self.errors: list[str] = []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "seed_type": self.seed_type,
            "seed_value": self.seed_value,
            "playbook_id": self.playbook_id,
            "metadata": self.metadata,
            "status": self.status,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "results": self.results,
            "errors": self.errors,
        }


class TaqEngine:
    def __init__(self):
        self._active: dict[str, Investigation] = {}

    async def create_investigation(self, seed_type: str, seed_value: str, playbook_id: Optional[str] = None, metadata: Optional[dict] = None, user_id: Optional[str] = None, user_tier: Optional[str] = None) -> Investigation:
        inv = Investigation(seed_type, seed_value, playbook_id, metadata, user_id, user_tier)
        self._active[inv.id] = inv
        logger.info(f"Investigation created: {inv.id} ({seed_type}: {seed_value})")
        return inv

    async def get_investigation(self, investigation_id: str, user_id: Optional[str] = None) -> Investigation:
        inv = self._active.get(investigation_id)
        if not inv:
            raise TaqError(f"Investigation {investigation_id} not found")
        if user_id is not None and inv.user_id != user_id:
            raise TaqError(f"Investigation {investigation_id} not found")
        return inv

    async def list_investigations(self, status: Optional[str] = None, limit: int = 50, offset: int = 0, user_id: Optional[str] = None) -> list[Investigation]:
        invs = list(self._active.values())
        if user_id is not None:
            invs = [i for i in invs if i.user_id == user_id]
        if status:
            invs = [i for i in invs if i.status == status]
        # apply offset and limit
        return invs[offset:offset + limit]

    async def run_investigation(self, investigation_id: str) -> Investigation:
        inv = await self.get_investigation(investigation_id)
        inv.status = "running"
        inv.updated_at = datetime.utcnow()
        logger.info(f"Investigation started: {investigation_id}")
        try:
            if inv.playbook_id:
                from taq.playbooks.executor import PlaybookExecutor
                executor = PlaybookExecutor()
                result = await executor.execute(inv.playbook_id, inv)
                inv.results = result
            inv.status = "completed"
        except TaqError as e:
            inv.status = "failed"
            inv.errors.append(str(e))
            logger.error(f"Investigation failed: {investigation_id}: {e}")
        except Exception as e:
            inv.status = "failed"
            inv.errors.append(f"Unexpected error: {e}")
            logger.error(f"Investigation failed: {investigation_id}: {e}")
        inv.updated_at = datetime.utcnow()
        return inv

    async def run_multi_investigation(self, seeds: list[tuple[str, str]], playbook_id: str) -> dict[str, Investigation]:
        tasks = []
        for seed_type, seed_value in seeds:
            inv = await self.create_investigation(seed_type, seed_value, playbook_id)
            tasks.append(self.run_investigation(inv.id))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {inv.id: inv for inv in results if isinstance(inv, Investigation)}


engine = TaqEngine()
