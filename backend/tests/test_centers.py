from __future__ import annotations

from app.db.session import SessionLocal
from app.models.center import Center


def register(client, email: str):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "مستخدم دليل المراكز",
            "password": "StrongPass123!",
            "role": "guardian",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_header(auth):
    return {"Authorization": f"Bearer {auth['access_token']}"}


def add_center(
    *,
    name: str,
    city: str,
    specialties: list[str],
    services: list[str],
    min_age: int = 2,
    max_age: int | None = 12,
    in_person: bool = True,
    remote: bool = False,
    active: bool = True,
) -> str:
    with SessionLocal() as db:
        center = Center(
            name=name,
            description="وصف تجريبي واضح لخدمات المركز.",
            city=city,
            region="منطقة تجريبية",
            address="عنوان تجريبي",
            specialties=specialties,
            services=services,
            served_needs=["دعم التواصل"],
            min_age_years=min_age,
            max_age_years=max_age,
            offers_in_person=in_person,
            offers_remote=remote,
            phone="+966 50 000 0000",
            email="center@example.test",
            working_hours="الأحد–الخميس، 8:00 ص–6:00 م",
            price_range="متوسط",
            is_active=active,
        )
        db.add(center)
        db.commit()
        db.refresh(center)
        return center.id


def test_centers_directory_requires_authentication(client):
    assert client.get("/api/v1/centers").status_code == 401
    assert client.get("/api/v1/centers/filter-options").status_code == 401


def test_center_search_and_filters_can_be_combined(client):
    auth = register(client, "centers.filters@example.com")
    headers = auth_header(auth)
    add_center(
        name="مركز التواصل التجريبي",
        city="الرياض",
        specialties=["النطق والتخاطب"],
        services=["جلسات تخاطب", "تدريب الأسرة"],
        min_age=1,
        max_age=12,
        in_person=True,
        remote=True,
    )
    add_center(
        name="مركز الحركة التجريبي",
        city="جدة",
        specialties=["العلاج الطبيعي"],
        services=["جلسات علاج طبيعي"],
        min_age=13,
        max_age=21,
        in_person=True,
        remote=False,
    )

    searched = client.get("/api/v1/centers?q=تخاطب", headers=headers)
    assert searched.status_code == 200, searched.text
    assert [item["name"] for item in searched.json()] == ["مركز التواصل التجريبي"]

    filtered = client.get(
        "/api/v1/centers",
        headers=headers,
        params={
            "city": "الرياض",
            "specialty": "النطق والتخاطب",
            "delivery_mode": "both",
            "age_group": "6-12",
        },
    )
    assert filtered.status_code == 200, filtered.text
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["offers_remote"] is True

    older = client.get(
        "/api/v1/centers",
        headers=headers,
        params={"age_group": "13-18", "service": "جلسات علاج طبيعي"},
    )
    assert [item["city"] for item in older.json()] == ["جدة"]


def test_center_detail_hides_inactive_centers(client):
    auth = register(client, "centers.detail@example.com")
    headers = auth_header(auth)
    active_id = add_center(
        name="مركز نشط تجريبي",
        city="الخبر",
        specialties=["التدخل المبكر"],
        services=["تقييم المهارات"],
    )
    inactive_id = add_center(
        name="مركز غير نشط",
        city="الخبر",
        specialties=["التدخل المبكر"],
        services=["تقييم المهارات"],
        active=False,
    )

    detail = client.get(f"/api/v1/centers/{active_id}", headers=headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["name"] == "مركز نشط تجريبي"

    listed = client.get("/api/v1/centers", headers=headers)
    assert [item["id"] for item in listed.json()] == [active_id]
    assert client.get(f"/api/v1/centers/{inactive_id}", headers=headers).status_code == 404


def test_favorites_are_idempotent_and_private_to_current_user(client):
    first = register(client, "centers.favorite.one@example.com")
    second = register(client, "centers.favorite.two@example.com")
    center_id = add_center(
        name="مركز مفضل تجريبي",
        city="الرياض",
        specialties=["العلاج الوظيفي"],
        services=["تقييم وظيفي"],
    )

    first_headers = auth_header(first)
    added_once = client.put(
        f"/api/v1/centers/{center_id}/favorite", headers=first_headers
    )
    added_twice = client.put(
        f"/api/v1/centers/{center_id}/favorite", headers=first_headers
    )
    assert added_once.status_code == 200
    assert added_twice.status_code == 200
    assert added_twice.json()["is_favorite"] is True

    favorites = client.get(
        "/api/v1/centers?favorites_only=true", headers=first_headers
    )
    assert [item["id"] for item in favorites.json()] == [center_id]

    second_detail = client.get(
        f"/api/v1/centers/{center_id}", headers=auth_header(second)
    )
    assert second_detail.json()["is_favorite"] is False

    removed = client.delete(
        f"/api/v1/centers/{center_id}/favorite", headers=first_headers
    )
    removed_again = client.delete(
        f"/api/v1/centers/{center_id}/favorite", headers=first_headers
    )
    assert removed.status_code == 204
    assert removed_again.status_code == 204
    assert client.get(
        "/api/v1/centers?favorites_only=true", headers=first_headers
    ).json() == []


def test_filter_options_only_include_active_centers(client):
    auth = register(client, "centers.options@example.com")
    headers = auth_header(auth)
    add_center(
        name="مركز خيارات تجريبي",
        city="أبها",
        specialties=["السمعيات"],
        services=["فحوصات سمع"],
    )
    add_center(
        name="مركز مخفي",
        city="مدينة مخفية",
        specialties=["تخصص مخفي"],
        services=["خدمة مخفية"],
        active=False,
    )

    response = client.get("/api/v1/centers/filter-options", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json() == {
        "cities": ["أبها"],
        "specialties": ["السمعيات"],
        "services": ["فحوصات سمع"],
    }


def test_invalid_directory_filter_is_rejected(client):
    auth = register(client, "centers.invalid@example.com")
    response = client.get(
        "/api/v1/centers?delivery_mode=unknown",
        headers=auth_header(auth),
    )
    assert response.status_code == 422
