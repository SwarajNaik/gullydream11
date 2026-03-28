"""Model registry — all models imported here so SQLModel.metadata is complete."""

from src.db.models.models import (
    Contest,
    ContestEntry,
    ContestStatus,
    ContestType,
    Match,
    MatchFormat,
    MatchPlayer,
    MatchStatus,
    PeerSettlement,
    PeerSettlementStatus,
    Player,
    PlayerRole,
    PlayerScore,
    Settlement,
    SettlementStatus,
    SportType,
    Team,
    TeamPlayer,
    TimeStampedModel,
    Tournament,
    TournamentStatus,
    Transaction,
    TransactionStatus,
    TransactionType,
    User,
    UserRole,
    Wallet,
)

__all_models__ = [
    User, Wallet, Transaction, Player, MatchPlayer, PlayerScore,
    Tournament, Match, Contest, ContestEntry, Team, TeamPlayer,
    Settlement, PeerSettlement,
]
