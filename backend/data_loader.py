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
                    print("CREATING SINGLETON DATALOADER INSTANCE")
                    cls._instance = super(BankDataLoader, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # Safer initialization check
        if getattr(self, "_initialized", False):
            return
            
        self.client = None
        self.db = None
        self._initialized = True
        
        # Debug: Check if URI exists before connecting
        mongodb_url = os.getenv("MONGODB_URL")
        print(f"Mongo URI Exists: {bool(mongodb_url)}")
        
        self.connect()
    
    def connect(self):
        """Connect to MongoDB using the same method as test_mongo.py"""
        try:
            mongodb_url = os.getenv("MONGODB_URL")
            
            if not mongodb_url:
                print("MONGODB_URL not found")
                self.client = None
                self.db = None
                return
            
            # Simple connection - identical to proven test_mongo.py
            self.client = MongoClient(
                mongodb_url.strip(),
                serverSelectionTimeoutMS=5000
            )
            
            # Verify connection
            self.client.admin.command("ping")
            self.db = self.client["bank_chatbot"]
            
            print("Connected to MongoDB")
            print(f"Mongo DB Connected: {self.db is not None}")
            
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            self.client = None
            self.db = None
    
    def _ensure_connection(self):
        """Check and re-establish connection if needed"""
        if self.client is None:
            print("No client exists, connecting...")
            self.connect()
            return
        
        try:
            self.client.admin.command("ping")
        except Exception as e:
            print(f"MongoDB connection lost: {e}")
            print("Attempting reconnect...")
            self.connect()
            # Verify reconnection worked
            if self.client is not None:
                try:
                    self.client.admin.command("ping")
                    print("Reconnection successful")
                except Exception:
                    print("Reconnection failed")
                    self.client = None
                    self.db = None
    
    def get_user(self, user_id):
        self._ensure_connection()
        
        if self.db is None:
            return None
        
        print(f"Fetching user: {user_id}")
        user = self.db.users.find_one({"user_id": user_id})
        print(f"User found: {user is not None}")
        
        if user is None:
            return None
        
        # Decrypt if needed
        if "encrypted_phone" in user and "phone" not in user:
            try:
                user = encryption_manager.decrypt_user_profile(user)
            except Exception as e:
                print(f"User decryption failed: {e}")
        
        user.pop("_id", None)
        return user
    
    def save_user_encrypted(self, user_data):
        self._ensure_connection()
        
        if self.db is None:
            return None
        
        encrypted_user = encryption_manager.encrypt_user_profile(user_data)
        result = self.db.users.update_one(
            {"user_id": user_data["user_id"]},
            {"$set": encrypted_user},
            upsert=True
        )
        return result
    
    def get_balance(self, user_id, account_type=None):
        user = self.get_user(user_id)
        
        if user is None:
            return None
        
        if account_type and account_type in user["accounts"]:
            return user["accounts"][account_type]["balance"]
        
        return {
            "savings": user["accounts"]["savings"]["balance"],
            "checking": user["accounts"]["checking"]["balance"]
        }
    
    def get_transactions(self, user_id, account_type=None, days=30):
        self._ensure_connection()
        
        if self.db is None:
            return []
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        query = {"user_id": user_id, "date": {"$gte": cutoff_date}}
        
        if account_type:
            query["account_type"] = account_type
        
        cursor = self.db.transactions.find(query).sort("date", -1)
        return list(cursor)
    
    def get_loan_eligibility(self, user_id):
        user = self.get_user(user_id)
        
        if user is None:
            return {"eligible": False, "reason": "User not found"}
        
        return {
            "eligible": user.get("loan_eligible", False),
            "credit_score": user.get("credit_score", 0),
            "account_age_years": user.get("account_age_years", 0),
            "savings_balance": user["accounts"]["savings"]["balance"],
            "monthly_income": user["employment"]["monthly_income"]
        }
    
    def get_all_users(self, limit=100):
        self._ensure_connection()
        
        if self.db is None:
            return []
        
        cursor = self.db.users.find({}, {"_id": 0}).limit(limit)
        users = list(cursor)
        processed_users = []
        
        for user in users:
            if "encrypted_phone" in user and "phone" not in user:
                try:
                    user = encryption_manager.decrypt_user_profile(user)
                except Exception as e:
                    print(f"User decryption failed: {e}")
            processed_users.append(user)
        
        return processed_users