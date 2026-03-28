import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources."""
    # Startup: initialize DB and Redis connections
    from src.db.redis import init_redis
    from src.db.session import init_db

    await init_db()
    await init_redis()

    # Start background scheduler for live data sync
    from src.api.services.scheduler import start_scheduler
    start_scheduler()

    yield

    # Shutdown: cleanup
    from src.api.services.scheduler import stop_scheduler
    from src.db.redis import close_redis

    stop_scheduler()
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    description="Fantasy Cricket Platform — Dream11 Clone",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        settings.API_BASE_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_request_timing(request: Request, call_next):
    start_time = time.time()
    response: Response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
    return response


# Health probes
@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    return {"status": "ready"}


# Register API routes
from src.api.routes import (
    admin,
    auth,
    contests,
    leaderboard,
    live,
    matches,
    players,
    scoring,
    settlements,
    teams,
    wallet,
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(matches.router, prefix="/api/matches", tags=["Matches"])
app.include_router(contests.router, prefix="/api/contests", tags=["Contests"])
app.include_router(teams.router, prefix="/api/teams", tags=["Teams"])
app.include_router(players.router, prefix="/api/players", tags=["Players"])
app.include_router(scoring.router, prefix="/api/scoring", tags=["Scoring"])
app.include_router(wallet.router, prefix="/api/wallet", tags=["Wallet"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["Leaderboard"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(live.router, prefix="/api/live", tags=["Live Data"])
app.include_router(settlements.router, prefix="/api/settlements", tags=["Settlements"])
