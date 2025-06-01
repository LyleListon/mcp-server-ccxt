"""
Real-time Data Pipeline - Phase 3 Chunk 3

Manages real-time data flows between MCP servers with event streaming,
data synchronization, and reactive pipelines for arbitrage opportunities.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict, deque

from .server_registry import MCPServerRegistry, ServerStatus, ServerType
from .data_fusion_engine import DataFusionEngine, FusionRequest, DataQuality

logger = logging.getLogger(__name__)


class StreamType(Enum):
    """Types of data streams."""
    PRICE_UPDATES = "price_updates"
    VOLUME_CHANGES = "volume_changes"
    ARBITRAGE_OPPORTUNITIES = "arbitrage_opportunities"
    MARKET_CONDITIONS = "market_conditions"
    TRADE_EXECUTIONS = "trade_executions"
    SERVER_EVENTS = "server_events"


class EventPriority(Enum):
    """Event priority levels."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass
class StreamEvent:
    """Real-time stream event."""
    event_id: str
    stream_type: StreamType
    source_server: str
    data: Dict[str, Any]
    timestamp: datetime
    priority: EventPriority = EventPriority.NORMAL
    sequence_number: int = 0
    correlation_id: Optional[str] = None


@dataclass
class StreamSubscription:
    """Stream subscription configuration."""
    subscription_id: str
    stream_types: List[StreamType]
    callback: Callable[[StreamEvent], None]
    filters: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_event: Optional[datetime] = None
    event_count: int = 0


@dataclass
class StreamMetrics:
    """Stream performance metrics."""
    events_processed: int = 0
    events_per_second: float = 0.0
    average_latency_ms: float = 0.0
    error_count: int = 0
    last_event_time: Optional[datetime] = None
    backpressure_events: int = 0


