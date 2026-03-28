"""Background scheduler for live data sync.

Runs periodic tasks:
- Sync upcoming matches every 6 hours
- Fetch live scores every 2 minutes during active matches
"""

import asyncio
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.config import settings
from src.db.models.models import Match, MatchStatus
from src.db.session import async_session

logger = logging.getLogger(__name__)

# Track API match IDs for live score polling
# Format: {our_match_id: api_match_id}
live_match_api_ids: dict[int, str] = {}

_scheduler_task: asyncio.Task | None = None


async def _sync_matches_job():
    """Background job: sync matches from CricAPI."""
    if not settings.CRICKET_API_KEY:
        return

    try:
        from src.api.services.cricket_data import sync_current_matches
        async with async_session() as session:
            result = await sync_current_matches(session)
            logger.info(f"Match sync complete: {len(result)} matches synced")
    except Exception as e:
        logger.error(f"Match sync failed: {e}")


async def _sync_live_scores_job():
    """Background job: fetch live scores for all LIVE matches."""
    if not settings.CRICKET_API_KEY:
        return

    try:
        from src.api.services.cricket_data import sync_live_scores
        async with async_session() as session:
            live_matches = (await session.execute(
                select(Match).where(Match.status == MatchStatus.LIVE)
            )).scalars().all()

            for match in live_matches:
                api_id = live_match_api_ids.get(match.id)
                if api_id:
                    try:
                        result = await sync_live_scores(session, match.id, api_id)
                        logger.info(f"Live scores updated for match {match.id}: {result}")
                    except Exception as e:
                        logger.error(f"Live score sync failed for match {match.id}: {e}")
    except Exception as e:
        logger.error(f"Live scores job failed: {e}")


async def scheduler_loop():
    """Main scheduler loop — runs match sync and live score polling."""
    logger.info("Scheduler started")
    match_sync_interval = 6 * 60 * 60  # 6 hours
    live_score_interval = 120  # 2 minutes

    last_match_sync = 0
    last_live_sync = 0

    while True:
        now = datetime.utcnow().timestamp()

        # Sync matches periodically
        if now - last_match_sync > match_sync_interval:
            await _sync_matches_job()
            last_match_sync = now

        # Sync live scores more frequently
        if now - last_live_sync > live_score_interval:
            await _sync_live_scores_job()
            last_live_sync = now

        await asyncio.sleep(30)  # Check every 30 seconds


def start_scheduler():
    """Start the background scheduler as an asyncio task."""
    global _scheduler_task
    if settings.CRICKET_API_KEY:
        _scheduler_task = asyncio.create_task(scheduler_loop())
        logger.info("Background scheduler started")
    else:
        logger.warning("CRICKET_API_KEY not set — scheduler disabled")


def stop_scheduler():
    """Stop the background scheduler."""
    global _scheduler_task
    if _scheduler_task:
        _scheduler_task.cancel()
        _scheduler_task = None
