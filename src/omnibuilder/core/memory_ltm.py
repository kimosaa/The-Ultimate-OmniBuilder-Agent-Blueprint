"""
P1.4 Long-Term Memory (LTM) Manager

Handles personalized, persistent knowledge, RAG over past projects, and user preferences.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from omnibuilder.models import Memory


class ProjectIndex:
    """Index of a project for memory retrieval."""

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.files: List[str] = []
        self.symbols: Dict[str, str] = {}
        self.created_at = datetime.now()


class Solution:
    """A past solution stored in memory."""

    def __init__(self, problem: str, solution: str, context: Dict[str, Any]):
        self.problem = problem
        self.solution = solution
        self.context = context
        self.success_count = 0


class LongTermMemoryManager:
    """Manages persistent knowledge and long-term memory."""

    def __init__(self, storage_path: str = ".omnibuilder/memory"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._memories: Dict[str, Memory] = {}
        self._user_preferences: Dict[str, Any] = {}
        self._project_indices: Dict[str, ProjectIndex] = {}
        self._solutions: List[Solution] = []

        self._load_memories()

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
                    self._user_preferences = data.get("preferences", {})
            except (json.JSONDecodeError, Exception):
                pass

    def _save_memories(self) -> None:
        """Save memories to disk."""
        memory_file = self.storage_path / "memories.json"
        data = {
            "memories": [m.model_dump() for m in self._memories.values()],
            "preferences": self._user_preferences
        }

        # Convert datetime objects to strings for JSON serialization
        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        with open(memory_file, "w") as f:
            json.dump(data, f, default=serialize, indent=2)

    def store_memory(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a memory item persistently.

        Args:
            key: Memory key for retrieval
            value: The value to store
            metadata: Optional metadata about the memory

        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())

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
        self._save_memories()

        return memory_id

    def retrieve_memory(self, query: str, top_k: int = 5) -> List[Memory]:
        """
        Retrieve memories matching a query.

        Args:
            query: Search query
            top_k: Maximum number of results

        Returns:
            List of matching memories
        """
        # Simple keyword-based retrieval
        # In production, use vector embeddings for semantic search
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

        # Sort by score and return top_k
        scored_memories.sort(key=lambda x: x[1], reverse=True)

        results = []
        for memory, _ in scored_memories[:top_k]:
            # Update access tracking
            memory.accessed_at = datetime.now()
            memory.access_count += 1
            results.append(memory)

        if results:
            self._save_memories()

        return results

    def update_user_preferences(self, prefs: Dict[str, Any]) -> None:
        """
        Update user preference profile.

        Args:
            prefs: Dictionary of preferences to update
        """
        self._user_preferences.update(prefs)
        self._save_memories()

    def get_user_preferences(self) -> Dict[str, Any]:
        """Get current user preferences."""
        return self._user_preferences.copy()

    def index_project(self, project_path: str) -> ProjectIndex:
        """
        Index a project for future reference.

        Args:
            project_path: Path to the project root

        Returns:
            ProjectIndex with file and symbol information
        """
        index = ProjectIndex(project_path)
        project_dir = Path(project_path)

        if not project_dir.exists():
            return index

        # Index all files
        for file_path in project_dir.rglob("*"):
            if file_path.is_file():
                # Skip hidden and common non-code files
                if any(part.startswith(".") for part in file_path.parts):
                    continue
                if file_path.suffix in [".pyc", ".class", ".o", ".exe"]:
                    continue

                rel_path = str(file_path.relative_to(project_dir))
                index.files.append(rel_path)

                # Extract symbols from Python files
                if file_path.suffix == ".py":
                    try:
                        content = file_path.read_text()
                        for line in content.split("\n"):
                            if line.strip().startswith("def "):
                                func_name = line.split("def ")[1].split("(")[0]
                                index.symbols[func_name] = rel_path
                            elif line.strip().startswith("class "):
                                class_name = line.split("class ")[1].split("(")[0].split(":")[0]
                                index.symbols[class_name] = rel_path
                    except Exception:
                        pass

        self._project_indices[project_path] = index

        # Store index in memory
        self.store_memory(
            key=f"project_index:{project_path}",
            value={"files": index.files, "symbols": index.symbols},
            metadata={"type": "project_index", "path": project_path}
        )

        return index

    def get_similar_solutions(self, problem: str, top_k: int = 5) -> List[Solution]:
        """
        Find similar past solutions.

        Args:
            problem: Problem description to match
            top_k: Maximum number of solutions

        Returns:
            List of similar solutions
        """
        problem_lower = problem.lower()
        problem_words = set(problem_lower.split())

        scored_solutions = []

        for solution in self._solutions:
            score = 0.0
            sol_words = set(solution.problem.lower().split())
            score += len(problem_words & sol_words)

            # Bonus for successful solutions
            score += solution.success_count * 0.5

            if score > 0:
                scored_solutions.append((solution, score))

        scored_solutions.sort(key=lambda x: x[1], reverse=True)

        return [sol for sol, _ in scored_solutions[:top_k]]

    def store_solution(
        self,
        problem: str,
        solution: str,
        context: Dict[str, Any]
    ) -> None:
        """
        Store a solution for future reference.

        Args:
            problem: The problem that was solved
            solution: The solution that worked
            context: Context about when/how it was solved
        """
        sol = Solution(problem, solution, context)
        self._solutions.append(sol)

        # Also store in general memory
        self.store_memory(
            key=f"solution:{problem[:50]}",
            value={"problem": problem, "solution": solution},
            metadata={"type": "solution", **context}
        )

    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.

        Args:
            memory_id: ID of memory to delete

        Returns:
            True if deleted, False if not found
        """
        if memory_id in self._memories:
            del self._memories[memory_id]
            self._save_memories()
            return True
        return False

    def clear_all(self) -> None:
        """Clear all memories."""
        self._memories.clear()
        self._user_preferences.clear()
        self._project_indices.clear()
        self._solutions.clear()
        self._save_memories()
