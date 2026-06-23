# backend/agents/calculator_agent.py
from backend.agents.base_agent import BaseAgent
from typing import Dict, Any
import re

class CalculatorAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.capabilities = ["calculator", "math", "calculate"]
    
    async def process(self, user_id: str, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        query = context.get("query", task) if context else task
        
        system_prompt = f"""
        You are a financial calculator at Aiko Bank. Perform calculations and explain results.
        
        User Query: {query}
        
        Guidelines:
        1. Parse the calculation from the query
        2. Perform the calculation accurately
        3. Show step-by-step process
        4. Explain what the result means in practical terms
        5. Keep response clear and concise
        
        Make it accurate and easy to understand.
        """
        
        response = await self.get_llm_response(system_prompt, query)
        
        return {
            "success": True,
            "message": response,
            "data": {"agent": "calculator_agent"}
        }