import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text

from src.config import settings
from src.logging_config import request_id_ctx, setup_logging

logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources."""
    # Structured logging
    setup_logging()

    logger.info("Starting %s...", settings.APP_NAME)

    # Sentry error tracking
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk

            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.ENVIRONMENT,
                traces_sample_rate=0.1,
            )
            logger.info("Sentry initialized for environment: %s", settings.ENVIRONMENT)
        except Exception:
            logger.exception("Failed to initialize Sentry")

    # Initialize DB and Redis
    from src.db.redis import init_redis
    from src.db.session import init_db

    await init_db()
    await init_redis()

    # Start background scheduler for live data sync
    from src.api.services.scheduler import start_scheduler

    start_scheduler()

    yield

    # Shutdown
    from src.api.services.scheduler import stop_scheduler
    from src.db.redis import close_redis

    stop_scheduler()
    await close_redis()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description="Fantasy Cricket Platform — Dream11 Clone",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# CORS — must be first middleware
# ---------------------------------------------------------------------------
cors_origins: list[str] = [settings.FRONTEND_URL]
if settings.DEBUG:
    cors_origins.extend(
        [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
        ]
    )
# Deduplicate while preserving order
cors_origins = list(dict.fromkeys(cors_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


# ---------------------------------------------------------------------------
# Security headers middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ---------------------------------------------------------------------------
# Request ID middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    token = request_id_ctx.set(rid)
    try:
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response
    finally:
        request_id_ctx.reset(token)


# ---------------------------------------------------------------------------
# Request timing middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def request_timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    response: Response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
    return response


# ---------------------------------------------------------------------------
# Health probes
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    """Liveness probe — always returns 200 if the process is alive."""
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    """Readiness probe — checks DB and Redis connectivity."""
    from src.db.redis import get_redis
    from src.db.session import async_session

    checks: dict[str, str] = {}

    # Database check
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        logger.error("Readiness: database check failed: %s", exc)
        checks["database"] = f"error: {exc}"

    # Redis check
    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        logger.error("Readiness: redis check failed: %s", exc)
        checks["redis"] = f"error: {exc}"

    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ready" if all_ok else "degraded", "checks": checks},
    )


# ---------------------------------------------------------------------------
# Register API routes
# ---------------------------------------------------------------------------
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
