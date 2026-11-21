from __future__ import annotations

import re
import sys
from getpass import getpass

from dotenv import load_dotenv
from sqlalchemy import select

load_dotenv()
from backend.app.core.database import SessionLocal
from backend.app.core.security import hash_password
from backend.app.models import AdminAccount


def main() -> None:
    # Run `alembic upgrade head` before this script.
    username = input("Admin username: ").strip().lower()
    password = getpass("Admin password (6+ characters): ")
    confirmation = getpass("Confirm admin password: ")
    if not re.fullmatch(r"[a-z0-9_]{3,50}", username):
        print("Username must be 3–50 characters and contain lowercase letters, numbers, or underscores.")
        sys.exit(1)
    if len(password) < 6 or len(password) > 128:
        print("Admin password must be 6–128 characters.")
        sys.exit(1)
    if password != confirmation:
        print("Password confirmation does not match.")
        sys.exit(1)
    with SessionLocal() as db:
        if db.scalar(select(AdminAccount.id).where(AdminAccount.username == username)):
            print("That administrator username already exists.")
            sys.exit(1)
        db.add(AdminAccount(username=username, password_hash=hash_password(password)))
        db.commit()
    print("Administrator account created successfully. You can sign in at /admin.")


if __name__ == "__main__":
    main()
