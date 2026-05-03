"""
OpenCog Inferno AGI - Knowledge Representation System
=====================================================

This module implements knowledge representation structures:
- Ontology management
- Semantic frames
- Conceptual hierarchies
- Knowledge schemas
- Temporal knowledge

Knowledge is represented in the AtomSpace using a rich
type system that supports reasoning and learning.
"""

from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import threading
import time
import json

from kernel.cognitive.types import (
    Atom, Node, Link, AtomHandle, AtomType,
    TruthValue, AttentionValue
)
from atomspace.hypergraph.atomspace import AtomSpace


# =============================================================================
# ONTOLOGY CLASSES
# =============================================================================

@dataclass
class OntologyClass:
    """
    A class in the ontology hierarchy.
    """
    name: str
    parent_classes: List[str] = field(default_factory=list)
    properties: Dict[str, 'PropertyDefinition'] = field(default_factory=dict)
    instances: Set[AtomHandle] = field(default_factory=set)
    description: str = ""
    handle: Optional[AtomHandle] = None
    
    def is_subclass_of(self, other: str, ontology: 'Ontology') -> bool:
        """Check if this class is a subclass of another."""
        if other in self.parent_classes:
            return True
        for parent in self.parent_classes:
            parent_class = ontology.get_class(parent)
            if parent_class and parent_class.is_subclass_of(other, ontology):
                return True
        return False


@dataclass
class PropertyDefinition:
    """Definition of a property in the ontology."""
    name: str
    domain: str                     # Class this property belongs to
    range_type: str                 # Type of values (class name or primitive)
    cardinality: str = "1"          # "1", "0..1", "0..*", "1..*"
    is_functional: bool = False     # True if single-valued
    inverse_property: Optional[str] = None
    description: str = ""


@dataclass
class OntologyRelation:
    """A relation in the ontology."""
    name: str
    domain: str
    range: str
    is_symmetric: bool = False
    is_transitive: bool = False
    is_reflexive: bool = False
    inverse: Optional[str] = None
    description: str = ""
    handle: Optional[AtomHandle] = None


