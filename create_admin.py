from getpass import getpass

from app.db import SessionLocal, engine, Base
from app.models import User
from app.auth import hash_password


def main():
    Base.metadata.create_all(bind=engine)

    username = input("Superadmin username/email: ").strip().lower()

    if not username:
        print("Username is required.")
        return

    password = getpass("Password: ")
    confirm_password = getpass("Confirm password: ")

    if not password:
        print("Password is required.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    db = SessionLocal()

    try:
        exists = (
            db.query(User)
            .filter(User.username == username)
            .first()
        )

        if exists:
            print("User already exists:", username)
            return

        user = User(
            username=username,
            password_hash=hash_password(password),
            role="superadmin",
            is_active=True,
        )

        db.add(user)
        db.commit()

        print("Superadmin created:", username)

    finally:
        db.close()


if __name__ == "__main__":
    main()