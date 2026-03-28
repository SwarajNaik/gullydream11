import ssl

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from src.config import settings

# Strip query params that asyncpg doesn't understand (sslmode, ssl, channel_binding)
db_url = settings.DATABASE_URL.split("?")[0]

# Build connect_args for SSL if needed (Neon requires SSL)
connect_args = {}
if "neon.tech" in settings.DATABASE_URL:
    ssl_context = ssl.create_default_context()
    connect_args["ssl"] = ssl_context

engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args=connect_args,
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database — create tables if needed."""
    from src.db.models import __all_models__  # noqa: F401


async def get_session():
    """Dependency: yield an async database session."""
    async with async_session() as session:
        yield session
