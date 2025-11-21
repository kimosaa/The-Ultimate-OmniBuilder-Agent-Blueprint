"""
Enhanced memory system with vector embeddings and semantic search.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from omnibuilder.models import Memory


class VectorMemoryStore:
    """Memory store with vector embeddings for semantic search."""

    def __init__(
        self,
        storage_path: str = ".omnibuilder/memory",
        embedding_func: Optional[callable] = None
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.embedding_func = embedding_func
        self._memories: Dict[str, Memory] = {}
        self._embeddings: Dict[str, List[float]] = {}
        self._chroma_client = None
        self._collection = None

        self._load_memories()
        self._initialize_vector_db()

    def _initialize_vector_db(self) -> None:
        """Initialize ChromaDB for vector storage."""
        try:
            import chromadb
            from chromadb.config import Settings

            chroma_path = str(self.storage_path / "chroma_db")

            self._chroma_client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=chroma_path
            ))

            self._collection = self._chroma_client.get_or_create_collection(
                name="omnibuilder_memory",
                metadata={"description": "OmniBuilder semantic memory"}
            )

        except ImportError:
            print("ChromaDB not available. Falling back to basic search.")

    def _load_memories(self) -> None:
        """Load memories from disk."""
        memory_file = self.storage_path / "memories.json"
        if memory_file.exists():
            try:
                with open(memory_file) as f:
                    data = json.load(f)
                    for mem_data in data.get("memories", []):
                        mem = Memory(**mem_data)
                        self._memories[mem.id] = mem
            except (json.JSONDecodeError, Exception):
                pass

    def _save_memories(self) -> None:
        """Save memories to disk."""
        memory_file = self.storage_path / "memories.json"

        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        data = {
            "memories": [m.model_dump() for m in self._memories.values()],
        }

        with open(memory_file, "w") as f:
            json.dump(data, f, default=serialize, indent=2)

    async def store(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a memory with vector embedding.

        Args:
            key: Memory key
            value: Value to store
            metadata: Optional metadata

        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())

        # Create memory object
        memory = Memory(
            id=memory_id,
            key=key,
            value=value,
            metadata=metadata or {},
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            access_count=0
        )

        self._memories[memory_id] = memory

        # Generate and store embedding
        if self._collection and self.embedding_func:
            # Create text representation for embedding
            text_repr = f"{key}: {str(value)}"

            try:
                embedding = await self.embedding_func(text_repr)

                self._collection.add(
                    embeddings=[embedding],
                    documents=[text_repr],
                    metadatas=[metadata or {}],
                    ids=[memory_id]
                )
            except Exception as e:
                print(f"Failed to generate embedding: {e}")

        self._save_memories()
        return memory_id

    async def search_semantic(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Memory]:
        """
        Semantic search using vector embeddings.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of matching memories
        """
        if not self._collection or not self.embedding_func:
            # Fallback to keyword search
            return self.search_keyword(query, top_k)

        try:
            # Generate query embedding
            query_embedding = await self.embedding_func(query)

            # Query ChromaDB
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )

            # Retrieve full memory objects
            memories = []
            for memory_id in results['ids'][0]:
                if memory_id in self._memories:
                    memory = self._memories[memory_id]
                    memory.accessed_at = datetime.now()
                    memory.access_count += 1
                    memories.append(memory)

            self._save_memories()
            return memories

        except Exception as e:
            print(f"Semantic search failed: {e}")
            return self.search_keyword(query, top_k)

    def search_keyword(self, query: str, top_k: int = 5) -> List[Memory]:
        """
        Keyword-based search fallback.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of matching memories
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored_memories = []

        for memory in self._memories.values():
            score = 0.0

            # Match on key
            key_words = set(memory.key.lower().split())
            score += len(query_words & key_words) * 2

            # Match on value if string
            if isinstance(memory.value, str):
                value_words = set(memory.value.lower().split())
                score += len(query_words & value_words)

            # Match on metadata
            for meta_value in memory.metadata.values():
                if isinstance(meta_value, str) and query_lower in meta_value.lower():
                    score += 1

            if score > 0:
                scored_memories.append((memory, score))

        # Sort by score and recency
        scored_memories.sort(
            key=lambda x: (x[1], x[0].accessed_at),
            reverse=True
        )

        results = []
        for memory, _ in scored_memories[:top_k]:
            memory.accessed_at = datetime.now()
            memory.access_count += 1
            results.append(memory)

        if results:
            self._save_memories()

        return results

    def get_recent(self, limit: int = 10) -> List[Memory]:
        """Get most recently accessed memories."""
        memories = sorted(
            self._memories.values(),
            key=lambda m: m.accessed_at,
            reverse=True
        )
        return memories[:limit]

    def get_popular(self, limit: int = 10) -> List[Memory]:
        """Get most frequently accessed memories."""
        memories = sorted(
            self._memories.values(),
            key=lambda m: m.access_count,
            reverse=True
        )
        return memories[:limit]

    def delete(self, memory_id: str) -> bool:
        """Delete a memory."""
        if memory_id in self._memories:
            del self._memories[memory_id]

            if self._collection:
                try:
                    self._collection.delete(ids=[memory_id])
                except Exception:
                    pass

            self._save_memories()
            return True

        return False

    def clear_all(self) -> None:
        """Clear all memories."""
        self._memories.clear()

        if self._collection:
            try:
                self._chroma_client.delete_collection("omnibuilder_memory")
                self._initialize_vector_db()
            except Exception:
                pass

        self._save_memories()

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "total_memories": len(self._memories),
            "vector_db_enabled": self._collection is not None,
            "total_accesses": sum(m.access_count for m in self._memories.values()),
            "oldest_memory": min(
                (m.created_at for m in self._memories.values()),
                default=None
            ),
            "newest_memory": max(
                (m.created_at for m in self._memories.values()),
                default=None
            ),
        }