class Ontology:
    """
    Manages the ontology for the knowledge base.
    
    The ontology defines the conceptual structure of knowledge,
    including classes, properties, and relations.
    """
    
    def __init__(self, atomspace: AtomSpace):
        self.atomspace = atomspace
        
        # Class hierarchy
        self._classes: Dict[str, OntologyClass] = {}
        
        # Relations
        self._relations: Dict[str, OntologyRelation] = {}
        
        # Properties
        self._properties: Dict[str, PropertyDefinition] = {}
        
        self._lock = threading.RLock()
        
        # Initialize base ontology
        self._initialize_base_ontology()
    
    def _initialize_base_ontology(self):
        """Initialize the base ontology with fundamental classes."""
        # Root class
        self.add_class(OntologyClass(
            name="Thing",
            description="The root class of all entities"
        ))
        
        # Basic categories
        self.add_class(OntologyClass(
            name="Entity",
            parent_classes=["Thing"],
            description="A concrete or abstract entity"
        ))
        
        self.add_class(OntologyClass(
            name="Event",
            parent_classes=["Thing"],
            description="An occurrence in time"
        ))
        
        self.add_class(OntologyClass(
            name="Process",
            parent_classes=["Event"],
            description="An ongoing activity"
        ))
        
        self.add_class(OntologyClass(
            name="State",
            parent_classes=["Thing"],
            description="A condition or situation"
        ))
        
        self.add_class(OntologyClass(
            name="Property",
            parent_classes=["Thing"],
            description="An attribute or characteristic"
        ))
        
        self.add_class(OntologyClass(
            name="Relation",
            parent_classes=["Thing"],
            description="A connection between entities"
        ))
        
        # Cognitive classes
        self.add_class(OntologyClass(
            name="Concept",
            parent_classes=["Entity"],
            description="An abstract idea or notion"
        ))
        
        self.add_class(OntologyClass(
            name="Agent",
            parent_classes=["Entity"],
            description="An entity capable of action"
        ))
        
        self.add_class(OntologyClass(
            name="Goal",
            parent_classes=["State"],
            description="A desired state to achieve"
        ))
        
        self.add_class(OntologyClass(
            name="Action",
            parent_classes=["Event"],
            description="An intentional act by an agent"
        ))
        
        # Basic relations
        self.add_relation(OntologyRelation(
            name="isA",
            domain="Thing",
            range="Thing",
            is_transitive=True,
            description="Inheritance relation"
        ))
        
        self.add_relation(OntologyRelation(
            name="partOf",
            domain="Thing",
            range="Thing",
            is_transitive=True,
            description="Part-whole relation"
        ))
        
        self.add_relation(OntologyRelation(
            name="causes",
            domain="Event",
            range="Event",
            is_transitive=True,
            description="Causal relation"
        ))
        
        self.add_relation(OntologyRelation(
            name="similarTo",
            domain="Thing",
            range="Thing",
            is_symmetric=True,
            description="Similarity relation"
        ))
    
    # =========================================================================
    # CLASS MANAGEMENT
    # =========================================================================
    
    def add_class(self, ont_class: OntologyClass) -> AtomHandle:
        """Add a class to the ontology."""
        with self._lock:
            # Create concept node in AtomSpace
            handle = self.atomspace.add_node(
                AtomType.CONCEPT_NODE,
                ont_class.name,
                tv=TruthValue(1.0, 1.0),
                av=AttentionValue(sti=0.3, lti=0.8)
            )
            ont_class.handle = handle
            
            # Create inheritance links to parents
            for parent_name in ont_class.parent_classes:
                parent = self._classes.get(parent_name)
                if parent and parent.handle:
                    self.atomspace.add_link(
                        AtomType.INHERITANCE_LINK,
                        [handle, parent.handle],
                        tv=TruthValue(1.0, 1.0)
                    )
            
            self._classes[ont_class.name] = ont_class
            return handle
    
    def get_class(self, name: str) -> Optional[OntologyClass]:
        """Get a class by name."""
        return self._classes.get(name)
    
    def get_subclasses(self, name: str) -> List[OntologyClass]:
        """Get all subclasses of a class."""
        subclasses = []
        for cls in self._classes.values():
            if name in cls.parent_classes:
                subclasses.append(cls)
        return subclasses
    
    def get_superclasses(self, name: str) -> List[OntologyClass]:
        """Get all superclasses of a class."""
        cls = self._classes.get(name)
        if not cls:
            return []
        
        superclasses = []
        for parent_name in cls.parent_classes:
            parent = self._classes.get(parent_name)
            if parent:
                superclasses.append(parent)
                superclasses.extend(self.get_superclasses(parent_name))
        
        return superclasses
    
    # =========================================================================
    # RELATION MANAGEMENT
    # =========================================================================
    
    def add_relation(self, relation: OntologyRelation) -> AtomHandle:
        """Add a relation to the ontology."""
        with self._lock:
            # Create predicate node
            handle = self.atomspace.add_node(
                AtomType.PREDICATE_NODE,
                relation.name,
                tv=TruthValue(1.0, 1.0),
                av=AttentionValue(sti=0.2, lti=0.7)
            )
            relation.handle = handle
            
            self._relations[relation.name] = relation
            return handle
    
    def get_relation(self, name: str) -> Optional[OntologyRelation]:
        """Get a relation by name."""
        return self._relations.get(name)
    
    # =========================================================================
    # PROPERTY MANAGEMENT
    # =========================================================================
    
    def add_property(self, prop: PropertyDefinition):
        """Add a property definition."""
        with self._lock:
            self._properties[prop.name] = prop
            
            # Add to domain class
            domain_class = self._classes.get(prop.domain)
            if domain_class:
                domain_class.properties[prop.name] = prop
    
    def get_property(self, name: str) -> Optional[PropertyDefinition]:
        """Get a property definition."""
        return self._properties.get(name)
    
    # =========================================================================
    # INSTANCE MANAGEMENT
    # =========================================================================
    
    def create_instance(
        self,
        class_name: str,
        instance_name: str,
        properties: Dict[str, Any] = None
    ) -> Optional[AtomHandle]:
        """Create an instance of a class."""
        ont_class = self._classes.get(class_name)
        if not ont_class:
            return None
        
        # Create instance node
        handle = self.atomspace.add_node(
            AtomType.CONCEPT_NODE,
            instance_name,
            tv=TruthValue(1.0, 0.9),
            av=AttentionValue(sti=0.4, lti=0.5)
        )
        
        # Create membership link
        if ont_class.handle:
            self.atomspace.add_link(
                AtomType.MEMBER_LINK,
                [handle, ont_class.handle],
                tv=TruthValue(1.0, 0.95)
            )
        
        # Add properties
        if properties:
            for prop_name, value in properties.items():
                self.set_property_value(handle, prop_name, value)
        
        ont_class.instances.add(handle)
        return handle
    
    def set_property_value(
        self,
        instance: AtomHandle,
        property_name: str,
        value: Any
    ):
        """Set a property value for an instance."""
        prop_def = self._properties.get(property_name)
        
        # Create property node if needed
        prop_handle = self.atomspace.add_node(
            AtomType.PREDICATE_NODE,
            property_name,
            tv=TruthValue(1.0, 1.0)
        )
        
        # Create value node
        if isinstance(value, (int, float)):
            value_handle = self.atomspace.add_node(
                AtomType.NUMBER_NODE,
                str(value),
                tv=TruthValue(1.0, 1.0)
            )
        elif isinstance(value, str):
            value_handle = self.atomspace.add_node(
                AtomType.CONCEPT_NODE,
                value,
                tv=TruthValue(1.0, 0.9)
            )
        elif isinstance(value, AtomHandle):
            value_handle = value
        else:
            return
        
        # Create evaluation link
        list_handle = self.atomspace.add_link(
            AtomType.LIST_LINK,
            [instance, value_handle]
        )
        
        self.atomspace.add_link(
            AtomType.EVALUATION_LINK,
            [prop_handle, list_handle],
            tv=TruthValue(1.0, 0.9)
        )
    
    def get_property_value(
        self,
        instance: AtomHandle,
        property_name: str
    ) -> Optional[Any]:
        """Get a property value for an instance."""
        # Find evaluation links with this property
        for link in self.atomspace.get_incoming(instance):
            if link.atom_type == AtomType.LIST_LINK:
                for eval_link in self.atomspace.get_incoming(link.handle):
                    if eval_link.atom_type == AtomType.EVALUATION_LINK:
                        pred = self.atomspace.get_atom(eval_link.outgoing[0])
                        if pred and isinstance(pred, Node) and pred.name == property_name:
                            # Get value from list link
                            list_link = self.atomspace.get_atom(eval_link.outgoing[1])
                            if list_link and len(list_link.outgoing) >= 2:
                                value_atom = self.atomspace.get_atom(list_link.outgoing[1])
                                if value_atom and isinstance(value_atom, Node):
                                    if value_atom.atom_type == AtomType.NUMBER_NODE:
                                        return float(value_atom.name)
                                    return value_atom.name
        return None


