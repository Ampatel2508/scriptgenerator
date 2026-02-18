import json
import os
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
try:
    from langchain.vectorstores import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document
import hashlib

class DocumentChunker:
    """Handles chunking and RAG setup for steps data"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        self.vector_db = None
        self.documents_processed = []
        
    def load_steps(self, filepath: str) -> List[Dict]:
        """Load steps from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def convert_steps_to_documents(self, steps: List[Dict]) -> List[Document]:
        """Convert step events into LangChain Documents"""
        documents = []
        
        for idx, step in enumerate(steps):
            # Create readable content from step
            content = self._create_step_content(step, idx)
            
            # Create metadata
            metadata = {
                "step_index": idx,
                "event_type": step.get("eventType", "UNKNOWN"),
                "url": step.get("url", ""),
                "timestamp": step.get("timestamp", ""),
                "element_preview": step.get("eventElement", "")[:100],
            }
            
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)
        
        return documents
    
    def _create_step_content(self, step: Dict, idx: int) -> str:
        """Create readable content from a step"""
        event_type = step.get("eventType", "UNKNOWN")
        event_data = step.get("eventData", "")
        element = step.get("eventElement", "")
        url = step.get("url", "")
        
        content = f"""
Step {idx}:
Event Type: {event_type}
URL: {url}
Event Data: {event_data[:200]}
Element HTML: {element[:200]}
        """
        return content.strip()
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Chunk documents into smaller pieces"""
        chunked_docs = []
        
        for doc in documents:
            chunks = self.splitter.split_text(doc.page_content)
            
            for chunk_idx, chunk in enumerate(chunks):
                metadata = doc.metadata.copy()
                metadata["chunk_index"] = chunk_idx
                
                chunked_doc = Document(page_content=chunk, metadata=metadata)
                chunked_docs.append(chunked_doc)
        
        self.documents_processed = chunked_docs
        return chunked_docs
    
    def setup_vector_store(self, documents: List[Document], persist_dir: str = "vector_db"):
        """Setup Chroma vector store with embeddings"""
        try:
            # Use simple fake embeddings for faster setup (no model download)
            from langchain.embeddings.fake import FakeEmbeddings
            embeddings = FakeEmbeddings(model_name="fake")
        except Exception as e:
            print(f"FakeEmbeddings not available: {e}")
            print("Vector store disabled for this run")
            self.vector_db = None
            return None
        
        # Create or load vector store
        try:
            self.vector_db = Chroma.from_documents(
                documents=documents,
                embedding=embeddings,
                persist_directory=persist_dir
            )
            self.vector_db.persist()
        except Exception as e:
            print(f"Vector store creation failed: {e}")
            print("Continuing without vector store...")
            self.vector_db = None
        
        return self.vector_db
    
    def retrieve_relevant_steps(self, query: str, k: int = 5) -> List[Dict]:
        """Retrieve relevant steps based on query"""
        if self.vector_db is None:
            raise ValueError("Vector store not initialized. Call setup_vector_store first.")
        
        results = self.vector_db.similarity_search(query, k=k)
        return results
    
    def get_all_steps_context(self, steps: List[Dict]) -> str:
        """Get all steps as context string for LLM"""
        context = "Complete User Journey Steps:\n\n"
        
        for idx, step in enumerate(steps):
            step_desc = self._create_step_content(step, idx)
            context += step_desc + "\n\n"
        
        return context


if __name__ == "__main__":
    chunker = DocumentChunker()
    steps = chunker.load_steps("steps.json")
    print(f"Loaded {len(steps)} steps")
    
    documents = chunker.convert_steps_to_documents(steps)
    print(f"Created {len(documents)} documents")
    
    chunked_docs = chunker.chunk_documents(documents)
    print(f"Chunked into {len(chunked_docs)} chunks")
