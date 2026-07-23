import random
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resolvehub.app.modules.problems.models import Problem
from resolvehub.app.modules.problems.schemas import ProblemCreate, ProblemUpdate


class ProblemService:
    @staticmethod
    async def list_problems(
        session: AsyncSession, organisation_id: UUID, search: str | None = None
    ) -> list[Problem]:
        query = select(Problem).where(Problem.organisation_id == organisation_id)
        if search:
            query = query.where(
                Problem.title.ilike(f"%{search}%") | Problem.root_cause.ilike(f"%{search}%")
            )
        query = query.order_by(Problem.created_at.desc())
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create_problem(
        session: AsyncSession, organisation_id: UUID, payload: ProblemCreate
    ) -> Problem:
        number = f"PRB-{random.randint(1000, 9999)}"
        problem = Problem(
            organisation_id=organisation_id,
            problem_number=number,
            title=payload.title,
            category=payload.category,
            root_cause=payload.root_cause,
            workaround=payload.workaround,
            impacted_incidents_count=payload.impacted_incidents_count,
            status="Investigation",
        )
        session.add(problem)
        await session.commit()
        await session.refresh(problem)
        return problem

    @staticmethod
    async def update_problem(
        session: AsyncSession, organisation_id: UUID, problem_id: UUID, payload: ProblemUpdate
    ) -> Problem | None:
        query = select(Problem).where(
            Problem.id == problem_id, Problem.organisation_id == organisation_id
        )
        result = await session.execute(query)
        problem = result.scalar_one_or_none()
        if not problem:
            return None

        if payload.title is not None:
            problem.title = payload.title
        if payload.category is not None:
            problem.category = payload.category
        if payload.status is not None:
            problem.status = payload.status
        if payload.root_cause is not None:
            problem.root_cause = payload.root_cause
        if payload.workaround is not None:
            problem.workaround = payload.workaround
        if payload.impacted_incidents_count is not None:
            problem.impacted_incidents_count = payload.impacted_incidents_count

        await session.commit()
        await session.refresh(problem)
        return problem
