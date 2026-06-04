import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, DateTime, Enum as SQLAEnum, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass



class EntityModel(Base):
    __tablename__ = "entities"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = Column(String(12), ForeignKey("investigations.id"), nullable=False)
    entity_type = Column(String(32), nullable=False)
    value = Column(String(512), nullable=False)
    source = Column(String(64), nullable=True)
    raw_data = Column(JSON, default=dict)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    investigation = relationship("InvestigationModel", back_populates="entities")


class ScoreModel(Base):
    __tablename__ = "scores"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = Column(String(12), ForeignKey("investigations.id"), nullable=False)
    entity_id = Column(String(36), ForeignKey("entities.id"), nullable=True)
    score_type = Column(String(32), nullable=False)
    value = Column(Float, nullable=False)
    factors = Column(JSON, default=dict)
    computed_at = Column(DateTime, default=datetime.utcnow)
    investigation = relationship("InvestigationModel", back_populates="scores")


class PlaybookModel(Base):
    __tablename__ = "playbooks"
    id = Column(String(12), primary_key=True)
    name = Column(String(128), unique=True, nullable=False)
    version = Column(String(16), nullable=False)
    description = Column(Text, nullable=True)
    trigger_type = Column(String(16), nullable=True)
    accepts = Column(JSON, default=list)
    steps = Column(JSON, nullable=False)
    # Optional: associate with a user for private playbooks
    user_id = Column(String(12), ForeignKey("users.id"), nullable=True)
    # If True, playbook is visible to everyone; if False, only visible to owner
    is_public = Column(Integer, default=1)  # 1 = public, 0 = private
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationship
    user = relationship("UserModel")


class UserTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"

    def __int__(self):
        return 0 if self == self.FREE else 1


class UserModel(Base):
    __tablename__ = "users"
    id = Column(String(12), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    tier = Column(SQLAEnum(UserTier), nullable=False, default=UserTier.FREE)
    is_active = Column(Integer, default=1)  # 1 = active, 0 = disabled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # For tracking daily limits
    investigations_today = Column(Integer, default=0)
    scoring_today = Column(Integer, default=0)
    queries_today = Column(Integer, default=0)
    last_reset_date = Column(DateTime, default=datetime.utcnow)
    # Hashed password for authentication
    hashed_password = Column(String(255), nullable=True)
    # Relationships
    investigations = relationship("InvestigationModel", back_populates="user", cascade="all, delete-orphan")


class InvestigationModel(Base):
    __tablename__ = "investigations"
    id = Column(String(12), primary_key=True)
    seed_type = Column(String(32), nullable=False)
    seed_value = Column(String(512), nullable=False)
    playbook_id = Column(String(128), nullable=True)
    user_id = Column(String(12), ForeignKey("users.id"), nullable=False)
    user_tier = Column(String(16), nullable=False)  # Store tier at time of creation for quick access without join
    status = Column(String(16), default="pending")
    metadata_json = Column(JSON, default=dict)
    results = Column(JSON, default=dict)
    errors = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    entities = relationship("EntityModel", back_populates="investigation", cascade="all, delete-orphan")
    scores = relationship("ScoreModel", back_populates="investigation", cascade="all, delete-orphan")
    user = relationship("UserModel", back_populates="investigations")


class ToolModel(Base):
    __tablename__ = "tools"
    id = Column(String(12), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(16), nullable=False)
    price = Column(Float, default=0.0)  # 0.0 for free tools
    tier_required = Column(SQLAEnum(UserTier), nullable=False, default=UserTier.FREE)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)