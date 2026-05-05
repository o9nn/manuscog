"""
Cognitive Advantage Algorithm
==============================

Extends OpenManus-RL's GiGPO (Group-in-Group Policy Optimization) with
cognitive signals from the manuscog kernel.

Key Innovation: Step-level grouping uses AtomSpace state fingerprints
as anchor observations, enabling the algorithm to recognize when the
cognitive state is "equivalent" across different trajectories.

Components:
    1. Episode-level advantage: Standard GRPO-style normalization
    2. Step-level advantage: GiGPO grouping by cognitive state
    3. Cognitive bonus: Additional advantage from reasoning quality
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AdvantageConfig:
    """Configuration for cognitive advantage computation."""

    # GiGPO parameters
    gamma: float = 0.99  # Discount factor
    step_advantage_weight: float = 1.0
    epsilon: float = 1e-6
    mode: str = "mean_norm"  # "mean_norm" or "mean_std_norm"

    # Cognitive bonus parameters
    reasoning_bonus_weight: float = 0.2
    attention_bonus_weight: float = 0.1
    coherence_bonus_weight: float = 0.1

    # Normalization
    normalize_advantages: bool = True


@dataclass
class TrajectoryStep:
    """A single step in a cognitive trajectory."""

    step_id: int
    episode_id: str
    traj_uid: str

    # State
    state_hash: str  # AtomSpace fingerprint
    observation_text: str = ""

    # Action
    action: str = ""
    action_type: str = ""

    # Rewards
    reward: float = 0.0
    cognitive_reward: float = 0.0

    # Cognitive metrics
    num_atoms: int = 0
    num_inferences: int = 0
    attention_sti: float = 0.0
    coherence: float = 0.0

    # Flags
    active: bool = True
    done: bool = False


class CognitiveAdvantageComputer:
    """
    Computes advantages for cognitive RL training.

    Combines GiGPO's step-level grouping with cognitive quality
    signals to produce advantages that encourage both task completion
    and cognitive development.
    """

    def __init__(self, config: Optional[AdvantageConfig] = None):
        self.config = config or AdvantageConfig()
        self._group_cache: Dict[str, List[int]] = {}

    def compute_advantages(
        self,
        trajectories: List[List[TrajectoryStep]],
    ) -> List[List[float]]:
        """
        Compute advantages for a batch of trajectories.

        Args:
            trajectories: List of trajectories, each a list of steps.

        Returns:
            List of advantage values per step per trajectory.
        """
        # Flatten for batch processing
        all_steps = []
        traj_boundaries = []
        offset = 0
        for traj in trajectories:
            traj_boundaries.append((offset, offset + len(traj)))
            all_steps.extend(traj)
            offset += len(traj)

        if not all_steps:
            return []

        # 1. Compute discounted returns
        returns = self._compute_discounted_returns(trajectories)

        # 2. Compute episode-level advantage
        episode_advantages = self._compute_episode_advantage(trajectories, returns)

        # 3. Compute step-level advantage (GiGPO-style)
        step_advantages = self._compute_step_advantage(all_steps, traj_boundaries)

        # 4. Compute cognitive bonus
        cognitive_bonuses = self._compute_cognitive_bonus(all_steps, traj_boundaries)

        # 5. Combine
        combined = []
        flat_idx = 0
        for traj_idx, traj in enumerate(trajectories):
            traj_advantages = []
            for step_idx in range(len(traj)):
                advantage = (
                    episode_advantages[traj_idx]
                    + self.config.step_advantage_weight * step_advantages[flat_idx]
                    + cognitive_bonuses[flat_idx]
                )
                traj_advantages.append(advantage)
                flat_idx += 1
            combined.append(traj_advantages)

        # Normalize
        if self.config.normalize_advantages:
            combined = self._normalize(combined)

        return combined

    def _compute_discounted_returns(
        self, trajectories: List[List[TrajectoryStep]]
    ) -> List[List[float]]:
        """Compute discounted returns for each trajectory."""
        all_returns = []

        for traj in trajectories:
            returns = [0.0] * len(traj)
            running_return = 0.0

            for t in reversed(range(len(traj))):
                total_reward = traj[t].reward + traj[t].cognitive_reward
                running_return = total_reward + self.config.gamma * running_return
                returns[t] = running_return

            all_returns.append(returns)

        return all_returns

    def _compute_episode_advantage(
        self,
        trajectories: List[List[TrajectoryStep]],
        returns: List[List[float]],
    ) -> List[float]:
        """
        Compute episode-level advantage.

        Groups trajectories by their starting state and normalizes
        returns within each group.
        """
        # Group by episode_id (same starting conditions)
        groups: Dict[str, List[int]] = defaultdict(list)
        episode_returns = []

        for traj_idx, traj in enumerate(trajectories):
            if traj:
                episode_id = traj[0].episode_id
                groups[episode_id].append(traj_idx)
                episode_returns.append(sum(s.reward + s.cognitive_reward for s in traj))
            else:
                episode_returns.append(0.0)

        # Normalize within groups
        advantages = [0.0] * len(trajectories)

        for group_indices in groups.values():
            if len(group_indices) <= 1:
                continue

            group_returns = [episode_returns[i] for i in group_indices]
            mean_return = sum(group_returns) / len(group_returns)

            if self.config.mode == "mean_norm":
                for idx in group_indices:
                    advantages[idx] = episode_returns[idx] - mean_return
            else:
                std_return = math.sqrt(
                    sum((r - mean_return) ** 2 for r in group_returns)
                    / len(group_returns)
                )
                for idx in group_indices:
                    advantages[idx] = (episode_returns[idx] - mean_return) / (
                        std_return + self.config.epsilon
                    )

        return advantages

    def _compute_step_advantage(
        self,
        all_steps: List[TrajectoryStep],
        traj_boundaries: List[Tuple[int, int]],
    ) -> List[float]:
        """
        Compute step-level advantage using GiGPO-style grouping.

        Groups steps by their cognitive state hash (anchor observation).
        Steps with the same AtomSpace fingerprint are in the same group.
        """
        # Build step groups by state hash
        groups: Dict[str, List[int]] = defaultdict(list)

        for idx, step in enumerate(all_steps):
            if step.active:
                groups[step.state_hash].append(idx)

        # Compute step rewards
        step_rewards = [s.reward + s.cognitive_reward for s in all_steps]

        # Normalize within groups
        advantages = [0.0] * len(all_steps)

        for group_indices in groups.values():
            if len(group_indices) <= 1:
                # Single-element group: advantage is the reward minus global mean
                if group_indices:
                    advantages[group_indices[0]] = step_rewards[group_indices[0]]
                continue

            group_rewards = [step_rewards[i] for i in group_indices]
            mean_reward = sum(group_rewards) / len(group_rewards)

            if self.config.mode == "mean_norm":
                for idx in group_indices:
                    advantages[idx] = step_rewards[idx] - mean_reward
            else:
                std_reward = math.sqrt(
                    sum((r - mean_reward) ** 2 for r in group_rewards)
                    / len(group_rewards)
                )
                for idx in group_indices:
                    advantages[idx] = (step_rewards[idx] - mean_reward) / (
                        std_reward + self.config.epsilon
                    )

        return advantages

    def _compute_cognitive_bonus(
        self,
        all_steps: List[TrajectoryStep],
        traj_boundaries: List[Tuple[int, int]],
    ) -> List[float]:
        """
        Compute cognitive bonus advantages.

        Rewards steps that improve cognitive quality:
        - Reasoning: More/better inferences
        - Attention: Effective focus allocation
        - Coherence: Better knowledge structure
        """
        bonuses = [0.0] * len(all_steps)

        for start, end in traj_boundaries:
            traj_steps = all_steps[start:end]

            for i, step in enumerate(traj_steps):
                bonus = 0.0

                # Reasoning bonus
                if step.num_inferences > 0:
                    # Reward for making inferences
                    bonus += self.config.reasoning_bonus_weight * min(
                        1.0, step.num_inferences / 5.0
                    )

                # Attention bonus
                if step.attention_sti > 0:
                    bonus += self.config.attention_bonus_weight * min(
                        1.0, step.attention_sti
                    )

                # Coherence bonus
                if step.coherence > 0:
                    bonus += self.config.coherence_bonus_weight * step.coherence

                # Growth bonus (diminishing)
                if i > 0:
                    atom_growth = step.num_atoms - traj_steps[i - 1].num_atoms
                    if atom_growth > 0:
                        bonus += 0.05 * math.log1p(atom_growth)

                bonuses[start + i] = bonus

        return bonuses

    def _normalize(self, advantages: List[List[float]]) -> List[List[float]]:
        """Normalize advantages across all trajectories."""
        # Flatten
        all_values = [v for traj in advantages for v in traj]

        if not all_values:
            return advantages

        mean = sum(all_values) / len(all_values)
        var = sum((v - mean) ** 2 for v in all_values) / len(all_values)
        std = math.sqrt(var + self.config.epsilon)

        # Normalize
        normalized = []
        for traj in advantages:
            normalized.append([(v - mean) / std for v in traj])

        return normalized

    @staticmethod
    def state_fingerprint(metrics: Dict[str, Any]) -> str:
        """
        Create a fingerprint of the cognitive state.

        Used as anchor observation for GiGPO step-level grouping.
        Two states with the same fingerprint are considered equivalent.
        """
        # Quantize metrics to create equivalence classes
        quantized = {
            "atoms_bucket": metrics.get("num_atoms", 0) // 10,
            "inference_bucket": metrics.get("total_inferences", 0) // 5,
            "sti_bucket": round(metrics.get("total_sti", 0), 1),
        }

        state_str = json.dumps(quantized, sort_keys=True)
        return hashlib.md5(state_str.encode()).hexdigest()[:12]
