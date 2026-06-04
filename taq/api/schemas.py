from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    app: str = "TaQ Engine"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class InvestigationCreate(BaseModel):
    seed_type: str; seed_value: str; playbook_id: str | None = None; metadata: dict = Field(default_factory=dict)

class InvestigationResponse(BaseModel):
    id: str; seed_type: str; seed_value: str; playbook_id: str | None = None; status: str
    metadata: dict = Field(default_factory=dict); results: dict = Field(default_factory=dict)
    errors: list = Field(default_factory=list); created_at: str; updated_at: str

class InvestigationListResponse(BaseModel):
    total: int; investigations: list[InvestigationResponse]; limit: int; offset: int

class PlaybookCreate(BaseModel):
    name: str; version: str = "1.0"; description: str | None = None
    trigger_type: str | None = None; accepts: list[str] = Field(default_factory=list)
    steps: list[dict] = Field(default_factory=list)

class PlaybookResponse(BaseModel):
    id: str; name: str; version: str; description: str | None = None
    trigger_type: str | None = None; accepts: list[str] = Field(default_factory=list)
    steps: list[dict] = Field(default_factory=list); created_at: str; updated_at: str

class ScoreRequest(BaseModel):
    entity_id: str; score_type: str = "threat"; factors: dict[str, float] = Field(default_factory=dict)

class ScoreResponse(BaseModel):
    id: str; investigation_id: str; entity_id: str | None = None
    score_type: str; value: float; factors: dict = Field(default_factory=dict); computed_at: str
