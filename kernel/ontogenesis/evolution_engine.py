"""
Evolution Engine Module
=======================

Manages the self-evolution of the cognitive kernel.
Coordinates kernel generation, evaluation, and deployment.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import asyncio
import logging
import json

from .kernel_generator import (
    KernelType, KernelSpec, GeneratedKernel,
    GenerationConfig, KernelGenerator, KernelComposer
)

if TYPE_CHECKING:
    from kernel.cognitive_kernel import CognitiveKernel
    from kernel.integration_hub import ManusIntegrationHub
    from kernel.metamodel import HolisticMetamodelOrchestrator


logger = logging.getLogger("Ontogenesis.EvolutionEngine")


# =============================================================================
# EVOLUTION STATE AND EVENTS
# =============================================================================

class EvolutionState(Enum):
    """State of the evolution engine."""
    IDLE = auto()
    ANALYZING = auto()
    GENERATING = auto()
    EVALUATING = auto()
    PROPOSING = auto()
    DEPLOYING = auto()
    ROLLING_BACK = auto()


class EvolutionTrigger(Enum):
    """Triggers for kernel evolution."""
    PERFORMANCE_DEGRADATION = auto()
    NEW_REQUIREMENTS = auto()
    SCHEDULED = auto()
    MANUAL = auto()
    METAMODEL_GUIDANCE = auto()
    MANUS_DIRECTIVE = auto()


@dataclass
class EvolutionEvent:
    """An evolution event."""
    timestamp: datetime
    trigger: EvolutionTrigger
    kernel_type: KernelType
    old_version: int
    new_version: int
    success: bool
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'trigger': self.trigger.name,
            'kernel_type': self.kernel_type.name,
            'old_version': self.old_version,
            'new_version': self.new_version,
            'success': self.success,
            'details': self.details
        }


@dataclass
class EvolutionProposal:
    """A proposal for kernel evolution."""
    proposal_id: str
    kernel_type: KernelType
    current_kernel: Optional[GeneratedKernel]
    proposed_kernel: GeneratedKernel
    expected_improvement: float
    risks: List[str]
    reversible: bool = True
    requires_approval: bool = True
    approved: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'proposal_id': self.proposal_id,
            'kernel_type': self.kernel_type.name,
            'current_fitness': self.current_kernel.fitness() if self.current_kernel else 0.0,
            'proposed_fitness': self.proposed_kernel.fitness(),
            'expected_improvement': self.expected_improvement,
            'risks': self.risks,
            'reversible': self.reversible,
            'requires_approval': self.requires_approval,
            'approved': self.approved
        }


# =============================================================================
# EVOLUTION ENGINE
# =============================================================================

@dataclass
class EvolutionConfig:
    """Configuration for the evolution engine."""
    enable_auto_evolution: bool = True
    require_manus_approval: bool = True
    min_improvement_threshold: float = 0.1
    max_risk_tolerance: float = 0.3
    evaluation_cycles: int = 10
    rollback_on_failure: bool = True
    evolution_interval: float = 300.0  # seconds


class EvolutionEngine:
    """
    Manages self-evolution of the cognitive kernel.
    
    Coordinates:
    - Performance monitoring
    - Kernel generation
    - Proposal creation
    - Approval workflow
    - Safe deployment
    - Rollback capability
    """
    
    def __init__(self, config: EvolutionConfig = None):
        self.config = config or EvolutionConfig()
        
        # State
        self.state = EvolutionState.IDLE
        self._is_running = False
        
        # Components
        self.generator = KernelGenerator()
        self.composer = KernelComposer()
        
        # Active kernels
        self._active_kernels: Dict[KernelType, GeneratedKernel] = {}
        self._kernel_history: Dict[KernelType, List[GeneratedKernel]] = {}
        
        # Proposals
        self._pending_proposals: Dict[str, EvolutionProposal] = {}
        self._proposal_counter = 0
        
        # Events
        self._events: List[EvolutionEvent] = []
        
        # External references
        self._kernel: Optional['CognitiveKernel'] = None
        self._integration_hub: Optional['ManusIntegrationHub'] = None
        self._metamodel: Optional['HolisticMetamodelOrchestrator'] = None
        
        # Background task
        self._evolution_task: Optional[asyncio.Task] = None
    
    async def initialize(self, kernel: 'CognitiveKernel'):
        """Initialize the evolution engine."""
        logger.info("Initializing Evolution Engine...")
        
        self._kernel = kernel
        
        # Get integration hub reference
        if hasattr(kernel, 'integration_hub') and kernel.integration_hub:
            self._integration_hub = kernel.integration_hub
        
        # Get metamodel reference
        if hasattr(kernel, 'metamodel') and kernel.metamodel:
            self._metamodel = kernel.metamodel
        
        # Initialize default kernels
        await self._initialize_default_kernels()
        
        logger.info("Evolution Engine initialized")
    
    async def start(self):
        """Start the evolution engine."""
        if self._is_running:
            logger.warning("Evolution Engine already running")
            return
        
        self._is_running = True
        
        if self.config.enable_auto_evolution:
            self._evolution_task = asyncio.create_task(self._evolution_loop())
        
        logger.info("Evolution Engine started")
    
    async def stop(self):
        """Stop the evolution engine."""
        self._is_running = False
        
        if self._evolution_task:
            self._evolution_task.cancel()
            try:
                await self._evolution_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Evolution Engine stopped")
    
    async def _initialize_default_kernels(self):
        """Initialize default kernels for each type."""
        for kernel_type in KernelType:
            spec = KernelSpec(
                kernel_type=kernel_type,
                name=f"Default_{kernel_type.name}",
                description=f"Default {kernel_type.name} kernel"
            )
            
            kernel = await self.generator.generate(spec)
            self._active_kernels[kernel_type] = kernel
            self._kernel_history[kernel_type] = [kernel]
    
    async def _evolution_loop(self):
        """Background loop for automatic evolution."""
        while self._is_running:
            try:
                await asyncio.sleep(self.config.evolution_interval)
                await self._check_evolution_opportunities()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Evolution loop error: {e}")
    
    async def _check_evolution_opportunities(self):
        """Check for evolution opportunities."""
        self.state = EvolutionState.ANALYZING
        
        # Check metamodel guidance
        if self._metamodel:
            guidance = self._metamodel.get_evolution_guidance()
            
            if guidance.get('ready_for_evolution'):
                direction = guidance.get('recommended_direction')
                
                if direction == 'transformation':
                    await self._propose_evolution(
                        KernelType.EVOLUTION,
                        EvolutionTrigger.METAMODEL_GUIDANCE
                    )
                elif direction == 'creation':
                    await self._propose_evolution(
                        KernelType.LEARNING,
                        EvolutionTrigger.METAMODEL_GUIDANCE
                    )
        
        # Check performance of active kernels
        for kernel_type, kernel in self._active_kernels.items():
            if kernel.fitness() < 0.5:
                await self._propose_evolution(
                    kernel_type,
                    EvolutionTrigger.PERFORMANCE_DEGRADATION
                )
        
        self.state = EvolutionState.IDLE
    
    async def _propose_evolution(self, kernel_type: KernelType,
                                  trigger: EvolutionTrigger) -> Optional[EvolutionProposal]:
        """Create an evolution proposal."""
        self.state = EvolutionState.GENERATING
        
        current_kernel = self._active_kernels.get(kernel_type)
        
        # Generate new kernel
        spec = KernelSpec(
            kernel_type=kernel_type,
            name=f"Evolved_{kernel_type.name}_v{self._get_next_version(kernel_type)}",
            description=f"Evolved {kernel_type.name} kernel"
        )
        
        new_kernel = await self.generator.generate(spec)
        
        # Calculate expected improvement
        current_fitness = current_kernel.fitness() if current_kernel else 0.0
        expected_improvement = new_kernel.fitness() - current_fitness
        
        # Check if improvement meets threshold
        if expected_improvement < self.config.min_improvement_threshold:
            logger.info(f"Improvement {expected_improvement:.4f} below threshold, skipping")
            self.state = EvolutionState.IDLE
            return None
        
        # Assess risks
        risks = self._assess_risks(current_kernel, new_kernel)
        
        # Create proposal
        self._proposal_counter += 1
        proposal = EvolutionProposal(
            proposal_id=f"prop_{self._proposal_counter:04d}",
            kernel_type=kernel_type,
            current_kernel=current_kernel,
            proposed_kernel=new_kernel,
            expected_improvement=expected_improvement,
            risks=risks,
            requires_approval=self.config.require_manus_approval
        )
        
        self._pending_proposals[proposal.proposal_id] = proposal
        
        # Request approval if needed
        if proposal.requires_approval and self._integration_hub:
            self.state = EvolutionState.PROPOSING
            approval = await self._request_manus_approval(proposal)
            proposal.approved = approval
        else:
            proposal.approved = True
        
        # Deploy if approved
        if proposal.approved:
            await self._deploy_kernel(proposal)
        
        self.state = EvolutionState.IDLE
        return proposal
    
    def _assess_risks(self, current: Optional[GeneratedKernel],
                      proposed: GeneratedKernel) -> List[str]:
        """Assess risks of kernel evolution."""
        risks = []
        
        if proposed.stability < 0.5:
            risks.append("Low stability in proposed kernel")
        
        if current and proposed.efficiency < current.efficiency:
            risks.append("Efficiency degradation")
        
        if proposed.accuracy < 0.7:
            risks.append("Accuracy below acceptable threshold")
        
        if not proposed.tableau.is_explicit():
            risks.append("Implicit method may have convergence issues")
        
        return risks
    
    async def _request_manus_approval(self, proposal: EvolutionProposal) -> bool:
        """Request approval from Primary Manus."""
        if not self._integration_hub:
            return True  # Auto-approve if no hub
        
        try:
            approval = await self._integration_hub.propose_evolution(
                evolution_type=proposal.kernel_type.name,
                description=f"Evolve {proposal.kernel_type.name} kernel",
                changes=[{
                    'type': 'kernel_replacement',
                    'from_version': proposal.current_kernel.version if proposal.current_kernel else 0,
                    'to_version': proposal.proposed_kernel.version
                }],
                expected_benefits=[f"Fitness improvement: {proposal.expected_improvement:.4f}"],
                risks=proposal.risks,
                reversible=proposal.reversible,
                confidence=proposal.proposed_kernel.fitness()
            )
            
            if approval:
                from kernel.integration_hub import ApprovalStatus
                return approval.status == ApprovalStatus.APPROVED
            
            return False
        except Exception as e:
            logger.error(f"Failed to request approval: {e}")
            return False
    
    async def _deploy_kernel(self, proposal: EvolutionProposal):
        """Deploy a new kernel."""
        self.state = EvolutionState.DEPLOYING
        
        kernel_type = proposal.kernel_type
        old_version = proposal.current_kernel.version if proposal.current_kernel else 0
        new_version = proposal.proposed_kernel.version
        
        try:
            # Store old kernel in history
            if kernel_type in self._active_kernels:
                history = self._kernel_history.setdefault(kernel_type, [])
                history.append(self._active_kernels[kernel_type])
            
            # Deploy new kernel
            self._active_kernels[kernel_type] = proposal.proposed_kernel
            
            # Record event
            event = EvolutionEvent(
                timestamp=datetime.now(),
                trigger=EvolutionTrigger.MANUAL,  # TODO: Track actual trigger
                kernel_type=kernel_type,
                old_version=old_version,
                new_version=new_version,
                success=True,
                details={'proposal_id': proposal.proposal_id}
            )
            self._events.append(event)
            
            logger.info(f"Deployed {kernel_type.name} kernel v{new_version}")
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            
            if self.config.rollback_on_failure:
                await self._rollback(kernel_type)
    
    async def _rollback(self, kernel_type: KernelType):
        """Rollback to previous kernel version."""
        self.state = EvolutionState.ROLLING_BACK
        
        history = self._kernel_history.get(kernel_type, [])
        
        if history:
            previous = history.pop()
            self._active_kernels[kernel_type] = previous
            logger.info(f"Rolled back {kernel_type.name} to v{previous.version}")
        else:
            logger.warning(f"No history for {kernel_type.name}, cannot rollback")
        
        self.state = EvolutionState.IDLE
    
    def _get_next_version(self, kernel_type: KernelType) -> int:
        """Get next version number for a kernel type."""
        current = self._active_kernels.get(kernel_type)
        if current:
            return current.version + 1
        return 1
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    async def evolve(self, kernel_type: KernelType,
                     trigger: EvolutionTrigger = EvolutionTrigger.MANUAL) -> Optional[EvolutionProposal]:
        """
        Manually trigger evolution for a kernel type.
        
        Args:
            kernel_type: Type of kernel to evolve
            trigger: Trigger reason
            
        Returns:
            Evolution proposal if created
        """
        return await self._propose_evolution(kernel_type, trigger)
    
    def get_active_kernel(self, kernel_type: KernelType) -> Optional[GeneratedKernel]:
        """Get the active kernel for a type."""
        return self._active_kernels.get(kernel_type)
    
    def get_all_active_kernels(self) -> Dict[KernelType, GeneratedKernel]:
        """Get all active kernels."""
        return self._active_kernels.copy()
    
    def get_pending_proposals(self) -> List[EvolutionProposal]:
        """Get pending evolution proposals."""
        return list(self._pending_proposals.values())
    
    def approve_proposal(self, proposal_id: str) -> bool:
        """Manually approve a proposal."""
        proposal = self._pending_proposals.get(proposal_id)
        if proposal:
            proposal.approved = True
            asyncio.create_task(self._deploy_kernel(proposal))
            return True
        return False
    
    def reject_proposal(self, proposal_id: str) -> bool:
        """Reject a proposal."""
        proposal = self._pending_proposals.get(proposal_id)
        if proposal:
            proposal.approved = False
            del self._pending_proposals[proposal_id]
            return True
        return False
    
    def get_evolution_history(self) -> List[Dict[str, Any]]:
        """Get evolution event history."""
        return [e.to_dict() for e in self._events]
    
    def get_status(self) -> Dict[str, Any]:
        """Get evolution engine status."""
        return {
            'state': self.state.name,
            'is_running': self._is_running,
            'active_kernels': {
                kt.name: k.to_dict() for kt, k in self._active_kernels.items()
            },
            'pending_proposals': len(self._pending_proposals),
            'total_events': len(self._events),
            'config': {
                'auto_evolution': self.config.enable_auto_evolution,
                'require_approval': self.config.require_manus_approval,
                'improvement_threshold': self.config.min_improvement_threshold
            }
        }
