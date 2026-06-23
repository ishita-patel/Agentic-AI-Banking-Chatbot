print("LOADED: backend/orchestrator/orchestrator.py")
# backend/orchestrator/orchestrator.py

from typing import Dict, Any, List

from backend.orchestrator.query_analyzer import QueryAnalyzer

from backend.agents.groq_agent import GroqAgent

from backend.agents.balance_agent import BalanceAgent
from backend.agents.loan_agent import LoanAgent
from backend.agents.statement_agent import StatementAgent
from backend.agents.travel_agent import TravelAgent
from backend.agents.calculator_agent import CalculatorAgent
from backend.agents.health_agent import HealthAgent
from backend.agents.investment_agent import InvestmentAgent
from backend.agents.tax_agent import TaxAgent
from backend.agents.legal_agent import LegalAgent
from backend.agents.web_search_agent import WebSearchAgent
from backend.agents.rag_agent import RAGAgent
from backend.agents.groq_agent import GroqAgent


class Orchestrator:

    def __init__(self):

        self.query_analyzer = QueryAnalyzer()

        self.llm = GroqAgent()

        self.agents = self.initialize_agents()

        self.conversation_memory = {}

    # =====================================================
    # AGENT REGISTRY
    # =====================================================

    def initialize_agents(self):

        return {
            "balance": BalanceAgent(),
            "statement": StatementAgent(),
            "loan": LoanAgent(),
            "travel": TravelAgent(),
            "calculator": CalculatorAgent(),
            "health": HealthAgent(),
            "investment": InvestmentAgent(),
            "tax": TaxAgent(),
            "legal": LegalAgent(),
            "web_search": WebSearchAgent(),
            "rag": RAGAgent()
        }

    # =====================================================
    # MEMORY
    # =====================================================

    def get_history(self, user_id):

        return self.conversation_memory.get(
            user_id,
            []
        )

    def save_message(
        self,
        user_id,
        role,
        content
    ):

        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = []

        self.conversation_memory[user_id].append(
            {
                "role": role,
                "content": content
            }
        )

        self.conversation_memory[user_id] = (
            self.conversation_memory[user_id][-10:]
        )

    # =====================================================
    # MAIN PROCESSOR
    # =====================================================

    async def process(
        self,
        user_id: str,
        query: str,
        has_documents: bool = False
    ) -> Dict[str, Any]:

        try:

            self.save_message(
                user_id,
                "user",
                query
            )

            history = self.get_history(user_id)

            analysis = await self.query_analyzer.analyze(
                query=query,
                user_id=user_id,
                has_documents=has_documents,
                history=history
            )

            primary_domain = analysis.get(
                "primary_domain",
                "general"
            )

            secondary_domains = analysis.get(
                "secondary_domains",
                []
            )

            domains = []

            if primary_domain != "general":
                domains.append(primary_domain)

            domains.extend(secondary_domains)

            domains = list(dict.fromkeys(domains))

            if not domains:

                response = await self.handle_general_query(
                    query,
                    history
                )

                self.save_message(
                    user_id,
                    "assistant",
                    response
                )

                return {
                    "success": True,
                    "response": response,
                    "analysis": analysis,
                    "agents_used": ["groq"]
                }

            agent_results = []

            successful_agents = []

            for domain in domains:

                if domain not in self.agents:
                    continue

                try:

                    agent = self.agents[domain]

                    context = {
                        "query": query,
                        "analysis": analysis,
                        "history": history,
                        "has_documents": has_documents
                    }

                    result = await agent.process(
                        user_id,
                        query,
                        context
                    )

                    if result.get("success"):

                        successful_agents.append(
                            domain
                        )

                        agent_results.append(
                            result.get(
                                "message",
                                ""
                            )
                        )

                except Exception as e:

                    print(
                        f"{domain} agent error: {e}"
                    )

            # ---------------------------------
            # Fallback
            # ---------------------------------

            if not agent_results:

                response = await self.handle_general_query(
                    query,
                    history
                )

                self.save_message(
                    user_id,
                    "assistant",
                    response
                )

                return {
                    "success": True,
                    "response": response,
                    "analysis": analysis,
                    "agents_used": ["groq"]
                }

            # ---------------------------------
            # Single Agent
            # ---------------------------------

            if len(agent_results) == 1:

                final_response = agent_results[0]

            # ---------------------------------
            # Multi Agent Synthesis
            # ---------------------------------

            else:

                final_response = await self.synthesize_results(
                    query,
                    agent_results
                )

            self.save_message(
                user_id,
                "assistant",
                final_response
            )

            return {
                "success": True,
                "response": final_response,
                "analysis": analysis,
                "agents_used": successful_agents,
                "primary_agent": (
                    successful_agents[0]
                    if successful_agents
                    else "groq"
                )
            }

        except Exception as e:

            print(f"Orchestrator Error: {e}")

            return {
                "success": False,
                "response": (
                    "I encountered an error "
                    "processing your request."
                ),
                "agents_used": ["error"]
            }

    # =====================================================
    # GENERAL CHAT
    # =====================================================

    async def handle_general_query(
        self,
        query,
        history
    ):

        history_text = "\n".join(
            [
                f"{m['role']}: {m['content']}"
                for m in history[-5:]
            ]
        )

        prompt = f"""
Conversation History:

{history_text}

User Query:

{query}

Respond naturally and conversationally.
"""

        return await self.llm.process(
            prompt,
            user_id="general_chat"
        )

    # =====================================================
    # SYNTHESIS
    # =====================================================

    async def synthesize_results(
        self,
        query,
        agent_outputs
    ):

        combined = "\n\n".join(
            agent_outputs
        )

        prompt = f"""
User Query:
{query}

Agent Outputs:
{combined}

Create ONE natural response.

Rules:
- Do not mention agents
- Remove repetition
- Keep it conversational
- Provide actionable guidance
"""

        return await self.llm.process(
            prompt,
            user_id="synthesizer"
        )

    # =====================================================
    # DOCUMENT UPLOAD
    # =====================================================

    async def upload_document(
        self,
        user_id,
        file_path
    ):

        rag_agent = self.agents.get("rag")

        if not rag_agent:

            return {
                "success": False,
                "message": "RAG unavailable"
            }

        return await rag_agent.upload_document(
            user_id,
            file_path
        )

    # =====================================================
    # STATUS
    # =====================================================

    def get_agent_status(self):

        return {
            name: True
            for name in self.agents
        }

    def get_available_agents(self):

        return list(
            self.agents.keys()
        )