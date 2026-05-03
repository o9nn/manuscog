"""
Autognosis Orchestrator Module
==============================

Coordinate the entire autognosis system for hierarchical self-image building.
The main entry point for self-awareness capabilities.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
import time
import asyncio
import logging
import hashlib

from .types import (
    AutognosisCycleResult, SelfImage, MetaCognitiveInsight,
    OptimizationOpportunity, SelfAwarenessAssessment,
    InsightType, InsightPriority, OptimizationType,
    SelfAwarenessLevel
)
from .self_monitor import SelfMonitor, MonitorConfig
from .self_modeler import HierarchicalSelfModeler, ModelerConfig
from .optimizer import AutognosisOptimizer, OptimizationPolicy

if TYPE_CHECKING:
    from kernel.cognitive_kernel import CognitiveKernel


logger = logging.getLogger("Autognosis.Orchestrator")


@dataclass
class AutognosisConfig:
    """Configuration for the autognosis system."""
    cycle_interval: float = 30.0  # seconds between cycles
    max_levels: int = 5
    enable_auto_optimization: bool = False
    optimization_approval_threshold: float = 0.8  # Risk threshold
    insight_retention: int = 100  # Max insights to retain


class AutognosisOrchestrator:
    """
    Coordinate the entire autognosis system.
    
    Responsibilities:
    - Run autognosis cycles
    - Coordinate self-monitor and self-modeler
    - Generate meta-cognitive insights
    - Discover optimization opportunities
    - Assess overall self-awareness
    """
    
    def __init__(self, config: AutognosisConfig = None):
        self.config = config or AutognosisConfig()
        
        # Core components
        self.monitor = SelfMonitor(MonitorConfig())
        self.modeler = HierarchicalSelfModeler(ModelerConfig(
            max_levels=self.config.max_levels
        ))
        self.optimizer = AutognosisOptimizer(OptimizationPolicy(
            auto_optimize=self.config.enable_auto_optimization,
            risk_threshold=self.config.optimization_approval_threshold
        ))
        
        # State
        self.current_self_images: Dict[int, SelfImage] = {}
        self._insights: List[MetaCognitiveInsight] = []
        self._optimizations: List[OptimizationOpportunity] = []
        self._cycle_count = 0
        self._is_running = False
        self._last_cycle_time: Optional[datetime] = None
        
        # Background task
        self._cycle_task: Optional[asyncio.Task] = None
    
    async def initialize(self, kernel: 'CognitiveKernel'):
        """Initialize the autognosis system."""
        logger.info("Initializing Autognosis System...")
        
        # Run initial observation
        await self.monitor.observe_system(kernel)
        
        # Build initial self-images
        for level in range(self.config.max_levels):
            self.current_self_images[level] = await self.modeler.build_self_image(
                level, self.monitor, kernel
            )
        
        logger.info(f"Autognosis initialized with {self.config.max_levels} levels")
    
    async def start(self, kernel: 'CognitiveKernel'):
        """Start the autognosis background cycle."""
        if self._is_running:
            logger.warning("Autognosis already running")
            return
        
        self._is_running = True
        self._cycle_task = asyncio.create_task(self._run_cycle_loop(kernel))
        logger.info("Autognosis background cycle started")
    
    async def stop(self):
        """Stop the autognosis background cycle."""
        self._is_running = False
        if self._cycle_task:
            self._cycle_task.cancel()
            try:
                await self._cycle_task
            except asyncio.CancelledError:
                pass
        logger.info("Autognosis background cycle stopped")
    
    async def _run_cycle_loop(self, kernel: 'CognitiveKernel'):
        """Background loop for autognosis cycles."""
        while self._is_running:
            try:
                await self.run_autognosis_cycle(kernel)
                await asyncio.sleep(self.config.cycle_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Autognosis cycle error: {e}")
                await asyncio.sleep(self.config.cycle_interval)
    
    async def run_autognosis_cycle(self, kernel: 'CognitiveKernel') -> AutognosisCycleResult:
        """
        Run a complete autognosis cycle.
        
        Steps:
        1. Observe system state
        2. Build self-images at all levels
        3. Generate meta-cognitive insights
        4. Discover optimization opportunities
        5. Assess overall self-awareness
        
        Args:
            kernel: The cognitive kernel to analyze
            
        Returns:
            Complete cycle results
        """
        start_time = time.time()
        cycle_id = self._generate_cycle_id()
        timestamp = datetime.now()
        
        logger.debug(f"Starting autognosis cycle {cycle_id}")
        
        # 1. Observe system
        observation = await self.monitor.observe_system(kernel)
        
        # 2. Build self-images at all levels
        for level in range(self.config.max_levels):
            self.current_self_images[level] = await self.modeler.build_self_image(
                level, self.monitor, kernel
            )
        
        # 3. Generate insights
        insights = await self._generate_insights(observation)
        self._insights.extend(insights)
        self._trim_insights()
        
        # 4. Discover optimizations
        optimizations = self._discover_optimizations(insights)
        self._optimizations.extend(optimizations)
        
        # 5. Assess self-awareness
        assessment = self._assess_self_awareness()
        
        # 6. Apply auto-optimizations if enabled
        if self.config.enable_auto_optimization:
            await self._apply_safe_optimizations(kernel, optimizations)
        
        # Complete
        duration_ms = (time.time() - start_time) * 1000
        self._cycle_count += 1
        self._last_cycle_time = timestamp
        
        result = AutognosisCycleResult(
            cycle_id=cycle_id,
            timestamp=timestamp,
            duration_ms=duration_ms,
            self_images=self.current_self_images.copy(),
            insights=insights,
            optimizations=optimizations,
            self_awareness_score=assessment.overall_score,
            metamodel_coherence=self._compute_metamodel_coherence()
        )
        
        logger.debug(f"Autognosis cycle {cycle_id} complete in {duration_ms:.2f}ms")
        
        return result
    
    async def _generate_insights(self, observation) -> List[MetaCognitiveInsight]:
        """Generate meta-cognitive insights from current state."""
        insights = []
        timestamp = datetime.now()
        
        # Insight: Resource utilization
        metrics = observation.performance_metrics
        if metrics.cpu_utilization < 0.3 and metrics.memory_utilization < 0.3:
            insights.append(MetaCognitiveInsight(
                insight_id=self._generate_insight_id('resource'),
                insight_type=InsightType.RESOURCE_UTILIZATION,
                priority=InsightPriority.MEDIUM,
                title="Resource Underutilization",
                description=f"System resources are underutilized (CPU: {metrics.cpu_utilization:.1%}, "
                           f"Memory: {metrics.memory_utilization:.1%}). Consider increasing cognitive load.",
                confidence=0.8,
                generated_at=timestamp,
                source_level=0,
                evidence={
                    'cpu_utilization': metrics.cpu_utilization,
                    'memory_utilization': metrics.memory_utilization
                },
                recommendations=[
                    "Increase inference depth",
                    "Enable more pattern mining",
                    "Expand attention focus"
                ]
            ))
        
        # Insight: Self-awareness quality
        if self.current_self_images:
            avg_confidence = sum(img.confidence for img in self.current_self_images.values()) / len(self.current_self_images)
            if avg_confidence > 0.7:
                insights.append(MetaCognitiveInsight(
                    insight_id=self._generate_insight_id('awareness'),
                    insight_type=InsightType.SELF_AWARENESS_QUALITY,
                    priority=InsightPriority.HIGH,
                    title="High Self-Awareness",
                    description=f"System demonstrates high self-awareness (average confidence: {avg_confidence:.2f})",
                    confidence=avg_confidence,
                    generated_at=timestamp,
                    source_level=max(self.current_self_images.keys()),
                    evidence={
                        'average_confidence': avg_confidence,
                        'levels_analyzed': len(self.current_self_images)
                    },
                    recommendations=[]
                ))
        
        # Insight: Behavioral stability
        patterns = self.monitor.get_detected_patterns()
        if patterns:
            stable_patterns = [p for p in patterns if p.frequency > 0.5]
            if len(stable_patterns) > len(patterns) * 0.7:
                insights.append(MetaCognitiveInsight(
                    insight_id=self._generate_insight_id('stability'),
                    insight_type=InsightType.BEHAVIORAL_STABILITY,
                    priority=InsightPriority.INFORMATIONAL,
                    title="Stable Behavioral Patterns",
                    description=f"System exhibits stable behavioral patterns ({len(stable_patterns)}/{len(patterns)} stable)",
                    confidence=0.75,
                    generated_at=timestamp,
                    source_level=1,
                    evidence={
                        'total_patterns': len(patterns),
                        'stable_patterns': len(stable_patterns)
                    },
                    recommendations=[]
                ))
        
        # Insight: Anomaly detection
        anomalies = observation.anomalies
        if anomalies:
            for anomaly in anomalies[:3]:  # Top 3 anomalies
                insights.append(MetaCognitiveInsight(
                    insight_id=self._generate_insight_id('anomaly'),
                    insight_type=InsightType.ANOMALY_DETECTION,
                    priority=InsightPriority.HIGH if anomaly.severity > 0.7 else InsightPriority.MEDIUM,
                    title=f"Anomaly: {anomaly.anomaly_type}",
                    description=anomaly.description,
                    confidence=0.8,
                    generated_at=timestamp,
                    source_level=0,
                    evidence=anomaly.metrics,
                    recommendations=["Investigate anomaly cause", "Monitor for recurrence"]
                ))
        
        return insights
    
    def _discover_optimizations(self, insights: List[MetaCognitiveInsight]) -> List[OptimizationOpportunity]:
        """Discover optimization opportunities from insights."""
        optimizations = []
        timestamp = datetime.now()
        
        for insight in insights:
            if insight.insight_type == InsightType.RESOURCE_UTILIZATION:
                optimizations.append(OptimizationOpportunity(
                    opportunity_id=self._generate_optimization_id(),
                    optimization_type=OptimizationType.RESOURCE_REALLOCATION,
                    priority=InsightPriority.MEDIUM,
                    title="Increase Cognitive Load",
                    description="Resources are underutilized. Consider increasing cognitive processing.",
                    expected_improvement=0.3,
                    risk_level=0.2,
                    discovered_at=timestamp,
                    source_insights=[insight.insight_id],
                    parameters={
                        'increase_inference_depth': True,
                        'expand_pattern_mining': True
                    }
                ))
            
            elif insight.insight_type == InsightType.ANOMALY_DETECTION:
                if insight.priority in [InsightPriority.HIGH, InsightPriority.CRITICAL]:
                    optimizations.append(OptimizationOpportunity(
                        opportunity_id=self._generate_optimization_id(),
                        optimization_type=OptimizationType.PARAMETER_TUNING,
                        priority=InsightPriority.HIGH,
                        title="Address Anomaly",
                        description=f"Anomaly detected: {insight.title}. Consider parameter adjustment.",
                        expected_improvement=0.2,
                        risk_level=0.4,
                        discovered_at=timestamp,
                        source_insights=[insight.insight_id],
                        parameters={}
                    ))
        
        return optimizations
    
    def _assess_self_awareness(self) -> SelfAwarenessAssessment:
        """Assess overall self-awareness quality."""
        timestamp = datetime.now()
        
        # Compute component scores
        pattern_recognition = self._compute_pattern_recognition_score()
        performance_awareness = self._compute_performance_awareness_score()
        meta_reflection_depth = self._compute_meta_reflection_depth()
        cognitive_complexity = self._compute_cognitive_complexity()
        behavioral_stability = self._compute_behavioral_stability()
        
        # Overall score
        overall_score = (
            pattern_recognition * 0.2 +
            performance_awareness * 0.2 +
            meta_reflection_depth * 0.25 +
            cognitive_complexity * 0.2 +
            behavioral_stability * 0.15
        )
        
        # Determine level
        level = SelfAwarenessAssessment.compute_level(overall_score)
        
        # Identify strengths and weaknesses
        scores = {
            'pattern_recognition': pattern_recognition,
            'performance_awareness': performance_awareness,
            'meta_reflection_depth': meta_reflection_depth,
            'cognitive_complexity': cognitive_complexity,
            'behavioral_stability': behavioral_stability
        }
        
        strengths = [k for k, v in scores.items() if v > 0.7]
        weaknesses = [k for k, v in scores.items() if v < 0.4]
        
        # Generate recommendations
        recommendations = []
        if meta_reflection_depth < 0.5:
            recommendations.append("Increase meta-cognitive processing depth")
        if pattern_recognition < 0.5:
            recommendations.append("Enhance pattern detection capabilities")
        if behavioral_stability < 0.5:
            recommendations.append("Stabilize behavioral patterns")
        
        return SelfAwarenessAssessment(
            timestamp=timestamp,
            overall_score=overall_score,
            level=level,
            pattern_recognition=pattern_recognition,
            performance_awareness=performance_awareness,
            meta_reflection_depth=meta_reflection_depth,
            cognitive_complexity=cognitive_complexity,
            behavioral_stability=behavioral_stability,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
    
    def _compute_pattern_recognition_score(self) -> float:
        """Compute pattern recognition capability score."""
        patterns = self.monitor.get_detected_patterns()
        if not patterns:
            return 0.3
        return min(1.0, len(patterns) / 10.0)
    
    def _compute_performance_awareness_score(self) -> float:
        """Compute performance awareness score."""
        observations = self.monitor.get_recent_observations(10)
        if not observations:
            return 0.3
        return min(1.0, len(observations) / 10.0)
    
    def _compute_meta_reflection_depth(self) -> float:
        """Compute meta-reflection depth score."""
        total_reflections = 0
        for image in self.current_self_images.values():
            total_reflections += len(image.meta_reflections)
        return min(1.0, total_reflections / (self.config.max_levels * 3))
    
    def _compute_cognitive_complexity(self) -> float:
        """Compute cognitive complexity score."""
        return min(1.0, len(self.current_self_images) / self.config.max_levels)
    
    def _compute_behavioral_stability(self) -> float:
        """Compute behavioral stability score."""
        patterns = self.monitor.get_detected_patterns()
        if not patterns:
            return 0.5
        avg_frequency = sum(p.frequency for p in patterns) / len(patterns)
        return avg_frequency
    
    def _compute_metamodel_coherence(self) -> float:
        """Compute overall metamodel coherence."""
        if not self.current_self_images:
            return 0.0
        
        # Coherence based on confidence progression
        confidences = [img.confidence for img in self.current_self_images.values()]
        if len(confidences) < 2:
            return confidences[0] if confidences else 0.0
        
        # Check if confidence decreases appropriately with level
        coherence = 1.0
        for i in range(1, len(confidences)):
            if confidences[i] > confidences[i-1]:
                coherence -= 0.1  # Penalty for increasing confidence at higher levels
        
        return max(0.0, coherence)
    
    async def _apply_safe_optimizations(self, kernel: 'CognitiveKernel',
                                         optimizations: List[OptimizationOpportunity]):
        """Apply optimizations that are below risk threshold using the optimizer."""
        if not self.config.enable_auto_optimization:
            return
        
        # Use the optimizer to actually apply changes
        results = await self.optimizer.apply_optimizations(
            kernel, optimizations, self._insights
        )
        
        for result in results:
            if result.success:
                logger.info(f"Applied optimization: {result.message}")
            else:
                logger.debug(f"Optimization skipped: {result.message}")
    
    def _generate_cycle_id(self) -> str:
        """Generate unique cycle ID."""
        content = f"cycle:{self._cycle_count}:{time.time()}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def _generate_insight_id(self, prefix: str) -> str:
        """Generate unique insight ID."""
        content = f"insight:{prefix}:{len(self._insights)}:{time.time()}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def _generate_optimization_id(self) -> str:
        """Generate unique optimization ID."""
        content = f"opt:{len(self._optimizations)}:{time.time()}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def _trim_insights(self):
        """Trim insights to retention limit."""
        if len(self._insights) > self.config.insight_retention:
            self._insights = self._insights[-self.config.insight_retention:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get autognosis system status."""
        return {
            'is_running': self._is_running,
            'cycle_count': self._cycle_count,
            'last_cycle_time': self._last_cycle_time.isoformat() if self._last_cycle_time else None,
            'self_image_levels': len(self.current_self_images),
            'total_insights': len(self._insights),
            'pending_optimizations': len(self._optimizations),
            'monitor_stats': self.monitor.get_statistics(),
            'modeler_stats': self.modeler.get_statistics(),
            'optimizer_stats': self.optimizer.get_statistics()
        }
    
    def get_self_awareness_report(self) -> Dict[str, Any]:
        """Get comprehensive self-awareness report."""
        assessment = self._assess_self_awareness()
        
        return {
            'assessment': assessment.to_dict(),
            'self_images': {
                level: {
                    'confidence': img.confidence,
                    'reflections': len(img.meta_reflections),
                    'patterns': len(img.behavioral_patterns),
                    'indicators': img.self_awareness_indicators
                }
                for level, img in self.current_self_images.items()
            },
            'recent_insights': [i.to_dict() for i in self._insights[-10:]],
            'pending_optimizations': [o.to_dict() for o in self._optimizations[-5:]]
        }
