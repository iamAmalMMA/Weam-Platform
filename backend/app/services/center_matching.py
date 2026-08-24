from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date

from app.core.config import get_settings
from app.models.center import Center
from app.models.child import Child
from app.services.assistant_rag import SourceChunk
from app.services.gemini_failover import call_gemini_with_failover

logger = logging.getLogger(__name__)

ARABIC_DIACRITICS = re.compile(r"[\u0617-\u061A\u064B-\u0652\u0670\u06D6-\u06ED]")
NON_WORD = re.compile(r"[^\w\u0600-\u06FF]+", re.UNICODE)

CONCEPTS: dict[str, tuple[str, tuple[str, ...]]] = {
    "communication": (
        "النطق والتواصل",
        ("نطق", "تخاطب", "تواصل", "لغه", "كلام", "لفظ"),
    ),
    "hearing": ("السمعيات", ("سمع", "سمعي", "سمعيات")),
    "occupational": (
        "العلاج الوظيفي والمهارات اليومية",
        ("علاج وظيفي", "وظيفي", "مهارات يوميه", "استقلال", "حسي", "حسيه"),
    ),
    "physical": (
        "الدعم الحركي والعلاج الطبيعي",
        ("علاج طبيعي", "حرك", "مشي", "توازن", "تناسق"),
    ),
    "behavior": (
        "الدعم السلوكي",
        ("سلوك", "تعديل السلوك", "روتين"),
    ),
    "psychological": (
        "الدعم النفسي",
        ("نفسي", "انفعال", "قلق", "عاطفي"),
    ),
    "early_intervention": (
        "التدخل المبكر",
        ("تدخل مبكر", "تاخر نمائي", "نمائي", "تنميه المهارات"),
    ),
    "special_education": (
        "التربية الخاصة والدعم التعليمي",
        ("تربيه خاصه", "تعلم", "تعليمي", "اكاديمي", "مدرسي", "مدرسه"),
    ),
    "social": (
        "المهارات الاجتماعية",
        ("اجتماعي", "مهارات اجتماعيه", "تفاعل"),
    ),
}

SOURCE_WEIGHTS = {"profile": 6, "report": 5, "goal": 3}
SAFETY_NOTE = (
    "هذه المطابقة أداة تنسيق مبنية على المعلومات المصرح بها في الملف، "
    "وليست تقييمًا طبيًا أو اعتمادًا لجودة المركز."
)


@dataclass(frozen=True)
class MatchingResult:
    provider: str
    model: str
    data: dict


def _normalize(value: str) -> str:
    text = ARABIC_DIACRITICS.sub("", value.casefold())
    text = (
        text.replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("ى", "ي")
        .replace("ؤ", "و")
        .replace("ئ", "ي")
        .replace("ة", "ه")
    )
    return " ".join(NON_WORD.sub(" ", text).split())


def _concepts_in(text: str) -> set[str]:
    normalized = _normalize(text)
    return {
        key
        for key, (_, aliases) in CONCEPTS.items()
        if any(_normalize(alias) in normalized for alias in aliases)
    }


def _age_years(child: Child) -> int | None:
    birth_date = child.identity.birth_date if child.identity else None
    if not birth_date:
        return None
    today = date.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def _supports_age(center: Center, age: int | None) -> bool:
    if age is None:
        return True
    if center.min_age_years is not None and age < center.min_age_years:
        return False
    if center.max_age_years is not None and age > center.max_age_years:
        return False
    return True


def _supports_delivery(center: Center, mode: str | None) -> bool:
    if mode == "in_person":
        return center.offers_in_person
    if mode == "remote":
        return center.offers_remote
    if mode == "both":
        return center.offers_in_person and center.offers_remote
    return True


def _public_source_type(source_type: str) -> str:
    return {
        "profile": "profile",
        "report": "approved_report",
        "goal": "active_goal",
    }[source_type]


