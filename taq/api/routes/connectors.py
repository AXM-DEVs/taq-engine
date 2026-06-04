from fastapi import APIRouter, Depends, HTTPException, status
from taq.connectors.registry import connector_registry
from taq.storage.models import UserModel
from taq.api.auth import get_current_user_required
from taq.storage.connection import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/connectors", tags=["connectors"])


@router.get("")
async def list_connectors(user: UserModel = Depends(get_current_user_required)):
    all_connectors = connector_registry.list()
    if user.tier == UserTier.FREE:
        # Filter out connectors that are not free (i.e., those that do not have '_free' in their name)
        # Assuming free connectors have '_free' in their name (case-insensitive)
        free_connectors = [name for name in all_connectors if '_free' in name.lower()]
        return {"connectors": free_connectors}
    else:
        # Premium users get all connectors
        return {"connectors": all_connectors}


@router.get("/{name}/health")
async def connector_health(name: str, user: UserModel = Depends(get_current_user_required)):
    try:
        result = await connector_registry.health(name)
        return {"connector": name, "status": "ok", "data": result}
    except Exception as e:
        return {"connector": name, "status": "error", "error": str(e)}
