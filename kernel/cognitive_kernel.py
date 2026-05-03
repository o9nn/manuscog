"""
OpenCog Inferno AGI - Cognitive Kernel
======================================

The Cognitive Kernel is the heart of the AGI operating system.
It integrates all cognitive subsystems and provides the runtime
environment for intelligent behavior.

This is not a traditional OS kernel - it's a cognitive kernel
where thinking, reasoning, and intelligence are fundamental
system services rather than applications.

Architecture:
    +--------------------------------------------------+
    |              Emergent Intelligence               |
    |  (Synergy, Goals, Reflection, Creativity)        |
    +--------------------------------------------------+
    |    PLN     |   MOSES   |   ECAN   |   Pattern   |
    | Reasoning  | Learning  | Attention| Recognition |
    +--------------------------------------------------+
    |              Cognitive File System               |
    |        (CogFS with Styx/9P Protocol)            |
    +--------------------------------------------------+
    |              AtomSpace Hypergraph                |
    |         (Distributed Knowledge Base)            |
    +--------------------------------------------------+
    |           Cognitive Process Scheduler            |
    |      (Attention-Based Process Management)       |
    +--------------------------------------------------+
    |              Memory Management                   |
    |    (Forgetting, Consolidation, Caching)         |
    +--------------------------------------------------+
"""

from __future__ import annotations
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import threading
import time
import logging

# Core types
from kernel.cognitive.types import (
    Atom, Node, Link, AtomHandle, AtomType,
    TruthValue, AttentionValue, CognitiveContext,
    CognitiveGoal, GoalState, CognitiveProcessState,
    KernelService
)

# AtomSpace
from atomspace.hypergraph.atomspace import AtomSpace

# Memory management
from kernel.memory.manager import (
    CognitiveMemoryManager, MemoryConfig
)

# Reasoning
from kernel.reasoning.pln import (
    PLNEngine, PLNConfig
)

# Pattern matching
from atomspace.query.pattern_matcher import PatternMatcher

# Attention
from kernel.attention.ecan import (
    ECANService, ECANConfig
)

# Pattern recognition
from kernel.pattern.recognition import PatternRecognitionService

# File system
from fs.cogfs.filesystem import CognitiveFileSystem, StyxServer

# Process scheduler
from proc.scheduler.cognitive_scheduler import (
    CognitiveScheduler, CogProcType, CogProcPriority,
    IPCManager, GoalDirectedProcessFactory
)

# Learning
from kernel.learning.moses import MOSESEngine, HebbianLearner

# Knowledge representation
from knowledge.ontology.representation import KnowledgeBase

# Distributed coordination
from distributed.coordination.cluster import (
    DistributedCoordinationService, ClusterNode, NodeRole
)

# Emergent intelligence
from kernel.emergence.intelligence import (
    EmergentIntelligenceService, CognitiveSynergy,
    GoalManager, SelfReflection, CreativityEngine
)

# Autognosis (self-awareness)
try:
    from kernel.autognosis import AutognosisOrchestrator, AutognosisConfig
    AUTOGNOSIS_AVAILABLE = True
except ImportError:
    AUTOGNOSIS_AVAILABLE = False

# Integration Hub (Manus connection)
try:
    from kernel.integration_hub import ManusIntegrationHub, HubConfig
    INTEGRATION_HUB_AVAILABLE = True
except ImportError:
    INTEGRATION_HUB_AVAILABLE = False

# Holistic Metamodel
try:
    from kernel.metamodel import HolisticMetamodelOrchestrator, MetamodelConfig
    METAMODEL_AVAILABLE = True
except ImportError:
    METAMODEL_AVAILABLE = False

# Ontogenesis (self-evolution)
try:
    from kernel.ontogenesis import EvolutionEngine, EvolutionConfig
    ONTOGENESIS_AVAILABLE = True
except ImportError:
    ONTOGENESIS_AVAILABLE = False

# VORTEX architecture
try:
    from kernel.vortex import VortexOrchestrator, VortexConfig
    VORTEX_AVAILABLE = True
except ImportError:
    VORTEX_AVAILABLE = False


# =============================================================================
# KERNEL STATE
# =============================================================================

