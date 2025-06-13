from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from auth import get_password_hash
from uuid import uuid4

models.Base.metadata.create_all(bind=engine)

def create_admin_user():
    db = SessionLocal()
    try:
        existing_admin = db.query(models.User).filter(models.User.role == "admin").first()
        if existing_admin:
            print("Admin user already exists")
            return
        
        admin_user = models.User(
            id=str(uuid4()),
            name="Admin User",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully")
        print("Email: admin@example.com")
        print("Password: admin123")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
