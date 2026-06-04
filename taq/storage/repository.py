from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from taq.storage.models import InvestigationModel, EntityModel, ScoreModel, PlaybookModel


class Repository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_investigation(self, inv: InvestigationModel) -> InvestigationModel:
        self.session.add(inv); await self.session.commit(); return inv

    async def get_investigation(self, id: str) -> Optional[InvestigationModel]:
        r = await self.session.execute(select(InvestigationModel).where(InvestigationModel.id == id))
        return r.scalar_one_or_none()

    async def list_investigations(self, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> list[InvestigationModel]:
        q = select(InvestigationModel)
        if status: q = q.where(InvestigationModel.status == status)
        q = q.order_by(InvestigationModel.created_at.desc()).limit(limit).offset(offset)
        return list((await self.session.execute(q)).scalars().all())

    async def count_investigations(self, status: Optional[str] = None) -> int:
        q = select(func.count(InvestigationModel.id))
        if status: q = q.where(InvestigationModel.status == status)
        return (await self.session.execute(q)).scalar() or 0

    async def save_entity(self, e: EntityModel) -> EntityModel:
        self.session.add(e); await self.session.commit(); return e

    async def save_score(self, s: ScoreModel) -> ScoreModel:
        self.session.add(s); await self.session.commit(); return s

    async def save_playbook(self, p: PlaybookModel) -> PlaybookModel:
        self.session.add(p); await self.session.commit(); return p

    async def get_playbook(self, id: str) -> Optional[PlaybookModel]:
        r = await self.session.execute(select(PlaybookModel).where(PlaybookModel.id == id))
        return r.scalar_one_or_none()

    async def list_playbooks(self) -> list[PlaybookModel]:
        r = await self.session.execute(select(PlaybookModel).order_by(PlaybookModel.created_at.desc()))
        return list(r.scalars().all())
