from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from resolvehub.app.core.dependencies import DbSession
from resolvehub.app.modules.problems.schemas import ProblemCreate, ProblemResponse, ProblemUpdate
from resolvehub.app.modules.problems.service import ProblemService

router = APIRouter(prefix="/organisations/{organisation_id}/problems", tags=["problems"])


@router.get("", response_model=list[ProblemResponse])
async def list_problems(
    organisation_id: UUID,
    session: DbSession,
    search: str | None = None,
):
    return await ProblemService.list_problems(session, organisation_id, search)


@router.post("", response_model=ProblemResponse, status_code=status.HTTP_201_CREATED)
async def create_problem(
    organisation_id: UUID,
    payload: ProblemCreate,
    session: DbSession,
):
    return await ProblemService.create_problem(session, organisation_id, payload)


@router.patch("/{problem_id}", response_model=ProblemResponse)
async def update_problem(
    organisation_id: UUID,
    problem_id: UUID,
    payload: ProblemUpdate,
    session: DbSession,
):
    updated = await ProblemService.update_problem(session, organisation_id, problem_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Problem not found")
    return updated
