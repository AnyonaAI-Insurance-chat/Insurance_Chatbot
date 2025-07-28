import os
import uuid
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import PyPDF2
import docify
from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InsurancePolicyEmbedder:
    def __init__(self, 
                 db_path: str = "./chroma_db",
                 collection_name: str = "insurance_policies",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        """
        Initialize the Insurance Policy Embedder
        
        Args:
            db_path: Path to store ChromaDB
            collection_name: Name of the ChromaDB collection
            embedding_model: SentenceTransformer model name
            chunk_size: Size of text chunks for embedding
            chunk_overlap: Overlap between chunks
        """
        self.db_path = db_path
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Initialize ChromaDB
        self.client = self._initialize_chromadb()
        self.collection = self._get_or_create_collection()
        
    def _initialize_chromadb(self):
        """Initialize ChromaDB client"""
        logger.info(f"Initializing ChromaDB at {self.db_path}")
        return chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)
        )
    
    def _get_or_create_collection(self):
        """Get or create ChromaDB collection"""
        try:
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Found existing collection: {self.collection_name}")
        except ValueError:
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Insurance policy documents"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
        return collection
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF using PyPDF2
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        logger.info(f"Extracting text from: {pdf_path}")
        text = ""
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}"
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            raise
        
        return text
    
    def process_with_docify(self, text: str, document_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process text with Docify for better structure
        Note: This is a placeholder - replace with actual Docify implementation
        
        Args:
            text: Raw text content
            document_metadata: Metadata about the document
            
        Returns:
            List of processed text chunks with metadata
        """
        # Placeholder for Docify processing
        # Replace this with actual Docify API calls or library usage
        
        # For now, we'll simulate structured processing
        sections = self._simple_section_extraction(text)
        
        processed_chunks = []
        for section in sections:
            processed_chunks.append({
                'content': section['content'],
                'metadata': {
                    **document_metadata,
                    'section_type': section.get('type', 'general'),
                    'section_title': section.get('title', ''),
                    'processed_at': datetime.now().isoformat()
                }
            })
        
        return processed_chunks
    
    def _simple_section_extraction(self, text: str) -> List[Dict[str, Any]]:
        """
        Simple section extraction (replace with Docify)
        """
        # Split text into manageable chunks
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            # Try to identify section type based on keywords
            section_type = self._identify_section_type(chunk_text)
            
            chunks.append({
                'content': chunk_text,
                'type': section_type,
                'title': self._extract_title(chunk_text)
            })
        
        return chunks
    
    def _identify_section_type(self, text: str) -> str:
        """Identify section type based on keywords"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['coverage', 'benefit', 'policy limit']):
            return 'coverage'
        elif any(keyword in text_lower for keyword in ['claim', 'procedure', 'process']):
            return 'claims'
        elif any(keyword in text_lower for keyword in ['premium', 'payment', 'cost']):
            return 'pricing'
        elif any(keyword in text_lower for keyword in ['exclusion', 'not covered', 'exception']):
            return 'exclusions'
        else:
            return 'general'
    
    def _extract_title(self, text: str) -> str:
        """Extract potential title from text chunk"""
        lines = text.split('\n')
        for line in lines[:3]:  # Check first 3 lines
            line = line.strip()
            if line and len(line) < 100 and line.isupper():
                return line
        return lines[0][:50] + "..." if lines[0] else ""
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Create embeddings for text chunks
        
        Args:
            texts: List of text chunks
            
        Returns:
            Numpy array of embeddings
        """
        logger.info(f"Creating embeddings for {len(texts)} text chunks")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        return embeddings
    
    def save_to_chromadb(self, 
                        chunks: List[Dict[str, Any]], 
                        embeddings: np.ndarray,
                        document_id: str) -> None:
        """
        Save embeddings and metadata to ChromaDB
        
        Args:
            chunks: List of text chunks with metadata
            embeddings: Corresponding embeddings
            document_id: Unique document identifier
        """
        logger.info(f"Saving {len(chunks)} chunks to ChromaDB")
        
        # Prepare data for ChromaDB
        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        documents = [chunk['content'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )
        
        logger.info(f"Successfully saved {len(chunks)} chunks with document_id: {document_id}")
    
    def process_pdf(self, pdf_path: str, policy_metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Complete pipeline to process a PDF and save to ChromaDB
        
        Args:
            pdf_path: Path to PDF file
            policy_metadata: Additional metadata about the policy
            
        Returns:
            Document ID
        """
        if policy_metadata is None:
            policy_metadata = {}
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        
        # Prepare document metadata
        document_metadata = {
            'document_id': document_id,
            'source_file': os.path.basename(pdf_path),
            'file_path': pdf_path,
            'document_type': 'insurance_policy',
            'processed_at': datetime.now().isoformat(),
            **policy_metadata
        }
        
        # Process with Docify (or our placeholder)
        chunks = self.process_with_docify(text, document_metadata)
        
        # Create embeddings
        texts = [chunk['content'] for chunk in chunks]
        embeddings = self.create_embeddings(texts)
        
        # Save to ChromaDB
        self.save_to_chromadb(chunks, embeddings, document_id)
        
        return document_id
    
    def process_multiple_pdfs(self, pdf_directory: str, metadata_file: Optional[str] = None) -> List[str]:
        """
        Process multiple PDFs from a directory
        
        Args:
            pdf_directory: Directory containing PDF files
            metadata_file: Optional JSON file with metadata for each PDF
            
        Returns:
            List of document IDs
        """
        # Load metadata if provided
        metadata_map = {}
        if metadata_file and os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata_map = json.load(f)
        
        pdf_files = list(Path(pdf_directory).glob("*.pdf"))
        document_ids = []
        
        for pdf_path in pdf_files:
            try:
                filename = pdf_path.name
                file_metadata = metadata_map.get(filename, {})
                
                logger.info(f"Processing: {filename}")
                doc_id = self.process_pdf(str(pdf_path), file_metadata)
                document_ids.append(doc_id)
                
            except Exception as e:
                logger.error(f"Error processing {pdf_path}: {e}")
                continue
        
        return document_ids
    
    def search_similar(self, 
                      query: str, 
                      n_results: int = 5,
                      section_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for similar content in the database
        
        Args:
            query: Search query
            n_results: Number of results to return
            section_type: Optional filter by section type
            
        Returns:
            Search results with documents and metadata
        """
        # Create query embedding
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Prepare where clause for filtering
        where_clause = None
        if section_type:
            where_clause = {"section_type": section_type}
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where_clause
        )
        
        return {
            'query': query,
            'results': {
                'documents': results['documents'][0],
                'metadatas': results['metadatas'][0],
                'distances': results['distances'][0],
                'ids': results['ids'][0]
            }
        }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        count = self.collection.count()
        return {
            'collection_name': self.collection_name,
            'total_documents': count,
            'db_path': self.db_path
        }
    
    def delete_document(self, document_id: str) -> None:
        """Delete all chunks for a specific document"""
        # Get all chunk IDs for this document
        results = self.collection.get(
            where={"document_id": document_id}
        )
        
        if results['ids']:
            self.collection.delete(ids=results['ids'])
            logger.info(f"Deleted document: {document_id}")
        else:
            logger.warning(f"No chunks found for document: {document_id}")

# Example usage and testing
def main():
    # Initialize the embedder
    embedder = InsurancePolicyEmbedder(
        db_path="./insurance_chroma_db",
        collection_name="insurance_policies",
        chunk_size=800,
        chunk_overlap=100
    )
    
    # Example: Process a single PDF
    # doc_id = embedder.process_pdf(
    #     "path/to/your/policy.pdf",
    #     {
    #         "policy_type": "auto_insurance",
    #         "policy_number": "POL123456",
    #         "effective_date": "2024-01-01"
    #     }
    # )
    
    # Example: Process multiple PDFs
    # document_ids = embedder.process_multiple_pdfs(
    #     pdf_directory="./policies",
    #     metadata_file="./policy_metadata.json"
    # )
    
    # Example: Search for similar content
    # results = embedder.search_similar(
    #     query="What is covered under collision coverage?",
    #     n_results=3,
    #     section_type="coverage"
    # )
    
    # Print collection stats
    stats = embedder.get_collection_stats()
    print(f"Collection stats: {stats}")

if __name__ == "__main__":
    main()