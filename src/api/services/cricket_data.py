"""Live cricket data integration via CricAPI (cricketdata.org).

Handles:
- Fetching upcoming/current IPL matches
- Syncing player squads for matches
- Fetching live scores and calculating fantasy points
- Auto-updating match statuses

API: https://cricketdata.org — Free tier: 100 requests/day
Endpoints used:
  - currentMatches: List current/recent matches
  - match_info: Match details
  - match_scorecard: Full scorecard with player batting/bowling stats
  - match_squad: Squad/playing XI for a match
"""

import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.api.services.scoring import T20_SCORING, calculate_fantasy_points
from src.config import settings
from src.db.models.models import (
    Contest,
    Match,
    MatchFormat,
    MatchPlayer,
    MatchStatus,
    Player,
    PlayerRole,
    PlayerScore,
    Team,
    TeamPlayer,
    Tournament,
    TournamentStatus,
)

logger = logging.getLogger(__name__)

API_KEY = settings.CRICKET_API_KEY
BASE_URL = settings.CRICKET_API_URL


# ========================
# API Client
# ========================


async def _api_get(endpoint: str, params: dict | None = None) -> dict:
    """Make a GET request to CricAPI."""
    if not API_KEY:
        raise ValueError("CRICKET_API_KEY not set in environment")

    url = f"{BASE_URL}/{endpoint}"
    all_params = {"apikey": API_KEY}
    if params:
        all_params.update(params)

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=all_params)
        resp.raise_for_status()
        data = resp.json()

    if data.get("status") != "success":
        logger.error(f"CricAPI error: {data.get('status')} - {data.get('info', 'unknown')}")
        raise ValueError(f"CricAPI error: {data.get('info', 'API call failed')}")

    return data


# ========================
# Match Sync
# ========================


def _parse_match_status(api_status: str, match_started: bool, match_ended: bool) -> MatchStatus:
    """Map CricAPI match status to our MatchStatus enum."""
    api_status = (api_status or "").lower()
    if match_ended or "complete" in api_status or "result" in api_status:
        return MatchStatus.COMPLETED
    if match_started or "live" in api_status or "in progress" in api_status:
        return MatchStatus.LIVE
    return MatchStatus.UPCOMING


def _parse_match_format(match_type: str) -> MatchFormat:
    """Map CricAPI match type to our MatchFormat enum."""
    match_type = (match_type or "").lower()
    if "t20" in match_type:
        return MatchFormat.T20
    if "odi" in match_type:
        return MatchFormat.ODI
    if "test" in match_type:
        return MatchFormat.TEST
    return MatchFormat.T20


