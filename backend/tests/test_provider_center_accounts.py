def register(client, email: str, role: str):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "حساب مركز تجريبي",
            "password": "StrongPass123!",
            "role": role,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def headers(auth):
    return {"Authorization": f"Bearer {auth['access_token']}"}


def center_payload():
    return {
        "name": "مركز بوابة النمو التجريبي",
        "description": "مركز تجريبي يقدم خدمات دعم متكاملة للأطفال والأسر.",
        "city": "الرياض",
        "region": "منطقة الرياض",
        "address": "عنوان تجريبي",
        "specialties": ["النطق والتخاطب"],
        "services": ["جلسات تخاطب"],
        "served_needs": ["دعم التواصل"],
        "min_age_years": 2,
        "max_age_years": 14,
        "offers_in_person": True,
        "offers_remote": True,
        "phone": "+966 50 000 0400",
        "email": "center-profile@example.com",
        "working_hours": "الأحد–الخميس، 8 ص–6 م",
        "price_range": "متوسط",
    }


def test_center_account_manages_profile_and_specialists(client):
    center_auth = register(client, "m7.center@example.com", "center")
    dashboard = client.get("/api/v1/provider/dashboard", headers=headers(center_auth))
    assert dashboard.status_code == 200
    assert dashboard.json()["center"] is None

    created = client.post(
        "/api/v1/provider/center",
        headers=headers(center_auth),
        json=center_payload(),
    )
    assert created.status_code == 201, created.text
    assert created.json()["verification_status"] == "unverified"

    specialist = client.post(
        "/api/v1/provider/center/specialists",
        headers=headers(center_auth),
        json={
            "full_name": "أ. نورة التجريبية",
            "professional_title": "أخصائية تخاطب",
            "specialty": "النطق والتخاطب",
            "bio": "خبرة تجريبية في دعم التواصل.",
        },
    )
    assert specialist.status_code == 201, specialist.text
    assert client.get(
        "/api/v1/provider/center/specialists",
        headers=headers(center_auth),
    ).json()[0]["full_name"] == "أ. نورة التجريبية"

    updated = client.patch(
        "/api/v1/provider/center",
        headers=headers(center_auth),
        json={"phone": "+966 50 000 0411"},
    )
    assert updated.status_code == 200
    assert updated.json()["phone"].endswith("0411")


def test_center_sees_only_children_explicitly_shared_with_its_account(client):
    guardian = register(client, "m7.guardian@example.com", "guardian")
    center_auth = register(client, "m7.access.center@example.com", "center")
    child = client.post(
        "/api/v1/children",
        headers=headers(guardian),
        json={
            "first_name": "تاليا",
            "conditions": [],
            "needs": ["دعم التواصل"],
            "support_requirements": [],
            "services": [],
        },
    ).json()
    assert client.get("/api/v1/children", headers=headers(center_auth)).json() == []

    invitation = client.post(
        f"/api/v1/children/{child['id']}/care-team/invitations",
        headers=headers(guardian),
        json={
            "email": center_auth["user"]["email"],
            "target_role": "center",
            "role_label": "مركز داعم",
            "permissions": ["view_profile", "view_care_team", "message_team"],
        },
    )
    assert invitation.status_code == 201, invitation.text
    accepted = client.post(
        f"/api/v1/care-team/invitations/{invitation.json()['id']}/accept",
        headers=headers(center_auth),
    )
    assert accepted.status_code == 200, accepted.text
    visible = client.get("/api/v1/children", headers=headers(center_auth))
    assert visible.status_code == 200
    assert [item["id"] for item in visible.json()] == [child["id"]]
