from unittest.mock import MagicMock
import uuid
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.database import get_db, GUID
from tests.conftest import test_engine, TestSessionLocal


@pytest.mark.asyncio
async def test_successful_database_connection():
    """Verifies that an async database connection can execute queries successfully."""
    async with test_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        scalar_val = result.scalar()
        assert scalar_val == 1


@pytest.mark.asyncio
async def test_failed_database_connection():
    """Verifies that connection failure to an invalid/unreachable database endpoint raises an error."""
    broken_engine = create_async_engine(
        "sqlite+aiosqlite:////non_existent_directory_travio_test/unreachable.db",
    )
    with pytest.raises(Exception):
        async with broken_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    await broken_engine.dispose()


@pytest.mark.asyncio
async def test_get_db_session_lifecycle_and_rollback(monkeypatch):
    """Verifies that get_db catches exceptions during route execution and calls rollback()."""
    rollback_called = False
    close_called = False

    original_rollback = AsyncSession.rollback
    original_close = AsyncSession.close

    async def mock_rollback(self):
        nonlocal rollback_called
        rollback_called = True
        await original_rollback(self)

    async def mock_close(self):
        nonlocal close_called
        close_called = True
        await original_close(self)

    monkeypatch.setattr(AsyncSession, "rollback", mock_rollback)
    monkeypatch.setattr(AsyncSession, "close", mock_close)
    monkeypatch.setattr("app.core.database.async_session_factory", TestSessionLocal)

    gen = get_db()
    session = await gen.asend(None)
    assert isinstance(session, AsyncSession)

    with pytest.raises(RuntimeError, match="Simulated error in DB transaction"):
        await gen.athrow(RuntimeError("Simulated error in DB transaction"))

    assert rollback_called is True
    assert close_called is True


def test_guid_type_decorator():
    """Verifies that GUID type decorator correctly handles UUID conversions across dialects."""
    guid_type = GUID()
    test_uuid = uuid.uuid4()

    pg_dialect = MagicMock()
    pg_dialect.name = "postgresql"

    sqlite_dialect = MagicMock()
    sqlite_dialect.name = "sqlite"

    # process_bind_param
    assert guid_type.process_bind_param(None, pg_dialect) is None
    assert guid_type.process_bind_param(test_uuid, pg_dialect) == str(test_uuid)
    assert guid_type.process_bind_param(test_uuid, sqlite_dialect) == str(test_uuid)

    # process_result_value
    assert guid_type.process_result_value(None, pg_dialect) is None
    assert guid_type.process_result_value(str(test_uuid), pg_dialect) == test_uuid
    assert guid_type.process_result_value(test_uuid, sqlite_dialect) == test_uuid