async def sync_current_matches(session: AsyncSession) -> list[dict]:
    """Fetch upcoming + live IPL matches from CricAPI and sync to database.

    Uses the 'matches' endpoint (scheduled/upcoming) and 'currentMatches' (live).
    Returns list of synced match info dicts.
    """
    # Fetch scheduled matches (includes upcoming IPL)
    data = await _api_get("matches")
    matches_data = data.get("data", [])

    # Also try currentMatches for live games
    try:
        live_data = await _api_get("currentMatches")
        matches_data.extend(live_data.get("data", []))
    except Exception:
        pass  # currentMatches may fail if no live matches

    # Filter to IPL / T20 matches
    ipl_matches = [
        m for m in matches_data
        if "indian premier league" in (m.get("name", "")).lower()
        or "ipl" in (m.get("name", "")).lower()
    ]

    if not ipl_matches:
        ipl_matches = [m for m in matches_data if m.get("matchType", "").lower() == "t20"]

    # Ensure IPL tournament exists
    result = await session.execute(select(Tournament).where(Tournament.short_name == "IPL25"))
    tournament = result.scalars().first()
    if not tournament:
        tournament = Tournament(
            name="Indian Premier League 2025", short_name="IPL25",
            status=TournamentStatus.LIVE,
            start_date=datetime(2025, 3, 22), end_date=datetime(2025, 5, 25),
            created_by_id=1,
        )
        session.add(tournament)
        await session.flush()

    synced = []
    for m in ipl_matches:
        api_match_id = m.get("id", "")
        teams_info = m.get("teams", [])
        if len(teams_info) < 2:
            continue

        team_a_name = teams_info[0] if isinstance(teams_info[0], str) else teams_info[0].get("name", "TBD")
        team_b_name = teams_info[1] if isinstance(teams_info[1], str) else teams_info[1].get("name", "TBD")

        # Generate short names
        team_a_short = _team_short_name(team_a_name)
        team_b_short = _team_short_name(team_b_name)

        # Parse dates
        date_str = m.get("dateTimeGMT") or m.get("date", "")
        try:
            start_time = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            start_time = datetime.now(timezone.utc)

        match_started = m.get("matchStarted", False)
        match_ended = m.get("matchEnded", False)
        status = _parse_match_status(m.get("status", ""), match_started, match_ended)

        # Check if match already exists (by API ID stored in result_summary field or team names + date)
        existing = await session.execute(
            select(Match).where(
                Match.team_a_short == team_a_short,
                Match.team_b_short == team_b_short,
                Match.tournament_id == tournament.id,
            )
        )
        match = existing.scalars().first()

        if match:
            # Update existing match
            match.status = status
            if m.get("status"):
                match.result_summary = m.get("status")
        else:
            # Create new match
            match = Match(
                tournament_id=tournament.id,
                team_a=team_a_name, team_a_short=team_a_short,
                team_b=team_b_name, team_b_short=team_b_short,
                format=_parse_match_format(m.get("matchType", "t20")),
                status=status,
                venue=m.get("venue", ""),
                start_time=start_time,
                lock_time=start_time,  # Lock at match start
                result_summary=m.get("status"),
            )
            session.add(match)
            await session.flush()

        synced.append({
            "match_id": match.id,
            "api_id": api_match_id,
            "teams": f"{team_a_short} vs {team_b_short}",
            "status": status.value,
            "start_time": start_time.isoformat(),
        })

    await session.commit()
    return synced


# ========================
# Player/Squad Sync
# ========================

ROLE_MAP = {
    "batsman": PlayerRole.BAT, "batter": PlayerRole.BAT, "bat": PlayerRole.BAT,
    "bowler": PlayerRole.BOWL, "bowl": PlayerRole.BOWL,
    "all-rounder": PlayerRole.AR, "allrounder": PlayerRole.AR, "ar": PlayerRole.AR,
    "batting allrounder": PlayerRole.AR, "bowling allrounder": PlayerRole.AR,
    "wk-batsman": PlayerRole.WK, "wicketkeeper": PlayerRole.WK, "wk": PlayerRole.WK,
    "keeper": PlayerRole.WK,
}


def _map_role(role_str: str) -> PlayerRole:
    """Map CricAPI player role string to our PlayerRole enum."""
    role_lower = (role_str or "bat").lower().strip()
    return ROLE_MAP.get(role_lower, PlayerRole.BAT)


def _estimate_credits(role: PlayerRole, name: str) -> float:
    """Estimate player credits based on role and name recognition.
    In production, this would come from the fantasy API endpoint.
    """
    # Star player credits (well-known players get higher credits)
    star_players = {
        "virat kohli": 10.5, "rohit sharma": 10.5, "jasprit bumrah": 10.0,
        "suryakumar yadav": 10.0, "travis head": 10.0, "heinrich klaasen": 10.0,
        "pat cummins": 9.5, "rashid khan": 9.5, "faf du plessis": 9.5,
        "ms dhoni": 9.5, "jos buttler": 10.0, "rishabh pant": 9.5,
        "glenn maxwell": 9.0, "mitchell starc": 9.5, "josh hazlewood": 9.0,
        "wanindu hasaranga": 9.0, "cameron green": 9.0, "marco jansen": 9.0,
        "mohammed siraj": 8.5, "harshal patel": 8.5, "bhuvneshwar kumar": 8.5,
        "kagiso rabada": 9.5, "trent boult": 9.0, "yuzvendra chahal": 8.5,
    }
    name_lower = name.lower()
    if name_lower in star_players:
        return star_players[name_lower]

    # Default by role
    defaults = {PlayerRole.BAT: 8.0, PlayerRole.BOWL: 7.5, PlayerRole.AR: 8.0, PlayerRole.WK: 7.5}
    return defaults.get(role, 8.0)


