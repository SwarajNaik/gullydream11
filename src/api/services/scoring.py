"""Fantasy points calculation engine — Dream11 T20 Cricket rules."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.api.exceptions import NotFoundException
from src.db.models.models import (
    Contest, Match, MatchPlayer, MatchStatus, PlayerRole, PlayerScore, Team, TeamPlayer,
)

T20_SCORING = {
    "STARTING_XI": 4,
    "RUN": 1, "FOUR": 1, "SIX": 2,
    "HALF_CENTURY": 8, "CENTURY": 16, "DUCK": -2,
    "SR_ABOVE_170": 6, "SR_150_170": 4, "SR_130_150": 2,
    "SR_60_70": -2, "SR_50_60": -4, "SR_BELOW_50": -6,
    "WICKET": 25, "WICKET_3": 4, "WICKET_4": 8, "WICKET_5": 16,
    "MAIDEN": 12,
    "ECO_BELOW_5": 6, "ECO_5_6": 4, "ECO_6_7": 2,
    "ECO_10_11": -2, "ECO_11_12": -4, "ECO_ABOVE_12": -6,
    "CATCH": 8, "CATCH_3": 4, "STUMPING": 12,
    "RUN_OUT_DIRECT": 12, "RUN_OUT_INDIRECT": 6,
    "CAPTAIN_X": 2.0, "VC_X": 1.5,
}
S = T20_SCORING


def calculate_fantasy_points(score: PlayerScore, role: PlayerRole) -> float:
    pts = 0.0
    if score.is_starting_xi:
        pts += S["STARTING_XI"]

    pts += score.runs * S["RUN"]
    pts += score.fours * S["FOUR"]
    pts += score.sixes * S["SIX"]
    if score.runs >= 100:
        pts += S["CENTURY"]
    elif score.runs >= 50:
        pts += S["HALF_CENTURY"]
    if score.runs == 0 and score.balls > 0 and role in (PlayerRole.BAT, PlayerRole.WK, PlayerRole.AR):
        pts += S["DUCK"]

    if score.balls >= 10:
        sr = (score.runs / score.balls) * 100
        if sr > 170: pts += S["SR_ABOVE_170"]
        elif sr >= 150: pts += S["SR_150_170"]
        elif sr >= 130: pts += S["SR_130_150"]
        elif sr <= 50: pts += S["SR_BELOW_50"]
        elif sr <= 60: pts += S["SR_50_60"]
        elif sr <= 70: pts += S["SR_60_70"]

    pts += score.wickets * S["WICKET"]
    if score.wickets >= 5: pts += S["WICKET_5"]
    elif score.wickets >= 4: pts += S["WICKET_4"]
    elif score.wickets >= 3: pts += S["WICKET_3"]
    pts += score.maidens * S["MAIDEN"]

    if score.overs >= 2:
        eco = score.runs_conceded / score.overs
        if eco < 5: pts += S["ECO_BELOW_5"]
        elif eco < 6: pts += S["ECO_5_6"]
        elif eco < 7: pts += S["ECO_6_7"]
        elif eco >= 12: pts += S["ECO_ABOVE_12"]
        elif eco >= 11: pts += S["ECO_11_12"]
        elif eco >= 10: pts += S["ECO_10_11"]

    pts += score.catches * S["CATCH"]
    if score.catches >= 3: pts += S["CATCH_3"]
    pts += score.stumpings * S["STUMPING"]
    pts += score.run_outs * S["RUN_OUT_DIRECT"]

    return pts


async def submit_scores(session: AsyncSession, match_id: int, scores_data: list):
    for s in scores_data:
        mp = (await session.execute(
            select(MatchPlayer).where(MatchPlayer.id == s.match_player_id)
            .options(selectinload(MatchPlayer.player))
        )).scalars().first()
        if not mp:
            continue

        existing = (await session.execute(
            select(PlayerScore).where(PlayerScore.match_player_id == mp.id)
        )).scalars().first()
        score = existing or PlayerScore(match_player_id=mp.id, player_id=mp.player_id, match_id=match_id)

        for field in ["runs", "balls", "fours", "sixes", "overs", "wickets",
                       "runs_conceded", "maidens", "catches", "stumpings", "run_outs", "is_starting_xi"]:
            setattr(score, field, getattr(s, field))

        score.fantasy_points = calculate_fantasy_points(score, mp.player.role)

        if not existing:
            session.add(score)

    await session.commit()


async def finalize_match(session: AsyncSession, match_id: int):
    from src.api.services.contest import distribute_prizes

    match = (await session.execute(select(Match).where(Match.id == match_id))).scalars().first()
    if not match:
        raise NotFoundException("Match not found")

    teams = list((await session.execute(
        select(Team).where(Team.match_id == match_id)
        .options(
            selectinload(Team.players)
            .selectinload(TeamPlayer.match_player)
            .selectinload(MatchPlayer.player_score)
        )
    )).scalars().all())

    for team in teams:
        total = 0.0
        for tp in team.players:
            base = tp.match_player.player_score.fantasy_points if tp.match_player and tp.match_player.player_score else 0
            mult = S["CAPTAIN_X"] if tp.is_captain else (S["VC_X"] if tp.is_vice_captain else 1.0)
            tp.points = base * mult
            total += tp.points
        team.total_points = total

    await session.flush()

    contests = list((await session.execute(select(Contest).where(Contest.match_id == match_id))).scalars().all())
    for contest in contests:
        await distribute_prizes(session, contest.id)

    match.status = MatchStatus.COMPLETED
    await session.commit()
