from datetime import datetime
from backend.data_loader import BankDataLoader


class AuditLogger:

    def __init__(self):
        self.loader = BankDataLoader()
        self.db = self.loader.db

    def log(
        self,
        user_id,
        action,
        details=None,
        ip=None
    ):

        if self.db is None:
            return

        self.db.audit_logs.insert_one({
            "user_id": user_id,
            "action": action,
            "details": details,
            "ip": ip,
            "timestamp": datetime.utcnow()
        })