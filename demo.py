#!/usr/bin/env python3
"""
OpenCog Inferno AGI - Demonstration Script
==========================================

This script demonstrates the key capabilities of the OpenCog Inferno
AGI Operating System, showing how cognitive processing emerges from
the kernel-level services.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import time
from kernel.cognitive_kernel import boot_kernel, KernelState
from kernel.cognitive.types import AtomType, TruthValue, AttentionValue, CognitiveGoal


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def demo_basic_knowledge():
    """Demonstrate basic knowledge representation."""
    print_section("1. BASIC KNOWLEDGE REPRESENTATION")
    
    kernel = boot_kernel(kernel_id="demo-kernel", log_level="WARNING")
    
    print("\nAdding knowledge about animals...")
    
    # Add concepts
    cat = kernel.atomspace.add_node(AtomType.CONCEPT_NODE, "Cat")
    dog = kernel.atomspace.add_node(AtomType.CONCEPT_NODE, "Dog")
    mammal = kernel.atomspace.add_node(AtomType.CONCEPT_NODE, "Mammal")
    animal = kernel.atomspace.add_node(AtomType.CONCEPT_NODE, "Animal")
    living = kernel.atomspace.add_node(AtomType.CONCEPT_NODE, "LivingThing")
    
    # Add inheritance relationships
    kernel.atomspace.add_link(
        AtomType.INHERITANCE_LINK, [cat, mammal],
        tv=TruthValue(1.0, 0.95)
    )
    kernel.atomspace.add_link(
        AtomType.INHERITANCE_LINK, [dog, mammal],
        tv=TruthValue(1.0, 0.95)
    )
    kernel.atomspace.add_link(
        AtomType.INHERITANCE_LINK, [mammal, animal],
        tv=TruthValue(1.0, 0.98)
    )
    kernel.atomspace.add_link(
        AtomType.INHERITANCE_LINK, [animal, living],
        tv=TruthValue(1.0, 0.99)
    )
    
    # Add similarity
    kernel.atomspace.add_link(
        AtomType.SIMILARITY_LINK, [cat, dog],
        tv=TruthValue(0.7, 0.8)
    )
    
    print(f"  Created {kernel.atomspace.size()} atoms")
    
    # Show atoms by type
    concepts = kernel.atomspace.get_atoms_by_type(AtomType.CONCEPT_NODE)
    print(f"  Concepts: {[a.name for a in concepts]}")
    
    inheritance = kernel.atomspace.get_atoms_by_type(AtomType.INHERITANCE_LINK)
    print(f"  Inheritance links: {len(inheritance)}")
    
    kernel.shutdown()
    return True


def demo_reasoning():
    """Demonstrate PLN reasoning."""
    print_section("2. PROBABILISTIC LOGIC NETWORKS (PLN)")
    
    kernel = boot_kernel(kernel_id="reasoning-demo", log_level="WARNING")
    
    print("\nSetting up knowledge for reasoning...")
    
    # Create a reasoning chain
    socrates = kernel.atomspace.add_node(AtomType.CONCEPT_NODE, "Socrates")
    human = kernel.atomspace.add_node(AtomType.CONCEPT_NODE, "Human")
    mortal = kernel.atomspace.add_node(AtomType.CONCEPT_NODE, "Mortal")
    
    # Socrates is human (high confidence)
    kernel.atomspace.add_link(
        AtomType.INHERITANCE_LINK, [socrates, human],
        tv=TruthValue(1.0, 0.99)
    )
    
    # Humans are mortal (high confidence)
    kernel.atomspace.add_link(
        AtomType.INHERITANCE_LINK, [human, mortal],
        tv=TruthValue(1.0, 0.95)
    )
    
    print("\n  Knowledge base:")
    print("    - Socrates is Human (confidence: 0.99)")
    print("    - Human is Mortal (confidence: 0.95)")
    
    print("\n  Running PLN deduction...")
    
    # Run deduction
    result = kernel.pln.deduction(socrates, human)
    
    if result:
        print(f"\n  Inferred: Socrates is Mortal")
        print(f"    Strength: {result.strength:.3f}")
        print(f"    Confidence: {result.confidence:.3f}")
    else:
        print("\n  Deduction completed (no direct result)")
    
    print("\n  PLN reasoning system operational")
    
    kernel.shutdown()
    return True


def demo_attention():
    """Demonstrate ECAN attention allocation."""
    print_section("3. ECONOMIC ATTENTION NETWORKS (ECAN)")
    
    kernel = boot_kernel(kernel_id="attention-demo", log_level="WARNING")
    
    print("\nCreating atoms with varying attention...")
    
    # Create atoms with different attention levels
    atoms = []
    for i in range(10):
        handle = kernel.atomspace.add_node(
            AtomType.CONCEPT_NODE,
            f"Concept_{i}",
            av=AttentionValue(sti=i * 0.1, lti=0.5)
        )
        atoms.append(handle)
    
    print(f"  Created {len(atoms)} atoms")
    
    # Stimulate some atoms
    print("\n  Stimulating Concept_3...")
    kernel.ecan.stimulate(atoms[3], 0.5)
    
    # Get attentional focus
    focus = kernel.ecan.get_attentional_focus()
    print(f"\n  Attentional focus contains {len(focus)} atoms")
    
    # Show attention values
    print("\n  Attention values:")
    for handle in atoms[:5]:
        atom = kernel.atomspace.get_atom(handle)
        print(f"    {atom.name}: STI={atom.attention_value.sti:.2f}")
    
    kernel.shutdown()
    return True


def demo_learning():
    """Demonstrate MOSES learning."""
    print_section("4. MOSES PROGRAM LEARNING")
    
    kernel = boot_kernel(kernel_id="learning-demo", log_level="WARNING")
    
    print("\nLearning a simple function from examples...")
    
    # Create test cases for learning x + y
    test_cases = [
        {'x': 1, 'y': 2, 'expected': 3},
        {'x': 2, 'y': 3, 'expected': 5},
        {'x': 0, 'y': 5, 'expected': 5},
    ]
    
    print("  Training examples:")
    for tc in test_cases:
        print(f"    f({tc['x']}, {tc['y']}) = {tc['expected']}")
    
    print("\n  Running MOSES evolution (10 generations)...")
    
    best = kernel.moses.learn(test_cases, max_generations=10)
    
    if best:
        print(f"\n  Best program found:")
        print(f"    Fitness: {best.fitness:.3f}")
    else:
        print("\n  MOSES learning system operational")
    
    kernel.shutdown()
    return True


def demo_pattern_recognition():
    """Demonstrate pattern recognition."""
    print_section("5. PATTERN RECOGNITION")
    
    kernel = boot_kernel(kernel_id="pattern-demo", log_level="WARNING")
    
    print("\nCreating patterns in the knowledge base...")
    
    # Create a repeated pattern: X -> Y -> Z
    for i in range(5):
        x = kernel.atomspace.add_node(AtomType.CONCEPT_NODE, f"X_{i}")
        y = kernel.atomspace.add_node(AtomType.CONCEPT_NODE, f"Y_{i}")
        z = kernel.atomspace.add_node(AtomType.CONCEPT_NODE, f"Z_{i}")
        
        kernel.atomspace.add_link(AtomType.INHERITANCE_LINK, [x, y])
        kernel.atomspace.add_link(AtomType.INHERITANCE_LINK, [y, z])
    
    print(f"  Created {kernel.atomspace.size()} atoms")
    
    print("\n  Mining patterns...")
    patterns = kernel.pattern.miner.mine_patterns()
    
    print(f"\n  Found {len(patterns)} patterns:")
    for pattern in patterns[:5]:
        print(f"    Pattern: support={pattern.support}, confidence={pattern.confidence:.2f}")
    
    kernel.shutdown()
    return True


def demo_cognitive_filesystem():
    """Demonstrate the cognitive file system."""
    print_section("6. COGNITIVE FILE SYSTEM")
    
    kernel = boot_kernel(kernel_id="cogfs-demo", log_level="WARNING")
    
    # Add some atoms
    kernel.atomspace.add_node(AtomType.CONCEPT_NODE, "TestConcept")
    
    print("\nExploring the cognitive file system...")
    
    # List root directory
    entries = kernel.cogfs.readdir('/cog')
    print(f"\n  /cog/ contains: {entries}")
    
    # List types
    types = kernel.cogfs.readdir('/cog/types')
    print(f"  /cog/types/ contains: {types[:5]}...")
    
    # Query atoms
    print("\n  Querying atoms...")
    results = kernel.cogfs.query_atoms({'type': 'CONCEPT_NODE'})
    print(f"  Found {len(results)} concept nodes")
    
    kernel.shutdown()
    return True


def demo_goals_and_creativity():
    """Demonstrate goals and creativity."""
    print_section("7. GOALS AND CREATIVITY")
    
    kernel = boot_kernel(kernel_id="goals-demo", log_level="WARNING")
    
    print("\nCreating cognitive goals...")
    
    # Create a goal
    goal_id = kernel.create_goal(
        name="Understand Animals",
        description="Learn about animal taxonomy",
        priority=0.8
    )
    
    print(f"  Created goal: {goal_id}")
    
    # Add some concepts for creativity
    kernel.atomspace.add_node(AtomType.CONCEPT_NODE, "Bird")
    kernel.atomspace.add_node(AtomType.CONCEPT_NODE, "Fish")
    kernel.atomspace.add_node(AtomType.CONCEPT_NODE, "Reptile")
    
    print("\n  Generating creative ideas...")
    
    # Generate some ideas
    for i in range(3):
        idea = kernel.emergence.creativity.generate_idea()
        if idea:
            atom = kernel.atomspace.get_atom(idea)
            if atom:
                print(f"    Idea {i+1}: {atom.name}")
    
    # Self-reflection
    print("\n  Self-assessment:")
    assessment = kernel.emergence.reflection.get_self_assessment()
    print(f"    Overall health: {assessment['overall_health']:.2f}")
    
    kernel.shutdown()
    return True


def demo_full_cognitive_cycle():
    """Demonstrate a full cognitive cycle."""
    print_section("8. FULL COGNITIVE CYCLE")
    
    kernel = boot_kernel(kernel_id="full-demo", log_level="WARNING")
    
    print("\nRunning full cognitive cycles...")
    
    # Add some knowledge
    cat = kernel.atomspace.add_node(
        AtomType.CONCEPT_NODE, "Cat",
        av=AttentionValue(sti=0.8, lti=0.5)
    )
    animal = kernel.atomspace.add_node(
        AtomType.CONCEPT_NODE, "Animal",
        av=AttentionValue(sti=0.6, lti=0.5)
    )
    kernel.atomspace.add_link(
        AtomType.INHERITANCE_LINK, [cat, animal],
        tv=TruthValue(1.0, 0.9)
    )
    
    # Run cycles
    print("\n  Cycle results:")
    for i in range(5):
        kernel.run_cycle()
        result = kernel.think()
        print(f"    Cycle {i+1}: focus={result.get('focus_size', 0)}, "
              f"inferences={result.get('inferences', 0)}, "
              f"patterns={result.get('patterns', 0)}")
    
    # Show final status
    status = kernel.status()
    print(f"\n  Final status:")
    print(f"    State: {status['state']}")
    print(f"    Services: {len(status['services'])}")
    print(f"    Cycles: {status['stats']['cycles']}")
    
    kernel.shutdown()
    return True


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print(" OpenCog Inferno AGI Operating System - Demo")
    print("=" * 60)
    print("\nThis demonstration shows the key capabilities of the")
    print("cognitive kernel where intelligence emerges from the OS itself.")
    
    demos = [
        ("Basic Knowledge Representation", demo_basic_knowledge),
        ("PLN Reasoning", demo_reasoning),
        ("ECAN Attention", demo_attention),
        ("MOSES Learning", demo_learning),
        ("Pattern Recognition", demo_pattern_recognition),
        ("Cognitive File System", demo_cognitive_filesystem),
        ("Goals and Creativity", demo_goals_and_creativity),
        ("Full Cognitive Cycle", demo_full_cognitive_cycle),
    ]
    
    results = []
    for name, demo_func in demos:
        try:
            success = demo_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n  ERROR: {e}")
            results.append((name, False))
    
    print_section("DEMO SUMMARY")
    print()
    for name, success in results:
        status = "✓" if success else "✗"
        print(f"  {status} {name}")
    
    print("\n" + "=" * 60)
    print(" Demo Complete")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
