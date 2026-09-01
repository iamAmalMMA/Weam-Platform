from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.constants import CarePermission
from app.db.session import SessionLocal, get_db
from app.models.care_team import AccessAuditLog, CareTeamMembership
from app.models.chat import (
    ChatAttachment,
    ChatMessage,
    Conversation,
    ConversationParticipant,
    MessageReadReceipt,
)
from app.models.child import GuardianMembership
from app.models.follow_up import FollowUp
from app.models.goal import Goal
from app.models.report import Report
from app.models.user import User
from app.schemas.chat import (
    ChatAttachmentPublic,
    ChatMessagePublic,
    ChatUnreadCountPublic,
    ConversationCreate,
    ConversationParticipantPublic,
    ConversationPublic,
    MarkConversationReadPublic,
    MessageCreate,
    ShareableItemPublic,
    SharedItemPublic,
)
from app.services.access import membership_is_active, require_child_access
from app.services.follow_up_notifications import can_view_follow_ups
from app.services.security import decode_token
from app.services.storage import LocalChatStorage, StorageValidationError

router = APIRouter(tags=["chat"])


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ConversationSocketManager:
    def __init__(self) -> None:
        self.connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, conversation_id: str, websocket: WebSocket) -> None:
        self.connections[conversation_id].add(websocket)

    def disconnect(self, conversation_id: str, websocket: WebSocket) -> None:
        sockets = self.connections.get(conversation_id)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self.connections.pop(conversation_id, None)

    async def broadcast(self, conversation_id: str, payload: dict) -> None:
        stale: list[WebSocket] = []
        for websocket in list(self.connections.get(conversation_id, set())):
            try:
                await websocket.send_json(payload)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(conversation_id, websocket)


socket_manager = ConversationSocketManager()


def _audit(
    db: Session,
    *,
    child_id: str,
    actor_user_id: str,
    action: str,
    entity_id: str,
    details: dict | None = None,
) -> None:
    db.add(
        AccessAuditLog(
            child_id=child_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type="conversation",
            entity_id=entity_id,
            details=details or {},
        )
    )


def _conversation_query(conversation_id: str):
    return (
        select(Conversation)
        .options(selectinload(Conversation.participants))
        .where(Conversation.id == conversation_id)
    )


def _conversation_or_404(db: Session, conversation_id: str) -> Conversation:
    conversation = db.scalar(_conversation_query(conversation_id))
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def _participant_user_ids(conversation: Conversation) -> set[str]:
    return {participant.user_id for participant in conversation.participants}


def _require_conversation_access(
    db: Session,
    conversation: Conversation,
    user: User,
):
    grant = require_child_access(
        db,
        conversation.child_id,
        user,
        CarePermission.MESSAGE_TEAM.value,
    )
    if user.id not in _participant_user_ids(conversation):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return grant


def _active_team_user_ids(db: Session, child_id: str) -> set[str]:
    active: set[str] = set()

    guardians = db.scalars(
        select(GuardianMembership).where(
            GuardianMembership.child_id == child_id
        )
    ).all()
    for membership in guardians:
        if membership_is_active(
            membership.access_status,
            membership.expires_at,
        ):
            active.add(membership.guardian_user_id)

    providers = db.scalars(
        select(CareTeamMembership).where(
            CareTeamMembership.child_id == child_id
        )
    ).all()
    for membership in providers:
        if (
            membership_is_active(
                membership.access_status,
                membership.expires_at,
            )
            and CarePermission.MESSAGE_TEAM.value
            in (membership.permissions or [])
        ):
            active.add(membership.user_id)

    return active


def _role_label(db: Session, child_id: str, user_id: str) -> str | None:
    guardian = db.scalar(
        select(GuardianMembership).where(
            GuardianMembership.child_id == child_id,
            GuardianMembership.guardian_user_id == user_id,
        )
    )
    if guardian:
        return guardian.role_label or (
            "ولي أمر رئيسي"
            if guardian.guardian_type == "primary"
            else "ولي أمر"
        )

    provider = db.scalar(
        select(CareTeamMembership).where(
            CareTeamMembership.child_id == child_id,
            CareTeamMembership.user_id == user_id,
        )
    )
    return provider.role_label if provider else None


