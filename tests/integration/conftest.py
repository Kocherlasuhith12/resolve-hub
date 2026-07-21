import os
import subprocess
import sys
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

TEST_DATABASE_URL = os.environ.get("RH_TEST_DATABASE_URL")

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    if not TEST_DATABASE_URL:
        pytest.skip("RH_TEST_DATABASE_URL is required for integration tests")
    env = os.environ.copy()
    env.update(
        RH_DATABASE_URL=TEST_DATABASE_URL,
        RH_ENVIRONMENT="test",
        RH_JWT_SECRET="integration-test-secret-at-least-32-characters",
    )
    subprocess.run(  # noqa: S603 -- sys.executable and every argument are trusted constants.
        [sys.executable, "-m", "alembic", "upgrade", "head"], check=True, env=env
    )


@pytest.fixture
async def client(migrated_database: None) -> AsyncIterator[AsyncClient]:
    assert TEST_DATABASE_URL
    os.environ.update(
        RH_DATABASE_URL=TEST_DATABASE_URL,
        RH_ENVIRONMENT="test",
        RH_JWT_SECRET="integration-test-secret-at-least-32-characters",
    )
    from resolvehub.app.core.database import get_db
    from resolvehub.app.main import app

    # pytest may use a different event loop between tests. Do not retain asyncpg
    # connections that are bound to a previous loop.
    test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_db() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as value:
        yield value
    app.dependency_overrides.clear()
    async with test_engine.begin() as connection:
        for table in reversed(
            __import__(
                "resolvehub.app.core.database", fromlist=["Base"]
            ).Base.metadata.sorted_tables
        ):
            await connection.execute(table.delete())
    await test_engine.dispose()
