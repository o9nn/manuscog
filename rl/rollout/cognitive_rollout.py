"""
Cognitive Rollout
=================

Multi-turn rollout loop that integrates cognitive operations into
the RL training cycle. Inspired by OpenManus-RL's modular stages
but with cognitive subsystems driving each stage.

Cognitive Cycle:
    1. PERCEIVE  → Observe AtomSpace state
    2. PLAN      → PLN forward chaining for action selection
    3. ACT       → Execute cognitive action
    4. REFLECT   → Autognosis self-monitoring
    5. LEARN     → Update memory and attention
    6. RECORD    → Store trajectory for training

This maps to OpenManus-RL's stages:
    Planning → PLN reasoning
    Action   → Cognitive action execution
    Memory   → AtomSpace persistence
    Reflection → Autognosis
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from rl.algorithms.cognitive_advantage import CognitiveAdvantageComputer, TrajectoryStep
from rl.environments.cognitive_env import (
    ActionSpec,
    CognitiveAction,
    CognitiveEnvironment,
    CognitiveObservation,
)
from rl.memory.cognitive_memory import CognitiveMemory, MemoryRecord
from rl.rewards.cognitive_rewards import CognitiveRewardManager, RewardConfig


@dataclass
class RolloutConfig:
    """Configuration for cognitive rollout."""

    max_turns: int = 20
    max_episodes: int = 100

    # Environment
    env_config: Dict[str, Any] = field(default_factory=dict)

    # Memory
    memory_history_length: int = 10
    memory_strategy: str = "mixed"

    # Reward
    reward_config: Optional[RewardConfig] = None

    # Policy
    exploration_rate: float = 0.3  # Epsilon for exploration
    exploration_decay: float = 0.995
    min_exploration: float = 0.05

    # Logging
    log_interval: int = 10
    verbose: bool = True


class CognitiveRollout:
    """
    Orchestrates cognitive RL rollouts.

    Manages the interaction loop between an agent policy and
    the cognitive environment, collecting trajectories for training.
    """

    def __init__(self, config: Optional[RolloutConfig] = None):
        self.config = config or RolloutConfig()

        # Components
        self.env = CognitiveEnvironment(self.config.env_config)
        self.reward_manager = CognitiveRewardManager(self.config.reward_config)
        self.memory = CognitiveMemory()
        self.advantage_computer = CognitiveAdvantageComputer()

        # Policy (can be set externally)
        self._policy: Optional[Callable] = None

        # Tracking
        self.total_episodes = 0
        self.total_steps = 0
        self.episode_rewards: List[float] = []
        self.trajectories: List[List[TrajectoryStep]] = []

    def set_policy(self, policy: Callable[[CognitiveObservation, str], ActionSpec]):
        """
        Set the agent policy.

        Args:
            policy: Function that takes (observation, memory_context)
                    and returns an ActionSpec.
        """
        self._policy = policy

    def run_episode(
        self,
        goals: Optional[List[Dict[str, Any]]] = None,
        policy: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Run a single episode.

        Args:
            goals: Optional goals for this episode.
            policy: Optional policy override.

        Returns:
            Episode summary with trajectory and metrics.
        """
        active_policy = policy or self._policy
        if active_policy is None:
            active_policy = self._default_policy

        # Reset
        obs = self.env.reset(goals)
        self.memory.reset()
        self.reward_manager.reset_episode()

        traj_uid = str(uuid.uuid4())[:8]
        episode_id = f"ep_{self.total_episodes}"
        trajectory: List[TrajectoryStep] = []

        done = False
        step = 0
        prev_metrics = self.env._get_metrics()

        while not done and step < self.config.max_turns:
            step += 1

            # 1. PERCEIVE: Get observation
            memory_context, _ = self.memory.fetch(
                history_length=self.config.memory_history_length,
                strategy=self.config.memory_strategy,
            )
            context = memory_context[0] if memory_context else ""

            # 2. PLAN + ACT: Get action from policy
            action = active_policy(obs, context)

            # 3. Execute action
            new_obs, env_reward, done, info = self.env.step(action)

            # 4. Calculate cognitive reward
            curr_metrics = self.env._get_metrics()
            reward_breakdown = self.reward_manager.calculate_step_reward(
                prev_metrics=prev_metrics,
                curr_metrics=curr_metrics,
                action_result=info.get("action_result", {}),
                goal_progress=info.get("goal_progress", 0.0),
            )

            # 5. REFLECT + LEARN: Store in memory
            record = MemoryRecord(
                step=step,
                episode=self.total_episodes,
                timestamp=time.time(),
                action=action.action.value,
                observation=new_obs.text,
                reward=reward_breakdown.total,
            )
            self.memory.store(record)

            # 6. RECORD: Build trajectory step
            traj_step = TrajectoryStep(
                step_id=step,
                episode_id=episode_id,
                traj_uid=traj_uid,
                state_hash=new_obs.state_hash,
                observation_text=new_obs.text,
                action=action.action.value,
                action_type=action.action.value,
                reward=env_reward,
                cognitive_reward=reward_breakdown.total - env_reward,
                num_atoms=new_obs.num_atoms,
                num_inferences=new_obs.total_inferences,
                attention_sti=new_obs.total_sti,
                coherence=0.0,
                active=True,
                done=done,
            )
            trajectory.append(traj_step)

            # Update state
            obs = new_obs
            prev_metrics = curr_metrics

        # Episode complete
        self.total_episodes += 1
        self.total_steps += step

        episode_reward = self.reward_manager.calculate_episode_reward(
            episode_metrics=self.env._get_metrics(),
            goal_achieved=info.get("goal_achieved", False),
        )
        self.episode_rewards.append(episode_reward)
        self.trajectories.append(trajectory)

        # Record successful procedures
        if info.get("goal_achieved", False):
            actions = [s.action for s in trajectory]
            self.memory.record_procedure(actions, episode_reward)

        summary = {
            "episode": self.total_episodes,
            "steps": step,
            "episode_reward": episode_reward,
            "goal_achieved": info.get("goal_achieved", False),
            "trajectory_length": len(trajectory),
            "reward_stats": self.reward_manager.get_episode_stats(),
            "memory_stats": self.memory.get_stats(),
            "env_summary": self.env.get_episode_summary(),
        }

        if self.config.verbose and self.total_episodes % self.config.log_interval == 0:
            self._log_episode(summary)

        return summary

    def run_batch(
        self,
        num_episodes: int,
        goals_per_episode: Optional[List[List[Dict[str, Any]]]] = None,
        policy: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Run a batch of episodes.

        Args:
            num_episodes: Number of episodes to run.
            goals_per_episode: Optional goals for each episode.
            policy: Optional policy override.

        Returns:
            Batch summary with aggregated metrics.
        """
        summaries = []

        for i in range(num_episodes):
            goals = goals_per_episode[i] if goals_per_episode else None
            summary = self.run_episode(goals=goals, policy=policy)
            summaries.append(summary)

        # Compute advantages
        recent_trajectories = self.trajectories[-num_episodes:]
        advantages = self.advantage_computer.compute_advantages(recent_trajectories)

        batch_summary = {
            "num_episodes": num_episodes,
            "total_steps": sum(s["steps"] for s in summaries),
            "mean_reward": sum(s["episode_reward"] for s in summaries) / num_episodes,
            "max_reward": max(s["episode_reward"] for s in summaries),
            "min_reward": min(s["episode_reward"] for s in summaries),
            "goals_achieved": sum(1 for s in summaries if s["goal_achieved"]),
            "success_rate": sum(1 for s in summaries if s["goal_achieved"])
            / num_episodes,
            "advantages_computed": len(advantages),
        }

        return batch_summary

    def _default_policy(self, obs: CognitiveObservation, context: str) -> ActionSpec:
        """
        Default exploration policy.

        Uses a simple heuristic strategy:
        1. If few atoms: add concepts
        2. If atoms but few inferences: reason
        3. If inferences but no focus: focus attention
        4. Otherwise: explore randomly
        """
        import random

        # Exploration
        if random.random() < self.config.exploration_rate:
            action = random.choice(list(CognitiveAction))
            params = {}

            if action == CognitiveAction.ADD_CONCEPT:
                concepts = [
                    "Python",
                    "AI",
                    "Machine Learning",
                    "Data Science",
                    "Neural Networks",
                    "Deep Learning",
                    "NLP",
                    "Computer Vision",
                    "Robotics",
                    "Algorithms",
                    "Mathematics",
                    "Statistics",
                    "TensorFlow",
                    "PyTorch",
                    "Transformers",
                    "Attention",
                ]
                params["concept"] = random.choice(concepts)
            elif action == CognitiveAction.ADD_RELATIONSHIP:
                relationships = [
                    ("Python", "Programming Language"),
                    ("Machine Learning", "AI"),
                    ("Deep Learning", "Machine Learning"),
                    ("Neural Networks", "Deep Learning"),
                    ("NLP", "AI"),
                    ("Computer Vision", "AI"),
                    ("TensorFlow", "ML Framework"),
                    ("PyTorch", "ML Framework"),
                    ("Transformers", "Neural Networks"),
                ]
                child, parent = random.choice(relationships)
                params["child"] = child
                params["parent"] = parent
            elif action == CognitiveAction.FOCUS_ATTENTION:
                concepts = ["AI", "Machine Learning", "Python", "Deep Learning"]
                params["concept"] = random.choice(concepts)
            elif action in (
                CognitiveAction.REASON_DEDUCTION,
                CognitiveAction.REASON_INDUCTION,
                CognitiveAction.REASON_ABDUCTION,
            ):
                params["max_inferences"] = random.randint(3, 10)

            return ActionSpec(action=action, params=params)

        # Heuristic policy
        if obs.num_atoms < 40:
            # Build knowledge base
            concepts = ["Python", "AI", "Machine Learning", "Data Science"]
            import random

            return ActionSpec(
                action=CognitiveAction.ADD_CONCEPT,
                params={"concept": random.choice(concepts)},
            )
        elif obs.total_inferences < 5:
            return ActionSpec(
                action=CognitiveAction.REASON_DEDUCTION, params={"max_inferences": 5}
            )
        elif obs.total_sti < 0.1:
            return ActionSpec(
                action=CognitiveAction.FOCUS_ATTENTION, params={"concept": "AI"}
            )
        else:
            return ActionSpec(action=CognitiveAction.REFLECT, params={})

    def _log_episode(self, summary: Dict[str, Any]):
        """Log episode summary."""
        print(
            f"  Episode {summary['episode']:4d} | "
            f"Steps: {summary['steps']:3d} | "
            f"Reward: {summary['episode_reward']:7.2f} | "
            f"Goal: {'✓' if summary['goal_achieved'] else '✗'}"
        )

    def get_training_data(self, last_n: int = 10) -> Dict[str, Any]:
        """
        Get training data from recent trajectories.

        Returns data in a format compatible with RL training loops.
        """
        recent = self.trajectories[-last_n:]
        advantages = self.advantage_computer.compute_advantages(recent)

        return {
            "trajectories": recent,
            "advantages": advantages,
            "episode_rewards": self.episode_rewards[-last_n:],
            "total_episodes": self.total_episodes,
            "total_steps": self.total_steps,
        }

    def close(self):
        """Clean up resources."""
        self.env.close()
