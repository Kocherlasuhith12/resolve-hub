import asyncio
from datetime import timedelta

from sqlalchemy import select
from temporalio.client import Client, WorkflowHandle
from temporalio.common import WorkflowIDConflictPolicy

from resolvehub.app.core.config import get_settings
from resolvehub.app.core.database import async_session_factory
from resolvehub.app.modules.sla.models import SlaPolicy, TicketSla
from resolvehub.app.modules.tickets.enums import SlaState
from resolvehub.app.temporal.workflows import SlaWorkflowInput, TicketSlaWorkflow


async def synchronize(client: Client) -> int:
    synchronized = 0
    async with async_session_factory() as session:
        executions = list(
            await session.scalars(
                select(TicketSla)
                .where(
                    TicketSla.state.in_(
                        [SlaState.ACTIVE, SlaState.PAUSED, SlaState.WARNING, SlaState.COMPLETED]
                    )
                )
                .order_by(TicketSla.created_at)
                .limit(200)
            )
        )
        for execution in executions:
            policy = await session.get(SlaPolicy, execution.policy_id)
            if policy is None:
                continue
            elapsed = execution.resolution_deadline - execution.started_at
            warning_at = execution.started_at + elapsed * (policy.warning_percent / 100)
            handle: WorkflowHandle[TicketSlaWorkflow, None] = await client.start_workflow(
                TicketSlaWorkflow.run,
                SlaWorkflowInput(
                    organisation_id=str(execution.organisation_id),
                    ticket_id=str(execution.ticket_id),
                    warning_at=warning_at,
                    deadline=execution.resolution_deadline,
                ),
                id=execution.workflow_id,
                task_queue=get_settings().temporal_task_queue,
                id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
                execution_timeout=timedelta(days=3660),
            )
            desired = execution.state.value
            synced = execution.workflow_metadata.get("synced_state")
            if desired != synced:
                if execution.state == SlaState.PAUSED:
                    await handle.signal(TicketSlaWorkflow.pause)
                elif execution.state == SlaState.COMPLETED:
                    await handle.signal(TicketSlaWorkflow.complete)
                elif synced == SlaState.PAUSED.value:
                    await handle.signal(TicketSlaWorkflow.resume)
                execution.workflow_metadata = {
                    **execution.workflow_metadata,
                    "synced_state": desired,
                }
            synchronized += 1
        await session.commit()
    return synchronized


async def run() -> None:
    settings = get_settings()
    client = await Client.connect(settings.temporal_address, namespace=settings.temporal_namespace)
    while True:
        await synchronize(client)
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(run())
