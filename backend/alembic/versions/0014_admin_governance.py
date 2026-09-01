"""admin governance and verification

Revision ID: 0014_admin_governance
Revises: 0013_center_accounts
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0014_admin_governance"
down_revision: str | None = "0013_center_accounts"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("verification_note", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("verified_by_user_id", sa.String(length=36), nullable=True))
    op.create_foreign_key("fk_users_verified_by", "users", "users", ["verified_by_user_id"], ["id"])

    op.add_column(
        "centers",
        sa.Column("verification_status", sa.String(length=24), server_default="unverified", nullable=False),
    )
    op.add_column("centers", sa.Column("verification_note", sa.Text(), nullable=True))
    op.add_column("centers", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("centers", sa.Column("verified_by_user_id", sa.String(length=36), nullable=True))
    op.create_foreign_key("fk_centers_verified_by", "centers", "users", ["verified_by_user_id"], ["id"])
    op.create_index(op.f("ix_centers_verification_status"), "centers", ["verification_status"], unique=False)
    op.execute("UPDATE centers SET verification_status = 'verified' WHERE id LIKE 'c4000000-%'")

    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("actor_user_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_audit_logs_actor_user_id"), "admin_audit_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_admin_audit_logs_action"), "admin_audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_admin_audit_logs_entity_type"), "admin_audit_logs", ["entity_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_audit_logs_entity_type"), table_name="admin_audit_logs")
    op.drop_index(op.f("ix_admin_audit_logs_action"), table_name="admin_audit_logs")
    op.drop_index(op.f("ix_admin_audit_logs_actor_user_id"), table_name="admin_audit_logs")
    op.drop_table("admin_audit_logs")
    op.drop_index(op.f("ix_centers_verification_status"), table_name="centers")
    op.drop_constraint("fk_centers_verified_by", "centers", type_="foreignkey")
    op.drop_column("centers", "verified_by_user_id")
    op.drop_column("centers", "verified_at")
    op.drop_column("centers", "verification_note")
    op.drop_column("centers", "verification_status")
    op.drop_constraint("fk_users_verified_by", "users", type_="foreignkey")
    op.drop_column("users", "verified_by_user_id")
    op.drop_column("users", "verified_at")
    op.drop_column("users", "verification_note")
