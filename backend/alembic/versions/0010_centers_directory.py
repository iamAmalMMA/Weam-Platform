"""centers directory and user favorites

Revision ID: 0010_centers_directory
Revises: 0009_followups_notifications
"""
from collections.abc import Sequence
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa

revision: str = "0010_centers_directory"
down_revision: str | None = "0009_followups_notifications"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "centers",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("address", sa.String(length=300), nullable=False),
        sa.Column("specialties", sa.JSON(), nullable=False),
        sa.Column("services", sa.JSON(), nullable=False),
        sa.Column("served_needs", sa.JSON(), nullable=False),
        sa.Column("min_age_years", sa.Integer(), nullable=True),
        sa.Column("max_age_years", sa.Integer(), nullable=True),
        sa.Column("offers_in_person", sa.Boolean(), nullable=False),
        sa.Column("offers_remote", sa.Boolean(), nullable=False),
        sa.Column("phone", sa.String(length=40), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("working_hours", sa.String(length=240), nullable=False),
        sa.Column("price_range", sa.String(length=120), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_centers_name"), "centers", ["name"], unique=False)
    op.create_index(op.f("ix_centers_city"), "centers", ["city"], unique=False)
    op.create_index(
        op.f("ix_centers_is_active"), "centers", ["is_active"], unique=False
    )

    op.create_table(
        "center_favorites",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("center_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["center_id"], ["centers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "center_id",
            name="uq_center_favorite_user_center",
        ),
    )
    op.create_index(
        op.f("ix_center_favorites_user_id"),
        "center_favorites",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_center_favorites_center_id"),
        "center_favorites",
        ["center_id"],
        unique=False,
    )

    centers = sa.table(
        "centers",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("city", sa.String),
        sa.column("region", sa.String),
        sa.column("address", sa.String),
        sa.column("specialties", sa.JSON),
        sa.column("services", sa.JSON),
        sa.column("served_needs", sa.JSON),
        sa.column("min_age_years", sa.Integer),
        sa.column("max_age_years", sa.Integer),
        sa.column("offers_in_person", sa.Boolean),
        sa.column("offers_remote", sa.Boolean),
        sa.column("phone", sa.String),
        sa.column("email", sa.String),
        sa.column("working_hours", sa.String),
        sa.column("price_range", sa.String),
        sa.column("latitude", sa.Float),
        sa.column("longitude", sa.Float),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    created_at = datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)
    common_hours = "الأحد–الخميس، 8:00 ص–6:00 م"
    op.bulk_insert(
        centers,
        [
            {
                "id": "c4000000-0000-4000-8000-000000000001",
                "name": "مركز إشراقة النمو التجريبي",
                "description": "مساحة رعاية متكاملة تركز على التواصل والمهارات اليومية والتدخل المبكر، مع إشراك الأسرة في خطة الدعم.",
                "city": "الرياض",
                "region": "منطقة الرياض",
                "address": "حي النخيل — عنوان تجريبي",
                "specialties": ["النطق والتخاطب", "العلاج الوظيفي", "التدخل المبكر"],
                "services": ["جلسات تخاطب", "تقييم المهارات", "تدريب الأسرة"],
                "served_needs": ["دعم التواصل", "التنظيم الحسي", "تأخر المهارات النمائية"],
                "min_age_years": 1,
                "max_age_years": 12,
                "offers_in_person": True,
                "offers_remote": True,
                "phone": "+966 50 000 0001",
                "email": "ishraqa@example.test",
                "working_hours": common_hours,
                "price_range": "متوسط",
                "latitude": 24.7136,
                "longitude": 46.6753,
                "is_active": True,
                "created_at": created_at,
                "updated_at": created_at,
            },
            {
                "id": "c4000000-0000-4000-8000-000000000002",
                "name": "عيادات خطوة وئام التجريبية",
                "description": "خدمات سمع وتواصل للأطفال واليافعين، تشمل التقييم والمتابعة والإرشاد الأسري ضمن خطة واضحة.",
                "city": "جدة",
                "region": "منطقة مكة المكرمة",
                "address": "حي السلامة — عنوان تجريبي",
                "specialties": ["السمعيات", "النطق والتخاطب"],
                "services": ["فحوصات سمع", "جلسات تخاطب", "إرشاد الأسرة"],
                "served_needs": ["متابعة سمعية", "دعم اللغة", "وضوح النطق"],
                "min_age_years": 2,
                "max_age_years": 16,
                "offers_in_person": True,
                "offers_remote": True,
                "phone": "+966 50 000 0002",
                "email": "khotwa@example.test",
                "working_hours": "الأحد–الخميس، 9:00 ص–7:00 م",
                "price_range": "متوسط",
                "latitude": 21.5433,
                "longitude": 39.1728,
                "is_active": True,
                "created_at": created_at,
                "updated_at": created_at,
            },
            {
                "id": "c4000000-0000-4000-8000-000000000003",
                "name": "مركز أفق الحركة التجريبي",
                "description": "برامج دعم حركي ووظيفي تهدف إلى تنمية الاستقلالية والمهارات الحركية في بيئة مناسبة للطفل.",
                "city": "الدمام",
                "region": "المنطقة الشرقية",
                "address": "حي الفيصلية — عنوان تجريبي",
                "specialties": ["العلاج الطبيعي", "العلاج الوظيفي"],
                "services": ["جلسات علاج طبيعي", "تدريب المهارات الحركية", "تقييم وظيفي"],
                "served_needs": ["دعم الحركة", "المهارات اليومية", "التوازن والتناسق"],
                "min_age_years": 1,
                "max_age_years": 18,
                "offers_in_person": True,
                "offers_remote": False,
                "phone": "+966 50 000 0003",
                "email": None,
                "working_hours": common_hours,
                "price_range": "متوسط",
                "latitude": 26.4207,
                "longitude": 50.0888,
                "is_active": True,
                "created_at": created_at,
                "updated_at": created_at,
            },
            {
                "id": "c4000000-0000-4000-8000-000000000004",
                "name": "مساحة نمو التعليمية التجريبية",
                "description": "برامج تربوية فردية ودعم أكاديمي مبكر بالتعاون مع الأسرة وفريق الرعاية، حضوريًا وعن بعد.",
                "city": "المدينة المنورة",
                "region": "منطقة المدينة المنورة",
                "address": "حي قربان — عنوان تجريبي",
                "specialties": ["التربية الخاصة", "التدخل المبكر"],
                "services": ["خطط تعليمية فردية", "دعم أكاديمي", "تدريب الأسرة"],
                "served_needs": ["صعوبات التعلم", "الاستعداد المدرسي", "تنمية المهارات"],
                "min_age_years": 3,
                "max_age_years": 14,
                "offers_in_person": True,
                "offers_remote": True,
                "phone": "+966 50 000 0004",
                "email": "numu@example.test",
                "working_hours": "الأحد–الخميس، 7:30 ص–5:00 م",
                "price_range": "اقتصادي إلى متوسط",
                "latitude": 24.5247,
                "longitude": 39.5692,
                "is_active": True,
                "created_at": created_at,
                "updated_at": created_at,
            },
            {
                "id": "c4000000-0000-4000-8000-000000000005",
                "name": "مركز توازن السلوك التجريبي",
                "description": "دعم سلوكي ونفسي يركز على المهارات الاجتماعية وتنظيم الروتين، مع متابعة عملية للأسرة.",
                "city": "الرياض",
                "region": "منطقة الرياض",
                "address": "حي الملز — عنوان تجريبي",
                "specialties": ["تعديل السلوك", "الدعم النفسي"],
                "services": ["خطط تعديل السلوك", "دعم نفسي", "تدريب المهارات الاجتماعية"],
                "served_needs": ["تنظيم السلوك", "المهارات الاجتماعية", "الدعم النفسي"],
                "min_age_years": 4,
                "max_age_years": 18,
                "offers_in_person": True,
                "offers_remote": True,
                "phone": "+966 50 000 0005",
                "email": "tawazon@example.test",
                "working_hours": "الأحد–الخميس، 10:00 ص–8:00 م",
                "price_range": "متوسط",
                "latitude": 24.6748,
                "longitude": 46.7241,
                "is_active": True,
                "created_at": created_at,
                "updated_at": created_at,
            },
            {
                "id": "c4000000-0000-4000-8000-000000000006",
                "name": "عيادة صوت وسمع التجريبية",
                "description": "عيادة تعريفية لخدمات السمع والتخاطب والإرشاد الأسري، مع متابعة تقدم الطفل بصورة منتظمة.",
                "city": "أبها",
                "region": "منطقة عسير",
                "address": "حي المنسك — عنوان تجريبي",
                "specialties": ["السمعيات", "النطق والتخاطب"],
                "services": ["فحوصات سمع", "جلسات تخاطب", "إرشاد الأسرة"],
                "served_needs": ["ضعف السمع", "تأخر اللغة", "دعم التواصل"],
                "min_age_years": 2,
                "max_age_years": 18,
                "offers_in_person": True,
                "offers_remote": False,
                "phone": "+966 50 000 0006",
                "email": None,
                "working_hours": common_hours,
                "price_range": "اقتصادي إلى متوسط",
                "latitude": 18.2164,
                "longitude": 42.5053,
                "is_active": True,
                "created_at": created_at,
                "updated_at": created_at,
            },
            {
                "id": "c4000000-0000-4000-8000-000000000007",
                "name": "مركز جسور الدعم التجريبي",
                "description": "خدمات نفسية وتربوية وسلوكية لليافعين، مع جلسات أسرية وخيارات متابعة عن بعد.",
                "city": "الخبر",
                "region": "المنطقة الشرقية",
                "address": "حي العليا — عنوان تجريبي",
                "specialties": ["الدعم النفسي", "التربية الخاصة", "تعديل السلوك"],
                "services": ["دعم نفسي", "خطط تعديل السلوك", "تدريب الأسرة"],
                "served_needs": ["القلق", "تنظيم السلوك", "صعوبات التعلم"],
                "min_age_years": 5,
                "max_age_years": 21,
                "offers_in_person": True,
                "offers_remote": True,
                "phone": "+966 50 000 0007",
                "email": "josoor@example.test",
                "working_hours": "الأحد–الخميس، 9:00 ص–8:00 م",
                "price_range": "متوسط إلى مرتفع",
                "latitude": 26.2172,
                "longitude": 50.1971,
                "is_active": True,
                "created_at": created_at,
                "updated_at": created_at,
            },
            {
                "id": "c4000000-0000-4000-8000-000000000008",
                "name": "منصة سند للرعاية عن بعد — تجريبية",
                "description": "جلسات واستشارات عن بعد لدعم الأسرة في التواصل والصحة النفسية ومتابعة المهارات المنزلية.",
                "city": "الرياض",
                "region": "خدمات لجميع مناطق المملكة",
                "address": "خدمة عن بعد",
                "specialties": ["النطق والتخاطب", "الدعم النفسي", "التدخل المبكر"],
                "services": ["استشارات تخاطب", "دعم نفسي", "تدريب الأسرة"],
                "served_needs": ["دعم التواصل", "الدعم النفسي", "إرشاد الأسرة"],
                "min_age_years": 3,
                "max_age_years": 18,
                "offers_in_person": False,
                "offers_remote": True,
                "phone": "+966 50 000 0008",
                "email": "sanad@example.test",
                "working_hours": "السبت–الخميس، 9:00 ص–9:00 م",
                "price_range": "اقتصادي",
                "latitude": None,
                "longitude": None,
                "is_active": True,
                "created_at": created_at,
                "updated_at": created_at,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_center_favorites_center_id"), table_name="center_favorites"
    )
    op.drop_index(
        op.f("ix_center_favorites_user_id"), table_name="center_favorites"
    )
    op.drop_table("center_favorites")
    op.drop_index(op.f("ix_centers_is_active"), table_name="centers")
    op.drop_index(op.f("ix_centers_city"), table_name="centers")
    op.drop_index(op.f("ix_centers_name"), table_name="centers")
    op.drop_table("centers")
