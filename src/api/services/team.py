"""Team creation and validation service."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.api.exceptions import NotFoundException, ValidationException
from src.db.models.models import Match, MatchPlayer, Team, TeamPlayer


TEAM_RULES = {
    "TOTAL_PLAYERS": 11,
    "TOTAL_CREDITS": 100,
    "MAX_PLAYERS_PER_TEAM": 7,
    "MIN_PLAYERS_PER_TEAM": 4,
    "MIN_WK": 1, "MAX_WK": 8,
    "MIN_BAT": 1, "MAX_BAT": 8,
    "MIN_AR": 1, "MAX_AR": 8,
    "MIN_BOWL": 1, "MAX_BOWL": 8,
}


async def create_team(
    session: AsyncSession,
    user_id: int,
    match_id: int,
    player_ids: list[int],
    captain_id: int,
    vice_captain_id: int,
    name: str = "Team 1",
) -> Team:
    match = (await session.execute(select(Match).where(Match.id == match_id))).scalars().first()
    if not match:
        raise NotFoundException("Match not found")
    if datetime.utcnow() >= match.lock_time:
        raise ValidationException("Match is locked")

    result = await session.execute(
        select(MatchPlayer)
        .where(MatchPlayer.id.in_(player_ids))
        .options(selectinload(MatchPlayer.player))
    )
    match_players = list(result.scalars().all())

    if len(match_players) != 11:
        raise ValidationException(f"Need exactly 11 players, got {len(match_players)}")

    for mp in match_players:
        if mp.match_id != match_id:
            raise ValidationException(f"Player {mp.id} not in this match")

    total_credits = sum(mp.credits for mp in match_players)
    if total_credits > 100:
        raise ValidationException(f"Credits {total_credits} exceeds 100")

    role_counts: dict[str, int] = {}
    for mp in match_players:
        r = mp.player.role.value
        role_counts[r] = role_counts.get(r, 0) + 1
    for role_key in ["WK", "BAT", "AR", "BOWL"]:
        count = role_counts.get(role_key, 0)
        mn, mx = TEAM_RULES[f"MIN_{role_key}"], TEAM_RULES[f"MAX_{role_key}"]
        if count < mn or count > mx:
            raise ValidationException(f"{role_key}: need {mn}-{mx}, got {count}")

    team_counts: dict[str, int] = {}
    for mp in match_players:
        team_counts[mp.team] = team_counts.get(mp.team, 0) + 1
    for t, count in team_counts.items():
        if count < 4 or count > 7:
            raise ValidationException(f"Need 4-7 from {t}, got {count}")

    mp_ids = {mp.id for mp in match_players}
    if captain_id not in mp_ids:
        raise ValidationException("Captain must be from selected 11")
    if vice_captain_id not in mp_ids:
        raise ValidationException("Vice Captain must be from selected 11")
    if captain_id == vice_captain_id:
        raise ValidationException("Captain and Vice Captain must differ")

    team = Team(
        user_id=user_id, match_id=match_id, name=name,
        captain_id=captain_id, vice_captain_id=vice_captain_id,
        total_credits=total_credits,
    )
    session.add(team)
    await session.flush()

    for mp in match_players:
        tp = TeamPlayer(
            team_id=team.id, match_player_id=mp.id, player_id=mp.player_id,
            is_captain=(mp.id == captain_id),
            is_vice_captain=(mp.id == vice_captain_id),
        )
        session.add(tp)

    await session.commit()
    await session.refresh(team)
    return team
