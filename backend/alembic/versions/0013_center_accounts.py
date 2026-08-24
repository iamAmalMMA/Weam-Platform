"""center accounts and specialists

Revision ID: 0013_center_accounts
Revises: 0012_communication_upgrade
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0013_center_accounts"
down_revision: str | None = "0012_communication_upgrade"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "center_account_memberships",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("center_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("account_role", sa.String(length=24), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["center_id"], ["centers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("center_id", "user_id", name="uq_center_account_user"),
    )
    op.create_index(op.f("ix_center_account_memberships_center_id"), "center_account_memberships", ["center_id"], unique=False)
    op.create_index(op.f("ix_center_account_memberships_user_id"), "center_account_memberships", ["user_id"], unique=False)

    op.create_table(
        "center_specialists",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("center_id", sa.String(length=36), nullable=False),
        sa.Column("full_name", sa.String(length=180), nullable=False),
        sa.Column("professional_title", sa.String(length=140), nullable=False),
        sa.Column("specialty", sa.String(length=140), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["center_id"], ["centers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_center_specialists_center_id"), "center_specialists", ["center_id"], unique=False)
    op.create_index(op.f("ix_center_specialists_specialty"), "center_specialists", ["specialty"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_center_specialists_specialty"), table_name="center_specialists")
    op.drop_index(op.f("ix_center_specialists_center_id"), table_name="center_specialists")
    op.drop_table("center_specialists")
    op.drop_index(op.f("ix_center_account_memberships_user_id"), table_name="center_account_memberships")
    op.drop_index(op.f("ix_center_account_memberships_center_id"), table_name="center_account_memberships")
    op.drop_table("center_account_memberships")
