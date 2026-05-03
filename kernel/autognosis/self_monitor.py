"""
Self-Monitor Module
===================

Continuous observation of system states and behaviors.
The first layer of the autognosis system.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
import time
import statistics
import logging

from .types import (
    ComponentState, PerformanceMetrics, BehavioralPattern,
    Anomaly, SystemObservation
)

if TYPE_CHECKING:
    from kernel.cognitive_kernel import CognitiveKernel


logger = logging.getLogger("Autognosis.SelfMonitor")


@dataclass
class MonitorConfig:
    """Configuration for the self-monitor."""
    observation_interval: float = 1.0  # seconds
    pattern_window_size: int = 100  # observations
    anomaly_threshold: float = 2.0  # standard deviations
    max_history_size: int = 1000


class SelfMonitor:
    """
    Continuous observation of system states and behaviors.
    
    Responsibilities:
    - Observe current system state
    - Detect behavioral patterns
    - Identify anomalies
    - Track performance trends
    """
    
    def __init__(self, config: MonitorConfig = None):
        self.config = config or MonitorConfig()
        
        # Observation history
        self._observations: List[SystemObservation] = []
        self._metrics_history: List[PerformanceMetrics] = []
        
        # Pattern detection state
        self._detected_patterns: Dict[str, BehavioralPattern] = {}
        self._pattern_counts: Dict[str, int] = {}
        
        # Anomaly detection state
        self._baseline_metrics: Dict[str, List[float]] = {}
        self._detected_anomalies: List[Anomaly] = []
        
        # Statistics
        self._total_observations = 0
        self._patterns_detected = 0
        self._anomalies_detected = 0
    
    async def observe_system(self, kernel: 'CognitiveKernel') -> SystemObservation:
        """
        Observe current system state.
        
        Args:
            kernel: The cognitive kernel to observe
            
        Returns:
            Complete observation of system state
        """
        timestamp = datetime.now()
        
        # Observe component states
        component_states = self._observe_components(kernel)
        
        # Measure performance
        performance_metrics = self._measure_performance(kernel)
        
        # Detect patterns
        behavioral_patterns = self._detect_patterns()
        
        # Detect anomalies
        anomalies = self._detect_anomalies(performance_metrics)
        
        # Create observation
        observation = SystemObservation(
            timestamp=timestamp,
            component_states=component_states,
            performance_metrics=performance_metrics,
            behavioral_patterns=behavioral_patterns,
            anomalies=anomalies
        )
        
        # Update history
        self._update_history(observation)
        self._total_observations += 1
        
        return observation
    
    def _observe_components(self, kernel: 'CognitiveKernel') -> Dict[str, ComponentState]:
        """Observe state of all cognitive components."""
        components = {}
        
        # AtomSpace
        if kernel.atomspace:
            components['atomspace'] = ComponentState(
                component_id='atomspace',
                component_type='knowledge_base',
                is_active=True,
                health_score=1.0,
                load=self._estimate_atomspace_load(kernel),
                last_activity=datetime.now(),
                metrics={
                    'atom_count': kernel.atomspace.size(),
                    'node_count': len([a for a in kernel.atomspace 
                                      if hasattr(a, 'name')]),
                    'link_count': len([a for a in kernel.atomspace 
                                      if hasattr(a, 'outgoing')])
                }
            )
        
        # PLN Engine
        if kernel.pln:
            components['pln'] = ComponentState(
                component_id='pln',
                component_type='reasoning_engine',
                is_active=True,
                health_score=1.0,
                load=0.0,  # Would need actual load tracking
                last_activity=datetime.now(),
                metrics={
                    'rules_available': len(kernel.pln.rules) if hasattr(kernel.pln, 'rules') else 0
                }
            )
        
        # ECAN
        if kernel.ecan:
            components['ecan'] = ComponentState(
                component_id='ecan',
                component_type='attention_network',
                is_active=kernel.ecan.is_running if hasattr(kernel.ecan, 'is_running') else True,
                health_score=1.0,
                load=0.0,
                last_activity=datetime.now(),
                metrics={}
            )
        
        # Pattern Recognition
        if kernel.pattern:
            components['pattern'] = ComponentState(
                component_id='pattern',
                component_type='pattern_recognition',
                is_active=True,
                health_score=1.0,
                load=0.0,
                last_activity=datetime.now(),
                metrics={}
            )
        
        # MOSES Learning
        if kernel.moses:
            components['moses'] = ComponentState(
                component_id='moses',
                component_type='learning_engine',
                is_active=True,
                health_score=1.0,
                load=0.0,
                last_activity=datetime.now(),
                metrics={}
            )
        
        # Memory Manager
        if kernel.memory_manager:
            components['memory'] = ComponentState(
                component_id='memory',
                component_type='memory_manager',
                is_active=True,
                health_score=1.0,
                load=0.0,
                last_activity=datetime.now(),
                metrics={}
            )
        
        # Scheduler
        if kernel.scheduler:
            components['scheduler'] = ComponentState(
                component_id='scheduler',
                component_type='process_scheduler',
                is_active=True,
                health_score=1.0,
                load=0.0,
                last_activity=datetime.now(),
                metrics={}
            )
        
        return components
    
    def _measure_performance(self, kernel: 'CognitiveKernel') -> PerformanceMetrics:
        """Measure current performance metrics."""
        import psutil
        
        process = psutil.Process()
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_utilization=process.cpu_percent() / 100.0,
            memory_utilization=process.memory_percent() / 100.0,
            atoms_count=kernel.atomspace.size() if kernel.atomspace else 0,
            inferences_per_second=kernel.stats.get('inferences_made', 0) / max(1, kernel.stats.get('uptime', 1)),
            patterns_detected=kernel.stats.get('patterns_found', 0),
            attention_spread=self._compute_attention_spread(kernel),
            cycle_time_ms=kernel.stats.get('last_cycle_time_ms', 0)
        )
    
    def _detect_patterns(self) -> List[BehavioralPattern]:
        """Detect behavioral patterns from observation history."""
        patterns = []
        
        if len(self._metrics_history) < 10:
            return patterns
        
        # Pattern 1: Stable performance
        recent_cpu = [m.cpu_utilization for m in self._metrics_history[-10:]]
        if statistics.stdev(recent_cpu) < 0.05:
            pattern = self._get_or_create_pattern(
                'stable_cpu',
                'performance',
                'CPU utilization is stable'
            )
            pattern.last_observed = datetime.now()
            pattern.frequency = min(1.0, pattern.frequency + 0.1)
            patterns.append(pattern)
        
        # Pattern 2: Growing knowledge base
        if len(self._metrics_history) >= 20:
            old_atoms = self._metrics_history[-20].atoms_count
            new_atoms = self._metrics_history[-1].atoms_count
            if new_atoms > old_atoms * 1.1:
                pattern = self._get_or_create_pattern(
                    'growing_knowledge',
                    'learning',
                    'Knowledge base is growing'
                )
                pattern.last_observed = datetime.now()
                pattern.frequency = min(1.0, pattern.frequency + 0.1)
                patterns.append(pattern)
        
        # Pattern 3: High inference activity
        recent_inferences = [m.inferences_per_second for m in self._metrics_history[-10:]]
        avg_inferences = statistics.mean(recent_inferences)
        if avg_inferences > 10:
            pattern = self._get_or_create_pattern(
                'high_inference',
                'reasoning',
                'High inference activity detected'
            )
            pattern.last_observed = datetime.now()
            pattern.frequency = min(1.0, pattern.frequency + 0.1)
            patterns.append(pattern)
        
        return patterns
    
    def _detect_anomalies(self, current_metrics: PerformanceMetrics) -> List[Anomaly]:
        """Detect anomalies in current metrics."""
        anomalies = []
        
        # Update baseline
        self._update_baseline(current_metrics)
        
        if len(self._metrics_history) < 20:
            return anomalies
        
        # Check each metric for anomalies
        metrics_to_check = [
            ('cpu_utilization', current_metrics.cpu_utilization),
            ('memory_utilization', current_metrics.memory_utilization),
            ('cycle_time_ms', current_metrics.cycle_time_ms)
        ]
        
        for metric_name, current_value in metrics_to_check:
            if metric_name in self._baseline_metrics:
                baseline = self._baseline_metrics[metric_name]
                if len(baseline) >= 10:
                    mean = statistics.mean(baseline)
                    stdev = statistics.stdev(baseline) if len(baseline) > 1 else 0.1
                    
                    if stdev > 0:
                        z_score = abs(current_value - mean) / stdev
                        if z_score > self.config.anomaly_threshold:
                            anomaly = Anomaly(
                                anomaly_id=f"anomaly_{metric_name}_{int(time.time())}",
                                anomaly_type=f"{metric_name}_deviation",
                                severity=min(1.0, z_score / 5.0),
                                description=f"{metric_name} deviated {z_score:.2f} standard deviations from baseline",
                                detected_at=datetime.now(),
                                affected_components=[],
                                metrics={
                                    'current_value': current_value,
                                    'baseline_mean': mean,
                                    'baseline_stdev': stdev,
                                    'z_score': z_score
                                }
                            )
                            anomalies.append(anomaly)
                            self._anomalies_detected += 1
        
        return anomalies
    
    def _get_or_create_pattern(self, pattern_id: str, pattern_type: str, 
                                description: str) -> BehavioralPattern:
        """Get existing pattern or create new one."""
        if pattern_id not in self._detected_patterns:
            self._detected_patterns[pattern_id] = BehavioralPattern(
                pattern_id=pattern_id,
                pattern_type=pattern_type,
                description=description,
                frequency=0.1,
                confidence=0.5,
                first_observed=datetime.now(),
                last_observed=datetime.now()
            )
            self._patterns_detected += 1
        return self._detected_patterns[pattern_id]
    
    def _update_history(self, observation: SystemObservation):
        """Update observation history."""
        self._observations.append(observation)
        self._metrics_history.append(observation.performance_metrics)
        
        # Trim history if needed
        if len(self._observations) > self.config.max_history_size:
            self._observations = self._observations[-self.config.max_history_size:]
        if len(self._metrics_history) > self.config.max_history_size:
            self._metrics_history = self._metrics_history[-self.config.max_history_size:]
    
    def _update_baseline(self, metrics: PerformanceMetrics):
        """Update baseline metrics for anomaly detection."""
        metrics_dict = {
            'cpu_utilization': metrics.cpu_utilization,
            'memory_utilization': metrics.memory_utilization,
            'cycle_time_ms': metrics.cycle_time_ms,
            'inferences_per_second': metrics.inferences_per_second
        }
        
        for name, value in metrics_dict.items():
            if name not in self._baseline_metrics:
                self._baseline_metrics[name] = []
            self._baseline_metrics[name].append(value)
            
            # Keep only recent values
            if len(self._baseline_metrics[name]) > self.config.pattern_window_size:
                self._baseline_metrics[name] = self._baseline_metrics[name][-self.config.pattern_window_size:]
    
    def _estimate_atomspace_load(self, kernel: 'CognitiveKernel') -> float:
        """Estimate AtomSpace load based on recent activity."""
        if not kernel.atomspace:
            return 0.0
        
        # Simple estimate based on atom count relative to max
        max_atoms = kernel.config.max_atoms if hasattr(kernel.config, 'max_atoms') else 1000000
        return min(1.0, kernel.atomspace.size() / max_atoms)
    
    def _compute_attention_spread(self, kernel: 'CognitiveKernel') -> float:
        """Compute how spread out attention is across atoms."""
        if not kernel.atomspace or not kernel.ecan:
            return 0.0
        
        # Would need actual attention values
        # For now, return a placeholder
        return 0.5
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get monitor statistics."""
        return {
            'total_observations': self._total_observations,
            'patterns_detected': self._patterns_detected,
            'anomalies_detected': self._anomalies_detected,
            'history_size': len(self._observations),
            'active_patterns': len(self._detected_patterns)
        }
    
    def get_recent_observations(self, count: int = 10) -> List[SystemObservation]:
        """Get recent observations."""
        return self._observations[-count:]
    
    def get_detected_patterns(self) -> List[BehavioralPattern]:
        """Get all detected patterns."""
        return list(self._detected_patterns.values())
    
    def get_recent_anomalies(self, count: int = 10) -> List[Anomaly]:
        """Get recent anomalies."""
        return self._detected_anomalies[-count:]
