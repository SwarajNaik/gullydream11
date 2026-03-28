"""Admin routes: CRUD for tournaments, matches, contests, players, users, settlements."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from src.api.dependencies.auth import require_admin
from src.api.schemas.common import APIResponse
from src.db.models.models import (
    Contest, ContestType, Match, MatchFormat, MatchPlayer, MatchStatus,
    Player, PlayerRole, Settlement, Tournament, TournamentStatus, User, Wallet,
)
from src.db.session import get_session

router = APIRouter()


# === Tournament ===
class CreateTournamentReq(BaseModel):
    name: str
    short_name: str
    start_date: str
    end_date: str
    image_url: str | None = None
    description: str | None = None

class TournamentResp(BaseModel):
    id: int
    name: str
    short_name: str
    status: str
    model_config = {"from_attributes": True}

@router.post("/tournaments", response_model=APIResponse[TournamentResp], status_code=201)
async def create_tournament(body: CreateTournamentReq, session: AsyncSession = Depends(get_session), admin: User = Depends(require_admin)):
    t = Tournament(name=body.name, short_name=body.short_name, start_date=datetime.fromisoformat(body.start_date), end_date=datetime.fromisoformat(body.end_date), image_url=body.image_url, description=body.description, created_by_id=admin.id)
    session.add(t)
    await session.commit()
    await session.refresh(t)
    return APIResponse(success=True, message="Tournament created", data=TournamentResp.model_validate(t))


# === Match ===
class CreateMatchReq(BaseModel):
    tournament_id: int
    team_a: str
    team_a_short: str
    team_b: str
    team_b_short: str
    format: str = "T20"
    venue: str | None = None
    start_time: str
    lock_time: str

class MatchResp(BaseModel):
    id: int
    team_a: str
    team_a_short: str
    team_b: str
    team_b_short: str
    status: str
    start_time: str
    model_config = {"from_attributes": True}

@router.post("/matches", response_model=APIResponse[MatchResp], status_code=201)
async def create_match(body: CreateMatchReq, session: AsyncSession = Depends(get_session), admin: User = Depends(require_admin)):
    m = Match(tournament_id=body.tournament_id, team_a=body.team_a, team_a_short=body.team_a_short, team_b=body.team_b, team_b_short=body.team_b_short, format=MatchFormat(body.format), venue=body.venue, start_time=datetime.fromisoformat(body.start_time), lock_time=datetime.fromisoformat(body.lock_time))
    session.add(m)
    await session.commit()
    await session.refresh(m)
    return APIResponse(success=True, message="Match created", data=MatchResp.model_validate(m))

class UpdateMatchReq(BaseModel):
    status: str | None = None
    result_summary: str | None = None

@router.put("/matches/{match_id}", response_model=APIResponse[None])
async def update_match(match_id: int, body: UpdateMatchReq, session: AsyncSession = Depends(get_session), admin: User = Depends(require_admin)):
    m = (await session.execute(select(Match).where(Match.id == match_id))).scalars().first()
    if body.status:
        m.status = MatchStatus(body.status)
    if body.result_summary:
        m.result_summary = body.result_summary
    await session.commit()
    return APIResponse(success=True, message="Match updated")


# === Add Players to Match ===
class AddMatchPlayerReq(BaseModel):
    player_id: int
    team: str
    credits: float
    is_playing: bool | None = None

class AddMatchPlayersReq(BaseModel):
    players: list[AddMatchPlayerReq]

@router.post("/matches/{match_id}/players", response_model=APIResponse[None], status_code=201)
async def add_players_to_match(match_id: int, body: AddMatchPlayersReq, session: AsyncSession = Depends(get_session), admin: User = Depends(require_admin)):
    for p in body.players:
        mp = MatchPlayer(match_id=match_id, player_id=p.player_id, team=p.team, credits=p.credits, is_playing=p.is_playing)
        session.add(mp)
    await session.commit()
    return APIResponse(success=True, message=f"{len(body.players)} players added to match")


# === Contest ===
class CreateContestReq(BaseModel):
    match_id: int
    name: str
    type: str = "MEGA"
    entry_fee: float
    total_prize_pool: float
    max_spots: int
    max_teams_per_user: int = 1
    is_guaranteed: bool = False
    prize_breakdown: list[dict] = []
    winner_count: int = 1

@router.post("/contests", response_model=APIResponse[None], status_code=201)
async def create_contest(body: CreateContestReq, session: AsyncSession = Depends(get_session), admin: User = Depends(require_admin)):
    c = Contest(match_id=body.match_id, name=body.name, type=ContestType(body.type), entry_fee=body.entry_fee, total_prize_pool=body.total_prize_pool, max_spots=body.max_spots, max_teams_per_user=body.max_teams_per_user, is_guaranteed=body.is_guaranteed, prize_breakdown=json.dumps(body.prize_breakdown), winner_count=body.winner_count, created_by_id=admin.id)
    session.add(c)
    await session.commit()
    return APIResponse(success=True, message="Contest created")


# === Player ===
class CreatePlayerReq(BaseModel):
    name: str
    short_name: str
    role: str
    country: str | None = None
    batting_style: str | None = None
    bowling_style: str | None = None
    default_credits: float = 8.0

@router.post("/players", response_model=APIResponse[None], status_code=201)
async def create_player(body: CreatePlayerReq, session: AsyncSession = Depends(get_session), admin: User = Depends(require_admin)):
    p = Player(name=body.name, short_name=body.short_name, role=PlayerRole(body.role), country=body.country, batting_style=body.batting_style, bowling_style=body.bowling_style, default_credits=body.default_credits)
    session.add(p)
    await session.commit()
    return APIResponse(success=True, message="Player added")


# === Users ===
class UserResp(BaseModel):
    id: int
    email: str
    username: str
    display_name: str
    role: str
    is_active: bool
    total_winnings: float
    model_config = {"from_attributes": True}

class UserListResp(BaseModel):
    users: list[UserResp]

@router.get("/users", response_model=APIResponse[UserListResp])
async def list_users(session: AsyncSession = Depends(get_session), admin: User = Depends(require_admin)):
    users = list((await session.execute(select(User))).scalars().all())
    return APIResponse(success=True, message="Users fetched", data=UserListResp(users=[UserResp.model_validate(u) for u in users]))


# === Wallet Credit/Debit ===
class WalletOpReq(BaseModel):
    amount: float
    note: str = ""

@router.post("/wallet/{user_id}/credit", response_model=APIResponse[None])
async def credit_wallet(user_id: int, body: WalletOpReq, session: AsyncSession = Depends(get_session), admin: User = Depends(require_admin)):
    from src.api.services.wallet import get_or_create_wallet
    from src.db.models.models import Transaction, TransactionType, TransactionStatus
    wallet = await get_or_create_wallet(session, user_id)
    wallet.balance += body.amount
    txn = Transaction(wallet_id=wallet.id, user_id=user_id, type=TransactionType.ADMIN_CREDIT, status=TransactionStatus.COMPLETED, amount=body.amount, balance_after=wallet.balance, description=body.note or "Admin credit")
    session.add(txn)
    await session.commit()
    return APIResponse(success=True, message=f"Credited {body.amount}")


# === Settlements ===
@router.get("/settlements", response_model=APIResponse[None])
async def list_settlements(session: AsyncSession = Depends(get_session), admin: User = Depends(require_admin)):
    settlements = list((await session.execute(select(Settlement))).scalars().all())
    return APIResponse(success=True, message="Settlements fetched", data=settlements)


# === Dashboard ===
class DashboardResp(BaseModel):
    total_users: int
    total_matches: int
    total_contests: int
    total_prize_pool: float

@router.get("/dashboard", response_model=APIResponse[DashboardResp])
async def get_dashboard(session: AsyncSession = Depends(get_session), admin: User = Depends(require_admin)):
    users = (await session.execute(select(func.count(User.id)))).scalar_one()
    matches = (await session.execute(select(func.count(Match.id)))).scalar_one()
    contests = (await session.execute(select(func.count(Contest.id)))).scalar_one()
    pool = (await session.execute(select(func.coalesce(func.sum(Contest.total_prize_pool), 0)))).scalar_one()
    return APIResponse(success=True, message="Dashboard", data=DashboardResp(total_users=users, total_matches=matches, total_contests=contests, total_prize_pool=pool))
