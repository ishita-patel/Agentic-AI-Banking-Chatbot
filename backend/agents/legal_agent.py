# backend/agents/legal_agent.py
from backend.agents.base_agent import BaseAgent
from typing import Dict, Any
import json

class LegalAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.capabilities = ["legal_advice", "contract_analysis", "legal_query", "document_review"]
    
    async def process(self, user_id: str, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        query = context.get("query", task) if context else task
        has_document = context.get("has_documents", False) if context else False
        
        # Determine legal domain
        legal_domain = self.detect_legal_domain(query)
        
        system_prompt = f"""
        You are a senior legal advisor at Aiko Bank's Legal Division with 15 years of experience.
        
        Legal Domain: {legal_domain}
        Has Uploaded Document: {has_document}
        User Query: {query}
        
        Follow this professional legal analysis framework:
        
        Step 1 - Legal Context Analysis:
        - Identify applicable laws and regulations
        - Determine legal nature of the issue
        - Assess legal implications for the user
        
        Step 2 - Rights and Obligations:
        - List user's legal rights in this situation
        - List user's legal obligations
        - Identify potential legal risks
        
        Step 3 - Documentation Requirements:
        - List required documents
        - Explain legal formalities
        - Mention registration/notarization needs
        - Provide document templates if applicable
        
        Step 4 - Legal Precedents:
        - Reference relevant case laws
        - Share industry best practices
        - Explain standard legal procedures
        
        Step 5 - Recommended Actions:
        - Provide step-by-step guidance
        - Suggest timeline for actions
        - Recommend when to consult a practicing lawyer
        
        Step 6 - Dispute Resolution:
        - Negotiation options
        - Mediation/arbitration process
        - Legal remedies available
        
        Format response professionally:
        
        [LEGAL CONTEXT]
        
        [RIGHTS AND OBLIGATIONS]
        
        [DOCUMENTATION REQUIRED]
        
        [LEGAL PRECEDENTS]
        
        [RECOMMENDED ACTIONS]
        
        [DISPUTE RESOLUTION]
        
        [DISCLAIMER]
        "This is general legal information, not legal advice. Please consult a qualified lawyer for specific legal advice."
        
        [WHEN TO CONSULT A LAWYER]
        
        [USEFUL RESOURCES]
        """
        
        response = await self.get_llm_response(system_prompt, query)
        
        return {
            "success": True,
            "message": response,
            "data": {
                "agent": "legal_agent",
                "llm_used": True,
                "legal_domain": legal_domain,
                "has_document": has_document
            }
        }
    
    def detect_legal_domain(self, query: str) -> str:
        query_lower = query.lower()
        
        if "rental" in query_lower or "tenant" in query_lower or "lease" in query_lower:
            return "Property/Rental Agreement"
        elif "will" in query_lower or "inheritance" in query_lower or "estate" in query_lower:
            return "Wills and Inheritance"
        elif "contract" in query_lower or "agreement" in query_lower:
            return "Contract/Agreement Review"
        elif "employment" in query_lower or "labor" in query_lower or "employee" in query_lower:
            return "Employment/Labor Law"
        elif "consumer" in query_lower or "customer" in query_lower:
            return "Consumer Rights"
        elif "business" in query_lower or "company" in query_lower:
            return "Business/Commercial Law"
        else:
            return "General Legal Query"