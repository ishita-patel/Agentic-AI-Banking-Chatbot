from data_loader import BankDataLoader

data_loader = BankDataLoader()

class BalanceAgent:
    async def process(self, user_id: str, message: str) -> dict:
        user = data_loader.get_user(user_id)
        
        if not user:
            return {
                "response": f"User {user_id} not found",
                "data": None
            }
        
        message_lower = message.lower()
        
        if "savings" in message_lower:
            balance = user["accounts"]["savings"]["balance"]
            response = f"Your savings account balance is {balance:,.2f}"
        elif "checking" in message_lower:
            balance = user["accounts"]["checking"]["balance"]
            response = f"Your checking account balance is {balance:,.2f}"
        else:
            savings = user["accounts"]["savings"]["balance"]
            checking = user["accounts"]["checking"]["balance"]
            response = f"Savings: {savings:,.2f}\nChecking: {checking:,.2f}"
        
        return {
            "response": response,
            "data": user["accounts"]
        }