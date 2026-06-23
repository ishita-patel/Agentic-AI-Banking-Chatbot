# backend/agents/document_processor.py
import os
import uuid
from typing import Dict, Any, List
import PyPDF2
import docx
import pandas as pd
from PIL import Image
import pytesseract
import io
import json

class DocumentProcessor:
    def __init__(self):
        self.supported_types = {
            '.pdf': self.process_pdf,
            '.docx': self.process_docx,
            '.doc': self.process_docx,
            '.xlsx': self.process_excel,
            '.xls': self.process_excel,
            '.csv': self.process_csv,
            '.txt': self.process_txt,
            '.png': self.process_image,
            '.jpg': self.process_image,
            '.jpeg': self.process_image
        }
    
    async def process(self, file_path: str, user_id: str) -> Dict[str, Any]:
        """Process any document based on file type"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext not in self.supported_types:
            return {
                "success": False,
                "message": f"Unsupported file type: {ext}"
            }
        
        try:
            result = await self.supported_types[ext](file_path)
            result["success"] = True
            result["user_id"] = user_id
            result["filename"] = os.path.basename(file_path)
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing document: {str(e)}"
            }
    
    async def process_pdf(self, file_path: str) -> Dict[str, Any]:
        """Process PDF files"""
        chunks = []
        metadata = {}
        
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            metadata = {
                "pages": len(reader.pages),
                "title": reader.metadata.title if reader.metadata else "",
                "author": reader.metadata.author if reader.metadata else ""
            }
            
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    chunks.append({
                        "text": text,
                        "page": i + 1,
                        "type": "text"
                    })
        
        return {
            "document_type": "pdf",
            "metadata": metadata,
            "chunks": chunks
        }
    
    async def process_docx(self, file_path: str) -> Dict[str, Any]:
        """Process Word documents"""
        chunks = []
        doc = docx.Document(file_path)
        
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        
        text = "\n".join(full_text)
        
        # Split into chunks
        chunks = self.chunk_text(text, 500)
        
        return {
            "document_type": "word",
            "metadata": {"paragraphs": len(full_text)},
            "chunks": chunks
        }
    
    async def process_excel(self, file_path: str) -> Dict[str, Any]:
        """Process Excel files"""
        chunks = []
        df = pd.read_excel(file_path)
        
        # Convert to text representation
        text = df.to_string()
        chunks = self.chunk_text(text, 500)
        
        return {
            "document_type": "excel",
            "metadata": {"rows": len(df), "columns": len(df.columns)},
            "chunks": chunks,
            "dataframe": df.to_dict()  # For structured data queries
        }
    
    async def process_csv(self, file_path: str) -> Dict[str, Any]:
        """Process CSV files"""
        chunks = []
        df = pd.read_csv(file_path)
        
        text = df.to_string()
        chunks = self.chunk_text(text, 500)
        
        return {
            "document_type": "csv",
            "metadata": {"rows": len(df), "columns": len(df.columns)},
            "chunks": chunks,
            "dataframe": df.to_dict()
        }
    
    async def process_txt(self, file_path: str) -> Dict[str, Any]:
        """Process text files"""
        with open(file_path, 'r') as file:
            text = file.read()
        
        chunks = self.chunk_text(text, 500)
        
        return {
            "document_type": "text",
            "metadata": {"length": len(text)},
            "chunks": chunks
        }
    
    async def process_image(self, file_path: str) -> Dict[str, Any]:
        """Process images with OCR"""
        image = Image.open(file_path)
        
        # Extract text using OCR
        text = pytesseract.image_to_string(image)
        
        chunks = self.chunk_text(text, 500)
        
        return {
            "document_type": "image",
            "metadata": {"size": image.size},
            "chunks": chunks
        }
    
    def chunk_text(self, text: str, max_chunk_size: int = 500) -> List[Dict[str, Any]]:
        """Split text into manageable chunks"""
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) > max_chunk_size and current_chunk:
                chunks.append({
                    "text": " ".join(current_chunk),
                    "type": "text"
                })
                current_chunk = []
                current_size = 0
            current_chunk.append(word)
            current_size += len(word)
        
        if current_chunk:
            chunks.append({
                "text": " ".join(current_chunk),
                "type": "text"
            })
        
        return chunks