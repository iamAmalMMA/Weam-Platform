"""تالية (Taleyah) — dedicated single-child demo persona for غيداء, built for
the presentation walkthrough (logo/home -> child profile -> reports + AI
analysis -> goals/follow-ups -> voice notes -> care team -> centers).

Unlike lama/youssef/rawan/omar, this guardian and her care team are their own
self-contained pool (not the shared four-child pool in shared.py), so this
script is run on its own — see seed_taleyah.py.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import AccessStatus, GuardianType, InvitationStatus, UserRole, VerificationStatus
from app.models.care_team import CareInvitation, CareTeamMembership
from app.models.center import Center
from app.models.center_match import CenterMatchRun
from app.models.chat import ChatMessage, Conversation, ConversationParticipant, MessageReadReceipt
from app.models.child import CareProfile, Child, ChildIdentity, GuardianMembership
from app.models.follow_up import FollowUp
from app.models.goal import Goal, GoalUpdate
from app.models.report import Report, ReportVersion
from app.models.report_ai import ReportAIAnalysis
from app.models.user import User
from app.services.access import AccessGrant
from app.services.center_matching import compute_center_matches
from app.services.security import hash_password

from .shared import (
    DEMO_PASSWORD,
    SeedContext,
    _get_or_create_center,
    add_audit_log,
    add_care_team_member,
    add_voice_note,
    date_days_ago,
    date_days_from_now,
    days_ago,
    days_from_now,
    ensure_favorite,
    upload_report_pdf,
)
from app.services.assistant_rag import collect_authorized_sources

EXTERNAL_REF = "demo-taleyah"
DEMO_BATCH = "weam-demo-2026-taleyah"


def _get_or_create_user(db: Session, *, email: str, full_name: str, role: str,
                         provider_specialty: str | None = None) -> User:
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        return existing
    user = User(
        email=email, full_name=full_name, password_hash=hash_password(DEMO_PASSWORD),
        role=role, provider_specialty=provider_specialty,
        verification_status=VerificationStatus.VERIFIED.value,
        auth_provider="password", demo_batch=DEMO_BATCH,
    )
    db.add(user)
    db.flush()
    return user


@dataclass
class GhaidaaPool:
    guardian: User
    audiologist: User
    slp: User
    behavioral: User
    teacher: User
    hearing_center: Center


def build_pool(db: Session) -> GhaidaaPool:
    guardian = _get_or_create_user(
        db, email="ghaidaa@weam.demo", full_name="غيداء المطيري", role=UserRole.GUARDIAN.value,
    )
    audiologist = _get_or_create_user(
        db, email="audiologist.taleyah@weam.demo", full_name="د. هيا الشهراني",
        role=UserRole.CARE_PROVIDER.value, provider_specialty="سمعيات",
    )
    slp = _get_or_create_user(
        db, email="slp.taleyah@weam.demo", full_name="جود القحطاني",
        role=UserRole.CARE_PROVIDER.value, provider_specialty="نطق وتخاطب",
    )
    behavioral = _get_or_create_user(
        db, email="behavioral.taleyah@weam.demo", full_name="فيصل العنزي",
        role=UserRole.CARE_PROVIDER.value, provider_specialty="تعديل سلوك",
    )
    teacher = _get_or_create_user(
        db, email="teacher.taleyah@weam.demo", full_name="منيرة الحارثي",
        role=UserRole.CARE_PROVIDER.value, provider_specialty="معلمة الصف",
    )
    hearing_center = _get_or_create_center(
        db,
        name="مركز تجريبي للسمعيات والتخاطب",
        city="الرياض",
        description="مركز تجريبي (بيانات اصطناعية) لخدمات السمعيات والنطق والتخاطب.",
        services=["سمعيات", "نطق وتخاطب", "متابعة سمعية"],
        specialties=["ضعف سمع", "اضطرابات النطق واللغة"],
        served_needs=["دعم التواصل", "متابعة سمعية", "تنسيق المتابعات"],
        min_age_years=1, max_age_years=12, latitude=24.7136, longitude=46.6753,
    )
    return GhaidaaPool(guardian=guardian, audiologist=audiologist, slp=slp,
                        behavioral=behavioral, teacher=teacher, hearing_center=hearing_center)


def build(db: Session, *, now) -> Child:
    pool = build_pool(db)
    guardian = pool.guardian
    audiologist = pool.audiologist
    slp = pool.slp
    behavioral = pool.behavioral
    teacher = pool.teacher

    # A minimal SeedContext so the shared add_* helpers (which take ctx: SeedContext)
    # work unchanged for this independent pool too.
    ctx = SeedContext(
        db=db, now=now, guardian=guardian, secondary_guardian=guardian,
        specialists={"audiologist": audiologist, "slp": slp, "behavioral": behavioral, "teacher": teacher},
        center_rep=guardian, centers={"hearing": pool.hearing_center},
    )

    child = Child(created_by_user_id=guardian.id, external_ref=EXTERNAL_REF,
                  created_at=days_ago(now, 110), updated_at=days_ago(now, 1))
    child.identity = ChildIdentity(first_name="تالية", birth_date=date(2017, 4, 10), gender="female")
    child.care_profile = CareProfile(
        conditions=["ضعف سمع", "تشتت انتباه"],
        needs=["دعم سمعي داخل الصف", "دعم الانتباه والتركيز", "روتين يومي منظم بصريًا",
               "تنسيق بين الأسرة والمختصين والمدرسة"],
        support_requirements=["الجلوس في مقدمة الصف", "تقسيم المهام إلى خطوات قصيرة",
                               "استخدام معين سمعي بمعايرة دورية"],
        services=["سمعيات", "نطق وتخاطب", "تعديل سلوك"],
        summary="طفلة تستخدم معينًا سمعيًا وتحتاج دعمًا في الانتباه أثناء المهام الطويلة، "
                "مع فريق رعاية منسّق بين السمعيات والتخاطب وتعديل السلوك والمدرسة.",
    )
    db.add(child)
    db.flush()

    db.add(GuardianMembership(child=child, guardian_user_id=guardian.id,
                               guardian_type=GuardianType.PRIMARY.value,
                               accepted_at=days_ago(now, 109), created_at=days_ago(now, 109)))

    add_care_team_member(
        db, child=child, specialist=audiologist, guardian=guardian, role_label="أخصائية سمعيات",
        permissions=["view_profile", "view_care_team", "view_reports", "upload_reports", "view_goals",
                     "manage_goals", "view_timeline", "message_team"],
        now=now, invited_days_ago=100, accepted_days_ago=99,
    )
    add_care_team_member(
        db, child=child, specialist=slp, guardian=guardian, role_label="أخصائية نطق وتخاطب",
        permissions=["view_profile", "view_care_team", "view_reports", "upload_reports", "view_goals",
                     "manage_goals", "view_timeline", "message_team"],
        now=now, invited_days_ago=95, accepted_days_ago=94,
    )
    add_care_team_member(
        db, child=child, specialist=behavioral, guardian=guardian, role_label="أخصائي تعديل سلوك",
        permissions=["view_profile", "view_care_team", "view_reports", "upload_reports", "view_goals",
                     "manage_goals", "view_timeline", "message_team"],
        now=now, invited_days_ago=60, accepted_days_ago=59,
    )
    add_care_team_member(
        db, child=child, specialist=teacher, guardian=guardian, role_label="معلمة الصف",
        permissions=["view_profile", "view_care_team", "view_goals", "view_timeline", "message_team"],
        now=now, invited_days_ago=40, accepted_days_ago=39,
    )

    # ---- Reports (3) + AI analysis on each ----------------------------------
    def make_report(*, title, report_type, source_label, created_by, days_ago_n, asset,
                     summary, key_findings, needs, recommendations, follow_up_actions, goal_mentions):
        report_id, version_id = str(uuid.uuid4()), str(uuid.uuid4())
        created = days_ago(now, days_ago_n)
        stored = upload_report_pdf(ctx, child_id=child.id, report_id=report_id, version_id=version_id,
                                    asset_filename=asset)
        db.add(Report(id=report_id, child_id=child.id, title=title, report_type=report_type,
                       report_date=date_days_ago(now, days_ago_n), source_label=source_label,
                       visibility="care_team", created_by_user_id=created_by.id,
                       created_at=created, updated_at=created))
        db.add(ReportVersion(id=version_id, report_id=report_id, version_number=1,
                              original_filename=asset, content_type=stored.content_type,
                              storage_key=stored.key, size_bytes=stored.size_bytes, sha256=stored.sha256,
                              uploaded_by_user_id=created_by.id, created_at=created))
        add_audit_log(db, child_id=child.id, actor_user_id=created_by.id, action="report_uploaded",
                       entity_type="report", entity_id=report_id, created_at=created,
                       details={"version": 1, "visibility": "care_team", "report_type": report_type})
        db.add(ReportAIAnalysis(
            child_id=child.id, report_id=report_id, report_version_id=version_id,
            provider="seeded_demo", model="weam-demo-v1", analysis_status="completed", review_status="approved",
            result_json={
                "summary": summary, "key_findings": key_findings, "needs": needs,
                "recommendations": recommendations, "follow_up_actions": follow_up_actions,
                "goal_mentions": goal_mentions, "source_language": "ar", "evidence": key_findings[:2],
                "limitations": ["هذا تحليل تجريبي مُعدّ مسبقًا لأغراض العرض، وليس نتيجة تحليل حي — راجعيه قبل الاعتماد عليه."],
                "safety_note": "هذا تلخيص مساعد وليس تشخيصًا أو خطة علاجية بديلة عن المختص.",
            },
            created_by_user_id=guardian.id, reviewed_by_user_id=created_by.id,
            reviewed_at=days_ago(now, days_ago_n - 1), created_at=days_ago(now, days_ago_n - 1),
            updated_at=days_ago(now, days_ago_n - 1),
        ))
        return report_id, follow_up_actions

    audiology_report_id, audiology_fu = make_report(
        title="تقرير سمعيات", report_type="سمعيات",
        source_label="مركز نبض للسمعيات والتخاطب (تجريبي)", created_by=audiologist, days_ago_n=13,
        asset="taleyah_audiology_report.pdf",
        summary="استخدام منتظم للمعين السمعي مع استجابة جيدة في البيئة الهادئة، وصعوبة عند ارتفاع الضوضاء المحيطة.",
        key_findings=["استخدام المعين السمعي بانتظام مع استجابة جيدة في البيئة الهادئة.",
                      "صعوبة في تمييز الأصوات المتعددة داخل الصف عند ارتفاع الضوضاء.",
                      "تحسّن تدريجي في الاستجابة للنداء بالاسم دون تكرار."],
        needs=["متابعة سمعية دورية لضبط إعدادات المعين السمعي", "دعم التواصل بين المنزل والمدرسة"],
        recommendations=["الجلوس في مقدمة الصف بعيدًا عن مصادر الضوضاء",
                          "استخدام التواصل البصري مع التعليمات الشفوية"],
        follow_up_actions=["مراجعة السمعيات ومعايرة المعين السمعي خلال 3 أشهر",
                            "تنسيق مع المدرسة بخصوص مقعد تالية داخل الصف"],
        goal_mentions=["التأقلم مع ارتداء المعين السمعي يوميًا"],
    )
    speech_report_id, speech_fu = make_report(
        title="تقرير نطق وتخاطب", report_type="نطق وتخاطب",
        source_label="مركز نبض للسمعيات والتخاطب (تجريبي)", created_by=slp, days_ago_n=6,
        asset="taleyah_speech_report.pdf",
        summary="توسّع ملحوظ في المفردات المستخدمة تلقائيًا، مع حاجة لتبسيط التعليمات الشفوية الطويلة.",
        key_findings=["توسّع ملحوظ في المفردات المستخدمة تلقائيًا خلال المحادثة الحرة.",
                      "تحسّن في نطق المقاطع الصوتية المركّبة خلال الجلسات الأخيرة.",
                      "تحتاج وقتًا إضافيًا لمعالجة التعليمات الشفوية الطويلة."],
        needs=["تبسيط التعليمات الشفوية إلى جمل قصيرة", "توحيد المفردات المستهدفة بين المنزل والمدرسة"],
        recommendations=["مشاركة قائمة المفردات المستهدفة مع المعلمة", "الاستمرار بالجلسات الأسبوعية دون انقطاع"],
        follow_up_actions=["مشاركة قائمة المفردات المستهدفة مع المعلمة هذا الأسبوع",
                            "جدولة جلسة تخاطب أسبوعية جديدة"],
        goal_mentions=["تحسين الاستجابة للتعليمات الشفوية القصيرة"],
    )
    behavior_report_id, behavior_fu = make_report(
        title="تقرير سلوكي وتقييم انتباه", report_type="تعديل سلوك",
        source_label="مركز نبض للسمعيات والتخاطب (تجريبي)", created_by=behavioral, days_ago_n=2,
        asset="taleyah_behavior_report.pdf",
        summary="مدة انتباه قصيرة نسبيًا في المهام الطويلة، مع تحسّن واضح عند تقسيمها إلى خطوات صغيرة ومكافآت فورية.",
        key_findings=["مدة انتباه قصيرة نسبيًا أثناء المهام الطويلة، مع تحسّن عند تقسيمها لخطوات صغيرة.",
                      "تشتت ملحوظ عند وجود مؤثرات بصرية أو صوتية إضافية.",
                      "استجابة جيدة جدًا لنظام المكافآت الفورية الصغيرة."],
        needs=["مؤقّت بصري لتقسيم المهام", "تقليل المؤثرات البصرية في مكان الدراسة"],
        recommendations=["استخدام مؤقّت بصري مع فواصل راحة قصيرة", "تعزيز فوري عند إتمام كل خطوة صغيرة"],
        follow_up_actions=["تجربة نظام المكافآت الفورية لمدة أسبوعين ومراجعة الأثر",
                            "اجتماع مع المعلمة لتوحيد استراتيجيات الانتباه"],
        goal_mentions=["زيادة مدة الانتباه أثناء المهام الصفية", "استخدام الجدول البصري لتنظيم المهام اليومية"],
    )

    # ---- Follow-ups: a rich mix of completed + open, manual + report-linked ----
    from app.services.follow_up_notifications import follow_up_source_id

    def fu(title, *, days, status, source_type="manual", source_id=None, source_label="متابعة يدوية",
           created_by, completed_days=None):
        db.add(FollowUp(
            child_id=child.id, title=title, note=title,
            due_date=(date_days_from_now(now, days) if days >= 0 else date_days_ago(now, -days)),
            status=status, source_type=source_type, source_id=source_id, source_label=source_label,
            created_by_user_id=created_by.id,
            completed_by_user_id=guardian.id if status == "completed" else None,
            completed_at=days_ago(now, completed_days) if completed_days is not None else None,
            created_at=days_ago(now, abs(days) + 5),
        ))

    fu(audiology_fu[0], days=80, status="open", source_type="report_ai",
       source_id=follow_up_source_id(audiology_report_id, audiology_fu[0]),
       source_label="تقرير معتمد · تقرير سمعيات", created_by=audiologist)
    fu(audiology_fu[1], days=-9, status="completed", source_type="report_ai",
       source_id=follow_up_source_id(audiology_report_id, audiology_fu[1]),
       source_label="تقرير معتمد · تقرير سمعيات", created_by=audiologist, completed_days=8)
    fu(speech_fu[0], days=-4, status="completed", source_type="report_ai",
       source_id=follow_up_source_id(speech_report_id, speech_fu[0]),
       source_label="تقرير معتمد · تقرير نطق وتخاطب", created_by=slp, completed_days=3)
    fu(speech_fu[1], days=4, status="open", source_type="report_ai",
       source_id=follow_up_source_id(speech_report_id, speech_fu[1]),
       source_label="تقرير معتمد · تقرير نطق وتخاطب", created_by=slp)
    fu(behavior_fu[0], days=12, status="open", source_type="report_ai",
       source_id=follow_up_source_id(behavior_report_id, behavior_fu[0]),
       source_label="تقرير معتمد · تقرير سلوكي وتقييم انتباه", created_by=behavioral)
    fu(behavior_fu[1], days=6, status="open", source_type="report_ai",
       source_id=follow_up_source_id(behavior_report_id, behavior_fu[1]),
       source_label="تقرير معتمد · تقرير سلوكي وتقييم انتباه", created_by=behavioral)
    fu("موعد فحص ومعايرة المعين السمعي الدوري", days=-45, status="completed",
       created_by=guardian, completed_days=44)
    fu("اجتماع تعارف مع معلمة الصف الجديدة", days=-38, status="completed",
       created_by=guardian, completed_days=37)
    fu("تحديث الجدول البصري اليومي في المنزل", days=-15, status="completed",
       created_by=behavioral, completed_days=14)
    fu("التأكد من بطارية المعين السمعي قبل بداية الأسبوع الدراسي", days=2, status="open",
       created_by=guardian)
    fu("اجتماع فريق الرعاية الفصلي لمراجعة الخطة الشاملة", days=20, status="open",
       created_by=audiologist)

    # ---- Goals (4) — one completed a while back -----------------------------
    goal_done = Goal(
        child_id=child.id, title="التأقلم مع ارتداء المعين السمعي يوميًا",
        description="بناء روتين ثابت لارتداء المعين السمعي طوال اليوم الدراسي دون مقاومة.",
        category="سمعيات", status="completed", progress_percent=100,
        start_date=date_days_ago(now, 105), target_date=date_days_ago(now, 70),
        assigned_to_user_id=audiologist.id, created_by_user_id=audiologist.id,
        created_at=days_ago(now, 105),
    )
    db.add(goal_done)
    db.flush()
    db.add(GoalUpdate(goal_id=goal_done.id, actor_user_id=audiologist.id,
                       note="أصبحت تالية ترتدي المعين السمعي طوال اليوم الدراسي دون تذكير — الهدف مكتمل.",
                       progress_percent=100, status="completed", created_at=days_ago(now, 72)))
    add_audit_log(db, child_id=child.id, actor_user_id=audiologist.id, action="goal_progress_updated",
                   entity_type="goal", entity_id=goal_done.id, created_at=days_ago(now, 72),
                   details={"progress_percent": 100, "status": "completed"})

    goal_attention = Goal(
        child_id=child.id, title="زيادة مدة الانتباه أثناء المهام الصفية",
        description="زيادة مدة التركيز المستمر أثناء أداء المهام الصفية القصيرة تدريجيًا.",
        category="تعديل سلوك", status="in_progress", progress_percent=30,
        start_date=date_days_ago(now, 25), target_date=date_days_from_now(now, 45),
        assigned_to_user_id=behavioral.id, created_by_user_id=behavioral.id,
        created_at=days_ago(now, 25),
    )
    db.add(goal_attention)
    db.flush()
    db.add(GoalUpdate(goal_id=goal_attention.id, actor_user_id=behavioral.id,
                       note="تحسّن ملحوظ عند استخدام المؤقّت البصري مع فواصل الراحة.",
                       progress_percent=30, status="in_progress", created_at=days_ago(now, 2)))

    goal_instructions = Goal(
        child_id=child.id, title="تحسين الاستجابة للتعليمات الشفوية القصيرة",
        description="الاستجابة للتعليمات الشفوية المكوّنة من خطوة أو خطوتين دون إعادة.",
        category="نطق وتخاطب", status="in_progress", progress_percent=45,
        start_date=date_days_ago(now, 30), target_date=date_days_from_now(now, 30),
        assigned_to_user_id=slp.id, created_by_user_id=slp.id, created_at=days_ago(now, 30),
    )
    db.add(goal_instructions)
    db.flush()
    db.add(GoalUpdate(goal_id=goal_instructions.id, actor_user_id=slp.id,
                       note="استجابة أسرع للتعليمات القصيرة عند التواصل البصري المباشر.",
                       progress_percent=45, status="in_progress", created_at=days_ago(now, 5)))

    goal_schedule = Goal(
        child_id=child.id, title="استخدام الجدول البصري لتنظيم المهام اليومية",
        description="الاعتماد على جدول بصري يومي لتنظيم مهام المنزل والمدرسة بشكل مستقل تدريجيًا.",
        category="تعديل سلوك", status="in_progress", progress_percent=20,
        start_date=date_days_ago(now, 14), target_date=date_days_from_now(now, 50),
        assigned_to_user_id=teacher.id, created_by_user_id=behavioral.id, created_at=days_ago(now, 14),
    )
    db.add(goal_schedule)
    db.flush()
    db.add(GoalUpdate(goal_id=goal_schedule.id, actor_user_id=teacher.id,
                       note="بدأنا استخدام الجدول البصري في الصف هذا الأسبوع مع متابعة يومية.",
                       progress_percent=20, status="in_progress", created_at=days_ago(now, 3)))

    # ---- Voice notes (3) -----------------------------------------------------
    add_voice_note(
        ctx, child=child, title="ملاحظة من الأم بعد يوم دراسي",
        transcript_draft="تالية لبست السماعة طول اليوم بدون ما تشتكي، وردت على اسمها بسرعة أكثر من قبل.",
        transcript_final="تالية ارتدت المعين السمعي طوال اليوم الدراسي دون شكوى، واستجابت لاسمها بسرعة أكبر من المعتاد.",
        created_by=guardian, now=now, days_ago_created=9,
    )
    add_voice_note(
        ctx, child=child, title="ملاحظة من المعلمة بعد الحصة",
        transcript_draft="تالية خلصت نشاط القراءة اليوم بخطوات مقسمة وما احتاجت تذكير كثير.",
        transcript_final="أنهت تالية نشاط القراءة اليوم بعد تقسيمه إلى خطوات قصيرة، واحتاجت تذكيرًا أقل من المعتاد.",
        created_by=teacher, now=now, days_ago_created=5,
    )
    add_voice_note(
        ctx, child=child, title="ملاحظة من أخصائي تعديل السلوك",
        transcript_draft="جربنا نظام المكافآت الفورية اليوم وكانت استجابة تالية ممتازة خلال أول جلستين.",
        transcript_final="بدأ تطبيق نظام المكافآت الفورية اليوم، وكانت استجابة تالية ممتازة خلال أول جلستين.",
        created_by=behavioral, now=now, days_ago_created=2,
    )

    # ---- Centers: an explainable match + favorite -----------------------------
    grant = AccessGrant(membership_id="seed", access_role="guardian", permissions=[],
                         guardian_type=GuardianType.PRIMARY.value, is_primary_guardian=True)
    sources = [s for s in collect_authorized_sources(db, child_id=child.id, user=guardian, grant=grant)
               if s.source_type in {"profile", "report", "goal"}]
    centers = list(db.scalars(select(Center).where(Center.is_active.is_(True),
                                                     Center.verification_status == "verified")).all())
    result = compute_center_matches(child=child, sources=sources, centers=centers, city="الرياض", delivery_mode="in_person")
    run = CenterMatchRun(child_id=child.id, requested_by_user_id=guardian.id, provider=result.provider,
                          model=result.model, criteria_json={"city": "الرياض", "delivery_mode": "in_person"},
                          result_json=result.data, created_at=days_ago(now, 3))
    db.add(run)
    db.flush()
    ensure_favorite(db, user_id=guardian.id, center_id=pool.hearing_center.id, created_at=days_ago(now, 3))

    # ---- A short care-team chat, guardian <-> audiologist ---------------------
    conversation = Conversation(child_id=child.id, kind="direct", created_by_user_id=guardian.id,
                                 created_at=days_ago(now, 1), updated_at=days_ago(now, 1))
    db.add(conversation)
    db.flush()
    db.add(ConversationParticipant(conversation_id=conversation.id, user_id=guardian.id, joined_at=days_ago(now, 1)))
    db.add(ConversationParticipant(conversation_id=conversation.id, user_id=audiologist.id, joined_at=days_ago(now, 1)))
    msg1 = ChatMessage(conversation_id=conversation.id, sender_user_id=guardian.id,
                        body="سماعة تالية صارت تصدر صوت خفيف اليوم، هل نحتاج موعد أبكر من المتابعة القادمة؟",
                        created_at=days_ago(now, 1))
    db.add(msg1)
    db.flush()
    db.add(MessageReadReceipt(message_id=msg1.id, user_id=guardian.id, read_at=days_ago(now, 1)))
    msg2 = ChatMessage(conversation_id=conversation.id, sender_user_id=audiologist.id,
                        body="ممكن يكون سبب بسيط بالبطارية، لكن لو استمر لنهاية الأسبوع نجدول فحص عاجل.",
                        created_at=days_ago(now, 1))
    db.add(msg2)
    db.flush()
    db.add(MessageReadReceipt(message_id=msg2.id, user_id=audiologist.id, read_at=days_ago(now, 1)))
    db.add(MessageReadReceipt(message_id=msg2.id, user_id=guardian.id, read_at=days_ago(now, 1)))

    return child
