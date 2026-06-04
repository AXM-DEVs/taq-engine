from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import HTTPException, status
import time
import os
from taq import __version__, __app_name__
from taq.api.routes import health, investigations, playbooks, scoring, query, connectors, retro
from taq.api import auth

app = FastAPI(title=__app_name__, version=__version__, docs_url="/docs", redoc_url="/redoc")

# CORS middleware - restrict origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Replace with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware - prevent HTTP Host header attacks
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # TODO: Replace with specific hosts in production
)

# Custom middleware for request logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Log request details
    print(
        f"{request.client.host if request.client else 'unknown'} "
        f"\"{request.method} {request.url.path}\" "
        f"{response.status_code} "
        f"{process_time:.3f}s"
    )

    return response
app.include_router(auth.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(investigations.router, prefix="/api/v1")
app.include_router(playbooks.router, prefix="/api/v1")
app.include_router(scoring.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")
app.include_router(connectors.router, prefix="/api/v1")
app.include_router(retro.router, prefix="/api/v1")

# Mount static files
app.mount("/static", StaticFiles(directory="taq/static"), name="static")

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("taq/static/landing.html")

@app.get("/dashboard", include_in_schema=False)
async def dashboard():
    return FileResponse("taq/static/dashboard.html")

@app.get("/system", include_in_schema=False)
async def system():
    return FileResponse("taq/static/system.html")


@app.on_event("startup")
async def startup():
    from taq.storage.connection import init_database
    from taq.playbooks.registry import playbook_registry
    from pathlib import Path
    await init_database()
    # Load default playbooks
    playbook_dir = Path(__file__).parent.parent.parent / "playbooks"
    if playbook_dir.exists():
        playbook_registry.load_directory(playbook_dir)
    # Load user playbooks from user directories
    user_playbooks_dir = Path("./playbooks/user")
    if user_playbooks_dir.exists():
        for user_dir in user_playbooks_dir.iterdir():
            if user_dir.is_dir():
                playbook_registry.load_directory(user_dir)


@app.on_event("shutdown")
async def shutdown():
    from taq.storage.connection import close_database
    await close_database()
