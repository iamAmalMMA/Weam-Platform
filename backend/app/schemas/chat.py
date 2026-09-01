from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ConversationCreate(BaseModel):
    kind: Literal["direct", "group"]
    title: str | None = Field(default=None, max_length=180)
    participant_user_ids: list[str] = Field(min_length=1, max_length=30)

    @field_validator("participant_user_ids")
    @classmethod
    def unique_participants(cls, values: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            cleaned = value.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                result.append(cleaned)
        return result


class ConversationParticipantPublic(BaseModel):
    user_id: str
    full_name: str
    role_label: str | None = None


class MessageCreate(BaseModel):
    body: str | None = Field(default=None, max_length=4000)
    shared_entity_type: Literal["report", "goal", "follow_up"] | None = None
    shared_entity_id: str | None = Field(default=None, max_length=36)

    @field_validator("body")
    @classmethod
    def clean_body(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def require_content(self):
        if self.shared_entity_type and not self.shared_entity_id:
            raise ValueError("shared_entity_id is required")
        if self.shared_entity_id and not self.shared_entity_type:
            raise ValueError("shared_entity_type is required")
        if not self.body and not self.shared_entity_type:
            raise ValueError("Message cannot be empty")
        return self


class ChatAttachmentPublic(BaseModel):
    id: str
    original_filename: str
    content_type: str
    size_bytes: int
    download_url: str


class SharedItemPublic(BaseModel):
    entity_type: Literal["report", "goal", "follow_up"]
    entity_id: str
    title: str
    url: str


class ShareableItemPublic(BaseModel):
    entity_type: Literal["report", "goal", "follow_up"]
    entity_id: str
    title: str
    subtitle: str | None = None


class ChatMessagePublic(BaseModel):
    id: str
    conversation_id: str
    sender_user_id: str
    sender_name: str
    body: str
    message_type: Literal["text", "attachment", "shared"]
    attachments: list[ChatAttachmentPublic]
    shared_item: SharedItemPublic | None
    is_read: bool
    read_by_count: int
    is_read_by_everyone: bool
    created_at: datetime


class ConversationPublic(BaseModel):
    id: str
    child_id: str
    kind: Literal["direct", "group"]
    title: str
    participants: list[ConversationParticipantPublic]
    last_message: ChatMessagePublic | None
    unread_count: int
    created_at: datetime
    updated_at: datetime


class ChatUnreadCountPublic(BaseModel):
    count: int


class MarkConversationReadPublic(BaseModel):
    conversation_id: str
    marked_count: int
    unread_count: int = 0
