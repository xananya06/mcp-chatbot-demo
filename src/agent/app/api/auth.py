import sys
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from descope import AuthException, DescopeClient

from app.db.database import get_db
from app.models.chat import User
from app.core.config import settings
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)

# Initialize the security scheme
security = HTTPBearer()


class Auth:
    def __init__(self):
        try:
            if settings.DESCOPE_PROJECT_ID:
                self.descope_client = DescopeClient(
                    project_id=settings.DESCOPE_PROJECT_ID
                )
            else:
                self.descope_client = None
        except Exception as e:
            logger.error(f"Failed to create DescopeClient: {e}")
            sys.exit(1)

    def validate_session(self, db: Session, session_token: str):
        if not self.descope_client:
            logger.warning("No authorization active.")
            return 1

        # Authorize with Descope
        try:
            jwt_response = self.descope_client.validate_session(
                session_token=session_token
            )
            user_id = jwt_response["userId"]
            logger.info(
                f"Successfully validated user session: {jwt_response} for user: {user_id}"
            )
            user = db.query(User).filter(User.username == user_id).first()
            if user:
                logger.debug(f"User found in database: {user}")
                return user.id
            else:
                logger.info(f"User not found in database, creating new user: {user_id}")
                user = User(
                    username=user_id,
                    email=f"{user_id}@email.com",  # Replace with actual email from JWT
                    hashed_password=get_password_hash(
                        "dummy_password"
                    ),  # Replace with actual password hashing
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                return user.id
        except AuthException as error:
            logger.error(f"Could not validate user session. Error: {error}")
            return 0

    def get_verified_user_id(
        self,
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ):
        token = credentials.credentials
        user_id = self.validate_session(db, token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return user_id


auth = Auth()
