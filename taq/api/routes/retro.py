from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from taq.storage.models import UserModel
from taq.api.auth import get_current_user_required
from taq.storage.connection import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/retro", tags=["retro"])


class IngestRequest(BaseModel):
    event_type: str
    source_ip: str
    source_port: int | None = None
    dest_port: int | None = None
    protocol: str = "tcp"
    payload: str | None = None
    user_agent: str | None = None
    username: str | None = None
    timestamp: str | None = None


class CountermeasureRequest(BaseModel):
    action: str
    target: str
    target_type: str = "ip"
    auto_approve: bool = False


class IngestResponse(BaseModel):
    status: str
    investigation_id: str | None = None
    threat_score: float = 0.0


@router.post("/ingest", response_model=IngestResponse)
async def ingest_event(body: IngestRequest, user: UserModel = Depends(get_current_user_required), session: AsyncSession = Depends(get_session)):
    # Check daily investigation limit before creating
    from taq.core.limiter import check_and_increment_daily_limit
    if not await check_and_increment_daily_limit(user, session):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily investigation limit exceeded"
        )
    from taq.core.engine import engine
    inv = await engine.create_investigation(
        seed_type="ip",
        seed_value=body.source_ip,
        playbook_id="ip_full_investigation",
        metadata=body.model_dump(),
        user_id=user.id
    )
    return IngestResponse(status="received", investigation_id=inv.id)


@router.post("/countermeasure")
async def execute_countermeasure(body: CountermeasureRequest, user: UserModel = Depends(get_current_user_required)):
    from taq.connectors.registry import connector_registry
    from taq.storage.models import UserTier
    # Check if the action is report_abuse and if user is premium
    if body.action == "report_abuse":
        if user.tier != UserTier.PREMIUM:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only premium users can perform this action"
            )
        if body.target_type == "ip":
            abuse = connector_registry.get("abuseipdb")
            if abuse:
                result = await abuse.call("report", {"ip": body.target, "comment": "Reported by Retro"})
                return {"status": "executed", "result": result.to_dict()}
    return {"status": "not_implemented", "action": body.action}
