from typing import Dict, Any, List
from opentelemetry import trace

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
#from backend.agents.rag_agent import RAGAgent
from backend.agents.groq_agent import GroqAgent

from opentelemetry.trace import Status, StatusCode
import time

from backend.services.langfuse_client import langfuse

tracer = trace.get_tracer(__name__)

class Orchestrator:

    def __init__(self):

        self.query_analyzer = QueryAnalyzer()
        self.llm = GroqAgent()
        self.agents = self.initialize_agents()
        self.conversation_memory = {}

    # AGENT REGISTRY

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
            #"rag": RAGAgent()
        }

    # MEMORY

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

    # MAIN PROCESSOR

    async def process(
        self,
        user_id: str,
        query: str,
        has_documents: bool = False
    ) -> Dict[str, Any]:

        # CREATE CHAT_REQUEST TRACE AROUND THE ENTIRE PROCESS
        with tracer.start_as_current_span("chat_request") as chat_span:
            
            # Set initial attributes
            chat_span.set_attribute("user_id", user_id)
            chat_span.set_attribute("query_length", len(query))
            
            try:
                self.save_message(
                    user_id,
                    "user",
                    query
                )

                history = self.get_history(user_id)

                # ROUTER SPAN - Query Analysis and Domain Routing
                with tracer.start_as_current_span("Router") as router_span:
                    
                    analysis = await self.query_analyzer.analyze(
                        query=query,
                        user_id=user_id,
                        has_documents=has_documents,
                        history=history
                    )
                    
                    # Set Router attributes
                    primary_domain = analysis.get("primary_domain", "general")
                    secondary_domains = analysis.get("secondary_domains", [])
                    
                    router_span.set_attribute("primary_domain", primary_domain)
                    router_span.set_attribute("secondary_domains", str(secondary_domains))
                    router_span.set_attribute("intent", analysis.get("intent"))
                    router_span.set_attribute("confidence", analysis.get("confidence"))
                    
                    # Set chat_request attributes
                    chat_span.set_attribute("primary_domain", primary_domain)
                    chat_span.set_attribute("secondary_domains", str(secondary_domains))
                    
                    print("\n========== ANALYSIS ==========")
                    print(analysis)
                    print("==============================")

                    # DOCUMENT MODE OVERRIDE

                    if has_documents:

                        print("\n========== DOCUMENT MODE ==========")
                        print("FORCING RAG ONLY")
                        print("===================================")

                        domains = ["rag"]

                    # NORMAL ROUTING

                    else:

                        domains = []

                        if primary_domain != "general":
                            domains.append(primary_domain)

                        domains.extend(secondary_domains)

                        domains = list(dict.fromkeys(domains))

                    # Set agents attribute on chat_request trace
                    chat_span.set_attribute("agents", str(domains))
                    chat_span.set_attribute("agent_count", len(domains))
                    router_span.set_attribute("routed_agents", str(domains))

                    print("\n========== DOMAINS ==========")
                    print(domains)
                    print("=============================")

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

                    # Set success attribute
                    chat_span.set_attribute("success", True)
                    
                    return {
                        "success": True,
                        "response": response,
                        "analysis": analysis,
                        "agents_used": ["groq"]
                    }

                agent_results = []
                successful_agents = []

                print("\n========== EXECUTING AGENTS ==========")
                print(domains)
                print("======================================")
                
                # EXECUTE AGENTS WITH INDIVIDUAL SPANS
                for domain in domains:

                    if domain not in self.agents:
                        continue

                    try:

                        agent = self.agents[domain]

                        context = {
                            "query": query,
                            "analysis": analysis,
                            "history": history,
                            "has_documents": has_documents,
                            "user_id": user_id
                        }

                        # Create individual span for each agent execution
                        # This will create spans like "agent.loan", "agent.calculator", etc.
                        with tracer.start_as_current_span(
                            f"agent.{domain}"
                        ) as agent_span:
                            
                            agent_span.set_attribute("agent", domain)
                            agent_span.set_attribute("agent_type", domain)
                            
                            result = await agent.process(
                                user_id,
                                query,
                                context
                            )
                            
                            agent_span.set_attribute("success", result.get("success", False))
                            agent_span.set_attribute(
                                "response_length",
                                len(result.get("message", ""))
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

                # Fallback

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

                    # Set success attribute
                    chat_span.set_attribute("success", True)

                    return {
                        "success": True,
                        "response": response,
                        "analysis": analysis,
                        "agents_used": ["groq"]
                    }

                # Single Agent

                if len(agent_results) == 1:

                    final_response = agent_results[0]

                # Multi Agent Synthesis
                else:
                    # Call synthesize_results - it will create its own Synthesizer span
                    final_response = await self.synthesize_results(
                        query,
                        agent_results
                    )

                self.save_message(
                    user_id,
                    "assistant",
                    final_response
                )

                # Set success attribute
                chat_span.set_attribute("success", True)

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
                
                # Set success attribute to False on error
                chat_span.set_attribute("success", False)
                chat_span.record_exception(e)

                return {
                    "success": False,
                    "response": (
                        "I encountered an error "
                        "processing your request."
                    ),
                    "agents_used": ["error"]
                }

    # GENERAL CHAT

    async def handle_general_query(
        self,
        query,
        history
    ):

        with tracer.start_as_current_span("General Chat") as span:
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

    # SYNTHESIS

    async def synthesize_results(
        self,
        query,
        agent_outputs
    ):

        with tracer.start_as_current_span("Synthesizer") as synthesis_span:
            
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

            synthesis_span.set_attribute("input_length", len(combined))
            synthesis_span.set_attribute("prompt_length", len(prompt))
            
            result = await self.llm.process(
                prompt,
                user_id="synthesizer"
            )
            
            synthesis_span.set_attribute("output_length", len(result))
            
            return result

    # DOCUMENT UPLOAD

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

    # STATUS

    def get_agent_status(self):

        return {
            name: True
            for name in self.agents
        }

    def get_available_agents(self):

        return list(
            self.agents.keys()
        )