"""Peer-to-peer settlement service."""

from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.api.exceptions import NotFoundException, ValidationException
from src.api.services.wallet import get_or_create_wallet
from src.db.models.models import (
    Contest,
    ContestEntry,
    PeerSettlement,
    PeerSettlementStatus,
    Transaction,
    TransactionStatus,
    TransactionType,
)


async def create_peer_settlements(
    session: AsyncSession, contest_id: int, match_id: int
):
    """Create peer-to-peer settlement records after prize distribution."""
    contest = (
        await session.execute(select(Contest).where(Contest.id == contest_id))
    ).scalars().first()
    if not contest or contest.entry_fee <= 0:
        return

    entries = list(
        (
            await session.execute(
                select(ContestEntry)
                .where(ContestEntry.contest_id == contest_id)
                .options(selectinload(ContestEntry.user))
            )
        ).scalars().all()
    )

    if len(entries) < 2:
        return

    # Aggregate net position per user (prize_won - entry_fee)
    user_net: dict[int, float] = {}
    for entry in entries:
        net = entry.prize - contest.entry_fee
        user_net[entry.user_id] = user_net.get(entry.user_id, 0) + net

    # Split into payers (negative net) and receivers (positive net)
    payers: list[list] = []
    receivers: list[list] = []
    for uid, net in user_net.items():
        net = round(net, 2)
        if net < 0:
            payers.append([uid, abs(net)])
        elif net > 0:
            receivers.append([uid, net])

    payers.sort(key=lambda x: x[1], reverse=True)
    receivers.sort(key=lambda x: x[1], reverse=True)

    # Greedy debt simplification (Splitwise algorithm)
    settlements: list[PeerSettlement] = []
    pi, ri = 0, 0
    while pi < len(payers) and ri < len(receivers):
        payer_id, payer_amt = payers[pi]
        recv_id, recv_amt = receivers[ri]
        transfer = round(min(payer_amt, recv_amt), 2)

        if transfer > 0:
            ps = PeerSettlement(
                payer_user_id=payer_id,
                receiver_user_id=recv_id,
                match_id=match_id,
                contest_id=contest_id,
                amount=transfer,
            )
            session.add(ps)
            settlements.append(ps)

        payers[pi][1] = round(payer_amt - transfer, 2)
        receivers[ri][1] = round(recv_amt - transfer, 2)

        if payers[pi][1] <= 0:
            pi += 1
        if receivers[ri][1] <= 0:
            ri += 1

    # Update wallet pending fields based on net positions
    payer_totals: dict[int, float] = {}
    receiver_totals: dict[int, float] = {}
    for s in settlements:
        payer_totals[s.payer_user_id] = payer_totals.get(s.payer_user_id, 0) + s.amount
        receiver_totals[s.receiver_user_id] = receiver_totals.get(s.receiver_user_id, 0) + s.amount

    for uid, total in payer_totals.items():
        wallet = await get_or_create_wallet(session, uid)
        wallet.pending_dues += total

    for uid, total in receiver_totals.items():
        wallet = await get_or_create_wallet(session, uid)
        wallet.pending_receive += total

    await session.flush()


