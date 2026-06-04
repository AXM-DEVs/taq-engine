from fastapi import APIRouter, Depends, HTTPException, Query, status
from taq.query.parser import parse
from taq.query.translator import translate
# We'll add limiter usage later if needed
from taq.storage.models import UserModel
from taq.api.auth import get_current_user_required
from taq.storage.connection import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/query", tags=["query"])

@router.get("/parse")
async def parse_query(q: str = Query(..., description="Natural language query"), user: UserModel = Depends(get_current_user_required), session: AsyncSession = Depends(get_session)):
    # Apply rate limiting for queries per day
    from taq.core.limiter import check_and_increment_queries_limit
    if not await check_and_increment_queries_limit(user, session):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily query limit exceeded"
        )
    p = parse(q)
    return {"raw": q, "intent": p.intent.value, "entity_type": p.entity_type, "entity_value": p.entity_value, "filters": p.filters, "limit": p.limit}

@router.get("/translate")
async def translate_query(q: str = Query(...), target: str = Query("sql"), user: UserModel = Depends(get_current_user_required), session: AsyncSession = Depends(get_session)):
    # Apply rate limiting
    from taq.core.limiter import check_and_increment_queries_limit
    if not await check_and_increment_queries_limit(user, session):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily query limit exceeded"
        )
    try:
        return {"raw": q, "intent": parse(q).intent.value, "target": target, "query": translate(parse(q), target)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
