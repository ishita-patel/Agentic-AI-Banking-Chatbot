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

        # Protect against accidental misuse
        analysis = context.get("analysis", {}) if context else {}
        
        intent = analysis.get("intent", "")
        primary_domain = analysis.get("primary_domain", "")
        
        if primary_domain != "web_search":
            return {
                "success": False,
                "message": (
                    "Web Search Agent received a request "
                    "outside its supported scope."
                ),
                "data": {
                    "agent": "web_search_agent"
                }
            }

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
        You are Aiko Bank's real-time information retrieval agent.

        You ONLY answer queries that require current or frequently changing information.

        Examples:

        ✓ Latest RBI repo rate
        ✓ Current USD-INR exchange rate
        ✓ Latest SBI FD interest rate
        ✓ Recent banking regulations
        ✓ Today's gold price
        ✓ Current market news
        ✓ Latest SEBI circular

        Do NOT answer unrelated general knowledge.

        Use ONLY the supplied search results.

        If the search results do not contain enough information,
        state that no reliable recent information was found.

        User Query:

        {query}

        Live Search Results:

        {json.dumps(search_results["results"], indent=2)}

        Return:

        SUMMARY

        KEY INSIGHTS

        RECOMMENDATIONS

        SOURCES
        """

        response = await self.get_llm_response(
            system_prompt,
            query,
            context
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