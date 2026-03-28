"""Wallet routes: balance and transaction history."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.dependencies.auth import get_current_user
from src.api.exceptions import NotFoundException, ValidationException
from src.api.schemas.common import APIResponse
from src.db.models import Transaction, User, Wallet
from src.db.session import get_session

router = APIRouter()


class WalletResponse(BaseModel):
    id: int
    balance: float
    total_winnings: float
    total_entry_fees: float
    pending_dues: float
    pending_receive: float

    model_config = {"from_attributes": True}


class TransactionResponse(BaseModel):
    id: int
    type: str
    status: str
    amount: float
    balance_after: float
    description: str
    created_at: str

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    transactions: list[TransactionResponse]


@router.get("", response_model=APIResponse[WalletResponse])
async def get_wallet(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get user's wallet and balance."""
    result = await session.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    wallet = result.scalars().first()
    if not wallet:
        raise NotFoundException("Wallet not found")

    return APIResponse(
        success=True,
        message="Wallet fetched",
        data=WalletResponse.model_validate(wallet),
    )


@router.get("/transactions", response_model=APIResponse[TransactionListResponse])
async def get_transactions(
    type: str | None = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get user's transaction history."""
    query = select(Transaction).where(Transaction.user_id == current_user.id)
    if type:
        query = query.where(Transaction.type == type)
    query = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit)

    result = await session.execute(query)
    transactions = result.scalars().all()

    return APIResponse(
        success=True,
        message="Transactions fetched",
        data=TransactionListResponse(
            transactions=[TransactionResponse.model_validate(t) for t in transactions]
        ),
    )


class TopupRequest(BaseModel):
    amount: float
    note: str | None = None


@router.post("/topup", response_model=APIResponse[WalletResponse])
async def topup_wallet(
    body: TopupRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Add money to wallet (self-declared deposit)."""
    if body.amount <= 0 or body.amount > 50000:
        raise ValidationException("Amount must be between 1 and 50000")

    from src.api.services.settlement import topup_wallet as do_topup

    wallet = await do_topup(session, current_user.id, body.amount, body.note)
    await session.commit()

    return APIResponse(
        success=True,
        message="Wallet topped up successfully",
        data=WalletResponse.model_validate(wallet),
    )
