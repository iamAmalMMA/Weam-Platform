"""communication unread, sharing and attachments

Revision ID: 0012_communication_upgrade
Revises: 0011_ai_center_matching
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0012_communication_upgrade"
down_revision: str | None = "0011_ai_center_matching"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("chat_messages", "body", existing_type=sa.Text(), nullable=True)
    op.add_column(
        "chat_messages",
        sa.Column("message_type", sa.String(length=24), server_default="text", nullable=False),
    )
    op.add_column("chat_messages", sa.Column("shared_entity_type", sa.String(length=32), nullable=True))
    op.add_column("chat_messages", sa.Column("shared_entity_id", sa.String(length=36), nullable=True))
    op.add_column("chat_messages", sa.Column("shared_entity_title", sa.String(length=220), nullable=True))
    op.create_index(op.f("ix_chat_messages_message_type"), "chat_messages", ["message_type"], unique=False)

    op.create_table(
        "chat_attachments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("message_id", sa.String(length=36), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=80), nullable=False),
        sa.Column("storage_key", sa.String(length=700), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index(op.f("ix_chat_attachments_message_id"), "chat_attachments", ["message_id"], unique=False)

    op.create_table(
        "message_read_receipts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("message_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "user_id", name="uq_message_read_user"),
    )
    op.create_index(op.f("ix_message_read_receipts_message_id"), "message_read_receipts", ["message_id"], unique=False)
    op.create_index(op.f("ix_message_read_receipts_user_id"), "message_read_receipts", ["user_id"], unique=False)
    # Existing conversations predate read receipts; keep their historical messages read.
    op.execute(
        """
        INSERT INTO message_read_receipts (id, message_id, user_id, read_at)
        SELECT
            substr(md5(m.id || ':' || p.user_id), 1, 8) || '-' ||
            substr(md5(m.id || ':' || p.user_id), 9, 4) || '-' ||
            substr(md5(m.id || ':' || p.user_id), 13, 4) || '-' ||
            substr(md5(m.id || ':' || p.user_id), 17, 4) || '-' ||
            substr(md5(m.id || ':' || p.user_id), 21, 12),
            m.id,
            p.user_id,
            m.created_at
        FROM chat_messages AS m
        JOIN conversation_participants AS p ON p.conversation_id = m.conversation_id
        WHERE p.user_id <> m.sender_user_id
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_message_read_receipts_user_id"), table_name="message_read_receipts")
    op.drop_index(op.f("ix_message_read_receipts_message_id"), table_name="message_read_receipts")
    op.drop_table("message_read_receipts")
    op.drop_index(op.f("ix_chat_attachments_message_id"), table_name="chat_attachments")
    op.drop_table("chat_attachments")
    op.drop_index(op.f("ix_chat_messages_message_type"), table_name="chat_messages")
    op.drop_column("chat_messages", "shared_entity_title")
    op.drop_column("chat_messages", "shared_entity_id")
    op.drop_column("chat_messages", "shared_entity_type")
    op.drop_column("chat_messages", "message_type")
    op.execute("UPDATE chat_messages SET body = '' WHERE body IS NULL")
    op.alter_column("chat_messages", "body", existing_type=sa.Text(), nullable=False)
