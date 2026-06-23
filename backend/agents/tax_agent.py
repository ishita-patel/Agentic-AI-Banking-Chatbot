# backend/agents/tax_agent.py
from backend.agents.base_agent import BaseAgent
from typing import Dict, Any
import json

class TaxAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.capabilities = ["tax_advice", "itr_help", "tax_saving", "deduction_planning"]
    
    async def process(self, user_id: str, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        query = context.get("query", task) if context else task
        query_lower = query.lower()
        
        # Determine tax context
        is_itr = "itr" in query_lower or "income tax" in query_lower or "filing" in query_lower
        is_saving = "saving" in query_lower or "deduction" in query_lower or "80c" in query_lower
        is_calculation = "calculate" in query_lower or "tax on" in query_lower
        
        system_prompt = f"""
        You are a senior chartered accountant at Aiko Bank's Taxation Division with 18 years of experience.
        
        User Query: {query}
        
        Tax Context:
        - ITR Filing: {is_itr}
        - Tax Saving: {is_saving}
        - Tax Calculation: {is_calculation}
        
        Follow this professional tax advisory framework:
        
        Step 1 - Tax Applicability:
        - Determine applicable tax regime (Old vs New)
        - Identify tax slab based on estimated income
        - Calculate tax liability (if income provided)
        - Explain the differences between regimes
        
        Step 2 - Deduction Opportunities:
        
        {self.get_deduction_options()}
        
        Step 3 - Tax Saving Recommendations:
        - Specific actionable recommendations
        - Investment suggestions with amounts
        - Timing considerations (before March 31)
        - Annual planning strategy
        
        Step 4 - ITR Filing Guidance:
        - Determine appropriate ITR form
        - List required documents
        - Explain filing process step-by-step
        - Mention deadlines and consequences of delay
        
        Step 5 - Compliance and Penalties:
        - Late filing penalties
        - Interest under Sections 234A, 234B, 234C
        - Consequences of non-compliance
        - Audit requirements if applicable
        
        Step 6 - Long-term Tax Planning:
        - 5-year tax planning strategy
        - Investment roadmap
        - Retirement planning tax implications
        
        Format response professionally:
        
        [TAX ASSESSMENT]
        
        [DEDUCTION OPPORTUNITIES]
        
        [TAX SAVING RECOMMENDATIONS]
        
        [FILING REQUIREMENTS]
        
        [COMPLIANCE GUIDANCE]
        
        [LONG-TERM PLANNING]
        
        [NEXT STEPS]
        
        [DISCLAIMER]
        "This is general tax guidance. Please consult a chartered accountant for your specific situation."
        """
        
        response = await self.get_llm_response(system_prompt, query)
        
        return {
            "success": True,
            "message": response,
            "data": {
                "agent": "tax_agent",
                "llm_used": True,
                "tax_context": {
                    "is_itr": is_itr,
                    "is_saving": is_saving,
                    "is_calculation": is_calculation
                }
            }
        }
    
    def get_deduction_options(self):
        return """
        Tax Deduction Opportunities (Section 80C):
        
        1. Public Provident Fund (PPF):
           - Max Deduction: ₹1,50,000
           - Lock-in: 15 years
           - Interest Rate: 7.1% p.a.
           - Best for: Risk-free returns, long-term wealth
        
        2. ELSS Mutual Funds:
           - Max Deduction: ₹1,50,000
           - Lock-in: 3 years
           - Returns: 12-15% p.a.
           - Best for: Higher returns, short lock-in
        
        3. Life Insurance Premium:
           - Max Deduction: ₹1,50,000
           - Lock-in: Policy term
           - Best for: Family protection + tax saving
        
        4. National Pension System (NPS):
           - Max Deduction: ₹1,50,000 + ₹50,000 (additional)
           - Lock-in: Until retirement
           - Returns: 8-10% p.a.
           - Best for: Retirement planning, additional deduction
        
        5. Home Loan Principal:
           - Max Deduction: ₹1,50,000
           - Lock-in: Loan tenure
           - Best for: Home buyers, property owners
        
        6. School Tuition Fees:
           - Max Deduction: ₹1,50,000
           - Per child (max 2 children)
           - Best for: Parents, education planning
        
        Additional Deductions:
        
        7. Health Insurance (Section 80D):
           - Self & Family: Up to ₹25,000
           - Senior Citizens: Up to ₹50,000
           - Best for: Health coverage + tax saving
        
        8. Home Loan Interest (Section 24):
           - Max Deduction: ₹2,00,000 (self-occupied)
           - Best for: Home loan borrowers
        
        9. Donations (Section 80G):
           - 50% or 100% of donated amount
           - Must donate to approved charities
           - Best for: Social responsibility + tax saving
        """