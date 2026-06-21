from pymongo import MongoClient
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from encryption import encryption_manager

load_dotenv()

class BankDataLoader:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        mongodb_url = os.getenv("MONGODB_URL")
        if mongodb_url:
            self.client = MongoClient(mongodb_url)
            self.db = self.client["bank_chatbot"]
            print("Connected to MongoDB for data loading")
        else:
            print("MONGODB_URL not found")
    
        # backend/data_loader.py
    def get_user(self, user_id):
        if self.db is None:
            return None
        
        user = self.db.users.find_one({"user_id": user_id})
        
        if user is None:
            return None
        
        if "encrypted_phone" in user:
            user = encryption_manager.decrypt_user_profile(user)
        
        user.pop("_id", None)
        
        return user
    
    def save_user_encrypted(self, user_data):
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
        if self.db is None:
            return []
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        query = {
            "user_id": user_id,
            "date": {"$gte": cutoff_date}
        }
        
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
        if self.db is None:
            return []
        
        cursor = self.db.users.find({}, {"_id": 0}).limit(limit)
        users = list(cursor)
        
        decrypted_users = []
        for user in users:
            if "encrypted_phone" in user:
                decrypted_users.append(encryption_manager.decrypt_user_profile(user))
            else:
                decrypted_users.append(user)
        
        return decrypted_users