# =============================================================================
# SEMANTIC FRAMES
# =============================================================================

@dataclass
class FrameSlot:
    """A slot in a semantic frame."""
    name: str
    filler_type: str                # Expected type of filler
    default_value: Any = None
    is_required: bool = False
    constraints: List[str] = field(default_factory=list)


@dataclass
class SemanticFrame:
    """
    A semantic frame representing a structured situation.
    
    Frames are templates for representing stereotypical situations,
    with slots that can be filled with specific values.
    """
    name: str
    parent_frame: Optional[str] = None
    slots: Dict[str, FrameSlot] = field(default_factory=dict)
    description: str = ""
    handle: Optional[AtomHandle] = None
    
    def create_instance(
        self,
        fillers: Dict[str, Any],
        atomspace: AtomSpace
    ) -> AtomHandle:
        """Create an instance of this frame with given fillers."""
        # Create frame instance node
        instance_name = f"{self.name}_instance_{int(time.time() * 1000)}"
        instance_handle = atomspace.add_node(
            AtomType.CONCEPT_NODE,
            instance_name,
            tv=TruthValue(1.0, 0.9)
        )
        
        # Link to frame type
        if self.handle:
            atomspace.add_link(
                AtomType.INHERITANCE_LINK,
                [instance_handle, self.handle],
                tv=TruthValue(1.0, 0.95)
            )
        
        # Fill slots
        for slot_name, value in fillers.items():
            if slot_name in self.slots:
                slot = self.slots[slot_name]
                
                # Create slot predicate
                slot_pred = atomspace.add_node(
                    AtomType.PREDICATE_NODE,
                    f"{self.name}:{slot_name}"
                )
                
                # Create value node
                if isinstance(value, AtomHandle):
                    value_handle = value
                elif isinstance(value, (int, float)):
                    value_handle = atomspace.add_node(AtomType.NUMBER_NODE, str(value))
                else:
                    value_handle = atomspace.add_node(AtomType.CONCEPT_NODE, str(value))
                
                # Create evaluation
                list_link = atomspace.add_link(
                    AtomType.LIST_LINK,
                    [instance_handle, value_handle]
                )
                atomspace.add_link(
                    AtomType.EVALUATION_LINK,
                    [slot_pred, list_link],
                    tv=TruthValue(1.0, 0.9)
                )
        
        return instance_handle


