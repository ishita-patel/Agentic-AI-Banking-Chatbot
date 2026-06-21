from cryptography.fernet import Fernet
import os
import json
import base64
from dotenv import load_dotenv

load_dotenv()

class EncryptionManager:
    def __init__(self):
        self.key = self.get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def get_or_create_key(self):
        existing_key = os.getenv("ENCRYPTION_KEY")
        
        if existing_key:
            return existing_key.encode()
        else:
            new_key = Fernet.generate_key()
            print("Generated new encryption key. Add to .env file:")
            print(f"ENCRYPTION_KEY={new_key.decode()}")
            return new_key
    
    def encrypt(self, data):
        if data is None:
            return None
        
        if isinstance(data, dict):
            json_str = json.dumps(data)
        elif isinstance(data, str):
            json_str = data
        else:
            json_str = str(data)
        
        encrypted = self.cipher.encrypt(json_str.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data):
        if encrypted_data is None:
            return None
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            result = json.loads(decrypted.decode())
            return result
        except Exception as e:
            print(f"Decryption error: {e}")
            return None
    
    def encrypt_user_profile(self, user_data):
        sensitive_fields = [
            "phone", "email", "address", "pan_number", 
            "aadhar_last_4", "account_number"
        ]
        
        encrypted_data = {}
        
        for key, value in user_data.items():
            if key in sensitive_fields:
                encrypted_data[f"encrypted_{key}"] = self.encrypt(value)
            elif isinstance(value, dict):
                encrypted_data[key] = self.encrypt_nested_dict(value, sensitive_fields)
            else:
                encrypted_data[key] = value
        
        return encrypted_data
    
    def encrypt_nested_dict(self, data, sensitive_fields):
        result = {}
        for key, value in data.items():
            if key in sensitive_fields:
                result[f"encrypted_{key}"] = self.encrypt(value)
            elif isinstance(value, dict):
                result[key] = self.encrypt_nested_dict(value, sensitive_fields)
            else:
                result[key] = value
        return result
    
    def decrypt_user_profile(self, encrypted_user_data):
        decrypted_data = {}
        
        for key, value in encrypted_user_data.items():
            if key.startswith("encrypted_"):
                original_key = key.replace("encrypted_", "")
                decrypted_data[original_key] = self.decrypt(value)
            elif isinstance(value, dict):
                decrypted_data[key] = self.decrypt_nested_dict(value)
            else:
                decrypted_data[key] = value
        
        return decrypted_data
    
    def decrypt_nested_dict(self, data):
        result = {}
        for key, value in data.items():
            if key.startswith("encrypted_"):
                original_key = key.replace("encrypted_", "")
                result[original_key] = self.decrypt(value)
            elif isinstance(value, dict):
                result[key] = self.decrypt_nested_dict(value)
            else:
                result[key] = value
        return result

encryption_manager = EncryptionManager()