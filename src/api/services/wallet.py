"""Wallet operations service."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.db.models.models import Transaction, TransactionStatus, TransactionType, Wallet


async def get_or_create_wallet(session: AsyncSession, user_id: int) -> Wallet:
    result = await session.execute(select(Wallet).where(Wallet.user_id == user_id))
    wallet = result.scalars().first()
    if not wallet:
        wallet = Wallet(user_id=user_id)
        session.add(wallet)
        await session.flush()
    return wallet


async def deduct_entry_fee(session: AsyncSession, user_id: int, amount: float, contest_id: int) -> Transaction:
    wallet = await get_or_create_wallet(session, user_id)
    if wallet.balance >= amount:
        wallet.balance -= amount
    else:
        wallet.pending_dues += amount
    wallet.total_entry_fees += amount

    txn = Transaction(
        wallet_id=wallet.id, user_id=user_id,
        type=TransactionType.ENTRY_FEE, status=TransactionStatus.COMPLETED,
        amount=-amount, balance_after=wallet.balance,
        description=f"Entry fee for contest #{contest_id}",
        reference_id=str(contest_id), reference_type="CONTEST",
    )
    session.add(txn)
    return txn


async def credit_winning(session: AsyncSession, user_id: int, amount: float, contest_id: int) -> Transaction:
    wallet = await get_or_create_wallet(session, user_id)
    wallet.balance += amount
    wallet.total_winnings += amount

    txn = Transaction(
        wallet_id=wallet.id, user_id=user_id,
        type=TransactionType.WINNING, status=TransactionStatus.COMPLETED,
        amount=amount, balance_after=wallet.balance,
        description=f"Prize from contest #{contest_id}",
        reference_id=str(contest_id), reference_type="CONTEST",
    )
    session.add(txn)
    return txn
