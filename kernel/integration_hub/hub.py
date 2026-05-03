"""
Integration Hub Core Module
===========================

The central nervous system connecting ManusCog with Primary Manus.
Coordinates all communication, state synchronization, and callbacks.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Callable, Awaitable, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import logging
import hashlib
import time

from .types import (
    ProtocolType, ConnectionState, ConnectionInfo, SyncState,
    IntegrationMessage, MessageHeader, MessageDirection, MessagePriority,
    RequestType, ResponseType, ApprovalStatus,
    GuidanceRequest, GuidanceResponse,
    AnalysisRequest, AnalysisResult,
    EvolutionProposal, EvolutionApproval,
    KnowledgeQuery, KnowledgeInjection,
    StatusReport, TaskAssignment, Command,
    PendingRequest, CallbackResult
)
from .protocol_adapter import (
    ProtocolConfig, BaseProtocolAdapter, ProtocolAdapterFactory
)

if TYPE_CHECKING:
    from kernel.cognitive_kernel import CognitiveKernel
    from kernel.autognosis import AutognosisOrchestrator


logger = logging.getLogger("IntegrationHub")


@dataclass
class HubConfig:
    """Configuration for the Integration Hub."""
    # Protocol settings
    primary_protocol: ProtocolType = ProtocolType.MCP
    fallback_protocol: ProtocolType = ProtocolType.FILE
    enable_fallback: bool = True
    
    # Timing settings
    heartbeat_interval: float = 30.0
    state_sync_interval: float = 60.0
    knowledge_sync_interval: float = 300.0
    request_timeout: float = 60.0
    
    # Retry settings
    max_retries: int = 3
    retry_backoff: float = 2.0
    
    # Queue settings
    max_pending_requests: int = 100
    max_message_queue_size: int = 1000
    
    # Feature flags
    enable_auto_sync: bool = True
    enable_knowledge_sharing: bool = True
    require_evolution_approval: bool = True


class ManusIntegrationHub:
    """
    Central hub for ManusCog-Manus integration.
    
    Provides:
    - Multi-protocol communication
    - Request-response correlation
    - State synchronization
    - Callback management
    - Automatic failover
    """
    
    def __init__(self, config: HubConfig = None):
        self.config = config or HubConfig()
        
        # Protocol adapters
        self._protocol_config = ProtocolConfig()
        self._primary_adapter: Optional[BaseProtocolAdapter] = None
        self._fallback_adapter: Optional[BaseProtocolAdapter] = None
        self._active_adapter: Optional[BaseProtocolAdapter] = None
        
        # State
        self._connection_info = ConnectionInfo(
            protocol=self.config.primary_protocol,
            state=ConnectionState.DISCONNECTED
        )
        self._sync_state = SyncState()
        
        # Request tracking
        self._pending_requests: Dict[str, PendingRequest] = {}
        self._response_handlers: Dict[str, Callable] = {}
        
        # Message queues
        self._outbound_queue: asyncio.Queue = asyncio.Queue(
            maxsize=self.config.max_message_queue_size
        )
        self._inbound_queue: asyncio.Queue = asyncio.Queue(
            maxsize=self.config.max_message_queue_size
        )
        
        # Background tasks
        self._is_running = False
        self._tasks: List[asyncio.Task] = []
        
        # Kernel reference
        self._kernel: Optional['CognitiveKernel'] = None
        
        # Statistics
        self._stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'requests_made': 0,
            'responses_received': 0,
            'errors': 0,
            'failovers': 0
        }
    
    async def initialize(self, kernel: 'CognitiveKernel'):
        """Initialize the integration hub."""
        logger.info("Initializing Manus Integration Hub...")
        
        self._kernel = kernel
        
        # Create protocol adapters
        self._primary_adapter = ProtocolAdapterFactory.create(
            self.config.primary_protocol,
            self._protocol_config
        )
        
        if self.config.enable_fallback:
            self._fallback_adapter = ProtocolAdapterFactory.create(
                self.config.fallback_protocol,
                self._protocol_config
            )
        
        # Register message handlers
        self._primary_adapter.add_message_handler(self._handle_incoming_message)
        if self._fallback_adapter:
            self._fallback_adapter.add_message_handler(self._handle_incoming_message)
        
        logger.info("Integration Hub initialized")
    
    async def connect(self) -> bool:
        """Establish connection to Primary Manus."""
        logger.info("Connecting to Primary Manus...")
        
        # Try primary protocol
        if await self._primary_adapter.connect():
            self._active_adapter = self._primary_adapter
            self._connection_info = self._primary_adapter.connection_info
            logger.info(f"Connected via {self.config.primary_protocol.name}")
            return True
        
        # Try fallback if enabled
        if self.config.enable_fallback and self._fallback_adapter:
            logger.warning("Primary protocol failed, trying fallback...")
            if await self._fallback_adapter.connect():
                self._active_adapter = self._fallback_adapter
                self._connection_info = self._fallback_adapter.connection_info
                self._stats['failovers'] += 1
                logger.info(f"Connected via fallback {self.config.fallback_protocol.name}")
                return True
        
        logger.error("Failed to connect to Primary Manus")
        return False
    
    async def start(self):
        """Start the integration hub background tasks."""
        if self._is_running:
            logger.warning("Integration Hub already running")
            return
        
        self._is_running = True
        
        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._outbound_loop()),
            asyncio.create_task(self._inbound_loop()),
            asyncio.create_task(self._timeout_loop())
        ]
        
        if self.config.enable_auto_sync:
            self._tasks.append(asyncio.create_task(self._sync_loop()))
        
        logger.info("Integration Hub started")
    
    async def stop(self):
        """Stop the integration hub."""
        self._is_running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Disconnect adapters
        if self._primary_adapter:
            await self._primary_adapter.disconnect()
        if self._fallback_adapter:
            await self._fallback_adapter.disconnect()
        
        logger.info("Integration Hub stopped")
    
    # =========================================================================
    # PUBLIC API - Request Methods
    # =========================================================================
    
    async def request_guidance(
        self,
        topic: str,
        question: str,
        context: Dict[str, Any] = None,
        urgency: MessagePriority = MessagePriority.MEDIUM
    ) -> Optional[GuidanceResponse]:
        """
        Request guidance from Primary Manus.
        
        Args:
            topic: The topic area for guidance
            question: The specific question
            context: Additional context
            urgency: Priority level
            
        Returns:
            GuidanceResponse if successful, None otherwise
        """
        request = GuidanceRequest(
            topic=topic,
            question=question,
            context=context or {},
            urgency=urgency
        )
        
        response = await self._send_request(
            request.to_message(),
            RequestType.GUIDANCE_REQUEST
        )
        
        if response:
            return GuidanceResponse.from_payload(response.payload)
        return None
    
    async def request_analysis(
        self,
        analysis_type: str,
        target: str,
        state_snapshot: Dict[str, Any],
        depth: int = 1
    ) -> Optional[AnalysisResult]:
        """
        Request analysis of internal state from Primary Manus.
        
        Args:
            analysis_type: Type of analysis to perform
            target: What to analyze
            state_snapshot: Current state data
            depth: Analysis depth
            
        Returns:
            AnalysisResult if successful, None otherwise
        """
        request = AnalysisRequest(
            analysis_type=analysis_type,
            target=target,
            state_snapshot=state_snapshot,
            depth=depth
        )
        
        response = await self._send_request(
            request.to_message(),
            RequestType.ANALYSIS_REQUEST
        )
        
        if response:
            return AnalysisResult.from_payload(response.payload)
        return None
    
    async def propose_evolution(
        self,
        evolution_type: str,
        description: str,
        changes: List[Dict[str, Any]],
        expected_benefits: List[str],
        risks: List[str],
        reversible: bool = True,
        confidence: float = 0.5
    ) -> Optional[EvolutionApproval]:
        """
        Propose a kernel evolution for approval.
        
        Args:
            evolution_type: Type of evolution
            description: Description of the change
            changes: List of specific changes
            expected_benefits: Expected benefits
            risks: Potential risks
            reversible: Whether the change is reversible
            confidence: Confidence in the proposal
            
        Returns:
            EvolutionApproval if response received, None otherwise
        """
        proposal_id = self._generate_id("proposal")
        
        proposal = EvolutionProposal(
            proposal_id=proposal_id,
            evolution_type=evolution_type,
            description=description,
            changes=changes,
            expected_benefits=expected_benefits,
            risks=risks,
            reversible=reversible,
            confidence=confidence
        )
        
        response = await self._send_request(
            proposal.to_message(),
            RequestType.EVOLUTION_PROPOSAL
        )
        
        if response:
            return EvolutionApproval.from_payload(response.payload)
        return None
    
    async def query_knowledge(
        self,
        query: str,
        domain: Optional[str] = None,
        max_results: int = 10
    ) -> Optional[KnowledgeInjection]:
        """
        Query Primary Manus for knowledge.
        
        Args:
            query: The knowledge query
            domain: Optional domain filter
            max_results: Maximum results to return
            
        Returns:
            KnowledgeInjection if successful, None otherwise
        """
        request = KnowledgeQuery(
            query=query,
            domain=domain,
            max_results=max_results
        )
        
        response = await self._send_request(
            request.to_message(),
            RequestType.KNOWLEDGE_QUERY
        )
        
        if response:
            return KnowledgeInjection.from_payload(response.payload)
        return None
    
    async def send_status_report(self) -> bool:
        """
        Send status report to Primary Manus.
        
        Returns:
            True if sent successfully
        """
        if not self._kernel:
            return False
        
        # Gather status information
        report = StatusReport(
            kernel_state=self._kernel.state.name if hasattr(self._kernel, 'state') else 'unknown',
            uptime_seconds=self._kernel.stats.get('uptime', 0),
            component_status=self._get_component_status(),
            metrics=self._get_metrics(),
            recent_events=self._get_recent_events(),
            autognosis_summary=self._get_autognosis_summary()
        )
        
        message = report.to_message()
        return await self._send_message(message)
    
    # =========================================================================
    # INTERNAL - Message Handling
    # =========================================================================
    
    async def _send_request(
        self,
        message: IntegrationMessage,
        request_type: RequestType
    ) -> Optional[IntegrationMessage]:
        """Send a request and wait for response."""
        if not self._active_adapter:
            logger.error("No active adapter for request")
            return None
        
        # Track pending request
        request_id = message.header.message_id
        pending = PendingRequest(
            request_id=request_id,
            request_type=request_type,
            sent_at=datetime.now(),
            timeout_at=datetime.now() + timedelta(seconds=self.config.request_timeout)
        )
        self._pending_requests[request_id] = pending
        
        # Create response future
        response_future: asyncio.Future = asyncio.Future()
        self._response_handlers[request_id] = lambda r: response_future.set_result(r)
        
        # Send message
        if not await self._send_message(message):
            del self._pending_requests[request_id]
            del self._response_handlers[request_id]
            return None
        
        self._stats['requests_made'] += 1
        
        # Wait for response
        try:
            response = await asyncio.wait_for(
                response_future,
                timeout=self.config.request_timeout
            )
            self._stats['responses_received'] += 1
            return response
        except asyncio.TimeoutError:
            logger.warning(f"Request {request_id} timed out")
            return None
        finally:
            self._pending_requests.pop(request_id, None)
            self._response_handlers.pop(request_id, None)
    
    async def _send_message(self, message: IntegrationMessage) -> bool:
        """Send a message through the active adapter."""
        if not self._active_adapter:
            return False
        
        success = await self._active_adapter.send(message)
        
        if success:
            self._stats['messages_sent'] += 1
        else:
            self._stats['errors'] += 1
            # Try failover
            if self.config.enable_fallback and self._fallback_adapter:
                if await self._try_failover():
                    success = await self._active_adapter.send(message)
        
        return success
    
    async def _handle_incoming_message(self, message: IntegrationMessage):
        """Handle an incoming message from Primary Manus."""
        self._stats['messages_received'] += 1
        
        # Check if this is a response to a pending request
        correlation_id = message.header.correlation_id
        if correlation_id and correlation_id in self._response_handlers:
            handler = self._response_handlers[correlation_id]
            handler(message)
            return
        
        # Handle based on message type
        message_type = message.payload.get('type')
        
        if message_type == ResponseType.TASK_ASSIGNMENT.value:
            await self._handle_task_assignment(TaskAssignment.from_payload(message.payload))
        
        elif message_type == ResponseType.COMMAND.value:
            await self._handle_command(Command.from_payload(message.payload))
        
        elif message_type == ResponseType.KNOWLEDGE_INJECTION.value:
            await self._handle_knowledge_injection(KnowledgeInjection.from_payload(message.payload))
        
        elif message_type == ResponseType.CONFIGURATION_UPDATE.value:
            await self._handle_configuration_update(message.payload)
        
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def _handle_task_assignment(self, task: TaskAssignment):
        """Handle a task assignment from Manus."""
        logger.info(f"Received task assignment: {task.task_id}")
        # TODO: Implement task execution
    
    async def _handle_command(self, command: Command):
        """Handle a direct command from Manus."""
        logger.info(f"Received command: {command.command_type}/{command.action}")
        # TODO: Implement command execution
    
    async def _handle_knowledge_injection(self, knowledge: KnowledgeInjection):
        """Handle knowledge injection from Manus."""
        logger.info(f"Received knowledge injection: {knowledge.knowledge_type}")
        # TODO: Integrate knowledge into AtomSpace
    
    async def _handle_configuration_update(self, payload: Dict[str, Any]):
        """Handle configuration update from Manus."""
        logger.info("Received configuration update")
        # TODO: Apply configuration changes
    
    # =========================================================================
    # INTERNAL - Background Tasks
    # =========================================================================
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats."""
        while self._is_running:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)
                await self.send_status_report()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
    
    async def _outbound_loop(self):
        """Process outbound message queue."""
        while self._is_running:
            try:
                message = await asyncio.wait_for(
                    self._outbound_queue.get(),
                    timeout=1.0
                )
                await self._send_message(message)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Outbound loop error: {e}")
    
    async def _inbound_loop(self):
        """Poll for incoming messages."""
        while self._is_running:
            try:
                if self._active_adapter:
                    message = await self._active_adapter.receive()
                    if message:
                        await self._handle_incoming_message(message)
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Inbound loop error: {e}")
    
    async def _timeout_loop(self):
        """Check for timed out requests."""
        while self._is_running:
            try:
                await asyncio.sleep(5.0)
                
                now = datetime.now()
                expired = [
                    req_id for req_id, req in self._pending_requests.items()
                    if req.is_expired()
                ]
                
                for req_id in expired:
                    logger.warning(f"Request {req_id} expired")
                    self._pending_requests.pop(req_id, None)
                    handler = self._response_handlers.pop(req_id, None)
                    if handler:
                        # Signal timeout
                        pass
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Timeout loop error: {e}")
    
    async def _sync_loop(self):
        """Periodic state synchronization."""
        while self._is_running:
            try:
                await asyncio.sleep(self.config.state_sync_interval)
                await self._sync_state_with_manus()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
    
    async def _sync_state_with_manus(self):
        """Synchronize state with Primary Manus."""
        # TODO: Implement state synchronization
        self._sync_state.last_sync = datetime.now()
        self._sync_state.sync_version += 1
    
    async def _try_failover(self) -> bool:
        """Attempt to failover to backup adapter."""
        if not self._fallback_adapter:
            return False
        
        logger.warning("Attempting failover to backup protocol...")
        
        if await self._fallback_adapter.connect():
            self._active_adapter = self._fallback_adapter
            self._connection_info = self._fallback_adapter.connection_info
            self._stats['failovers'] += 1
            logger.info("Failover successful")
            return True
        
        logger.error("Failover failed")
        return False
    
    # =========================================================================
    # INTERNAL - Helpers
    # =========================================================================
    
    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID."""
        content = f"{prefix}:{time.time()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _get_component_status(self) -> Dict[str, str]:
        """Get status of all kernel components."""
        if not self._kernel:
            return {}
        
        status = {}
        components = ['atomspace', 'pln', 'ecan', 'pattern', 'moses', 'memory_manager', 'scheduler']
        
        for comp in components:
            if hasattr(self._kernel, comp) and getattr(self._kernel, comp):
                status[comp] = 'active'
            else:
                status[comp] = 'inactive'
        
        return status
    
    def _get_metrics(self) -> Dict[str, float]:
        """Get current kernel metrics."""
        if not self._kernel:
            return {}
        
        return self._kernel.stats.copy() if hasattr(self._kernel, 'stats') else {}
    
    def _get_recent_events(self) -> List[Dict[str, Any]]:
        """Get recent kernel events."""
        # TODO: Implement event logging
        return []
    
    def _get_autognosis_summary(self) -> Optional[Dict[str, Any]]:
        """Get autognosis summary if available."""
        if not self._kernel or not hasattr(self._kernel, 'autognosis'):
            return None
        
        if self._kernel.autognosis:
            return self._kernel.autognosis.get_status()
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get hub status."""
        return {
            'is_running': self._is_running,
            'connection': self._connection_info.to_dict(),
            'sync_state': self._sync_state.to_dict(),
            'pending_requests': len(self._pending_requests),
            'stats': self._stats.copy()
        }
