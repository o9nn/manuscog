"""
Cognitive RL Trainer
====================

End-to-end training pipeline that combines cognitive rollouts with
policy optimization. This is the main entry point for training
cognitive agents using reinforcement learning.

Training Loop:
    1. Collect trajectories via CognitiveRollout
    2. Compute advantages via CognitiveAdvantageComputer
    3. Update policy (supports multiple strategies)
    4. Evaluate and log progress
    5. Repeat

Policy Strategies:
    - Random: Baseline random exploration
    - Heuristic: Rule-based cognitive strategy
    - Tabular Q: Simple Q-learning on cognitive states
    - Neural: LLM-based policy (requires external model)
"""

from __future__ import annotations
import time
import json
import math
import random
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from rl.rollout.cognitive_rollout import CognitiveRollout, RolloutConfig
from rl.environments.cognitive_env import (
    CognitiveObservation, CognitiveAction, ActionSpec
)
from rl.rewards.cognitive_rewards import RewardConfig
from rl.algorithms.cognitive_advantage import AdvantageConfig


@dataclass
class TrainerConfig:
    """Configuration for the cognitive RL trainer."""
    # Training
    num_epochs: int = 10
    episodes_per_epoch: int = 10
    eval_episodes: int = 5
    eval_interval: int = 2
    
    # Rollout
    rollout_config: Optional[RolloutConfig] = None
    
    # Policy
    policy_type: str = "tabular_q"  # "random", "heuristic", "tabular_q", "neural"
    learning_rate: float = 0.1
    discount_factor: float = 0.99
    
    # Exploration
    initial_exploration: float = 0.5
    exploration_decay: float = 0.95
    min_exploration: float = 0.05
    
    # Goals
    goal_curriculum: bool = True  # Progressively harder goals
    
    # Logging
    log_dir: str = "logs/cognitive_rl"
    verbose: bool = True


