"""
Phase 3 MCP Orchestration Engine

Advanced MCP server orchestration and data fusion capabilities for the
MayArbi arbitrage system.

Components:
- ServerRegistry: Centralized MCP server registry and discovery
- DataFusionEngine: Intelligent data combination from multiple sources
- RealTimePipeline: Real-time data flow management
- CoordinatorService: MCP server communication orchestration
- HealthMonitor: Server health monitoring and failover
"""

from .server_registry import MCPServerRegistry, ServerStatus, ServerType, ServerCapability
from .data_fusion_engine import DataFusionEngine, FusionRequest, FusedData, DataQuality, ConflictResolution
from .real_time_pipeline import RealTimeDataPipeline, StreamEvent, StreamType, EventPriority, StreamSubscription
from .coordinator_service import MCPCoordinatorService, OperationType, OperationPriority, TransactionState
from .health_monitor import HealthMonitoringSystem, HealthStatus, AlertSeverity, HealthAlert

__all__ = [
    'MCPServerRegistry',
    'ServerStatus',
    'ServerType',
    'ServerCapability',
    'DataFusionEngine',
    'FusionRequest',
    'FusedData',
    'DataQuality',
    'ConflictResolution',
    'RealTimeDataPipeline',
    'StreamEvent',
    'StreamType',
    'EventPriority',
    'StreamSubscription',
    'MCPCoordinatorService',
    'OperationType',
    'OperationPriority',
    'TransactionState',
    'HealthMonitoringSystem',
    'HealthStatus',
    'AlertSeverity',
    'HealthAlert'
]

__version__ = '3.0.0'
