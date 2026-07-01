from backend.data_loader import BankDataLoader
from backend.auth.password_utils import verify_password
from backend.auth.jwt_handler import create_access_token


class AuthService:

    def __init__(self):
        self.loader = BankDataLoader()

    def login(
        self,
        username,
        password
    ):
        user = self.loader.get_user_by_username(
            username
        )

        if not user:
            return None

        if not verify_password(
            password,
            user["password_hash"]
        ):
            return None

        token = create_access_token(
            {
                "user_id": user["user_id"],
                "role": user.get(
                    "role",
                    "customer"
                )
            }
        )

        return token