"""Create the default admin user for local testing."""

from sqlalchemy import select

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.models.user import User, UserRole

ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "admin123"
ADMIN_NAME = "Admin"


def create_admin() -> None:
    """Create the default admin user if it does not exist."""

    with SessionLocal() as db:
        existing_user = db.scalar(select(User).where(User.email == ADMIN_EMAIL))

        if existing_user is not None:
            if existing_user.role == UserRole.ADMIN:
                print("Default admin already exists.")
                return

            existing_user.role = UserRole.ADMIN
            db.commit()

            print("Existing user promoted to admin.")
            return

        admin = User(
            name=ADMIN_NAME,
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            role=UserRole.ADMIN,
        )

        db.add(admin)
        db.commit()

        print("Default admin created.")


if __name__ == "__main__":
    create_admin()