class FrameLibrary:
    """
    Library of semantic frames.
    """
    
    def __init__(self, atomspace: AtomSpace):
        self.atomspace = atomspace
        self._frames: Dict[str, SemanticFrame] = {}
        self._lock = threading.Lock()
        
        # Initialize common frames
        self._initialize_common_frames()
    
    def _initialize_common_frames(self):
        """Initialize commonly used frames."""
        # Action frame
        action_frame = SemanticFrame(
            name="Action",
            slots={
                'agent': FrameSlot('agent', 'Agent', is_required=True),
                'patient': FrameSlot('patient', 'Entity'),
                'instrument': FrameSlot('instrument', 'Entity'),
                'location': FrameSlot('location', 'Location'),
                'time': FrameSlot('time', 'Time'),
                'manner': FrameSlot('manner', 'Property'),
                'purpose': FrameSlot('purpose', 'Goal'),
            },
            description="A general action performed by an agent"
        )
        self.add_frame(action_frame)
        
        # Causation frame
        causation_frame = SemanticFrame(
            name="Causation",
            slots={
                'cause': FrameSlot('cause', 'Event', is_required=True),
                'effect': FrameSlot('effect', 'Event', is_required=True),
                'mechanism': FrameSlot('mechanism', 'Process'),
            },
            description="A causal relationship between events"
        )
        self.add_frame(causation_frame)
        
        # Transfer frame
        transfer_frame = SemanticFrame(
            name="Transfer",
            parent_frame="Action",
            slots={
                'agent': FrameSlot('agent', 'Agent', is_required=True),
                'theme': FrameSlot('theme', 'Entity', is_required=True),
                'source': FrameSlot('source', 'Entity'),
                'destination': FrameSlot('destination', 'Entity'),
            },
            description="Transfer of an entity from source to destination"
        )
        self.add_frame(transfer_frame)
        
        # Communication frame
        comm_frame = SemanticFrame(
            name="Communication",
            parent_frame="Action",
            slots={
                'speaker': FrameSlot('speaker', 'Agent', is_required=True),
                'addressee': FrameSlot('addressee', 'Agent'),
                'message': FrameSlot('message', 'Concept', is_required=True),
                'medium': FrameSlot('medium', 'Entity'),
            },
            description="Communication between agents"
        )
        self.add_frame(comm_frame)
    
    def add_frame(self, frame: SemanticFrame) -> AtomHandle:
        """Add a frame to the library."""
        with self._lock:
            # Create frame node
            handle = self.atomspace.add_node(
                AtomType.DEFINED_FRAME_NODE,
                frame.name,
                tv=TruthValue(1.0, 1.0),
                av=AttentionValue(sti=0.2, lti=0.8)
            )
            frame.handle = handle
            
            # Link to parent frame
            if frame.parent_frame:
                parent = self._frames.get(frame.parent_frame)
                if parent and parent.handle:
                    self.atomspace.add_link(
                        AtomType.INHERITANCE_LINK,
                        [handle, parent.handle],
                        tv=TruthValue(1.0, 1.0)
                    )
            
            self._frames[frame.name] = frame
            return handle
    
    def get_frame(self, name: str) -> Optional[SemanticFrame]:
        """Get a frame by name."""
        return self._frames.get(name)
    
    def create_frame_instance(
        self,
        frame_name: str,
        fillers: Dict[str, Any]
    ) -> Optional[AtomHandle]:
        """Create an instance of a frame."""
        frame = self._frames.get(frame_name)
        if not frame:
            return None
        return frame.create_instance(fillers, self.atomspace)


