"""AI center matching runs

Revision ID: 0011_ai_center_matching
Revises: 0010_centers_directory
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0011_ai_center_matching"
down_revision: str | None = "0010_centers_directory"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "center_match_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("child_id", sa.String(length=36), nullable=False),
        sa.Column("requested_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("criteria_json", sa.JSON(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["requested_by_user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_center_match_runs_child_id"),
        "center_match_runs",
        ["child_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_center_match_runs_requested_by_user_id"),
        "center_match_runs",
        ["requested_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_center_match_runs_created_at"),
        "center_match_runs",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_center_match_runs_created_at"), table_name="center_match_runs")
    op.drop_index(
        op.f("ix_center_match_runs_requested_by_user_id"),
        table_name="center_match_runs",
    )
    op.drop_index(op.f("ix_center_match_runs_child_id"), table_name="center_match_runs")
    op.drop_table("center_match_runs")
