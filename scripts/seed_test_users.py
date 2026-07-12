from __future__ import annotations

from backend.api.security import hash_password
from backend.db import models
from backend.db.session import SessionLocal, engine


TEST_USERS = [
    {
        "username": "admin",
        "password": "admin123",
        "tenant_id": "default",
        "is_admin": True,
    },
    {
        "username": "employee",
        "password": "user123",
        "tenant_id": "default",
        "is_admin": False,
    },
]


def main() -> None:
    models.Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        for item in TEST_USERS:
            user = session.query(models.User).filter(models.User.username == item["username"]).first()
            if user:
                user.hashed_password = hash_password(item["password"])
                user.tenant_id = item["tenant_id"]
                user.is_active = True
                user.is_admin = item["is_admin"]
                print(f"updated {item['username']}")
                continue

            session.add(
                models.User(
                    username=item["username"],
                    hashed_password=hash_password(item["password"]),
                    tenant_id=item["tenant_id"],
                    is_active=True,
                    is_admin=item["is_admin"],
                )
            )
            print(f"created {item['username']}")
        session.commit()
    finally:
        session.close()

    print("test users ready:")
    print("  admin / admin123")
    print("  employee / user123")


if __name__ == "__main__":
    main()
