from fastapi import APIRouter, Depends, HTTPException, status
from taq.api.schemas import PlaybookCreate, PlaybookResponse
from taq.playbooks.registry import playbook_registry
from taq.storage.models import UserModel, PlaybookModel
from taq.api.auth import get_current_user_required
from taq.storage.connection import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
from pathlib import Path
import yaml

router = APIRouter(prefix="/playbooks", tags=["playbooks"])

# Ensure user playbooks directory exists
USER_PLAYBOOKS_DIR = Path("./playbooks/user")
USER_PLAYBOOKS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("", response_model=PlaybookResponse, status_code=201)
async def register(body: PlaybookCreate, user: UserModel = Depends(get_current_user_required), session: AsyncSession = Depends(get_session)):
    # Enforce a limit on number of playbooks per user based on tier
    from taq.core.limiter import check_user_limit, LimitType
    # Get current count of playbooks for the user
    from sqlalchemy import select, func
    result = await session.execute(
        select(func.count(PlaybookModel.id)).where(PlaybookModel.user_id == user.id)
    )
    current_playbooks = result.scalar() or 0
    if not await check_user_limit(user, LimitType.PLAYBOOKS_PER_USER, current_playbooks, session):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Playbook limit exceeded. Your plan allows at most {get_playbooks_per_user_limit(user)} playbooks."
        )
    try:
        pb = playbook_registry.register_from_dict(body.model_dump())
        # Persist playbook to DB with user_id and is_public (default True for now)
        playbook_model = PlaybookModel(
            id=pb.id,
            name=pb.name,
            version=pb.version,
            description=pb.description,
            trigger_type=pb.trigger_type,
            accepts=pb.accepts,
            steps=pb.steps,
            user_id=user.id,  # associate with creator
            is_public=True    # default to public; could be made configurable
        )
        session.add(playbook_model)
        await session.commit()
        await session.refresh(playbook_model)

        # Also persist to YAML file for survival across restarts
        user_playbook_dir = USER_PLAYBOOKS_DIR / str(user.id)
        user_playbook_dir.mkdir(parents=True, exist_ok=True)
        yaml_file = user_playbook_dir / f"{pb.name}.yaml"
        playbook_data = {
            'name': pb.name,
            'version': pb.version,
            'description': pb.description,
            'trigger_type': pb.trigger_type,
            'accepts': pb.accepts,
            'steps': pb.steps
        }
        with open(yaml_file, 'w') as f:
            yaml.dump(playbook_data, f, default_flow_style=False)

        # Return combined data (registry data plus db fields)
        res = pb.to_dict()
        res.update({
            "created_at": playbook_model.created_at.isoformat(),
            "updated_at": playbook_model.updated_at.isoformat()
        })
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[PlaybookResponse])
async def list_pb(user: UserModel = Depends(get_current_user_required), session: AsyncSession = Depends(get_session)):
    # Get all playbooks from registry (in-memory)
    all_pbs = playbook_registry.list_playbooks()
    # Fetch from DB to get visibility and ownership
    from sqlalchemy import select
    result = await session.execute(select(PlaybookModel))
    db_playbooks = {pb.id: pb for pb in result.scalars()}
    # Build list with access control
    accessible = []
    for pb_dict in all_pbs:
        pb_id = pb_dict["id"]
        db_pb = db_playbooks.get(pb_id)
        if not db_pb:
            # Should not happen, but skip if missing
            continue
        # Check if public or belongs to user
        if db_pb.is_public or (db_pb.user_id == user.id):
            # Combine registry data with DB timestamps
            res = pb_dict.copy()
            res.update({
                "created_at": db_pb.created_at.isoformat(),
                "updated_at": db_pb.updated_at.isoformat()
            })
            accessible.append(res)
    return accessible


@router.get("/{pb_id}", response_model=PlaybookResponse)
async def get_pb(pb_id: str, user: UserModel = Depends(get_current_user_required), session: AsyncSession = Depends(get_session)):
    pb = playbook_registry.get(pb_id)
    if not pb:
        raise HTTPException(status_code=404, detail=f"Playbook '{pb_id}' not found")
    # Fetch from DB to check visibility
    result = await session.execute(select(PlaybookModel).where(PlaybookModel.id == pb_id))
    db_pb = result.scalar_one_or_none()
    if not db_pb:
        # Should not happen if registry and DB are in sync, but be safe
        raise HTTPException(status_code=404, detail=f"Playbook '{pb_id}' not found")
    # Check access: public or owned by user
    if not (db_pb.is_public or db_pb.user_id == user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions to access this playbook")
    # Combine registry data with DB timestamps
    res = pb.to_dict()
    res.update({
        "created_at": db_pb.created_at.isoformat(),
        "updated_at": db_pb.updated_at.isoformat()
    })
    return res


@router.get("/by-name/{name}", response_model=PlaybookResponse)
async def get_by_name(name: str, user: UserModel = Depends(get_current_user_required), session: AsyncSession = Depends(get_session)):
    pb = playbook_registry.get_by_name(name)
    if not pb:
        raise HTTPException(status_code=404, detail=f"Playbook '{name}' not found")
    # Fetch from DB to check visibility
    result = await session.execute(select(PlaybookModel).where(PlaybookModel.id == pb.id))
    db_pb = result.scalar_one_or_none()
    if not db_pb:
        raise HTTPException(status_code=404, detail=f"Playbook '{name}' not found")
    # Check access: public or owned by user
    if not (db_pb.is_public or db_pb.user_id == user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions to access this playbook")
    # Combine registry data with DB timestamps
    res = pb.to_dict()
    res.update({
        "created_at": db_pb.created_at.isoformat(),
        "updated_at": db_pb.updated_at.isoformat()
    })
    return res


@router.delete("/{pb_id}", status_code=204)
async def delete_pb(pb_id: str, user: UserModel = Depends(get_current_user_required), session: AsyncSession = Depends(get_session)):
    # Check if user owns the playbook before deleting
    result = await session.execute(select(PlaybookModel).where(PlaybookModel.id == pb_id))
    db_pb = result.scalar_one_or_none()
    if not db_pb:
        raise HTTPException(status_code=404, detail=f"Playbook '{pb_id}' not found")
    if db_pb.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions to delete this playbook")

    playbook_registry.delete(pb_id)
    await session.delete(db_pb)
    await session.commit()

    # Also delete YAML file if exists
    user_playbook_dir = USER_PLAYBOOKS_DIR / str(user.id)
    yaml_file = user_playbook_dir / f"{db_pb.name}.yaml"
    if yaml_file.exists():
        yaml_file.unlink()