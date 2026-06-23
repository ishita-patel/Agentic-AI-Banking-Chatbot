from backend.agents.base_agent import BaseAgent
from typing import Dict, Any, List
import chromadb
from sentence_transformers import SentenceTransformer
from backend.agents.groq_agent import GroqAgent
from backend.agents.document_processor import DocumentProcessor
import uuid
import os

class RAGAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.capabilities = ["retrieve_knowledge", "process_query", "answer_general_query"]
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        
        # NO FIXED KNOWLEDGE BASE - Only user documents
        self.user_collections = {}
        
        # Initialize document processor
        self.doc_processor = DocumentProcessor()
        
        # Initialize LLM
        self.llm = GroqAgent()
    
    def get_user_collection(self, user_id: str):
        """Get or create user-specific collection for their documents"""
        if user_id not in self.user_collections:
            collection_name = f"user_{user_id}_documents"
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"description": f"Documents for user {user_id}"}
            )
            self.user_collections[user_id] = collection
        return self.user_collections[user_id]
    
    async def upload_document(self, user_id: str, file_path: str) -> Dict[str, Any]:
        """Upload and process a document for a user"""
        processed = await self.doc_processor.process(file_path, user_id)
        
        if not processed["success"]:
            return processed
        
        chunks = processed.get("chunks", [])
        collection = self.get_user_collection(user_id)
        
        for i, chunk in enumerate(chunks):
            embedding = self.embedding_model.encode(chunk["text"]).tolist()
            doc_id = f"user_{user_id}_{uuid.uuid4().hex[:8]}"
            
            collection.add(
                documents=[chunk["text"]],
                embeddings=[embedding],
                ids=[doc_id],
                metadatas=[{
                    "source_file": processed.get("filename", "unknown"),
                    "chunk_index": i,
                    "page": chunk.get("page", 0),
                    "document_type": processed.get("document_type", "unknown")
                }]
            )
        
        return {
            "success": True,
            "message": f"Document processed and stored: {len(chunks)} chunks",
            "data": {
                "filename": processed.get("filename"),
                "document_type": processed.get("document_type"),
                "chunks": len(chunks)
            }
        }
    
    async def retrieve_from_user_docs(self, query: str, user_id: str, top_k: int = 5) -> List[str]:
        """Retrieve relevant information ONLY from user's uploaded documents"""
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
    
    async def process(self, user_id: str, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        query = context.get("query", task) if context else task
        
        # Get sources for this query
        sources = context.get("sources", {}) if context else {}
        
        # Build context from all available sources
        context_parts = []
        
        # 1. User documents (if any)
        user_docs = await self.retrieve_from_user_docs(query, user_id)
        if user_docs:
            context_parts.append("From your uploaded documents:\n" + "\n".join(user_docs))
        
        # 2. User account data
        if sources.get("user_data"):
            context_parts.append(f"User Financial Data:\n{sources['user_data']}")
        
        # 3. Web search results
        if sources.get("web_search"):
            context_parts.append(f"Web Search Results:\n{sources['web_search']}")
        
        # 4. LLM will use its own knowledge for general questions
        
        context_text = "\n\n".join(context_parts) if context_parts else "No specific data found. Use general knowledge."
        
        prompt = f"""
        User Query: {query}
        
        Available Context:
        {context_text}
        
        Instructions:
        1. If context has information, use it to answer
        2. If user documents were used, mention that
        3. If no specific information is found, use your knowledge
        4. Provide accurate, helpful responses
        """
        
        response = await self.llm.process(prompt, user_id)
        
        return {
            "success": True,
            "message": response,
            "data": {
                "sources_used": {
                    "user_documents": bool(user_docs),
                    "user_data": bool(sources.get("user_data")),
                    "web_search": bool(sources.get("web_search"))
                }
            }
        }