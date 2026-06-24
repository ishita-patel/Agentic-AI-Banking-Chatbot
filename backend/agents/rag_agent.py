from backend.agents.base_agent import BaseAgent
from typing import Dict, Any, List
import chromadb
import uuid
import re
import time
from sentence_transformers import SentenceTransformer
from backend.agents.groq_agent import GroqAgent
from backend.agents.document_processor import DocumentProcessor


class RAGAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        
        self.capabilities = [
            "retrieve_knowledge",
            "document_qa",
            "financial_document_analysis"
        ]
        
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.user_collections = {}
        self.doc_processor = DocumentProcessor()
        self.llm = GroqAgent()
        
        # STRICT KEYWORDS FOR VALIDATION
        
        # MUST HAVE at least one of these to be considered financial
        self.required_financial_keywords = [
            "bank", "banking", "financial", "finance", 
            "account", "loan", "mortgage", "investment",
            "tax", "insurance", "salary", "statement",
            "transaction", "balance", "credit", "debit",
            "fixed deposit", "recurring deposit", "mutual fund",
            "stock", "bond", "portfolio", "retirement",
            "pension", "nps", "ppf", "cibil", "credit score"
        ]
        
        # Additional banking keywords (for scoring)
        self.financial_keywords = [
            "bank", "banking", "account", "savings", "checking", "current account",
            "loan", "mortgage", "emi", "credit", "debit", "statement", "transaction",
            "balance", "withdrawal", "deposit", "interest", "rate", "apr", "apy",
            "investment", "stock", "bond", "mutual fund", "etf", "portfolio",
            "tax", "taxation", "itr", "income tax", "gst", "tds", "pan", "aadhar",
            "insurance", "policy", "premium", "claim", "coverage", "deductible",
            "salary", "payroll", "compensation", "bonus", "reimbursement",
            "financial", "finance", "wealth", "retirement", "pension", "401k",
            "nps", "ppf", "fd", "rd", "fixed deposit", "recurring deposit",
            "credit score", "cibil", "credit report", "forex", "currency",
            "invoice", "bill", "payment", "receipt", "expense", "revenue",
            "profit", "loss", "balance sheet", "income statement", "cash flow",
            "strategy", "digital transformation", "roadmap", "initiative",
            "digital banking", "fintech", "financial technology"
        ]
        
        # Strong financial indicators (ACCEPT)
        self.strong_financial_indicators = [
            r'\b(?:bank|banking)\s+statement',
            r'\b(?:loan|mortgage)\s+(?:agreement|application)',
            r'\b(?:salary|payroll|compensation)\s+(?:slip|statement)',
            r'\b(?:tax|itr|income tax)\s+(?:return|document)',
            r'\b(?:investment|portfolio)\s+(?:report|summary)',
            r'\b(?:insurance)\s+(?:policy|document)',
            r'\b(?:credit|debit)\s+card\s+statement',
            r'\b(?:balance|income|profit/loss)\s+sheet',
            r'\b(?:financial|audit)\s+report',
            r'\baccount\s+statement',
            r'\b(?:bank|financial)\s+(?:strategy|transformation)',
            r'\b(?:digital)\s+(?:banking|finance)',
            r'\b(?:financial)\s+(?:technology|inclusion)'
        ]
        
        # REJECT - Non-financial indicators (REJECT immediately)
        self.reject_indicators = [
            "internship", "intern", "training", "employee", "handbook",
            "hr policy", "onboarding", "orientation", "company policy",
            "code of conduct", "workplace", "benefits", "pto", "leave policy",
            "resume", "interview", "career", "job description",
            "performance review", "appraisal", "promotion",
            "software engineering", "programming", "technical documentation",
            "api documentation", "developer guide", "code review",
            "sprint", "agile", "scrum", "jira", "github"
        ]
        
        # Document title patterns that indicate non-financial content
        self.reject_title_patterns = [
            r'internship\s+(?:program|handbook|guide)',
            r'employee\s+handbook',
            r'hr\s+policy',
            r'code\s+of\s+conduct',
            r'performance\s+review',
            r'job\s+description',
            r'career\s+guide',
            r'onboarding\s+guide',
            r'company\s+policy'
        ]

    # COLLECTION MANAGEMENT

    def get_user_collection(self, user_id: str):
        if user_id not in self.user_collections:
            collection_name = f"user_{user_id}_documents"
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"description": f"Documents for {user_id}"}
            )
            self.user_collections[user_id] = collection
        return self.user_collections[user_id]

    # CLEAR USER COLLECTION

    async def clear_user_collection(self, user_id: str) -> Dict[str, Any]:
        """Clear all documents for a user"""
        try:
            if user_id in self.user_collections:
                collection_name = f"user_{user_id}_documents"
                try:
                    self.chroma_client.delete_collection(collection_name)
                except:
                    pass
                del self.user_collections[user_id]
                return {
                    "success": True,
                    "message": "User documents cleared successfully."
                }
            else:
                collection_name = f"user_{user_id}_documents"
                try:
                    self.chroma_client.delete_collection(collection_name)
                    return {
                        "success": True,
                        "message": "User documents cleared successfully."
                    }
                except:
                    return {
                        "success": False,
                        "message": "No collection found for this user."
                    }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error clearing documents: {str(e)}"
            }

    # STRICT DOCUMENT CLASSIFICATION

    async def classify_document(self, document_text: str, filename: str = "") -> str:
        """
        STRICT classification - rejects ANY non-financial document
        """
        
        sample = document_text[:3000].lower()
        filename_lower = filename.lower()

        # STEP 1: Check filename for reject patterns

        reject_filename_patterns = [
            "internship", "handbook", "employee", "hr", 
            "career", "job", "training", "onboarding",
            "policy", "code of conduct", "resume"
        ]
        
        for pattern in reject_filename_patterns:
            if pattern in filename_lower:
                return "INVALID"
        
        # STEP 2: Check document header/title (first 500 chars)

        header = sample[:500]
        
        # Check for title patterns that indicate non-financial content
        for pattern in self.reject_title_patterns:
            if re.search(pattern, header, re.IGNORECASE):
                return "INVALID"
        
        # Check for obvious non-financial keywords in header
        for keyword in self.reject_indicators:
            if keyword in header:
                # If it appears prominently in the header, reject
                return "INVALID"

        # STEP 3: Check for required financial keywords

        has_required_keyword = any(
            keyword in sample 
            for keyword in self.required_financial_keywords
        )
        
        # If NO financial keywords found, reject immediately
        if not has_required_keyword:
            return "INVALID"
        
        # STEP 4: Count financial vs non-financial keywords

        financial_count = sum(
            1 for keyword in self.financial_keywords 
            if keyword in sample
        )
        
        non_financial_count = sum(
            1 for indicator in self.reject_indicators 
            if indicator in sample
        )
        
        # If non-financial count is higher, reject
        if non_financial_count > financial_count:
            return "INVALID"
        
        # Need at least 3 financial keywords to accept
        if financial_count < 3:
            return "INVALID"
        
        # STEP 5: Check for strong financial patterns

        for pattern in self.strong_financial_indicators:
            if re.search(pattern, sample, re.IGNORECASE):
                return "VALID"

        # STEP 6: LLM verification (strict)

        prompt = f"""
You are a STRICT banking document validator.

ACCEPT ONLY these document types:
- Bank statements
- Loan agreements / mortgage documents
- Salary slips / payroll documents
- Tax returns (ITR, Form 16)
- Investment reports (mutual funds, stocks, bonds)
- Insurance policies
- Credit card statements
- Financial statements (balance sheet, P&L)
- Banking strategy / digital transformation documents
- Financial reports / audit reports
- KYC documents
- Financial itinerary

REJECT ANY document that is about:
Any non-financial topic, that can be-
    - Internships, training programs
    - HR policies, employee handbooks
    - Company culture, general company info
    - Software engineering, programming
    - Technical documentation
    - Job descriptions, career guides


Document snippet:
{document_text[:1500]}

Return ONLY "VALID" or "INVALID".
"""

        result = await self.llm.process(prompt, user_id="document_classifier")
        result_clean = result.strip().upper()
        
        # STEP 7: Final safety check

        if result_clean == "VALID":
            # If document mentions internship/handbook/training, reject anyway
            final_reject_check = [
                "internship", "intern", "handbook", "training",
                "employee", "hr policy", "code of conduct",
                "career", "job description", "onboarding"
            ]
            
            for keyword in final_reject_check:
                if keyword in sample and keyword not in self.financial_keywords:
                    return "INVALID"
            
            # If non-financial count is still high, reject
            if non_financial_count >= 3 and financial_count < 5:
                return "INVALID"
        
        return result_clean

    # QUERY VALIDATION

    async def validate_query(self, query: str) -> str:
        """Smart query validation"""
        
        query_lower = query.lower()
        
        # Meta queries are allowed
        document_meta_phrases = [
            "what is this doc about", "what is this document",
            "summarise the doc", "summarize the doc",
            "document summary", "about this document",
            "tell me about this document", "what does this document contain",
            "summarise this doc", "summarize this doc",
            "summarise this document", "summarize this document",
            "what is this", "what's this", "tell me about this"
        ]
        
        is_meta_query = any(phrase in query_lower for phrase in document_meta_phrases)
        
        if is_meta_query:
            return "VALID"
        
        # Check for banking indicators
        banking_indicators = [
            "bank", "banking", "financial", "finance", "account",
            "investment", "loan", "mortgage", "insurance", "tax",
            "strategy", "digital", "transformation", "statement",
            "salary", "transaction", "balance", "credit", "debit",
            "savings", "interest", "emi", "cibil", "credit score", "portfolio"
        ]
        
        has_banking_indicator = any(
            indicator in query_lower 
            for indicator in banking_indicators
        )
        
        if not has_banking_indicator:
            # Check for non-financial queries
            non_financial_query_indicators = [
                "internship", "intern", "handbook", "hr policy", 
                "code of conduct", "onboarding", "orientation",
                "resume", "interview", "career", "job description",
                "performance review", "appraisal", "promotion",
                "software", "engineering", "programming", "code"
            ]
            
            if any(indicator in query_lower for indicator in non_financial_query_indicators):
                return "INVALID"
        
        return "VALID"

    # DOCUMENT UPLOAD WITH AUTOMATIC CLEANUP

    async def upload_document(
        self,
        user_id: str,
        file_path: str,
        clear_existing: bool = True
    ) -> Dict[str, Any]:
        """Upload a document with automatic cleanup"""
        
        # Clear existing documents
        if clear_existing:
            await self.clear_user_collection(user_id)
        
        processed = await self.doc_processor.process(file_path, user_id)

        if not processed["success"]:
            return processed

        chunks = processed.get("chunks", [])
        if not chunks:
            return {
                "success": False,
                "message": "No text extracted from the document."
            }

        # Get full text for classification
        full_text = "\n".join([chunk["text"] for chunk in chunks[:50]])
        sample_text = full_text[:3000]
        filename = processed.get("filename", "")

        # STRICT classification
        classification = await self.classify_document(sample_text, filename)

        if classification != "VALID":
            return {
                "success": False,
                "message": (
                    "  Document REJECTED\n\n"
                    "This document does not appear to be a banking or financial document.\n\n"
                    "  Your previous financial document (if any) has been preserved.\n\n"
                    "  ACCEPTED document types:\n"
                    "• Bank statements\n"
                    "• Loan agreements\n"
                    "• Salary slips\n"
                    "• Tax returns\n"
                    "• Investment reports\n"
                    "• Insurance policies\n"
                    "• Banking strategy documents\n"
                    "• Financial reports\n\n"
                    "  REJECTED document types:\n"
                    "• Internship handbooks\n"
                    "• HR policies\n"
                    "• Employee handbooks\n"
                    "• Technical documentation\n"
                    "• Career guides\n"
                    "• Any non-financial content"
                )
            }

        # Store documents
        collection = self.get_user_collection(user_id)

        for i, chunk in enumerate(chunks):
            embedding = self.embedding_model.encode(chunk["text"]).tolist()
            doc_id = f"user_{user_id}_{uuid.uuid4().hex[:8]}"
            
            collection.add(
                documents=[chunk["text"]],
                embeddings=[embedding],
                ids=[doc_id],
                metadatas=[{
                    "chunk_index": i,
                    "source_file": filename,
                    "page": chunk.get("page", 0),
                    "document_type": "financial",
                    "upload_timestamp": int(time.time())
                }]
            )

        return {
            "success": True,
            "message": f"Financial document processed successfully. {len(chunks)} chunks stored.",
            "data": {
                "chunks": len(chunks),
                "filename": filename
            }
        }

    # RETRIEVAL

    async def retrieve_from_user_docs(
        self,
        query: str,
        user_id: str,
        top_k: int = 5
    ) -> List[str]:
        try:
            collection = self.get_user_collection(user_id)
            query_embedding = self.embedding_model.encode(query).tolist()
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )

            if results and results.get("documents"):
                return results["documents"][0]
            return []
        except Exception:
            return []

    # MAIN PROCESS

    async def process(
        self,
        user_id: str,
        task: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        query = context.get("query", task) if context else task
        query_lower = query.lower()
        
        # Check if meta query
        meta_phrases = [
            "summarise this doc", "summarize this doc",
            "summarise this document", "summarize this document",
            "what is this doc about", "what is this document",
            "document summary", "about this document",
            "tell me about this document", "what does this document contain",
            "what is this", "what's this", "tell me about this"
        ]
        
        is_meta_query = any(phrase in query_lower for phrase in meta_phrases)
        
        # Validate query
        query_valid = await self.validate_query(query)
        
        if query_valid != "VALID":
            if is_meta_query:
                pass  
            else:
                return {
                    "success": True,
                    "message": (
                        "I can only assist with banking, loans, savings, investments, "
                        "taxation, insurance, personal finance, and questions about "
                        "your uploaded financial documents."
                    )
                }
        
        # Check for documents
        try:
            collection = self.get_user_collection(user_id)
            test_query = "banking finance"
            test_embedding = self.embedding_model.encode(test_query).tolist()
            test_results = collection.query(
                query_embeddings=[test_embedding],
                n_results=1
            )
            
            if not test_results.get("documents") or not test_results["documents"][0]:
                return {
                    "success": True,
                    "message": (
                        "Invalid financial documents found.\n\n"
                        "Please upload relavent financial document to get started."
                    )
                }
        except Exception:
            return {
                "success": True,
                "message": (
                    "Please upload a financial document first."
                )
            }
        
        # Retrieve from documents
        user_docs = await self.retrieve_from_user_docs(query, user_id)
        
        if not user_docs:
            if is_meta_query:
                generic_queries = [
                    "summary overview",
                    "document content",
                    "main topics"
                ]
                
                for generic_query in generic_queries:
                    user_docs = await self.retrieve_from_user_docs(generic_query, user_id)
                    if user_docs:
                        break
                
                if not user_docs:
                    return {
                        "success": True,
                        "message": (
                            "I found your document but couldn't extract a summary. "
                            "Please try asking a specific question about the content."
                        )
                    }
            else:
                return {
                    "success": True,
                    "message": (
                        "I couldn't find relevant information. Please try rephrasing your question."
                    )
                }
        
        # Generate response
        context_text = "\n\n".join(user_docs)
        
        prompt = f"""
You are Aiko Bank's Financial Document Assistant.

User Question: {query}

Retrieved Context from Financial Documents:
{context_text}

Instructions:
1. Answer ONLY using the retrieved context
2. If information is missing, clearly say so
3. Do not hallucinate
4. Keep responses professional
5. Mention the answer comes from uploaded documents
6. Only answer banking/financial related questions
"""

        response = await self.llm.process(prompt, user_id=user_id)

        return {
            "success": True,
            "message": response,
            "data": {
                "documents_used": True,
                "chunks_retrieved": len(user_docs)
            }
        }

    # HELPER METHODS

    async def has_financial_documents(self, user_id: str) -> bool:
        """Check if user has uploaded financial documents"""
        try:
            collection = self.get_user_collection(user_id)
            test_query = "banking finance"
            test_embedding = self.embedding_model.encode(test_query).tolist()
            test_results = collection.query(
                query_embeddings=[test_embedding],
                n_results=1
            )
            return bool(test_results.get("documents") and test_results["documents"][0])
        except Exception:
            return False