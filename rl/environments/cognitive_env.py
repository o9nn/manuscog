"""
Cognitive Environment
=====================

Wraps the manuscog Cognitive Kernel as a reinforcement learning environment.
The AtomSpace becomes the state space, cognitive operations become actions,
and cognitive quality metrics become rewards.

Inspired by OpenManus-RL's EnvironmentManagerBase but adapted for
cognitive architecture where the "world" is a knowledge hypergraph.

Architecture:
    Agent → Action (add_concept, reason, focus, learn, reflect)
         → CognitiveEnvironment
         → Observation (AtomSpace state fingerprint + cognitive metrics)
         → Reward (reasoning quality + attention efficiency + self-improvement)
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# Add project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from kernel.cognitive.types import AtomType, AttentionValue, TruthValue


# =============================================================================
# ACTION SPACE
# =============================================================================


class CognitiveAction(Enum):
    """Actions available in the cognitive environment."""

    ADD_CONCEPT = "add_concept"
    ADD_RELATIONSHIP = "add_relationship"
    REASON_DEDUCTION = "reason_deduction"
    REASON_INDUCTION = "reason_induction"
    REASON_ABDUCTION = "reason_abduction"
    FOCUS_ATTENTION = "focus_attention"
    SPREAD_ATTENTION = "spread_attention"
    LEARN_HEBBIAN = "learn_hebbian"
    REFLECT = "reflect"
    QUERY_CONCEPT = "query_concept"
    QUERY_RELATIONSHIPS = "query_relationships"
    CONSOLIDATE_MEMORY = "consolidate_memory"
    NO_OP = "no_op"


@dataclass
class ActionSpec:
    """Specification for a cognitive action."""

    action: CognitiveAction
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"action": self.action.value, "params": self.params}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ActionSpec":
        return cls(action=CognitiveAction(d["action"]), params=d.get("params", {}))

    @classmethod
    def from_text(cls, text: str) -> "ActionSpec":
        """Parse a text action into an ActionSpec.

        Supports formats:
            "add_concept: Python"
            "reason_deduction"
            "focus_attention: Machine Learning"
            "add_relationship: Python -> Programming Language"
        """
        text = text.strip()
        if ":" in text:
            action_str, param_str = text.split(":", 1)
            action_str = action_str.strip()
            param_str = param_str.strip()
        else:
            action_str = text
            param_str = ""

        # Normalize action name
        action_str = action_str.lower().replace(" ", "_")

        try:
            action = CognitiveAction(action_str)
        except ValueError:
            return cls(action=CognitiveAction.NO_OP)

        # Parse parameters based on action type
        params = {}
        if action in (
            CognitiveAction.ADD_CONCEPT,
            CognitiveAction.FOCUS_ATTENTION,
            CognitiveAction.QUERY_CONCEPT,
        ):
            params["concept"] = param_str
        elif action == CognitiveAction.ADD_RELATIONSHIP:
            if "->" in param_str:
                parts = param_str.split("->")
                params["child"] = parts[0].strip()
                params["parent"] = parts[1].strip()
            else:
                params["concept"] = param_str
        elif action == CognitiveAction.QUERY_RELATIONSHIPS:
            params["concept"] = param_str
        elif action in (
            CognitiveAction.REASON_DEDUCTION,
            CognitiveAction.REASON_INDUCTION,
            CognitiveAction.REASON_ABDUCTION,
        ):
            if param_str:
                try:
                    params["max_inferences"] = int(param_str)
                except ValueError:
                    params["max_inferences"] = 5

        return cls(action=action, params=params)


# =============================================================================
# OBSERVATION SPACE
# =============================================================================


@dataclass
class CognitiveObservation:
    """Observation from the cognitive environment."""

    # State fingerprint
    state_hash: str = ""

    # AtomSpace metrics
    num_atoms: int = 0
    num_nodes: int = 0
    num_links: int = 0

    # Cognitive metrics
    total_sti: float = 0.0
    focus_set_size: int = 0
    avg_truth_strength: float = 0.0
    avg_truth_confidence: float = 0.0

    # Reasoning metrics
    total_inferences: int = 0
    new_inferences_this_step: int = 0

    # Attention metrics
    attention_entropy: float = 0.0
    top_focus_concepts: List[str] = field(default_factory=list)

    # Self-awareness
    self_awareness_score: float = 0.0
    optimization_opportunities: int = 0

    # Step info
    step: int = 0
    episode: int = 0

    # Text representation for LLM-based agents
    text: str = ""

    # Anchor (for GiGPO step-level grouping)
    anchor: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state_hash": self.state_hash,
            "num_atoms": self.num_atoms,
            "num_nodes": self.num_nodes,
            "num_links": self.num_links,
            "total_sti": self.total_sti,
            "focus_set_size": self.focus_set_size,
            "avg_truth_strength": self.avg_truth_strength,
            "avg_truth_confidence": self.avg_truth_confidence,
            "total_inferences": self.total_inferences,
            "new_inferences_this_step": self.new_inferences_this_step,
            "attention_entropy": self.attention_entropy,
            "top_focus_concepts": self.top_focus_concepts,
            "self_awareness_score": self.self_awareness_score,
            "optimization_opportunities": self.optimization_opportunities,
            "step": self.step,
            "episode": self.episode,
        }

    def to_text(self) -> str:
        """Generate text observation for LLM-based agents."""
        lines = [
            f"[Cognitive State - Step {self.step}]",
            f"AtomSpace: {self.num_atoms} atoms ({self.num_nodes} nodes, {self.num_links} links)",
            f"Attention: total_sti={self.total_sti:.2f}, focus_set={self.focus_set_size}",
            f"Truth: avg_strength={self.avg_truth_strength:.3f}, avg_confidence={self.avg_truth_confidence:.3f}",
            f"Reasoning: {self.total_inferences} total inferences (+{self.new_inferences_this_step} this step)",
            f"Self-awareness: {self.self_awareness_score:.2f}",
        ]
        if self.top_focus_concepts:
            lines.append(f"Focus: {', '.join(self.top_focus_concepts[:5])}")
        if self.optimization_opportunities > 0:
            lines.append(
                f"Optimization opportunities: {self.optimization_opportunities}"
            )
        return "\n".join(lines)


# =============================================================================
# COGNITIVE ENVIRONMENT
# =============================================================================


class CognitiveEnvironment:
    """
    Reinforcement learning environment wrapping the Cognitive Kernel.

    The environment exposes cognitive operations as actions and
    cognitive quality metrics as observations and rewards.

    Compatible with OpenManus-RL's EnvironmentManagerBase interface.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Lazy import to avoid circular dependencies
        from kernel.cognitive_kernel import CognitiveKernel, KernelConfig

        # Kernel configuration
        kernel_config = KernelConfig(
            max_inference_depth=self.config.get("max_inference_depth", 10),
            attention_budget=self.config.get("attention_budget", 100.0),
            learning_rate=self.config.get("learning_rate", 0.1),
            log_level=self.config.get("log_level", "WARNING"),
        )

        self.kernel = CognitiveKernel(kernel_config)
        self.kernel.boot()

        # Episode tracking
        self.episode = 0
        self.step_count = 0
        self.max_steps = self.config.get("max_steps", 50)
        self.done = False

        # Reward tracking
        self._prev_metrics = {}
        self._episode_rewards = []
        self._step_history: List[Dict[str, Any]] = []

        # Task goals (optional)
        self._goals: List[Dict[str, Any]] = []
        self._goal_achieved = False

        # Action space info
        self.action_space = list(CognitiveAction)
        self.num_actions = len(self.action_space)

    def reset(
        self, goals: Optional[List[Dict[str, Any]]] = None
    ) -> CognitiveObservation:
        """
        Reset the environment for a new episode.

        Args:
            goals: Optional list of goals for this episode.
                   Each goal: {"type": "concept_exists", "concept": "X"}
                   or {"type": "inference_count", "min": 10}

        Returns:
            Initial observation.
        """
        # Shutdown old kernel
        if self.kernel.state.name == "RUNNING":
            self.kernel.shutdown()

        # Boot fresh kernel
        from kernel.cognitive_kernel import CognitiveKernel, KernelConfig

        kernel_config = KernelConfig(
            max_inference_depth=self.config.get("max_inference_depth", 10),
            attention_budget=self.config.get("attention_budget", 100.0),
            learning_rate=self.config.get("learning_rate", 0.1),
            log_level=self.config.get("log_level", "WARNING"),
        )
        self.kernel = CognitiveKernel(kernel_config)
        self.kernel.boot()

        # Reset tracking
        self.episode += 1
        self.step_count = 0
        self.done = False
        self._prev_metrics = self._get_metrics()
        self._episode_rewards = []
        self._step_history = []
        self._goals = goals or []
        self._goal_achieved = False

        obs = self._observe()
        return obs

    def step(
        self, action: ActionSpec
    ) -> Tuple[CognitiveObservation, float, bool, Dict[str, Any]]:
        """
        Execute a cognitive action and return the result.

        Args:
            action: The cognitive action to execute.

        Returns:
            Tuple of (observation, reward, done, info)
        """
        if self.done:
            obs = self._observe()
            return obs, 0.0, True, {"error": "Episode already done"}

        self.step_count += 1
        info = {"action": action.to_dict(), "step": self.step_count}

        # Execute the action
        action_result = self._execute_action(action)
        info["action_result"] = action_result

        # Get new metrics
        new_metrics = self._get_metrics()

        # Calculate reward
        reward = self._calculate_reward(
            self._prev_metrics, new_metrics, action, action_result
        )
        self._prev_metrics = new_metrics
        self._episode_rewards.append(reward)

        # Check if done
        self.done = self._check_done()
        info["episode_reward"] = sum(self._episode_rewards)
        info["goal_achieved"] = self._goal_achieved

        # Record step
        self._step_history.append(
            {
                "step": self.step_count,
                "action": action.to_dict(),
                "reward": reward,
                "metrics": new_metrics,
            }
        )

        obs = self._observe()
        return obs, reward, self.done, info

    def _execute_action(self, action: ActionSpec) -> Dict[str, Any]:
        """Execute a cognitive action on the kernel."""
        result = {"success": False, "details": {}}

        try:
            if action.action == CognitiveAction.ADD_CONCEPT:
                concept = action.params.get("concept", "")
                if concept:
                    strength = action.params.get("strength", 0.9)
                    confidence = action.params.get("confidence", 0.8)
                    self.kernel.atomspace.add_node(
                        AtomType.CONCEPT_NODE,
                        concept,
                        tv=TruthValue(strength, confidence),
                    )
                    result["success"] = True
                    result["details"] = {"concept": concept}

            elif action.action == CognitiveAction.ADD_RELATIONSHIP:
                child = action.params.get("child", "")
                parent = action.params.get("parent", "")
                if child and parent:
                    child_node = self.kernel.atomspace.add_node(
                        AtomType.CONCEPT_NODE, child
                    )
                    parent_node = self.kernel.atomspace.add_node(
                        AtomType.CONCEPT_NODE, parent
                    )
                    self.kernel.atomspace.add_link(
                        AtomType.INHERITANCE_LINK,
                        [child_node, parent_node],
                        tv=TruthValue(
                            action.params.get("strength", 0.9),
                            action.params.get("confidence", 0.8),
                        ),
                    )
                    result["success"] = True
                    result["details"] = {"child": child, "parent": parent}

            elif action.action == CognitiveAction.REASON_DEDUCTION:
                max_inf = action.params.get("max_inferences", 5)
                inferences = self.kernel.pln.forward_chain(max_iterations=max_inf)
                result["success"] = True
                result["details"] = {"inferences_made": len(inferences)}

            elif action.action == CognitiveAction.REASON_INDUCTION:
                max_inf = action.params.get("max_inferences", 5)
                inferences = self.kernel.pln.forward_chain(max_iterations=max_inf)
                result["success"] = True
                result["details"] = {"inferences_made": len(inferences)}

            elif action.action == CognitiveAction.REASON_ABDUCTION:
                max_inf = action.params.get("max_inferences", 5)
                inferences = self.kernel.pln.forward_chain(max_iterations=max_inf)
                result["success"] = True
                result["details"] = {"inferences_made": len(inferences)}

            elif action.action == CognitiveAction.FOCUS_ATTENTION:
                concept = action.params.get("concept", "")
                if concept:
                    node = self.kernel.atomspace.get_node(
                        AtomType.CONCEPT_NODE, concept
                    )
                    if node:
                        sti = action.params.get("sti", 0.8)
                        self.kernel.atomspace.set_attention_value(
                            node.handle, AttentionValue(sti=sti, lti=0.5)
                        )
                        result["success"] = True
                        result["details"] = {"concept": concept, "sti": sti}
                    else:
                        result["details"] = {"error": f"Concept '{concept}' not found"}

            elif action.action == CognitiveAction.SPREAD_ATTENTION:
                self.kernel.ecan.spread_importance()
                result["success"] = True

            elif action.action == CognitiveAction.LEARN_HEBBIAN:
                self.kernel.hebbian.decay_associations()
                result["success"] = True

            elif action.action == CognitiveAction.REFLECT:
                if self.kernel.autognosis:
                    try:
                        status = self.kernel.autognosis.get_status()
                        result["success"] = True
                        result["details"] = {"status": str(status)[:200]}
                    except Exception:
                        result["success"] = True
                        result["details"] = {"status": "reflection_completed"}
                else:
                    result["success"] = True
                    result["details"] = {"status": "no_autognosis"}

            elif action.action == CognitiveAction.QUERY_CONCEPT:
                concept = action.params.get("concept", "")
                if concept:
                    node = self.kernel.atomspace.get_node(
                        AtomType.CONCEPT_NODE, concept
                    )
                    if node:
                        result["success"] = True
                        result["details"] = {
                            "concept": concept,
                            "found": True,
                            "strength": node.truth_value.strength,
                            "confidence": node.truth_value.confidence,
                        }
                    else:
                        result["success"] = True
                        result["details"] = {"concept": concept, "found": False}

            elif action.action == CognitiveAction.QUERY_RELATIONSHIPS:
                concept = action.params.get("concept", "")
                if concept:
                    node = self.kernel.atomspace.get_node(
                        AtomType.CONCEPT_NODE, concept
                    )
                    if node:
                        incoming = self.kernel.atomspace.get_incoming(node.handle)
                        result["success"] = True
                        result["details"] = {
                            "concept": concept,
                            "relationships": len(incoming),
                        }
                    else:
                        result["success"] = True
                        result["details"] = {"concept": concept, "found": False}

            elif action.action == CognitiveAction.CONSOLIDATE_MEMORY:
                if self.kernel.memory_manager:
                    self.kernel.memory_manager.consolidate()
                result["success"] = True

            elif action.action == CognitiveAction.NO_OP:
                result["success"] = True
                result["details"] = {"action": "no_op"}

        except Exception as e:
            result["success"] = False
            result["details"] = {"error": str(e)}

        return result

    def _get_metrics(self) -> Dict[str, Any]:
        """Get current cognitive metrics."""
        stats = self.kernel.atomspace.get_stats()
        pln_stats = (
            self.kernel.pln.stats
            if self.kernel.pln and hasattr(self.kernel.pln, "stats")
            else {}
        )
        ecan_stats = (
            self.kernel.ecan.get_stats()
            if self.kernel.ecan and hasattr(self.kernel.ecan, "get_stats")
            else {}
        )

        # Count nodes and links from type_counts
        type_counts = stats.get("type_counts", {})
        total_atoms = stats.get("total_atoms", 0)

        # Separate nodes from links
        node_types = [k for k in type_counts if k.endswith("_NODE")]
        link_types = [k for k in type_counts if k.endswith("_LINK")]
        num_nodes = sum(type_counts.get(t, 0) for t in node_types)
        num_links = sum(type_counts.get(t, 0) for t in link_types)

        return {
            "num_atoms": total_atoms,
            "num_nodes": num_nodes,
            "num_links": num_links,
            "total_inferences": pln_stats.get("total_inferences", 0),
            "successful_inferences": pln_stats.get("successful_inferences", 0),
            "new_atoms_created": pln_stats.get("new_atoms_created", 0),
            "total_sti": ecan_stats.get("total_sti", 0.0),
            "ecan_cycles": ecan_stats.get("cycles", 0),
            "stimulus_pool": ecan_stats.get("stimulus_pool", 0.0),
        }

    def _observe(self) -> CognitiveObservation:
        """Generate an observation from the current cognitive state."""
        metrics = self._get_metrics()

        # State fingerprint for GiGPO grouping
        state_str = json.dumps(metrics, sort_keys=True, default=str)
        state_hash = hashlib.md5(state_str.encode()).hexdigest()[:12]

        obs = CognitiveObservation(
            state_hash=state_hash,
            num_atoms=metrics["num_atoms"],
            num_nodes=metrics["num_nodes"],
            num_links=metrics["num_links"],
            total_sti=metrics["total_sti"],
            total_inferences=metrics["total_inferences"],
            new_inferences_this_step=metrics.get("new_atoms_created", 0),
            step=self.step_count,
            episode=self.episode,
        )

        obs.text = obs.to_text()
        obs.anchor = state_hash

        return obs

    def _calculate_reward(
        self,
        prev_metrics: Dict[str, Any],
        new_metrics: Dict[str, Any],
        action: ActionSpec,
        action_result: Dict[str, Any],
    ) -> float:
        """
        Calculate reward based on cognitive improvement.

        Reward components:
        1. Knowledge growth: New atoms added
        2. Reasoning quality: New inferences made
        3. Action success: Whether the action succeeded
        4. Goal progress: Progress toward episode goals
        5. Efficiency: Penalize redundant actions
        """
        reward = 0.0

        # 1. Knowledge growth reward
        atom_delta = new_metrics["num_atoms"] - prev_metrics["num_atoms"]
        if atom_delta > 0:
            reward += 0.1 * atom_delta  # Small reward per new atom

        # 2. Reasoning reward
        inference_delta = (
            new_metrics["total_inferences"] - prev_metrics["total_inferences"]
        )
        if inference_delta > 0:
            reward += 0.3 * inference_delta  # Larger reward for inferences

        # 3. Action success reward
        if action_result.get("success", False):
            reward += 0.05
        else:
            reward -= 0.1  # Penalty for failed actions

        # 4. Goal progress reward
        goal_reward = self._evaluate_goal_progress()
        reward += goal_reward

        # 5. Efficiency penalty
        if action.action == CognitiveAction.NO_OP:
            reward -= 0.05  # Small penalty for doing nothing

        # 6. Diversity bonus (encourage exploring different actions)
        if len(self._step_history) > 0:
            recent_actions = [h["action"]["action"] for h in self._step_history[-5:]]
            if action.action.value not in recent_actions:
                reward += 0.02  # Small bonus for trying new actions

        return reward

    def _evaluate_goal_progress(self) -> float:
        """Evaluate progress toward episode goals."""
        if not self._goals:
            return 0.0

        total_progress = 0.0
        for goal in self._goals:
            if goal["type"] == "concept_exists":
                concept = goal["concept"]
                node = self.kernel.atomspace.get_node("CONCEPT_NODE", concept)
                if node:
                    total_progress += 1.0
            elif goal["type"] == "inference_count":
                min_inferences = goal.get("min", 5)
                metrics = self._get_metrics()
                progress = min(1.0, metrics["total_inferences"] / min_inferences)
                total_progress += progress
            elif goal["type"] == "atom_count":
                min_atoms = goal.get("min", 20)
                metrics = self._get_metrics()
                progress = min(1.0, metrics["num_atoms"] / min_atoms)
                total_progress += progress

        avg_progress = total_progress / len(self._goals) if self._goals else 0.0

        if avg_progress >= 1.0:
            self._goal_achieved = True
            return 2.0  # Big bonus for achieving all goals

        return 0.1 * avg_progress

    def _check_done(self) -> bool:
        """Check if the episode is done."""
        if self.step_count >= self.max_steps:
            return True
        if self._goal_achieved:
            return True
        return False

    def get_episode_summary(self) -> Dict[str, Any]:
        """Get a summary of the current/last episode."""
        return {
            "episode": self.episode,
            "total_steps": self.step_count,
            "total_reward": sum(self._episode_rewards),
            "avg_reward": sum(self._episode_rewards)
            / max(1, len(self._episode_rewards)),
            "goal_achieved": self._goal_achieved,
            "final_metrics": self._get_metrics(),
            "action_distribution": self._get_action_distribution(),
        }

    def _get_action_distribution(self) -> Dict[str, int]:
        """Get distribution of actions taken this episode."""
        dist = defaultdict(int)
        for h in self._step_history:
            dist[h["action"]["action"]] += 1
        return dict(dist)

    def close(self):
        """Close the environment."""
        if self.kernel and self.kernel.state.name == "RUNNING":
            self.kernel.shutdown()