class RealTimeDataPipeline:
    """
    Real-time data pipeline for MCP server event streaming and synchronization.
    
    This is Chunk 3 of the Phase 3 MCP Orchestration Engine.
    """

    def __init__(self, server_registry: MCPServerRegistry, 
                 fusion_engine: DataFusionEngine, config: Dict[str, Any] = None):
        """Initialize the real-time data pipeline."""
        self.server_registry = server_registry
        self.fusion_engine = fusion_engine
        self.config = config or {}
        
        # Pipeline configuration
        self.max_queue_size = self.config.get('max_queue_size', 1000)
        self.batch_size = self.config.get('batch_size', 10)
        self.flush_interval = self.config.get('flush_interval', 1.0)  # seconds
        self.backpressure_threshold = self.config.get('backpressure_threshold', 0.8)
        
        # Event management
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=self.max_queue_size)
        self.subscriptions: Dict[str, StreamSubscription] = {}
        self.stream_metrics: Dict[StreamType, StreamMetrics] = {
            stream_type: StreamMetrics() for stream_type in StreamType
        }
        
        # Pipeline state
        self.running = False
        self.pipeline_task: Optional[asyncio.Task] = None
        self.producer_tasks: List[asyncio.Task] = []
        self.sequence_counter = 0
        
        # Event history for replay and debugging
        self.event_history: deque = deque(maxlen=1000)
        
        # Stream processors
        self.stream_processors: Dict[StreamType, Callable] = {
            StreamType.PRICE_UPDATES: self._process_price_updates,
            StreamType.ARBITRAGE_OPPORTUNITIES: self._process_arbitrage_opportunities,
            StreamType.MARKET_CONDITIONS: self._process_market_conditions,
            StreamType.TRADE_EXECUTIONS: self._process_trade_executions
        }

    async def start_pipeline(self) -> None:
        """Start the real-time data pipeline."""
        if self.running:
            logger.warning("Pipeline already running")
            return
        
        self.running = True
        logger.info("Starting real-time data pipeline")
        
        # Start main pipeline processor
        self.pipeline_task = asyncio.create_task(self._pipeline_processor())
        
        # Start data producers for real-time capable servers
        await self._start_data_producers()
        
        logger.info("Real-time data pipeline started successfully")

    async def stop_pipeline(self) -> None:
        """Stop the real-time data pipeline."""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping real-time data pipeline")
        
        # Stop data producers
        for task in self.producer_tasks:
            task.cancel()
        
        if self.producer_tasks:
            await asyncio.gather(*self.producer_tasks, return_exceptions=True)
        
        # Stop main pipeline
        if self.pipeline_task:
            self.pipeline_task.cancel()
            try:
                await self.pipeline_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Real-time data pipeline stopped")

    async def _start_data_producers(self) -> None:
        """Start data producers for real-time capable servers."""
        real_time_servers = []
        
        for server in self.server_registry.get_available_servers():
            # Check if server has real-time capabilities
            has_real_time = any(
                cap.real_time for cap in server.capabilities
            )
            if has_real_time:
                real_time_servers.append(server)
        
        logger.info(f"Starting {len(real_time_servers)} real-time data producers")
        
        for server in real_time_servers:
            task = asyncio.create_task(
                self._data_producer(server),
                name=f"producer_{server.server_id}"
            )
            self.producer_tasks.append(task)

    async def _data_producer(self, server) -> None:
        """Data producer for a specific server."""
        logger.info(f"Starting data producer for {server.server_id}")
        
        try:
            while self.running:
                # Generate mock real-time events for testing
                await self._generate_mock_events(server)
                await asyncio.sleep(0.5)  # 2 events per second per server
                
        except asyncio.CancelledError:
            logger.info(f"Data producer for {server.server_id} cancelled")
        except Exception as e:
            logger.error(f"Error in data producer for {server.server_id}: {e}")

    async def _generate_mock_events(self, server) -> None:
        """Generate mock real-time events for testing."""
        import random
        
        # Generate different types of events based on server capabilities
        for capability in server.capabilities:
            if not capability.real_time:
                continue
            
            if capability.name == 'arbitrage_memory':
                # Generate arbitrage opportunity events
                if random.random() < 0.3:  # 30% chance
                    event = StreamEvent(
                        event_id=f"arb_{self.sequence_counter}",
                        stream_type=StreamType.ARBITRAGE_OPPORTUNITIES,
                        source_server=server.server_id,
                        data={
                            'pair': random.choice(['ETH/USDC', 'USDT/USDC', 'BTC/USDC']),
                            'buy_dex': random.choice(['uniswap_v3', 'sushiswap']),
                            'sell_dex': random.choice(['aerodrome', 'camelot']),
                            'profit_percentage': round(random.uniform(0.1, 2.0), 3),
                            'confidence': round(random.uniform(0.6, 0.95), 3)
                        },
                        timestamp=datetime.now(),
                        priority=EventPriority.HIGH,
                        sequence_number=self.sequence_counter
                    )
                    await self._emit_event(event)
            
            elif capability.name == 'exchange_data':
                # Generate price update events
                event = StreamEvent(
                    event_id=f"price_{self.sequence_counter}",
                    stream_type=StreamType.PRICE_UPDATES,
                    source_server=server.server_id,
                    data={
                        'pair': 'ETH/USDC',
                        'price': 2565.0 + random.uniform(-10, 10),
                        'volume_24h': random.uniform(1000000, 5000000),
                        'change_24h': random.uniform(-5, 5)
                    },
                    timestamp=datetime.now(),
                    priority=EventPriority.NORMAL,
                    sequence_number=self.sequence_counter
                )
                await self._emit_event(event)
        
        self.sequence_counter += 1

    async def _emit_event(self, event: StreamEvent) -> None:
        """Emit an event to the pipeline."""
        try:
            # Check for backpressure
            queue_usage = self.event_queue.qsize() / self.max_queue_size
            if queue_usage > self.backpressure_threshold:
                self.stream_metrics[event.stream_type].backpressure_events += 1
                logger.warning(f"Backpressure detected: queue {queue_usage:.1%} full")
                return
            
            # Add to queue
            await self.event_queue.put(event)
            
            # Update metrics
            metrics = self.stream_metrics[event.stream_type]
            metrics.events_processed += 1
            metrics.last_event_time = event.timestamp
            
        except asyncio.QueueFull:
            logger.warning(f"Event queue full, dropping event {event.event_id}")
            self.stream_metrics[event.stream_type].error_count += 1

    async def _pipeline_processor(self) -> None:
        """Main pipeline processor that handles events."""
        logger.info("Pipeline processor started")
        
        try:
            while self.running:
                # Process events in batches
                events = []
                
                # Collect batch of events
                try:
                    # Get first event (blocking)
                    event = await asyncio.wait_for(
                        self.event_queue.get(), 
                        timeout=self.flush_interval
                    )
                    events.append(event)
                    
                    # Get additional events (non-blocking)
                    for _ in range(self.batch_size - 1):
                        try:
                            event = self.event_queue.get_nowait()
                            events.append(event)
                        except asyncio.QueueEmpty:
                            break
                            
                except asyncio.TimeoutError:
                    # No events received, continue
                    continue
                
                # Process the batch
                if events:
                    await self._process_event_batch(events)
                    
        except asyncio.CancelledError:
            logger.info("Pipeline processor cancelled")
        except Exception as e:
            logger.error(f"Error in pipeline processor: {e}")

    async def _process_event_batch(self, events: List[StreamEvent]) -> None:
        """Process a batch of events."""
        # Group events by type for efficient processing
        events_by_type = defaultdict(list)
        for event in events:
            events_by_type[event.stream_type].append(event)
        
        # Process each type
        for stream_type, type_events in events_by_type.items():
            try:
                # Use specific processor if available
                if stream_type in self.stream_processors:
                    await self.stream_processors[stream_type](type_events)
                else:
                    await self._process_generic_events(type_events)
                
                # Notify subscribers
                await self._notify_subscribers(type_events)
                
                # Store in history
                self.event_history.extend(type_events)
                
            except Exception as e:
                logger.error(f"Error processing {stream_type.value} events: {e}")
                for event in type_events:
                    self.stream_metrics[event.stream_type].error_count += 1

    async def _process_price_updates(self, events: List[StreamEvent]) -> None:
        """Process price update events."""
        logger.debug(f"Processing {len(events)} price update events")
        
        # Group by trading pair
        pairs_data = defaultdict(list)
        for event in events:
            pair = event.data.get('pair')
            if pair:
                pairs_data[pair].append(event)
        
        # Detect significant price movements
        for pair, pair_events in pairs_data.items():
            if len(pair_events) > 1:
                prices = [e.data.get('price', 0) for e in pair_events]
                price_change = (max(prices) - min(prices)) / min(prices) * 100
                
                if price_change > 1.0:  # 1% change threshold
                    logger.info(f"Significant price movement in {pair}: {price_change:.2f}%")

    async def _process_arbitrage_opportunities(self, events: List[StreamEvent]) -> None:
        """Process arbitrage opportunity events."""
        logger.debug(f"Processing {len(events)} arbitrage opportunity events")
        
        high_confidence_opportunities = [
            event for event in events 
            if event.data.get('confidence', 0) > 0.8
        ]
        
        if high_confidence_opportunities:
            logger.info(f"Found {len(high_confidence_opportunities)} high-confidence arbitrage opportunities")
            
            # Could trigger immediate analysis or execution here
            for event in high_confidence_opportunities:
                logger.info(f"High-confidence opportunity: {event.data}")

    async def _process_market_conditions(self, events: List[StreamEvent]) -> None:
        """Process market condition events."""
        logger.debug(f"Processing {len(events)} market condition events")

    async def _process_trade_executions(self, events: List[StreamEvent]) -> None:
        """Process trade execution events."""
        logger.debug(f"Processing {len(events)} trade execution events")

    async def _process_generic_events(self, events: List[StreamEvent]) -> None:
        """Process generic events."""
        logger.debug(f"Processing {len(events)} generic events")

    async def _notify_subscribers(self, events: List[StreamEvent]) -> None:
        """Notify subscribers of events."""
        for event in events:
            for subscription in self.subscriptions.values():
                if not subscription.active:
                    continue
                
                if event.stream_type in subscription.stream_types:
                    # Check filters
                    if self._event_matches_filters(event, subscription.filters):
                        try:
                            # Call subscriber callback
                            if asyncio.iscoroutinefunction(subscription.callback):
                                await subscription.callback(event)
                            else:
                                subscription.callback(event)
                            
                            subscription.last_event = event.timestamp
                            subscription.event_count += 1
                            
                        except Exception as e:
                            logger.error(f"Error in subscriber callback: {e}")

    def _event_matches_filters(self, event: StreamEvent, filters: Dict[str, Any]) -> bool:
        """Check if event matches subscription filters."""
        for filter_key, filter_value in filters.items():
            event_value = event.data.get(filter_key)
            if event_value != filter_value:
                return False
        return True

    def subscribe(self, stream_types: List[StreamType], 
                 callback: Callable[[StreamEvent], None],
                 filters: Dict[str, Any] = None) -> str:
        """Subscribe to stream events."""
        subscription_id = f"sub_{len(self.subscriptions)}_{datetime.now().timestamp()}"
        
        subscription = StreamSubscription(
            subscription_id=subscription_id,
            stream_types=stream_types,
            callback=callback,
            filters=filters or {}
        )
        
        self.subscriptions[subscription_id] = subscription
        logger.info(f"Created subscription {subscription_id} for {[st.value for st in stream_types]}")
        
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from stream events."""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            logger.info(f"Removed subscription {subscription_id}")
            return True
        return False

    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get pipeline performance metrics."""
        total_events = sum(m.events_processed for m in self.stream_metrics.values())
        total_errors = sum(m.error_count for m in self.stream_metrics.values())
        
        return {
            'running': self.running,
            'total_events_processed': total_events,
            'total_errors': total_errors,
            'queue_size': self.event_queue.qsize(),
            'queue_usage': self.event_queue.qsize() / self.max_queue_size,
            'active_subscriptions': len([s for s in self.subscriptions.values() if s.active]),
            'active_producers': len(self.producer_tasks),
            'stream_metrics': {
                stream_type.value: {
                    'events_processed': metrics.events_processed,
                    'error_count': metrics.error_count,
                    'backpressure_events': metrics.backpressure_events,
                    'last_event_time': metrics.last_event_time.isoformat() if metrics.last_event_time else None
                }
                for stream_type, metrics in self.stream_metrics.items()
            }
        }

    async def get_recent_events(self, stream_type: StreamType = None, 
                              limit: int = 10) -> List[StreamEvent]:
        """Get recent events from history."""
        events = list(self.event_history)
        
        if stream_type:
            events = [e for e in events if e.stream_type == stream_type]
        
        # Sort by timestamp (newest first) and limit
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]
