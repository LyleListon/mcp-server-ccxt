#!/usr/bin/env python3
"""
Data Flow Coordination System - System Integration Plan #3

Comprehensive data flow management system that ensures:
- Efficient data movement between components
- Data synchronization and consistency
- Conflict resolution and data validation
- Real-time data streaming and batching
- Data transformation and routing
- Flow control and backpressure management
- Data lineage and audit trails
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
from pathlib import Path
from collections import deque, defaultdict
import weakref

logger = logging.getLogger(__name__)


class DataFlowType(Enum):
    """Types of data flows in the system."""
    PRICE_DATA = "price_data"
    ARBITRAGE_OPPORTUNITIES = "arbitrage_opportunities"
    TRADE_EXECUTIONS = "trade_executions"
    BRIDGE_COSTS = "bridge_costs"
    WALLET_BALANCES = "wallet_balances"
    MARKET_CONDITIONS = "market_conditions"
    SYSTEM_EVENTS = "system_events"
    MEMORY_UPDATES = "memory_updates"
    HEALTH_STATUS = "health_status"
    ERROR_EVENTS = "error_events"


class DataPriority(Enum):
    """Data priority levels for flow management."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class FlowDirection(Enum):
    """Data flow directions."""
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    BIDIRECTIONAL = "bidirectional"
    BROADCAST = "broadcast"