# =============================================================================
# TEMPORAL KNOWLEDGE
# =============================================================================

class TemporalRelation(Enum):
    """Allen's interval algebra relations."""
    BEFORE = auto()
    AFTER = auto()
    MEETS = auto()
    MET_BY = auto()
    OVERLAPS = auto()
    OVERLAPPED_BY = auto()
    STARTS = auto()
    STARTED_BY = auto()
    FINISHES = auto()
    FINISHED_BY = auto()
    DURING = auto()
    CONTAINS = auto()
    EQUALS = auto()


@dataclass
class TemporalInterval:
    """A temporal interval."""
    start: float
    end: float
    name: Optional[str] = None
    handle: Optional[AtomHandle] = None
    
    def duration(self) -> float:
        return self.end - self.start
    
    def contains(self, time: float) -> bool:
        return self.start <= time <= self.end
    
    def overlaps(self, other: 'TemporalInterval') -> bool:
        return self.start < other.end and other.start < self.end


class TemporalKnowledge:
    """
    Manages temporal knowledge in the AtomSpace.
    """
    
    def __init__(self, atomspace: AtomSpace):
        self.atomspace = atomspace
        self._intervals: Dict[str, TemporalInterval] = {}
        self._lock = threading.Lock()
    
    def create_interval(
        self,
        name: str,
        start: float,
        end: float
    ) -> AtomHandle:
        """Create a temporal interval."""
        interval = TemporalInterval(start=start, end=end, name=name)
        
        # Create time node
        handle = self.atomspace.add_node(
            AtomType.TIME_NODE,
            name,
            tv=TruthValue(1.0, 1.0)
        )
        interval.handle = handle
        
        # Store interval bounds in metadata
        atom = self.atomspace.get_atom(handle)
        if atom:
            atom.metadata['start'] = start
            atom.metadata['end'] = end
        
        self._intervals[name] = interval
        return handle
    
    def add_temporal_relation(
        self,
        interval1: AtomHandle,
        relation: TemporalRelation,
        interval2: AtomHandle
    ) -> AtomHandle:
        """Add a temporal relation between intervals."""
        # Create relation predicate
        rel_pred = self.atomspace.add_node(
            AtomType.PREDICATE_NODE,
            f"temporal:{relation.name}"
        )
        
        # Create evaluation
        list_link = self.atomspace.add_link(
            AtomType.LIST_LINK,
            [interval1, interval2]
        )
        
        return self.atomspace.add_link(
            AtomType.EVALUATION_LINK,
            [rel_pred, list_link],
            tv=TruthValue(1.0, 0.95)
        )
    
    def get_temporal_relation(
        self,
        interval1: TemporalInterval,
        interval2: TemporalInterval
    ) -> TemporalRelation:
        """Compute the temporal relation between two intervals."""
        if interval1.end < interval2.start:
            return TemporalRelation.BEFORE
        elif interval1.start > interval2.end:
            return TemporalRelation.AFTER
        elif interval1.end == interval2.start:
            return TemporalRelation.MEETS
        elif interval1.start == interval2.end:
            return TemporalRelation.MET_BY
        elif interval1.start == interval2.start and interval1.end == interval2.end:
            return TemporalRelation.EQUALS
        elif interval1.start < interval2.start and interval1.end > interval2.end:
            return TemporalRelation.CONTAINS
        elif interval2.start < interval1.start and interval2.end > interval1.end:
            return TemporalRelation.DURING
        elif interval1.start < interval2.start and interval1.end < interval2.end:
            return TemporalRelation.OVERLAPS
        elif interval2.start < interval1.start and interval2.end < interval1.end:
            return TemporalRelation.OVERLAPPED_BY
        elif interval1.start == interval2.start:
            return TemporalRelation.STARTS if interval1.end < interval2.end else TemporalRelation.STARTED_BY
        elif interval1.end == interval2.end:
            return TemporalRelation.FINISHES if interval1.start > interval2.start else TemporalRelation.FINISHED_BY
        
        return TemporalRelation.OVERLAPS  # Default


# =============================================================================
# KNOWLEDGE SCHEMA
# =============================================================================

