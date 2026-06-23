# backend/agents/health_agent.py
from backend.agents.base_agent import BaseAgent
from typing import Dict, Any

class HealthAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.capabilities = ["health", "insurance", "medical"]
    
    async def process(self, user_id: str, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        query = context.get("query", task) if context else task
        
        system_prompt = f"""
        You are a senior health insurance advisor at Aiko Bank. Provide professional health insurance guidance.
        
        Available Health Insurance Plans:
        1. Star Health Comprehensive - ₹5L coverage, ₹8,500/year
        2. HDFC Ergo Optima - ₹10L coverage, ₹12,000/year
        3. ICICI Lombard Complete - ₹7.5L coverage, ₹9,800/year
        4. New India Assurance - ₹5L coverage, ₹7,500/year
        
        Guidelines:
        1. Help compare plans based on user needs
        2. Explain coverage, premiums, and benefits
        3. Suggest the best plan based on user profile
        4. Mention claim settlement ratios
        5. Keep response under 250 words
        
        Make it professional and helpful.
        """
        
        response = await self.get_llm_response(system_prompt, query)
        
        return {
            "success": True,
            "message": response,
            "data": {"agent": "health_agent"}
        }