from __future__ import annotations

from datetime import date, datetime, timezone

from app.db.session import SessionLocal
from app.models.care_team import CareTeamMembership
from app.models.center import Center
from app.models.goal import Goal
from app.models.report import Report, ReportVersion
from app.models.report_ai import ReportAIAnalysis


def register(client, email: str):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "ولي أمر المطابقة",
            "password": "StrongPass123!",
            "role": "guardian",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_header(auth):
    return {"Authorization": f"Bearer {auth['access_token']}"}


def create_child(client, auth, *, needs=None, services=None, conditions=None):
    response = client.post(
        "/api/v1/children",
        headers=auth_header(auth),
        json={
            "first_name": "سارة",
            "birth_date": date(date.today().year - 8, 1, 15).isoformat(),
            "conditions": conditions or [],
            "needs": needs or [],
            "support_requirements": [],
            "services": services or [],
            "summary": "ملف رعاية تجريبي للمطابقة.",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def add_center(
    *,
    name: str,
    city: str,
    specialties: list[str],
    services: list[str],
    served_needs: list[str],
    min_age: int = 1,
    max_age: int = 18,
    remote: bool = True,
) -> str:
    with SessionLocal() as db:
        center = Center(
            name=name,
            description="مركز تعريفي تجريبي لخدمات المطابقة.",
            city=city,
            region="منطقة تجريبية",
            address="عنوان تجريبي",
            specialties=specialties,
            services=services,
            served_needs=served_needs,
            min_age_years=min_age,
            max_age_years=max_age,
            offers_in_person=True,
            offers_remote=remote,
            phone="+966 50 000 0099",
            email="matching@example.test",
            working_hours="الأحد–الخميس، 8:00 ص–6:00 م",
            price_range="متوسط",
            is_active=True,
        )
        db.add(center)
        db.commit()
        db.refresh(center)
        return center.id


def test_center_matching_uses_profile_age_city_and_delivery_mode(client):
    auth = register(client, "matching.profile@example.com")
    child = create_child(
        client,
        auth,
        needs=["دعم التواصل", "تنظيم السلوك"],
        services=["جلسات تخاطب"],
    )
    strong_id = add_center(
        name="مركز التواصل والسلوك التجريبي",
        city="الرياض",
        specialties=["النطق والتخاطب", "تعديل السلوك"],
        services=["جلسات تخاطب", "خطط تعديل السلوك"],
        served_needs=["دعم التواصل", "تنظيم السلوك"],
    )
    behavior_id = add_center(
        name="مركز السلوك التجريبي",
        city="الرياض",
        specialties=["تعديل السلوك"],
        services=["خطط تعديل السلوك"],
        served_needs=["تنظيم السلوك"],
    )
    add_center(
        name="مركز خارج المدينة",
        city="جدة",
        specialties=["النطق والتخاطب"],
        services=["جلسات تخاطب"],
        served_needs=["دعم التواصل"],
    )
    add_center(
        name="مركز خارج العمر",
        city="الرياض",
        specialties=["النطق والتخاطب"],
        services=["جلسات تخاطب"],
        served_needs=["دعم التواصل"],
        min_age=13,
        max_age=18,
    )

    headers = auth_header(auth)
    assert client.get(
        f"/api/v1/children/{child['id']}/center-matches/latest",
        headers=headers,
    ).status_code == 404

    response = client.post(
        f"/api/v1/children/{child['id']}/center-matches",
        headers=headers,
        json={"city": "الرياض", "delivery_mode": "both"},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["preferred_city"] == "الرياض"
    assert payload["child_age_years"] in {7, 8}
    assert payload["insufficient_data"] is False
    assert [item["center"]["id"] for item in payload["matches"]] == [
        strong_id,
        behavior_id,
    ]
    assert payload["matches"][0]["match_level"] == "strong"
    assert payload["matches"][0]["sources"][0]["source_type"] == "profile"
    assert "ليست تقييمًا طبيًا" in payload["safety_note"]

    latest = client.get(
        f"/api/v1/children/{child['id']}/center-matches/latest",
        headers=headers,
    )
    assert latest.status_code == 200
    assert latest.json()["id"] == payload["id"]


def test_matching_uses_only_approved_reports_and_active_goals(client):
    auth = register(client, "matching.sources@example.com")
    child = create_child(client, auth)
    user_id = auth["user"]["id"]
    center_id = add_center(
        name="مركز المهارات اليومية التجريبي",
        city="الرياض",
        specialties=["العلاج الوظيفي"],
        services=["تقييم وظيفي", "تدريب المهارات اليومية"],
        served_needs=["المهارات اليومية", "الاستقلالية"],
    )

    with SessionLocal() as db:
        report = Report(
            child_id=child["id"],
            title="تقرير وظيفي",
            report_type="occupational",
            visibility="care_team",
            allowed_user_ids=[],
            created_by_user_id=user_id,
        )
        version = ReportVersion(
            report=report,
            version_number=1,
            original_filename="report.pdf",
            content_type="application/pdf",
            storage_key="matching/report.pdf",
            size_bytes=10,
            sha256="a" * 64,
            uploaded_by_user_id=user_id,
        )
        db.add_all([report, version])
        db.flush()
        db.add(
            ReportAIAnalysis(
                child_id=child["id"],
                report_id=report.id,
                report_version_id=version.id,
                provider="mock",
                model="test",
                analysis_status="completed",
                review_status="approved",
                result_json={
                    "summary": "الحاجة إلى تنمية الاستقلال والمهارات اليومية.",
                    "needs": ["العلاج الوظيفي", "المهارات اليومية"],
                    "recommendations": ["تقييم وظيفي"],
                },
                created_by_user_id=user_id,
                reviewed_by_user_id=user_id,
                reviewed_at=datetime.now(timezone.utc),
            )
        )
        db.add(
            Goal(
                child_id=child["id"],
                title="تحسين المهارات اليومية والاستقلال",
                description="التدرب على مهارات العناية اليومية.",
                category="مهارات يومية",
                status="in_progress",
                progress_percent=25,
                created_by_user_id=user_id,
            )
        )
        draft_report = Report(
            child_id=child["id"],
            title="تقرير سمعي غير معتمد",
            report_type="hearing",
            visibility="care_team",
            allowed_user_ids=[],
            created_by_user_id=user_id,
        )
        draft_version = ReportVersion(
            report=draft_report,
            version_number=1,
            original_filename="draft.pdf",
            content_type="application/pdf",
            storage_key="matching/draft.pdf",
            size_bytes=10,
            sha256="b" * 64,
            uploaded_by_user_id=user_id,
        )
        db.add_all([draft_report, draft_version])
        db.flush()
        db.add(
            ReportAIAnalysis(
                child_id=child["id"],
                report_id=draft_report.id,
                report_version_id=draft_version.id,
                provider="mock",
                model="test",
                analysis_status="completed",
                review_status="draft",
                result_json={"needs": ["متابعة سمعية"]},
                created_by_user_id=user_id,
            )
        )
        db.commit()

    response = client.post(
        f"/api/v1/children/{child['id']}/center-matches",
        headers=auth_header(auth),
        json={},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["matches"][0]["center"]["id"] == center_id
    assert payload["evidence"]["approved_reports_used"] == 1
    assert payload["evidence"]["active_goals_used"] == 1
    source_types = {
        source["source_type"]
        for source in payload["matches"][0]["sources"]
    }
    assert {"approved_report", "active_goal"}.issubset(source_types)
    assert "السمعيات" not in payload["profile_signals"]


def test_matching_reports_insufficient_profile_data_without_guessing(client):
    auth = register(client, "matching.insufficient@example.com")
    child = create_child(client, auth, conditions=["حالة غير مصنفة"])
    add_center(
        name="مركز عام تجريبي",
        city="الرياض",
        specialties=["النطق والتخاطب"],
        services=["جلسات تخاطب"],
        served_needs=["دعم التواصل"],
    )

    response = client.post(
        f"/api/v1/children/{child['id']}/center-matches",
        headers=auth_header(auth),
        json={},
    )
    assert response.status_code == 201, response.text
    assert response.json()["insufficient_data"] is True
    assert response.json()["matches"] == []


def test_center_matching_is_private_to_authorized_child_users(client):
    owner = register(client, "matching.owner@example.com")
    outsider = register(client, "matching.outsider@example.com")
    child = create_child(client, owner, needs=["دعم التواصل"])

    response = client.post(
        f"/api/v1/children/{child['id']}/center-matches",
        headers=auth_header(outsider),
        json={},
    )
    assert response.status_code == 404


def test_matching_does_not_use_reports_without_view_permission(client):
    owner = register(client, "matching.permission.owner@example.com")
    child = create_child(client, owner)
    provider_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "matching.permission.provider@example.com",
            "full_name": "مختص تجريبي",
            "password": "StrongPass123!",
            "role": "care_provider",
            "provider_specialty": "النطق والتخاطب",
        },
    )
    assert provider_response.status_code == 201
    provider = provider_response.json()

    with SessionLocal() as db:
        db.add(
            CareTeamMembership(
                child_id=child["id"],
                user_id=provider["user"]["id"],
                invited_by_user_id=owner["user"]["id"],
                role_label="مختص مطلع على الملف فقط",
                permissions=["view_profile"],
            )
        )
        report = Report(
            child_id=child["id"],
            title="تقرير تخاطب خاص",
            report_type="speech",
            visibility="care_team",
            allowed_user_ids=[],
            created_by_user_id=owner["user"]["id"],
        )
        version = ReportVersion(
            report=report,
            version_number=1,
            original_filename="private.pdf",
            content_type="application/pdf",
            storage_key="matching/private.pdf",
            size_bytes=10,
            sha256="c" * 64,
            uploaded_by_user_id=owner["user"]["id"],
        )
        db.add_all([report, version])
        db.flush()
        db.add(
            ReportAIAnalysis(
                child_id=child["id"],
                report_id=report.id,
                report_version_id=version.id,
                provider="mock",
                model="test",
                analysis_status="completed",
                review_status="approved",
                result_json={"needs": ["جلسات تخاطب"]},
                created_by_user_id=owner["user"]["id"],
                reviewed_by_user_id=owner["user"]["id"],
                reviewed_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

    response = client.post(
        f"/api/v1/children/{child['id']}/center-matches",
        headers=auth_header(provider),
        json={},
    )
    assert response.status_code == 201, response.text
    assert response.json()["evidence"]["approved_reports_used"] == 0
    assert response.json()["insufficient_data"] is True
