"""Update player images using CricAPI player IDs.

Image URL pattern: https://h.cricapi.com/img/players/{api_player_id}.jpg
We fetch the squad to get API IDs, then construct image URLs without extra API calls.
"""

import asyncio
import os
import ssl
import sys

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from src.db.models.models import Player

API_KEY = os.getenv("CRICKET_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "")
MATCH_API_ID = "55fe0f15-6eb0-4ad5-835b-5564be4f6a21"


async def main():
    # Fetch squad to get player API IDs
    print("Fetching squad from CricAPI...")
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            "https://api.cricapi.com/v1/match_squad",
            params={"apikey": API_KEY, "id": MATCH_API_ID},
        )
        data = resp.json()

    # Build name -> image URL mapping
    image_map = {}
    for team in data.get("data", []):
        for p in team.get("players", []):
            name = p.get("name", "")
            api_id = p.get("id", "")
            if name and api_id:
                image_map[name.lower()] = f"https://h.cricapi.com/img/players/{api_id}.jpg"

    print(f"Found {len(image_map)} player image URLs")

    # Connect to DB and update
    db_url = DATABASE_URL.split("?")[0]
    connect_args = {}
    if "neon.tech" in DATABASE_URL:
        connect_args["ssl"] = ssl.create_default_context()

    engine = create_async_engine(db_url, echo=False, connect_args=connect_args)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        players = (await session.execute(select(Player))).scalars().all()
        updated = 0
        for player in players:
            img_url = image_map.get(player.name.lower())
            if img_url:
                player.image_url = img_url
                updated += 1
                print(f"  {player.name}: {img_url}")

        await session.commit()
        print(f"\nUpdated {updated}/{len(players)} player images")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