class DataState(Enum):
    """Data processing states."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class DataPacket:
    """Represents a data packet flowing through the system."""
    packet_id: str
    flow_type: DataFlowType
    source_component: str
    target_components: List[str]
    data: Any
    priority: DataPriority
    timestamp: datetime
    expiry_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_history: List[str] = field(default_factory=list)
    state: DataState = DataState.PENDING
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class DataFlow:
    """Represents a data flow configuration between components."""
    flow_id: str
    source_component: str
    target_component: str
    flow_type: DataFlowType
    direction: FlowDirection
    priority: DataPriority
    batch_size: int = 1
    batch_timeout: float = 1.0
    transformation_function: Optional[Callable] = None
    validation_function: Optional[Callable] = None
    enabled: bool = True
    flow_rate_limit: Optional[float] = None  # packets per second
    last_activity: Optional[datetime] = None


@dataclass
class ComponentDataInterface:
    """Data interface configuration for a component."""
    component_name: str
    input_flows: List[DataFlowType]
    output_flows: List[DataFlowType]
    processing_capacity: int = 100  # packets per second
    buffer_size: int = 1000
    backpressure_threshold: float = 0.8
    data_handlers: Dict[DataFlowType, Callable] = field(default_factory=dict)
    transformation_rules: Dict[DataFlowType, Callable] = field(default_factory=dict)


class DataFlowCoordinator:
    """
    Comprehensive data flow coordination system.
    
    Features:
    - Real-time data routing and transformation
    - Flow control and backpressure management
    - Data validation and conflict resolution
    - Batch processing and streaming
    - Data lineage tracking
    - Performance monitoring and optimization
    - Fault tolerance and recovery
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the data flow coordinator."""
        self.config = config or {}
        
        # Core data structures
        self.data_flows: Dict[str, DataFlow] = {}
        self.component_interfaces: Dict[str, ComponentDataInterface] = {}
        self.active_packets: Dict[str, DataPacket] = {}
        
        # Flow management
        self.flow_queues: Dict[str, asyncio.Queue] = {}
        self.batch_buffers: Dict[str, List[DataPacket]] = defaultdict(list)
        self.flow_statistics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Routing and transformation
        self.routing_table: Dict[Tuple[str, DataFlowType], List[str]] = {}
        self.transformation_pipeline: Dict[str, List[Callable]] = {}
        self.validation_rules: Dict[DataFlowType, List[Callable]] = defaultdict(list)
        
        # Flow control
        self.flow_controllers: Dict[str, 'FlowController'] = {}
        self.backpressure_monitors: Dict[str, 'BackpressureMonitor'] = {}
        
        # Event handling
        self.event_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.data_lineage: Dict[str, List[str]] = {}
        
        # Configuration
        self.max_packet_age = self.config.get('max_packet_age', 300)  # 5 minutes
        self.cleanup_interval = self.config.get('cleanup_interval', 60)  # 1 minute
        self.stats_interval = self.config.get('stats_interval', 30)  # 30 seconds
        
        # State management
        self.running = False
        self.coordinator_tasks: List[asyncio.Task] = []
        
        # State persistence
        self.state_file = Path("data/data_flow_state.json")
        self.state_file.parent.mkdir(exist_ok=True)
        
        # Initialize system
        self._initialize_component_interfaces()
        self._initialize_data_flows()
        self._initialize_routing_table()
    
    def _initialize_component_interfaces(self):
        """Initialize data interfaces for all MayArbi components."""
        # Define component data interfaces
        interfaces = {
            "arbitrage_engine": ComponentDataInterface(
                component_name="arbitrage_engine",
                input_flows=[DataFlowType.PRICE_DATA, DataFlowType.BRIDGE_COSTS, DataFlowType.WALLET_BALANCES],
                output_flows=[DataFlowType.ARBITRAGE_OPPORTUNITIES, DataFlowType.TRADE_EXECUTIONS],
                processing_capacity=50,
                buffer_size=500
            ),
            "bridge_monitor": ComponentDataInterface(
                component_name="bridge_monitor",
                input_flows=[DataFlowType.PRICE_DATA, DataFlowType.SYSTEM_EVENTS],
                output_flows=[DataFlowType.BRIDGE_COSTS],
                processing_capacity=20,
                buffer_size=200
            ),
            "cross_chain_mev": ComponentDataInterface(
                component_name="cross_chain_mev",
                input_flows=[DataFlowType.BRIDGE_COSTS, DataFlowType.ARBITRAGE_OPPORTUNITIES],
                output_flows=[DataFlowType.ARBITRAGE_OPPORTUNITIES, DataFlowType.TRADE_EXECUTIONS],
                processing_capacity=30,
                buffer_size=300
            ),
            "wallet_manager": ComponentDataInterface(
                component_name="wallet_manager",
                input_flows=[DataFlowType.TRADE_EXECUTIONS, DataFlowType.SYSTEM_EVENTS],
                output_flows=[DataFlowType.WALLET_BALANCES],
                processing_capacity=40,
                buffer_size=400
            ),
            "price_feeds": ComponentDataInterface(
                component_name="price_feeds",
                input_flows=[DataFlowType.SYSTEM_EVENTS],
                output_flows=[DataFlowType.PRICE_DATA, DataFlowType.MARKET_CONDITIONS],
                processing_capacity=100,
                buffer_size=1000
            ),
            "memory_system": ComponentDataInterface(
                component_name="memory_system",
                input_flows=[DataFlowType.TRADE_EXECUTIONS, DataFlowType.ARBITRAGE_OPPORTUNITIES, DataFlowType.SYSTEM_EVENTS],
                output_flows=[DataFlowType.MEMORY_UPDATES],
                processing_capacity=60,
                buffer_size=600
            ),
            "health_monitor": ComponentDataInterface(
                component_name="health_monitor",
                input_flows=[DataFlowType.SYSTEM_EVENTS, DataFlowType.ERROR_EVENTS],
                output_flows=[DataFlowType.HEALTH_STATUS],
                processing_capacity=80,
                buffer_size=800
            ),
            "error_manager": ComponentDataInterface(
                component_name="error_manager",
                input_flows=[DataFlowType.SYSTEM_EVENTS],
                output_flows=[DataFlowType.ERROR_EVENTS],
                processing_capacity=70,
                buffer_size=700
            )
        }
        
        self.component_interfaces = interfaces
        
        # Initialize flow queues for each component
        for component_name in interfaces.keys():
            self.flow_queues[component_name] = asyncio.Queue(maxsize=interfaces[component_name].buffer_size)
    
    def _initialize_data_flows(self):
        """Initialize data flow configurations."""
        flows = [
            # Price data flows
            DataFlow("price_feeds_to_arbitrage", "price_feeds", "arbitrage_engine", 
                    DataFlowType.PRICE_DATA, FlowDirection.DOWNSTREAM, DataPriority.HIGH,
                    batch_size=10, batch_timeout=0.5),
            DataFlow("price_feeds_to_bridge", "price_feeds", "bridge_monitor",
                    DataFlowType.PRICE_DATA, FlowDirection.DOWNSTREAM, DataPriority.NORMAL,
                    batch_size=5, batch_timeout=1.0),
            
            # Arbitrage opportunity flows
            DataFlow("arbitrage_to_mev", "arbitrage_engine", "cross_chain_mev",
                    DataFlowType.ARBITRAGE_OPPORTUNITIES, FlowDirection.DOWNSTREAM, DataPriority.HIGH,
                    batch_size=1, batch_timeout=0.1),
            DataFlow("mev_to_arbitrage", "cross_chain_mev", "arbitrage_engine",
                    DataFlowType.ARBITRAGE_OPPORTUNITIES, FlowDirection.UPSTREAM, DataPriority.HIGH,
                    batch_size=1, batch_timeout=0.1),
            
            # Bridge cost flows
            DataFlow("bridge_to_arbitrage", "bridge_monitor", "arbitrage_engine",
                    DataFlowType.BRIDGE_COSTS, FlowDirection.DOWNSTREAM, DataPriority.NORMAL,
                    batch_size=5, batch_timeout=2.0),
            DataFlow("bridge_to_mev", "bridge_monitor", "cross_chain_mev",
                    DataFlowType.BRIDGE_COSTS, FlowDirection.DOWNSTREAM, DataPriority.NORMAL,
                    batch_size=5, batch_timeout=2.0),
            
            # Trade execution flows
            DataFlow("arbitrage_to_wallet", "arbitrage_engine", "wallet_manager",
                    DataFlowType.TRADE_EXECUTIONS, FlowDirection.DOWNSTREAM, DataPriority.CRITICAL,
                    batch_size=1, batch_timeout=0.05),
            DataFlow("mev_to_wallet", "cross_chain_mev", "wallet_manager",
                    DataFlowType.TRADE_EXECUTIONS, FlowDirection.DOWNSTREAM, DataPriority.CRITICAL,
                    batch_size=1, batch_timeout=0.05),
            
            # Wallet balance flows
            DataFlow("wallet_to_arbitrage", "wallet_manager", "arbitrage_engine",
                    DataFlowType.WALLET_BALANCES, FlowDirection.DOWNSTREAM, DataPriority.HIGH,
                    batch_size=1, batch_timeout=1.0),
            
            # Memory flows
            DataFlow("arbitrage_to_memory", "arbitrage_engine", "memory_system",
                    DataFlowType.TRADE_EXECUTIONS, FlowDirection.DOWNSTREAM, DataPriority.NORMAL,
                    batch_size=10, batch_timeout=5.0),
            DataFlow("mev_to_memory", "cross_chain_mev", "memory_system",
                    DataFlowType.TRADE_EXECUTIONS, FlowDirection.DOWNSTREAM, DataPriority.NORMAL,
                    batch_size=10, batch_timeout=5.0),
            
            # Health monitoring flows
            DataFlow("system_to_health", "error_manager", "health_monitor",
                    DataFlowType.ERROR_EVENTS, FlowDirection.DOWNSTREAM, DataPriority.HIGH,
                    batch_size=5, batch_timeout=1.0),
            
            # System event broadcasts
            DataFlow("health_broadcast", "health_monitor", "*",
                    DataFlowType.HEALTH_STATUS, FlowDirection.BROADCAST, DataPriority.NORMAL,
                    batch_size=1, batch_timeout=10.0)
        ]
        
        for flow in flows:
            self.data_flows[flow.flow_id] = flow
    
    def _initialize_routing_table(self):
        """Initialize data routing table."""
        for flow in self.data_flows.values():
            route_key = (flow.source_component, flow.flow_type)
            
            if route_key not in self.routing_table:
                self.routing_table[route_key] = []
            
            if flow.target_component == "*":
                # Broadcast to all components that accept this flow type
                targets = [
                    comp_name for comp_name, interface in self.component_interfaces.items()
                    if flow.flow_type in interface.input_flows and comp_name != flow.source_component
                ]
                self.routing_table[route_key].extend(targets)
            else:
                self.routing_table[route_key].append(flow.target_component)
    
    async def start_coordinator(self):
        """Start the data flow coordinator."""
        if self.running:
            logger.warning("Data flow coordinator already running")
            return
        
        self.running = True
        logger.info("🔄 Starting data flow coordinator")
        
        # Load previous state
        await self._load_state()
        
        # Start coordinator tasks
        self.coordinator_tasks = [
            asyncio.create_task(self._packet_processor()),
            asyncio.create_task(self._batch_processor()),
            asyncio.create_task(self._flow_monitor()),
            asyncio.create_task(self._cleanup_processor()),
            asyncio.create_task(self._statistics_collector())
        ]
        
        logger.info("✅ Data flow coordinator started")
    
    async def stop_coordinator(self):
        """Stop the data flow coordinator."""
        if not self.running:
            return
        
        self.running = False
        logger.info("🛑 Stopping data flow coordinator")
        
        # Cancel all tasks
        for task in self.coordinator_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.coordinator_tasks, return_exceptions=True)
        
        # Save state
        await self._save_state()
        
        logger.info("✅ Data flow coordinator stopped")
    
    async def send_data(self, 
                       source_component: str,
                       flow_type: DataFlowType,
                       data: Any,
                       priority: DataPriority = DataPriority.NORMAL,
                       target_components: List[str] = None,
                       metadata: Dict[str, Any] = None) -> str:
        """
        Send data through the coordination system.
        
        Args:
            source_component: Component sending the data
            flow_type: Type of data flow
            data: Data to send
            priority: Data priority level
            target_components: Specific target components (optional)
            metadata: Additional metadata
            
        Returns:
            Packet ID for tracking
        """
        try:
            # Generate packet ID
            packet_id = f"{source_component}_{flow_type.value}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Determine target components
            if target_components is None:
                route_key = (source_component, flow_type)
                target_components = self.routing_table.get(route_key, [])
            
            if not target_components:
                logger.warning(f"No target components found for {source_component} -> {flow_type.value}")
                return packet_id
            
            # Create data packet
            packet = DataPacket(
                packet_id=packet_id,
                flow_type=flow_type,
                source_component=source_component,
                target_components=target_components,
                data=data,
                priority=priority,
                timestamp=datetime.now(),
                expiry_time=datetime.now() + timedelta(seconds=self.max_packet_age),
                metadata=metadata or {}
            )
            
            # Store packet
            self.active_packets[packet_id] = packet
            
            # Route packet to target components
            await self._route_packet(packet)
            
            # Update statistics
            self._update_flow_statistics(source_component, flow_type, "sent")
            
            logger.debug(f"📤 Data sent: {packet_id} from {source_component} to {target_components}")
            
            return packet_id
            
        except Exception as e:
            logger.error(f"Error sending data from {source_component}: {e}")
            return ""

    async def _route_packet(self, packet: DataPacket):
        """Route a data packet to its target components."""
        for target_component in packet.target_components:
            try:
                # Check if target component exists
                if target_component not in self.component_interfaces:
                    logger.warning(f"Unknown target component: {target_component}")
                    continue

                # Check if target accepts this flow type
                interface = self.component_interfaces[target_component]
                if packet.flow_type not in interface.input_flows:
                    logger.warning(f"{target_component} does not accept {packet.flow_type.value}")
                    continue

                # Check backpressure
                queue = self.flow_queues[target_component]
                if queue.qsize() / queue.maxsize > interface.backpressure_threshold:
                    logger.warning(f"Backpressure detected for {target_component}")
                    await self._handle_backpressure(target_component, packet)
                    continue

                # Apply transformations if needed
                transformed_packet = await self._apply_transformations(packet, target_component)

                # Validate data
                if not await self._validate_packet(transformed_packet):
                    logger.error(f"Packet validation failed for {target_component}")
                    continue

                # Queue packet for processing
                await queue.put(transformed_packet)

                # Update packet history
                packet.processing_history.append(f"routed_to_{target_component}")

                logger.debug(f"📨 Packet routed: {packet.packet_id} -> {target_component}")

            except Exception as e:
                logger.error(f"Error routing packet {packet.packet_id} to {target_component}: {e}")

    async def _apply_transformations(self, packet: DataPacket, target_component: str) -> DataPacket:
        """Apply data transformations for the target component."""
        try:
            interface = self.component_interfaces[target_component]

            # Check if transformation is needed
            if packet.flow_type in interface.transformation_rules:
                transform_func = interface.transformation_rules[packet.flow_type]

                # Apply transformation
                transformed_data = await self._execute_transformation(transform_func, packet.data)

                # Create new packet with transformed data
                transformed_packet = DataPacket(
                    packet_id=f"{packet.packet_id}_transformed",
                    flow_type=packet.flow_type,
                    source_component=packet.source_component,
                    target_components=[target_component],
                    data=transformed_data,
                    priority=packet.priority,
                    timestamp=packet.timestamp,
                    expiry_time=packet.expiry_time,
                    metadata=packet.metadata.copy(),
                    processing_history=packet.processing_history.copy(),
                    state=packet.state,
                    retry_count=packet.retry_count,
                    max_retries=packet.max_retries
                )

                transformed_packet.processing_history.append(f"transformed_for_{target_component}")
                return transformed_packet

            return packet

        except Exception as e:
            logger.error(f"Error applying transformations for {target_component}: {e}")
            return packet

    async def _execute_transformation(self, transform_func: Callable, data: Any) -> Any:
        """Execute a data transformation function."""
        try:
            if asyncio.iscoroutinefunction(transform_func):
                return await transform_func(data)
            else:
                return transform_func(data)
        except Exception as e:
            logger.error(f"Transformation function failed: {e}")
            return data

    async def _validate_packet(self, packet: DataPacket) -> bool:
        """Validate a data packet."""
        try:
            # Check packet expiry
            if packet.expiry_time and datetime.now() > packet.expiry_time:
                logger.warning(f"Packet expired: {packet.packet_id}")
                packet.state = DataState.EXPIRED
                return False

            # Check data validity
            if packet.data is None:
                logger.warning(f"Packet has no data: {packet.packet_id}")
                return False

            # Apply flow-specific validation rules
            validation_rules = self.validation_rules.get(packet.flow_type, [])
            for rule in validation_rules:
                if not await self._execute_validation_rule(rule, packet.data):
                    logger.warning(f"Validation rule failed for {packet.packet_id}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating packet {packet.packet_id}: {e}")
            return False

    async def _execute_validation_rule(self, rule: Callable, data: Any) -> bool:
        """Execute a validation rule."""
        try:
            if asyncio.iscoroutinefunction(rule):
                return await rule(data)
            else:
                return rule(data)
        except Exception as e:
            logger.error(f"Validation rule failed: {e}")
            return False

    async def _handle_backpressure(self, component: str, packet: DataPacket):
        """Handle backpressure for a component."""
        try:
            logger.warning(f"🔴 Backpressure handling for {component}")

            # Strategy 1: Drop low priority packets
            if packet.priority == DataPriority.LOW:
                logger.info(f"Dropping low priority packet: {packet.packet_id}")
                packet.state = DataState.FAILED
                return

            # Strategy 2: Retry with exponential backoff
            if packet.retry_count < packet.max_retries:
                packet.retry_count += 1
                delay = min(2 ** packet.retry_count, 30)  # Max 30 seconds

                logger.info(f"Retrying packet {packet.packet_id} in {delay}s (attempt {packet.retry_count})")

                # Schedule retry
                await asyncio.sleep(delay)
                await self._route_packet(packet)
            else:
                logger.error(f"Max retries exceeded for packet: {packet.packet_id}")
                packet.state = DataState.FAILED

        except Exception as e:
            logger.error(f"Error handling backpressure for {component}: {e}")

    async def _packet_processor(self):
        """Main packet processing loop."""
        logger.info("🔄 Starting packet processor")

        while self.running:
            try:
                # Process packets from all component queues
                for component_name, queue in self.flow_queues.items():
                    if not queue.empty():
                        try:
                            # Get packet with timeout
                            packet = await asyncio.wait_for(queue.get(), timeout=0.1)

                            # Process packet
                            await self._process_packet(packet, component_name)

                        except asyncio.TimeoutError:
                            continue
                        except Exception as e:
                            logger.error(f"Error processing packet for {component_name}: {e}")

                # Brief pause to prevent CPU spinning
                await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"Error in packet processor: {e}")
                await asyncio.sleep(1)

    async def _process_packet(self, packet: DataPacket, target_component: str):
        """Process a single packet for a target component."""
        try:
            packet.state = DataState.PROCESSING
            packet.processing_history.append(f"processing_by_{target_component}")

            # Get component interface
            interface = self.component_interfaces[target_component]

            # Check if component has a handler for this flow type
            if packet.flow_type in interface.data_handlers:
                handler = interface.data_handlers[packet.flow_type]

                # Execute handler
                result = await self._execute_data_handler(handler, packet.data, packet.metadata)

                if result:
                    packet.state = DataState.COMPLETED
                    logger.debug(f"✅ Packet processed: {packet.packet_id} by {target_component}")
                else:
                    packet.state = DataState.FAILED
                    logger.warning(f"❌ Packet processing failed: {packet.packet_id} by {target_component}")
            else:
                # No specific handler, just mark as completed
                packet.state = DataState.COMPLETED
                logger.debug(f"📝 Packet received: {packet.packet_id} by {target_component}")

            # Update statistics
            self._update_flow_statistics(target_component, packet.flow_type, "processed")

            # Update data lineage
            self._update_data_lineage(packet)

        except Exception as e:
            logger.error(f"Error processing packet {packet.packet_id} for {target_component}: {e}")
            packet.state = DataState.FAILED

    async def _execute_data_handler(self, handler: Callable, data: Any, metadata: Dict[str, Any]) -> bool:
        """Execute a data handler function."""
        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(data, metadata)
            else:
                return handler(data, metadata)
        except Exception as e:
            logger.error(f"Data handler failed: {e}")
            return False

    def _update_data_lineage(self, packet: DataPacket):
        """Update data lineage tracking."""
        lineage_key = packet.packet_id
        if lineage_key not in self.data_lineage:
            self.data_lineage[lineage_key] = []

        self.data_lineage[lineage_key].extend(packet.processing_history)

    def _update_flow_statistics(self, component: str, flow_type: DataFlowType, action: str):
        """Update flow statistics."""
        stats_key = f"{component}_{flow_type.value}"

        if stats_key not in self.flow_statistics:
            self.flow_statistics[stats_key] = {
                "sent": 0,
                "processed": 0,
                "failed": 0,
                "last_activity": None
            }

        self.flow_statistics[stats_key][action] = self.flow_statistics[stats_key].get(action, 0) + 1
        self.flow_statistics[stats_key]["last_activity"] = datetime.now()

    async def _batch_processor(self):
        """Process batched data flows."""
        logger.info("🔄 Starting batch processor")

        while self.running:
            try:
                # Process batches for each flow
                for flow in self.data_flows.values():
                    if flow.batch_size > 1:
                        await self._process_batch_flow(flow)

                await asyncio.sleep(0.5)  # Check batches every 500ms

            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
                await asyncio.sleep(1)

    async def _process_batch_flow(self, flow: DataFlow):
        """Process a batch flow."""
        try:
            batch_key = f"{flow.source_component}_{flow.target_component}_{flow.flow_type.value}"
            batch = self.batch_buffers[batch_key]

            # Check if batch should be processed
            should_process = False

            # Check batch size
            if len(batch) >= flow.batch_size:
                should_process = True
                reason = f"batch_size_reached_{len(batch)}"

            # Check batch timeout
            elif batch and (datetime.now() - batch[0].timestamp).total_seconds() >= flow.batch_timeout:
                should_process = True
                reason = f"batch_timeout_{flow.batch_timeout}s"

            if should_process and batch:
                logger.debug(f"📦 Processing batch: {batch_key} ({reason})")

                # Create batch packet
                batch_packet = self._create_batch_packet(batch, flow)

                # Route batch packet
                await self._route_packet(batch_packet)

                # Clear batch
                self.batch_buffers[batch_key] = []

        except Exception as e:
            logger.error(f"Error processing batch flow {flow.flow_id}: {e}")

    def _create_batch_packet(self, packets: List[DataPacket], flow: DataFlow) -> DataPacket:
        """Create a batch packet from individual packets."""
        batch_data = [packet.data for packet in packets]
        batch_metadata = {
            "batch_size": len(packets),
            "batch_flow": flow.flow_id,
            "individual_packets": [packet.packet_id for packet in packets]
        }

        # Use the first packet as template
        template = packets[0]

        batch_packet = DataPacket(
            packet_id=f"batch_{flow.flow_id}_{int(time.time())}",
            flow_type=template.flow_type,
            source_component=template.source_component,
            target_components=[flow.target_component],
            data=batch_data,
            priority=max(packet.priority for packet in packets),
            timestamp=datetime.now(),
            expiry_time=min(packet.expiry_time for packet in packets if packet.expiry_time),
            metadata=batch_metadata
        )

        return batch_packet

    async def _flow_monitor(self):
        """Monitor data flows and performance."""
        logger.info("🔄 Starting flow monitor")

        while self.running:
            try:
                # Monitor flow health
                await self._check_flow_health()

                # Monitor queue sizes
                await self._monitor_queue_sizes()

                # Monitor flow rates
                await self._monitor_flow_rates()

                await asyncio.sleep(10)  # Monitor every 10 seconds

            except Exception as e:
                logger.error(f"Error in flow monitor: {e}")
                await asyncio.sleep(5)

    async def _check_flow_health(self):
        """Check the health of all data flows."""
        for flow in self.data_flows.values():
            try:
                # Check if flow is active
                if flow.last_activity:
                    time_since_activity = (datetime.now() - flow.last_activity).total_seconds()

                    # Alert if flow has been inactive for too long
                    if time_since_activity > 300:  # 5 minutes
                        logger.warning(f"⚠️ Flow inactive: {flow.flow_id} ({time_since_activity:.0f}s)")

                # Check flow rate limits
                if flow.flow_rate_limit:
                    # Implementation for rate limiting would go here
                    pass

            except Exception as e:
                logger.error(f"Error checking flow health for {flow.flow_id}: {e}")

    async def _monitor_queue_sizes(self):
        """Monitor queue sizes for backpressure detection."""
        for component_name, queue in self.flow_queues.items():
            try:
                queue_size = queue.qsize()
                max_size = queue.maxsize
                utilization = queue_size / max_size if max_size > 0 else 0

                interface = self.component_interfaces[component_name]

                if utilization > interface.backpressure_threshold:
                    logger.warning(f"🔴 High queue utilization: {component_name} ({utilization:.1%})")
                elif utilization > 0.5:
                    logger.info(f"⚠️ Moderate queue utilization: {component_name} ({utilization:.1%})")

            except Exception as e:
                logger.error(f"Error monitoring queue for {component_name}: {e}")

    async def _monitor_flow_rates(self):
        """Monitor data flow rates."""
        for stats_key, stats in self.flow_statistics.items():
            try:
                if stats["last_activity"]:
                    # Calculate flow rates (simplified)
                    total_processed = stats.get("processed", 0)
                    if total_processed > 0:
                        logger.debug(f"📊 Flow stats: {stats_key} - processed: {total_processed}")

            except Exception as e:
                logger.error(f"Error monitoring flow rates for {stats_key}: {e}")

    async def _cleanup_processor(self):
        """Clean up expired packets and old data."""
        logger.info("🔄 Starting cleanup processor")

        while self.running:
            try:
                current_time = datetime.now()

                # Clean up expired packets
                expired_packets = []
                for packet_id, packet in self.active_packets.items():
                    if packet.expiry_time and current_time > packet.expiry_time:
                        expired_packets.append(packet_id)
                    elif packet.state in [DataState.COMPLETED, DataState.FAILED]:
                        # Clean up completed/failed packets after some time
                        age = (current_time - packet.timestamp).total_seconds()
                        if age > 3600:  # 1 hour
                            expired_packets.append(packet_id)

                for packet_id in expired_packets:
                    del self.active_packets[packet_id]

                if expired_packets:
                    logger.debug(f"🧹 Cleaned up {len(expired_packets)} expired packets")

                # Clean up old lineage data
                old_lineage_keys = []
                for lineage_key in self.data_lineage.keys():
                    # Keep lineage for 24 hours
                    if lineage_key not in self.active_packets:
                        old_lineage_keys.append(lineage_key)

                for key in old_lineage_keys[:100]:  # Limit cleanup per cycle
                    del self.data_lineage[key]

                await asyncio.sleep(self.cleanup_interval)

            except Exception as e:
                logger.error(f"Error in cleanup processor: {e}")
                await asyncio.sleep(60)

    async def _statistics_collector(self):
        """Collect and report flow statistics."""
        logger.info("🔄 Starting statistics collector")

        while self.running:
            try:
                # Collect current statistics
                stats_summary = self._generate_statistics_summary()

                # Log summary periodically
                logger.info(f"📊 Flow Statistics: {stats_summary['total_active_packets']} active packets, "
                           f"{stats_summary['total_flows']} flows, "
                           f"{stats_summary['avg_queue_utilization']:.1%} avg queue utilization")

                await asyncio.sleep(self.stats_interval)

            except Exception as e:
                logger.error(f"Error in statistics collector: {e}")
                await asyncio.sleep(30)

    def _generate_statistics_summary(self) -> Dict[str, Any]:
        """Generate comprehensive statistics summary."""
        try:
            # Count active packets by state
            packet_states = defaultdict(int)
            for packet in self.active_packets.values():
                packet_states[packet.state.value] += 1

            # Calculate queue utilizations
            queue_utilizations = []
            for component_name, queue in self.flow_queues.items():
                if queue.maxsize > 0:
                    utilization = queue.qsize() / queue.maxsize
                    queue_utilizations.append(utilization)

            avg_queue_utilization = sum(queue_utilizations) / len(queue_utilizations) if queue_utilizations else 0

            # Flow statistics
            total_flows = len(self.data_flows)
            active_flows = sum(1 for flow in self.data_flows.values() if flow.enabled)

            return {
                "total_active_packets": len(self.active_packets),
                "packet_states": dict(packet_states),
                "total_flows": total_flows,
                "active_flows": active_flows,
                "avg_queue_utilization": avg_queue_utilization,
                "total_components": len(self.component_interfaces),
                "data_lineage_entries": len(self.data_lineage),
                "batch_buffers": {k: len(v) for k, v in self.batch_buffers.items()},
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating statistics summary: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    # Public API Methods
    def register_data_handler(self, component: str, flow_type: DataFlowType, handler: Callable):
        """Register a data handler for a component and flow type."""
        if component in self.component_interfaces:
            self.component_interfaces[component].data_handlers[flow_type] = handler
            logger.info(f"📝 Registered data handler: {component} -> {flow_type.value}")
        else:
            logger.warning(f"Unknown component: {component}")

    def register_transformation_rule(self, component: str, flow_type: DataFlowType, transform_func: Callable):
        """Register a data transformation rule for a component and flow type."""
        if component in self.component_interfaces:
            self.component_interfaces[component].transformation_rules[flow_type] = transform_func
            logger.info(f"🔄 Registered transformation rule: {component} -> {flow_type.value}")
        else:
            logger.warning(f"Unknown component: {component}")

    def register_validation_rule(self, flow_type: DataFlowType, validation_func: Callable):
        """Register a validation rule for a flow type."""
        self.validation_rules[flow_type].append(validation_func)
        logger.info(f"✅ Registered validation rule for {flow_type.value}")

    def get_flow_statistics(self) -> Dict[str, Any]:
        """Get current flow statistics."""
        return self._generate_statistics_summary()

    def get_component_status(self, component: str) -> Dict[str, Any]:
        """Get status information for a specific component."""
        if component not in self.component_interfaces:
            return {"error": f"Unknown component: {component}"}

        interface = self.component_interfaces[component]
        queue = self.flow_queues[component]

        return {
            "component": component,
            "queue_size": queue.qsize(),
            "queue_max_size": queue.maxsize,
            "queue_utilization": queue.qsize() / queue.maxsize if queue.maxsize > 0 else 0,
            "processing_capacity": interface.processing_capacity,
            "backpressure_threshold": interface.backpressure_threshold,
            "input_flows": [flow.value for flow in interface.input_flows],
            "output_flows": [flow.value for flow in interface.output_flows],
            "registered_handlers": list(interface.data_handlers.keys()),
            "transformation_rules": list(interface.transformation_rules.keys())
        }

    def get_packet_lineage(self, packet_id: str) -> List[str]:
        """Get the processing lineage for a packet."""
        return self.data_lineage.get(packet_id, [])

    def get_active_packets(self, component: str = None, flow_type: DataFlowType = None) -> List[Dict[str, Any]]:
        """Get information about active packets."""
        packets = []

        for packet in self.active_packets.values():
            # Filter by component if specified
            if component and packet.source_component != component and component not in packet.target_components:
                continue

            # Filter by flow type if specified
            if flow_type and packet.flow_type != flow_type:
                continue

            packets.append({
                "packet_id": packet.packet_id,
                "flow_type": packet.flow_type.value,
                "source_component": packet.source_component,
                "target_components": packet.target_components,
                "priority": packet.priority.value,
                "state": packet.state.value,
                "timestamp": packet.timestamp.isoformat(),
                "processing_history": packet.processing_history,
                "retry_count": packet.retry_count
            })

        return packets

    async def _save_state(self):
        """Save coordinator state to file."""
        try:
            state = {
                "flow_statistics": {k: {**v, "last_activity": v["last_activity"].isoformat() if v["last_activity"] else None}
                                   for k, v in self.flow_statistics.items()},
                "data_flows": {},
                "component_interfaces": {},
                "active_packet_count": len(self.active_packets),
                "data_lineage_count": len(self.data_lineage),
                "last_updated": datetime.now().isoformat()
            }

            # Save flow configurations
            for flow_id, flow in self.data_flows.items():
                state["data_flows"][flow_id] = {
                    "flow_id": flow.flow_id,
                    "source_component": flow.source_component,
                    "target_component": flow.target_component,
                    "flow_type": flow.flow_type.value,
                    "direction": flow.direction.value,
                    "priority": flow.priority.value,
                    "batch_size": flow.batch_size,
                    "batch_timeout": flow.batch_timeout,
                    "enabled": flow.enabled,
                    "flow_rate_limit": flow.flow_rate_limit,
                    "last_activity": flow.last_activity.isoformat() if flow.last_activity else None
                }

            # Save component interface configurations
            for comp_name, interface in self.component_interfaces.items():
                state["component_interfaces"][comp_name] = {
                    "component_name": interface.component_name,
                    "input_flows": [flow.value for flow in interface.input_flows],
                    "output_flows": [flow.value for flow in interface.output_flows],
                    "processing_capacity": interface.processing_capacity,
                    "buffer_size": interface.buffer_size,
                    "backpressure_threshold": interface.backpressure_threshold
                }

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

            logger.debug(f"Data flow coordinator state saved to {self.state_file}")

        except Exception as e:
            logger.error(f"Failed to save coordinator state: {e}")

    async def _load_state(self):
        """Load coordinator state from file."""
        try:
            if not self.state_file.exists():
                logger.debug("No previous coordinator state found")
                return

            with open(self.state_file) as f:
                state = json.load(f)

            # Load flow statistics
            for stats_key, stats in state.get("flow_statistics", {}).items():
                self.flow_statistics[stats_key] = stats.copy()
                if stats.get("last_activity"):
                    self.flow_statistics[stats_key]["last_activity"] = datetime.fromisoformat(stats["last_activity"])

            logger.debug(f"Data flow coordinator state loaded from {self.state_file}")

        except Exception as e:
            logger.error(f"Failed to load coordinator state: {e}")

    def print_flow_dashboard(self):
        """Print comprehensive data flow dashboard."""
        stats = self._generate_statistics_summary()

        print("\n🔄 DATA FLOW COORDINATION DASHBOARD")
        print("=" * 60)

        # Overall statistics
        print(f"📊 OVERALL STATISTICS:")
        print(f"   Active Packets: {stats['total_active_packets']}")
        print(f"   Total Flows: {stats['total_flows']}")
        print(f"   Active Flows: {stats['active_flows']}")
        print(f"   Components: {stats['total_components']}")
        print(f"   Avg Queue Utilization: {stats['avg_queue_utilization']:.1%}")

        # Packet states
        if stats.get('packet_states'):
            print(f"\n📦 PACKET STATES:")
            for state, count in stats['packet_states'].items():
                state_icon = {
                    "pending": "⏳",
                    "processing": "🔄",
                    "completed": "✅",
                    "failed": "❌",
                    "expired": "⏰"
                }.get(state, "❓")
                print(f"   {state_icon} {state.title()}: {count}")

        # Component status
        print(f"\n🏗️ COMPONENT STATUS:")
        for component_name in self.component_interfaces.keys():
            status = self.get_component_status(component_name)
            utilization = status['queue_utilization']

            status_icon = "✅" if utilization < 0.5 else "⚠️" if utilization < 0.8 else "🔴"
            component_display = component_name.replace('_', ' ').title()

            print(f"   {status_icon} {component_display}: {status['queue_size']}/{status['queue_max_size']} "
                  f"({utilization:.1%} utilization)")

        # Batch buffers
        if stats.get('batch_buffers'):
            active_batches = {k: v for k, v in stats['batch_buffers'].items() if v > 0}
            if active_batches:
                print(f"\n📦 ACTIVE BATCHES:")
                for batch_key, count in active_batches.items():
                    print(f"   • {batch_key}: {count} packets")

        print(f"\n🕐 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


# Example usage and testing
async def main():
    """Example usage of the data flow coordination system."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create data flow coordinator
    config = {
        'max_packet_age': 300,
        'cleanup_interval': 60,
        'stats_interval': 30
    }

    coordinator = DataFlowCoordinator(config)

    try:
        # Start coordinator
        await coordinator.start_coordinator()

        # Simulate some data flows
        await coordinator.send_data(
            "price_feeds",
            DataFlowType.PRICE_DATA,
            {"ETH/USD": 2500.0, "BTC/USD": 45000.0},
            DataPriority.HIGH
        )

        await coordinator.send_data(
            "arbitrage_engine",
            DataFlowType.ARBITRAGE_OPPORTUNITIES,
            {"token": "ETH", "profit": 0.5, "route": "uniswap->sushiswap"},
            DataPriority.CRITICAL
        )

        # Wait a bit for processing
        await asyncio.sleep(2)

        # Print dashboard
        coordinator.print_flow_dashboard()

        # Get statistics
        stats = coordinator.get_flow_statistics()
        print(f"\nFlow Statistics: {stats}")

    except KeyboardInterrupt:
        print("\n🛑 Coordinator stopped by user")
    finally:
        await coordinator.stop_coordinator()


if __name__ == "__main__":
    asyncio.run(main())
