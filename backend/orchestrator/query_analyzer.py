import json
import re
from typing import Dict, Any
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from backend.agents.groq_agent import GroqAgent


class QueryAnalyzer:

    def __init__(self):
        self.llm = GroqAgent()
        self.tracer = trace.get_tracer("aiko-bank.query_analyzer")  # Changed tracer name

    async def analyze(
        self,
        query: str,
        user_id: str,
        has_documents: bool = False,
        history: list = None
    ) -> Dict[str, Any]:

        history = history or []

        # Start span first, then handle errors inside it
        with self.tracer.start_as_current_span(
            "LLM Router"
        ) as span:

            try:

                span.set_attribute(
                    "temperature",
                    0
                )

                span.set_attribute(
                    "has_documents",
                    has_documents
                )

                history_text = "\n".join(
                    [
                        f"{msg['role']}: {msg['content']}"
                        for msg in history[-5:]
                    ]
                )

                prompt = f"""
                You are a banking query router.

                Classify the query into ONE primary domain and optional secondary domains.

                Available domains:

                balance
                statement
                loan
                travel
                calculator
                health
                investment
                tax
                legal
                web_search
                rag
                general

                Conversation History:
                {history_text}

                Current Query:
                {query}

                Has Documents:
                {has_documents}

                Return ONLY valid JSON.

                Example:

                {{
                    "primary_domain":"loan",
                    "secondary_domains":["calculator"],
                    "intent":"loan_query",
                    "complexity":"medium",
                    "confidence":0.95
                }}
                """

                response = await self.llm.process(
                    prompt,
                    user_id=user_id,  # Pass real user_id instead of hardcoded value
                    temperature=0,
                    operation="query_analyzer"
                )

                print("\n========== RAW ROUTER RESPONSE ==========")
                print(type(response))
                print(response)
                print("=========================================\n")

                # CASE 1: GroqAgent returns dict

                if isinstance(response, dict):

                    if "response" in response:
                        response_text = response["response"]
                    elif "message" in response:
                        response_text = response["message"]
                    else:
                        response_text = str(response)

                else:
                    response_text = str(response)

                # Extract JSON if wrapped in text
                
                json_match = re.search(
                    r'\{.*\}',
                    response_text,
                    re.DOTALL
                )

                if json_match:
                    response_text = json_match.group(0)

                print("\n========== CLEANED JSON ==========")
                print(response_text)
                print("==================================\n")

                result = json.loads(response_text)

                # NEW: Add span attributes immediately after parsing result
                span.set_attribute(
                    "primary_domain",
                    result["primary_domain"]
                )

                span.set_attribute(
                    "secondary_domains",
                    ",".join(result["secondary_domains"])
                )

                span.set_attribute(
                    "intent",
                    result["intent"]
                )

                span.set_attribute(
                    "confidence",
                    result["confidence"]
                )

                # NEW: Add event for intent classification
                span.add_event("Intent classified")

                result.setdefault(
                    "primary_domain",
                    "general"
                )

                result.setdefault(
                    "secondary_domains",
                    []
                )

                result.setdefault(
                    "intent",
                    "general_query"
                )

                result.setdefault(
                    "complexity",
                    "simple"
                )

                result.setdefault(
                    "confidence",
                    0.5
                )

                if has_documents:
                    if (
                        "rag"
                        not in result["secondary_domains"]
                    ):
                        result["secondary_domains"].append(
                            "rag"
                        )

                # Record routing results on the Router span
                span.set_attribute(
                    "primary_domain",
                    result["primary_domain"]
                )

                span.set_attribute(
                    "secondary_domains",
                    ",".join(result["secondary_domains"])
                )

                span.set_attribute(
                    "intent",
                    result["intent"]
                )

                span.set_attribute(
                    "confidence",
                    result["confidence"]
                )

                # Mark success with proper status
                span.set_attribute("success", True)
                span.set_status(Status(StatusCode.OK))

                print("\n========== ROUTING RESULT ==========")
                print(result)
                print("====================================\n")

                return result

            except Exception as e:

                print(
                    f"Analyzer Error: {e}"
                )

                # Record exception and failure with proper status
                span.record_exception(e)
                span.set_attribute("success", False)
                span.set_status(Status(StatusCode.ERROR))

                return self.fallback_analysis(
                    query,
                    has_documents
                )

    def fallback_analysis(
        self,
        query: str,
        has_documents: bool
    ) -> Dict[str, Any]:

        query_lower = query.lower()

        primary_domain = "general"
        secondary_domains = []

        # BALANCE

        if any(
            word in query_lower
            for word in [
                "balance",
                "account balance",
                "checking",
                "savings"
            ]
        ):
            primary_domain = "balance"

        # STATEMENT

        elif any(
            word in query_lower
            for word in [
                "statement",
                "transaction",
                "history",
                "transactions"
            ]
        ):
            primary_domain = "statement"

        # LOAN

        elif any(
            word in query_lower
            for word in [
                "loan",
                "emi",
                "borrow",
                "eligibility",
                "interest rate",
                "home loan",
                "personal loan"
            ]
        ):
            primary_domain = "loan"

        # CALCULATOR

        elif any(
            word in query_lower
            for word in [
                "calculate",
                "add",
                "subtract",
                "multiply",
                "divide"
            ]
        ):
            primary_domain = "calculator"

        elif (
            re.search(r"\d+", query)
            and any(
                op in query
                for op in [
                    "+",
                    "-",
                    "*",
                    "/"
                ]
            )
        ):
            primary_domain = "calculator"

        # TRAVEL

        elif any(
            word in query_lower
            for word in [
                "travel",
                "trip",
                "vacation",
                "flight",
                "hotel",
                "japan",
                "dubai",
                "europe"
            ]
        ):
            primary_domain = "travel"

        # HEALTH

        elif any(
            word in query_lower
            for word in [
                "health",
                "insurance",
                "medical"
            ]
        ):
            primary_domain = "health"

        # INVESTMENT

        elif any(
            word in query_lower
            for word in [
                "sip",
                "mutual fund",
                "investment",
                "stock",
                "portfolio"
            ]
        ):
            primary_domain = "investment"

        # TAX

        elif any(
            word in query_lower
            for word in [
                "tax",
                "itr",
                "deduction",
                "80c"
            ]
        ):
            primary_domain = "tax"

        # LEGAL

        elif any(
            word in query_lower
            for word in [
                "legal",
                "agreement",
                "contract",
                "lease",
                "tenant"
            ]
        ):
            primary_domain = "legal"

        # Multi-agent

        if (
            "loan" in query_lower
            and (
                "emi" in query_lower
                or re.search(r"\d+", query)
            )
        ):
            secondary_domains.append(
                "calculator"
            )

        if has_documents:
            secondary_domains.append(
                "rag"
            )

        secondary_domains = list(
            set(secondary_domains)
        )

        result = {
            "primary_domain": primary_domain,
            "secondary_domains": secondary_domains,
            "intent": f"{primary_domain}_query",
            "complexity": (
                "medium"
                if secondary_domains
                else "simple"
            ),
            "confidence": 0.85
        }

        print("\n========== FALLBACK ROUTING ==========")
        print(result)
        print("======================================\n")

        return result