# backend/agents/investment_agent.py
from backend.agents.base_agent import BaseAgent
from typing import Dict, Any

class InvestmentAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.capabilities = ["investment", "mutual_fund", "sip"]
    
    async def process(self, user_id: str, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        query = context.get("query", task) if context else task
        
        system_prompt = f"""
        You are a SEBI-registered investment advisor at Aiko Bank. Provide professional investment guidance.
        
        Investment Options:
        1. Large Cap Funds - 10-12% returns, Low risk
        2. Mid Cap Funds - 12-15% returns, Moderate risk
        3. Small Cap Funds - 15-20% returns, High risk
        4. ELSS Funds - 12-15% returns, 3-year lock-in, Tax benefit
        5. Balanced Funds - 10-12% returns, Balanced risk
        
        Guidelines:
        1. Provide investment recommendations based on risk profile
        2. Suggest SIP amounts and frequency
        3. Include tax implications
        4. Provide projected returns
        5. Keep response under 250 words
        
        Make it professional and actionable.
        """
        
        response = await self.get_llm_response(system_prompt, query)
        
        return {
            "success": True,
            "message": response,
            "data": {"agent": "investment_agent"}
        }