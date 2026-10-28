import uuid
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator
import jwt
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.config import settings
from app.core.database import Base, get_db

TEST_JWT_SECRET = "test-secret-super-secure-key-1234567890"

# Configure settings for tests
settings.SUPABASE_JWT_SECRET = TEST_JWT_SECRET
settings.SUPABASE_AUDIENCE = "authenticated"
settings.SUPABASE_URL = "https://test.supabase.co"

# Isolated test engine (SQLite in-memory with static pool)
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_test_database():
    """Initializes tables before tests and drops them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


def create_test_jwt(
    user_id: uuid.UUID,
    email: str = "testuser@travio.local",
    secret: str = TEST_JWT_SECRET,
    algorithm: str = "HS256",
    expires_in_minutes: int = 60,
    audience: str = "authenticated",
    issuer: str = "https://test.supabase.co/auth/v1",
    extra_claims: dict = None,
) -> str:
    """Helper to generate mock Supabase access tokens."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "aud": audience,
        "iss": issuer,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_in_minutes)).timestamp()),
        "user_metadata": {
            "full_name": "Test User",
        },
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, secret, algorithm=algorithm)


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session
