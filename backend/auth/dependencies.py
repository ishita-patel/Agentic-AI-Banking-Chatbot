from fastapi import Depends
from fastapi.security import HTTPBearer
from fastapi import HTTPException
from backend.auth.jwt_handler import decode_token

security = HTTPBearer()


def get_current_user(
    credentials=Depends(security)
):

    try:

        payload = decode_token(
            credentials.credentials
        )

        return payload

    except Exception:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )