from dataclasses import dataclass
from datetime import datetime, timedelta

from temporalio import workflow


@dataclass
class SlaWorkflowInput:
    organisation_id: str
    ticket_id: str
    warning_at: datetime
    deadline: datetime


@workflow.defn
class TicketSlaWorkflow:
    def __init__(self) -> None:
        self.paused = False
        self.completed = False
        self.pause_started: datetime | None = None

    @workflow.signal
    async def pause(self) -> None:
        if not self.paused:
            self.paused = True
            self.pause_started = workflow.now()

    @workflow.signal
    async def resume(self) -> None:
        self.paused = False

    @workflow.signal
    async def complete(self) -> None:
        self.completed = True

    async def _wait_until(self, target: datetime) -> bool:
        while not self.completed:
            if self.paused:
                await workflow.wait_condition(lambda: not self.paused or self.completed)
                if self.pause_started is not None:
                    target += workflow.now() - self.pause_started
                    self.pause_started = None
                continue
            delay = target - workflow.now()
            if delay <= timedelta(0):
                return True
            try:
                await workflow.wait_condition(lambda: self.paused or self.completed, timeout=delay)
            except TimeoutError:
                return True
        return False

    @workflow.run
    async def run(self, value: SlaWorkflowInput) -> None:
        warning_due = await self._wait_until(value.warning_at)
        if warning_due and not self.completed:
            await workflow.execute_activity(
                "record_sla_event",
                args=[value.organisation_id, value.ticket_id, "SLA_WARNING"],
                start_to_close_timeout=timedelta(seconds=30),
            )
        breach_due = await self._wait_until(value.deadline)
        if breach_due and not self.completed:
            await workflow.execute_activity(
                "record_sla_event",
                args=[value.organisation_id, value.ticket_id, "SLA_BREACHED"],
                start_to_close_timeout=timedelta(seconds=30),
            )