def _local_summary(child_name: str, match_count: int, insufficient: bool) -> str:
    if insufficient:
        return (
            f"لا تتوفر في ملف {child_name} احتياجات أو خدمات كافية لإجراء مطابقة موثوقة. "
            "أكملي بيانات الملف ثم أعيدي المحاولة."
        )
    if not match_count:
        return (
            "لم نجد ضمن بيانات الدليل الحالية مركزًا يجمع الاحتياجات المسجلة "
            "مع العمر وخيارات الموقع المحددة."
        )
    return (
        f"وجدنا {match_count} خيارات مناسبة بناءً على احتياجات الملف والمصادر المعتمدة المتاحة. "
        "راجعي أسباب المطابقة وتواصلي مع المركز للتحقق من توفر الخدمة."
    )


def _extract_gemini_text(payload: dict) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    return "\n".join(
        str(part.get("text") or "").strip()
        for part in parts
        if part.get("text")
    ).strip()


def _safe_ai_summary(*, child_name: str, matches: list[dict]) -> tuple[str, str, str]:
    fallback = _local_summary(child_name, len(matches), False)
    settings = get_settings()
    provider = settings.assistant_provider.strip().lower()
    api_key = (settings.assistant_api_key or settings.ai_api_key or "").strip()
    if provider != "gemini" or not api_key:
        return fallback, "local_grounded_matching", "weam-center-matching-v1"

    candidates = "\n".join(
        f"- {item['center_name']}: {', '.join(item['matched_signals'])}"
        for item in matches
    )
    prompt = f"""
أنت مساعد تنسيق داخل منصة وئام. اكتب سطرين عربيين موجزين لولي أمر الطفل {child_name}.
الخيارات أدناه رتبتها المنصة مسبقًا بقواعد قابلة للتفسير؛ لا تغيّر الترتيب ولا تضف معلومة.
استخدم العبارة: «مناسبة بناءً على احتياجات الملف».
لا تقل «أفضل مركز» أو «الأفضل طبيًا»، ولا تضف تشخيصًا أو توصية علاجية.
اطلب من ولي الأمر مراجعة الأسباب والتواصل مع المركز للتحقق من التوفر.

الخيارات:
{candidates}
""".strip()
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 240,
            "thinkingConfig": {"thinkingLevel": "low"},
        },
    }
    primary_model = settings.assistant_model.strip() or "gemini-3.6-flash"
    try:
        response = call_gemini_with_failover(
            api_key=api_key,
            primary_model=primary_model,
            body=body,
            timeout_seconds=settings.assistant_timeout_seconds,
        )
        text = " ".join(_extract_gemini_text(response.payload).split())
        forbidden = ("أفضل مركز", "الأفضل طبي", "تشخيص", "خطة علاج")
        if not text or len(text) > 500 or any(term in text for term in forbidden):
            return fallback, "local_grounded_matching", "weam-center-matching-v1"
        if "مناسبة بناءً على احتياجات الملف" not in text:
            text = f"هذه الخيارات مناسبة بناءً على احتياجات الملف. {text}"
        return text, "gemini", response.model
    except Exception as exc:
        logger.warning("Gemini center matching summary fallback activated: %s", exc)
        return fallback, "local_grounded_matching", "weam-center-matching-v1"


