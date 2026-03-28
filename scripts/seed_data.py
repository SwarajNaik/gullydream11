"""Seed database with IPL 2025 data: RCB vs SRH match, real players, contests."""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from src.db.models.models import (
    Contest, ContestType, Match, MatchFormat, MatchPlayer, MatchStatus,
    Player, PlayerRole, Tournament, TournamentStatus, User, UserRole, Wallet,
)

def hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5436/gullydream11")


async def seed():
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # === ADMIN USER ===
        admin = User(
            email="naik.swaraj2007@gmail.com", username="swaraj",
            password_hash=hash_pw("admin123"),
            display_name="Swaraj Naik", role=UserRole.ADMIN,
        )
        session.add(admin)
        await session.flush()

        admin_wallet = Wallet(user_id=admin.id, balance=10000)
        session.add(admin_wallet)

        # === SAMPLE USERS ===
        users = []
        for i in range(1, 6):
            u = User(
                email=f"player{i}@test.com", username=f"player{i}",
                password_hash=hash_pw("test123"),
                display_name=f"Test Player {i}",
            )
            session.add(u)
            await session.flush()
            session.add(Wallet(user_id=u.id, balance=1000))
            users.append(u)

        # === TOURNAMENT ===
        tournament = Tournament(
            name="Indian Premier League 2025", short_name="IPL25",
            status=TournamentStatus.LIVE,
            start_date=datetime(2025, 3, 22),
            end_date=datetime(2025, 5, 25),
            description="IPL Season 18",
            created_by_id=admin.id,
        )
        session.add(tournament)
        await session.flush()

        # === MATCH: RCB vs SRH (Today) ===
        today = datetime.utcnow().replace(hour=14, minute=0, second=0, microsecond=0)  # 7:30 PM IST = 2:00 PM UTC
        match = Match(
            tournament_id=tournament.id,
            team_a="Royal Challengers Bengaluru", team_a_short="RCB",
            team_b="Sunrisers Hyderabad", team_b_short="SRH",
            format=MatchFormat.T20, status=MatchStatus.UPCOMING,
            venue="M. Chinnaswamy Stadium, Bengaluru",
            start_time=today, lock_time=today,
        )
        session.add(match)
        await session.flush()

        # === RCB PLAYERS ===
        rcb_players = [
            ("Virat Kohli", "V Kohli", PlayerRole.BAT, 10.5, "Right Handed", None),
            ("Faf du Plessis", "F du Plessis", PlayerRole.BAT, 9.5, "Right Handed", None),
            ("Rajat Patidar", "R Patidar", PlayerRole.BAT, 8.5, "Right Handed", None),
            ("Glenn Maxwell", "G Maxwell", PlayerRole.AR, 9.0, "Right Handed", "Right Arm Off Break"),
            ("Dinesh Karthik", "D Karthik", PlayerRole.WK, 8.0, "Right Handed", None),
            ("Anuj Rawat", "A Rawat", PlayerRole.WK, 7.0, "Left Handed", None),
            ("Mahipal Lomror", "M Lomror", PlayerRole.AR, 7.5, "Left Handed", "Left Arm Orthodox"),
            ("Shahbaz Ahmed", "S Ahmed", PlayerRole.AR, 7.5, "Left Handed", "Left Arm Orthodox"),
            ("Wanindu Hasaranga", "W Hasaranga", PlayerRole.BOWL, 9.0, "Right Handed", "Right Arm Leg Break"),
            ("Mohammed Siraj", "M Siraj", PlayerRole.BOWL, 8.5, None, "Right Arm Fast"),
            ("Josh Hazlewood", "J Hazlewood", PlayerRole.BOWL, 9.0, None, "Right Arm Fast"),
            ("Harshal Patel", "H Patel", PlayerRole.BOWL, 8.5, "Right Handed", "Right Arm Medium"),
            ("Karn Sharma", "K Sharma", PlayerRole.BOWL, 7.0, "Left Handed", "Left Arm Chinaman"),
            ("Cameron Green", "C Green", PlayerRole.AR, 9.0, "Right Handed", "Right Arm Fast Medium"),
            ("Will Jacks", "W Jacks", PlayerRole.AR, 8.5, "Right Handed", "Right Arm Off Break"),
            ("Yash Dayal", "Y Dayal", PlayerRole.BOWL, 7.5, None, "Left Arm Fast Medium"),
        ]

        # === SRH PLAYERS ===
        srh_players = [
            ("Travis Head", "T Head", PlayerRole.BAT, 10.0, "Left Handed", None),
            ("Abhishek Sharma", "A Sharma", PlayerRole.BAT, 8.5, "Left Handed", "Left Arm Orthodox"),
            ("Heinrich Klaasen", "H Klaasen", PlayerRole.WK, 10.0, "Right Handed", None),
            ("Aiden Markram", "A Markram", PlayerRole.BAT, 8.5, "Right Handed", "Right Arm Off Break"),
            ("Pat Cummins", "P Cummins", PlayerRole.BOWL, 9.5, "Right Handed", "Right Arm Fast"),
            ("Bhuvneshwar Kumar", "B Kumar", PlayerRole.BOWL, 8.5, None, "Right Arm Medium Fast"),
            ("T Natarajan", "T Natarajan", PlayerRole.BOWL, 8.0, None, "Left Arm Medium Fast"),
            ("Rahul Tripathi", "R Tripathi", PlayerRole.BAT, 7.5, "Right Handed", None),
            ("Abdul Samad", "A Samad", PlayerRole.AR, 7.5, "Right Handed", "Right Arm Leg Break"),
            ("Washington Sundar", "W Sundar", PlayerRole.AR, 8.0, "Left Handed", "Right Arm Off Break"),
            ("Marco Jansen", "M Jansen", PlayerRole.AR, 9.0, "Left Handed", "Left Arm Fast"),
            ("Umran Malik", "U Malik", PlayerRole.BOWL, 7.5, None, "Right Arm Fast"),
            ("Nitish Kumar Reddy", "N Reddy", PlayerRole.AR, 8.0, "Right Handed", "Right Arm Medium"),
            ("Glenn Phillips", "G Phillips", PlayerRole.WK, 8.0, "Right Handed", "Right Arm Leg Break"),
            ("Jaydev Unadkat", "J Unadkat", PlayerRole.BOWL, 7.0, None, "Left Arm Medium Fast"),
            ("Mayank Agarwal", "M Agarwal", PlayerRole.BAT, 7.5, "Right Handed", None),
        ]

        all_match_players = []

        for name, short, role, credits, bat_style, bowl_style in rcb_players:
            p = Player(name=name, short_name=short, role=role, default_credits=credits,
                       country="India" if not any(x in name for x in ["du Plessis", "Maxwell", "Hasaranga", "Hazlewood", "Green", "Jacks"]) else "Overseas",
                       batting_style=bat_style, bowling_style=bowl_style)
            session.add(p)
            await session.flush()
            mp = MatchPlayer(match_id=match.id, player_id=p.id, team="RCB", credits=credits, is_playing=True)
            session.add(mp)
            await session.flush()
            all_match_players.append(mp)

        for name, short, role, credits, bat_style, bowl_style in srh_players:
            p = Player(name=name, short_name=short, role=role, default_credits=credits,
                       country="India" if not any(x in name for x in ["Head", "Klaasen", "Markram", "Cummins", "Jansen", "Phillips"]) else "Overseas",
                       batting_style=bat_style, bowling_style=bowl_style)
            session.add(p)
            await session.flush()
            mp = MatchPlayer(match_id=match.id, player_id=p.id, team="SRH", credits=credits, is_playing=True)
            session.add(mp)
            await session.flush()
            all_match_players.append(mp)

        # === CONTESTS ===
        mega_breakdown = json.dumps([
            {"rank": 1, "prize": 2000}, {"rank": 2, "prize": 1000},
            {"rank_from": 3, "rank_to": 5, "prize": 500},
            {"rank_from": 6, "rank_to": 10, "prize": 100},
        ])
        mega = Contest(
            match_id=match.id, name="Mega Contest", type=ContestType.MEGA,
            entry_fee=50, total_prize_pool=5000, max_spots=100,
            max_teams_per_user=3, is_guaranteed=True,
            prize_breakdown=mega_breakdown, winner_count=10,
            created_by_id=admin.id,
        )
        session.add(mega)

        h2h_breakdown = json.dumps([{"rank": 1, "prize": 200}])
        h2h = Contest(
            match_id=match.id, name="Head to Head", type=ContestType.HEAD_TO_HEAD,
            entry_fee=100, total_prize_pool=200, max_spots=2,
            max_teams_per_user=1, is_guaranteed=False,
            prize_breakdown=h2h_breakdown, winner_count=1,
            created_by_id=admin.id,
        )
        session.add(h2h)

        await session.commit()

        print("\n=== SEED COMPLETE ===")
        print(f"Admin: naik.swaraj2007@gmail.com / admin123")
        print(f"Users: player1-5@test.com / test123")
        print(f"Tournament: {tournament.name}")
        print(f"Match: RCB vs SRH (ID: {match.id})")
        print(f"RCB Players: {len(rcb_players)}")
        print(f"SRH Players: {len(srh_players)}")
        print(f"Total MatchPlayers: {len(all_match_players)}")
        print(f"Contests: Mega Contest, Head to Head")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