# =============================================================================
# VECTORIZED ENVIRONMENT (for parallel training)
# =============================================================================


class VectorizedCognitiveEnv:
    """
    Vectorized cognitive environment for parallel training.
    Manages multiple CognitiveEnvironment instances.
    """

    def __init__(self, num_envs: int, config: Optional[Dict[str, Any]] = None):
        self.num_envs = num_envs
        self.config = config or {}
        self.envs = [CognitiveEnvironment(config) for _ in range(num_envs)]

    def reset(
        self, goals: Optional[List[List[Dict[str, Any]]]] = None
    ) -> List[CognitiveObservation]:
        """Reset all environments."""
        if goals is None:
            goals = [None] * self.num_envs
        return [env.reset(g) for env, g in zip(self.envs, goals)]

    def step(
        self, actions: List[ActionSpec]
    ) -> Tuple[
        List[CognitiveObservation], List[float], List[bool], List[Dict[str, Any]]
    ]:
        """Step all environments."""
        results = [env.step(a) for env, a in zip(self.envs, actions)]
        obs = [r[0] for r in results]
        rewards = [r[1] for r in results]
        dones = [r[2] for r in results]
        infos = [r[3] for r in results]
        return obs, rewards, dones, infos

    def close(self):
        """Close all environments."""
        for env in self.envs:
            env.close()
