import logging
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.chat import User
from app.core.config import settings

# Initialize logging
logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    """Initialize database with first admin user"""
    # Check if we already have any users
    user = db.query(User).first()
    if user:
        logger.info("Database already has data, skipping initialization")
        return

    logger.info("Creating initial admin user")
    admin_user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin"),  # Change in production!
        is_active=1
    )

    db.add(admin_user)
    db.commit()
    logger.info("Initial admin user created successfully")