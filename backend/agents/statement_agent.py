# backend/agents/statement_agent.py
from backend.agents.base_agent import BaseAgent
from typing import Dict, Any
from backend.data_loader import BankDataLoader
from datetime import datetime, timedelta

class StatementAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.capabilities = ["statement", "transaction", "history"]
        self.data_loader = BankDataLoader()
    
    async def process(self, user_id: str, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        query = context.get("query", task) if context else task
        
        # Get user data
        user = self.data_loader.get_user(user_id)
        
        if not user:
            return {"success": False, "message": "User not found", "data": {}}
        
        # Get recent transactions
        transactions = self.data_loader.get_transactions(user_id, "savings", 30)
        
        if not transactions:
            return {"success": True, "message": "No recent transactions found.", "data": {}}
        
        # Format transactions for prompt
        tx_list = []
        for t in transactions[:20]:
            tx_list.append(f"- {t['date'][:10]}: {t['description']} - ₹{t['amount']:,.2f}")
        
        tx_text = "\n".join(tx_list)
        
        system_prompt = f"""
        You are a senior banking advisor at Aiko Bank. Provide a professional transaction history analysis.
        
        User: {user['name']}
        Recent Transactions (last 30 days):
        {tx_text}
        
        Guidelines:
        1. Summarize the transaction history
        2. Identify spending patterns
        3. Highlight any unusual or large transactions
        4. Provide financial insights
        5. Suggest budget improvements if needed
        6. Keep response under 250 words
        
        Make it professional and actionable.
        """
        
        response = await self.get_llm_response(system_prompt, query)
        
        return {
            "success": True,
            "message": response,
            "data": {"agent": "statement_agent", "transaction_count": len(tx_list)}
        }