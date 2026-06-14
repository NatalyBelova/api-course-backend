from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Token, User


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is missing",
        )

    token_value = credentials.credentials

    token = db.query(Token).filter(Token.token == token_value).first()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    if not token.is_active:
        raise HTTPException(
            status_code=401,
            detail="Token is inactive",
        )

    user = db.query(User).filter(User.id == token.user_id).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user