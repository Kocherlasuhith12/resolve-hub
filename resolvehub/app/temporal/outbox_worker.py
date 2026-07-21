import asyncio

from resolvehub.app.core.config import get_settings
from resolvehub.app.core.database import async_session_factory
from resolvehub.app.modules.notifications.service import process_outbox
from resolvehub.app.realtime.publisher import publish_json


async def run() -> None:
    settings = get_settings()
    while True:
        delivered = await process_outbox(
            async_session_factory, limit=settings.outbox_batch_size, publisher=publish_json
        )
        await asyncio.sleep(0.1 if delivered else 1.0)


if __name__ == "__main__":
    asyncio.run(run())
