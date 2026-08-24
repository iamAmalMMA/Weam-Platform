from __future__ import annotations

import argparse
from getpass import getpass

from sqlalchemy import select

from app.core.constants import UserRole, VerificationStatus
from app.db.session import SessionLocal
from app.models.user import User
from app.services.security import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or promote a Weam admin account")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="إدارة وئام")
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="Request and save a new password when the account already exists",
    )
    args = parser.parse_args()
    email = args.email.lower().strip()
    if not email or "@" not in email:
        raise SystemExit("A valid email is required")

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        account_existed = user is not None
        password_changed = False
        password_hash: str | None = None
        if not user or not user.password_hash or args.reset_password:
            password = getpass("Admin password (8+ characters): ")
            if len(password) < 8:
                raise SystemExit("Password must contain at least 8 characters")
            password_hash = hash_password(password)
            password_changed = True
        if not user:
            assert password_hash is not None
            user = User(
                email=email,
                full_name=args.name.strip() or "إدارة وئام",
                password_hash=password_hash,
                role=UserRole.ADMIN.value,
                verification_status=VerificationStatus.VERIFIED.value,
                auth_provider="password",
                is_active=True,
            )
            db.add(user)
        else:
            user.role = UserRole.ADMIN.value
            user.verification_status = VerificationStatus.VERIFIED.value
            user.is_active = True
            if password_changed:
                assert password_hash is not None
                user.password_hash = password_hash
                user.auth_provider = "password+google" if user.auth_provider == "google" else user.auth_provider
            db.add(user)
        db.commit()
    print(f"Admin account is ready: {email}")
    if account_existed and not password_changed:
        print("Existing password was not changed. Use --reset-password to set a new one.")
    elif account_existed:
        print("Existing admin password was updated.")


if __name__ == "__main__":
    main()
