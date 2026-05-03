"""
Protocol Adapter Module
=======================

Handles communication protocols between ManusCog and Primary Manus.
Supports MCP, REST, WebSocket, and file-based communication.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
import asyncio
import json
import logging
import aiohttp
import os

from .types import (
    ProtocolType, ConnectionState, ConnectionInfo,
    IntegrationMessage, MessageHeader, MessageDirection
)


logger = logging.getLogger("IntegrationHub.ProtocolAdapter")


@dataclass
class ProtocolConfig:
    """Configuration for protocol adapters."""
    # MCP settings
    mcp_server_name: str = "manuscog"
    mcp_capabilities: List[str] = None
    
    # REST settings
    rest_base_url: str = "http://localhost:8080/api/v1"
    rest_timeout: int = 30
    
    # WebSocket settings
    websocket_url: str = "ws://localhost:8080/ws"
    websocket_reconnect_interval: int = 5
    
    # File-based settings
    file_inbox_path: str = "/tmp/manuscog/inbox"
    file_outbox_path: str = "/tmp/manuscog/outbox"
    file_poll_interval: float = 1.0
    
    def __post_init__(self):
        if self.mcp_capabilities is None:
            self.mcp_capabilities = ["guidance", "analysis", "evolution", "knowledge"]


class BaseProtocolAdapter(ABC):
    """Base class for protocol adapters."""
    
    def __init__(self, config: ProtocolConfig):
        self.config = config
        self.connection_info = ConnectionInfo(
            protocol=self.protocol_type,
            state=ConnectionState.DISCONNECTED
        )
        self._message_handlers: List[Callable[[IntegrationMessage], Awaitable[None]]] = []
    
    @property
    @abstractmethod
    def protocol_type(self) -> ProtocolType:
        """Return the protocol type."""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection."""
        pass
    
    @abstractmethod
    async def send(self, message: IntegrationMessage) -> bool:
        """Send a message."""
        pass
    
    @abstractmethod
    async def receive(self) -> Optional[IntegrationMessage]:
        """Receive a message (non-blocking)."""
        pass
    
    def add_message_handler(self, handler: Callable[[IntegrationMessage], Awaitable[None]]):
        """Add a handler for incoming messages."""
        self._message_handlers.append(handler)
    
    async def _dispatch_message(self, message: IntegrationMessage):
        """Dispatch message to all handlers."""
        for handler in self._message_handlers:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Handler error: {e}")


