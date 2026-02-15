#!/usr/bin/env python3
"""
Cognitive RL Training Demo
===========================

Demonstrates the full cognitive RL training pipeline:
1. Cognitive environment with AtomSpace as state space
2. Multi-signal reward system (reasoning + attention + growth)
3. Tabular Q-learning policy on cognitive states
4. GiGPO-inspired advantage computation
5. Goal curriculum with progressive difficulty

This is the "proof of life" for cognitive reinforcement learning:
an agent that learns to build knowledge, reason, and self-optimize.
"""

import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

import time
import json


def demo_environment():
    """Demo 1: Cognitive Environment basics."""
    print("\n" + "=" * 60)
    print("  Demo 1: Cognitive Environment")
    print("=" * 60)
    
    from rl.environments.cognitive_env import (
        CognitiveEnvironment, CognitiveAction, ActionSpec
    )
    
    env = CognitiveEnvironment({"log_level": "WARNING", "max_steps": 30})
    
    # Reset
    obs = env.reset()
    print(f"\n  Initial state:")
    print(f"    Atoms: {obs.num_atoms}, Inferences: {obs.total_inferences}")
    print(f"    State hash: {obs.state_hash}")
    
    # Take some actions
    actions = [
        ActionSpec(CognitiveAction.ADD_CONCEPT, {"concept": "Python"}),
        ActionSpec(CognitiveAction.ADD_CONCEPT, {"concept": "AI"}),
        ActionSpec(CognitiveAction.ADD_CONCEPT, {"concept": "Machine Learning"}),
        ActionSpec(CognitiveAction.ADD_RELATIONSHIP, {"child": "Python", "parent": "Programming Language"}),
        ActionSpec(CognitiveAction.ADD_RELATIONSHIP, {"child": "Machine Learning", "parent": "AI"}),
        ActionSpec(CognitiveAction.REASON_DEDUCTION, {"max_inferences": 5}),
        ActionSpec(CognitiveAction.FOCUS_ATTENTION, {"concept": "AI", "sti": 0.9}),
        ActionSpec(CognitiveAction.SPREAD_ATTENTION, {}),
        ActionSpec(CognitiveAction.REFLECT, {}),
    ]
    
    total_reward = 0
    for i, action in enumerate(actions):
        obs, reward, done, info = env.step(action)
        total_reward += reward
        print(f"    Step {i+1}: {action.action.value:20s} → reward={reward:+.3f}, "
              f"atoms={obs.num_atoms}, inferences={obs.total_inferences}")
    
    print(f"\n  Total reward: {total_reward:.3f}")
    print(f"  Final state: {obs.num_atoms} atoms, {obs.total_inferences} inferences")
    
    summary = env.get_episode_summary()
    print(f"  Action distribution: {summary['action_distribution']}")
    
    env.close()
    print("  ✓ Environment demo complete")


