# src/db/seed.py
from .database import engine, SessionLocal, Base
from . import models, crud, auth

def init_db(admin_user: str = "admin", admin_pass: str = "password"):
    # create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing = crud.get_user_by_username(db, admin_user)
        if existing:
            print(f"User '{admin_user}' already exists, skipping creation.")
            return

        hashed = auth.hash_password(admin_pass)
        crud.create_user(db, admin_user, hashed)
        print(f"Created user '{admin_user}' with provided password.")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
