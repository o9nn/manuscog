"""
Integration Hub Type Definitions
================================

Core type definitions for the Manus Integration Hub.
Enables communication between ManusCog and Primary Manus.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import hashlib
import json


# =============================================================================
# ENUMERATIONS
# =============================================================================

class ProtocolType(Enum):
    """Communication protocol types."""
    MCP = auto()       # Model Context Protocol
    REST = auto()      # REST API
    WEBSOCKET = auto() # WebSocket
    FILE = auto()      # File-based communication


class MessagePriority(Enum):
    """Message priority levels."""
    CRITICAL = auto()
    HIGH = auto()
    MEDIUM = auto()
    LOW = auto()
    BACKGROUND = auto()


class MessageDirection(Enum):
    """Direction of message flow."""
    TO_MANUS = auto()      # From ManusCog to Primary Manus
    FROM_MANUS = auto()    # From Primary Manus to ManusCog
    BIDIRECTIONAL = auto() # Both directions


class ConnectionState(Enum):
    """Connection state with Primary Manus."""
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    AUTHENTICATED = auto()
    SYNCING = auto()
    READY = auto()
    ERROR = auto()


class RequestType(Enum):
    """Types of requests from ManusCog to Manus."""
    GUIDANCE_REQUEST = "guidance_request"
    ANALYSIS_REQUEST = "analysis_request"
    EVOLUTION_PROPOSAL = "evolution_proposal"
    KNOWLEDGE_QUERY = "knowledge_query"
    COLLABORATION_INVITE = "collaboration_invite"
    STATUS_REPORT = "status_report"
    ERROR_REPORT = "error_report"
    TASK_COMPLETION = "task_completion"


class ResponseType(Enum):
    """Types of responses from Manus to ManusCog."""
    GUIDANCE_RESPONSE = "guidance_response"
    ANALYSIS_RESULT = "analysis_result"
    EVOLUTION_APPROVAL = "evolution_approval"
    KNOWLEDGE_INJECTION = "knowledge_injection"
    TASK_ASSIGNMENT = "task_assignment"
    CONFIGURATION_UPDATE = "configuration_update"
    COMMAND = "command"
    ACKNOWLEDGMENT = "acknowledgment"


class ApprovalStatus(Enum):
    """Status of approval requests."""
    PENDING = auto()
    APPROVED = auto()
    REJECTED = auto()
    NEEDS_REVISION = auto()
    DEFERRED = auto()


# =============================================================================
# MESSAGE TYPES
# =============================================================================

@dataclass
class MessageHeader:
    """Header for all integration messages."""
    message_id: str
    timestamp: datetime
    direction: MessageDirection
    priority: MessagePriority
    correlation_id: Optional[str] = None  # For request-response correlation
    ttl_seconds: int = 300  # Time to live
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'message_id': self.message_id,
            'timestamp': self.timestamp.isoformat(),
            'direction': self.direction.name,
            'priority': self.priority.name,
            'correlation_id': self.correlation_id,
            'ttl_seconds': self.ttl_seconds
        }
    
    @classmethod
    def create(cls, direction: MessageDirection, 
               priority: MessagePriority = MessagePriority.MEDIUM,
               correlation_id: Optional[str] = None) -> 'MessageHeader':
        """Create a new message header."""
        import time
        content = f"{direction.name}:{time.time()}"
        message_id = hashlib.sha256(content.encode()).hexdigest()[:16]
        return cls(
            message_id=message_id,
            timestamp=datetime.now(),
            direction=direction,
            priority=priority,
            correlation_id=correlation_id
        )


@dataclass
class IntegrationMessage:
    """Base class for all integration messages."""
    header: MessageHeader
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'header': self.header.to_dict(),
            'payload': self.payload,
            'metadata': self.metadata
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntegrationMessage':
        header = MessageHeader(
            message_id=data['header']['message_id'],
            timestamp=datetime.fromisoformat(data['header']['timestamp']),
            direction=MessageDirection[data['header']['direction']],
            priority=MessagePriority[data['header']['priority']],
            correlation_id=data['header'].get('correlation_id'),
            ttl_seconds=data['header'].get('ttl_seconds', 300)
        )
        return cls(
            header=header,
            payload=data['payload'],
            metadata=data.get('metadata', {})
        )


# =============================================================================
# REQUEST TYPES (ManusCog → Manus)
# =============================================================================

@dataclass
class GuidanceRequest:
    """Request for guidance from Manus."""
    topic: str
    context: Dict[str, Any]
    question: str
    urgency: MessagePriority = MessagePriority.MEDIUM
    constraints: List[str] = field(default_factory=list)
    preferred_response_format: str = "structured"
    
    def to_message(self) -> IntegrationMessage:
        header = MessageHeader.create(
            direction=MessageDirection.TO_MANUS,
            priority=self.urgency
        )
        return IntegrationMessage(
            header=header,
            payload={
                'type': RequestType.GUIDANCE_REQUEST.value,
                'topic': self.topic,
                'context': self.context,
                'question': self.question,
                'constraints': self.constraints,
                'preferred_response_format': self.preferred_response_format
            }
        )


@dataclass
class AnalysisRequest:
    """Request for analysis of internal state."""
    analysis_type: str
    target: str  # What to analyze
    state_snapshot: Dict[str, Any]
    depth: int = 1  # Analysis depth
    include_recommendations: bool = True
    
    def to_message(self) -> IntegrationMessage:
        header = MessageHeader.create(
            direction=MessageDirection.TO_MANUS,
            priority=MessagePriority.MEDIUM
        )
        return IntegrationMessage(
            header=header,
            payload={
                'type': RequestType.ANALYSIS_REQUEST.value,
                'analysis_type': self.analysis_type,
                'target': self.target,
                'state_snapshot': self.state_snapshot,
                'depth': self.depth,
                'include_recommendations': self.include_recommendations
            }
        )


@dataclass
class EvolutionProposal:
    """Proposal for kernel evolution requiring approval."""
    proposal_id: str
    evolution_type: str
    description: str
    changes: List[Dict[str, Any]]
    expected_benefits: List[str]
    risks: List[str]
    reversible: bool
    confidence: float
    
    def to_message(self) -> IntegrationMessage:
        header = MessageHeader.create(
            direction=MessageDirection.TO_MANUS,
            priority=MessagePriority.HIGH
        )
        return IntegrationMessage(
            header=header,
            payload={
                'type': RequestType.EVOLUTION_PROPOSAL.value,
                'proposal_id': self.proposal_id,
                'evolution_type': self.evolution_type,
                'description': self.description,
                'changes': self.changes,
                'expected_benefits': self.expected_benefits,
                'risks': self.risks,
                'reversible': self.reversible,
                'confidence': self.confidence
            }
        )


@dataclass
class KnowledgeQuery:
    """Query for external knowledge."""
    query: str
    domain: Optional[str] = None
    max_results: int = 10
    include_sources: bool = True
    format: str = "atoms"  # atoms, text, structured
    
    def to_message(self) -> IntegrationMessage:
        header = MessageHeader.create(
            direction=MessageDirection.TO_MANUS,
            priority=MessagePriority.MEDIUM
        )
        return IntegrationMessage(
            header=header,
            payload={
                'type': RequestType.KNOWLEDGE_QUERY.value,
                'query': self.query,
                'domain': self.domain,
                'max_results': self.max_results,
                'include_sources': self.include_sources,
                'format': self.format
            }
        )


@dataclass
class StatusReport:
    """Regular status report to Manus."""
    kernel_state: str
    uptime_seconds: float
    component_status: Dict[str, str]
    metrics: Dict[str, float]
    recent_events: List[Dict[str, Any]]
    autognosis_summary: Optional[Dict[str, Any]] = None
    
    def to_message(self) -> IntegrationMessage:
        header = MessageHeader.create(
            direction=MessageDirection.TO_MANUS,
            priority=MessagePriority.LOW
        )
        return IntegrationMessage(
            header=header,
            payload={
                'type': RequestType.STATUS_REPORT.value,
                'kernel_state': self.kernel_state,
                'uptime_seconds': self.uptime_seconds,
                'component_status': self.component_status,
                'metrics': self.metrics,
                'recent_events': self.recent_events,
                'autognosis_summary': self.autognosis_summary
            }
        )


# =============================================================================
# RESPONSE TYPES (Manus → ManusCog)
# =============================================================================

@dataclass
class GuidanceResponse:
    """Response to a guidance request."""
    guidance: str
    confidence: float
    reasoning: str
    recommendations: List[str]
    alternatives: List[str] = field(default_factory=list)
    caveats: List[str] = field(default_factory=list)
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'GuidanceResponse':
        return cls(
            guidance=payload['guidance'],
            confidence=payload['confidence'],
            reasoning=payload['reasoning'],
            recommendations=payload['recommendations'],
            alternatives=payload.get('alternatives', []),
            caveats=payload.get('caveats', [])
        )


@dataclass
class AnalysisResult:
    """Result of an analysis request."""
    analysis_type: str
    findings: List[Dict[str, Any]]
    summary: str
    recommendations: List[str]
    confidence: float
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'AnalysisResult':
        return cls(
            analysis_type=payload['analysis_type'],
            findings=payload['findings'],
            summary=payload['summary'],
            recommendations=payload['recommendations'],
            confidence=payload['confidence']
        )


@dataclass
class EvolutionApproval:
    """Response to an evolution proposal."""
    proposal_id: str
    status: ApprovalStatus
    feedback: str
    conditions: List[str] = field(default_factory=list)
    suggested_modifications: List[Dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'EvolutionApproval':
        return cls(
            proposal_id=payload['proposal_id'],
            status=ApprovalStatus[payload['status']],
            feedback=payload['feedback'],
            conditions=payload.get('conditions', []),
            suggested_modifications=payload.get('suggested_modifications', [])
        )


@dataclass
class KnowledgeInjection:
    """Knowledge injected from Manus."""
    knowledge_type: str
    content: List[Dict[str, Any]]
    source: str
    confidence: float
    integration_hints: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'KnowledgeInjection':
        return cls(
            knowledge_type=payload['knowledge_type'],
            content=payload['content'],
            source=payload['source'],
            confidence=payload['confidence'],
            integration_hints=payload.get('integration_hints', {})
        )


@dataclass
class TaskAssignment:
    """Task assigned by Manus to ManusCog."""
    task_id: str
    task_type: str
    description: str
    parameters: Dict[str, Any]
    deadline: Optional[datetime] = None
    priority: MessagePriority = MessagePriority.MEDIUM
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'TaskAssignment':
        deadline = None
        if payload.get('deadline'):
            deadline = datetime.fromisoformat(payload['deadline'])
        return cls(
            task_id=payload['task_id'],
            task_type=payload['task_type'],
            description=payload['description'],
            parameters=payload['parameters'],
            deadline=deadline,
            priority=MessagePriority[payload.get('priority', 'MEDIUM')]
        )


@dataclass
class Command:
    """Direct command from Manus."""
    command_type: str
    action: str
    parameters: Dict[str, Any]
    require_confirmation: bool = False
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'Command':
        return cls(
            command_type=payload['command_type'],
            action=payload['action'],
            parameters=payload['parameters'],
            require_confirmation=payload.get('require_confirmation', False)
        )


# =============================================================================
# CONNECTION AND STATE TYPES
# =============================================================================

@dataclass
class ConnectionInfo:
    """Information about the connection to Manus."""
    protocol: ProtocolType
    state: ConnectionState
    connected_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    latency_ms: float = 0.0
    messages_sent: int = 0
    messages_received: int = 0
    errors: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'protocol': self.protocol.name,
            'state': self.state.name,
            'connected_at': self.connected_at.isoformat() if self.connected_at else None,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'latency_ms': self.latency_ms,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'errors': self.errors
        }


@dataclass
class SyncState:
    """State synchronization information."""
    last_sync: Optional[datetime] = None
    sync_version: int = 0
    pending_updates: int = 0
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'sync_version': self.sync_version,
            'pending_updates': self.pending_updates,
            'conflicts': self.conflicts
        }


# =============================================================================
# CALLBACK TYPES
# =============================================================================

@dataclass
class PendingRequest:
    """A pending request awaiting response."""
    request_id: str
    request_type: RequestType
    sent_at: datetime
    timeout_at: datetime
    callback: Optional[Callable] = None
    retries: int = 0
    max_retries: int = 3
    
    def is_expired(self) -> bool:
        return datetime.now() > self.timeout_at


@dataclass
class CallbackResult:
    """Result of a callback execution."""
    request_id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
