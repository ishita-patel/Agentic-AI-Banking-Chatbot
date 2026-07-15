from typing import Dict, Any

# Domains your assistant is allowed to answer
ALLOWED_DOMAINS = {
    "balance",
    "statement",
    "loan",
    "travel",
    "calculator",
    "health",
    "investment",
    "tax",
    "legal",
    "web_search",
    "rag",
}

# Intents that are allowed even if the router isn't perfect
ALLOWED_INTENTS = {
    "balance_inquiry",
    "statement_request",
    "loan_inquiry",
    "trip_planning",
    "currency_conversion",
    "financial_calculation",
    "investment_advice",
    "tax_query",
    "legal_query",
    "health_query",
    "document_question",
    "news_lookup",
    "banking_info",
}


class ScopeGuard:

    @staticmethod
    def check(analysis: Dict[str, Any]):

        primary = (
            analysis.get("primary_domain", "")
            .strip()
            .lower()
        )

        secondary = [
            d.lower()
            for d in analysis.get("secondary_domains", [])
        ]

        intent = (
            analysis.get("intent", "")
            .strip()
            .lower()
        )

        confidence = analysis.get("confidence", 0)

        # Primary domain allowed
        if primary in ALLOWED_DOMAINS:
            return True, None

        # Secondary domain allowed
        for domain in secondary:
            if domain in ALLOWED_DOMAINS:
                return True, None

        # Known intent allowed
        if intent in ALLOWED_INTENTS:
            return True, None

        # Low confidence? Don't block automatically.
        # Let the orchestrator fall back to the LLM/router.
        if confidence < 0.60:
            return True, "low_confidence"

        return False, "out_of_scope"