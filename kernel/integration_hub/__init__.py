"""
Manus Integration Hub
=====================

The central nervous system connecting ManusCog with Primary Manus.
Enables bidirectional communication, state synchronization, and
collaborative intelligence between the AGI operating system and
its creator/collaborator.

Components:
- ManusIntegrationHub: Main orchestrator for all integration
- Protocol Adapters: MCP, REST, WebSocket, File-based communication
- Message Types: Requests, responses, and commands

Usage:
    from kernel.integration_hub import ManusIntegrationHub, HubConfig
    
    # Initialize hub
    config = HubConfig(
        primary_protocol=ProtocolType.MCP,
        enable_fallback=True,
        heartbeat_interval=30.0
    )
    hub = ManusIntegrationHub(config)
    
    # Initialize with kernel
    await hub.initialize(kernel)
    
    # Connect to Primary Manus
    await hub.connect()
    
    # Start background tasks
    await hub.start()
    
    # Request guidance
    guidance = await hub.request_guidance(
        topic="self_optimization",
        question="How can I improve my pattern recognition?",
        context=autognosis.get_current_state()
    )
    
    # Propose evolution
    approval = await hub.propose_evolution(
        evolution_type="parameter_tuning",
        description="Increase attention spread",
        changes=[{"param": "attention_spread", "from": 0.5, "to": 0.7}],
        expected_benefits=["Better pattern coverage"],
        risks=["Potential attention dilution"]
    )
"""

from .types import (
    # Enumerations
    ProtocolType,
    MessagePriority,
    MessageDirection,
    ConnectionState,
    RequestType,
    ResponseType,
    ApprovalStatus,
    
    # Message types
    MessageHeader,
    IntegrationMessage,
    
    # Request types
    GuidanceRequest,
    AnalysisRequest,
    EvolutionProposal,
    KnowledgeQuery,
    StatusReport,
    
    # Response types
    GuidanceResponse,
    AnalysisResult,
    EvolutionApproval,
    KnowledgeInjection,
    TaskAssignment,
    Command,
    
    # State types
    ConnectionInfo,
    SyncState,
    PendingRequest,
    CallbackResult
)

from .protocol_adapter import (
    ProtocolConfig,
    BaseProtocolAdapter,
    MCPProtocolAdapter,
    RESTProtocolAdapter,
    WebSocketProtocolAdapter,
    FileProtocolAdapter,
    ProtocolAdapterFactory
)

from .hub import ManusIntegrationHub, HubConfig

__all__ = [
    # Main hub
    'ManusIntegrationHub',
    'HubConfig',
    
    # Protocol adapters
    'ProtocolConfig',
    'BaseProtocolAdapter',
    'MCPProtocolAdapter',
    'RESTProtocolAdapter',
    'WebSocketProtocolAdapter',
    'FileProtocolAdapter',
    'ProtocolAdapterFactory',
    
    # Enumerations
    'ProtocolType',
    'MessagePriority',
    'MessageDirection',
    'ConnectionState',
    'RequestType',
    'ResponseType',
    'ApprovalStatus',
    
    # Message types
    'MessageHeader',
    'IntegrationMessage',
    
    # Request types
    'GuidanceRequest',
    'AnalysisRequest',
    'EvolutionProposal',
    'KnowledgeQuery',
    'StatusReport',
    
    # Response types
    'GuidanceResponse',
    'AnalysisResult',
    'EvolutionApproval',
    'KnowledgeInjection',
    'TaskAssignment',
    'Command',
    
    # State types
    'ConnectionInfo',
    'SyncState',
    'PendingRequest',
    'CallbackResult'
]

__version__ = '0.1.0'