@dataclass
class KnowledgeSchema:
    """
    A schema for structured knowledge.
    
    Schemas define patterns of knowledge that can be
    instantiated and reasoned about.
    """
    name: str
    variables: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    implications: List[str] = field(default_factory=list)
    handle: Optional[AtomHandle] = None


class KnowledgeBase:
    """
    High-level knowledge base interface.
    
    Integrates ontology, frames, and temporal knowledge.
    """
    
    def __init__(self, atomspace: AtomSpace):
        self.atomspace = atomspace
        
        # Components
        self.ontology = Ontology(atomspace)
        self.frame_library = FrameLibrary(atomspace)
        self.temporal = TemporalKnowledge(atomspace)
        
        # Schemas
        self._schemas: Dict[str, KnowledgeSchema] = {}
        
        self._lock = threading.RLock()
    
    def add_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 0.9
    ) -> AtomHandle:
        """Add a simple fact to the knowledge base."""
        # Create nodes
        subj_handle = self.atomspace.add_node(
            AtomType.CONCEPT_NODE,
            subject,
            tv=TruthValue(1.0, 0.9)
        )
        
        pred_handle = self.atomspace.add_node(
            AtomType.PREDICATE_NODE,
            predicate,
            tv=TruthValue(1.0, 1.0)
        )
        
        obj_handle = self.atomspace.add_node(
            AtomType.CONCEPT_NODE,
            obj,
            tv=TruthValue(1.0, 0.9)
        )
        
        # Create evaluation
        list_link = self.atomspace.add_link(
            AtomType.LIST_LINK,
            [subj_handle, obj_handle]
        )
        
        return self.atomspace.add_link(
            AtomType.EVALUATION_LINK,
            [pred_handle, list_link],
            tv=TruthValue(1.0, confidence)
        )
    
    def add_inheritance(
        self,
        child: str,
        parent: str,
        confidence: float = 0.95
    ) -> AtomHandle:
        """Add an inheritance relationship."""
        child_handle = self.atomspace.add_node(
            AtomType.CONCEPT_NODE,
            child,
            tv=TruthValue(1.0, 0.9)
        )
        
        parent_handle = self.atomspace.add_node(
            AtomType.CONCEPT_NODE,
            parent,
            tv=TruthValue(1.0, 0.9)
        )
        
        return self.atomspace.add_link(
            AtomType.INHERITANCE_LINK,
            [child_handle, parent_handle],
            tv=TruthValue(1.0, confidence)
        )
    
    def query_facts(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        obj: Optional[str] = None
    ) -> List[Tuple[str, str, str, float]]:
        """Query facts from the knowledge base."""
        results = []
        
        for link in self.atomspace.get_atoms_by_type(AtomType.EVALUATION_LINK):
            if len(link.outgoing) < 2:
                continue
            
            pred_atom = self.atomspace.get_atom(link.outgoing[0])
            list_atom = self.atomspace.get_atom(link.outgoing[1])
            
            if not pred_atom or not list_atom:
                continue
            
            if not isinstance(pred_atom, Node):
                continue
            
            if predicate and pred_atom.name != predicate:
                continue
            
            if list_atom.atom_type == AtomType.LIST_LINK and len(list_atom.outgoing) >= 2:
                subj_atom = self.atomspace.get_atom(list_atom.outgoing[0])
                obj_atom = self.atomspace.get_atom(list_atom.outgoing[1])
                
                if not subj_atom or not obj_atom:
                    continue
                
                if not isinstance(subj_atom, Node) or not isinstance(obj_atom, Node):
                    continue
                
                if subject and subj_atom.name != subject:
                    continue
                if obj and obj_atom.name != obj:
                    continue
                
                results.append((
                    subj_atom.name,
                    pred_atom.name,
                    obj_atom.name,
                    link.truth_value.strength
                ))
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        return {
            'classes': len(self.ontology._classes),
            'relations': len(self.ontology._relations),
            'frames': len(self.frame_library._frames),
            'intervals': len(self.temporal._intervals),
            'schemas': len(self._schemas)
        }


# Export
__all__ = [
    'OntologyClass',
    'PropertyDefinition',
    'OntologyRelation',
    'Ontology',
    'FrameSlot',
    'SemanticFrame',
    'FrameLibrary',
    'TemporalRelation',
    'TemporalInterval',
    'TemporalKnowledge',
    'KnowledgeSchema',
    'KnowledgeBase',
]
