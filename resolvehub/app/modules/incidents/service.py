import random
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resolvehub.app.modules.incidents.models import Incident
from resolvehub.app.modules.incidents.schemas import IncidentCreate, IncidentUpdate


class IncidentService:
    @staticmethod
    async def list_incidents(
        session: AsyncSession, organisation_id: UUID, severity: str | None = None
    ) -> list[Incident]:
        query = select(Incident).where(Incident.organisation_id == organisation_id)
        if severity and severity != "ALL":
            query = query.where(Incident.severity.contains(severity))
        query = query.order_by(Incident.created_at.desc())
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create_incident(
        session: AsyncSession, organisation_id: UUID, payload: IncidentCreate
    ) -> Incident:
        number = f"INC-2026-{random.randint(100, 999)}"
        incident = Incident(
            organisation_id=organisation_id,
            incident_number=number,
            title=payload.title,
            description=payload.description,
            severity=payload.severity,
            service_name=payload.service_name,
            commander_name=payload.commander_name,
            impact_summary=payload.impact_summary,
            status="Investigating",
        )
        session.add(incident)
        await session.commit()
        await session.refresh(incident)
        return incident

    @staticmethod
    async def update_incident(
        session: AsyncSession, organisation_id: UUID, incident_id: UUID, payload: IncidentUpdate
    ) -> Incident | None:
        query = select(Incident).where(
            Incident.id == incident_id, Incident.organisation_id == organisation_id
        )
        result = await session.execute(query)
        incident = result.scalar_one_or_none()
        if not incident:
            return None

        if payload.title is not None:
            incident.title = payload.title
        if payload.description is not None:
            incident.description = payload.description
        if payload.severity is not None:
            incident.severity = payload.severity
        if payload.status is not None:
            incident.status = payload.status
            if payload.status == "Resolved" and not incident.resolved_at:
                incident.resolved_at = datetime.now(UTC)
        if payload.commander_name is not None:
            incident.commander_name = payload.commander_name
        if payload.impact_summary is not None:
            incident.impact_summary = payload.impact_summary

        await session.commit()
        await session.refresh(incident)
        return incident
