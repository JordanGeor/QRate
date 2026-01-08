from app.db import SessionLocal, engine, Base
from app.models import User
from app.auth import hash_password

def main():
    Base.metadata.create_all(bind=engine)

    email = "admin@test.gr"
    password = "123456"

    db = SessionLocal()
    try:
        exists = db.query(User).filter(User.email == email).first()
        if exists:
            print("User already exists:", email)
            return

        u = User(email=email, password_hash=hash_password(password))
        db.add(u)
        db.commit()
        print("Created admin:", email, "password:", password)
    finally:
        db.close()

if __name__ == "__main__":
    main()