def demo_reward_system():
    """Demo 2: Cognitive Reward System."""
    print("\n" + "=" * 60)
    print("  Demo 2: Cognitive Reward System")
    print("=" * 60)
    
    from rl.rewards.cognitive_rewards import (
        CognitiveRewardManager, RewardConfig
    )
    
    config = RewardConfig(
        reasoning_weight=0.3,
        attention_weight=0.2,
        growth_weight=0.1,
        normalize_rewards=False,  # Disable for demo clarity
    )
    
    reward_mgr = CognitiveRewardManager(config)
    
    # Simulate some steps
    scenarios = [
        {
            "name": "Add concept",
            "prev": {"num_atoms": 10, "num_nodes": 8, "num_links": 2, 
                     "total_inferences": 0, "successful_inferences": 0,
                     "total_sti": 0, "ecan_cycles": 0, "stimulus_pool": 100,
                     "new_atoms_created": 0},
            "curr": {"num_atoms": 11, "num_nodes": 9, "num_links": 2,
                     "total_inferences": 0, "successful_inferences": 0,
                     "total_sti": 0, "ecan_cycles": 0, "stimulus_pool": 100,
                     "new_atoms_created": 0},
            "result": {"success": True},
        },
        {
            "name": "Successful reasoning",
            "prev": {"num_atoms": 20, "num_nodes": 15, "num_links": 5,
                     "total_inferences": 0, "successful_inferences": 0,
                     "total_sti": 0, "ecan_cycles": 0, "stimulus_pool": 100,
                     "new_atoms_created": 0},
            "curr": {"num_atoms": 23, "num_nodes": 15, "num_links": 8,
                     "total_inferences": 5, "successful_inferences": 4,
                     "total_sti": 0, "ecan_cycles": 0, "stimulus_pool": 100,
                     "new_atoms_created": 3},
            "result": {"success": True},
        },
        {
            "name": "Focus attention",
            "prev": {"num_atoms": 23, "num_nodes": 15, "num_links": 8,
                     "total_inferences": 5, "successful_inferences": 4,
                     "total_sti": 0, "ecan_cycles": 0, "stimulus_pool": 100,
                     "new_atoms_created": 0},
            "curr": {"num_atoms": 23, "num_nodes": 15, "num_links": 8,
                     "total_inferences": 5, "successful_inferences": 4,
                     "total_sti": 0.8, "ecan_cycles": 1, "stimulus_pool": 99.2,
                     "new_atoms_created": 0},
            "result": {"success": True},
        },
        {
            "name": "Failed action",
            "prev": {"num_atoms": 23, "num_nodes": 15, "num_links": 8,
                     "total_inferences": 5, "successful_inferences": 4,
                     "total_sti": 0.8, "ecan_cycles": 1, "stimulus_pool": 99.2,
                     "new_atoms_created": 0},
            "curr": {"num_atoms": 23, "num_nodes": 15, "num_links": 8,
                     "total_inferences": 5, "successful_inferences": 4,
                     "total_sti": 0.8, "ecan_cycles": 1, "stimulus_pool": 99.2,
                     "new_atoms_created": 0},
            "result": {"success": False},
        },
    ]
    
    print(f"\n  {'Scenario':<25} {'Total':>8} {'Task':>8} {'Reason':>8} {'Attn':>8} {'Growth':>8} {'Coher':>8}")
    print("  " + "-" * 85)
    
    for scenario in scenarios:
        breakdown = reward_mgr.calculate_step_reward(
            prev_metrics=scenario["prev"],
            curr_metrics=scenario["curr"],
            action_result=scenario["result"],
        )
        print(f"  {scenario['name']:<25} "
              f"{breakdown.total:>8.3f} "
              f"{breakdown.task:>8.3f} "
              f"{breakdown.reasoning:>8.3f} "
              f"{breakdown.attention:>8.3f} "
              f"{breakdown.growth:>8.3f} "
              f"{breakdown.coherence:>8.3f}")
    
    stats = reward_mgr.get_episode_stats()
    print(f"\n  Episode stats: {stats['num_steps']} steps, "
          f"total={stats['total_reward']:.3f}, mean={stats['mean_reward']:.3f}")
    
    print("  ✓ Reward system demo complete")


