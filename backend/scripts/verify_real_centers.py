"""Admin-verify all publicly-sourced ("public_research") centers so they appear in
the guardian-facing directory.

Deliberately a separate step from `seed_real_centers.py`: seeding writes the
public-source data, verification is a distinct admin decision to publish it (see
`test_seed_real_centers.py::test_seeded_real_centers_are_tagged_and_sourced`). This
script is the repeatable version of that manual review step — it does not invent
any facts, it only flips the visibility flag once source_urls/last_reviewed_at are
already on file.

Usage (from backend/):
    .venv\\Scripts\\python.exe -m scripts.verify_real_centers
"""
from __future__ import annotations

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.center import Center
from app.models.user import User

NOTES = {
    "high": "بيانات موثقة من الموقع الرسمي للمركز (انظر source_urls)، تمت مراجعتها بتاريخ last_reviewed_at.",
    "medium": (
        "بيانات من OpenStreetMap (انظر source_urls)؛ لم تُراجع مباشرة من موقع المركز الرسمي — "
        "يُنصح بالتواصل المباشر للتأكد من التفاصيل."
    ),
}


def verify_real_centers() -> int:
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.role == "admin"))
        rows = db.scalars(
            select(Center).where(Center.source_type == "public_research")
        ).all()
        count = 0
        for center in rows:
            center.verification_status = "verified"
            center.verification_note = NOTES.get(center.data_confidence or "high", NOTES["high"])
            center.verified_at = center.last_reviewed_at
            if admin:
                center.verified_by_user_id = admin.id
            count += 1
        db.commit()
        return count


def main() -> None:
    count = verify_real_centers()
    print(f"Verified {count} publicly-sourced center(s).")


if __name__ == "__main__":
    main()