def compute_center_matches(
    *,
    child: Child,
    sources: list[SourceChunk],
    centers: list[Center],
    city: str | None,
    delivery_mode: str | None,
) -> MatchingResult:
    child_name = (
        child.identity.preferred_name
        if child.identity and child.identity.preferred_name
        else child.identity.first_name
        if child.identity
        else "الطفل"
    )
    child_age = _age_years(child)
    allowed_sources = []
    for source in sources:
        if source.source_type not in SOURCE_WEIGHTS:
            continue
        if source.source_type == "goal" and "الحالة الحالية: completed" in source.text:
            continue
        concepts = _concepts_in(source.text)
        if concepts:
            allowed_sources.append((source, concepts))

    concept_scores: dict[str, int] = {}
    sources_by_concept: dict[str, list[SourceChunk]] = {}
    for source, concepts in allowed_sources:
        for concept in concepts:
            concept_scores[concept] = concept_scores.get(concept, 0) + SOURCE_WEIGHTS[source.source_type]
            sources_by_concept.setdefault(concept, []).append(source)

    profile_signals = [
        CONCEPTS[key][0]
        for key in sorted(concept_scores, key=lambda item: (-concept_scores[item], CONCEPTS[item][0]))
    ]
    evidence = {
        "profile_used": any(source.source_type == "profile" for source, _ in allowed_sources),
        "approved_reports_used": len({source.source_id for source, _ in allowed_sources if source.source_type == "report"}),
        "active_goals_used": len({source.source_id for source, _ in allowed_sources if source.source_type == "goal"}),
    }
    limitations: list[str] = []
    if child_age is None:
        limitations.append("تاريخ الميلاد غير متاح، لذلك لم يدخل العمر في المطابقة.")
    limitations.append("تستخدم المطابقة فقط المصادر التي يملك المستخدم الحالي صلاحية عرضها.")

    insufficient = not concept_scores
    ranked: list[tuple[int, str, dict]] = []
    normalized_city = _normalize(city or "")
    if not insufficient:
        for center in centers:
            if not center.is_active or not _supports_age(center, child_age):
                continue
            if not _supports_delivery(center, delivery_mode):
                continue
            if city and _normalize(center.city) != normalized_city:
                continue

            center_text = " ".join(
                [*(center.specialties or []), *(center.services or []), *(center.served_needs or [])]
            )
            matched = _concepts_in(center_text) & set(concept_scores)
            if not matched:
                continue
            ordered_matches = sorted(
                matched,
                key=lambda key: (-concept_scores[key], CONCEPTS[key][0]),
            )
            score = sum(concept_scores[key] for key in ordered_matches)
            score += 3 if child_age is not None else 0
            score += 3 if city else 0
            score += 1 if delivery_mode else 0

            source_map: dict[tuple[str, str], dict] = {}
            for concept in ordered_matches:
                for source in sources_by_concept.get(concept, []):
                    key = (source.source_type, source.source_id)
                    entry = source_map.setdefault(
                        key,
                        {
                            "source_type": _public_source_type(source.source_type),
                            "source_id": source.source_id,
                            "title": source.title,
                            "matched_signals": [],
                        },
                    )
                    label = CONCEPTS[concept][0]
                    if label not in entry["matched_signals"]:
                        entry["matched_signals"].append(label)

            matched_labels = [CONCEPTS[key][0] for key in ordered_matches]
            reasons = [
                f"يقدم خدمات مرتبطة بـ«{label}» المذكورة ضمن مصادر ملف الطفل."
                for label in matched_labels[:2]
            ]
            if child_age is not None:
                reasons.append(f"الفئة العمرية للمركز تشمل عمر الطفل ({child_age} سنة).")
            elif city:
                reasons.append(f"المركز موجود في المدينة المحددة: {center.city}.")

            level = "strong" if len(ordered_matches) >= 2 and score >= 12 else "good"
            item = {
                "center_id": center.id,
                "center_name": center.name,
                "match_level": level,
                "reasons": reasons[:3],
                "matched_signals": matched_labels,
                "sources": list(source_map.values())[:6],
            }
            ranked.append((score, center.name, item))

    ranked.sort(key=lambda row: (-row[0], row[1]))
    matches = [item for _, _, item in ranked[:3]]
    if insufficient or not matches:
        summary = _local_summary(child_name, len(matches), insufficient)
        provider = "local_grounded_matching"
        model = "weam-center-matching-v1"
    else:
        summary, provider, model = _safe_ai_summary(
            child_name=child_name,
            matches=matches,
        )

    return MatchingResult(
        provider=provider,
        model=model,
        data={
            "child_name": child_name,
            "child_age_years": child_age,
            "summary": summary,
            "profile_signals": profile_signals,
            "evidence": evidence,
            "insufficient_data": insufficient,
            "limitations": limitations,
            "safety_note": SAFETY_NOTE,
            "matches": matches,
        },
    )