def demo_memory():
    """Demo 3: Cognitive Memory System."""
    print("\n" + "=" * 60)
    print("  Demo 3: Cognitive Memory System")
    print("=" * 60)
    
    from rl.memory.cognitive_memory import CognitiveMemory, MemoryRecord
    import time
    
    memory = CognitiveMemory(max_episodic_length=50)
    memory.reset()
    
    # Store some records
    records = [
        MemoryRecord(step=1, episode=1, timestamp=time.time(),
                     action="add_concept", observation="Added Python", reward=0.15),
        MemoryRecord(step=2, episode=1, timestamp=time.time(),
                     action="add_concept", observation="Added AI", reward=0.15),
        MemoryRecord(step=3, episode=1, timestamp=time.time(),
                     action="reason_deduction", observation="Inferred 3 new facts", reward=0.9),
        MemoryRecord(step=4, episode=1, timestamp=time.time(),
                     action="focus_attention", observation="Focused on AI", reward=0.2),
        MemoryRecord(step=5, episode=1, timestamp=time.time(),
                     action="add_concept", observation="Added ML", reward=0.15),
        MemoryRecord(step=6, episode=1, timestamp=time.time(),
                     action="reason_deduction", observation="Inferred 5 new facts", reward=1.5),
        MemoryRecord(step=7, episode=1, timestamp=time.time(),
                     action="reflect", observation="Self-awareness: 0.72", reward=0.1),
    ]
    
    for record in records:
        memory.store(record)
    
    # Fetch with different strategies
    print(f"\n  Stored {len(records)} records")
    
    for strategy in ["recent", "attention", "mixed"]:
        contexts, lengths = memory.fetch(history_length=4, strategy=strategy)
        print(f"\n  Strategy: {strategy} (returned {lengths[0]} records)")
        for line in contexts[0].split("\n")[:3]:
            print(f"    {line}")
    
    # Semantic memory
    semantic = memory.fetch_semantic("reasoning deduction")
    print(f"\n  Semantic memories for 'reasoning deduction': {len(semantic)}")
    for s in semantic[:3]:
        print(f"    {s['key']}: avg_reward={s.get('avg_reward', 0):.3f}, count={s.get('count', 0)}")
    
    # Record a procedure
    memory.record_procedure(
        actions=["add_concept", "add_relationship", "reason_deduction"],
        total_reward=2.5,
    )
    procedures = memory.fetch_procedures()
    print(f"\n  Procedures stored: {len(procedures)}")
    if procedures:
        print(f"    Best: {procedures[0]['actions']} → reward={procedures[0]['avg_reward']:.3f}")
    
    stats = memory.get_stats()
    print(f"\n  Memory stats: {json.dumps(stats, indent=4)}")
    
    print("  ✓ Memory system demo complete")


def demo_advantage():
    """Demo 4: Cognitive Advantage Computation."""
    print("\n" + "=" * 60)
    print("  Demo 4: Cognitive Advantage Computation (GiGPO)")
    print("=" * 60)
    
    from rl.algorithms.cognitive_advantage import (
        CognitiveAdvantageComputer, AdvantageConfig, TrajectoryStep
    )
    
    computer = CognitiveAdvantageComputer(AdvantageConfig(
        step_advantage_weight=1.0,
        reasoning_bonus_weight=0.2,
    ))
    
    # Create two trajectories with shared state hashes
    traj1 = [
        TrajectoryStep(step_id=1, episode_id="ep_1", traj_uid="t1",
                      state_hash="abc123", action="add_concept",
                      reward=0.1, cognitive_reward=0.05, num_atoms=10),
        TrajectoryStep(step_id=2, episode_id="ep_1", traj_uid="t1",
                      state_hash="def456", action="reason_deduction",
                      reward=0.5, cognitive_reward=0.3, num_atoms=15, num_inferences=3),
        TrajectoryStep(step_id=3, episode_id="ep_1", traj_uid="t1",
                      state_hash="ghi789", action="focus_attention",
                      reward=0.2, cognitive_reward=0.1, num_atoms=15, attention_sti=0.8),
    ]
    
    traj2 = [
        TrajectoryStep(step_id=1, episode_id="ep_1", traj_uid="t2",
                      state_hash="abc123", action="add_relationship",
                      reward=0.15, cognitive_reward=0.08, num_atoms=11),
        TrajectoryStep(step_id=2, episode_id="ep_1", traj_uid="t2",
                      state_hash="def456", action="add_concept",
                      reward=0.1, cognitive_reward=0.05, num_atoms=12),
        TrajectoryStep(step_id=3, episode_id="ep_1", traj_uid="t2",
                      state_hash="ghi789", action="reason_deduction",
                      reward=0.4, cognitive_reward=0.2, num_atoms=15, num_inferences=2),
    ]
    
    advantages = computer.compute_advantages([traj1, traj2])
    
    print(f"\n  Trajectory 1 advantages:")
    for i, (step, adv) in enumerate(zip(traj1, advantages[0])):
        print(f"    Step {i+1} ({step.action:20s}): advantage = {adv:+.4f}")
    
    print(f"\n  Trajectory 2 advantages:")
    for i, (step, adv) in enumerate(zip(traj2, advantages[1])):
        print(f"    Step {i+1} ({step.action:20s}): advantage = {adv:+.4f}")
    
    # Show grouping effect
    print(f"\n  State grouping (GiGPO):")
    print(f"    State 'abc123': traj1.step1 vs traj2.step1 → different actions, different advantages")
    print(f"    State 'def456': traj1.step2 vs traj2.step2 → reasoning vs adding, reasoning wins")
    print(f"    State 'ghi789': traj1.step3 vs traj2.step3 → attention vs reasoning, compared")
    
    print("  ✓ Advantage computation demo complete")


