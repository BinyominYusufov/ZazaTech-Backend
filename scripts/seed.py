"""Seed script: create the first super_admin.

Run from the project root with the venv active:
    python scripts/seed.py

Synchronous on purpose: the project uses sync SQLAlchemy (no aiosqlite /
asyncio.run). It reuses the exact same `engine` as app/core/database.py.
"""

from __future__ import annotations

import sys

# Make the `app` package importable when run as `python scripts/seed.py`
# from the repository root.
sys.path.insert(0, ".")

from sqlmodel import Session, select  # noqa: E402

from app.core.database import create_db_and_tables, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.user import User  # noqa: E402

ADMIN_NAME = "Admin"
ADMIN_EMAIL = "admin@zazetech.com"
ADMIN_PASSWORD = "Admin123!"


def main() -> None:
    create_db_and_tables()

    with Session(engine) as session:
        existing = session.exec(
            select(User).where(User.role == "super_admin")
        ).first()
        if existing is not None:
            print(f"Super admin already exists: {existing.email}")
            return

        admin = User(
            name=ADMIN_NAME,
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            role="super_admin",
        )
        session.add(admin)
        session.commit()

    print(f"✓ Super admin created: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")


if __name__ == "__main__":
    # Windows consoles default to cp1252; force UTF-8 so the checkmark prints.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    main()
