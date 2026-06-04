from fastapi import APIRouter, Depends, HTTPException, status
from taq.api.schemas import InvestigationCreate, InvestigationResponse, InvestigationListResponse
from taq.core.engine import engine
from taq.core.limiter import (
    check_user_limit,
    LimitType,
    get_investigations_per_day_limit,
    get_connectors_per_investigation_limit,
    get_playbook_steps_limit
)
from taq.utils.serialization import serialize_investigation
from taq.connectors.registry import connector_registry
from taq.storage.models import UserModel
from taq.api.auth import get_current_user_optional, get_current_user_required
from taq.storage.connection import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/investigations", tags=["investigations"])

@router.post("", response_model=InvestigationResponse, status_code=201)
async def create(body: InvestigationCreate, user: UserModel = Depends(get_current_user_required), session: AsyncSession = Depends(get_session)):
    # Check daily investigation limit
    from taq.core.limiter import check_and_increment_daily_limit
    if not await check_and_increment_daily_limit(user, session):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily investigation limit exceeded"
        )

    inv = await engine.create_investigation(
        seed_type=body.seed_type,
        seed_value=body.seed_value,
        playbook_id=body.playbook_id,
        metadata=body.metadata,
        user_id=user.id,
        user_tier=user.tier.value
    )
    return serialize_investigation(inv)

@router.get("", response_model=InvestigationListResponse)
async def list_inv(status: str | None = None, limit: int = 50, offset: int = 0, user: UserModel = Depends(get_current_user_required), session: AsyncSession = Depends(get_session)):
    invs = await engine.list_investigations(status=status, limit=limit, user_id=user.id)
    # Apply pagination manually since engine.list_investigations currently does limit but not offset?
    # We'll keep simple: engine returns limited list; we can slice for offset if needed.
    # For now, ignore offset (or implement)
    # Let's just slice:
    start = offset
    end = offset + limit
    paginated = invs[start:end]
    return InvestigationListResponse(total=len(invs), investigations=[serialize_investigation(i) for i in paginated], limit=limit, offset=offset)

@router.get("/{inv_id}", response_model=InvestigationResponse)
async def get_inv(inv_id: str, user: UserModel = Depends(get_current_user_required), session: AsyncSession = Depends(get_session)):
    inv = await engine.get_investigation(inv_id, user_id=user.id)
    return serialize_investigation(inv)

@router.post("/{inv_id}/run", response_model=InvestigationResponse)
async def run_inv(inv_id: str, user: UserModel = Depends(get_current_user_required), session: AsyncSession = Depends(get_session)):
    # First, fetch the investigation to ensure it belongs to the user
    inv = await engine.get_investigation(inv_id, user_id=user.id)
    # If there is a playbook_id, check limits before running
    if inv.playbook_id:
        # Import playbook registry to get playbook definition
        from taq.playbooks.registry import playbook_registry
        pb = playbook_registry.get(inv.playbook_id)
        if pb is None:
            raise HTTPException(status_code=404, detail=f"Playbook '{inv.playbook_id}' not found")
        # Count steps and connector calls
        total_steps = len(pb.steps)
        connector_calls = sum(1 for step in pb.steps if step.get("type") == "connector_call")
        # Get user limits
        max_steps = get_playbook_steps_limit(user)
        max_connectors = get_connectors_per_investigation_limit(user)
        if total_steps > max_steps:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Playbook has {total_steps} steps, but your plan allows at most {max_steps} steps per playbook."
            )
        if connector_calls > max_connectors:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Playbook uses {connector_calls} connector calls, but your plan allows at most {max_connectors} connectors per investigation."
            )
    # Run the investigation
    try:
        inv = await engine.run_investigation(inv_id)
        return serialize_investigation(inv)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
