import json
import os

class IntentClassifier:
    def __init__(self, config_path="config/intents.json"):
        self.config_path = config_path
        self.banking_keywords = {
            "balance": ["balance", "savings", "checking", "account balance", "how much", "my money"],
            "statement": ["statement", "transactions", "transaction history", "download statement"],
            "loan": ["loan", "emi", "eligibility", "borrow", "personal loan"]
        }
        self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config = json.load(f)
                self.intents = config.get("intents", [])
        else:
            self.intents = []
    
    def classify(self, message):
        message_lower = message.lower()
        
        # Check for balance queries
        if any(word in message_lower for word in self.banking_keywords["balance"]):
            if "statement" not in message_lower and "loan" not in message_lower:
                return {
                    "agent": "balance",
                    "confidence": 0.9,
                    "layer": "keyword"
                }
        
        # Check for statement queries
        if any(word in message_lower for word in self.banking_keywords["statement"]):
            return {
                "agent": "statement",
                "confidence": 0.9,
                "layer": "keyword"
            }
        
        # Check for loan queries
        if any(word in message_lower for word in self.banking_keywords["loan"]):
            return {
                "agent": "loan",
                "confidence": 0.9,
                "layer": "keyword"
            }
        
        # Everything else goes to Groq
        return {
            "agent": "unknown",
            "confidence": 0,
            "layer": "unknown"
        }