class TabularQPolicy:
    """
    Simple tabular Q-learning policy for cognitive actions.
    
    Uses quantized AtomSpace state as the state representation
    and cognitive actions as the action space.
    """
    
    def __init__(self, learning_rate: float = 0.1, discount: float = 0.99):
        self.lr = learning_rate
        self.discount = discount
        self.q_table: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {a.value: 0.0 for a in CognitiveAction}
        )
        self.action_params_cache: Dict[str, Dict[str, Any]] = {}
        self._visit_counts: Dict[str, int] = defaultdict(int)
    
    def select_action(
        self, 
        obs: CognitiveObservation, 
        context: str,
        epsilon: float = 0.1,
    ) -> ActionSpec:
        """Select action using epsilon-greedy Q-learning."""
        state_key = self._state_key(obs)
        self._visit_counts[state_key] += 1
        
        if random.random() < epsilon:
            # Explore
            action = random.choice(list(CognitiveAction))
        else:
            # Exploit
            q_values = self.q_table[state_key]
            best_action_name = max(q_values, key=q_values.get)
            action = CognitiveAction(best_action_name)
        
        # Generate appropriate parameters
        params = self._generate_params(action, obs)
        return ActionSpec(action=action, params=params)
    
    def update(
        self,
        state: CognitiveObservation,
        action: str,
        reward: float,
        next_state: CognitiveObservation,
        done: bool,
    ):
        """Update Q-values using TD learning."""
        state_key = self._state_key(state)
        next_state_key = self._state_key(next_state)
        
        # Current Q-value
        current_q = self.q_table[state_key][action]
        
        # Target Q-value
        if done:
            target = reward
        else:
            next_q_values = self.q_table[next_state_key]
            max_next_q = max(next_q_values.values())
            target = reward + self.discount * max_next_q
        
        # Update
        self.q_table[state_key][action] = (
            current_q + self.lr * (target - current_q)
        )
    
    def _state_key(self, obs: CognitiveObservation) -> str:
        """Create a quantized state key from observation."""
        return (
            f"a{obs.num_atoms // 10}_"
            f"i{obs.total_inferences // 3}_"
            f"s{int(obs.total_sti * 10)}"
        )
    
    def _generate_params(
        self, action: CognitiveAction, obs: CognitiveObservation
    ) -> Dict[str, Any]:
        """Generate appropriate parameters for an action."""
        concepts = [
            "Python", "AI", "Machine Learning", "Data Science",
            "Neural Networks", "Deep Learning", "NLP", "Computer Vision",
            "Robotics", "Algorithms", "TensorFlow", "PyTorch",
        ]
        relationships = [
            ("Python", "Programming Language"),
            ("Machine Learning", "AI"),
            ("Deep Learning", "Machine Learning"),
            ("Neural Networks", "Deep Learning"),
            ("NLP", "AI"),
            ("Computer Vision", "AI"),
            ("TensorFlow", "ML Framework"),
            ("PyTorch", "ML Framework"),
        ]
        
        if action == CognitiveAction.ADD_CONCEPT:
            return {"concept": random.choice(concepts)}
        elif action == CognitiveAction.ADD_RELATIONSHIP:
            child, parent = random.choice(relationships)
            return {"child": child, "parent": parent}
        elif action == CognitiveAction.FOCUS_ATTENTION:
            return {"concept": random.choice(concepts[:4])}
        elif action in (CognitiveAction.REASON_DEDUCTION,
                       CognitiveAction.REASON_INDUCTION,
                       CognitiveAction.REASON_ABDUCTION):
            return {"max_inferences": random.randint(3, 8)}
        else:
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get policy statistics."""
        return {
            "num_states": len(self.q_table),
            "total_visits": sum(self._visit_counts.values()),
            "unique_states_visited": len(self._visit_counts),
        }


class CognitiveRLTrainer:
    """
    Main trainer for cognitive reinforcement learning.
    
    Orchestrates the training loop, managing rollouts, policy updates,
    evaluation, and logging.
    """
    
    def __init__(self, config: Optional[TrainerConfig] = None):
        self.config = config or TrainerConfig()
        
        # Initialize rollout
        rollout_config = self.config.rollout_config or RolloutConfig(
            max_turns=20,
            verbose=False,
        )
        self.rollout = CognitiveRollout(rollout_config)
        
        # Initialize policy
        if self.config.policy_type == "tabular_q":
            self.policy = TabularQPolicy(
                learning_rate=self.config.learning_rate,
                discount=self.config.discount_factor,
            )
        else:
            self.policy = None
        
        # Training state
        self.epoch = 0
        self.exploration_rate = self.config.initial_exploration
        self.training_history: List[Dict[str, Any]] = []
        self.eval_history: List[Dict[str, Any]] = []
    
    def train(self) -> Dict[str, Any]:
        """
        Run the full training loop.
        
        Returns:
            Training summary with metrics.
        """
        print("=" * 60)
        print("  Cognitive RL Training")
        print("=" * 60)
        print(f"  Policy: {self.config.policy_type}")
        print(f"  Epochs: {self.config.num_epochs}")
        print(f"  Episodes/epoch: {self.config.episodes_per_epoch}")
        print(f"  Exploration: {self.exploration_rate:.2f}")
        print("=" * 60)
        
        start_time = time.time()
        
        for epoch in range(self.config.num_epochs):
            self.epoch = epoch + 1
            
            # Generate goals for this epoch
            goals = self._generate_goals(epoch)
            
            # Training episodes
            epoch_metrics = self._train_epoch(goals)
            self.training_history.append(epoch_metrics)
            
            # Evaluation
            if (epoch + 1) % self.config.eval_interval == 0:
                eval_metrics = self._evaluate(goals)
                self.eval_history.append(eval_metrics)
            
            # Decay exploration
            self.exploration_rate = max(
                self.config.min_exploration,
                self.exploration_rate * self.config.exploration_decay
            )
            
            # Log
            if self.config.verbose:
                self._log_epoch(epoch_metrics)
        
        elapsed = time.time() - start_time
        
        summary = {
            "total_epochs": self.config.num_epochs,
            "total_episodes": self.rollout.total_episodes,
            "total_steps": self.rollout.total_steps,
            "training_time": elapsed,
            "final_mean_reward": self.training_history[-1]["mean_reward"] if self.training_history else 0,
            "best_reward": max(h["max_reward"] for h in self.training_history) if self.training_history else 0,
            "final_success_rate": self.training_history[-1].get("success_rate", 0) if self.training_history else 0,
            "policy_stats": self.policy.get_stats() if hasattr(self.policy, "get_stats") else {},
        }
        
        print("\n" + "=" * 60)
        print("  Training Complete!")
        print("=" * 60)
        print(f"  Total time: {elapsed:.1f}s")
        print(f"  Total episodes: {summary['total_episodes']}")
        print(f"  Final mean reward: {summary['final_mean_reward']:.3f}")
        print(f"  Best reward: {summary['best_reward']:.3f}")
        print(f"  Final success rate: {summary['final_success_rate']:.1%}")
        print("=" * 60)
        
        return summary
    
    def _train_epoch(self, goals: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Run training episodes for one epoch."""
        episode_rewards = []
        episode_steps = []
        goals_achieved = 0
        
        for i in range(self.config.episodes_per_epoch):
            ep_goals = goals[i % len(goals)] if goals else None
            
            # Create policy wrapper with current exploration rate
            def policy_fn(obs, context, eps=self.exploration_rate):
                if self.policy and hasattr(self.policy, "select_action"):
                    return self.policy.select_action(obs, context, eps)
                return self.rollout._default_policy(obs, context)
            
            # Run episode
            summary = self.rollout.run_episode(
                goals=ep_goals,
                policy=policy_fn,
            )
            
            episode_rewards.append(summary["episode_reward"])
            episode_steps.append(summary["steps"])
            if summary["goal_achieved"]:
                goals_achieved += 1
            
            # Update policy from trajectory
            if self.policy and hasattr(self.policy, "update"):
                self._update_policy_from_trajectory(
                    self.rollout.trajectories[-1]
                )
        
        return {
            "epoch": self.epoch,
            "mean_reward": sum(episode_rewards) / len(episode_rewards),
            "max_reward": max(episode_rewards),
            "min_reward": min(episode_rewards),
            "mean_steps": sum(episode_steps) / len(episode_steps),
            "goals_achieved": goals_achieved,
            "success_rate": goals_achieved / self.config.episodes_per_epoch,
            "exploration_rate": self.exploration_rate,
        }
    
    def _evaluate(self, goals: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Run evaluation episodes (no exploration)."""
        episode_rewards = []
        goals_achieved = 0
        
        for i in range(self.config.eval_episodes):
            ep_goals = goals[i % len(goals)] if goals else None
            
            def eval_policy(obs, context):
                if self.policy and hasattr(self.policy, "select_action"):
                    return self.policy.select_action(obs, context, epsilon=0.0)
                return self.rollout._default_policy(obs, context)
            
            summary = self.rollout.run_episode(
                goals=ep_goals,
                policy=eval_policy,
            )
            
            episode_rewards.append(summary["episode_reward"])
            if summary["goal_achieved"]:
                goals_achieved += 1
        
        return {
            "epoch": self.epoch,
            "eval_mean_reward": sum(episode_rewards) / len(episode_rewards),
            "eval_success_rate": goals_achieved / self.config.eval_episodes,
        }
    
    def _update_policy_from_trajectory(
        self, trajectory: List[Any]
    ):
        """Update policy using trajectory data."""
        if not trajectory or not hasattr(self.policy, "update"):
            return
        
        for i in range(len(trajectory) - 1):
            step = trajectory[i]
            next_step = trajectory[i + 1]
            
            # Create observation-like objects
            obs = CognitiveObservation(
                num_atoms=step.num_atoms,
                total_inferences=step.num_inferences,
                total_sti=step.attention_sti,
                state_hash=step.state_hash,
            )
            next_obs = CognitiveObservation(
                num_atoms=next_step.num_atoms,
                total_inferences=next_step.num_inferences,
                total_sti=next_step.attention_sti,
                state_hash=next_step.state_hash,
            )
            
            self.policy.update(
                state=obs,
                action=step.action,
                reward=step.reward + step.cognitive_reward,
                next_state=next_obs,
                done=next_step.done,
            )
    
    def _generate_goals(self, epoch: int) -> List[List[Dict[str, Any]]]:
        """Generate goals for an epoch, with optional curriculum."""
        if not self.config.goal_curriculum:
            return [
                [{"type": "inference_count", "min": 5}]
            ] * self.config.episodes_per_epoch
        
        # Curriculum: progressively harder goals
        difficulty = min(1.0, epoch / max(1, self.config.num_epochs - 1))
        
        goals = []
        for _ in range(self.config.episodes_per_epoch):
            episode_goals = []
            
            # Always: build some knowledge
            min_atoms = int(35 + 25 * difficulty)
            episode_goals.append({"type": "atom_count", "min": min_atoms})
            
            # Medium difficulty: require inferences
            if difficulty > 0.3:
                min_inferences = int(3 + 12 * difficulty)
                episode_goals.append({"type": "inference_count", "min": min_inferences})
            
            # Hard: require specific concepts
            if difficulty > 0.6:
                episode_goals.append({"type": "concept_exists", "concept": "AI"})
            
            goals.append(episode_goals)
        
        return goals
    
    def _log_epoch(self, metrics: Dict[str, Any]):
        """Log epoch metrics."""
        print(
            f"  Epoch {metrics['epoch']:3d} | "
            f"Reward: {metrics['mean_reward']:7.3f} "
            f"(max: {metrics['max_reward']:6.2f}) | "
            f"Steps: {metrics['mean_steps']:5.1f} | "
            f"Success: {metrics['success_rate']:5.1%} | "
            f"ε: {metrics['exploration_rate']:.3f}"
        )
    
    def save_results(self, path: str):
        """Save training results to file."""
        results = {
            "config": {
                "num_epochs": self.config.num_epochs,
                "episodes_per_epoch": self.config.episodes_per_epoch,
                "policy_type": self.config.policy_type,
            },
            "training_history": self.training_history,
            "eval_history": self.eval_history,
            "total_episodes": self.rollout.total_episodes,
            "total_steps": self.rollout.total_steps,
        }
        
        with open(path, "w") as f:
            json.dump(results, f, indent=2, default=str)
    
    def close(self):
        """Clean up resources."""
        self.rollout.close()