def demo_full_training():
    """Demo 5: Full Cognitive RL Training."""
    print("\n" + "=" * 60)
    print("  Demo 5: Full Cognitive RL Training")
    print("=" * 60)
    
    from rl.training.cognitive_trainer import CognitiveRLTrainer, TrainerConfig
    from rl.rollout.cognitive_rollout import RolloutConfig
    
    trainer = CognitiveRLTrainer(TrainerConfig(
        num_epochs=5,
        episodes_per_epoch=4,
        eval_episodes=2,
        eval_interval=2,
        policy_type="tabular_q",
        learning_rate=0.15,
        initial_exploration=0.5,
        exploration_decay=0.9,
        min_exploration=0.1,
        goal_curriculum=True,
        rollout_config=RolloutConfig(
            max_turns=15,
            verbose=False,
            env_config={"log_level": "WARNING", "max_steps": 15},
        ),
    ))
    
    # Train
    summary = trainer.train()
    
    # Show learning curve
    print(f"\n  Learning Curve:")
    print(f"  {'Epoch':>6} {'Mean Reward':>12} {'Success Rate':>13} {'Exploration':>12}")
    print("  " + "-" * 50)
    for h in trainer.training_history:
        print(f"  {h['epoch']:>6d} {h['mean_reward']:>12.3f} {h['success_rate']:>12.1%} {h['exploration_rate']:>12.3f}")
    
    # Show Q-table stats
    if hasattr(trainer.policy, "get_stats"):
        stats = trainer.policy.get_stats()
        print(f"\n  Q-Table: {stats['num_states']} states, {stats['total_visits']} visits")
    
    # Save results
    results_path = os.path.join(PROJECT_ROOT, "rl_training_results.json")
    trainer.save_results(results_path)
    print(f"\n  Results saved to: {results_path}")
    
    trainer.close()
    print("  ✓ Full training demo complete")


def main():
    """Run all demos."""
    print("╔" + "═" * 58 + "╗")
    print("║     ManusCog Cognitive RL — Integration Demo             ║")
    print("║     OpenManus-RL × Cognitive Architecture                ║")
    print("╚" + "═" * 58 + "╝")
    
    start = time.time()
    
    demo_environment()
    demo_reward_system()
    demo_memory()
    demo_advantage()
    demo_full_training()
    
    elapsed = time.time() - start
    
    print("\n" + "=" * 60)
    print(f"  All demos complete in {elapsed:.1f}s")
    print("=" * 60)
    print("""
  What was demonstrated:
  
  1. CognitiveEnvironment: AtomSpace as RL state space with
     cognitive actions (add, reason, focus, reflect)
  
  2. CognitiveRewardManager: Multi-signal rewards combining
     reasoning quality, attention efficiency, and knowledge growth
  
  3. CognitiveMemory: Attention-based memory with episodic,
     semantic, working, and procedural memory types
  
  4. CognitiveAdvantageComputer: GiGPO-inspired step-level
     grouping using AtomSpace state fingerprints
  
  5. CognitiveRLTrainer: Full training pipeline with tabular
     Q-learning, goal curriculum, and evaluation
""")


if __name__ == "__main__":
    main()
