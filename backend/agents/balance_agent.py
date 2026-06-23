# backend/agents/balance_agent.py
from backend.agents.base_agent import BaseAgent
from typing import Dict, Any
from backend.data_loader import BankDataLoader

class BalanceAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.capabilities = ["balance", "account_balance", "balance_inquiry"]
        self.data_loader = BankDataLoader()
    
    async def process(self, user_id: str, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        query = context.get("query", task) if context else task
        
        # Get user data
        user = self.data_loader.get_user(user_id)
        
        if not user:
            return {
                "success": False,
                "message": "User not found",
                "data": {}
            }
        
        balances = {
            "savings": user["accounts"]["savings"]["balance"],
            "checking": user["accounts"]["checking"]["balance"],
            "name": user["name"],
            "account_age": user.get("account_age_years", 0)
        }
        
        system_prompt = f"""
        You are a senior banking advisor at Aiko Bank. Provide personalized account balance information.
        
        User Information:
        - Name: {balances['name']}
        - Savings Balance: ₹{balances['savings']:,.2f}
        - Checking Balance: ₹{balances['checking']:,.2f}
        - Account Age: {balances['account_age']} years
        
        Guidelines:
        1. Present balances clearly
        2. Provide financial insights based on balance levels
        3. Suggest savings goals
        4. Be professional and helpful
        5. Keep response under 200 words
        """
        
        response = await self.get_llm_response(system_prompt, query)
        
        return {
            "success": True,
            "message": response,
            "data": {"agent": "balance_agent", "balances": balances}
        }