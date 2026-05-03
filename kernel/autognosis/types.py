"""
Autognosis Type Definitions
===========================

Core type definitions for the hierarchical self-image building system.
Enables the kernel to understand, monitor, and optimize its own cognitive processes.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import hashlib


# =============================================================================
# ENUMERATIONS
# =============================================================================

class SelfAwarenessLevel(Enum):
    """Levels of self-awareness in the autognosis system."""
    UNAWARE = auto()           # No self-awareness
    REACTIVE = auto()          # Basic stimulus-response
    MONITORING = auto()        # Observes own states
    REFLECTIVE = auto()        # Analyzes own patterns
    META_COGNITIVE = auto()    # Reasons about own reasoning
    SELF_MODIFYING = auto()    # Can modify own processes
    TRANSCENDENT = auto()      # Recursive self-awareness


class InsightType(Enum):
    """Types of meta-cognitive insights."""
    RESOURCE_UTILIZATION = auto()
    BEHAVIORAL_STABILITY = auto()
    PERFORMANCE_TREND = auto()
    ANOMALY_DETECTION = auto()
    OPTIMIZATION_OPPORTUNITY = auto()
    SELF_AWARENESS_QUALITY = auto()
    PATTERN_RECOGNITION = auto()
    COGNITIVE_COMPLEXITY = auto()


class InsightPriority(Enum):
    """Priority levels for insights."""
    CRITICAL = auto()
    HIGH = auto()
    MEDIUM = auto()
    LOW = auto()
    INFORMATIONAL = auto()


class OptimizationType(Enum):
    """Types of self-optimization."""
    PARAMETER_TUNING = auto()
    RESOURCE_REALLOCATION = auto()
    PROCESS_RESTRUCTURING = auto()
    ATTENTION_ADJUSTMENT = auto()
    MEMORY_CONSOLIDATION = auto()
    PATTERN_REINFORCEMENT = auto()


# =============================================================================
# OBSERVATION TYPES
# =============================================================================

@dataclass
class ComponentState:
    """State of a single cognitive component."""
    component_id: str
    component_type: str
    is_active: bool
    health_score: float  # 0.0 to 1.0
    load: float  # 0.0 to 1.0
    last_activity: datetime
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'component_id': self.component_id,
            'component_type': self.component_type,
            'is_active': self.is_active,
            'health_score': self.health_score,
            'load': self.load,
            'last_activity': self.last_activity.isoformat(),
            'metrics': self.metrics
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for the system."""
    timestamp: datetime
    cpu_utilization: float
    memory_utilization: float
    atoms_count: int
    inferences_per_second: float
    patterns_detected: int
    attention_spread: float
    cycle_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_utilization': self.cpu_utilization,
            'memory_utilization': self.memory_utilization,
            'atoms_count': self.atoms_count,
            'inferences_per_second': self.inferences_per_second,
            'patterns_detected': self.patterns_detected,
            'attention_spread': self.attention_spread,
            'cycle_time_ms': self.cycle_time_ms
        }


@dataclass
class BehavioralPattern:
    """A detected behavioral pattern."""
    pattern_id: str
    pattern_type: str
    description: str
    frequency: float
    confidence: float
    first_observed: datetime
    last_observed: datetime
    components_involved: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'pattern_id': self.pattern_id,
            'pattern_type': self.pattern_type,
            'description': self.description,
            'frequency': self.frequency,
            'confidence': self.confidence,
            'first_observed': self.first_observed.isoformat(),
            'last_observed': self.last_observed.isoformat(),
            'components_involved': self.components_involved
        }


@dataclass
class Anomaly:
    """A detected anomaly in system behavior."""
    anomaly_id: str
    anomaly_type: str
    severity: float  # 0.0 to 1.0
    description: str
    detected_at: datetime
    affected_components: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'anomaly_id': self.anomaly_id,
            'anomaly_type': self.anomaly_type,
            'severity': self.severity,
            'description': self.description,
            'detected_at': self.detected_at.isoformat(),
            'affected_components': self.affected_components,
            'metrics': self.metrics
        }


@dataclass
class SystemObservation:
    """Complete observation of system state."""
    timestamp: datetime
    component_states: Dict[str, ComponentState]
    performance_metrics: PerformanceMetrics
    behavioral_patterns: List[BehavioralPattern]
    anomalies: List[Anomaly]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'component_states': {k: v.to_dict() for k, v in self.component_states.items()},
            'performance_metrics': self.performance_metrics.to_dict(),
            'behavioral_patterns': [p.to_dict() for p in self.behavioral_patterns],
            'anomalies': [a.to_dict() for a in self.anomalies]
        }


# =============================================================================
# SELF-IMAGE TYPES
# =============================================================================

@dataclass
class MetaReflection:
    """A meta-cognitive reflection about self-understanding."""
    reflection_id: str
    level: int
    content: str
    confidence: float
    generated_at: datetime
    source_insights: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'reflection_id': self.reflection_id,
            'level': self.level,
            'content': self.content,
            'confidence': self.confidence,
            'generated_at': self.generated_at.isoformat(),
            'source_insights': self.source_insights
        }


