from pymongo import MongoClient
from datetime import datetime, timedelta
import os
import threading

from dotenv import load_dotenv

from backend.encryption import encryption_manager

load_dotenv()


class BankDataLoader:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    print("Creating singleton BankDataLoader")
                    cls._instance = super(
                        BankDataLoader,
                        cls
                    ).__new__(cls)

                    cls._instance._initialized = False

        return cls._instance

    def __init__(self):

        if getattr(self, "_initialized", False):
            return

        self.client = None
        self.db = None

        self._initialized = True

        self.connect()

    # =====================================================
    # CONNECTION MANAGEMENT
    # =====================================================

    def connect(self):

        try:

            mongodb_url = os.getenv(
                "MONGODB_URL"
            )

            if not mongodb_url:

                print(
                    "MONGODB_URL not found"
                )

                return

            self.client = MongoClient(
                mongodb_url.strip(),
                serverSelectionTimeoutMS=5000
            )

            self.client.admin.command(
                "ping"
            )

            self.db = self.client[
                "bank_chatbot"
            ]

            print(
                "Connected to MongoDB"
            )

        except Exception as e:

            print(
                f"Mongo connection failed: {e}"
            )

            self.client = None
            self.db = None

    def ensure_connection(self):

        if self.client is None:
            self.connect()

        if self.client is None:
            return False

        try:

            self.client.admin.command(
                "ping"
            )

            return True

        except Exception as e:

            print(
                f"Mongo connection lost: {e}"
            )

            self.connect()

            return (
                self.client is not None
            )

    # =====================================================
    # USER AUTHENTICATION
    # =====================================================

    def get_user_by_username(
        self,
        username: str
    ):

        if not self.ensure_connection():
            return None

        user = self.db.users.find_one(
            {
                "username": username
            }
        )

        if user:
            user.pop("_id", None)

        return user

    def get_user(
        self,
        user_id: str
    ):

        if not self.ensure_connection():
            return None

        user = self.db.users.find_one(
            {
                "user_id": user_id
            }
        )

        if not user:
            return None

        if (
            "encrypted_phone" in user
            and "phone" not in user
        ):
            try:
                user = (
                    encryption_manager
                    .decrypt_user_profile(
                        user
                    )
                )
            except Exception as e:
                print(
                    f"Decryption failed: {e}"
                )

        user.pop("_id", None)

        return user

    def save_user_encrypted(
        self,
        user_data
    ):

        if not self.ensure_connection():
            return None

        encrypted_user = (
            encryption_manager
            .encrypt_user_profile(
                user_data
            )
        )

        result = (
            self.db.users.update_one(
                {
                    "user_id":
                    user_data["user_id"]
                },
                {
                    "$set":
                    encrypted_user
                },
                upsert=True
            )
        )

        return result

    # =====================================================
    # ACCOUNT OPERATIONS
    # =====================================================

    def get_balance(
        self,
        user_id,
        account_type=None
    ):

        user = self.get_user(
            user_id
        )

        if not user:
            return None

        if (
            account_type
            and account_type
            in user["accounts"]
        ):
            return (
                user["accounts"]
                [account_type]
                ["balance"]
            )

        return {
            "savings":
            user["accounts"]
            ["savings"]
            ["balance"],

            "checking":
            user["accounts"]
            ["checking"]
            ["balance"]
        }

    def get_transactions(
        self,
        user_id,
        account_type=None,
        days=30
    ):

        if not self.ensure_connection():
            return []

        cutoff_date = (
            datetime.now()
            - timedelta(days=days)
        ).isoformat()

        query = {
            "user_id": user_id,
            "date": {
                "$gte": cutoff_date
            }
        }

        if account_type:
            query[
                "account_type"
            ] = account_type

        cursor = (
            self.db.transactions
            .find(query)
            .sort("date", -1)
        )

        return list(cursor)

    # =====================================================
    # LOAN OPERATIONS
    # =====================================================

    def get_loan_eligibility(
        self,
        user_id
    ):

        user = self.get_user(
            user_id
        )

        if not user:

            return {
                "eligible": False,
                "reason":
                "User not found"
            }

        return {
            "eligible":
            user.get(
                "loan_eligible",
                False
            ),

            "credit_score":
            user.get(
                "credit_score",
                0
            ),

            "account_age_years":
            user.get(
                "account_age_years",
                0
            ),

            "savings_balance":
            user["accounts"]
            ["savings"]
            ["balance"],

            "monthly_income":
            user["employment"]
            ["monthly_income"]
        }

    # =====================================================
    # ADMIN / RBAC
    # =====================================================

    def get_all_users(
        self,
        limit=100
    ):

        if not self.ensure_connection():
            return []

        cursor = (
            self.db.users
            .find(
                {},
                {"_id": 0}
            )
            .limit(limit)
        )

        users = list(cursor)

        processed = []

        for user in users:

            if (
                "encrypted_phone"
                in user
                and "phone"
                not in user
            ):
                try:
                    user = (
                        encryption_manager
                        .decrypt_user_profile(
                            user
                        )
                    )
                except:
                    pass

            processed.append(user)

        return processed

    # =====================================================
    # AUDIT LOGGING
    # =====================================================

    def save_audit_log(
        self,
        user_id,
        action,
        status,
        metadata=None
    ):

        if not self.ensure_connection():
            return

        self.db.audit_logs.insert_one(
            {
                "user_id": user_id,
                "action": action,
                "status": status,
                "metadata":
                metadata or {},
                "timestamp":
                datetime.utcnow()
            }
        )