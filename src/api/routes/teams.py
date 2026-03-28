"""Team routes: create, edit, view."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.dependencies.auth import get_current_user
from src.api.exceptions import NotFoundException
from src.api.schemas.common import APIResponse
from src.api.services import team as team_service
from src.db.models.models import Team, User
from src.db.session import get_session

router = APIRouter()


class TeamResponse(BaseModel):
    id: int
    user_id: int
    match_id: int
    name: str
    captain_id: int
    vice_captain_id: int
    total_credits: float
    total_points: float
    model_config = {"from_attributes": True}


class TeamListResponse(BaseModel):
    teams: list[TeamResponse]


class CreateTeamRequest(BaseModel):
    match_id: int
    name: str = "Team 1"
    captain_id: int
    vice_captain_id: int
    player_ids: list[int]


@router.get("", response_model=APIResponse[TeamListResponse])
async def list_teams(
    match_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Team).where(Team.user_id == current_user.id, Team.match_id == match_id)
    )
    teams = result.scalars().all()
    return APIResponse(success=True, message="Teams fetched",
                       data=TeamListResponse(teams=[TeamResponse.model_validate(t) for t in teams]))


@router.post("", response_model=APIResponse[TeamResponse], status_code=201)
async def create_team(
    body: CreateTeamRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    team = await team_service.create_team(
        session, current_user.id, body.match_id, body.player_ids,
        body.captain_id, body.vice_captain_id, body.name,
    )
    return APIResponse(success=True, message="Team created",
                       data=TeamResponse.model_validate(team))


@router.get("/{team_id}", response_model=APIResponse[TeamResponse])
async def get_team(
    team_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(Team).where(Team.id == team_id))
    team = result.scalars().first()
    if not team:
        raise NotFoundException("Team not found")
    return APIResponse(success=True, message="Team fetched",
                       data=TeamResponse.model_validate(team))
