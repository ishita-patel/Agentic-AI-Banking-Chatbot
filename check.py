from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URL"))
db = client["bank_chatbot"]

for uid in ["user_001", "user_002"]:
    user = db.users.find_one(
        {"user_id": uid},
        {
            "_id": 0,
            "name": 1,
            "mfa_enabled": 1,
            "totp_secret": 1
        }
    )
    print(uid, user)