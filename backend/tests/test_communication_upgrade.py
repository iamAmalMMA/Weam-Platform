from app.db.session import SessionLocal
from app.models.goal import Goal


def register(client, email: str, role: str, specialty: str | None = None):
    payload = {
        "email": email,
        "full_name": email.split("@")[0],
        "password": "StrongPass123!",
        "role": role,
    }
    if specialty:
        payload["provider_specialty"] = specialty
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def headers(auth):
    return {"Authorization": f"Bearer {auth['access_token']}"}


def create_child(client, guardian, name="تاليا"):
    response = client.post(
        "/api/v1/children",
        headers=headers(guardian),
        json={
            "first_name": name,
            "conditions": [],
            "needs": ["دعم التواصل"],
            "support_requirements": [],
            "services": ["تخاطب"],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def invite_provider(client, guardian, provider, child):
    response = client.post(
        f"/api/v1/children/{child['id']}/care-team/invitations",
        headers=headers(guardian),
        json={
            "email": provider["user"]["email"],
            "target_role": provider["user"]["role"],
            "permissions": [
                "view_profile",
                "view_care_team",
                "view_goals",
                "message_team",
            ],
        },
    )
    assert response.status_code == 201, response.text
    accepted = client.post(
        f"/api/v1/care-team/invitations/{response.json()['id']}/accept",
        headers=headers(provider),
    )
    assert accepted.status_code == 200, accepted.text


def conversation(client, guardian, provider, child):
    response = client.post(
        f"/api/v1/children/{child['id']}/conversations",
        headers=headers(guardian),
        json={
            "kind": "direct",
            "participant_user_ids": [provider["user"]["id"]],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_unread_count_and_read_receipts(client):
    guardian = register(client, "m6.guardian@example.com", "guardian")
    provider = register(client, "m6.provider@example.com", "care_provider", "تخاطب")
    child = create_child(client, guardian)
    invite_provider(client, guardian, provider, child)
    chat = conversation(client, guardian, provider, child)

    sent = client.post(
        f"/api/v1/conversations/{chat['id']}/messages",
        headers=headers(provider),
        json={"body": "تمت مراجعة الخطة."},
    )
    assert sent.status_code == 201, sent.text

    unread = client.get("/api/v1/chat/unread-count", headers=headers(guardian))
    assert unread.status_code == 200
    assert unread.json()["count"] == 1
    listed = client.get(
        f"/api/v1/children/{child['id']}/conversations",
        headers=headers(guardian),
    )
    assert listed.json()[0]["unread_count"] == 1

    marked = client.post(
        f"/api/v1/conversations/{chat['id']}/read",
        headers=headers(guardian),
    )
    assert marked.status_code == 200
    assert marked.json()["marked_count"] == 1
    assert client.get("/api/v1/chat/unread-count", headers=headers(guardian)).json()["count"] == 0

    provider_view = client.get(
        f"/api/v1/conversations/{chat['id']}/messages",
        headers=headers(provider),
    )
    assert provider_view.json()[0]["is_read_by_everyone"] is True


def test_share_goal_opens_the_shared_item(client):
    guardian = register(client, "share.guardian@example.com", "guardian")
    provider = register(client, "share.provider@example.com", "care_provider", "علاج وظيفي")
    child = create_child(client, guardian)
    invite_provider(client, guardian, provider, child)
    chat = conversation(client, guardian, provider, child)

    goal_response = client.post(
        f"/api/v1/children/{child['id']}/goals",
        headers=headers(guardian),
        json={"title": "تحسين التواصل اليومي"},
    )
    assert goal_response.status_code == 201, goal_response.text
    goal = goal_response.json()

    shared = client.post(
        f"/api/v1/conversations/{chat['id']}/messages",
        headers=headers(guardian),
        json={
            "body": "للمراجعة",
            "shared_entity_type": "goal",
            "shared_entity_id": goal["id"],
        },
    )
    assert shared.status_code == 201, shared.text
    payload = shared.json()
    assert payload["message_type"] == "shared"
    assert payload["shared_item"]["title"] == "تحسين التواصل اليومي"
    assert payload["shared_item"]["url"].endswith(f"goals?goal={goal['id']}")

    other_child = create_child(client, guardian, "سارة")
    with SessionLocal() as db:
        other_goal = Goal(
            child_id=other_child["id"],
            title="هدف خاص",
            created_by_user_id=guardian["user"]["id"],
        )
        db.add(other_goal)
        db.commit()
        db.refresh(other_goal)
        other_goal_id = other_goal.id
    blocked = client.post(
        f"/api/v1/conversations/{chat['id']}/messages",
        headers=headers(guardian),
        json={"shared_entity_type": "goal", "shared_entity_id": other_goal_id},
    )
    assert blocked.status_code == 404


def test_private_chat_attachment_requires_conversation_access(client):
    guardian = register(client, "file.guardian@example.com", "guardian")
    provider = register(client, "file.provider@example.com", "care_provider", "سمعيات")
    outsider = register(client, "file.outsider@example.com", "care_provider", "تخاطب")
    child = create_child(client, guardian)
    invite_provider(client, guardian, provider, child)
    chat = conversation(client, guardian, provider, child)

    uploaded = client.post(
        f"/api/v1/conversations/{chat['id']}/attachments",
        headers=headers(guardian),
        data={"body": "صورة المتابعة"},
        files={"file": ("follow-up.png", b"\x89PNG\r\n\x1a\ncontent", "image/png")},
    )
    assert uploaded.status_code == 201, uploaded.text
    attachment = uploaded.json()["attachments"][0]

    download_url = f"/api/v1{attachment['download_url']}"
    downloaded = client.get(download_url, headers=headers(provider))
    assert downloaded.status_code == 200
    assert downloaded.content.startswith(b"\x89PNG")
    blocked = client.get(download_url, headers=headers(outsider))
    assert blocked.status_code == 404


def test_shared_item_keeps_its_own_view_permission(client):
    guardian = register(client, "private.share.guardian@example.com", "guardian")
    provider = register(client, "private.share.provider@example.com", "care_provider", "تخاطب")
    child = create_child(client, guardian)
    invitation = client.post(
        f"/api/v1/children/{child['id']}/care-team/invitations",
        headers=headers(guardian),
        json={
            "email": provider["user"]["email"],
            "target_role": "care_provider",
            "permissions": ["view_profile", "view_care_team", "message_team"],
        },
    )
    client.post(
        f"/api/v1/care-team/invitations/{invitation.json()['id']}/accept",
        headers=headers(provider),
    )
    chat = conversation(client, guardian, provider, child)
    goal = client.post(
        f"/api/v1/children/{child['id']}/goals",
        headers=headers(guardian),
        json={"title": "هدف لا يملك المختص صلاحية عرضه"},
    ).json()
    sent = client.post(
        f"/api/v1/conversations/{chat['id']}/messages",
        headers=headers(guardian),
        json={"shared_entity_type": "goal", "shared_entity_id": goal["id"]},
    )
    assert sent.status_code == 201
    provider_messages = client.get(
        f"/api/v1/conversations/{chat['id']}/messages",
        headers=headers(provider),
    )
    assert provider_messages.status_code == 200
    assert provider_messages.json()[0]["shared_item"] is None
