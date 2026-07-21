import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from resolvehub.app.core.config import get_settings
from resolvehub.app.temporal.activities import record_sla_event
from resolvehub.app.temporal.workflows import TicketSlaWorkflow


async def run_worker() -> None:
    settings = get_settings()
    client = await Client.connect(settings.temporal_address, namespace=settings.temporal_namespace)
    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[TicketSlaWorkflow],
        activities=[record_sla_event],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