class KernelState(Enum):
    """State of the cognitive kernel."""
    UNINITIALIZED = auto()
    INITIALIZING = auto()
    RUNNING = auto()
    PAUSED = auto()
    SHUTTING_DOWN = auto()
    TERMINATED = auto()


@dataclass
class KernelConfig:
    """Configuration for the cognitive kernel."""
    # Identity
    kernel_id: str = "opencog-inferno-0"
    kernel_name: str = "OpenCog Inferno AGI Kernel"
    
    # Memory
    max_atoms: int = 1000000
    forgetting_threshold: float = 0.01
    
    # Attention
    attention_budget: float = 100.0
    focus_boundary: float = 0.5
    
    # Reasoning
    max_inference_depth: int = 10
    inference_timeout: float = 5.0
    
    # Learning
    learning_rate: float = 0.1
    population_size: int = 100
    
    # Scheduling
    max_processes: int = 16
    cycle_budget: float = 10.0
    
    # Distribution
    enable_distribution: bool = False
    cluster_address: str = "localhost"
    cluster_port: int = 9000
    
    # Logging
    log_level: str = "INFO"


# =============================================================================
# COGNITIVE KERNEL
# =============================================================================

class CognitiveKernel:
    """
    The OpenCog Inferno Cognitive Kernel.
    
    This is the main entry point for the AGI operating system.
    It initializes and coordinates all cognitive subsystems.
    """
    
    VERSION = "0.1.0"
    
    def __init__(self, config: KernelConfig = None):
        self.config = config or KernelConfig()
        self.state = KernelState.UNINITIALIZED
        
        # Core components (initialized in boot())
        self.atomspace: Optional[AtomSpace] = None
        self.memory_manager: Optional[CognitiveMemoryManager] = None
        self.scheduler: Optional[CognitiveScheduler] = None
        self.ipc: Optional[IPCManager] = None
        
        # Cognitive services
        self.pln: Optional[PLNEngine] = None
        self.ecan: Optional[ECANService] = None
        self.pattern: Optional[PatternRecognitionService] = None
        self.moses: Optional[MOSESEngine] = None
        self.hebbian: Optional[HebbianLearner] = None
        
        # Higher-level systems
        self.cogfs: Optional[CognitiveFileSystem] = None
        self.styx: Optional[StyxServer] = None
        self.knowledge: Optional[KnowledgeBase] = None
        self.emergence: Optional[EmergentIntelligenceService] = None
        
        # Distribution (optional)
        self.distributed: Optional[DistributedCoordinationService] = None
        
        # Advanced cognitive modules (optional)
        self.autognosis: Optional['AutognosisOrchestrator'] = None
        self.integration_hub: Optional['ManusIntegrationHub'] = None
        self.metamodel: Optional['HolisticMetamodelOrchestrator'] = None
        self.evolution_engine: Optional['EvolutionEngine'] = None
        self.vortex: Optional['VortexOrchestrator'] = None
        
        # Service registry
        self._services: Dict[str, KernelService] = {}
        
        # Callbacks
        self._on_boot: List[Callable[['CognitiveKernel'], None]] = []
        self._on_shutdown: List[Callable[['CognitiveKernel'], None]] = []
        
        # Threading
        self._main_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # Statistics
        self.stats = {
            'boot_time': None,
            'uptime': 0,
            'cycles': 0,
            'atoms_created': 0,
            'inferences_made': 0,
            'patterns_found': 0
        }
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup kernel logging."""
        self.logger = logging.getLogger("CognitiveKernel")
        self.logger.setLevel(getattr(logging, self.config.log_level))
        
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
    
    # =========================================================================
    # BOOT SEQUENCE
    # =========================================================================
    
    def boot(self) -> bool:
        """
        Boot the cognitive kernel.
        
        This initializes all subsystems in the correct order
        and starts the main cognitive loop.
        """
        if self.state != KernelState.UNINITIALIZED:
            self.logger.warning("Kernel already initialized")
            return False
        
        self.logger.info(f"Booting {self.config.kernel_name} v{self.VERSION}")
        self.state = KernelState.INITIALIZING
        
        try:
            # Phase 1: Core initialization
            self._init_atomspace()
            self._init_memory_manager()
            self._init_scheduler()
            
            # Phase 2: Cognitive services
            self._init_reasoning()
            self._init_attention()
            self._init_pattern_recognition()
            self._init_learning()
            
            # Phase 3: Higher-level systems
            self._init_filesystem()
            self._init_knowledge()
            self._init_emergence()
            
            # Phase 4: Distribution (optional)
            if self.config.enable_distribution:
                self._init_distribution()
            
            # Phase 5: Advanced cognitive modules
            self._init_advanced_modules()
            
            # Phase 6: Start services
            self._start_services()
            
            # Boot complete
            self.state = KernelState.RUNNING
            self.stats['boot_time'] = time.time()
            
            # Notify callbacks
            for callback in self._on_boot:
                try:
                    callback(self)
                except Exception as e:
                    self.logger.error(f"Boot callback error: {e}")
            
            self.logger.info("Kernel boot complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Boot failed: {e}")
            self.state = KernelState.TERMINATED
            return False
    
    def _init_atomspace(self):
        """Initialize the AtomSpace."""
        self.logger.info("Initializing AtomSpace...")
        self.atomspace = AtomSpace()
    
    def _init_memory_manager(self):
        """Initialize memory management."""
        self.logger.info("Initializing Memory Manager...")
        mem_config = MemoryConfig(
            forgetting_threshold=self.config.forgetting_threshold
        )
        self.memory_manager = CognitiveMemoryManager(self.atomspace, mem_config)
    
    def _init_scheduler(self):
        """Initialize the process scheduler."""
        self.logger.info("Initializing Process Scheduler...")
        self.scheduler = CognitiveScheduler(
            self.atomspace,
            max_concurrent=self.config.max_processes,
            cycle_budget=self.config.cycle_budget
        )
        self.ipc = IPCManager()
    
    def _init_reasoning(self):
        """Initialize reasoning systems."""
        self.logger.info("Initializing PLN Reasoning Engine...")
        pln_config = PLNConfig(
            max_depth=self.config.max_inference_depth,
            timeout=self.config.inference_timeout
        )
        self.pln = PLNEngine(self.atomspace, pln_config)
        self._register_service(self.pln)
    
    def _init_attention(self):
        """Initialize attention allocation."""
        self.logger.info("Initializing ECAN Attention System...")
        from kernel.attention.ecan import ECANParameters
        ecan_params = ECANParameters(
            total_stimulus=self.config.attention_budget,
            focus_boundary=self.config.focus_boundary
        )
        self.ecan = ECANService(self.atomspace, ecan_params)
        self._register_service(self.ecan)
    
    def _init_pattern_recognition(self):
        """Initialize pattern recognition."""
        self.logger.info("Initializing Pattern Recognition...")
        self.pattern = PatternRecognitionService(self.atomspace)
        self._register_service(self.pattern)
    
    def _init_learning(self):
        """Initialize learning systems."""
        self.logger.info("Initializing Learning Systems...")
        self.moses = MOSESEngine(
            self.atomspace,
            population_size=self.config.population_size
        )
        self.hebbian = HebbianLearner(
            self.atomspace,
            learning_rate=self.config.learning_rate
        )
        self._register_service(self.moses)
    
    def _init_filesystem(self):
        """Initialize the cognitive file system."""
        self.logger.info("Initializing Cognitive File System...")
        self.cogfs = CognitiveFileSystem(self.atomspace)
        self.styx = StyxServer(self.cogfs)
    
    def _init_knowledge(self):
        """Initialize knowledge representation."""
        self.logger.info("Initializing Knowledge Base...")
        self.knowledge = KnowledgeBase(self.atomspace)
    
    def _init_emergence(self):
        """Initialize emergent intelligence."""
        self.logger.info("Initializing Emergent Intelligence...")
        self.emergence = EmergentIntelligenceService(self.atomspace)
        self._register_service(self.emergence)
    
    def _init_distribution(self):
        """Initialize distributed coordination."""
        self.logger.info("Initializing Distributed Coordination...")
        self.distributed = DistributedCoordinationService(
            self.atomspace,
            node_id=self.config.kernel_id,
            address=self.config.cluster_address,
            port=self.config.cluster_port
        )
        self._register_service(self.distributed)
    
    def _init_advanced_modules(self):
        """
        Initialize advanced cognitive modules.
        
        These modules provide:
        - Autognosis: Self-awareness and self-monitoring
        - Integration Hub: Connection to Primary Manus
        - Metamodel: Holistic organizational dynamics
        - Ontogenesis: Self-evolution capabilities
        - VORTEX: Vortical cognitive organization
        """
        # Autognosis (self-awareness)
        if AUTOGNOSIS_AVAILABLE:
            self.logger.info("Initializing Autognosis (self-awareness)...")
            try:
                autognosis_config = AutognosisConfig()
                self.autognosis = AutognosisOrchestrator(autognosis_config)
                # Note: Full initialization requires async, done in start_advanced_modules
            except Exception as e:
                self.logger.warning(f"Autognosis initialization deferred: {e}")
        
        # Integration Hub (Manus connection)
        if INTEGRATION_HUB_AVAILABLE:
            self.logger.info("Initializing Manus Integration Hub...")
            try:
                hub_config = HubConfig()
                self.integration_hub = ManusIntegrationHub(hub_config)
            except Exception as e:
                self.logger.warning(f"Integration Hub initialization deferred: {e}")
        
        # Holistic Metamodel
        if METAMODEL_AVAILABLE:
            self.logger.info("Initializing Holistic Metamodel...")
            try:
                metamodel_config = MetamodelConfig()
                self.metamodel = HolisticMetamodelOrchestrator(metamodel_config)
            except Exception as e:
                self.logger.warning(f"Metamodel initialization deferred: {e}")
        
        # Ontogenesis (self-evolution)
        if ONTOGENESIS_AVAILABLE:
            self.logger.info("Initializing Ontogenesis (self-evolution)...")
            try:
                evolution_config = EvolutionConfig()
                self.evolution_engine = EvolutionEngine(evolution_config)
            except Exception as e:
                self.logger.warning(f"Evolution Engine initialization deferred: {e}")
        
        # VORTEX architecture
        if VORTEX_AVAILABLE:
            self.logger.info("Initializing VORTEX architecture...")
            try:
                vortex_config = VortexConfig()
                self.vortex = VortexOrchestrator(vortex_config)
            except Exception as e:
                self.logger.warning(f"VORTEX initialization deferred: {e}")
    
    async def start_advanced_modules(self):
        """
        Start advanced cognitive modules (async initialization).
        
        Call this after boot() to fully initialize async modules.
        """
        if self.autognosis:
            try:
                await self.autognosis.initialize(self)
                await self.autognosis.start()
                self.logger.info("Autognosis started")
            except Exception as e:
                self.logger.error(f"Autognosis start failed: {e}")
        
        if self.integration_hub:
            try:
                await self.integration_hub.initialize(self)
                if await self.integration_hub.connect():
                    await self.integration_hub.start()
                    self.logger.info("Integration Hub connected and started")
            except Exception as e:
                self.logger.error(f"Integration Hub start failed: {e}")
        
        if self.metamodel:
            try:
                await self.metamodel.initialize(self)
                await self.metamodel.start()
                self.logger.info("Metamodel started")
            except Exception as e:
                self.logger.error(f"Metamodel start failed: {e}")
        
        if self.evolution_engine:
            try:
                await self.evolution_engine.initialize(self)
                await self.evolution_engine.start()
                self.logger.info("Evolution Engine started")
            except Exception as e:
                self.logger.error(f"Evolution Engine start failed: {e}")
        
        if self.vortex:
            try:
                await self.vortex.initialize(self)
                await self.vortex.start()
                self.logger.info("VORTEX started")
            except Exception as e:
                self.logger.error(f"VORTEX start failed: {e}")
    
    async def stop_advanced_modules(self):
        """Stop advanced cognitive modules."""
        if self.vortex:
            await self.vortex.stop()
        if self.evolution_engine:
            await self.evolution_engine.stop()
        if self.metamodel:
            await self.metamodel.stop()
        if self.integration_hub:
            await self.integration_hub.stop()
        if self.autognosis:
            await self.autognosis.stop()
    
    def _register_service(self, service: KernelService):
        """Register a kernel service."""
        self._services[service.service_name] = service
    
    def _start_services(self):
        """Start all registered services."""
        self.logger.info("Starting services...")
        for name, service in self._services.items():
            try:
                service.start()
                self.logger.info(f"  Started: {name}")
            except Exception as e:
                self.logger.error(f"  Failed to start {name}: {e}")
    
    # =========================================================================
    # SHUTDOWN
    # =========================================================================
    
    def shutdown(self) -> bool:
        """
        Shutdown the cognitive kernel.
        
        Gracefully stops all services and releases resources.
        """
        if self.state not in [KernelState.RUNNING, KernelState.PAUSED]:
            return False
        
        self.logger.info("Shutting down kernel...")
        self.state = KernelState.SHUTTING_DOWN
        
        # Notify callbacks
        for callback in self._on_shutdown:
            try:
                callback(self)
            except Exception as e:
                self.logger.error(f"Shutdown callback error: {e}")
        
        # Stop services in reverse order
        for name, service in reversed(list(self._services.items())):
            try:
                service.stop()
                self.logger.info(f"  Stopped: {name}")
            except Exception as e:
                self.logger.error(f"  Failed to stop {name}: {e}")
        
        # Stop scheduler
        if self.scheduler:
            self.scheduler.stop()
        
        # Final cleanup
        self.state = KernelState.TERMINATED
        self.logger.info("Kernel shutdown complete")
        
        return True
    
    # =========================================================================
    # RUNTIME OPERATIONS
    # =========================================================================
    
    def pause(self) -> bool:
        """Pause kernel execution."""
        if self.state != KernelState.RUNNING:
            return False
        
        self.state = KernelState.PAUSED
        self.logger.info("Kernel paused")
        return True
    
    def resume(self) -> bool:
        """Resume kernel execution."""
        if self.state != KernelState.PAUSED:
            return False
        
        self.state = KernelState.RUNNING
        self.logger.info("Kernel resumed")
        return True
    
    def run_cycle(self):
        """Run one cognitive cycle."""
        if self.state != KernelState.RUNNING:
            return
        
        with self._lock:
            self.stats['cycles'] += 1
            
            # Run scheduler cycle
            if self.scheduler:
                self.scheduler.run_cycle()
            
            # Update uptime
            if self.stats['boot_time']:
                self.stats['uptime'] = time.time() - self.stats['boot_time']
    
    # =========================================================================
    # SERVICE ACCESS
    # =========================================================================
    
    def get_service(self, name: str) -> Optional[KernelService]:
        """Get a service by name."""
        return self._services.get(name)
    
    def list_services(self) -> List[str]:
        """List all registered services."""
        return list(self._services.keys())
    
    # =========================================================================
    # COGNITIVE OPERATIONS
    # =========================================================================
    
    def think(self, context: CognitiveContext = None) -> Dict[str, Any]:
        """
        Perform a thinking cycle.
        
        This triggers reasoning, attention updates, and pattern recognition.
        """
        if self.state != KernelState.RUNNING:
            return {'error': 'Kernel not running'}
        
        results = {}
        
        # Focus attention
        if self.ecan:
            focus = self.ecan.get_attentional_focus()
            results['focus_size'] = len(focus)
        
        # Reason about focus
        if self.pln and focus:
            inferences = []
            for atom in focus[:5]:  # Limit to top 5
                inference = self.pln.forward_chain(atom.handle, max_steps=3)
                if inference:
                    inferences.append(inference)
                    self.stats['inferences_made'] += 1
            results['inferences'] = len(inferences)
        
        # Recognize patterns
        if self.pattern:
            status = self.pattern.status()
            results['patterns'] = status.get('patterns_count', 0)
        
        return results
    
    def learn(self, examples: List[Dict[str, Any]]) -> Optional[AtomHandle]:
        """
        Learn from examples.
        
        Uses MOSES to evolve programs that explain the examples.
        """
        if self.state != KernelState.RUNNING:
            return None
        
        if not self.moses:
            return None
        
        # Convert examples to test cases
        test_cases = []
        for ex in examples:
            test_cases.append(ex)
        
        # Run learning
        program = self.moses.learn(test_cases, max_generations=50)
        
        if program and program.fitness > 0.8:
            # Store learned program in AtomSpace
            return self.moses._program_to_atom(program)
        
        return None
    
    def remember(self, query: str) -> List[Atom]:
        """
        Remember (retrieve) knowledge related to a query.
        """
        if self.state != KernelState.RUNNING:
            return []
        
        # Search by name
        results = self.atomspace.get_atoms_by_name(query)
        
        # Boost attention for retrieved atoms
        if self.ecan:
            for atom in results:
                self.ecan.stimulate(atom.handle, 0.3)
        
        return results
    
    def create_goal(
        self,
        name: str,
        description: str = "",
        priority: float = 0.5
    ) -> Optional[str]:
        """Create a new goal for the system to pursue."""
        if self.state != KernelState.RUNNING:
            return None
        
        if not self.emergence:
            return None
        
        goal = CognitiveGoal(
            name=name,
            description=description,
            priority=priority
        )
        
        goal_id = self.emergence.goals.add_goal(goal)
        self.emergence.goals.activate_goal(goal_id)
        
        return goal_id
    
    # =========================================================================
    # STATUS AND MONITORING
    # =========================================================================
    
    def status(self) -> Dict[str, Any]:
        """Get comprehensive kernel status."""
        status = {
            'kernel_id': self.config.kernel_id,
            'version': self.VERSION,
            'state': self.state.name,
            'stats': self.stats.copy(),
            'services': {}
        }
        
        # Get service statuses
        for name, service in self._services.items():
            try:
                status['services'][name] = service.status()
            except:
                status['services'][name] = {'error': 'Status unavailable'}
        
        # AtomSpace stats
        if self.atomspace:
            status['atomspace'] = self.atomspace.get_stats()
        
        return status
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all components."""
        health = {
            'kernel': self.state == KernelState.RUNNING,
            'atomspace': self.atomspace is not None,
            'scheduler': self.scheduler is not None,
        }
        
        for name, service in self._services.items():
            try:
                service_status = service.status()
                health[name] = service_status.get('running', False)
            except:
                health[name] = False
        
        return health
    
    # =========================================================================
    # CALLBACKS
    # =========================================================================
    
    def on_boot(self, callback: Callable[['CognitiveKernel'], None]):
        """Register a callback for kernel boot."""
        self._on_boot.append(callback)
    
    def on_shutdown(self, callback: Callable[['CognitiveKernel'], None]):
        """Register a callback for kernel shutdown."""
        self._on_shutdown.append(callback)