class MCPProtocolAdapter(BaseProtocolAdapter):
    """
    Model Context Protocol adapter.
    
    Uses the manus-mcp-cli utility for communication.
    This is the primary integration method.
    """
    
    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.MCP
    
    def __init__(self, config: ProtocolConfig):
        super().__init__(config)
        self._tools_cache: Dict[str, Any] = {}
        self._last_tool_list: Optional[datetime] = None
    
    async def connect(self) -> bool:
        """Establish MCP connection by verifying tool availability."""
        self.connection_info.state = ConnectionState.CONNECTING
        
        try:
            # List available tools to verify connection
            tools = await self._list_tools()
            if tools:
                self.connection_info.state = ConnectionState.CONNECTED
                self.connection_info.connected_at = datetime.now()
                logger.info(f"MCP connected with {len(tools)} tools available")
                return True
            else:
                self.connection_info.state = ConnectionState.ERROR
                return False
        except Exception as e:
            logger.error(f"MCP connection failed: {e}")
            self.connection_info.state = ConnectionState.ERROR
            return False
    
    async def disconnect(self) -> None:
        """Disconnect MCP (no persistent connection to close)."""
        self.connection_info.state = ConnectionState.DISCONNECTED
        logger.info("MCP disconnected")
    
    async def send(self, message: IntegrationMessage) -> bool:
        """Send message via MCP tool call."""
        try:
            # Convert message to MCP tool call
            tool_name = self._get_tool_for_message(message)
            tool_input = message.to_dict()
            
            # Execute via manus-mcp-cli
            result = await self._call_tool(tool_name, tool_input)
            
            self.connection_info.messages_sent += 1
            self.connection_info.last_heartbeat = datetime.now()
            
            return result is not None
        except Exception as e:
            logger.error(f"MCP send failed: {e}")
            self.connection_info.errors += 1
            return False
    
    async def receive(self) -> Optional[IntegrationMessage]:
        """Receive message from MCP (poll-based)."""
        try:
            # Poll for incoming messages
            result = await self._call_tool("manuscog_receive", {})
            
            if result and 'message' in result:
                self.connection_info.messages_received += 1
                return IntegrationMessage.from_dict(result['message'])
            
            return None
        except Exception as e:
            logger.error(f"MCP receive failed: {e}")
            return None
    
    async def _list_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools."""
        import subprocess
        
        try:
            result = subprocess.run(
                ["manus-mcp-cli", "tool", "list", "--server", self.config.mcp_server_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse tool list from output
                tools = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        tools.append({'name': line.strip()})
                self._tools_cache = {t['name']: t for t in tools}
                self._last_tool_list = datetime.now()
                return tools
            else:
                logger.warning(f"MCP tool list failed: {result.stderr}")
                return []
        except subprocess.TimeoutExpired:
            logger.error("MCP tool list timed out")
            return []
        except FileNotFoundError:
            logger.warning("manus-mcp-cli not found, MCP unavailable")
            return []
    
    async def _call_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call an MCP tool."""
        import subprocess
        
        try:
            input_json = json.dumps(tool_input)
            result = subprocess.run(
                [
                    "manus-mcp-cli", "tool", "call", tool_name,
                    "--server", self.config.mcp_server_name,
                    "--input", input_json
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout) if result.stdout.strip() else {}
            else:
                logger.warning(f"MCP tool call failed: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            logger.error(f"MCP tool call timed out: {tool_name}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from MCP tool: {tool_name}")
            return None
    
    def _get_tool_for_message(self, message: IntegrationMessage) -> str:
        """Map message type to MCP tool name."""
        message_type = message.payload.get('type', 'unknown')
        tool_mapping = {
            'guidance_request': 'manuscog_guidance',
            'analysis_request': 'manuscog_analysis',
            'evolution_proposal': 'manuscog_evolution',
            'knowledge_query': 'manuscog_knowledge',
            'status_report': 'manuscog_status',
            'error_report': 'manuscog_error'
        }
        return tool_mapping.get(message_type, 'manuscog_generic')


class RESTProtocolAdapter(BaseProtocolAdapter):
    """
    REST API protocol adapter.
    
    Fallback HTTP-based communication.
    """
    
    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.REST
    
    def __init__(self, config: ProtocolConfig):
        super().__init__(config)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def connect(self) -> bool:
        """Establish REST connection."""
        self.connection_info.state = ConnectionState.CONNECTING
        
        try:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.rest_timeout)
            )
            
            # Test connection with health check
            async with self._session.get(f"{self.config.rest_base_url}/health") as resp:
                if resp.status == 200:
                    self.connection_info.state = ConnectionState.CONNECTED
                    self.connection_info.connected_at = datetime.now()
                    logger.info("REST API connected")
                    return True
                else:
                    self.connection_info.state = ConnectionState.ERROR
                    return False
        except Exception as e:
            logger.error(f"REST connection failed: {e}")
            self.connection_info.state = ConnectionState.ERROR
            return False
    
    async def disconnect(self) -> None:
        """Close REST session."""
        if self._session:
            await self._session.close()
            self._session = None
        self.connection_info.state = ConnectionState.DISCONNECTED
        logger.info("REST API disconnected")
    
    async def send(self, message: IntegrationMessage) -> bool:
        """Send message via REST POST."""
        if not self._session:
            return False
        
        try:
            async with self._session.post(
                f"{self.config.rest_base_url}/messages",
                json=message.to_dict()
            ) as resp:
                self.connection_info.messages_sent += 1
                self.connection_info.last_heartbeat = datetime.now()
                return resp.status in (200, 201, 202)
        except Exception as e:
            logger.error(f"REST send failed: {e}")
            self.connection_info.errors += 1
            return False
    
    async def receive(self) -> Optional[IntegrationMessage]:
        """Receive message via REST GET."""
        if not self._session:
            return None
        
        try:
            async with self._session.get(
                f"{self.config.rest_base_url}/messages/pending"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        self.connection_info.messages_received += 1
                        return IntegrationMessage.from_dict(data)
                return None
        except Exception as e:
            logger.error(f"REST receive failed: {e}")
            return None


class WebSocketProtocolAdapter(BaseProtocolAdapter):
    """
    WebSocket protocol adapter.
    
    Real-time bidirectional streaming.
    """
    
    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.WEBSOCKET
    
    def __init__(self, config: ProtocolConfig):
        super().__init__(config)
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
    
    async def connect(self) -> bool:
        """Establish WebSocket connection."""
        self.connection_info.state = ConnectionState.CONNECTING
        
        try:
            self._session = aiohttp.ClientSession()
            self._ws = await self._session.ws_connect(self.config.websocket_url)
            
            self.connection_info.state = ConnectionState.CONNECTED
            self.connection_info.connected_at = datetime.now()
            
            # Start receive loop
            self._receive_task = asyncio.create_task(self._receive_loop())
            
            logger.info("WebSocket connected")
            return True
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.connection_info.state = ConnectionState.ERROR
            return False
    
    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        if self._session:
            await self._session.close()
            self._session = None
        
        self.connection_info.state = ConnectionState.DISCONNECTED
        logger.info("WebSocket disconnected")
    
    async def send(self, message: IntegrationMessage) -> bool:
        """Send message via WebSocket."""
        if not self._ws:
            return False
        
        try:
            await self._ws.send_json(message.to_dict())
            self.connection_info.messages_sent += 1
            self.connection_info.last_heartbeat = datetime.now()
            return True
        except Exception as e:
            logger.error(f"WebSocket send failed: {e}")
            self.connection_info.errors += 1
            return False
    
    async def receive(self) -> Optional[IntegrationMessage]:
        """Receive message from queue."""
        try:
            return self._message_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None
    
    async def _receive_loop(self):
        """Background loop to receive WebSocket messages."""
        while self._ws:
            try:
                msg = await self._ws.receive()
                
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    message = IntegrationMessage.from_dict(data)
                    await self._message_queue.put(message)
                    self.connection_info.messages_received += 1
                    await self._dispatch_message(message)
                
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    break
                
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {self._ws.exception()}")
                    break
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"WebSocket receive error: {e}")


