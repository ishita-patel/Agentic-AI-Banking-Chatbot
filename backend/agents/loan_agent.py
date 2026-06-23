# backend/agents/loan_agent.py
from backend.agents.base_agent import BaseAgent
from typing import Dict, Any
from backend.data_loader import BankDataLoader
import re

class LoanAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.capabilities = ["loan", "emi", "eligibility"]
        self.data_loader = BankDataLoader()
    
    async def process(self, user_id: str, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        query = context.get("query", task) if context else task
        query_lower = query.lower()
        
        # Get user data
        user = self.data_loader.get_user(user_id)
        
        if not user:
            return {"success": False, "message": "User not found", "data": {}}
        
        savings = user["accounts"]["savings"]["balance"]
        monthly_income = user["employment"]["monthly_income"]
        credit_score = user.get("credit_score", 0)
        
        # Check for EMI calculation
        amounts = re.findall(r'(\d+)', query)
        loan_amount = None
        if amounts:
            for amt in amounts:
                if int(amt) > 1000:
                    loan_amount = int(amt)
                    break
        
        eligibility = savings > 25000 and monthly_income > 25000
        
        system_prompt = f"""
        You are a senior loan advisor at Aiko Bank. Provide professional loan guidance.
        
        User Financial Profile:
        - Savings Balance: ₹{savings:,.2f}
        - Monthly Income: ₹{monthly_income:,.2f}
        - Credit Score: {credit_score}
        - Loan Eligibility: {'ELIGIBLE' if eligibility else 'NOT ELIGIBLE'}
        
        {f"Requested Loan Amount: ₹{loan_amount:,.2f}" if loan_amount else "No specific loan amount requested"}
        
        Guidelines:
        1. If EMI calculation is requested, provide clear EMI breakdown
        2. If eligibility check is requested, explain the status clearly
        3. Provide loan recommendations based on the user's profile
        4. Include interest rates, tenure options, and monthly payments
        5. If not eligible, suggest improvement actions
        6. Keep response under 250 words
        
        Make it professional and actionable.
        """
        
        response = await self.get_llm_response(system_prompt, query)
        
        return {
            "success": True,
            "message": response,
            "data": {"agent": "loan_agent", "eligible": eligibility}
        }