def _shared_url(message: ChatMessage) -> str | None:
    if not message.shared_entity_type or not message.shared_entity_id:
        return None
    if message.shared_entity_type == "report":
        return f"/children/{message.conversation.child_id}/reports?report={message.shared_entity_id}"
    if message.shared_entity_type == "goal":
        return f"/children/{message.conversation.child_id}/goals?goal={message.shared_entity_id}"
    if message.shared_entity_type == "follow_up":
        return f"/children/{message.conversation.child_id}/follow-ups?follow_up={message.shared_entity_id}"
    return None


def _serialize_message(
    db: Session,
    message: ChatMessage,
    current_user_id: str,
    participant_count: int | None = None,
) -> ChatMessagePublic:
    sender = db.get(User, message.sender_user_id)
    receipts = db.scalars(
        select(MessageReadReceipt).where(MessageReadReceipt.message_id == message.id)
    ).all()
    receipt_user_ids = {receipt.user_id for receipt in receipts}
    if participant_count is None:
        participant_count = db.scalar(
            select(func.count(ConversationParticipant.id)).where(
                ConversationParticipant.conversation_id == message.conversation_id
            )
        ) or 1
    shared_url = _shared_url(message)
    shared_title = message.shared_entity_title
    if shared_url and message.shared_entity_type and message.shared_entity_id:
        viewer = db.get(User, current_user_id)
        try:
            if not viewer:
                raise HTTPException(status_code=404, detail="User not found")
            shared_title, shared_url = _resolve_shared_entity(
                db,
                message.conversation,
                viewer,
                message.shared_entity_type,
                message.shared_entity_id,
            )
        except HTTPException:
            # A conversation membership never bypasses the item's own permission.
            shared_url = None
            shared_title = None
    return ChatMessagePublic(
        id=message.id,
        conversation_id=message.conversation_id,
        sender_user_id=message.sender_user_id,
        sender_name=sender.full_name if sender else "عضو فريق الرعاية",
        body=message.body or (
            "هذا العنصر غير متاح ضمن صلاحياتك."
            if message.message_type == "shared" and shared_url is None
            else ""
        ),
        message_type=message.message_type,
        attachments=[
            ChatAttachmentPublic(
                id=item.id,
                original_filename=item.original_filename,
                content_type=item.content_type,
                size_bytes=item.size_bytes,
                download_url=f"/chat-attachments/{item.id}/download",
            )
            for item in message.attachments
        ],
        shared_item=(
            SharedItemPublic(
                entity_type=message.shared_entity_type,
                entity_id=message.shared_entity_id,
                title=shared_title or "عنصر مشترك",
                url=shared_url,
            )
            if shared_url
            else None
        ),
        is_read=(message.sender_user_id == current_user_id or current_user_id in receipt_user_ids),
        read_by_count=len(receipt_user_ids),
        is_read_by_everyone=len(receipt_user_ids) >= max(participant_count - 1, 0),
        created_at=message.created_at,
    )


def _unread_count(db: Session, conversation_id: str, user_id: str) -> int:
    receipt_exists = select(MessageReadReceipt.id).where(
        MessageReadReceipt.message_id == ChatMessage.id,
        MessageReadReceipt.user_id == user_id,
    ).exists()
    return int(
        db.scalar(
            select(func.count(ChatMessage.id)).where(
                ChatMessage.conversation_id == conversation_id,
                ChatMessage.sender_user_id != user_id,
                ~receipt_exists,
            )
        )
        or 0
    )


def _resolve_shared_entity(
    db: Session,
    conversation: Conversation,
    user: User,
    entity_type: str,
    entity_id: str,
) -> tuple[str, str]:
    grant = require_child_access(db, conversation.child_id, user)
    if entity_type == "report":
        if not grant.allows(CarePermission.VIEW_REPORTS.value):
            raise HTTPException(status_code=403, detail="Insufficient permission")
        item = db.get(Report, entity_id)
        if (
            not item
            or item.child_id != conversation.child_id
            or item.is_archived
            or not (
                grant.is_primary_guardian
                or item.visibility == "care_team"
                or user.id in (item.allowed_user_ids or [])
            )
        ):
            raise HTTPException(status_code=404, detail="Report not found")
        return item.title, f"/children/{conversation.child_id}/reports?report={item.id}"
    if entity_type == "goal":
        if not grant.allows(CarePermission.VIEW_GOALS.value):
            raise HTTPException(status_code=403, detail="Insufficient permission")
        item = db.get(Goal, entity_id)
        if not item or item.child_id != conversation.child_id:
            raise HTTPException(status_code=404, detail="Goal not found")
        return item.title, f"/children/{conversation.child_id}/goals?goal={item.id}"
    if entity_type == "follow_up":
        if not can_view_follow_ups(grant):
            raise HTTPException(status_code=403, detail="Insufficient permission")
        item = db.get(FollowUp, entity_id)
        if not item or item.child_id != conversation.child_id:
            raise HTTPException(status_code=404, detail="Follow-up not found")
        return item.title, f"/children/{conversation.child_id}/follow-ups?follow_up={item.id}"
    raise HTTPException(status_code=422, detail="Unsupported shared item")