@dataclass
class SelfImage:
    """Hierarchical self-image at a specific cognitive level."""
    level: int
    image_id: str
    timestamp: datetime
    confidence: float  # Certainty about self-understanding
    
    # Level 0: Direct observation
    component_states: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Level 1+: Pattern analysis
    behavioral_patterns: List[BehavioralPattern] = field(default_factory=list)
    cognitive_processes: List[str] = field(default_factory=list)
    
    # Level 2+: Meta-cognitive
    meta_reflections: List[MetaReflection] = field(default_factory=list)
    self_awareness_indicators: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.image_id:
            # Generate unique ID based on content hash
            content = f"{self.level}:{self.timestamp}:{self.confidence}"
            self.image_id = hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'level': self.level,
            'image_id': self.image_id,
            'timestamp': self.timestamp.isoformat(),
            'confidence': self.confidence,
            'component_states': self.component_states,
            'performance_metrics': self.performance_metrics,
            'behavioral_patterns': [p.to_dict() for p in self.behavioral_patterns],
            'cognitive_processes': self.cognitive_processes,
            'meta_reflections': [r.to_dict() for r in self.meta_reflections],
            'self_awareness_indicators': self.self_awareness_indicators
        }


# =============================================================================
# INSIGHT TYPES
# =============================================================================

@dataclass
class MetaCognitiveInsight:
    """An insight generated from self-analysis."""
    insight_id: str
    insight_type: InsightType
    priority: InsightPriority
    title: str
    description: str
    confidence: float
    generated_at: datetime
    source_level: int
    evidence: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'insight_id': self.insight_id,
            'insight_type': self.insight_type.name,
            'priority': self.priority.name,
            'title': self.title,
            'description': self.description,
            'confidence': self.confidence,
            'generated_at': self.generated_at.isoformat(),
            'source_level': self.source_level,
            'evidence': self.evidence,
            'recommendations': self.recommendations
        }


# =============================================================================
# OPTIMIZATION TYPES
# =============================================================================

@dataclass
class OptimizationOpportunity:
    """A discovered opportunity for self-optimization."""
    opportunity_id: str
    optimization_type: OptimizationType
    priority: InsightPriority
    title: str
    description: str
    expected_improvement: float  # 0.0 to 1.0
    risk_level: float  # 0.0 to 1.0
    discovered_at: datetime
    source_insights: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'opportunity_id': self.opportunity_id,
            'optimization_type': self.optimization_type.name,
            'priority': self.priority.name,
            'title': self.title,
            'description': self.description,
            'expected_improvement': self.expected_improvement,
            'risk_level': self.risk_level,
            'discovered_at': self.discovered_at.isoformat(),
            'source_insights': self.source_insights,
            'parameters': self.parameters
        }


# =============================================================================
# CYCLE RESULT TYPES
# =============================================================================

@dataclass
class AutognosisCycleResult:
    """Result of a complete autognosis cycle."""
    cycle_id: str
    timestamp: datetime
    duration_ms: float
    
    # Self-images at all levels
    self_images: Dict[int, SelfImage]
    
    # Generated insights
    insights: List[MetaCognitiveInsight]
    
    # Discovered optimizations
    optimizations: List[OptimizationOpportunity]
    
    # Overall assessment
    self_awareness_score: float
    metamodel_coherence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cycle_id': self.cycle_id,
            'timestamp': self.timestamp.isoformat(),
            'duration_ms': self.duration_ms,
            'self_images': {k: v.to_dict() for k, v in self.self_images.items()},
            'insights': [i.to_dict() for i in self.insights],
            'optimizations': [o.to_dict() for o in self.optimizations],
            'self_awareness_score': self.self_awareness_score,
            'metamodel_coherence': self.metamodel_coherence
        }


# =============================================================================
# SELF-AWARENESS ASSESSMENT
# =============================================================================

@dataclass
class SelfAwarenessAssessment:
    """Comprehensive assessment of self-awareness quality."""
    timestamp: datetime
    overall_score: float  # 0.0 to 1.0
    level: SelfAwarenessLevel
    
    # Component scores
    pattern_recognition: float
    performance_awareness: float
    meta_reflection_depth: float
    cognitive_complexity: float
    behavioral_stability: float
    
    # Qualitative assessment
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'overall_score': self.overall_score,
            'level': self.level.name,
            'pattern_recognition': self.pattern_recognition,
            'performance_awareness': self.performance_awareness,
            'meta_reflection_depth': self.meta_reflection_depth,
            'cognitive_complexity': self.cognitive_complexity,
            'behavioral_stability': self.behavioral_stability,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'recommendations': self.recommendations
        }
    
    @classmethod
    def compute_level(cls, score: float) -> SelfAwarenessLevel:
        """Compute self-awareness level from score."""
        if score < 0.1:
            return SelfAwarenessLevel.UNAWARE
        elif score < 0.25:
            return SelfAwarenessLevel.REACTIVE
        elif score < 0.4:
            return SelfAwarenessLevel.MONITORING
        elif score < 0.6:
            return SelfAwarenessLevel.REFLECTIVE
        elif score < 0.8:
            return SelfAwarenessLevel.META_COGNITIVE
        elif score < 0.95:
            return SelfAwarenessLevel.SELF_MODIFYING
        else:
            return SelfAwarenessLevel.TRANSCENDENT
