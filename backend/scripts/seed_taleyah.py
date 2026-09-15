"""Create the غيداء / تالية single-child demo persona, built for the
presentation walkthrough script. Independent of the four-child seed_demo.py
pool.

Usage (from backend/):
    .venv\\Scripts\\python.exe -m scripts.seed_taleyah              # create (safe to rerun)
    .venv\\Scripts\\python.exe -m scripts.seed_taleyah --rebuild     # delete and recreate
    .venv\\Scripts\\python.exe -m scripts.seed_taleyah --reset       # delete only
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import select

import app.models  # noqa: F401
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.child import Child
from app.models.user import User
from scripts._seed_shared import assert_migrations_at_head
from scripts.demo_data.shared import DEMO_PASSWORD
from scripts.demo_data.taleyah import DEMO_BATCH, EXTERNAL_REF, build


def _delete(db) -> tuple[int, int]:
    children = db.scalars(select(Child).where(Child.external_ref == EXTERNAL_REF)).all()
    for child in children:
        db.delete(child)
    db.flush()
    users = db.scalars(select(User).where(User.demo_batch == DEMO_BATCH)).all()
    for user in users:
        db.delete(user)
    db.flush()
    return len(children), len(users)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    if settings.environment == "production" and os.environ.get("WEAM_ALLOW_DEMO_SEED") != "true":
        raise SystemExit(
            "Refusing to run demo seeding in production without explicit override. "
            "Set WEAM_ALLOW_DEMO_SEED=true if this is intentional."
        )

    assert_migrations_at_head()

    with SessionLocal() as db:
        if args.reset:
            deleted_children, deleted_users = _delete(db)
            db.commit()
            print(f"Reset: removed {deleted_children} child(ren), {deleted_users} user(s).")
            return

        if args.rebuild:
            _delete(db)
            db.flush()

        existing = db.scalar(select(Child.id).where(Child.external_ref == EXTERNAL_REF))
        if existing:
            db.commit()
            print("تالية already exists — skipped (use --rebuild to recreate).")
            print(f"Guardian login: ghaidaa@weam.demo / {DEMO_PASSWORD}")
            return

        now = datetime.now(timezone.utc)
        build(db, now=now)
        db.commit()
        print("تالية demo persona created.")
        print(f"Guardian login: ghaidaa@weam.demo / {DEMO_PASSWORD}")
        print("Care team logins (same password): audiologist.taleyah@, slp.taleyah@, "
              "behavioral.taleyah@, teacher.taleyah@weam.demo")


if __name__ == "__main__":
    main()