# =============================================================================
# KERNEL FACTORY
# =============================================================================

def create_kernel(
    kernel_id: str = None,
    enable_distribution: bool = False,
    **kwargs
) -> CognitiveKernel:
    """
    Factory function to create a cognitive kernel.
    """
    config = KernelConfig(
        kernel_id=kernel_id or f"kernel_{int(time.time())}",
        enable_distribution=enable_distribution,
        **kwargs
    )
    
    return CognitiveKernel(config)


def boot_kernel(**kwargs) -> CognitiveKernel:
    """
    Create and boot a cognitive kernel in one step.
    """
    kernel = create_kernel(**kwargs)
    kernel.boot()
    return kernel


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Boot the kernel
    print("=" * 60)
    print("OpenCog Inferno AGI Operating System")
    print("=" * 60)
    
    kernel = boot_kernel(
        kernel_id="main-kernel",
        log_level="INFO"
    )
    
    if kernel.state == KernelState.RUNNING:
        print("\nKernel Status:")
        status = kernel.status()
        print(f"  State: {status['state']}")
        print(f"  Services: {len(status['services'])}")
        print(f"  AtomSpace: {status.get('atomspace', {}).get('total_atoms', 0)} atoms")
        
        # Run a few cycles
        print("\nRunning cognitive cycles...")
        for i in range(5):
            kernel.run_cycle()
            result = kernel.think()
            print(f"  Cycle {i+1}: Focus={result.get('focus_size', 0)}, "
                  f"Inferences={result.get('inferences', 0)}")
        
        # Shutdown
        print("\nShutting down...")
        kernel.shutdown()
    
    print("\nDone.")


# Export
__all__ = [
    'KernelState',
    'KernelConfig',
    'CognitiveKernel',
    'create_kernel',
    'boot_kernel',
]
