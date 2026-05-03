#!/usr/bin/env python3
"""
AtomSpace Persistence Demo
==========================

This demo shows how the AtomSpace can persist knowledge across restarts.
Knowledge survives shutdown - enabling true cognitive continuity.

The demo:
1. Creates an AtomSpace with knowledge
2. Saves it to persistent storage
3. Creates a NEW AtomSpace
4. Loads the knowledge back
5. Verifies the knowledge was preserved

Run with: python demo_persistence.py
"""

import asyncio
import sys
import os
import tempfile

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from kernel.cognitive_kernel import CognitiveKernel, KernelConfig, KernelState
from kernel.cognitive.types import AtomType, TruthValue, AttentionValue
from atomspace.persistence.storage import (
    AtomSpacePersistence, PersistenceConfig, StorageBackend
)


class DemoOutput:
    """Pretty output for the demo."""
    
    COLORS = {
        'header': '\033[95m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'bold': '\033[1m',
        'end': '\033[0m'
    }
    
    @classmethod
    def header(cls, text: str):
        print(f"\n{cls.COLORS['bold']}{cls.COLORS['header']}{'='*60}{cls.COLORS['end']}")
        print(f"{cls.COLORS['bold']}{cls.COLORS['header']}{text.center(60)}{cls.COLORS['end']}")
        print(f"{cls.COLORS['bold']}{cls.COLORS['header']}{'='*60}{cls.COLORS['end']}\n")
    
    @classmethod
    def section(cls, text: str):
        print(f"\n{cls.COLORS['bold']}{cls.COLORS['cyan']}▶ {text}{cls.COLORS['end']}")
        print(f"{cls.COLORS['cyan']}{'-'*50}{cls.COLORS['end']}")
    
    @classmethod
    def info(cls, text: str):
        print(f"  {cls.COLORS['blue']}ℹ {text}{cls.COLORS['end']}")
    
    @classmethod
    def success(cls, text: str):
        print(f"  {cls.COLORS['green']}✓ {text}{cls.COLORS['end']}")
    
    @classmethod
    def warning(cls, text: str):
        print(f"  {cls.COLORS['yellow']}⚠ {text}{cls.COLORS['end']}")
    
    @classmethod
    def data(cls, label: str, value):
        print(f"    {cls.COLORS['bold']}{label}:{cls.COLORS['end']} {value}")


def demo_persistence():
    """Demonstrate AtomSpace persistence."""
    
    DemoOutput.header("AtomSpace Persistence Demo")
    print("This demo shows how knowledge survives across restarts.")
    print("The cognitive kernel can maintain continuity of knowledge.\n")
    
    # Use a temporary file for the demo
    db_path = os.path.join(tempfile.gettempdir(), "manuscog_demo.db")
    json_path = os.path.join(tempfile.gettempdir(), "manuscog_demo.json")
    
    try:
        # Clean up any previous demo
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # =====================================================================
        # PHASE 1: Create and populate AtomSpace
        # =====================================================================
        
        DemoOutput.section("Phase 1: Creating Original AtomSpace")
        
        config = KernelConfig(
            kernel_id="persistence-demo-1",
            kernel_name="Original Kernel",
            log_level="WARNING"
        )
        
        kernel1 = CognitiveKernel(config)
        kernel1.boot()
        
        DemoOutput.success("Original kernel booted")
        DemoOutput.data("Initial AtomSpace size", kernel1.atomspace.size())
        
        # Add knowledge
        DemoOutput.info("Adding knowledge to AtomSpace...")
        
        concepts = [
            ("Python", "Programming Language"),
            ("JavaScript", "Programming Language"),
            ("Machine Learning", "Technology"),
            ("Deep Learning", "Machine Learning"),
            ("Neural Networks", "Deep Learning"),
            ("TensorFlow", "ML Framework"),
            ("PyTorch", "ML Framework"),
        ]
        
        for name, category in concepts:
            kernel1.atomspace.add_node(
                AtomType.CONCEPT_NODE,
                name,
                tv=TruthValue(1.0, 0.9),
                av=AttentionValue(sti=0.5)
            )
            
            # Add category if not exists
            cat_handles = kernel1.atomspace._name_index.get_by_name(category)
            if not cat_handles:
                kernel1.atomspace.add_node(
                    AtomType.CONCEPT_NODE,
                    category,
                    tv=TruthValue(1.0, 0.9)
                )
        
        # Add relationships
        relationships = [
            ("Python", "Programming Language"),
            ("JavaScript", "Programming Language"),
            ("Deep Learning", "Machine Learning"),
            ("Neural Networks", "Deep Learning"),
            ("TensorFlow", "ML Framework"),
            ("PyTorch", "ML Framework"),
        ]
        
        for child, parent in relationships:
            child_handles = kernel1.atomspace._name_index.get_by_name(child)
            parent_handles = kernel1.atomspace._name_index.get_by_name(parent)
            
            if child_handles and parent_handles:
                kernel1.atomspace.add_link(
                    AtomType.INHERITANCE_LINK,
                    [list(child_handles)[0], list(parent_handles)[0]],
                    tv=TruthValue(1.0, 0.9)
                )
        
        DemoOutput.success(f"Added {len(concepts)} concepts and {len(relationships)} relationships")
        DemoOutput.data("Final AtomSpace size", kernel1.atomspace.size())
        
        # Run some PLN inference
        if kernel1.pln:
            DemoOutput.info("Running PLN inference...")
            premises = kernel1.pln.controller.find_deduction_premises()
            for link_ab, link_bc in premises[:5]:
                kernel1.pln.deduction(link_ab, link_bc)
            DemoOutput.success(f"Made {kernel1.pln.stats['total_inferences']} inferences")
        
        DemoOutput.data("AtomSpace size after inference", kernel1.atomspace.size())
        
        # =====================================================================
        # PHASE 2: Save to persistent storage
        # =====================================================================
        
        DemoOutput.section("Phase 2: Saving to Persistent Storage")
        
        persistence_config = PersistenceConfig(
            backend=StorageBackend.SQLITE,
            storage_path=db_path
        )
        
        persistence = AtomSpacePersistence(persistence_config)
        
        # Save to SQLite
        saved_count = persistence.save(kernel1.atomspace)
        DemoOutput.success(f"Saved {saved_count} atoms to SQLite")
        DemoOutput.data("Storage path", db_path)
        
        # Also export to JSON for human readability
        json_count = persistence.export_json(kernel1.atomspace, json_path)
        DemoOutput.success(f"Exported {json_count} atoms to JSON")
        DemoOutput.data("JSON path", json_path)
        
        # Show persistence stats
        stats = persistence.get_statistics()
        DemoOutput.info("Persistence statistics:")
        for key, value in stats.items():
            DemoOutput.data(f"  {key}", value)
        
        # Shutdown original kernel
        DemoOutput.info("Shutting down original kernel...")
        kernel1.shutdown()
        DemoOutput.success("Original kernel shutdown complete")
        
        # =====================================================================
        # PHASE 3: Create NEW AtomSpace and load
        # =====================================================================
        
        DemoOutput.section("Phase 3: Loading into New AtomSpace")
        
        DemoOutput.warning("Creating COMPLETELY NEW kernel (simulating restart)")
        
        config2 = KernelConfig(
            kernel_id="persistence-demo-2",
            kernel_name="Restored Kernel",
            log_level="WARNING"
        )
        
        kernel2 = CognitiveKernel(config2)
        kernel2.boot()
        
        DemoOutput.success("New kernel booted")
        DemoOutput.data("Initial AtomSpace size (empty)", kernel2.atomspace.size())
        
        # Load from persistent storage
        DemoOutput.info("Loading knowledge from persistent storage...")
        loaded_count = persistence.load(kernel2.atomspace)
        
        DemoOutput.success(f"Loaded {loaded_count} atoms from storage")
        DemoOutput.data("Restored AtomSpace size", kernel2.atomspace.size())
        
        # =====================================================================
        # PHASE 4: Verify knowledge was preserved
        # =====================================================================
        
        DemoOutput.section("Phase 4: Verifying Knowledge Preservation")
        
        # Check that concepts exist
        DemoOutput.info("Checking for preserved concepts...")
        
        preserved_concepts = []
        for name, _ in concepts:
            handles = kernel2.atomspace._name_index.get_by_name(name)
            if handles:
                preserved_concepts.append(name)
                atom = kernel2.atomspace.get_atom(list(handles)[0])
                if atom:
                    DemoOutput.success(f"Found '{name}' (strength: {atom.truth_value.strength:.2f})")
        
        DemoOutput.data("Concepts preserved", f"{len(preserved_concepts)}/{len(concepts)}")
        
        # Check relationships
        DemoOutput.info("Checking for preserved relationships...")
        
        preserved_links = 0
        for child, parent in relationships:
            child_handles = kernel2.atomspace._name_index.get_by_name(child)
            parent_handles = kernel2.atomspace._name_index.get_by_name(parent)
            
            if child_handles and parent_handles:
                # Check if link exists
                existing = kernel2.atomspace.match_pattern(
                    AtomType.INHERITANCE_LINK,
                    [list(child_handles)[0], list(parent_handles)[0]]
                )
                if existing:
                    preserved_links += 1
        
        DemoOutput.data("Relationships preserved", f"{preserved_links}/{len(relationships)}")
        
        # Run inference on restored knowledge
        DemoOutput.info("Running PLN inference on restored knowledge...")
        if kernel2.pln:
            premises = kernel2.pln.controller.find_deduction_premises()
            for link_ab, link_bc in premises[:5]:
                kernel2.pln.deduction(link_ab, link_bc)
            DemoOutput.success(f"Made {kernel2.pln.stats['total_inferences']} new inferences")
        
        # Final comparison
        DemoOutput.section("Summary")
        
        DemoOutput.data("Original AtomSpace size", saved_count)
        DemoOutput.data("Restored AtomSpace size", kernel2.atomspace.size())
        DemoOutput.data("Concepts preserved", f"{len(preserved_concepts)}/{len(concepts)}")
        DemoOutput.data("Relationships preserved", f"{preserved_links}/{len(relationships)}")
        
        if len(preserved_concepts) == len(concepts):
            DemoOutput.success("All knowledge successfully preserved!")
        else:
            DemoOutput.warning("Some knowledge may have been lost")
        
        # Cleanup
        kernel2.shutdown()
        persistence.close()
        
        # Clean up temp files
        if os.path.exists(db_path):
            os.remove(db_path)
        if os.path.exists(json_path):
            os.remove(json_path)
        
    except Exception as e:
        print(f"\n  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    DemoOutput.header("Demo Complete!")
    print("The AtomSpace persistence system enables:")
    print("  - Knowledge to survive across restarts")
    print("  - Cognitive continuity over time")
    print("  - Export/import for backup and sharing")
    print("  - True long-term memory for the cognitive kernel\n")


if __name__ == "__main__":
    demo_persistence()
