"""
MCP Server Registry - Phase 3 Chunk 1

Centralized registry for managing all MCP servers in the arbitrage system.
Provides discovery, capability tracking, and health monitoring for MCP servers.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ServerStatus(Enum):
    """MCP Server status enumeration."""
    UNKNOWN = "unknown"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class ServerType(Enum):
    """MCP Server type enumeration."""
    MEMORY = "memory"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    MARKET_DATA = "market_data"
    EXCHANGE = "exchange"
    ANALYTICS = "analytics"
    ORGANIZATION = "organization"
    CUSTOM = "custom"


@dataclass
class ServerCapability:
    """Represents a capability provided by an MCP server."""
    name: str
    description: str
    tools: List[str] = field(default_factory=list)
    data_types: List[str] = field(default_factory=list)
    real_time: bool = False
    priority: int = 1  # 1=highest, 10=lowest


@dataclass
class ServerMetadata:
    """Metadata for an MCP server."""
    server_id: str
    name: str
    server_type: ServerType
    description: str
    version: str = "unknown"
    capabilities: List[ServerCapability] = field(default_factory=list)
    endpoints: Dict[str, str] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    required: bool = True
    priority: int = 1
    tags: Set[str] = field(default_factory=set)
    
    # Health tracking
    status: ServerStatus = ServerStatus.UNKNOWN
    last_seen: Optional[datetime] = None
    last_error: Optional[str] = None
    uptime_start: Optional[datetime] = None
    connection_attempts: int = 0
    max_retries: int = 3


class MCPServerRegistry:
    """
    Centralized registry for MCP servers with discovery and health monitoring.
    
    This is Chunk 1 of the Phase 3 MCP Orchestration Engine.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the MCP server registry."""
        self.config = config or {}
        self.servers: Dict[str, ServerMetadata] = {}
        self.capabilities_index: Dict[str, List[str]] = {}  # capability -> server_ids
        self.type_index: Dict[ServerType, List[str]] = {}  # type -> server_ids
        self.tag_index: Dict[str, List[str]] = {}  # tag -> server_ids
        
        # Health monitoring
        self.health_check_interval = self.config.get('health_check_interval', 30)
        self.health_monitor_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Initialize with default servers
        self._register_default_servers()

    def _register_default_servers(self) -> None:
        """Register default MCP servers for the arbitrage system."""
        default_servers = [
            {
                'server_id': 'dexmind',
                'name': 'DexMind',
                'server_type': ServerType.MEMORY,
                'description': 'Custom memory server for arbitrage patterns',
                'capabilities': [
                    ServerCapability(
                        name='arbitrage_memory',
                        description='Store and retrieve arbitrage patterns',
                        tools=['store_penny_trade', 'get_profitable_patterns', 'analyze_trade_history'],
                        data_types=['trade_data', 'profit_patterns', 'market_conditions'],
                        real_time=True,
                        priority=1
                    )
                ],
                'required': True,
                'priority': 1,
                'tags': {'arbitrage', 'memory', 'patterns'}
            },
            {
                'server_id': 'memory_service',
                'name': 'MCP Memory Service',
                'server_type': ServerType.MEMORY,
                'description': 'General memory and pattern storage',
                'capabilities': [
                    ServerCapability(
                        name='general_memory',
                        description='Store and retrieve general information',
                        tools=['store_memory', 'retrieve_memory', 'search_by_tag'],
                        data_types=['text', 'metadata', 'tags'],
                        real_time=False,
                        priority=2
                    )
                ],
                'required': True,
                'priority': 2,
                'tags': {'memory', 'storage', 'general'}
            },
            {
                'server_id': 'knowledge_graph',
                'name': 'Knowledge Graph',
                'server_type': ServerType.KNOWLEDGE_GRAPH,
                'description': 'Token and market relationship storage',
                'capabilities': [
                    ServerCapability(
                        name='relationship_storage',
                        description='Store and query entity relationships',
                        tools=['create_entities', 'create_relations', 'search_nodes'],
                        data_types=['entities', 'relations', 'graph_data'],
                        real_time=False,
                        priority=1
                    )
                ],
                'required': True,
                'priority': 1,
                'tags': {'graph', 'relationships', 'entities'}
            },
            {
                'server_id': 'ccxt',
                'name': 'CCXT Exchange Data',
                'server_type': ServerType.EXCHANGE,
                'description': 'Exchange data and trading pairs',
                'capabilities': [
                    ServerCapability(
                        name='exchange_data',
                        description='Real-time exchange data and rates',
                        tools=['get_exchange_rates', 'get_trading_pairs', 'get_order_book'],
                        data_types=['prices', 'volumes', 'order_books'],
                        real_time=True,
                        priority=1
                    )
                ],
                'required': True,
                'priority': 1,
                'tags': {'exchange', 'prices', 'real_time'}
            }
        ]
        
        for server_config in default_servers:
            self.register_server(**server_config)

    def register_server(self, server_id: str, name: str, server_type: ServerType, 
                       description: str, capabilities: List[ServerCapability] = None,
                       **kwargs) -> bool:
        """
        Register a new MCP server in the registry.
        
        Args:
            server_id: Unique identifier for the server
            name: Human-readable name
            server_type: Type of server (enum)
            description: Server description
            capabilities: List of server capabilities
            **kwargs: Additional metadata
            
        Returns:
            bool: True if registration successful
        """
        try:
            if server_id in self.servers:
                logger.warning(f"Server {server_id} already registered, updating...")
            
            # Create server metadata
            metadata = ServerMetadata(
                server_id=server_id,
                name=name,
                server_type=server_type,
                description=description,
                capabilities=capabilities or [],
                **kwargs
            )
            
            # Store in main registry
            self.servers[server_id] = metadata
            
            # Update indexes
            self._update_indexes(server_id, metadata)
            
            logger.info(f"Registered MCP server: {server_id} ({name})")
            return True
            
        except Exception as e:
            logger.error(f"Error registering server {server_id}: {e}")
            return False

    def _update_indexes(self, server_id: str, metadata: ServerMetadata) -> None:
        """Update all indexes with server information."""
        # Update capabilities index
        for capability in metadata.capabilities:
            if capability.name not in self.capabilities_index:
                self.capabilities_index[capability.name] = []
            if server_id not in self.capabilities_index[capability.name]:
                self.capabilities_index[capability.name].append(server_id)
        
        # Update type index
        if metadata.server_type not in self.type_index:
            self.type_index[metadata.server_type] = []
        if server_id not in self.type_index[metadata.server_type]:
            self.type_index[metadata.server_type].append(server_id)
        
        # Update tag index
        for tag in metadata.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            if server_id not in self.tag_index[tag]:
                self.tag_index[tag].append(server_id)

    def get_server(self, server_id: str) -> Optional[ServerMetadata]:
        """Get server metadata by ID."""
        return self.servers.get(server_id)

    def get_servers_by_type(self, server_type: ServerType) -> List[ServerMetadata]:
        """Get all servers of a specific type."""
        server_ids = self.type_index.get(server_type, [])
        return [self.servers[sid] for sid in server_ids if sid in self.servers]

    def get_servers_by_capability(self, capability_name: str) -> List[ServerMetadata]:
        """Get all servers that provide a specific capability."""
        server_ids = self.capabilities_index.get(capability_name, [])
        return [self.servers[sid] for sid in server_ids if sid in self.servers]

    def get_servers_by_tag(self, tag: str) -> List[ServerMetadata]:
        """Get all servers with a specific tag."""
        server_ids = self.tag_index.get(tag, [])
        return [self.servers[sid] for sid in server_ids if sid in self.servers]

    def get_available_servers(self) -> List[ServerMetadata]:
        """Get all servers that are currently available (connected)."""
        return [
            server for server in self.servers.values()
            if server.status == ServerStatus.CONNECTED
        ]

    def get_required_servers(self) -> List[ServerMetadata]:
        """Get all servers marked as required."""
        return [server for server in self.servers.values() if server.required]

    def update_server_status(self, server_id: str, status: ServerStatus, 
                           error: str = None) -> bool:
        """Update server status and health information."""
        if server_id not in self.servers:
            logger.warning(f"Cannot update status for unknown server: {server_id}")
            return False
        
        server = self.servers[server_id]
        old_status = server.status
        server.status = status
        server.last_seen = datetime.now()
        
        if error:
            server.last_error = error
        
        if status == ServerStatus.CONNECTED and old_status != ServerStatus.CONNECTED:
            server.uptime_start = datetime.now()
            server.connection_attempts = 0
            logger.info(f"Server {server_id} connected successfully")
        elif status == ServerStatus.ERROR:
            server.connection_attempts += 1
            logger.error(f"Server {server_id} error (attempt {server.connection_attempts}): {error}")
        
        return True

    def get_registry_summary(self) -> Dict[str, Any]:
        """Get a summary of the current registry state."""
        status_counts = {}
        for status in ServerStatus:
            status_counts[status.value] = sum(
                1 for server in self.servers.values() 
                if server.status == status
            )
        
        return {
            'total_servers': len(self.servers),
            'status_breakdown': status_counts,
            'server_types': {
                server_type.value: len(server_ids)
                for server_type, server_ids in self.type_index.items()
            },
            'capabilities': list(self.capabilities_index.keys()),
            'required_servers': len(self.get_required_servers()),
            'available_servers': len(self.get_available_servers())
        }

    async def start_health_monitoring(self) -> None:
        """Start the health monitoring system."""
        if self.running:
            logger.warning("Health monitoring already running")
            return
        
        self.running = True
        self.health_monitor_task = asyncio.create_task(self._health_monitor_loop())
        logger.info("Started MCP server health monitoring")

    async def stop_health_monitoring(self) -> None:
        """Stop the health monitoring system."""
        self.running = False
        if self.health_monitor_task:
            self.health_monitor_task.cancel()
            try:
                await self.health_monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped MCP server health monitoring")

    async def _health_monitor_loop(self) -> None:
        """Main health monitoring loop."""
        while self.running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying

    async def _perform_health_checks(self) -> None:
        """Perform health checks on all registered servers."""
        for server_id, server in self.servers.items():
            try:
                # Skip servers that are not supposed to be connected
                if server.status in [ServerStatus.MAINTENANCE, ServerStatus.UNKNOWN]:
                    continue
                
                # Check if server has been seen recently
                if server.last_seen:
                    time_since_seen = datetime.now() - server.last_seen
                    if time_since_seen > timedelta(minutes=5):
                        self.update_server_status(
                            server_id, 
                            ServerStatus.DISCONNECTED,
                            "No recent activity"
                        )
                
            except Exception as e:
                logger.error(f"Error checking health of server {server_id}: {e}")

    def export_registry(self) -> Dict[str, Any]:
        """Export the registry to a dictionary for persistence."""
        return {
            'servers': {
                server_id: {
                    'server_id': server.server_id,
                    'name': server.name,
                    'server_type': server.server_type.value,
                    'description': server.description,
                    'version': server.version,
                    'required': server.required,
                    'priority': server.priority,
                    'tags': list(server.tags),
                    'config': server.config,
                    'capabilities': [
                        {
                            'name': cap.name,
                            'description': cap.description,
                            'tools': cap.tools,
                            'data_types': cap.data_types,
                            'real_time': cap.real_time,
                            'priority': cap.priority
                        }
                        for cap in server.capabilities
                    ]
                }
                for server_id, server in self.servers.items()
            },
            'export_timestamp': datetime.now().isoformat()
        }

    def __str__(self) -> str:
        """String representation of the registry."""
        summary = self.get_registry_summary()
        return (f"MCPServerRegistry: {summary['total_servers']} servers, "
                f"{summary['available_servers']} available, "
                f"{len(summary['capabilities'])} capabilities")
