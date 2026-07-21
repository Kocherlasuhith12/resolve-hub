from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from resolvehub.app.core.config import get_settings
from resolvehub.app.core.database import Base
from resolvehub.app.modules.ai_assistance import models as ai_models  # noqa: F401
from resolvehub.app.modules.attachments import models as attachment_models  # noqa: F401
from resolvehub.app.modules.comments import models as comment_models  # noqa: F401
from resolvehub.app.modules.identity import models as identity_models  # noqa: F401
from resolvehub.app.modules.notifications import models as notification_models  # noqa: F401
from resolvehub.app.modules.organisations import models as organisation_models  # noqa: F401
from resolvehub.app.modules.service_catalogue import models as catalogue_models  # noqa: F401
from resolvehub.app.modules.sla import models as sla_models  # noqa: F401
from resolvehub.app.modules.tickets import models as ticket_models  # noqa: F401

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: object) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    import asyncio

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
