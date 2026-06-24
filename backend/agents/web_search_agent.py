from backend.agents.base_agent import BaseAgent
from backend.tools.web_search import search_web

from typing import Dict, Any
import json


class WebSearchAgent(BaseAgent):

    def __init__(self):
        super().__init__()

        self.capabilities = [
            "search_web",
            "realtime_info",
            "news",
            "current_rates",
            "live_data"
        ]


    async def process(
        self,
        user_id: str,
        task: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:

        query = context.get(
            "query",
            task
        ) if context else task

        search_results = search_web(query)

        if not search_results.get("success"):

            return {
                "success": False,
                "message": (
                    f"Web search failed: "
                    f"{search_results.get('error')}"
                ),
                "data": {
                    "agent": "web_search_agent"
                }
            }

        system_prompt = f"""
You are a senior financial research analyst at Aiko Bank.

The user asked:

{query}

Live Search Results:

{json.dumps(search_results['results'], indent=2)}

Instructions:

1. Summarize the latest information.
2. Prioritize factual information from search results.
3. Mention important dates if available.
4. If the query is financial:
   - explain impact
   - provide practical guidance
5. Keep response concise and professional.
6. Do NOT say:
   "I do not have access to real-time data"
7. Use only information found in search results.

Format:

SUMMARY

KEY INSIGHTS

RECOMMENDATIONS

SOURCES
"""

        response = await self.get_llm_response(
            system_prompt,
            query
        )

        return {
            "success": True,
            "message": response,
            "data": {
                "agent": "web_search_agent",
                "live_search": True,
                "results_found": len(
                    search_results["results"]
                )
            }
        }