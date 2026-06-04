from fastapi import APIRouter, Depends, HTTPException, status
from taq.api.schemas import ScoreRequest, ScoreResponse
from taq.scoring.score import compute_threat_score
from taq.core.limiter import check_user_limit, LimitType
from taq.storage.models import UserModel
from taq.api.auth import get_current_user_required
from taq.storage.connection import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/scoring", tags=["scoring"])

@router.post("/compute", response_model=ScoreResponse)
async def compute(body: ScoreRequest, user: UserModel = Depends(get_current_user_required), session: AsyncSession = Depends(get_session)):
    # Check and increment scoring limit per day
    from taq.core.limiter import check_and_increment_scoring_limit
    if not await check_and_increment_scoring_limit(user, session):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily scoring limit exceeded"
        )
    r = await compute_threat_score(entity_id=body.entity_id, score_type=body.score_type, overrides=body.factors if body.factors else None)
    return ScoreResponse(**r)
