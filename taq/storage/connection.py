from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import create_engine
from taq.core.config import config
from taq.storage.models import Base

_engine = None
_sync_engine = None
_factory = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(config.db.dsn, echo=config.debug)
    return _engine

def get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(config.db.dsn_sync, echo=config.debug)
    return _sync_engine

def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _factory
    if _factory is None:
        _factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _factory

async def get_session() -> AsyncSession:
    """Dependency that returns an async SQLAlchemy session."""
    async with get_session_factory()() as session:
        yield session

async def init_database():
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Base.metadata.create_all(get_sync_engine())

async def close_database():
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
