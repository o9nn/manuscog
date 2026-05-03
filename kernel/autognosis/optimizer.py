"""
Autognosis Optimizer Module
===========================

This module implements actual optimization actions based on autognosis insights.
Unlike the original placeholder, this optimizer ACTUALLY modifies system parameters
to improve cognitive performance.

The optimizer can:
1. Adjust ECAN parameters (attention spread, decay rates, focus size)
2. Tune PLN inference depth and confidence thresholds
3. Manage memory pressure by adjusting AtomSpace parameters
4. Rebalance attention allocation based on task demands
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import logging

from .types import (
    OptimizationOpportunity, OptimizationType, InsightPriority,
    MetaCognitiveInsight, InsightType
)

if TYPE_CHECKING:
    from kernel.cognitive_kernel import CognitiveKernel


logger = logging.getLogger("Autognosis.Optimizer")


# =============================================================================
# OPTIMIZATION ACTIONS
# =============================================================================

class OptimizationAction(Enum):
    """Specific optimization actions that can be taken."""
    # ECAN optimizations
    INCREASE_ATTENTION_SPREAD = auto()
    DECREASE_ATTENTION_SPREAD = auto()
    INCREASE_FOCUS_SIZE = auto()
    DECREASE_FOCUS_SIZE = auto()
    ADJUST_DECAY_RATE = auto()
    INCREASE_STIMULUS = auto()
    
    # PLN optimizations
    INCREASE_INFERENCE_DEPTH = auto()
    DECREASE_INFERENCE_DEPTH = auto()
    ADJUST_CONFIDENCE_THRESHOLD = auto()
    ENABLE_BACKGROUND_INFERENCE = auto()
    DISABLE_BACKGROUND_INFERENCE = auto()
    
    # Memory optimizations
    TRIGGER_FORGETTING = auto()
    CONSOLIDATE_MEMORY = auto()
    EXPAND_ATOMSPACE = auto()
    
    # Pattern optimizations
    INCREASE_PATTERN_MINING = auto()
    DECREASE_PATTERN_MINING = auto()


@dataclass
class OptimizationResult:
    """Result of an optimization action."""
    action: OptimizationAction
    success: bool
    timestamp: datetime
    old_value: Any
    new_value: Any
    message: str
    improvement_estimate: float = 0.0


@dataclass
class OptimizationPolicy:
    """Policy for when and how to apply optimizations."""
    auto_optimize: bool = True
    risk_threshold: float = 0.5  # Max risk level for auto-optimization
    min_confidence: float = 0.6  # Min confidence in insight to act
    cooldown_seconds: float = 30.0  # Min time between same optimization
    max_optimizations_per_cycle: int = 3
    
    # Bounds for parameter adjustments
    min_inference_depth: int = 2
    max_inference_depth: int = 10
    min_focus_size: int = 20
    max_focus_size: int = 500
    min_decay_rate: float = 0.9
    max_decay_rate: float = 0.999


# =============================================================================
# AUTOGNOSIS OPTIMIZER
# =============================================================================

class AutognosisOptimizer:
    """
    Implements actual optimization actions based on autognosis insights.
    
    This is the "action" part of the autognosis system - it takes the
    insights and optimization opportunities discovered by the orchestrator
    and actually applies changes to improve system performance.
    """
    
    def __init__(self, policy: OptimizationPolicy = None):
        self.policy = policy or OptimizationPolicy()
        
        # Tracking
        self._optimization_history: List[OptimizationResult] = []
        self._last_optimization_time: Dict[OptimizationAction, datetime] = {}
        self._total_optimizations = 0
        self._successful_optimizations = 0
        
        # Statistics
        self.stats = {
            'optimizations_attempted': 0,
            'optimizations_successful': 0,
            'optimizations_skipped': 0,
            'total_improvement': 0.0
        }
    
    async def apply_optimizations(
        self,
        kernel: 'CognitiveKernel',
        opportunities: List[OptimizationOpportunity],
        insights: List[MetaCognitiveInsight]
    ) -> List[OptimizationResult]:
        """
        Apply optimizations based on discovered opportunities.
        
        Args:
            kernel: The cognitive kernel to optimize
            opportunities: Optimization opportunities from autognosis
            insights: Meta-cognitive insights that inform optimization
            
        Returns:
            List of optimization results
        """
        if not self.policy.auto_optimize:
            return []
        
        results = []
        applied_count = 0
        
        for opportunity in opportunities:
            # Check limits
            if applied_count >= self.policy.max_optimizations_per_cycle:
                logger.debug("Reached max optimizations per cycle")
                break
            
            # Check risk level
            if opportunity.risk_level > self.policy.risk_threshold:
                logger.debug(f"Skipping high-risk optimization: {opportunity.title}")
                self.stats['optimizations_skipped'] += 1
                continue
            
            # Apply the optimization
            result = await self._apply_optimization(kernel, opportunity, insights)
            if result:
                results.append(result)
                if result.success:
                    applied_count += 1
                    self._successful_optimizations += 1
                    self.stats['optimizations_successful'] += 1
                    self.stats['total_improvement'] += result.improvement_estimate
        
        return results
    
    async def _apply_optimization(
        self,
        kernel: 'CognitiveKernel',
        opportunity: OptimizationOpportunity,
        insights: List[MetaCognitiveInsight]
    ) -> Optional[OptimizationResult]:
        """Apply a single optimization."""
        self.stats['optimizations_attempted'] += 1
        
        # Map opportunity type to action
        if opportunity.optimization_type == OptimizationType.RESOURCE_REALLOCATION:
            return await self._optimize_resources(kernel, opportunity, insights)
        elif opportunity.optimization_type == OptimizationType.PARAMETER_TUNING:
            return await self._tune_parameters(kernel, opportunity, insights)
        elif opportunity.optimization_type == OptimizationType.ATTENTION_ADJUSTMENT:
            return await self._adjust_attention(kernel, opportunity, insights)
        elif opportunity.optimization_type == OptimizationType.MEMORY_CONSOLIDATION:
            return await self._consolidate_memory(kernel, opportunity, insights)
        else:
            logger.warning(f"Unknown optimization type: {opportunity.optimization_type}")
            return None
    
    async def _optimize_resources(
        self,
        kernel: 'CognitiveKernel',
        opportunity: OptimizationOpportunity,
        insights: List[MetaCognitiveInsight]
    ) -> OptimizationResult:
        """Optimize resource allocation."""
        timestamp = datetime.now()
        
        # Check for resource underutilization
        underutilized = any(
            i.insight_type == InsightType.RESOURCE_UTILIZATION and
            'underutilized' in i.description.lower()
            for i in insights
        )
        
        if underutilized and kernel.pln:
            # Increase inference depth to use more resources
            old_depth = kernel.pln.max_inference_depth
            new_depth = min(old_depth + 1, self.policy.max_inference_depth)
            
            if new_depth != old_depth:
                kernel.pln.max_inference_depth = new_depth
                
                logger.info(f"Increased PLN inference depth: {old_depth} → {new_depth}")
                
                return OptimizationResult(
                    action=OptimizationAction.INCREASE_INFERENCE_DEPTH,
                    success=True,
                    timestamp=timestamp,
                    old_value=old_depth,
                    new_value=new_depth,
                    message=f"Increased inference depth from {old_depth} to {new_depth}",
                    improvement_estimate=0.1
                )
        
        # If resources are overutilized, decrease depth
        overutilized = any(
            i.insight_type == InsightType.RESOURCE_UTILIZATION and
            'overutilized' in i.description.lower()
            for i in insights
        )
        
        if overutilized and kernel.pln:
            old_depth = kernel.pln.max_inference_depth
            new_depth = max(old_depth - 1, self.policy.min_inference_depth)
            
            if new_depth != old_depth:
                kernel.pln.max_inference_depth = new_depth
                
                return OptimizationResult(
                    action=OptimizationAction.DECREASE_INFERENCE_DEPTH,
                    success=True,
                    timestamp=timestamp,
                    old_value=old_depth,
                    new_value=new_depth,
                    message=f"Decreased inference depth from {old_depth} to {new_depth}",
                    improvement_estimate=0.05
                )
        
        return OptimizationResult(
            action=OptimizationAction.INCREASE_INFERENCE_DEPTH,
            success=False,
            timestamp=timestamp,
            old_value=None,
            new_value=None,
            message="No resource optimization needed",
            improvement_estimate=0.0
        )
    
    async def _tune_parameters(
        self,
        kernel: 'CognitiveKernel',
        opportunity: OptimizationOpportunity,
        insights: List[MetaCognitiveInsight]
    ) -> OptimizationResult:
        """Tune system parameters based on insights."""
        timestamp = datetime.now()
        
        # Check for anomalies that suggest parameter issues
        anomalies = [i for i in insights if i.insight_type == InsightType.ANOMALY_DETECTION]
        
        if anomalies and kernel.ecan:
            # Adjust attention decay rate based on anomaly patterns
            params = kernel.ecan.params
            old_decay = params.sti_decay_rate
            
            # If seeing attention spikes, increase decay
            if any('spike' in a.description.lower() for a in anomalies):
                new_decay = max(old_decay - 0.01, self.policy.min_decay_rate)
            # If attention is too flat, decrease decay
            elif any('flat' in a.description.lower() or 'uniform' in a.description.lower() for a in anomalies):
                new_decay = min(old_decay + 0.005, self.policy.max_decay_rate)
            else:
                new_decay = old_decay
            
            if new_decay != old_decay:
                params.sti_decay_rate = new_decay
                
                return OptimizationResult(
                    action=OptimizationAction.ADJUST_DECAY_RATE,
                    success=True,
                    timestamp=timestamp,
                    old_value=old_decay,
                    new_value=new_decay,
                    message=f"Adjusted attention decay rate: {old_decay:.4f} → {new_decay:.4f}",
                    improvement_estimate=0.05
                )
        
        return OptimizationResult(
            action=OptimizationAction.ADJUST_DECAY_RATE,
            success=False,
            timestamp=timestamp,
            old_value=None,
            new_value=None,
            message="No parameter tuning needed",
            improvement_estimate=0.0
        )
    
    async def _adjust_attention(
        self,
        kernel: 'CognitiveKernel',
        opportunity: OptimizationOpportunity,
        insights: List[MetaCognitiveInsight]
    ) -> OptimizationResult:
        """Adjust attention allocation."""
        timestamp = datetime.now()
        
        if not kernel.ecan:
            return OptimizationResult(
                action=OptimizationAction.INCREASE_ATTENTION_SPREAD,
                success=False,
                timestamp=timestamp,
                old_value=None,
                new_value=None,
                message="ECAN not available",
                improvement_estimate=0.0
            )
        
        params = kernel.ecan.params
        
        # Check if focus is too narrow or too broad
        focus_size = len(kernel.atomspace.get_attentional_focus())
        
        if focus_size < params.max_focus_size * 0.2:
            # Focus is narrow, increase spread
            old_spread = params.spread_decay
            new_spread = min(old_spread + 0.02, 0.95)
            
            if new_spread != old_spread:
                params.spread_decay = new_spread
                
                return OptimizationResult(
                    action=OptimizationAction.INCREASE_ATTENTION_SPREAD,
                    success=True,
                    timestamp=timestamp,
                    old_value=old_spread,
                    new_value=new_spread,
                    message=f"Increased attention spread: {old_spread:.2f} → {new_spread:.2f}",
                    improvement_estimate=0.08
                )
        
        elif focus_size > params.max_focus_size * 0.8:
            # Focus is too broad, decrease spread
            old_spread = params.spread_decay
            new_spread = max(old_spread - 0.02, 0.7)
            
            if new_spread != old_spread:
                params.spread_decay = new_spread
                
                return OptimizationResult(
                    action=OptimizationAction.DECREASE_ATTENTION_SPREAD,
                    success=True,
                    timestamp=timestamp,
                    old_value=old_spread,
                    new_value=new_spread,
                    message=f"Decreased attention spread: {old_spread:.2f} → {new_spread:.2f}",
                    improvement_estimate=0.08
                )
        
        return OptimizationResult(
            action=OptimizationAction.INCREASE_ATTENTION_SPREAD,
            success=False,
            timestamp=timestamp,
            old_value=None,
            new_value=None,
            message="Attention allocation is balanced",
            improvement_estimate=0.0
        )
    
    async def _consolidate_memory(
        self,
        kernel: 'CognitiveKernel',
        opportunity: OptimizationOpportunity,
        insights: List[MetaCognitiveInsight]
    ) -> OptimizationResult:
        """Consolidate memory by removing low-importance atoms."""
        timestamp = datetime.now()
        
        atomspace_size = kernel.atomspace.size()
        
        # Only consolidate if AtomSpace is getting large
        if atomspace_size < 10000:
            return OptimizationResult(
                action=OptimizationAction.CONSOLIDATE_MEMORY,
                success=False,
                timestamp=timestamp,
                old_value=atomspace_size,
                new_value=atomspace_size,
                message="Memory consolidation not needed (AtomSpace small)",
                improvement_estimate=0.0
            )
        
        # Find atoms with very low attention that aren't VLTI
        removed_count = 0
        atoms_to_remove = []
        
        for atom in kernel.atomspace:
            if (atom.attention_value.sti < -0.5 and 
                not atom.attention_value.vlti and
                atom.truth_value.confidence < 0.3):
                atoms_to_remove.append(atom.handle)
        
        # Remove up to 10% of low-importance atoms
        max_remove = int(atomspace_size * 0.1)
        for handle in atoms_to_remove[:max_remove]:
            if kernel.atomspace.remove_atom(handle):
                removed_count += 1
        
        new_size = kernel.atomspace.size()
        
        if removed_count > 0:
            logger.info(f"Memory consolidation: removed {removed_count} low-importance atoms")
            
            return OptimizationResult(
                action=OptimizationAction.CONSOLIDATE_MEMORY,
                success=True,
                timestamp=timestamp,
                old_value=atomspace_size,
                new_value=new_size,
                message=f"Removed {removed_count} low-importance atoms",
                improvement_estimate=0.1 * (removed_count / atomspace_size)
            )
        
        return OptimizationResult(
            action=OptimizationAction.CONSOLIDATE_MEMORY,
            success=False,
            timestamp=timestamp,
            old_value=atomspace_size,
            new_value=new_size,
            message="No atoms eligible for removal",
            improvement_estimate=0.0
        )
    
    def get_optimization_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent optimization history."""
        return [
            {
                'action': r.action.name,
                'success': r.success,
                'timestamp': r.timestamp.isoformat(),
                'old_value': r.old_value,
                'new_value': r.new_value,
                'message': r.message,
                'improvement': r.improvement_estimate
            }
            for r in self._optimization_history[-limit:]
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get optimizer statistics."""
        return {
            **self.stats,
            'success_rate': (
                self.stats['optimizations_successful'] / self.stats['optimizations_attempted']
                if self.stats['optimizations_attempted'] > 0 else 0.0
            ),
            'history_size': len(self._optimization_history)
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'OptimizationAction',
    'OptimizationResult',
    'OptimizationPolicy',
    'AutognosisOptimizer',
]
