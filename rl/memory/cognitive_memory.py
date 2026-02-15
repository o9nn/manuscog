"""
Cognitive Memory for RL
=======================

Memory system that bridges OpenManus-RL's SimpleMemory with
manuscog's AtomSpace-backed persistent memory.

The key insight: instead of storing flat text histories,
we store structured knowledge in the AtomSpace and use
attention values to determine what's "remembered" vs "forgotten".

Memory Types:
    1. Episodic Memory  - Step-by-step interaction history
    2. Semantic Memory   - Learned concepts and relationships (AtomSpace)
    3. Working Memory    - Current attentional focus (ECAN)
    4. Procedural Memory - Successful action sequences
"""

from __future__ import annotations
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class MemoryRecord:
    """A single memory record."""
    step: int
    episode: int
    timestamp: float
    action: str
    observation: str
    reward: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5  # ECAN-style attention value


class CognitiveMemory:
    """
    Cognitive memory system for RL training.
    
    Combines episodic, semantic, working, and procedural memory
    using AtomSpace-inspired attention-based retrieval.
    """
    
    def __init__(self, max_episodic_length: int = 100, decay_rate: float = 0.95):
        self.max_episodic_length = max_episodic_length
        self.decay_rate = decay_rate
        
        # Episodic memory: step-by-step history
        self._episodic: List[List[MemoryRecord]] = []
        self._current_episode: List[MemoryRecord] = []
        
        # Semantic memory: learned patterns
        self._semantic: Dict[str, Dict[str, Any]] = {}
        
        # Working memory: current focus
        self._working: List[MemoryRecord] = []
        self._working_capacity = 7  # Miller's magic number
        
        # Procedural memory: successful action sequences
        self._procedures: List[Dict[str, Any]] = []
        
        # Batch tracking
        self._batch_data: Optional[List[List[MemoryRecord]]] = None
        self.batch_size = 0
    
    def reset(self, batch_size: int = 1):
        """Reset memory for a new episode or batch."""
        if self._current_episode:
            self._episodic.append(self._current_episode)
        self._current_episode = []
        self._working = []
        
        # Batch mode
        self.batch_size = batch_size
        self._batch_data = [[] for _ in range(batch_size)]
    
    def store(self, record: MemoryRecord):
        """Store a new memory record."""
        # Calculate importance based on reward and novelty
        record.importance = self._calculate_importance(record)
        
        # Add to episodic memory
        self._current_episode.append(record)
        
        # Trim if too long
        if len(self._current_episode) > self.max_episodic_length:
            # Remove lowest importance records
            self._current_episode.sort(key=lambda r: r.importance, reverse=True)
            self._current_episode = self._current_episode[:self.max_episodic_length]
        
        # Update working memory
        self._update_working_memory(record)
        
        # Extract semantic patterns
        self._extract_semantic(record)
    
    def store_batch(self, records: Dict[str, List[Any]]):
        """
        Store batch records (compatible with OpenManus-RL SimpleMemory).
        
        Args:
            records: Dict with keys like 'text_obs', 'action', 'reward'
                     Each value is a list of length batch_size.
        """
        if self._batch_data is None:
            self.reset(len(list(records.values())[0]))
        
        for env_idx in range(self.batch_size):
            record = MemoryRecord(
                step=len(self._batch_data[env_idx]),
                episode=len(self._episodic),
                timestamp=time.time(),
                action=str(records.get("action", [""])[env_idx]),
                observation=str(records.get("text_obs", [""])[env_idx]),
                reward=float(records.get("reward", [0.0])[env_idx]),
                metadata={k: records[k][env_idx] for k in records if k not in ("action", "text_obs", "reward")},
            )
            record.importance = self._calculate_importance(record)
            self._batch_data[env_idx].append(record)
    
    def fetch(
        self,
        history_length: int = 10,
        strategy: str = "attention",
    ) -> Tuple[List[str], List[int]]:
        """
        Fetch memory context for each environment.
        
        Args:
            history_length: Maximum records to retrieve
            strategy: Retrieval strategy
                - "recent": Most recent records
                - "attention": Highest importance records
                - "mixed": Blend of recent and important
        
        Returns:
            memory_contexts: List of formatted context strings
            valid_lengths: List of actual record counts
        """
        contexts = []
        lengths = []
        
        # Use current_episode for non-batch mode, or when batch_data has empty lists
        if self._batch_data and any(len(d) > 0 for d in self._batch_data):
            data = self._batch_data
        else:
            data = [self._current_episode]
        
        for env_records in data:
            if not env_records:
                contexts.append("")
                lengths.append(0)
                continue
            
            # Select records based on strategy
            if strategy == "recent":
                selected = env_records[-history_length:]
            elif strategy == "attention":
                sorted_records = sorted(env_records, key=lambda r: r.importance, reverse=True)
                selected = sorted_records[:history_length]
                selected.sort(key=lambda r: r.step)  # Re-sort by time
            elif strategy == "mixed":
                half = history_length // 2
                recent = env_records[-half:]
                important = sorted(env_records[:-half] if len(env_records) > half else [],
                                   key=lambda r: r.importance, reverse=True)[:half]
                selected = sorted(important + recent, key=lambda r: r.step)
            else:
                selected = env_records[-history_length:]
            
            # Format as text
            lines = []
            for rec in selected:
                lines.append(
                    f"[Step {rec.step} | R:{rec.reward:.2f} | I:{rec.importance:.2f}] "
                    f"Action: {rec.action} → Obs: {rec.observation[:100]}"
                )
            
            contexts.append("\n".join(lines))
            lengths.append(len(selected))
        
        return contexts, lengths
    
    def fetch_semantic(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch relevant semantic memories.
        
        Uses simple keyword matching (could be upgraded to embeddings).
        """
        query_words = set(query.lower().split())
        scored = []
        
        for key, value in self._semantic.items():
            key_words = set(key.lower().split("_"))
            overlap = len(query_words & key_words)
            if overlap > 0:
                scored.append((overlap * value.get("importance", 0.5), key, value))
        
        scored.sort(reverse=True)
        return [{"key": k, **v} for _, k, v in scored[:top_k]]
    
    def fetch_procedures(self, context: str = "", top_k: int = 3) -> List[Dict[str, Any]]:
        """Fetch relevant successful procedures."""
        if not self._procedures:
            return []
        
        # Sort by success rate
        sorted_procs = sorted(
            self._procedures,
            key=lambda p: p.get("avg_reward", 0),
            reverse=True
        )
        return sorted_procs[:top_k]
    
    def _calculate_importance(self, record: MemoryRecord) -> float:
        """
        Calculate importance (attention value) for a memory record.
        
        Factors:
        - Reward magnitude (high reward = important)
        - Novelty (new action types = important)
        - Recency (recent = slightly more important)
        """
        importance = 0.5  # Base importance
        
        # Reward factor
        importance += 0.3 * min(1.0, abs(record.reward))
        
        # Novelty factor
        recent_actions = [r.action for r in self._current_episode[-10:]]
        if record.action not in recent_actions:
            importance += 0.1
        
        # Recency factor (slight boost)
        importance += 0.1
        
        return min(1.0, importance)
    
    def _update_working_memory(self, record: MemoryRecord):
        """Update working memory with attention-based selection."""
        self._working.append(record)
        
        # Apply decay to existing items
        for item in self._working:
            item.importance *= self.decay_rate
        
        # Keep only top-k by importance
        if len(self._working) > self._working_capacity:
            self._working.sort(key=lambda r: r.importance, reverse=True)
            self._working = self._working[:self._working_capacity]
    
    def _extract_semantic(self, record: MemoryRecord):
        """Extract semantic patterns from episodic memory."""
        # Track action-reward associations
        action_key = f"action_{record.action}"
        if action_key not in self._semantic:
            self._semantic[action_key] = {
                "count": 0,
                "total_reward": 0.0,
                "avg_reward": 0.0,
                "importance": 0.5,
            }
        
        entry = self._semantic[action_key]
        entry["count"] += 1
        entry["total_reward"] += record.reward
        entry["avg_reward"] = entry["total_reward"] / entry["count"]
        entry["importance"] = min(1.0, 0.3 + 0.7 * abs(entry["avg_reward"]))
    
    def record_procedure(self, actions: List[str], total_reward: float):
        """Record a successful action sequence as a procedure."""
        self._procedures.append({
            "actions": actions,
            "total_reward": total_reward,
            "avg_reward": total_reward / max(1, len(actions)),
            "length": len(actions),
            "timestamp": time.time(),
        })
        
        # Keep only top procedures
        if len(self._procedures) > 50:
            self._procedures.sort(key=lambda p: p["avg_reward"], reverse=True)
            self._procedures = self._procedures[:50]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "episodic_episodes": len(self._episodic),
            "current_episode_length": len(self._current_episode),
            "semantic_entries": len(self._semantic),
            "working_memory_size": len(self._working),
            "procedures_stored": len(self._procedures),
            "batch_size": self.batch_size,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize memory state."""
        return {
            "episodic_count": len(self._episodic),
            "semantic": self._semantic,
            "procedures": self._procedures[:10],
            "stats": self.get_stats(),
        }