async def get_settlements_i_owe(
    session: AsyncSession,
    user_id: int,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    query = (
        select(PeerSettlement)
        .where(PeerSettlement.payer_user_id == user_id)
        .options(
            selectinload(PeerSettlement.receiver),
            selectinload(PeerSettlement.payer),
            selectinload(PeerSettlement.match),
            selectinload(PeerSettlement.contest),
        )
    )
    if status:
        query = query.where(PeerSettlement.status == PeerSettlementStatus(status))
    query = query.order_by(PeerSettlement.created_at.desc()).offset(offset).limit(limit)

    result = await session.execute(query)
    settlements = list(result.scalars().all())

    count_query = select(func.count()).select_from(PeerSettlement).where(
        PeerSettlement.payer_user_id == user_id
    )
    if status:
        count_query = count_query.where(PeerSettlement.status == PeerSettlementStatus(status))
    total = (await session.execute(count_query)).scalar() or 0

    return settlements, total


async def get_settlements_owed_to_me(
    session: AsyncSession,
    user_id: int,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    query = (
        select(PeerSettlement)
        .where(PeerSettlement.receiver_user_id == user_id)
        .options(
            selectinload(PeerSettlement.payer),
            selectinload(PeerSettlement.receiver),
            selectinload(PeerSettlement.match),
            selectinload(PeerSettlement.contest),
        )
    )
    if status:
        query = query.where(PeerSettlement.status == PeerSettlementStatus(status))
    query = query.order_by(PeerSettlement.created_at.desc()).offset(offset).limit(limit)

    result = await session.execute(query)
    settlements = list(result.scalars().all())

    count_query = select(func.count()).select_from(PeerSettlement).where(
        PeerSettlement.receiver_user_id == user_id
    )
    if status:
        count_query = count_query.where(PeerSettlement.status == PeerSettlementStatus(status))
    total = (await session.execute(count_query)).scalar() or 0

    return settlements, total


async def get_settlement_summary(session: AsyncSession, user_id: int):
    owe_result = await session.execute(
        select(func.coalesce(func.sum(PeerSettlement.amount), 0)).where(
            PeerSettlement.payer_user_id == user_id,
            PeerSettlement.status == PeerSettlementStatus.PENDING,
        )
    )
    total_i_owe = float(owe_result.scalar() or 0)

    owed_result = await session.execute(
        select(func.coalesce(func.sum(PeerSettlement.amount), 0)).where(
            PeerSettlement.receiver_user_id == user_id,
            PeerSettlement.status == PeerSettlementStatus.PENDING,
        )
    )
    total_owed_to_me = float(owed_result.scalar() or 0)

    count_result = await session.execute(
        select(func.count())
        .select_from(PeerSettlement)
        .where(
            PeerSettlement.status == PeerSettlementStatus.PENDING,
            (PeerSettlement.payer_user_id == user_id)
            | (PeerSettlement.receiver_user_id == user_id),
        )
    )
    pending_count = count_result.scalar() or 0

    return {
        "total_i_owe": round(total_i_owe, 2),
        "total_owed_to_me": round(total_owed_to_me, 2),
        "pending_count": pending_count,
    }


async def mark_paid(
    session: AsyncSession, settlement_id: int, user_id: int, note: str | None = None
):
    settlement = (
        await session.execute(
            select(PeerSettlement).where(PeerSettlement.id == settlement_id)
        )
    ).scalars().first()
    if not settlement:
        raise NotFoundException("Settlement not found")
    if settlement.payer_user_id != user_id:
        raise ValidationException("Only the payer can mark as paid")
    if settlement.status == PeerSettlementStatus.COMPLETED:
        raise ValidationException("Settlement already completed")

    settlement.payer_confirmed = True
    if note:
        settlement.settlement_note = note

    if settlement.receiver_confirmed:
        settlement.status = PeerSettlementStatus.COMPLETED
        settlement.settled_at = datetime.now(UTC)
        payer_wallet = await get_or_create_wallet(session, settlement.payer_user_id)
        payer_wallet.pending_dues = max(0, payer_wallet.pending_dues - settlement.amount)
        receiver_wallet = await get_or_create_wallet(session, settlement.receiver_user_id)
        receiver_wallet.pending_receive = max(0, receiver_wallet.pending_receive - settlement.amount)

    await session.flush()
    return settlement


async def confirm_received(
    session: AsyncSession, settlement_id: int, user_id: int, note: str | None = None
):
    settlement = (
        await session.execute(
            select(PeerSettlement).where(PeerSettlement.id == settlement_id)
        )
    ).scalars().first()
    if not settlement:
        raise NotFoundException("Settlement not found")
    if settlement.receiver_user_id != user_id:
        raise ValidationException("Only the receiver can confirm receipt")
    if settlement.status == PeerSettlementStatus.COMPLETED:
        raise ValidationException("Settlement already completed")

    settlement.receiver_confirmed = True
    if note:
        settlement.settlement_note = note

    if settlement.payer_confirmed:
        settlement.status = PeerSettlementStatus.COMPLETED
        settlement.settled_at = datetime.now(UTC)
        payer_wallet = await get_or_create_wallet(session, settlement.payer_user_id)
        payer_wallet.pending_dues = max(0, payer_wallet.pending_dues - settlement.amount)
        receiver_wallet = await get_or_create_wallet(session, settlement.receiver_user_id)
        receiver_wallet.pending_receive = max(0, receiver_wallet.pending_receive - settlement.amount)

    await session.flush()
    return settlement


async def get_contest_settlements(
    session: AsyncSession, contest_id: int, user_id: int
):
    query = (
        select(PeerSettlement)
        .where(
            PeerSettlement.contest_id == contest_id,
            (PeerSettlement.payer_user_id == user_id)
            | (PeerSettlement.receiver_user_id == user_id),
        )
        .options(
            selectinload(PeerSettlement.payer),
            selectinload(PeerSettlement.receiver),
            selectinload(PeerSettlement.match),
            selectinload(PeerSettlement.contest),
        )
        .order_by(PeerSettlement.created_at.desc())
    )
    result = await session.execute(query)
    return list(result.scalars().all())


async def topup_wallet(
    session: AsyncSession, user_id: int, amount: float, note: str | None = None
):
    wallet = await get_or_create_wallet(session, user_id)
    wallet.balance += amount

    txn = Transaction(
        wallet_id=wallet.id,
        user_id=user_id,
        type=TransactionType.TOPUP,
        status=TransactionStatus.COMPLETED,
        amount=amount,
        balance_after=wallet.balance,
        description=note or "Wallet top-up",
        reference_type="TOPUP",
    )
    session.add(txn)
    await session.flush()
    return wallet
