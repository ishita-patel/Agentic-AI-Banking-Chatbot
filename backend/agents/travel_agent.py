# backend/agents/travel_agent.py
from backend.agents.base_agent import BaseAgent
from typing import Dict, Any
import re

class TravelAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.capabilities = ["travel", "trip", "vacation"]
    
    async def process(self, user_id: str, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        query = context.get("query", task) if context else task
        query_lower = query.lower()
        
        # Extract destination
        destinations = ["japan", "thailand", "europe", "dubai", "india", "paris", "london", "bali", "singapore"]
        destination = "your destination"
        for d in destinations:
            if d in query_lower:
                destination = d.capitalize()
                break
        
        # Extract duration
        duration_match = re.search(r'(\d+)\s*(day|days|night|nights)', query_lower)
        duration = int(duration_match.group(1)) if duration_match else 7
        
        system_prompt = f"""
        You are a senior travel advisor at Aiko Bank. Provide professional travel planning advice.
        
        Travel Details:
        - Destination: {destination}
        - Duration: {duration} days
        
        Guidelines:
        1. Provide estimated trip costs (flights, accommodation, daily expenses)
        2. Suggest best time to visit
        3. Include visa requirements
        4. Provide travel tips and recommendations
        5. Suggest budget-friendly options
        6. Keep response under 250 words
        
        Make it practical and actionable.
        """
        
        response = await self.get_llm_response(system_prompt, query)
        
        return {
            "success": True,
            "message": response,
            "data": {"agent": "travel_agent", "destination": destination, "duration": duration}
        }