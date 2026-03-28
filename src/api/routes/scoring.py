"""Scoring routes: admin score entry and finalization."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import require_admin
from src.api.schemas.common import APIResponse
from src.api.services import scoring as scoring_service
from src.db.models.models import User
from src.db.session import get_session

router = APIRouter()


class PlayerScoreInput(BaseModel):
    match_player_id: int
    runs: int = 0
    balls: int = 0
    fours: int = 0
    sixes: int = 0
    overs: float = 0.0
    wickets: int = 0
    runs_conceded: int = 0
    maidens: int = 0
    catches: int = 0
    stumpings: int = 0
    run_outs: int = 0
    is_starting_xi: bool = True


class SubmitScoresRequest(BaseModel):
    scores: list[PlayerScoreInput]


@router.post("/{match_id}", response_model=APIResponse[None])
async def submit_scores(
    match_id: int,
    body: SubmitScoresRequest,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    await scoring_service.submit_scores(session, match_id, body.scores)
    return APIResponse(success=True, message="Scores submitted and fantasy points calculated")


@router.post("/{match_id}/finalize", response_model=APIResponse[None])
async def finalize_scores(
    match_id: int,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    await scoring_service.finalize_match(session, match_id)
    return APIResponse(success=True, message="Match finalized — rankings updated, prizes distributed")
