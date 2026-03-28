"""Contest join and prize distribution service.

Pool System:
- Total pool = entry_fee × number of participants
- 1st place: 50% of pool
- 2nd place: 30% of pool
- 3rd place: 20% of pool
"""

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

# Prize distribution percentages
PRIZE_SPLIT = {
    1: 0.50,  # 1st place: 50%
    2: 0.30,  # 2nd place: 30%
    3: 0.20,  # 3rd place: 20%
}


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

    # Deduct entry fee from wallet
    await wallet_service.deduct_entry_fee(session, user_id, contest.entry_fee, contest_id)

    entry = ContestEntry(contest_id=contest_id, user_id=user_id, team_id=team_id)
    session.add(entry)
    contest.filled_spots += 1

    # Update the live pool amount (pool = entry_fee × participants)
    contest.total_prize_pool = contest.entry_fee * contest.filled_spots

    if contest.filled_spots >= contest.max_spots:
        contest.status = ContestStatus.FULL

    await session.commit()
    await session.refresh(entry)
    return entry


async def distribute_prizes(session: AsyncSession, contest_id: int):
    """Distribute prizes using pool system: 50% / 30% / 20% to top 3."""
    contest = (await session.execute(select(Contest).where(Contest.id == contest_id))).scalars().first()
    if not contest:
        raise NotFoundException("Contest not found")

    entries = list((await session.execute(
        select(ContestEntry)
        .where(ContestEntry.contest_id == contest_id)
        .options(selectinload(ContestEntry.team))
    )).scalars().all())

    if not entries:
        contest.status = ContestStatus.COMPLETED
        await session.commit()
        return

    # Sort by fantasy points (highest first)
    sorted_entries = sorted(entries, key=lambda e: e.team.total_points if e.team else 0, reverse=True)

    # Calculate pool: entry_fee × number of participants
    pool = contest.entry_fee * len(sorted_entries)
    contest.total_prize_pool = pool

    # Assign ranks and distribute prizes (50% / 30% / 20%)
    for rank_idx, entry in enumerate(sorted_entries):
        entry.rank = rank_idx + 1
        entry.total_points = entry.team.total_points if entry.team else 0

        # Prize for top 3
        percentage = PRIZE_SPLIT.get(entry.rank, 0)
        prize_amount = round(pool * percentage, 2)

        entry.prize = prize_amount
        if prize_amount > 0:
            await wallet_service.credit_winning(session, entry.user_id, prize_amount, contest_id)

    contest.winner_count = min(3, len(sorted_entries))
    contest.status = ContestStatus.COMPLETED
    await session.commit()
