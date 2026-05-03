"""
Hierarchical Self-Modeler Module
================================

Build multi-level self-images for recursive self-understanding.
The second layer of the autognosis system.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import logging

from .types import (
    SelfImage, MetaReflection, BehavioralPattern,
    SelfAwarenessLevel
)
from .self_monitor import SelfMonitor

if TYPE_CHECKING:
    from kernel.cognitive_kernel import CognitiveKernel


logger = logging.getLogger("Autognosis.SelfModeler")


@dataclass
class ModelerConfig:
    """Configuration for the self-modeler."""
    max_levels: int = 5
    confidence_decay: float = 0.1  # Confidence decreases per level
    reflection_depth: int = 3  # Max reflections per level


class HierarchicalSelfModeler:
    """
    Build multi-level self-images.
    
    Levels:
    - Level 0: Direct observation (raw states and metrics)
    - Level 1: Pattern analysis (behavioral patterns, trends)
    - Level 2+: Meta-cognitive analysis (analysis of lower levels)
    
    Each level maintains:
    - Confidence scores indicating certainty of self-understanding
    - Meta-reflections documenting insights about that level
    - Behavioral patterns detected at that cognitive level
    """
    
    def __init__(self, config: ModelerConfig = None):
        self.config = config or ModelerConfig()
        
        # Current self-images at each level
        self._self_images: Dict[int, SelfImage] = {}
        
        # History of self-images
        self._image_history: Dict[int, List[SelfImage]] = {}
        
        # Statistics
        self._images_built = 0
        self._reflections_generated = 0
    
    async def build_self_image(self, level: int, monitor: SelfMonitor,
                                kernel: 'CognitiveKernel' = None) -> SelfImage:
        """
        Build self-image at specified cognitive level.
        
        Args:
            level: The cognitive level (0 = direct observation, higher = more meta)
            monitor: The self-monitor providing observations
            kernel: The cognitive kernel (optional, for direct access)
            
        Returns:
            Self-image at the specified level
        """
        if level < 0 or level >= self.config.max_levels:
            raise ValueError(f"Level must be between 0 and {self.config.max_levels - 1}")
        
        timestamp = datetime.now()
        
        if level == 0:
            image = await self._build_direct_observation_image(monitor, kernel, timestamp)
        elif level == 1:
            image = await self._build_pattern_analysis_image(monitor, timestamp)
        else:
            image = await self._build_metacognitive_image(level, monitor, timestamp)
        
        # Store the image
        self._self_images[level] = image
        if level not in self._image_history:
            self._image_history[level] = []
        self._image_history[level].append(image)
        
        # Trim history
        if len(self._image_history[level]) > 100:
            self._image_history[level] = self._image_history[level][-100:]
        
        self._images_built += 1
        
        return image
    
    async def _build_direct_observation_image(self, monitor: SelfMonitor,
                                               kernel: 'CognitiveKernel',
                                               timestamp: datetime) -> SelfImage:
        """Build Level 0: Direct observation image."""
        # Get recent observations
        observations = monitor.get_recent_observations(10)
        
        # Extract component states
        component_states = {}
        if observations:
            latest = observations[-1]
            component_states = {
                k: v.to_dict() for k, v in latest.component_states.items()
            }
        
        # Extract performance metrics
        performance_metrics = {}
        if observations:
            latest = observations[-1]
            performance_metrics = latest.performance_metrics.to_dict()
        
        return SelfImage(
            level=0,
            image_id='',  # Will be auto-generated
            timestamp=timestamp,
            confidence=0.9,  # High confidence for direct observation
            component_states=component_states,
            performance_metrics=performance_metrics,
            behavioral_patterns=[],
            cognitive_processes=self._identify_active_processes(kernel),
            meta_reflections=[],
            self_awareness_indicators={}
        )
    
    async def _build_pattern_analysis_image(self, monitor: SelfMonitor,
                                             timestamp: datetime) -> SelfImage:
        """Build Level 1: Pattern analysis image."""
        # Get detected patterns
        patterns = monitor.get_detected_patterns()
        
        # Analyze patterns
        pattern_summary = self._analyze_patterns(patterns)
        
        # Generate first-order reflections
        reflections = self._generate_pattern_reflections(patterns, timestamp)
        
        # Compute confidence (slightly lower than level 0)
        confidence = 0.9 - self.config.confidence_decay
        
        return SelfImage(
            level=1,
            image_id='',
            timestamp=timestamp,
            confidence=confidence,
            component_states={},
            performance_metrics=pattern_summary,
            behavioral_patterns=patterns,
            cognitive_processes=[],
            meta_reflections=reflections,
            self_awareness_indicators={
                'pattern_recognition': len(patterns) / 10.0,  # Normalized
                'behavioral_stability': self._compute_stability(patterns)
            }
        )
    
    async def _build_metacognitive_image(self, level: int, monitor: SelfMonitor,
                                          timestamp: datetime) -> SelfImage:
        """Build Level 2+: Meta-cognitive analysis image."""
        # Get lower level image
        lower_level = level - 1
        if lower_level not in self._self_images:
            # Build lower level first
            lower_image = await self.build_self_image(lower_level, monitor)
        else:
            lower_image = self._self_images[lower_level]
        
        # Analyze lower level image
        analysis = self._analyze_lower_image(lower_image)
        
        # Generate meta-reflections
        reflections = self._generate_meta_reflections(lower_image, level, timestamp)
        
        # Compute confidence (decreases with level)
        confidence = max(0.1, 0.9 - (level * self.config.confidence_decay))
        
        # Compute self-awareness indicators
        indicators = self._compute_self_awareness_indicators(lower_image, level)
        
        return SelfImage(
            level=level,
            image_id='',
            timestamp=timestamp,
            confidence=confidence,
            component_states={},
            performance_metrics=analysis,
            behavioral_patterns=lower_image.behavioral_patterns,
            cognitive_processes=[],
            meta_reflections=reflections,
            self_awareness_indicators=indicators
        )
    
    def _identify_active_processes(self, kernel: 'CognitiveKernel') -> List[str]:
        """Identify currently active cognitive processes."""
        processes = []
        
        if kernel is None:
            return processes
        
        if kernel.pln:
            processes.append('probabilistic_reasoning')
        if kernel.ecan:
            processes.append('attention_allocation')
        if kernel.pattern:
            processes.append('pattern_recognition')
        if kernel.moses:
            processes.append('evolutionary_learning')
        if kernel.memory_manager:
            processes.append('memory_management')
        if kernel.scheduler:
            processes.append('process_scheduling')
        
        return processes
    
    def _analyze_patterns(self, patterns: List[BehavioralPattern]) -> Dict[str, float]:
        """Analyze behavioral patterns and return summary metrics."""
        if not patterns:
            return {}
        
        return {
            'pattern_count': len(patterns),
            'avg_frequency': sum(p.frequency for p in patterns) / len(patterns),
            'avg_confidence': sum(p.confidence for p in patterns) / len(patterns),
            'pattern_diversity': len(set(p.pattern_type for p in patterns)) / max(1, len(patterns))
        }
    
    def _compute_stability(self, patterns: List[BehavioralPattern]) -> float:
        """Compute behavioral stability from patterns."""
        if not patterns:
            return 0.5
        
        # Stability is high when patterns are consistent
        avg_frequency = sum(p.frequency for p in patterns) / len(patterns)
        avg_confidence = sum(p.confidence for p in patterns) / len(patterns)
        
        return (avg_frequency + avg_confidence) / 2
    
    def _generate_pattern_reflections(self, patterns: List[BehavioralPattern],
                                       timestamp: datetime) -> List[MetaReflection]:
        """Generate reflections about detected patterns."""
        reflections = []
        
        if not patterns:
            reflections.append(MetaReflection(
                reflection_id=self._generate_reflection_id(1, timestamp),
                level=1,
                content="No behavioral patterns detected yet. System may be in early observation phase.",
                confidence=0.7,
                generated_at=timestamp,
                source_insights=[]
            ))
            return reflections
        
        # Reflection on pattern count
        if len(patterns) > 5:
            reflections.append(MetaReflection(
                reflection_id=self._generate_reflection_id(1, timestamp),
                level=1,
                content=f"Rich behavioral repertoire detected with {len(patterns)} distinct patterns.",
                confidence=0.8,
                generated_at=timestamp,
                source_insights=['pattern_count']
            ))
        
        # Reflection on stability
        stability = self._compute_stability(patterns)
        if stability > 0.7:
            reflections.append(MetaReflection(
                reflection_id=self._generate_reflection_id(1, timestamp),
                level=1,
                content=f"System exhibits high behavioral stability (score: {stability:.2f}).",
                confidence=0.8,
                generated_at=timestamp,
                source_insights=['stability_score']
            ))
        
        self._reflections_generated += len(reflections)
        return reflections
    
    def _analyze_lower_image(self, lower_image: SelfImage) -> Dict[str, float]:
        """Analyze a lower-level self-image."""
        return {
            'lower_level_confidence': lower_image.confidence,
            'reflection_count': len(lower_image.meta_reflections),
            'pattern_count': len(lower_image.behavioral_patterns),
            'indicator_count': len(lower_image.self_awareness_indicators)
        }
    
    def _generate_meta_reflections(self, lower_image: SelfImage, level: int,
                                    timestamp: datetime) -> List[MetaReflection]:
        """Generate meta-cognitive reflections about lower-level self-understanding."""
        reflections = []
        
        # Reflection on confidence
        reflections.append(MetaReflection(
            reflection_id=self._generate_reflection_id(level, timestamp),
            level=level,
            content=f"Level {lower_image.level} self-understanding has confidence {lower_image.confidence:.2f}. "
                    f"This {'provides a solid foundation' if lower_image.confidence > 0.7 else 'suggests uncertainty'} "
                    f"for higher-level analysis.",
            confidence=min(0.9, lower_image.confidence + 0.1),
            generated_at=timestamp,
            source_insights=[lower_image.image_id]
        ))
        
        # Reflection on reflections (recursive!)
        if lower_image.meta_reflections:
            reflections.append(MetaReflection(
                reflection_id=self._generate_reflection_id(level, timestamp),
                level=level,
                content=f"Level {lower_image.level} generated {len(lower_image.meta_reflections)} reflections. "
                        f"This indicates {'active' if len(lower_image.meta_reflections) > 2 else 'limited'} "
                        f"meta-cognitive processing at that level.",
                confidence=0.7,
                generated_at=timestamp,
                source_insights=[r.reflection_id for r in lower_image.meta_reflections]
            ))
        
        # Reflection on self-awareness indicators
        if lower_image.self_awareness_indicators:
            avg_indicator = sum(lower_image.self_awareness_indicators.values()) / len(lower_image.self_awareness_indicators)
            reflections.append(MetaReflection(
                reflection_id=self._generate_reflection_id(level, timestamp),
                level=level,
                content=f"Self-awareness indicators at level {lower_image.level} average {avg_indicator:.2f}. "
                        f"This suggests {'strong' if avg_indicator > 0.6 else 'developing'} self-awareness.",
                confidence=0.75,
                generated_at=timestamp,
                source_insights=list(lower_image.self_awareness_indicators.keys())
            ))
        
        self._reflections_generated += len(reflections)
        return reflections[:self.config.reflection_depth]
    
    def _compute_self_awareness_indicators(self, lower_image: SelfImage,
                                            level: int) -> Dict[str, float]:
        """Compute self-awareness indicators for a meta-cognitive level."""
        indicators = {}
        
        # Inherit and transform lower-level indicators
        for key, value in lower_image.self_awareness_indicators.items():
            indicators[f"meta_{key}"] = value * 0.9  # Slight decay
        
        # Add level-specific indicators
        indicators['recursive_depth'] = level / self.config.max_levels
        indicators['reflection_quality'] = (
            len(lower_image.meta_reflections) / self.config.reflection_depth
            if lower_image.meta_reflections else 0.0
        )
        indicators['confidence_calibration'] = lower_image.confidence
        
        return indicators
    
    def _generate_reflection_id(self, level: int, timestamp: datetime) -> str:
        """Generate unique reflection ID."""
        content = f"{level}:{timestamp.isoformat()}:{self._reflections_generated}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def get_current_images(self) -> Dict[int, SelfImage]:
        """Get current self-images at all levels."""
        return self._self_images.copy()
    
    def get_image_history(self, level: int, count: int = 10) -> List[SelfImage]:
        """Get history of self-images at a specific level."""
        if level not in self._image_history:
            return []
        return self._image_history[level][-count:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get modeler statistics."""
        return {
            'images_built': self._images_built,
            'reflections_generated': self._reflections_generated,
            'current_levels': list(self._self_images.keys()),
            'history_sizes': {k: len(v) for k, v in self._image_history.items()}
        }