async def sync_match_squad(session: AsyncSession, match_id: int, api_match_id: str) -> dict:
    """Fetch squad/playing XI for a match and create Player + MatchPlayer records."""
    data = await _api_get("match_squad", {"id": api_match_id})
    squads = data.get("data", [])

    match = (await session.execute(select(Match).where(Match.id == match_id))).scalars().first()
    if not match:
        raise ValueError(f"Match {match_id} not found")

    total_added = 0
    for squad_info in squads:
        team_name = squad_info.get("teamName", "")
        team_short = _team_short_name(team_name)
        players_list = squad_info.get("players", [])

        for p_data in players_list:
            player_name = p_data.get("name", "Unknown")
            player_api_id = p_data.get("id", "")
            role = _map_role(p_data.get("playerRole", "batsman"))
            country = p_data.get("country", "")

            # Check if player exists
            existing_player = (await session.execute(
                select(Player).where(Player.name == player_name)
            )).scalars().first()

            if not existing_player:
                credits = _estimate_credits(role, player_name)
                player = Player(
                    name=player_name,
                    short_name=_short_name(player_name),
                    role=role,
                    country=country,
                    default_credits=credits,
                    image_url=p_data.get("img"),
                )
                session.add(player)
                await session.flush()
            else:
                player = existing_player

            # Check if MatchPlayer exists
            existing_mp = (await session.execute(
                select(MatchPlayer).where(
                    MatchPlayer.match_id == match_id,
                    MatchPlayer.player_id == player.id,
                )
            )).scalars().first()

            if not existing_mp:
                mp = MatchPlayer(
                    match_id=match_id,
                    player_id=player.id,
                    team=team_short,
                    credits=player.default_credits,
                    is_playing=True,
                )
                session.add(mp)
                total_added += 1

    await session.commit()
    return {"match_id": match_id, "players_added": total_added}


# ========================
# Live Score Sync
# ========================


