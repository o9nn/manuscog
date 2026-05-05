"""
ManusCog Reinforcement Learning Module
=======================================

Integrates OpenManus-RL reinforcement learning capabilities with
the manuscog cognitive architecture.

Components:
    - environments: Cognitive environment wrapping AtomSpace
    - rewards: Cognitive reward manager with multi-signal rewards
    - memory: AtomSpace-backed RL memory system
    - algorithms: Cognitive advantage computation (GiGPO-inspired)
    - rollout: Multi-turn cognitive rollout loop
    - training: End-to-end cognitive RL trainer
"""

from rl.algorithms.cognitive_advantage import (
    AdvantageConfig,
    CognitiveAdvantageComputer,
    TrajectoryStep,
)
from rl.environments.cognitive_env import (
    ActionSpec,
    CognitiveAction,
    CognitiveEnvironment,
    CognitiveObservation,
    VectorizedCognitiveEnv,
)
from rl.memory.cognitive_memory import CognitiveMemory, MemoryRecord
from rl.rewards.cognitive_rewards import (
    CognitiveRewardManager,
    RewardBreakdown,
    RewardConfig,
)
from rl.rollout.cognitive_rollout import CognitiveRollout, RolloutConfig
from rl.training.cognitive_trainer import (
    CognitiveRLTrainer,
    TabularQPolicy,
    TrainerConfig,
)


__all__ = [
    # Environment
    "CognitiveEnvironment",
    "CognitiveObservation",
    "CognitiveAction",
    "ActionSpec",
    "VectorizedCognitiveEnv",
    # Rewards
    "CognitiveRewardManager",
    "RewardConfig",
    "RewardBreakdown",
    # Memory
    "CognitiveMemory",
    "MemoryRecord",
    # Algorithms
    "CognitiveAdvantageComputer",
    "AdvantageConfig",
    "TrajectoryStep",
    # Rollout
    "CognitiveRollout",
    "RolloutConfig",
    # Training
    "CognitiveRLTrainer",
    "TrainerConfig",
    "TabularQPolicy",
]
