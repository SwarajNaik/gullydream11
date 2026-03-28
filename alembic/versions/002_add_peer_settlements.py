"""add peer settlements table and TOPUP transaction type

Revision ID: 002
Revises:
Create Date: 2026-03-28
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add TOPUP to transactiontype enum
    op.execute("ALTER TYPE transactiontype ADD VALUE IF NOT EXISTS 'TOPUP'")

    # Create peersettlementstatus enum
    peersettlementstatus = sa.Enum(
        "PENDING", "COMPLETED", "DISPUTED", name="peersettlementstatus"
    )
    peersettlementstatus.create(op.get_bind(), checkfirst=True)

    # Create peer_settlements table
    op.create_table(
        "peer_settlements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("payer_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("receiver_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("match_id", sa.Integer(), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("contest_id", sa.Integer(), sa.ForeignKey("contests.id"), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("payer_confirmed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("receiver_confirmed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "COMPLETED", "DISPUTED", name="peersettlementstatus", create_type=False),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("settlement_note", sa.String(500), nullable=True),
        sa.Column("settled_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )

    op.create_index("ix_peer_settlements_payer_user_id", "peer_settlements", ["payer_user_id"])
    op.create_index("ix_peer_settlements_receiver_user_id", "peer_settlements", ["receiver_user_id"])
    op.create_index("ix_peer_settlements_match_id", "peer_settlements", ["match_id"])
    op.create_index("ix_peer_settlements_contest_id", "peer_settlements", ["contest_id"])


def downgrade() -> None:
    op.drop_table("peer_settlements")
    op.execute("DROP TYPE IF EXISTS peersettlementstatus")
