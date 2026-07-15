from typing import Dict, Any, List, Optional
from opentelemetry import trace
import asyncio

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
from backend.judge.llm_judge import LLMJudge
from backend.security.kill_switch import KillSwitch


tracer = trace.get_tracer(__name__)

class Orchestrator:

    def __init__(self):

        self.query_analyzer = QueryAnalyzer()
        self.llm = GroqAgent()
        self.agents = self.initialize_agents()
        self.conversation_memory = {}
        self.judge = LLMJudge()
        self.judge_enabled = True  # Can be disabled via config

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

    # JUDGE HELPER

    async def evaluate_response(
        self,
        query: str,
        response: str,
        analysis: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a response using the LLM Judge.
        Runs asynchronously and can be called in the background.
        """
        if not self.judge_enabled:
            return {}

        try:
            # LLMJudge.evaluate() is now async - use await
            judge_result = await self.judge.evaluate(
                query=query,
                response=response,
                context=str(analysis)
            )
            
            return judge_result
            
        except Exception as e:
            print(f"Judge evaluation failed: {e}")
            # Return a default dictionary to avoid None causing Pydantic validation errors
            return {
                "relevance": 0.0,
                "helpful": 0.0,
                "grounded": 0.0,
                "safety": 0.0,
                "hallucination": True,
                "confidence": 0.0,
                "reason": f"Evaluation failed: {str(e)}"
            }

    async def save_judge_result(
        self,
        user_id: str,
        query: str,
        judge_result: Dict[str, Any]
    ):
        """
        Persist judge results for analytics.
        Override this method to save to your database.
        """
        # TODO: Save to MongoDB, PostgreSQL, or Langfuse
        # Example:
        # await db.judge_results.insert_one({
        #     "user_id": user_id,
        #     "query": query,
        #     "timestamp": datetime.utcnow(),
        #     "judge_result": judge_result
        # })
        pass

    # MAIN PROCESSOR

    async def process(
        self,
        user_id: str,
        query: str,
        has_documents: bool = False,
        skip_judge: bool = False
    ) -> Dict[str, Any]:

        # CREATE CHAT_REQUEST TRACE AROUND THE ENTIRE PROCESS
        with tracer.start_as_current_span("chat_request") as chat_span:
            
            # Set initial attributes
            chat_span.set_attribute("user_id", user_id)
            chat_span.set_attribute("query_length", len(query))
            chat_span.set_attribute("has_documents", has_documents)
            chat_span.add_event("Chat request started")
            
            print("\n===== BEFORE KILL SWITCH =====")
            print(query)
            print("==============================")

            try:
                # KILL SWITCH - Check for malicious/unsafe queries
                safe, reason = KillSwitch.check(query)

                print("SAFE =", safe)
                print("REASON =", reason)

                print("\n========== KILL SWITCH ==========")
                print("QUERY:", query)
                print("SAFE:", safe)
                print("REASON:", reason)
                print("=================================\n")
                
                if not safe:
                    # Log the blocked request
                    print(f"⚠️ KILL SWITCH TRIGGERED - User: {user_id}, Reason: {reason}")
                    
                    # Set attributes for blocked request
                    chat_span.set_attribute("blocked", True)
                    chat_span.set_attribute("block_reason", reason)
                    chat_span.set_attribute("success", False)
                    chat_span.set_attribute("block_type", "kill_switch")  # NEW
                    chat_span.set_attribute("matched_pattern", reason)    # NEW
                    chat_span.add_event("Request blocked by kill switch")
                    
                    # Return blocked response
                    return {
                        "success": False,
                        "response": "I'm here to assist with banking-related requests and other supported tasks, but I can't process requests that attempt to change or bypass my operating instructions.",
                        "blocked": True,
                        "reason": reason,
                        "agents_used": []
                    }
                
                self.save_message(
                    user_id,
                    "user",
                    query
                )

                history = self.get_history(user_id)

                # ROUTER SPAN - Query Analysis and Domain Routing
                with tracer.start_as_current_span("Router") as router_span:
                    
                    router_span.set_attribute("user_id", user_id)
                    router_span.set_attribute("query_length", len(query))
                    router_span.set_attribute("has_documents", has_documents)
                    router_span.add_event("Routing analysis started")
                    
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
                    router_span.set_attribute("intent", analysis.get("intent", "unknown"))
                    router_span.set_attribute("confidence", analysis.get("confidence", 0.0))
                    
                    # Set chat_request attributes
                    chat_span.set_attribute("primary_domain", primary_domain)
                    chat_span.set_attribute("secondary_domains", str(secondary_domains))
                    
                    print("\n========== ANALYSIS ==========")
                    print(analysis)
                    print("==============================")

                    # Check if out of scope first
                    if primary_domain == "out_of_scope":
                        chat_span.set_attribute("blocked", True)
                        chat_span.set_attribute("block_reason", "out_of_scope")
                        chat_span.set_attribute("block_type", "scope_guard")  # NEW
                        chat_span.add_event("Request blocked - out of scope")
                        
                        return {
                            "success": False,
                            "response": (
                                "I'm Aiko Bank's AI assistant. "
                                "I can help with banking, loans, investments, travel, taxes, legal information, financial calculations, uploaded documents, and financial news. "
                                "I can't answer unrelated general knowledge questions."
                            ),
                            "analysis": analysis,
                            "agents_used": [],
                            "judge": {}
                        }

                    # DOCUMENT MODE OVERRIDE
                    if has_documents:
                        print("\n========== DOCUMENT MODE ==========")
                        print("FORCING RAG ONLY")
                        print("===================================")
                        domains = ["rag"]

                    # NORMAL ROUTING
                    else:
                        domains = []

                        # CHANGED: Check for out_of_scope instead of general
                        if primary_domain != "out_of_scope":
                            domains.append(primary_domain)

                        domains.extend(secondary_domains)
                        domains = list(dict.fromkeys(domains))

                    # Set agents attribute on chat_request trace
                    chat_span.set_attribute("agents", str(domains))
                    chat_span.set_attribute("agent_count", len(domains))
                    chat_span.set_attribute("routing_confidence", analysis.get("confidence", 0.0))  # NEW
                    router_span.set_attribute("routed_agents", str(domains))
                    router_span.add_event("Routing analysis completed")

                    print("\n========== DOMAINS ==========")
                    print(domains)
                    print("=============================")

                # CHANGED: No more fallback to general Groq
                if not domains:
                    chat_span.set_attribute("blocked", True)
                    chat_span.set_attribute("block_reason", "no_domains_found")
                    chat_span.set_attribute("block_type", "scope_guard")  # NEW
                    chat_span.set_attribute("routing_confidence", analysis.get("confidence", 0.0))  # NEW
                    chat_span.add_event("Request blocked - no domains found")
                    
                    return {
                        "success": False,
                        "response": (
                            "I'm Aiko Bank's AI assistant. "
                            "I can help with banking, loans, investments, travel, taxes, legal information, financial calculations, uploaded documents, and financial news. "
                            "I can't answer unrelated general knowledge questions."
                        ),
                        "analysis": analysis,
                        "agents_used": [],
                        "judge": {}
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
                        with tracer.start_as_current_span(
                            f"agent.{domain}"
                        ) as agent_span:
                            
                            # Set agent identification attributes
                            agent_span.set_attribute("agent_name", domain)
                            agent_span.set_attribute("agent_type", domain)
                            agent_span.set_attribute("user_id", user_id)
                            agent_span.set_attribute("query_length", len(query))
                            
                            # Determine if agent uses LLM based on type
                            # Deterministic agents that don't use LLM
                            deterministic_agents = ["calculator", "balance", "statement"]
                            uses_llm = domain not in deterministic_agents
                            agent_span.set_attribute("llm_used", uses_llm)
                            
                            # Add start event
                            agent_span.add_event("Agent execution started")
                            
                            # Execute the agent
                            result = await agent.process(
                                user_id,
                                query,
                                context
                            )
                            
                            # Set success/failure
                            success = result.get("success", False)
                            agent_span.set_attribute("success", success)
                            agent_span.set_attribute("status", "success" if success else "failure")
                            
                            # Add response length if available
                            if "message" in result:
                                agent_span.set_attribute(
                                    "response_length",
                                    len(result.get("message", ""))
                                )
                            
                            # Add completion event
                            agent_span.add_event("Agent execution completed")
                            
                            # Record any errors if they occurred
                            if not success and "error" in result:
                                agent_span.record_exception(
                                    Exception(result.get("error", "Unknown error"))
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
                        
                        # Handle agent exception with span
                        print(f"{domain} agent error: {e}")
                        
                        # Try to get current span to record exception
                        current_span = trace.get_current_span()
                        if current_span:
                            current_span.set_attribute("status", "failure")
                            current_span.record_exception(e)
                            current_span.add_event("Agent execution failed")

                # CHANGED: No more fallback to general Groq
                if not agent_results:
                    chat_span.set_attribute("success", False)
                    chat_span.set_attribute("blocked", True)
                    chat_span.set_attribute("block_reason", "all_agents_failed")
                    chat_span.set_attribute("block_type", "scope_guard")  # NEW
                    chat_span.set_attribute("routing_confidence", analysis.get("confidence", 0.0))  # NEW
                    chat_span.add_event("Request failed - all agents failed")
                    
                    return {
                        "success": False,
                        "response": (
                            "I'm Aiko Bank's AI assistant. "
                            "I can help with banking, loans, investments, travel, taxes, legal information, financial calculations, uploaded documents, and financial news. "
                            "I can't answer unrelated general knowledge questions."
                        ),
                        "analysis": analysis,
                        "agents_used": [],
                        "judge": {}
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
                chat_span.set_attribute("successful_agents", str(successful_agents))
                chat_span.set_attribute("primary_agent", successful_agents[0] if successful_agents else "groq")
                chat_span.set_attribute("routing_confidence", analysis.get("confidence", 0.0))  # NEW
                chat_span.add_event("Chat request completed")

                result = {
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
                
                # Run judge (synchronously but returns immediately)
                if not skip_judge:
                    judge_result = await self.evaluate_response(
                        query=query,
                        response=final_response,
                        analysis=analysis,
                        user_id=user_id
                    )
                    if judge_result:
                        result["judge"] = judge_result

                return result

            except Exception as e:

                print(f"Orchestrator Error: {e}")
                
                # Set success attribute to False on error
                chat_span.set_attribute("success", False)
                chat_span.record_exception(e)
                chat_span.add_event("Chat request failed")

                error_response = (
                    "I encountered an error "
                    "processing your request."
                )
                
                result = {
                    "success": False,
                    "response": error_response,
                    "agents_used": ["error"]
                }
                
                # Skip judge for errors - no useful information
                # But we could log the error for monitoring
                
                return result

    # GENERAL CHAT - REMOVED/UNUSED
    # The handle_general_query method is no longer used
    # Keeping it for potential future use but it won't be called

    # SYNTHESIS

    async def synthesize_results(
        self,
        query,
        agent_outputs
    ):

        with tracer.start_as_current_span("Synthesizer") as synthesis_span:
            
            synthesis_span.set_attribute("num_agent_outputs", len(agent_outputs))
            synthesis_span.set_attribute("llm_used", True)
            synthesis_span.add_event("Synthesis started")
            
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
            synthesis_span.set_attribute("success", True)
            synthesis_span.add_event("Synthesis completed")
            
            return result

    # DOCUMENT UPLOAD

    async def upload_document(
        self,
        user_id,
        file_path
    ):

        with tracer.start_as_current_span("Document Upload") as span:
            
            span.set_attribute("user_id", user_id)
            span.set_attribute("file_path", file_path)
            span.add_event("Document upload started")
            
            rag_agent = self.agents.get("rag")

            if not rag_agent:
                
                span.set_attribute("success", False)
                span.add_event("Document upload failed - RAG unavailable")
                
                return {
                    "success": False,
                    "message": "RAG unavailable"
                }

            result = await rag_agent.upload_document(
                user_id,
                file_path
            )
            
            span.set_attribute("success", result.get("success", False))
            span.add_event("Document upload completed")
            
            return result

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