def _conversation_title(
    db: Session,
    conversation: Conversation,
    current_user_id: str,
) -> str:
    if conversation.title:
        return conversation.title

    people = []
    for participant in conversation.participants:
        if conversation.kind == "direct" and participant.user_id == current_user_id:
            continue
        user = db.get(User, participant.user_id)
        if user:
            people.append(user.full_name)

    if conversation.kind == "direct":
        return people[0] if people else "محادثة مباشرة"
    return " · ".join(people[:3]) or "مجموعة فريق الرعاية"


def _serialize_conversation(
    db: Session,
    conversation: Conversation,
    current_user_id: str,
) -> ConversationPublic:
    participants: list[ConversationParticipantPublic] = []
    for participant in conversation.participants:
        user = db.get(User, participant.user_id)
        if not user:
            continue
        participants.append(
            ConversationParticipantPublic(
                user_id=user.id,
                full_name=user.full_name,
                role_label=_role_label(
                    db,
                    conversation.child_id,
                    user.id,
                ),
            )
        )

    last = db.scalar(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(1)
    )

    return ConversationPublic(
        id=conversation.id,
        child_id=conversation.child_id,
        kind=conversation.kind,
        title=_conversation_title(
            db,
            conversation,
            current_user_id,
        ),
        participants=participants,
        last_message=(
            _serialize_message(
                db,
                last,
                current_user_id,
                participant_count=len(conversation.participants),
            )
            if last
            else None
        ),
        unread_count=_unread_count(db, conversation.id, current_user_id),
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.get(
    "/children/{child_id}/conversations",
    response_model=list[ConversationPublic],
)
def list_conversations(
    child_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ConversationPublic]:
    require_child_access(
        db,
        child_id,
        user,
        CarePermission.MESSAGE_TEAM.value,
    )

    conversations = db.scalars(
        select(Conversation)
        .join(ConversationParticipant)
        .options(selectinload(Conversation.participants))
        .where(
            Conversation.child_id == child_id,
            ConversationParticipant.user_id == user.id,
        )
        .order_by(Conversation.updated_at.desc())
    ).unique().all()

    return [
        _serialize_conversation(db, conversation, user.id)
        for conversation in conversations
    ]


@router.get("/chat/unread-count", response_model=ChatUnreadCountPublic)
def chat_unread_count(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatUnreadCountPublic:
    conversations = db.scalars(
        select(Conversation)
        .join(ConversationParticipant)
        .options(selectinload(Conversation.participants))
        .where(ConversationParticipant.user_id == user.id)
    ).unique().all()
    total = 0
    for conversation in conversations:
        try:
            _require_conversation_access(db, conversation, user)
        except HTTPException:
            continue
        total += _unread_count(db, conversation.id, user.id)
    return ChatUnreadCountPublic(count=total)


@router.get(
    "/children/{child_id}/shareable-items",
    response_model=list[ShareableItemPublic],
)
def shareable_items(
    child_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ShareableItemPublic]:
    grant = require_child_access(db, child_id, user, CarePermission.MESSAGE_TEAM.value)
    output: list[ShareableItemPublic] = []

    if grant.allows(CarePermission.VIEW_REPORTS.value):
        reports = db.scalars(
            select(Report)
            .where(Report.child_id == child_id, Report.is_archived.is_(False))
            .order_by(Report.updated_at.desc())
            .limit(30)
        ).all()
        for item in reports:
            if (
                grant.is_primary_guardian
                or item.visibility == "care_team"
                or user.id in (item.allowed_user_ids or [])
            ):
                output.append(
                    ShareableItemPublic(
                        entity_type="report",
                        entity_id=item.id,
                        title=item.title,
                        subtitle="تقرير",
                    )
                )

    if grant.allows(CarePermission.VIEW_GOALS.value):
        goals = db.scalars(
            select(Goal)
            .where(Goal.child_id == child_id)
            .order_by(Goal.updated_at.desc())
            .limit(30)
        ).all()
        output.extend(
            ShareableItemPublic(
                entity_type="goal",
                entity_id=item.id,
                title=item.title,
                subtitle="هدف",
            )
            for item in goals
        )

    if can_view_follow_ups(grant):
        follow_ups = db.scalars(
            select(FollowUp)
            .where(FollowUp.child_id == child_id)
            .order_by(FollowUp.updated_at.desc())
            .limit(30)
        ).all()
        output.extend(
            ShareableItemPublic(
                entity_type="follow_up",
                entity_id=item.id,
                title=item.title,
                subtitle="متابعة",
            )
            for item in follow_ups
        )
    return output


@router.post(
    "/children/{child_id}/conversations",
    response_model=ConversationPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    child_id: str,
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConversationPublic:
    require_child_access(
        db,
        child_id,
        user,
        CarePermission.MESSAGE_TEAM.value,
    )

    participant_ids = [
        participant_id
        for participant_id in payload.participant_user_ids
        if participant_id != user.id
    ]

    if payload.kind == "direct" and len(participant_ids) != 1:
        raise HTTPException(
            status_code=422,
            detail="Direct conversation requires exactly one other participant",
        )
    if payload.kind == "group" and len(participant_ids) < 1:
        raise HTTPException(
            status_code=422,
            detail="Group conversation requires at least one other participant",
        )

    allowed = _active_team_user_ids(db, child_id)
    if user.id not in allowed:
        allowed.add(user.id)
    unknown = [
        participant_id
        for participant_id in participant_ids
        if participant_id not in allowed
    ]
    if unknown:
        raise HTTPException(
            status_code=422,
            detail="Conversation participants must be active care-team members with messaging access",
        )

    # Reuse an existing direct conversation for the same pair.
    if payload.kind == "direct":
        candidate_ids = {user.id, participant_ids[0]}
        existing = db.scalars(
            select(Conversation)
            .options(selectinload(Conversation.participants))
            .where(
                Conversation.child_id == child_id,
                Conversation.kind == "direct",
            )
        ).all()
        for conversation in existing:
            if _participant_user_ids(conversation) == candidate_ids:
                return _serialize_conversation(db, conversation, user.id)

    clean_title = (
        " ".join(payload.title.strip().split())
        if payload.title
        else None
    )
    conversation = Conversation(
        child_id=child_id,
        kind=payload.kind,
        title=clean_title,
        created_by_user_id=user.id,
    )
    db.add(conversation)
    db.flush()

    for participant_id in [user.id, *participant_ids]:
        db.add(
            ConversationParticipant(
                conversation_id=conversation.id,
                user_id=participant_id,
            )
        )

    _audit(
        db,
        child_id=child_id,
        actor_user_id=user.id,
        action="conversation_created",
        entity_id=conversation.id,
        details={
            "kind": payload.kind,
            "participant_count": len(participant_ids) + 1,
        },
    )
    db.commit()

    conversation = _conversation_or_404(db, conversation.id)
    return _serialize_conversation(db, conversation, user.id)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[ChatMessagePublic],
)
def list_messages(
    conversation_id: str,
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ChatMessagePublic]:
    conversation = _conversation_or_404(db, conversation_id)
    _require_conversation_access(db, conversation, user)

    rows = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    ).all()
    rows.reverse()
    return [
        _serialize_message(
            db,
            message,
            user.id,
            participant_count=len(conversation.participants),
        )
        for message in rows
    ]


@router.post(
    "/conversations/{conversation_id}/read",
    response_model=MarkConversationReadPublic,
)
async def mark_conversation_read(
    conversation_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MarkConversationReadPublic:
    conversation = _conversation_or_404(db, conversation_id)
    _require_conversation_access(db, conversation, user)
    already_read = select(MessageReadReceipt.message_id).where(
        MessageReadReceipt.user_id == user.id
    )
    message_ids = db.scalars(
        select(ChatMessage.id).where(
            ChatMessage.conversation_id == conversation.id,
            ChatMessage.sender_user_id != user.id,
            ChatMessage.id.not_in(already_read),
        )
    ).all()
    for message_id in message_ids:
        db.add(MessageReadReceipt(message_id=message_id, user_id=user.id))
    if message_ids:
        db.commit()
        await socket_manager.broadcast(
            conversation.id,
            {"type": "read", "user_id": user.id, "message_ids": message_ids},
        )
    return MarkConversationReadPublic(
        conversation_id=conversation.id,
        marked_count=len(message_ids),
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatMessagePublic,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatMessagePublic:
    conversation = _conversation_or_404(db, conversation_id)
    _require_conversation_access(db, conversation, user)

    shared_title: str | None = None
    message_type = "text"
    if payload.shared_entity_type and payload.shared_entity_id:
        shared_title, _ = _resolve_shared_entity(
            db,
            conversation,
            user,
            payload.shared_entity_type,
            payload.shared_entity_id,
        )
        message_type = "shared"

    message = ChatMessage(
        conversation_id=conversation.id,
        sender_user_id=user.id,
        body=payload.body,
        message_type=message_type,
        shared_entity_type=payload.shared_entity_type,
        shared_entity_id=payload.shared_entity_id,
        shared_entity_title=shared_title,
    )
    conversation.updated_at = utcnow()
    db.add(message)
    db.add(conversation)
    db.commit()
    db.refresh(message)

    public = _serialize_message(
        db,
        message,
        user.id,
        participant_count=len(conversation.participants),
    )
    # Each participant refetches through the permission-aware REST serializer.
    await socket_manager.broadcast(conversation.id, {"type": "refresh"})
    return public


@router.post(
    "/conversations/{conversation_id}/attachments",
    response_model=ChatMessagePublic,
    status_code=status.HTTP_201_CREATED,
)
async def send_attachment(
    conversation_id: str,
    file: UploadFile = File(...),
    body: str | None = Form(default=None, max_length=4000),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatMessagePublic:
    conversation = _conversation_or_404(db, conversation_id)
    _require_conversation_access(db, conversation, user)
    attachment_id = str(uuid.uuid4())
    storage = LocalChatStorage()
    try:
        stored = storage.save_upload(
            file,
            conversation_id=conversation.id,
            attachment_id=attachment_id,
        )
    except StorageValidationError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    message = ChatMessage(
        conversation_id=conversation.id,
        sender_user_id=user.id,
        body=(body or "").strip() or None,
        message_type="attachment",
    )
    attachment = ChatAttachment(
        id=attachment_id,
        message=message,
        original_filename=(file.filename or "attachment").strip()[:255] or "attachment",
        content_type=stored.content_type,
        storage_key=stored.key,
        size_bytes=stored.size_bytes,
        sha256=stored.sha256,
    )
    conversation.updated_at = utcnow()
    db.add_all([message, attachment, conversation])
    try:
        db.commit()
    except Exception:
        db.rollback()
        storage.delete(stored.key)
        raise
    db.refresh(message)
    public = _serialize_message(
        db,
        message,
        user.id,
        participant_count=len(conversation.participants),
    )
    await socket_manager.broadcast(conversation.id, {"type": "refresh"})
    return public


@router.get("/chat-attachments/{attachment_id}/download")
def download_chat_attachment(
    attachment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    attachment = db.get(ChatAttachment, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    message = db.get(ChatMessage, attachment.message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Attachment not found")
    conversation = _conversation_or_404(db, message.conversation_id)
    _require_conversation_access(db, conversation, user)
    try:
        path = LocalChatStorage().resolve(attachment.storage_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Attachment file not found") from exc
    return FileResponse(
        path,
        media_type=attachment.content_type,
        filename=attachment.original_filename,
    )


@router.websocket("/ws/conversations/{conversation_id}")
async def conversation_socket(
    websocket: WebSocket,
    conversation_id: str,
) -> None:
    await websocket.accept()
    connected = False

    try:
        auth_payload = await websocket.receive_json()
        if (
            auth_payload.get("type") != "auth"
            or not auth_payload.get("token")
        ):
            await websocket.close(code=4401)
            return

        claims = decode_token(
            str(auth_payload["token"]),
            "access",
        )
        if not claims:
            await websocket.close(code=4401)
            return

        with SessionLocal() as db:
            user = db.get(User, claims["sub"])
            conversation = db.scalar(
                _conversation_query(conversation_id)
            )
            if not user or not conversation:
                await websocket.close(code=4404)
                return
            try:
                _require_conversation_access(
                    db,
                    conversation,
                    user,
                )
            except HTTPException:
                await websocket.close(code=4403)
                return

        await socket_manager.connect(conversation_id, websocket)
        connected = True
        await websocket.send_json({"type": "ready"})

        while True:
            payload = await websocket.receive_json()
            if payload.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        if connected:
            socket_manager.disconnect(
                conversation_id,
                websocket,
            )
