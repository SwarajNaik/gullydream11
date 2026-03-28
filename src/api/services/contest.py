"""Contest join and prize distribution service."""

import json
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.api.exceptions import ConflictException, NotFoundException, ValidationException
from src.api.services import wallet as wallet_service
from src.db.models.models import (
    Contest,
    ContestEntry,
    ContestStatus,
    Match,
    Team,
)


async def join_contest(
    session: AsyncSession, user_id: int, contest_id: int, team_id: int
) -> ContestEntry:
    contest = (await session.execute(select(Contest).where(Contest.id == contest_id))).scalars().first()
    if not contest:
        raise NotFoundException("Contest not found")

    match = (await session.execute(select(Match).where(Match.id == contest.match_id))).scalars().first()
    if not match:
        raise NotFoundException("Match not found")
    if datetime.utcnow() >= match.lock_time:
        raise ValidationException("Match is locked")
    if contest.filled_spots >= contest.max_spots:
        raise ValidationException("Contest is full")

    team = (await session.execute(select(Team).where(Team.id == team_id))).scalars().first()
    if not team or team.user_id != user_id or team.match_id != contest.match_id:
        raise ValidationException("Invalid team for this contest")

    existing = list((await session.execute(
        select(ContestEntry).where(ContestEntry.contest_id == contest_id, ContestEntry.user_id == user_id)
    )).scalars().all())
    if len(existing) >= contest.max_teams_per_user:
        raise ValidationException(f"Max {contest.max_teams_per_user} teams per contest")

    dup = (await session.execute(
        select(ContestEntry).where(ContestEntry.contest_id == contest_id, ContestEntry.team_id == team_id)
    )).scalars().first()
    if dup:
        raise ConflictException("Team already in this contest")

    await wallet_service.deduct_entry_fee(session, user_id, contest.entry_fee, contest_id)

    entry = ContestEntry(contest_id=contest_id, user_id=user_id, team_id=team_id)
    session.add(entry)
    contest.filled_spots += 1
    if contest.filled_spots >= contest.max_spots:
        contest.status = ContestStatus.FULL

    await session.commit()
    await session.refresh(entry)
    return entry


async def distribute_prizes(session: AsyncSession, contest_id: int):
    contest = (await session.execute(select(Contest).where(Contest.id == contest_id))).scalars().first()
    if not contest:
        raise NotFoundException("Contest not found")

    entries = list((await session.execute(
        select(ContestEntry)
        .where(ContestEntry.contest_id == contest_id)
        .options(selectinload(ContestEntry.team))
    )).scalars().all())

    sorted_entries = sorted(entries, key=lambda e: e.team.total_points if e.team else 0, reverse=True)

    breakdown = json.loads(contest.prize_breakdown) if contest.prize_breakdown else []

    for rank_idx, entry in enumerate(sorted_entries):
        entry.rank = rank_idx + 1
        entry.total_points = entry.team.total_points if entry.team else 0

        prize_amount = 0.0
        for tier in breakdown:
            if "rank" in tier and tier["rank"] == entry.rank:
                prize_amount = tier.get("prize", 0)
                break
            elif "rank_from" in tier and "rank_to" in tier:
                if tier["rank_from"] <= entry.rank <= tier["rank_to"]:
                    prize_amount = tier.get("prize", 0)
                    break

        entry.prize = prize_amount
        if prize_amount > 0:
            await wallet_service.credit_winning(session, entry.user_id, prize_amount, contest_id)

    # Create peer-to-peer settlement records
    if contest.entry_fee > 0:
        from src.api.services.settlement import create_peer_settlements
        await create_peer_settlements(session, contest_id, contest.match_id)

    contest.status = ContestStatus.COMPLETED
    await session.commit()
