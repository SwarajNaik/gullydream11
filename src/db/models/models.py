"""All domain models — consolidated to avoid circular imports."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Enum, Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlmodel import Field, Relationship, SQLModel


# ========================
# Helpers
# ========================

def _JSONB():
    """JSONB column with SQLite fallback for tests."""
    return Column(JSONB().with_variant(JSON(), "sqlite"), default={})


class TimeStampedModel(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ========================
# ENUMS
# ========================

class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class PlayerRole(str, enum.Enum):
    WK = "WK"
    BAT = "BAT"
    AR = "AR"
    BOWL = "BOWL"

class SportType(str, enum.Enum):
    CRICKET = "CRICKET"

class TournamentStatus(str, enum.Enum):
    UPCOMING = "UPCOMING"
    LIVE = "LIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class MatchStatus(str, enum.Enum):
    UPCOMING = "UPCOMING"
    LINEUPS_OUT = "LINEUPS_OUT"
    LIVE = "LIVE"
    IN_REVIEW = "IN_REVIEW"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ABANDONED = "ABANDONED"

class MatchFormat(str, enum.Enum):
    T20 = "T20"
    ODI = "ODI"
    TEST = "TEST"
    T10 = "T10"

class ContestType(str, enum.Enum):
    MEGA = "MEGA"
    HEAD_TO_HEAD = "HEAD_TO_HEAD"
    SMALL = "SMALL"
    PRACTICE = "PRACTICE"
    PRIVATE = "PRIVATE"

class ContestStatus(str, enum.Enum):
    UPCOMING = "UPCOMING"
    LIVE = "LIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FULL = "FULL"

class TransactionType(str, enum.Enum):
    ENTRY_FEE = "ENTRY_FEE"
    WINNING = "WINNING"
    REFUND = "REFUND"
    ADMIN_CREDIT = "ADMIN_CREDIT"
    ADMIN_DEBIT = "ADMIN_DEBIT"
    SETTLEMENT_PAID = "SETTLEMENT_PAID"
    SETTLEMENT_RECEIVED = "SETTLEMENT_RECEIVED"
    TOPUP = "TOPUP"

class TransactionStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    FAILED = "FAILED"
    REVERSED = "REVERSED"

class SettlementStatus(str, enum.Enum):
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    COMPLETED = "COMPLETED"


class PeerSettlementStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    DISPUTED = "DISPUTED"


# ========================
# USER & WALLET
# ========================

class User(TimeStampedModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    username: str = Field(index=True, unique=True, max_length=50)
    password_hash: str = Field(max_length=255)
    display_name: str = Field(max_length=100)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    role: UserRole = Field(default=UserRole.USER, sa_column=Column(Enum(UserRole), default="USER"))
    is_active: bool = Field(default=True)
    total_matches: int = Field(default=0)
    total_winnings: float = Field(default=0.0)
    total_contests: int = Field(default=0)
    skill_score: float = Field(default=0.0)

    wallet: Optional["Wallet"] = Relationship(back_populates="user")
    teams: list["Team"] = Relationship(back_populates="user")
    contest_entries: list["ContestEntry"] = Relationship(back_populates="user")
    transactions: list["Transaction"] = Relationship(back_populates="user")


class Wallet(TimeStampedModel, table=True):
    __tablename__ = "wallets"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)
    balance: float = Field(default=0.0)
    total_winnings: float = Field(default=0.0)
    total_entry_fees: float = Field(default=0.0)
    pending_dues: float = Field(default=0.0)
    pending_receive: float = Field(default=0.0)

    user: Optional[User] = Relationship(back_populates="wallet")
    transactions: list["Transaction"] = Relationship(back_populates="wallet")


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"
    id: Optional[int] = Field(default=None, primary_key=True)
    wallet_id: int = Field(foreign_key="wallets.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    type: TransactionType = Field(sa_column=Column(Enum(TransactionType)))
    status: TransactionStatus = Field(default=TransactionStatus.COMPLETED, sa_column=Column(Enum(TransactionStatus), default="COMPLETED"))
    amount: float = Field()
    balance_after: float = Field()
    description: str = Field(max_length=500)
    reference_id: Optional[str] = Field(default=None, max_length=100)
    reference_type: Optional[str] = Field(default=None, max_length=50)
    settled_by: Optional[str] = Field(default=None, max_length=100)
    settled_at: Optional[datetime] = Field(default=None)
    settlement_note: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    wallet: Optional[Wallet] = Relationship(back_populates="transactions")
    user: Optional[User] = Relationship(back_populates="transactions")


# ========================
# TOURNAMENT & MATCH
# ========================

class Tournament(TimeStampedModel, table=True):
    __tablename__ = "tournaments"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200)
    short_name: str = Field(max_length=20)
    sport: SportType = Field(default=SportType.CRICKET, sa_column=Column(Enum(SportType), default="CRICKET"))
    status: TournamentStatus = Field(default=TournamentStatus.UPCOMING, sa_column=Column(Enum(TournamentStatus), default="UPCOMING"))
    start_date: datetime = Field()
    end_date: datetime = Field()
    image_url: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None)
    created_by_id: int = Field()

    matches: list["Match"] = Relationship(back_populates="tournament")


class Match(TimeStampedModel, table=True):
    __tablename__ = "matches"
    id: Optional[int] = Field(default=None, primary_key=True)
    tournament_id: int = Field(foreign_key="tournaments.id", index=True)
    team_a: str = Field(max_length=100)
    team_a_short: str = Field(max_length=10)
    team_a_logo: Optional[str] = Field(default=None, max_length=500)
    team_b: str = Field(max_length=100)
    team_b_short: str = Field(max_length=10)
    team_b_logo: Optional[str] = Field(default=None, max_length=500)
    format: MatchFormat = Field(default=MatchFormat.T20, sa_column=Column(Enum(MatchFormat), default="T20"))
    status: MatchStatus = Field(default=MatchStatus.UPCOMING, sa_column=Column(Enum(MatchStatus), default="UPCOMING"))
    venue: Optional[str] = Field(default=None, max_length=200)
    start_time: datetime = Field(index=True)
    lock_time: datetime = Field()
    result_summary: Optional[str] = Field(default=None, max_length=500)

    tournament: Optional[Tournament] = Relationship(back_populates="matches")
    players: list["MatchPlayer"] = Relationship(back_populates="match")
    contests: list["Contest"] = Relationship(back_populates="match")
    teams: list["Team"] = Relationship(back_populates="match")


# ========================
# PLAYER & SCORING
# ========================

class Player(TimeStampedModel, table=True):
    __tablename__ = "players"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=200)
    short_name: str = Field(max_length=50)
    image_url: Optional[str] = Field(default=None, max_length=500)
    country: Optional[str] = Field(default=None, max_length=100)
    role: PlayerRole = Field(sa_column=Column(Enum(PlayerRole)))
    batting_style: Optional[str] = Field(default=None, max_length=100)
    bowling_style: Optional[str] = Field(default=None, max_length=100)
    default_credits: float = Field(default=8.0)

    match_players: list["MatchPlayer"] = Relationship(back_populates="player")
    team_players: list["TeamPlayer"] = Relationship(back_populates="player")
    player_scores: list["PlayerScore"] = Relationship(back_populates="player")


class MatchPlayer(SQLModel, table=True):
    __tablename__ = "match_players"
    id: Optional[int] = Field(default=None, primary_key=True)
    match_id: int = Field(foreign_key="matches.id", index=True)
    player_id: int = Field(foreign_key="players.id", index=True)
    team: str = Field(max_length=50)
    credits: float = Field()
    is_playing: Optional[bool] = Field(default=None)
    selection_pct: float = Field(default=0.0)
    captain_pct: float = Field(default=0.0)
    vice_captain_pct: float = Field(default=0.0)

    match: Optional[Match] = Relationship(back_populates="players")
    player: Optional[Player] = Relationship(back_populates="match_players")
    player_score: Optional["PlayerScore"] = Relationship(back_populates="match_player")
    team_players: list["TeamPlayer"] = Relationship(back_populates="match_player")


class PlayerScore(TimeStampedModel, table=True):
    __tablename__ = "player_scores"
    id: Optional[int] = Field(default=None, primary_key=True)
    match_player_id: int = Field(foreign_key="match_players.id", unique=True)
    player_id: int = Field(foreign_key="players.id", index=True)
    match_id: int = Field(index=True)
    runs: int = Field(default=0)
    balls: int = Field(default=0)
    fours: int = Field(default=0)
    sixes: int = Field(default=0)
    overs: float = Field(default=0.0)
    wickets: int = Field(default=0)
    runs_conceded: int = Field(default=0)
    maidens: int = Field(default=0)
    catches: int = Field(default=0)
    stumpings: int = Field(default=0)
    run_outs: int = Field(default=0)
    fantasy_points: float = Field(default=0.0)
    is_starting_xi: bool = Field(default=True)

    match_player: Optional[MatchPlayer] = Relationship(back_populates="player_score")
    player: Optional[Player] = Relationship(back_populates="player_scores")


# ========================
# CONTEST
# ========================

class Contest(TimeStampedModel, table=True):
    __tablename__ = "contests"
    id: Optional[int] = Field(default=None, primary_key=True)
    match_id: int = Field(foreign_key="matches.id", index=True)
    name: str = Field(max_length=200)
    type: ContestType = Field(default=ContestType.MEGA, sa_column=Column(Enum(ContestType), default="MEGA"))
    status: ContestStatus = Field(default=ContestStatus.UPCOMING, sa_column=Column(Enum(ContestStatus), default="UPCOMING"))
    entry_fee: float = Field()
    total_prize_pool: float = Field()
    max_spots: int = Field()
    filled_spots: int = Field(default=0)
    max_teams_per_user: int = Field(default=1)
    is_guaranteed: bool = Field(default=False)
    prize_breakdown: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON string
    winner_count: int = Field(default=1)
    invite_code: Optional[str] = Field(default=None, unique=True, max_length=20)
    created_by_id: int = Field()

    match: Optional[Match] = Relationship(back_populates="contests")
    entries: list["ContestEntry"] = Relationship(back_populates="contest")


# ========================
# TEAM & ENTRIES
# ========================

class Team(TimeStampedModel, table=True):
    __tablename__ = "teams"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    match_id: int = Field(foreign_key="matches.id", index=True)
    name: str = Field(default="Team 1", max_length=100)
    captain_id: int = Field()
    vice_captain_id: int = Field()
    total_credits: float = Field()
    total_points: float = Field(default=0.0)

    user: Optional[User] = Relationship(back_populates="teams")
    match: Optional[Match] = Relationship(back_populates="teams")
    players: list["TeamPlayer"] = Relationship(back_populates="team")
    contest_entries: list["ContestEntry"] = Relationship(back_populates="team")


class TeamPlayer(SQLModel, table=True):
    __tablename__ = "team_players"
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="teams.id", index=True)
    match_player_id: int = Field(foreign_key="match_players.id")
    player_id: int = Field(foreign_key="players.id")
    is_captain: bool = Field(default=False)
    is_vice_captain: bool = Field(default=False)
    points: float = Field(default=0.0)

    team: Optional[Team] = Relationship(back_populates="players")
    match_player: Optional[MatchPlayer] = Relationship(back_populates="team_players")
    player: Optional[Player] = Relationship(back_populates="team_players")


class ContestEntry(SQLModel, table=True):
    __tablename__ = "contest_entries"
    id: Optional[int] = Field(default=None, primary_key=True)
    contest_id: int = Field(foreign_key="contests.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    team_id: int = Field(foreign_key="teams.id")
    rank: Optional[int] = Field(default=None)
    prize: float = Field(default=0.0)
    total_points: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    contest: Optional[Contest] = Relationship(back_populates="entries")
    user: Optional[User] = Relationship(back_populates="contest_entries")
    team: Optional[Team] = Relationship(back_populates="contest_entries")


# ========================
# SETTLEMENT
# ========================

class Settlement(TimeStampedModel, table=True):
    __tablename__ = "settlements"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    match_id: Optional[int] = Field(default=None)
    contest_id: Optional[int] = Field(default=None)
    type: str = Field(max_length=50)
    amount: float = Field()
    status: SettlementStatus = Field(default=SettlementStatus.PENDING, sa_column=Column(Enum(SettlementStatus), default="PENDING"))
    settled_amount: float = Field(default=0.0)
    settlement_mode: Optional[str] = Field(default=None, max_length=50)
    settlement_note: Optional[str] = Field(default=None, max_length=500)
    settled_by: Optional[str] = Field(default=None, max_length=100)
    settled_at: Optional[datetime] = Field(default=None)


class PeerSettlement(TimeStampedModel, table=True):
    __tablename__ = "peer_settlements"
    id: Optional[int] = Field(default=None, primary_key=True)
    payer_user_id: int = Field(foreign_key="users.id", index=True)
    receiver_user_id: int = Field(foreign_key="users.id", index=True)
    match_id: int = Field(foreign_key="matches.id", index=True)
    contest_id: int = Field(foreign_key="contests.id", index=True)
    amount: float = Field()
    payer_confirmed: bool = Field(default=False)
    receiver_confirmed: bool = Field(default=False)
    status: PeerSettlementStatus = Field(
        default=PeerSettlementStatus.PENDING,
        sa_column=Column(Enum(PeerSettlementStatus), default="PENDING"),
    )
    settlement_note: Optional[str] = Field(default=None, max_length=500)
    settled_at: Optional[datetime] = Field(default=None)

    payer: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[PeerSettlement.payer_user_id]"}
    )
    receiver: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[PeerSettlement.receiver_user_id]"}
    )
    match: Optional["Match"] = Relationship()
    contest: Optional["Contest"] = Relationship()