class FileProtocolAdapter(BaseProtocolAdapter):
    """
    File-based protocol adapter.
    
    Uses shared filesystem for communication.
    Useful for debugging and offline operation.
    """
    
    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.FILE
    
    def __init__(self, config: ProtocolConfig):
        super().__init__(config)
        self._poll_task: Optional[asyncio.Task] = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
    
    async def connect(self) -> bool:
        """Set up file-based communication directories."""
        self.connection_info.state = ConnectionState.CONNECTING
        
        try:
            # Create directories if they don't exist
            os.makedirs(self.config.file_inbox_path, exist_ok=True)
            os.makedirs(self.config.file_outbox_path, exist_ok=True)
            
            self.connection_info.state = ConnectionState.CONNECTED
            self.connection_info.connected_at = datetime.now()
            
            # Start polling loop
            self._poll_task = asyncio.create_task(self._poll_loop())
            
            logger.info("File-based communication ready")
            return True
        except Exception as e:
            logger.error(f"File setup failed: {e}")
            self.connection_info.state = ConnectionState.ERROR
            return False
    
    async def disconnect(self) -> None:
        """Stop file polling."""
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        
        self.connection_info.state = ConnectionState.DISCONNECTED
        logger.info("File-based communication stopped")
    
    async def send(self, message: IntegrationMessage) -> bool:
        """Write message to outbox file."""
        try:
            filename = f"{message.header.message_id}.json"
            filepath = os.path.join(self.config.file_outbox_path, filename)
            
            with open(filepath, 'w') as f:
                json.dump(message.to_dict(), f, indent=2, default=str)
            
            self.connection_info.messages_sent += 1
            self.connection_info.last_heartbeat = datetime.now()
            return True
        except Exception as e:
            logger.error(f"File send failed: {e}")
            self.connection_info.errors += 1
            return False
    
    async def receive(self) -> Optional[IntegrationMessage]:
        """Get message from queue."""
        try:
            return self._message_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None
    
    async def _poll_loop(self):
        """Poll inbox directory for new messages."""
        while True:
            try:
                await asyncio.sleep(self.config.file_poll_interval)
                
                # Check for new files in inbox
                for filename in os.listdir(self.config.file_inbox_path):
                    if filename.endswith('.json'):
                        filepath = os.path.join(self.config.file_inbox_path, filename)
                        
                        try:
                            with open(filepath, 'r') as f:
                                data = json.load(f)
                            
                            message = IntegrationMessage.from_dict(data)
                            await self._message_queue.put(message)
                            self.connection_info.messages_received += 1
                            await self._dispatch_message(message)
                            
                            # Remove processed file
                            os.remove(filepath)
                        except Exception as e:
                            logger.error(f"Error processing file {filename}: {e}")
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"File poll error: {e}")


class ProtocolAdapterFactory:
    """Factory for creating protocol adapters."""
    
    @staticmethod
    def create(protocol: ProtocolType, config: ProtocolConfig) -> BaseProtocolAdapter:
        """Create a protocol adapter of the specified type."""
        adapters = {
            ProtocolType.MCP: MCPProtocolAdapter,
            ProtocolType.REST: RESTProtocolAdapter,
            ProtocolType.WEBSOCKET: WebSocketProtocolAdapter,
            ProtocolType.FILE: FileProtocolAdapter
        }
        
        adapter_class = adapters.get(protocol)
        if not adapter_class:
            raise ValueError(f"Unknown protocol type: {protocol}")
        
        return adapter_class(config)
