"""Idempotently seed real, publicly-sourced centers (Riyadh, Jeddah, Dammam, Medina,
Abha) into the directory.

Every fact below was read directly from the center's own official website on
2026-09-01 (see `source_urls` on each row). Nothing here is inferred: fields the
source did not state (working hours, exact age range, etc.) are left empty or
carry an explicit "not published" note rather than a guess.

This is deliberately a SEPARATE script from `seed_demo.py`: real centers are
reference data that should persist across demo resets, not synthetic data that
gets wiped. It is safe to re-run — rows are upserted by (name, city).

Coordinates are approximate, district/street-level geocodes of each center's
own stated address, from OpenStreetMap/Nominatim (free, properly attributed,
no paid API) — not a precise building-level geocode. Any "distance from you"
shown in the app must be labeled as approximate for this reason.

Two centers surfaced during research were deliberately excluded from this batch
even though the initial review marked them "include":
  * Riyadh Specialized Rehabilitation Center — a direct fetch of the site found
    no itemized services/specialties, and the male branch is stated to serve
    ages 12+ only, which is hard to reconcile with confident inclusion in a
    directory meant to also serve young children. Held back pending a manual
    look rather than seeded on thin/ambiguous data.
  * The five "include-with-caveats" candidates from the original research table
    are not in this script at all — their own sites blocked automated access,
    so no field values could be directly verified.

Usage (from backend/):
    .venv\\Scripts\\python.exe -m scripts.seed_real_centers
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.center import Center
from scripts._seed_shared import assert_migrations_at_head

REVIEWED_AT = datetime(2026, 9, 1, tzinfo=timezone.utc)

# 2026-09-04 batch: sourced from OpenStreetMap's Overpass API (free, ODbL-licensed,
# no scraping/paid API), expanding city coverage per the earlier demo-data city list
# (Riyadh, Jeddah, Dammam, Medina, Abha, Khobar). Every row here was found via a real
# Overpass query and cross-checked by fetching its full OSM tag set — not guessed.
#
# Coverage is genuinely uneven: OSM has almost no data specifically tagged or named
# as disability/rehabilitation/special-needs services in Saudi cities (hundreds of
# hospitals/pharmacies/dentists are tagged, but almost none are relevant to this
# platform's purpose). Rather than pad the list with irrelevant clinics to hit a
# target count, only entries with a clear, tag-or-name-confirmed connection to
# rehabilitation/disability/autism services were kept. Khobar had zero such entries
# within a 40km radius and was left out entirely rather than forced in.
#
# The five "مركز التنمية الاجتماعية" (Social Development Center) rows are the same
# nationwide government program in five different cities — confirmed via their
# operator tag (Ministry of Human Resources and Social Development) and official
# website, not five independent guesses. Their listed focus is deliberately generic
# (family/social support, outreach) since OSM does not state which specific clinical
# services each branch offers.
OSM_REVIEWED_AT = datetime(2026, 9, 4, tzinfo=timezone.utc)

REAL_CENTERS: list[dict] = [
    {
        "name": "مراكز الأوائل للرعاية والتأهيل",
        "latitude": 24.7586458,
        "longitude": 46.7363571,
        "city": "الرياض",
        "region": "منطقة الرياض",
        "address": "تقاطع طريق عثمان بن عفان مع طريق الملك عبدالله، الرياض",
        "phone": "0535242200",
        "email": "info@alaweal.org",
        "working_hours": "الأحد – الخميس | صباحي 7:30ص–12:30م | مسائي 3:00م–8:00م",
        "services": ["تدخل مبكر", "تأهيل توحد", "علاج نفسي وسلوكي", "تأهيل نطق ولغة", "علاج وظيفي وحسي", "أنشطة ترفيهية واجتماعية"],
        "specialties": ["إعاقة ذهنية", "اضطراب طيف التوحد", "متلازمة داون", "صعوبات تعلم", "فرط حركة وتشتت انتباه", "تأخر نمو"],
        "served_needs": ["دعم النمو", "دعم سلوكي", "دعم النطق واللغة", "دعم حسي"],
        "min_age_years": 2,
        "max_age_years": None,
        "offers_in_person": True,
        "offers_remote": True,
        "description": (
            "مركز رعاية وتأهيل خاص في الرياض. يذكر الموقع الرسمي إتاحة جلسات فيديو عن بعد "
            "للعائلات البعيدة، إلى جانب الخدمات الحضورية."
        ),
        "source_urls": ["https://awael.sa/"],
    },
    {
        "name": "مركز العباقرة للرعاية النهارية",
        "latitude": 24.6542241,
        "longitude": 46.6710904,
        "city": "الرياض",
        "region": "منطقة الرياض",
        "address": "الرياض – حي الشرفية",
        "phone": "0556511765 / 0118102496",
        "email": "abaqera2023@gmail.com",
        "working_hours": "الأحد – الخميس | قسم الإناث 7:00–1:00 | قسم الذكور 3:00–8:00",
        "services": ["علاج طبيعي", "علاج نطق ولغة", "علاج وظيفي", "خدمات نفسية وسلوكية", "خدمات اجتماعية", "رعاية طبية"],
        "specialties": ["متلازمة داون", "اضطراب طيف التوحد", "إعاقة ذهنية", "إعاقة حركية", "فرط حركة وتشتت انتباه", "ضعف سمع"],
        "served_needs": ["دعم حركي", "دعم النطق واللغة", "دعم سلوكي", "متابعة سمعية"],
        "min_age_years": 2,
        "max_age_years": 45,
        "offers_in_person": True,
        "offers_remote": False,
        "description": (
            "مركز رعاية نهارية بقسمين منفصلين للذكور والإناث في حي الشرفية بالرياض. "
            "يذكر الموقع الرسمي ترخيصًا رقم 150 لقسم الإناث ورقم 2349 لقسم الذكور، "
            "وشهادة أيزو 9001:2015. يخدم فئات عمرية من 2 إلى 45 سنة."
        ),
        "source_urls": ["https://abaqeracenter.com/"],
    },
    {
        "name": "مركز بداية لتأهيل اضطرابات التواصل",
        "latitude": 24.8340701,
        "longitude": 46.6801706,
        "city": "الرياض",
        "region": "منطقة الرياض",
        "address": "حي النرجس، الرياض",
        "phone": "00966538626901",
        "email": "info@bedayacenter.sa",
        "working_hours": "غير معلن على الموقع الرسمي — يُنصح بالتواصل للتأكد.",
        "services": ["علاج اضطرابات النطق", "علاج اللغة", "علاج النطق عند الأطفال", "علاج اضطرابات البلع والصوت", "خدمات مساندة للتواصل (وظيفي وسلوكي ونفسي وأكاديمي)"],
        "specialties": ["تأتأة", "عسر التلفظ", "تأخر لغوي", "اضطرابات اللغة التعبيرية والاستقبالية"],
        "served_needs": ["دعم النطق واللغة", "دعم التواصل"],
        "min_age_years": None,
        "max_age_years": None,
        "offers_in_person": True,
        "offers_remote": False,
        "description": "مركز متخصص في اضطرابات التواصل والنطق واللغة في حي النرجس بالرياض، يخدم الأطفال والبالغين.",
        "source_urls": ["https://bedayacenter.sa/"],
    },
    {
        "name": "مركز تأهيل ورعاية الأطفال ذوي الإعاقة بشمال جدة",
        "latitude": 21.8160366,
        "longitude": 39.2157769,
        "city": "جدة",
        "region": "منطقة مكة المكرمة",
        "address": "حي الفروسية، شمال جدة",
        "phone": "920006222",
        "email": "info@dca.org.sa",
        "working_hours": "غير معلن على الموقع الرسمي — يُنصح بالتواصل للتأكد.",
        "services": ["عيادات تأهيلية وتعليمية شاملة"],
        "specialties": [],
        "served_needs": [],
        "min_age_years": None,
        "max_age_years": None,
        "offers_in_person": True,
        "offers_remote": False,
        "description": (
            "مركز تابع لجمعية الأطفال ذوي الإعاقة (دي سي ايه) في شمال جدة، مخصص للأطفال حصرًا "
            "بحسب ما نُشر (طاقة استيعابية معلنة 500 طفل). لا تتوفر تفاصيل عامة عن الفئات "
            "العمرية أو التخصصات الدقيقة على المصدر المتاح."
        ),
        "source_urls": ["https://store.dca.org.sa/p/72507"],
    },
    {
        "name": "الجمعية الأولى للتوحد بمنطقة مكة المكرمة",
        "latitude": 21.5864,
        "longitude": 39.1288,
        "city": "جدة",
        "region": "منطقة مكة المكرمة",
        "address": "جدة - حي الشاطئ",
        "phone": "0561868244",
        "email": None,
        "working_hours": "غير معلن على الموقع الرسمي — يُنصح بالتواصل للتأكد.",
        "services": ["برامج تعليمية", "برامج تدريب أسري", "استشارات أسرية", "برامج رياضية لأطفال التوحد", "برامج تأهيل مهني لشباب التوحد"],
        "specialties": ["اضطراب طيف التوحد"],
        "served_needs": ["دعم سلوكي", "دعم أسري"],
        "min_age_years": None,
        "max_age_years": None,
        "offers_in_person": True,
        "offers_remote": False,
        "description": "جمعية متخصصة في التوحد بحي الشاطئ في جدة، تقدم برامج للأطفال والشباب على السواء.",
        "source_urls": ["https://www.jacenter.sa/"],
    },
    {
        "name": "Badghish Rehabilitation and Healthcare (BRHC)",
        "latitude": 21.5476471,
        "longitude": 39.1706901,
        "city": "جدة",
        "region": "منطقة مكة المكرمة",
        "address": "Ibrahim Aljaffali, Jeddah, Saudi Arabia",
        "phone": "+966 54 911 2030 / +966 55 110 6350 / 920001604 (toll-free)",
        "email": "info@brhc.com.sa",
        "working_hours": "غير معلن على الموقع الرسمي — يُنصح بالتواصل للتأكد.",
        "services": [
            "Occupational Therapy", "Psychology", "Speech and Hearing therapy",
            "Paediatric Rehabilitation", "Neuro Rehabilitation", "Women's Health",
            "Spine Care", "Cardio Rehabilitation", "Orthopaedic Rehabilitation",
        ],
        "specialties": [
            "Cerebral palsy", "Nerve plexus injury", "Brain strokes", "Spinal injuries",
            "Hemiplegia", "Quadriplegia", "Neck/back pain", "Herniated disc",
        ],
        "served_needs": ["دعم حركي", "متابعة سمعية", "دعم النطق واللغة"],
        "min_age_years": None,
        "max_age_years": None,
        "offers_in_person": True,
        "offers_remote": False,
        "description": (
            "Badghish Rehabilitation and Healthcare (BRHC) — مركز تأهيل في جدة. الاسم "
            "المنشور رسميًا باللغة الإنجليزية فقط على الموقع الذي تم الاطلاع عليه؛ يقدم "
            "من ضمن خدماته تأهيلاً للأطفال (Paediatric Rehabilitation) إلى جانب خدمات "
            "للبالغين. يذكر الموقع قبول شركات تأمين (Bupa, Gulf, ISDB, Med) دون تفاصيل تغطية."
        ),
        "source_urls": ["https://brhc.com.sa/"],
    },
    {
        "name": "مركز التنمية الاجتماعية بالدرعية",
        "latitude": 24.7450689,
        "longitude": 46.5678438,
        "city": "الرياض",
        "region": "منطقة الرياض",
        "address": "الدرعية، منطقة الرياض",
        "phone": "",
        "email": None,
        "working_hours": "غير معلن — يُنصح بالتواصل للتأكد.",
        "services": ["خدمات التنمية الاجتماعية والتوعية الأسرية"],
        "specialties": [],
        "served_needs": ["دعم أسري", "التوعية والإرشاد"],
        "min_age_years": None,
        "max_age_years": None,
        "offers_in_person": True,
        "offers_remote": False,
        "description": (
            "مركز تنمية اجتماعية تابع لوزارة الموارد البشرية والتنمية الاجتماعية في الدرعية "
            "بمنطقة الرياض. بيانات OpenStreetMap تصنّفه كمنشأة خدمة اجتماعية توعوية "
            "(outreach)، دون تفاصيل عن خدمات علاجية محددة — يُنصح بالتواصل المباشر لمعرفة "
            "ما يقدّمه هذا الفرع تحديدًا لأسر الأطفال ذوي الإعاقة."
        ),
        "source_urls": ["https://www.openstreetmap.org/node/13335312608", "https://www.hrsd.gov.sa"],
        "reviewed_at": OSM_REVIEWED_AT,
        "data_confidence": "medium",
    },
    {
        "name": "مركز التأهيل الشامل للإناث",
        "latitude": 24.6928782,
        "longitude": 46.7258907,
        "city": "الرياض",
        "region": "منطقة الرياض",
        "address": "الرياض",
        "phone": "",
        "email": None,
        "working_hours": "غير معلن — يُنصح بالتواصل للتأكد.",
        "services": ["تأهيل شامل"],
        "specialties": ["إعاقة حركية", "إعاقة ذهنية"],
        "served_needs": ["دعم حركي", "دعم النمو"],
        "min_age_years": None,
        "max_age_years": None,
        "offers_in_person": True,
        "offers_remote": False,
        "description": (
            "مركز تأهيل شامل في الرياض، مصنّف على OpenStreetMap بوسم healthcare=rehabilitation. "
            "الاسم يشير إلى أن الخدمة مخصصة للإناث. لا تتوفر تفاصيل إضافية عن الفئات العمرية "
            "أو التخصصات الدقيقة من هذا المصدر — يُنصح بالتواصل المباشر للتأكد."
        ),
        "source_urls": ["https://www.openstreetmap.org/way/1301926849"],
        "reviewed_at": OSM_REVIEWED_AT,
        "data_confidence": "medium",
    },
    {
        "name": "مستشفى آمّاد",
        "latitude": 24.8563115,
        "longitude": 46.6390141,
        "city": "الرياض",
        "region": "منطقة الرياض",
        "address": "الرياض",
        "phone": "",
        "email": None,
        "working_hours": "غير معلن — يُنصح بالتواصل للتأكد.",
        "services": ["رعاية تأهيلية طويلة الأمد"],
        "specialties": [],
        "served_needs": ["دعم حركي"],
        "min_age_years": None,
        "max_age_years": None,
        "offers_in_person": True,
        "offers_remote": False,
        "description": (
            "مستشفى تأهيلي في الرياض (اسمه المنشور بالإنجليزية: AMAD)، مصنّف على "
            "OpenStreetMap بوسم healthcare=rehabilitation وتخصص long term care "
            "(رعاية طويلة الأمد). لا تتوفر معلومات تؤكد وجود برامج مخصصة للأطفال تحديدًا — "
            "يُنصح بالتواصل المباشر للتأكد."
        ),
        "source_urls": ["https://www.openstreetmap.org/way/1457822424"],
        "reviewed_at": OSM_REVIEWED_AT,
        "data_confidence": "medium",
    },
    {
        "name": "مركز التنمية الاجتماعية بجدة",
        "latitude": 21.5322609,
        "longitude": 39.1727543,
        "city": "جدة",
        "region": "منطقة مكة المكرمة",
        "address": "جدة، منطقة مكة المكرمة",
        "phone": "",
        "email": None,
        "working_hours": "غير معلن — يُنصح بالتواصل للتأكد.",
        "services": ["خدمات التنمية الاجتماعية والتوعية الأسرية"],
        "specialties": [],
        "served_needs": ["دعم أسري", "التوعية والإرشاد"],
        "min_age_years": None,
        "max_age_years": None,
        "offers_in_person": True,
        "offers_remote": False,
        "description": (
            "مركز تنمية اجتماعية تابع لوزارة الموارد البشرية والتنمية الاجتماعية في جدة. "
            "بيانات OpenStreetMap تصنّفه كمنشأة خدمة اجتماعية توعوية (outreach)، دون تفاصيل "
            "عن خدمات علاجية محددة — يُنصح بالتواصل المباشر لمعرفة ما يقدّمه هذا الفرع "
            "تحديدًا لأسر الأطفال ذوي الإعاقة."
        ),
        "source_urls": ["https://www.openstreetmap.org/node/13335254384", "https://www.hrsd.gov.sa"],
        "reviewed_at": OSM_REVIEWED_AT,
        "data_confidence": "medium",
    },
    {
        "name": "مبنى العلاج الطبيعي والتأهيل ومركز السكر",
        "latitude": 21.4244884,
        "longitude": 39.3597238,
        "city": "جدة",
        "region": "منطقة مكة المكرمة",
        "address": "جدة",
        "phone": "",
        "email": None,
        "working_hours": "غير معلن — يُنصح بالتواصل للتأكد.",
        "services": ["علاج طبيعي", "تأهيل", "رعاية السكري"],
        "specialties": [],
        "served_needs": ["دعم حركي"],
        "min_age_years": None,
        "max_age_years": None,
        "offers_in_person": True,
        "offers_remote": False,
        "description": (
            "مبنى علاج طبيعي وتأهيل ومركز سكري تابع للشؤون الصحية بوزارة الحرس الوطني في "
            "جدة (Ministry of National Guard Health Affairs). لا تتوفر معلومات تؤكد وجود "
            "برامج مخصصة للأطفال تحديدًا — يُنصح بالتواصل المباشر للتأكد."
        ),
        "source_urls": ["https://www.openstreetmap.org/way/1507435777"],
        "reviewed_at": OSM_REVIEWED_AT,
        "data_confidence": "medium",
    },
    {
        "name": "مركز التنمية الاجتماعية بالدمام",
        "latitude": 26.4473938,
        "longitude": 50.1087195,
        "city": "الدمام",
        "region": "المنطقة الشرقية",
        "address": "الدمام، المنطقة الشرقية",
        "phone": "",
        "email": None,
        "working_hours": "غير معلن — يُنصح بالتواصل للتأكد.",
        "services": ["خدمات التنمية الاجتماعية والتوعية الأسرية"],
        "specialties": [],
        "served_needs": ["دعم أسري", "التوعية والإرشاد"],
        "min_age_years": None,
        "max_age_years": None,
        "offers_in_person": True,
        "offers_remote": False,
        "description": (
            "مركز تنمية اجتماعية تابع لوزارة الموارد البشرية والتنمية الاجتماعية في الدمام. "
            "بيانات OpenStreetMap تصنّفه كمنشأة خدمة اجتماعية توعوية (outreach)، دون تفاصيل "
            "عن خدمات علاجية محددة — يُنصح بالتواصل المباشر لمعرفة ما يقدّمه هذا الفرع "
            "تحديدًا لأسر الأطفال ذوي الإعاقة."
        ),
        "source_urls": ["https://www.openstreetmap.org/node/13335254391", "https://www.hrsd.gov.sa"],
        "reviewed_at": OSM_REVIEWED_AT,
        "data_confidence": "medium",
    },
    {
        "name": "مركز السمو التخصصي للتوحد",
        "latitude": 26.3646829,
        "longitude": 50.1012647,
        "city": "الدمام",
        "region": "المنطقة الشرقية",
        "address": "الدمام",
        "phone": "",
        "email": None,
        "working_hours": "غير معلن — يُنصح بالتواصل للتأكد.",
        "services": ["برامج تخصصية لاضطراب طيف التوحد"],
        "specialties": ["اضطراب طيف التوحد"],
        "served_needs": ["دعم سلوكي", "دعم التواصل"],
        "min_age_years": None,
        "max_age_years": None,
        "offers_in_person": True,
        "offers_remote": False,
        "description": (
            "مركز متخصص في اضطراب طيف التوحد بالدمام (الاسم المنشور بالإنجليزية: HH "
            "Specialized Autism Center). لا تتوفر تفاصيل إضافية عن الفئات العمرية أو "
            "الخدمات الدقيقة من هذا المصدر — يُنصح بالتواصل المباشر للتأكد."
        ),
        "source_urls": ["https://www.openstreetmap.org/way/850758656"],
        "reviewed_at": OSM_REVIEWED_AT,
        "data_confidence": "medium",
    },
    {
        "name": "مركز التنمية الاجتماعية بالمدينة المنورة",
        "latitude": 24.4678349,
        "longitude": 39.5972447,
        "city": "المدينة المنورة",
        "region": "منطقة المدينة المنورة",
        "address": "المدينة المنورة",
        "phone": "",
        "email": None,
        "working_hours": "غير معلن — يُنصح بالتواصل للتأكد.",
        "services": ["خدمات التنمية الاجتماعية والتوعية الأسرية"],
        "specialties": [],
        "served_needs": ["دعم أسري", "التوعية والإرشاد"],
        "min_age_years": None,
        "max_age_years": None,
        "offers_in_person": True,
        "offers_remote": False,
        "description": (
            "مركز تنمية اجتماعية تابع لوزارة الموارد البشرية والتنمية الاجتماعية في المدينة "
            "المنورة. بيانات OpenStreetMap تصنّفه كمنشأة خدمة اجتماعية توعوية (outreach)، "
            "دون تفاصيل عن خدمات علاجية محددة — يُنصح بالتواصل المباشر لمعرفة ما يقدّمه هذا "
            "الفرع تحديدًا لأسر الأطفال ذوي الإعاقة."
        ),
        "source_urls": ["https://www.openstreetmap.org/node/13335312601", "https://www.hrsd.gov.sa"],
        "reviewed_at": OSM_REVIEWED_AT,
        "data_confidence": "medium",
    },
    {
        "name": "Medical Rehabilitation Hospital",
        "latitude": 24.4503311,
        "longitude": 39.6302648,
        "city": "المدينة المنورة",
        "region": "منطقة المدينة المنورة",
        "address": "المدينة المنورة",
        "phone": "",
        "email": None,
        "working_hours": "غير معلن — يُنصح بالتواصل للتأكد.",
        "services": ["رعاية تأهيلية"],
        "specialties": [],
        "served_needs": ["دعم حركي"],
        "min_age_years": None,
        "max_age_years": None,
        "offers_in_person": True,
        "offers_remote": False,
        "description": (
            "مستشفى تأهيل طبي في المدينة المنورة (اسمه على OpenStreetMap متوفر بالإنجليزية "
            "فقط: Medical Rehabilitation Hospital). لا تتوفر معلومات تؤكد وجود برامج مخصصة "
            "للأطفال تحديدًا — يُنصح بالتواصل المباشر للتأكد."
        ),
        "source_urls": ["https://www.openstreetmap.org/way/458592099"],
        "reviewed_at": OSM_REVIEWED_AT,
        "data_confidence": "medium",
    },
    {
        "name": "مركز التنمية الاجتماعية بأبها",
        "latitude": 18.2315927,
        "longitude": 42.581863,
        "city": "أبها",
        "region": "منطقة عسير",
        "address": "أبها، منطقة عسير",
        "phone": "",
        "email": None,
        "working_hours": "غير معلن — يُنصح بالتواصل للتأكد.",
        "services": ["خدمات التنمية الاجتماعية والتوعية الأسرية"],
        "specialties": [],
        "served_needs": ["دعم أسري", "التوعية والإرشاد"],
        "min_age_years": None,
        "max_age_years": None,
        "offers_in_person": True,
        "offers_remote": False,
        "description": (
            "مركز تنمية اجتماعية تابع لوزارة الموارد البشرية والتنمية الاجتماعية في أبها. "
            "بيانات OpenStreetMap تصنّفه كمنشأة خدمة اجتماعية توعوية (outreach)، دون تفاصيل "
            "عن خدمات علاجية محددة — يُنصح بالتواصل المباشر لمعرفة ما يقدّمه هذا الفرع "
            "تحديدًا لأسر الأطفال ذوي الإعاقة."
        ),
        "source_urls": ["https://www.openstreetmap.org/node/13335254393", "https://www.hrsd.gov.sa"],
        "reviewed_at": OSM_REVIEWED_AT,
        "data_confidence": "medium",
    },
]


def seed_real_centers(db: Session, *, check_migrations: bool = True) -> dict[str, int]:
    if check_migrations:
        assert_migrations_at_head()

    created = 0
    updated = 0
    for entry in REAL_CENTERS:
        reviewed_at = entry.get("reviewed_at", REVIEWED_AT)
        data_confidence = entry.get("data_confidence", "high")
        existing = db.scalar(
            select(Center).where(Center.name == entry["name"], Center.city == entry["city"])
        )
        if existing is None:
            db.add(
                Center(
                    name=entry["name"],
                    description=entry["description"],
                    city=entry["city"],
                    region=entry["region"],
                    address=entry["address"],
                    latitude=entry.get("latitude"),
                    longitude=entry.get("longitude"),
                    specialties=entry["specialties"],
                    services=entry["services"],
                    served_needs=entry["served_needs"],
                    min_age_years=entry["min_age_years"],
                    max_age_years=entry["max_age_years"],
                    offers_in_person=entry["offers_in_person"],
                    offers_remote=entry["offers_remote"],
                    phone=entry["phone"],
                    email=entry["email"],
                    working_hours=entry["working_hours"],
                    source_type="public_research",
                    source_urls=entry["source_urls"],
                    last_reviewed_at=reviewed_at,
                    data_confidence=data_confidence,
                )
            )
            created += 1
        else:
            existing.description = entry["description"]
            existing.region = entry["region"]
            existing.address = entry["address"]
            existing.latitude = entry.get("latitude")
            existing.longitude = entry.get("longitude")
            existing.specialties = entry["specialties"]
            existing.services = entry["services"]
            existing.served_needs = entry["served_needs"]
            existing.min_age_years = entry["min_age_years"]
            existing.max_age_years = entry["max_age_years"]
            existing.offers_in_person = entry["offers_in_person"]
            existing.offers_remote = entry["offers_remote"]
            existing.phone = entry["phone"]
            existing.email = entry["email"]
            existing.working_hours = entry["working_hours"]
            existing.source_type = "public_research"
            existing.source_urls = entry["source_urls"]
            existing.last_reviewed_at = reviewed_at
            existing.data_confidence = data_confidence
            updated += 1

    db.commit()
    return {"created": created, "updated": updated, "total": len(REAL_CENTERS)}


def main() -> None:
    settings = get_settings()
    if settings.environment == "production" and os.environ.get("WEAM_ALLOW_REAL_CENTER_SEED") != "true":
        raise SystemExit(
            "Refusing to seed real centers in production without explicit override. "
            "Set WEAM_ALLOW_REAL_CENTER_SEED=true if this is intentional."
        )

    with SessionLocal() as db:
        result = seed_real_centers(db)

    print(f"Real centers: {result['created']} created, {result['updated']} updated (of {result['total']} total).")


if __name__ == "__main__":
    main()
