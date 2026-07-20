"""Memory management for Agent."""

from datetime import datetime
from typing import Any, Dict, List, Optional


class Memory:
    """Single memory entry."""
    
    def __init__(self, content: str, memory_type: str = 'short_term', metadata: Dict = None):
        self.content = content
        self.memory_type = memory_type
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.accessed_at = None


class MemoryStore:
    """In-memory store for agent memories."""
    
    def __init__(self, max_short_term: int = 10):
        self.max_short_term = max_short_term
        self._memories: List[Memory] = []
    
    async def store(self, content: str, memory_type: str = 'short_term', metadata: Dict = None) -> None:
        """Store a new memory."""
        memory = Memory(content=content, memory_type=memory_type, metadata=metadata)
        self._memories.append(memory)
        
        # Keep only recent short-term memories
        if memory_type == 'short_term':
            short_term = [m for m in self._memories if m.memory_type == 'short_term']
            if len(short_term) > self.max_short_term:
                self._memories = [
                    m for m in self._memories 
                    if m.memory_type != 'short_term' or m not in short_term[:-self.max_short_term]
                ]
    
    async def retrieve(self, query: str = None, limit: int = 10) -> List[Memory]:
        """Retrieve memories."""
        sorted_memories = sorted(self._memories, key=lambda m: m.created_at, reverse=True)
        return sorted_memories[:limit]
    
    async def clear(self) -> None:
        """Clear all memories."""
        self._memories = []
