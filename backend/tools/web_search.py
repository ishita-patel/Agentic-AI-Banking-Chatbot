# backend/tools/web_search.py
import os
import requests
import json
from typing import Dict, Any, List

class WebSearch:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        self.use_mock = not self.api_key
    
    async def search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Search the web using SerpAPI"""
        if self.use_mock:
            return self.mock_search(query)
        
        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": num_results,
                "engine": "google"
            }
            response = requests.get("https://serpapi.com/search", params=params, timeout=10)
            data = response.json()
            
            results = []
            for result in data.get("organic_results", [])[:num_results]:
                results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "link": result.get("link", "")
                })
            
            return {
                "success": True,
                "results": results,
                "source": "serpapi"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def mock_search(self, query: str) -> Dict[str, Any]:
        """Mock search for demo"""
        query_lower = query.lower()
        results = []
        
        # Mock responses for common queries
        mock_data = {
            "japan travel": {
                "title": "Japan Travel Guide 2026",
                "snippet": "Discover Japan with our comprehensive guide. Best time to visit is March-April for cherry blossoms or October-November for autumn colors."
            },
            "best time to visit japan": {
                "title": "Best Time to Visit Japan",
                "snippet": "March to April for cherry blossoms. October to November for autumn foliage. Summer is hot and humid. Winter is cold with snow in Hokkaido."
            },
            "flight to japan": {
                "title": "Flights to Japan",
                "snippet": "Round trip flights from India to Japan start from ₹60,000. Airlines: Air India, Japan Airlines, Emirates."
            },
            "health insurance": {
                "title": "Best Health Insurance India 2026",
                "snippet": "Compare top health insurance plans with benefits and premiums. Find coverage up to ₹1 crore."
            }
        }
        
        # Find matching mock data
        for key, data in mock_data.items():
            if key in query_lower:
                results.append(data)
                break
        
        if not results:
            results.append({
                "title": f"Search results for '{query}'",
                "snippet": "Real web search results would appear here. Configure SERPAPI_KEY in .env for live results."
            })
        
        return {
            "success": True,
            "results": results,
            "source": "mock"
        }