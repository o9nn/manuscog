"""
Cognitive Reward Manager
========================

Reward system that combines traditional RL rewards with cognitive quality
signals from the manuscog kernel. Inspired by OpenManus-RL's
EpisodeRewardManager but enhanced with cognitive metrics.

Reward Sources:
    1. Task Reward     - Did the agent achieve the goal?
    2. Reasoning Reward - Quality of PLN inferences
    3. Attention Reward - Efficiency of ECAN attention allocation
    4. Growth Reward    - Knowledge graph growth and connectivity
    5. Coherence Reward - Consistency of the knowledge base
    6. Self-Improvement - Autognosis optimization effectiveness
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class RewardConfig:
    """Configuration for cognitive reward calculation."""

    # Weight for each reward component
    task_weight: float = 1.0
    reasoning_weight: float = 0.3
    attention_weight: float = 0.2
    growth_weight: float = 0.1
    coherence_weight: float = 0.15
    self_improvement_weight: float = 0.15
    efficiency_weight: float = 0.1

    # Thresholds
    min_inference_quality: float = 0.3
    target_attention_entropy: float = 2.0  # bits
    max_atoms_bonus: int = 100

    # Penalties
    redundancy_penalty: float = -0.05
    failed_action_penalty: float = -0.1
    no_op_penalty: float = -0.02

    # Normalization
    normalize_rewards: bool = True
    reward_clip: float = 5.0


@dataclass
class RewardBreakdown:
    """Detailed breakdown of reward components."""

    total: float = 0.0
    task: float = 0.0
    reasoning: float = 0.0
    attention: float = 0.0
    growth: float = 0.0
    coherence: float = 0.0
    self_improvement: float = 0.0
    efficiency: float = 0.0
    penalties: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "total": self.total,
            "task": self.task,
            "reasoning": self.reasoning,
            "attention": self.attention,
            "growth": self.growth,
            "coherence": self.coherence,
            "self_improvement": self.self_improvement,
            "efficiency": self.efficiency,
            "penalties": self.penalties,
        }


class CognitiveRewardManager:
    """
    Manages reward calculation for cognitive RL training.

    Combines multiple cognitive quality signals into a single
    reward value that encourages the agent to build better
    knowledge structures and reason more effectively.
    """

    def __init__(self, config: Optional[RewardConfig] = None):
        self.config = config or RewardConfig()
        self._episode_history: List[RewardBreakdown] = []
        self._running_stats = {
            "mean": 0.0,
            "var": 1.0,
            "count": 0,
        }

    def calculate_step_reward(
        self,
        prev_metrics: Dict[str, Any],
        curr_metrics: Dict[str, Any],
        action_result: Dict[str, Any],
        goal_progress: float = 0.0,
    ) -> RewardBreakdown:
        """
        Calculate reward for a single step.

        Args:
            prev_metrics: Metrics before the action
            curr_metrics: Metrics after the action
            action_result: Result of the action execution
            goal_progress: Progress toward episode goals (0-1)

        Returns:
            RewardBreakdown with detailed component scores
        """
        breakdown = RewardBreakdown()

        # 1. Task reward
        breakdown.task = self._task_reward(goal_progress)

        # 2. Reasoning reward
        breakdown.reasoning = self._reasoning_reward(prev_metrics, curr_metrics)

        # 3. Attention reward
        breakdown.attention = self._attention_reward(prev_metrics, curr_metrics)

        # 4. Growth reward
        breakdown.growth = self._growth_reward(prev_metrics, curr_metrics)

        # 5. Coherence reward
        breakdown.coherence = self._coherence_reward(curr_metrics)

        # 6. Self-improvement reward
        breakdown.self_improvement = self._self_improvement_reward(
            prev_metrics, curr_metrics
        )

        # 7. Efficiency reward
        breakdown.efficiency = self._efficiency_reward(action_result)

        # 8. Penalties
        breakdown.penalties = self._calculate_penalties(action_result)

        # Weighted sum
        breakdown.total = (
            self.config.task_weight * breakdown.task
            + self.config.reasoning_weight * breakdown.reasoning
            + self.config.attention_weight * breakdown.attention
            + self.config.growth_weight * breakdown.growth
            + self.config.coherence_weight * breakdown.coherence
            + self.config.self_improvement_weight * breakdown.self_improvement
            + self.config.efficiency_weight * breakdown.efficiency
            + breakdown.penalties
        )

        # Normalize
        if self.config.normalize_rewards:
            breakdown.total = self._normalize_reward(breakdown.total)

        # Clip
        breakdown.total = max(
            -self.config.reward_clip, min(self.config.reward_clip, breakdown.total)
        )

        self._episode_history.append(breakdown)
        return breakdown

    def calculate_episode_reward(
        self,
        episode_metrics: Dict[str, Any],
        goal_achieved: bool,
    ) -> float:
        """
        Calculate the total episode reward.

        Args:
            episode_metrics: Final metrics for the episode
            goal_achieved: Whether the episode goal was achieved

        Returns:
            Total episode reward
        """
        # Base: sum of step rewards
        step_total = sum(b.total for b in self._episode_history)

        # Goal achievement bonus
        if goal_achieved:
            step_total += 5.0

        # Efficiency bonus: fewer steps to achieve goal = better
        if goal_achieved and len(self._episode_history) > 0:
            efficiency_bonus = 1.0 / math.sqrt(len(self._episode_history))
            step_total += efficiency_bonus

        return step_total

    def reset_episode(self):
        """Reset for a new episode."""
        self._episode_history = []

    # =========================================================================
    # REWARD COMPONENTS
    # =========================================================================

    def _task_reward(self, goal_progress: float) -> float:
        """Reward for progress toward the task goal."""
        return goal_progress

    def _reasoning_reward(self, prev: Dict[str, Any], curr: Dict[str, Any]) -> float:
        """Reward for quality reasoning."""
        # New inferences
        inference_delta = curr.get("total_inferences", 0) - prev.get(
            "total_inferences", 0
        )
        if inference_delta <= 0:
            return 0.0

        # Quality: ratio of successful to total
        total = curr.get("total_inferences", 1)
        successful = curr.get("successful_inferences", 0)
        quality = successful / max(1, total)

        # Reward scales with both quantity and quality
        return inference_delta * quality

    def _attention_reward(self, prev: Dict[str, Any], curr: Dict[str, Any]) -> float:
        """Reward for effective attention allocation."""
        # Reward for using attention (not letting it stagnate)
        sti_delta = abs(curr.get("total_sti", 0) - prev.get("total_sti", 0))

        # Reward for attention cycles
        cycle_delta = curr.get("ecan_cycles", 0) - prev.get("ecan_cycles", 0)

        return 0.1 * sti_delta + 0.05 * cycle_delta

    def _growth_reward(self, prev: Dict[str, Any], curr: Dict[str, Any]) -> float:
        """Reward for knowledge graph growth."""
        atom_delta = curr.get("num_atoms", 0) - prev.get("num_atoms", 0)

        if atom_delta <= 0:
            return 0.0

        # Diminishing returns for growth
        current_size = curr.get("num_atoms", 0)
        if current_size > self.config.max_atoms_bonus:
            return 0.01 * atom_delta  # Reduced reward for large graphs

        return 0.1 * atom_delta

    def _coherence_reward(self, curr: Dict[str, Any]) -> float:
        """Reward for knowledge base coherence."""
        # Ratio of links to nodes (connectivity)
        nodes = max(1, curr.get("num_nodes", 1))
        links = curr.get("num_links", 0)
        connectivity = links / nodes

        # Ideal connectivity is around 2-3 links per node
        if connectivity < 0.5:
            return -0.1  # Too sparse
        elif connectivity > 5.0:
            return -0.05  # Too dense
        else:
            return 0.1 * min(1.0, connectivity / 2.0)

    def _self_improvement_reward(
        self, prev: Dict[str, Any], curr: Dict[str, Any]
    ) -> float:
        """Reward for self-improvement through autognosis."""
        # Reward for optimization actions
        prev_pool = prev.get("stimulus_pool", 100.0)
        curr_pool = curr.get("stimulus_pool", 100.0)

        # If stimulus pool is being used effectively
        if curr_pool < prev_pool:
            return 0.1  # Attention is being allocated

        return 0.0

    def _efficiency_reward(self, action_result: Dict[str, Any]) -> float:
        """Reward for efficient actions."""
        if action_result.get("success", False):
            return 0.05
        return 0.0

    def _calculate_penalties(self, action_result: Dict[str, Any]) -> float:
        """Calculate penalties for bad behavior."""
        penalties = 0.0

        if not action_result.get("success", False):
            penalties += self.config.failed_action_penalty

        action = action_result.get("action", {})
        if isinstance(action, dict) and action.get("action") == "no_op":
            penalties += self.config.no_op_penalty

        return penalties

    def _normalize_reward(self, reward: float) -> float:
        """Normalize reward using running statistics."""
        self._running_stats["count"] += 1
        n = self._running_stats["count"]

        old_mean = self._running_stats["mean"]
        self._running_stats["mean"] = old_mean + (reward - old_mean) / n

        if n > 1:
            self._running_stats["var"] = self._running_stats["var"] * (n - 2) / (
                n - 1
            ) + (reward - old_mean) * (reward - self._running_stats["mean"]) / (n - 1)

        std = math.sqrt(max(self._running_stats["var"], 1e-8))
        return (reward - self._running_stats["mean"]) / std

    def get_episode_stats(self) -> Dict[str, Any]:
        """Get statistics for the current episode."""
        if not self._episode_history:
            return {}

        totals = [b.total for b in self._episode_history]
        return {
            "num_steps": len(self._episode_history),
            "total_reward": sum(totals),
            "mean_reward": sum(totals) / len(totals),
            "max_reward": max(totals),
            "min_reward": min(totals),
            "component_means": {
                "task": sum(b.task for b in self._episode_history)
                / len(self._episode_history),
                "reasoning": sum(b.reasoning for b in self._episode_history)
                / len(self._episode_history),
                "attention": sum(b.attention for b in self._episode_history)
                / len(self._episode_history),
                "growth": sum(b.growth for b in self._episode_history)
                / len(self._episode_history),
                "coherence": sum(b.coherence for b in self._episode_history)
                / len(self._episode_history),
                "self_improvement": sum(
                    b.self_improvement for b in self._episode_history
                )
                / len(self._episode_history),
            },
        }
