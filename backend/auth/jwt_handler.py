from jose import jwt
from datetime import datetime, timedelta
import os

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: dict):

    payload = data.copy()

    expire = (
        datetime.utcnow()
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload.update(
        {"exp": expire}
    )

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def decode_token(token: str):

    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )