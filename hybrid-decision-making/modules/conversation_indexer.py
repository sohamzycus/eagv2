# modules/conversation_indexer.py

"""
Historical Conversation Indexing System
Uses FAISS vector embeddings to search past conversations and provide context to the agent.
"""

import json
import os
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime
from modules.memory import MemoryItem

# Configuration
EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
CONVERSATION_INDEX_DIR = Path("faiss_index/conversations")
CONVERSATION_INDEX_DIR.mkdir(parents=True, exist_ok=True)


class ConversationIndexer:
    """
    Indexes historical conversations for semantic search.
    Allows agent to learn from past interactions.
    """
    
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.index_path = CONVERSATION_INDEX_DIR / "conversations.faiss"
        self.metadata_path = CONVERSATION_INDEX_DIR / "conversations_metadata.json"
        self.index = None
        self.metadata = []
        
        # Load existing index if available
        if self.index_path.exists() and self.metadata_path.exists():
            self.load_index()
    
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding vector for text using Ollama"""
        try:
            result = requests.post(
                EMBED_URL,
                json={"model": EMBED_MODEL, "prompt": text},
                timeout=30
            )
            result.raise_for_status()
            embedding = np.array(result.json()["embedding"], dtype=np.float32)
            return embedding
        except Exception as e:
            print(f"⚠️ Embedding error: {e}")
            # Return zero vector as fallback
            return np.zeros(768, dtype=np.float32)
    
    
    def scan_memory_directory(self) -> List[Dict[str, Any]]:
        """
        Scan memory directory for all session files
        Returns list of conversations with metadata
        """
        conversations = []
        
        if not self.memory_dir.exists():
            print(f"⚠️ Memory directory not found: {self.memory_dir}")
            return conversations
        
        # Recursively find all JSON files
        session_files = list(self.memory_dir.rglob("session-*.json"))
        print(f"📁 Found {len(session_files)} session files")
        
        for session_file in session_files:
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    items = json.load(f)
                
                # Extract session info
                session_id = session_file.stem.replace("session-", "")
                
                # Find user query and final answer
                user_query = None
                final_answer = None
                tool_calls = []
                success_count = 0
                
                for item in items:
                    if item.get("type") == "run_metadata" and "user_query" in item.get("metadata", {}):
                        user_query = item["metadata"]["user_query"]
                    elif item.get("type") == "final_answer":
                        final_answer = item.get("final_answer")
                    elif item.get("type") == "tool_output":
                        tool_calls.append(item.get("tool_name"))
                        if item.get("success"):
                            success_count += 1
                
                if user_query:  # Only index if we have a user query
                    conversations.append({
                        "session_id": session_id,
                        "user_query": user_query,
                        "final_answer": final_answer or "No answer recorded",
                        "tool_calls": tool_calls,
                        "success_count": success_count,
                        "total_interactions": len(items),
                        "file_path": str(session_file),
                        "date": session_file.parent.parent.parent.name + "-" + 
                               session_file.parent.parent.name + "-" + 
                               session_file.parent.name
                    })
            
            except Exception as e:
                print(f"⚠️ Error reading {session_file}: {e}")
        
        return conversations
    
    
    def index_conversations(self, force_rebuild: bool = False):
        """
        Index all conversations from memory directory
        Creates FAISS index for semantic search
        """
        if not force_rebuild and self.index is not None:
            print("✅ Index already loaded")
            return
        
        print("🔍 Scanning memory directory...")
        conversations = self.scan_memory_directory()
        
        if not conversations:
            print("⚠️ No conversations found to index")
            return
        
        print(f"📊 Indexing {len(conversations)} conversations...")
        
        embeddings = []
        metadata = []
        
        for i, conv in enumerate(conversations):
            # Create rich text representation for embedding
            text_to_embed = (
                f"User Query: {conv['user_query']}\n"
                f"Final Answer: {conv['final_answer']}\n"
                f"Tools Used: {', '.join(conv['tool_calls']) if conv['tool_calls'] else 'None'}"
            )
            
            embedding = self.get_embedding(text_to_embed)
            embeddings.append(embedding)
            metadata.append(conv)
            
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(conversations)} conversations...")
        
        # Create FAISS index
        embeddings_array = np.stack(embeddings)
        dimension = embeddings_array.shape[1]
        
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_array)
        self.metadata = metadata
        
        # Save index
        self.save_index()
        
        print(f"✅ Indexed {len(conversations)} conversations successfully")
    
    
    def save_index(self):
        """Save FAISS index and metadata to disk"""
        if self.index is None:
            print("⚠️ No index to save")
            return
        
        faiss.write_index(self.index, str(self.index_path))
        
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)
        
        print(f"💾 Saved index to {self.index_path}")
    
    
    def load_index(self):
        """Load FAISS index and metadata from disk"""
        try:
            self.index = faiss.read_index(str(self.index_path))
            
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            
            print(f"✅ Loaded index with {len(self.metadata)} conversations")
        except Exception as e:
            print(f"⚠️ Error loading index: {e}")
            self.index = None
            self.metadata = []
    
    
    def search_similar_conversations(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar past conversations using semantic search
        
        Args:
            query: Current user query
            top_k: Number of similar conversations to return
            min_similarity: Minimum similarity threshold
        
        Returns:
            List of similar conversations with metadata
        """
        if self.index is None or len(self.metadata) == 0:
            print("⚠️ No index loaded. Attempting to build...")
            self.index_conversations()
            if self.index is None:
                return []
        
        # Get query embedding
        query_embedding = self.get_embedding(query).reshape(1, -1)
        
        # Search FAISS index
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Prepare results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):  # Valid index
                similarity = 1 / (1 + dist)  # Convert distance to similarity
                
                if similarity >= min_similarity:
                    result = self.metadata[idx].copy()
                    result["similarity"] = float(similarity)
                    result["distance"] = float(dist)
                    results.append(result)
        
        return results
    
    
    def get_context_for_agent(
        self,
        query: str,
        top_k: int = 3
    ) -> str:
        """
        Get formatted context from similar conversations for agent prompt
        
        Args:
            query: Current user query
            top_k: Number of examples to include
        
        Returns:
            Formatted string for LLM prompt
        """
        similar = self.search_similar_conversations(query, top_k=top_k, min_similarity=0.5)
        
        if not similar:
            return "No relevant past conversations found."
        
        context_parts = ["📚 Relevant Past Conversations:\n"]
        
        for i, conv in enumerate(similar, 1):
            context_parts.append(
                f"\n{i}. Similar Query (Similarity: {conv['similarity']:.2%})\n"
                f"   Q: {conv['user_query']}\n"
                f"   A: {conv['final_answer'][:200]}{'...' if len(conv['final_answer']) > 200 else ''}\n"
                f"   Tools: {', '.join(conv['tool_calls'][:3])}{'...' if len(conv['tool_calls']) > 3 else ''}\n"
                f"   Success Rate: {conv['success_count']}/{len(conv['tool_calls']) or 1}"
            )
        
        return "".join(context_parts)
    
    
    def export_to_json(self, output_path: str = "historical_conversations.json"):
        """
        Export all indexed conversations to a JSON file
        """
        if not self.metadata:
            print("⚠️ No conversations to export")
            return
        
        export_data = {
            "total_conversations": len(self.metadata),
            "export_date": datetime.now().isoformat(),
            "conversations": self.metadata
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Exported {len(self.metadata)} conversations to {output_path}")


def create_sample_conversations():
    """
    Create sample conversations for testing
    """
    sample_sessions = [
        {
            "query": "What is the capital of France?",
            "answer": "The capital of France is Paris.",
            "tools": ["search"],
            "success": True
        },
        {
            "query": "Calculate 5 + 3",
            "answer": "5 + 3 = 8",
            "tools": ["add"],
            "success": True
        },
        {
            "query": "Find ASCII values of INDIA",
            "answer": "I=73, N=78, D=68, I=73, A=65",
            "tools": ["strings_to_chars_to_int"],
            "success": True
        }
    ]
    
    memory_dir = Path("memory/2025/01/15")
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    for i, sample in enumerate(sample_sessions):
        session_file = memory_dir / f"session-test-{i}.json"
        
        items = [
            {
                "timestamp": 1234567890.0,
                "type": "run_metadata",
                "text": f"Started session with: {sample['query']}",
                "session_id": f"test-{i}",
                "tags": ["run_start"],
                "metadata": {
                    "start_time": "2025-01-15T10:00:00",
                    "step": 0,
                    "user_query": sample["query"]
                }
            },
            {
                "timestamp": 1234567891.0,
                "type": "tool_output",
                "text": f"Tool result: {sample['answer']}",
                "tool_name": sample["tools"][0],
                "tool_args": {},
                "tool_result": {"result": sample["answer"]},
                "success": sample["success"],
                "tags": []
            },
            {
                "timestamp": 1234567892.0,
                "type": "final_answer",
                "text": sample["answer"],
                "final_answer": sample["answer"]
            }
        ]
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2)
    
    print(f"✅ Created {len(sample_sessions)} sample conversations")


# ==================== MAIN ====================

if __name__ == "__main__":
    print("🧠 Conversation Indexer - Historical Context System\n")
    
    # Create sample data (comment out if you have real data)
    # create_sample_conversations()
    
    # Initialize indexer
    indexer = ConversationIndexer()
    
    # Index all conversations
    indexer.index_conversations(force_rebuild=True)
    
    # Test search
    print("\n🔍 Testing semantic search...\n")
    test_queries = [
        "What is the capital city of France?",
        "Add two numbers together",
        "Convert string to ASCII values"
    ]
    
    for query in test_queries:
        print(f"Query: {query}")
        context = indexer.get_context_for_agent(query, top_k=2)
        print(context)
        print("-" * 80)
    
    # Export to JSON
    indexer.export_to_json("historical_conversations.json")
    
    print("\n✅ Indexing complete!")

