from fastapi import APIRouter
from taq import __version__
from taq.api.schemas import HealthResponse

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(version=__version__)
