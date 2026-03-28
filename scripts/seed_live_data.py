"""Re-seed database with REAL IPL 2026 data from CricAPI."""

import asyncio
import json
import os
import ssl
import sys

import bcrypt
import httpx
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from src.db.models.models import (
    Contest, ContestType, Match, MatchFormat, MatchPlayer, MatchStatus,
    Player, PlayerRole, Tournament, TournamentStatus, User, UserRole, Wallet,
)

API_KEY = os.getenv("CRICKET_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Known IPL player roles — comprehensive mapping
PLAYER_ROLES = {
    # RCB 2026
    "virat kohli": PlayerRole.BAT,
    "philip salt": PlayerRole.WK,
    "rajat patidar": PlayerRole.BAT,
    "devdutt padikkal": PlayerRole.BAT,
    "jacob bethell": PlayerRole.AR,
    "tim david": PlayerRole.BAT,
    "venkatesh iyer": PlayerRole.AR,
    "krunal pandya": PlayerRole.AR,
    "jitesh sharma": PlayerRole.WK,
    "josh hazlewood": PlayerRole.BOWL,
    "bhuvneshwar kumar": PlayerRole.BOWL,
    "yash dayal": PlayerRole.BOWL,
    "nuwan thushara": PlayerRole.BOWL,
    "romario shepherd": PlayerRole.AR,
    "swapnil singh": PlayerRole.AR,
    "rasikh salam dar": PlayerRole.BOWL,
    "vicky ostwal": PlayerRole.BOWL,
    "mangesh yadav": PlayerRole.BOWL,
    "jacob duffy": PlayerRole.BOWL,
    "kanishk chouhan": PlayerRole.BOWL,
    "suyash sharma": PlayerRole.BOWL,
    "abhinandan singh": PlayerRole.BAT,
    "satvik deswal": PlayerRole.WK,
    "jordan cox": PlayerRole.WK,
    "vihaan malhotra": PlayerRole.BAT,

    # SRH 2026
    "travis head": PlayerRole.BAT,
    "abhishek sharma": PlayerRole.AR,
    "heinrich klaasen": PlayerRole.WK,
    "ishan kishan": PlayerRole.WK,
    "pat cummins": PlayerRole.BOWL,
    "harshal patel": PlayerRole.BOWL,
    "nitish kumar reddy": PlayerRole.AR,
    "liam livingstone": PlayerRole.AR,
    "kamindu mendis": PlayerRole.AR,
    "brydon carse": PlayerRole.AR,
    "shivam mavi": PlayerRole.BOWL,
    "jaydev unadkat": PlayerRole.BOWL,
    "eshan malinga": PlayerRole.BOWL,
    "jack edwards": PlayerRole.AR,
    "david payne": PlayerRole.BOWL,
    "harsh dubey": PlayerRole.BOWL,
    "zeeshan ansari": PlayerRole.BOWL,
    "salil arora": PlayerRole.BOWL,
    "smaran ravichandran": PlayerRole.BAT,
    "aniket verma": PlayerRole.BAT,
    "amit kumar": PlayerRole.BAT,
    "praful hinge": PlayerRole.BAT,
    "krains fuletra": PlayerRole.BAT,
    "shivang kumar": PlayerRole.BAT,
    "onkar tukaram tarmale": PlayerRole.BAT,
    "sakib hussain": PlayerRole.BOWL,
}

# Known player credits (star players get higher)
PLAYER_CREDITS = {
    "virat kohli": 10.5, "philip salt": 10.0, "travis head": 10.0,
    "heinrich klaasen": 10.0, "pat cummins": 9.5, "josh hazlewood": 9.0,
    "ishan kishan": 9.0, "liam livingstone": 9.0, "jacob bethell": 9.0,
    "tim david": 9.0, "venkatesh iyer": 9.0, "krunal pandya": 8.5,
    "harshal patel": 8.5, "bhuvneshwar kumar": 8.5, "kamindu mendis": 8.5,
    "nitish kumar reddy": 8.5, "abhishek sharma": 8.5, "brydon carse": 8.5,
    "rajat patidar": 8.5, "devdutt padikkal": 8.5, "romario shepherd": 8.0,
    "shivam mavi": 8.0, "yash dayal": 8.0, "nuwan thushara": 8.0,
    "jitesh sharma": 8.0, "jack edwards": 7.5, "jaydev unadkat": 7.5,
    "jordan cox": 7.5, "swapnil singh": 7.5, "david payne": 7.5,
    "eshan malinga": 7.5, "harsh dubey": 7.0, "vicky ostwal": 7.0,
    "rasikh salam dar": 7.0, "jacob duffy": 7.0, "smaran ravichandran": 7.0,
}


def hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def get_role(name: str) -> PlayerRole:
    return PLAYER_ROLES.get(name.lower(), PlayerRole.BAT)


def get_credits(name: str, role: PlayerRole) -> float:
    if name.lower() in PLAYER_CREDITS:
        return PLAYER_CREDITS[name.lower()]
    defaults = {PlayerRole.BAT: 7.0, PlayerRole.BOWL: 7.0, PlayerRole.AR: 7.5, PlayerRole.WK: 7.0}
    return defaults.get(role, 7.0)


async def fetch_squad(match_api_id: str) -> list[dict]:
    """Fetch squad from CricAPI."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"https://api.cricapi.com/v1/match_squad",
            params={"apikey": API_KEY, "id": match_api_id},
        )
        data = resp.json()
        if data.get("status") != "success":
            print(f"API error: {data}")
            return []
        return data.get("data", [])


async def seed():
    db_url = DATABASE_URL.split("?")[0]
    connect_args = {}
    if "neon.tech" in DATABASE_URL:
        ssl_ctx = ssl.create_default_context()
        connect_args["ssl"] = ssl_ctx

    engine = create_async_engine(db_url, echo=False, connect_args=connect_args)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Fetch real squad from CricAPI
    print("Fetching RCB vs SRH squad from CricAPI...")
    squads = await fetch_squad("55fe0f15-6eb0-4ad5-835b-5564be4f6a21")
    if not squads:
        print("ERROR: Could not fetch squad data")
        return

    async with async_session() as session:
        # === Users ===
        admin = User(
            email="naik.swaraj2007@gmail.com", username="swaraj",
            password_hash=hash_pw("admin123"),
            display_name="Swaraj Naik", role=UserRole.ADMIN,
        )
        session.add(admin)
        await session.flush()
        session.add(Wallet(user_id=admin.id, balance=10000))

        for i in range(1, 6):
            u = User(
                email=f"player{i}@test.com", username=f"player{i}",
                password_hash=hash_pw("test123"),
                display_name=f"Test Player {i}",
            )
            session.add(u)
            await session.flush()
            session.add(Wallet(user_id=u.id, balance=1000))

        # === Tournament ===
        tournament = Tournament(
            name="Indian Premier League 2026", short_name="IPL26",
            status=TournamentStatus.LIVE,
            start_date=__import__("datetime").datetime(2026, 3, 28),
            end_date=__import__("datetime").datetime(2026, 5, 25),
            description="IPL Season 19", created_by_id=admin.id,
        )
        session.add(tournament)
        await session.flush()

        # === Match: RCB vs SRH ===
        from datetime import datetime
        match = Match(
            tournament_id=tournament.id,
            team_a="Royal Challengers Bengaluru", team_a_short="RCB",
            team_b="Sunrisers Hyderabad", team_b_short="SRH",
            format=MatchFormat.T20, status=MatchStatus.UPCOMING,
            venue="M.Chinnaswamy Stadium, Bengaluru",
            start_time=datetime(2026, 3, 28, 14, 0, 0),  # 7:30 PM IST = 2:00 PM UTC
            lock_time=datetime(2026, 3, 28, 14, 0, 0),
        )
        session.add(match)
        await session.flush()

        # === Players from CricAPI ===
        total_players = 0
        for squad in squads:
            team_name = squad.get("teamName", "")
            team_short = "RCB" if "bengaluru" in team_name.lower() or "rcb" in team_name.lower() else "SRH"
            players_list = squad.get("players", [])

            print(f"\n{team_short} ({team_name}) — {len(players_list)} players:")

            for p_data in players_list:
                name = p_data.get("name", "Unknown")
                country = p_data.get("country", "")
                api_id = p_data.get("id", "")
                img_url = p_data.get("img") or None

                role = get_role(name)
                credits = get_credits(name, role)

                # Create player
                player = Player(
                    name=name,
                    short_name=_short_name(name),
                    role=role,
                    country=country,
                    default_credits=credits,
                    image_url=img_url,
                )
                session.add(player)
                await session.flush()

                # Create match player
                mp = MatchPlayer(
                    match_id=match.id, player_id=player.id,
                    team=team_short, credits=credits, is_playing=True,
                )
                session.add(mp)
                total_players += 1

                print(f"  {name:<28} | {role.value:<4} | {credits} cr | {country}")

        # === Contests ===
        mega_breakdown = json.dumps([
            {"rank": 1, "prize": 2000}, {"rank": 2, "prize": 1000},
            {"rank_from": 3, "rank_to": 5, "prize": 500},
            {"rank_from": 6, "rank_to": 10, "prize": 100},
        ])
        session.add(Contest(
            match_id=match.id, name="Mega Contest", type=ContestType.MEGA,
            entry_fee=50, total_prize_pool=5000, max_spots=100,
            max_teams_per_user=3, is_guaranteed=True,
            prize_breakdown=mega_breakdown, winner_count=10, created_by_id=admin.id,
        ))
        session.add(Contest(
            match_id=match.id, name="Head to Head", type=ContestType.HEAD_TO_HEAD,
            entry_fee=100, total_prize_pool=200, max_spots=2,
            max_teams_per_user=1, is_guaranteed=False,
            prize_breakdown=json.dumps([{"rank": 1, "prize": 200}]),
            winner_count=1, created_by_id=admin.id,
        ))
        session.add(Contest(
            match_id=match.id, name="Small League", type=ContestType.SMALL,
            entry_fee=25, total_prize_pool=500, max_spots=20,
            max_teams_per_user=2, is_guaranteed=True,
            prize_breakdown=json.dumps([
                {"rank": 1, "prize": 250}, {"rank": 2, "prize": 150},
                {"rank": 3, "prize": 100},
            ]),
            winner_count=3, created_by_id=admin.id,
        ))

        await session.commit()

        print(f"\n{'='*50}")
        print(f"SEED COMPLETE")
        print(f"{'='*50}")
        print(f"Admin: naik.swaraj2007@gmail.com / admin123")
        print(f"Users: player1-5@test.com / test123")
        print(f"Tournament: {tournament.name}")
        print(f"Match: RCB vs SRH (ID: {match.id})")
        print(f"Total players: {total_players}")
        print(f"Contests: Mega Contest, Head to Head, Small League")
        print(f"API Match ID: 55fe0f15-6eb0-4ad5-835b-5564be4f6a21")

    await engine.dispose()


def _short_name(full_name: str) -> str:
    parts = full_name.strip().split()
    if len(parts) <= 1:
        return full_name
    return f"{parts[0][0]} {parts[-1]}"


if __name__ == "__main__":
    asyncio.run(seed())