async def sync_live_scores(session: AsyncSession, match_id: int, api_match_id: str) -> dict:
    """Fetch live scorecard and update PlayerScore + fantasy points."""
    data = await _api_get("match_scorecard", {"id": api_match_id})
    scorecard = data.get("data", {})

    match = (await session.execute(select(Match).where(Match.id == match_id))).scalars().first()
    if not match:
        raise ValueError(f"Match {match_id} not found")

    # Update match status
    match_started = scorecard.get("matchStarted", False)
    match_ended = scorecard.get("matchEnded", False)
    if match_ended:
        match.status = MatchStatus.IN_REVIEW
        match.result_summary = scorecard.get("status", "")
    elif match_started:
        match.status = MatchStatus.LIVE

    # Process scorecard — extract batting and bowling stats
    scores_updated = 0
    score_data = scorecard.get("score", [])  # Array of innings scores

    # Get all match players
    mps = (await session.execute(
        select(MatchPlayer).where(MatchPlayer.match_id == match_id)
        .options(selectinload(MatchPlayer.player))
    )).scalars().all()
    mp_by_name = {mp.player.name.lower(): mp for mp in mps if mp.player}

    # Process batting stats from each innings
    for innings in score_data:
        batting = innings.get("batting", []) if isinstance(innings, dict) else []
        for bat_entry in batting:
            player_name = (bat_entry.get("batsman", {}).get("name", "") or bat_entry.get("name", "")).lower()
            mp = mp_by_name.get(player_name)
            if not mp:
                continue

            # Get or create PlayerScore
            existing_score = (await session.execute(
                select(PlayerScore).where(PlayerScore.match_player_id == mp.id)
            )).scalars().first()
            ps = existing_score or PlayerScore(match_player_id=mp.id, player_id=mp.player_id, match_id=match_id)

            # Update batting stats
            ps.runs = _safe_int(bat_entry.get("r", bat_entry.get("runs", 0)))
            ps.balls = _safe_int(bat_entry.get("b", bat_entry.get("balls", 0)))
            ps.fours = _safe_int(bat_entry.get("4s", bat_entry.get("fours", 0)))
            ps.sixes = _safe_int(bat_entry.get("6s", bat_entry.get("sixes", 0)))
            ps.is_starting_xi = True

            # Recalculate fantasy points
            ps.fantasy_points = calculate_fantasy_points(ps, mp.player.role)

            if not existing_score:
                session.add(ps)
            scores_updated += 1

        # Process bowling stats
        bowling = innings.get("bowling", []) if isinstance(innings, dict) else []
        for bowl_entry in bowling:
            player_name = (bowl_entry.get("bowler", {}).get("name", "") or bowl_entry.get("name", "")).lower()
            mp = mp_by_name.get(player_name)
            if not mp:
                continue

            existing_score = (await session.execute(
                select(PlayerScore).where(PlayerScore.match_player_id == mp.id)
            )).scalars().first()
            ps = existing_score or PlayerScore(match_player_id=mp.id, player_id=mp.player_id, match_id=match_id)

            # Update bowling stats (merge with existing batting stats)
            ps.overs = _safe_float(bowl_entry.get("o", bowl_entry.get("overs", 0)))
            ps.wickets = _safe_int(bowl_entry.get("w", bowl_entry.get("wickets", 0)))
            ps.runs_conceded = _safe_int(bowl_entry.get("r", bowl_entry.get("runs_conceded", 0)))
            ps.maidens = _safe_int(bowl_entry.get("m", bowl_entry.get("maidens", 0)))

            ps.fantasy_points = calculate_fantasy_points(ps, mp.player.role)

            if not existing_score:
                session.add(ps)
            scores_updated += 1

    # Process fielding from catch data if available
    catching = scorecard.get("fielding", [])
    for catch_entry in catching:
        player_name = (catch_entry.get("name", "")).lower()
        mp = mp_by_name.get(player_name)
        if not mp:
            continue
        existing_score = (await session.execute(
            select(PlayerScore).where(PlayerScore.match_player_id == mp.id)
        )).scalars().first()
        if existing_score:
            existing_score.catches = _safe_int(catch_entry.get("catches", 0))
            existing_score.stumpings = _safe_int(catch_entry.get("stumpings", 0))
            existing_score.run_outs = _safe_int(catch_entry.get("runouts", 0))
            existing_score.fantasy_points = calculate_fantasy_points(existing_score, mp.player.role)

    await session.flush()

    # Update team total points
    teams = (await session.execute(
        select(Team).where(Team.match_id == match_id)
        .options(
            selectinload(Team.players)
            .selectinload(TeamPlayer.match_player)
            .selectinload(MatchPlayer.player_score)
        )
    )).scalars().all()

    for team in teams:
        total = 0.0
        for tp in team.players:
            base = tp.match_player.player_score.fantasy_points if tp.match_player and tp.match_player.player_score else 0
            mult = T20_SCORING["CAPTAIN_X"] if tp.is_captain else (T20_SCORING["VC_X"] if tp.is_vice_captain else 1.0)
            tp.points = base * mult
            total += tp.points
        team.total_points = total

    # Update contest entry points
    from src.db.models.models import ContestEntry
    entries = (await session.execute(
        select(ContestEntry)
        .options(selectinload(ContestEntry.team))
        .join(Contest).where(Contest.match_id == match_id)
    )).scalars().all()
    for entry in entries:
        if entry.team:
            entry.total_points = entry.team.total_points

    await session.commit()

    return {
        "match_id": match_id,
        "status": match.status.value,
        "scores_updated": scores_updated,
        "teams_updated": len(teams),
        "result": match.result_summary,
    }


# ========================
# Helpers
# ========================

IPL_TEAM_MAP = {
    "chennai super kings": "CSK", "mumbai indians": "MI",
    "royal challengers bangalore": "RCB", "royal challengers bengaluru": "RCB",
    "kolkata knight riders": "KKR", "sunrisers hyderabad": "SRH",
    "rajasthan royals": "RR", "delhi capitals": "DC",
    "punjab kings": "PBKS", "lucknow super giants": "LSG",
    "gujarat titans": "GT",
}


def _team_short_name(name: str) -> str:
    """Convert full team name to short code."""
    name_lower = name.lower().strip()
    for full, short in IPL_TEAM_MAP.items():
        if full in name_lower:
            return short
    # Fallback: first 3 chars uppercase
    return name[:3].upper()


def _short_name(full_name: str) -> str:
    """Convert 'Virat Kohli' to 'V Kohli'."""
    parts = full_name.strip().split()
    if len(parts) <= 1:
        return full_name
    return f"{parts[0][0]} {parts[-1]}"


def _safe_int(val) -> int:
    try:
        return int(val or 0)
    except (ValueError, TypeError):
        return 0


def _safe_float(val) -> float:
    try:
        return float(val or 0)
    except (ValueError, TypeError):
        return 0.0
