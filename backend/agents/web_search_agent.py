# backend/agents/web_search_agent.py
from backend.agents.base_agent import BaseAgent
from typing import Dict, Any
import requests
import os
import json
from datetime import datetime

class WebSearchAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.capabilities = ["search_web", "realtime_info", "current_rates"]
    
    async def process(self, user_id: str, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        query = context.get("query", task) if context else task
        
        # Perform mock search (replace with real API later)
        search_results = self.mock_search(query)
        
        system_prompt = f"""
        You are a research analyst at Aiko Bank. Synthesize web search results into professional insights.
        
        Search Query: {query}
        
        Search Results:
        {json.dumps(search_results, indent=2)}
        
        Follow this professional research framework:
        
        Step 1 - Information Synthesis:
        - Extract key information from results
        - Identify reliable sources
        - Date-stamp the information
        
        Step 2 - Relevance Assessment:
        - Evaluate how information applies to user needs
        - Filter out outdated or irrelevant information
        
        Step 3 - Insights Generation:
        - Provide key takeaways
        - Identify trends or patterns
        - Connect to financial context
        
        Step 4 - Actionable Recommendations:
        - Based on the information found
        - Suggest practical next steps
        - Cite sources appropriately
        
        Format response:
        
        [INFORMATION SUMMARY]
        
        [KEY INSIGHTS]
        
        [RECOMMENDATIONS]
        
        [SOURCES]
        
        [DISCLAIMER]
        "Information is based on current search results. Please verify important details from official sources."
        """
        
        response = await self.get_llm_response(system_prompt, query)
        
        return {
            "success": True,
            "message": response,
            "data": {
                "agent": "web_search_agent",
                "llm_used": True,
                "search_results": search_results
            }
        }
    
    def mock_search(self, query):
        query_lower = query.lower()
        
        mock_data = {
            "japan": {
                "title": "Japan Travel Guide 2026",
                "snippet": "Japan remains a top destination. Best time to visit is March-April for cherry blossoms. Current USD/JPY rate is 1 USD = 156 JPY.",
                "source": "Japan Tourism Board",
                "date": datetime.now().strftime("%d-%b-%Y")
            },
            "mutual fund": {
                "title": "Mutual Fund Performance 2026",
                "snippet": "Top performing funds: Quant Mid Cap (18.5%), SBI Small Cap (17.2%), Axis Bluechip (15.8%). Market shows positive sentiment.",
                "source": "Value Research",
                "date": datetime.now().strftime("%d-%b-%Y")
            },
            "health insurance": {
                "title": "Health Insurance Premiums 2026",
                "snippet": "Star Health ₹8,500/year, HDFC Ergo ₹12,000/year. Claims settlement ratio highest for HDFC Ergo at 97%.",
                "source": "IRDAI Report",
                "date": datetime.now().strftime("%d-%b-%Y")
            },
            "default": {
                "title": f"Search Results for '{query}'",
                "snippet": "Real-time search results would appear here. Configure API key for live results.",
                "source": "Search Engine",
                "date": datetime.now().strftime("%d-%b-%Y")
            }
        }
        
        for key in mock_data:
            if key in query_lower:
                return mock_data[key]
        
        return mock_data["default"]