# backend/tools/web_search.py

import os
import requests


def search_web(query: str):

    api_key = os.getenv("SERPAPI_API_KEY")

    if not api_key:
        return {
            "error": "SERPAPI_API_KEY not configured"
        }

    url = "https://serpapi.com/search"

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": 5
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        data = response.json()

        results = []

        for item in data.get("organic_results", [])[:5]:

            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", "")
            })

        return {
            "success": True,
            "results": results
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }