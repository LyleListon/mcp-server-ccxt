"""
Load Balancer - Work Distribution and Load Management for MayArbi System

Manages work distribution across system components, implements load balancing
algorithms, monitors component capacity, and provides dynamic workload
redistribution for optimal system performance.
"""

import asyncio
import logging
import time
import random
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import statistics
from collections import deque, defaultdict
import heapq

logger = logging.getLogger(__name__)


class LoadBalancingAlgorithm(Enum):
    """Load balancing algorithms."""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    RESOURCE_BASED = "resource_based"
    PERFORMANCE_BASED = "performance_based"
    ADAPTIVE = "adaptive"


class WorkloadType(Enum):
    """Types of workloads."""
    ARBITRAGE_OPPORTUNITY = "arbitrage_opportunity"
    PRICE_UPDATE = "price_update"
    BRIDGE_MONITORING = "bridge_monitoring"
    MEV_DETECTION = "mev_detection"
    WALLET_OPERATION = "wallet_operation"
    MEMORY_OPERATION = "memory_operation"
    HEALTH_CHECK = "health_check"
    GENERAL = "general"


class ComponentStatus(Enum):
    """Component status for load balancing."""
    AVAILABLE = "available"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    MAINTENANCE = "maintenance"
    FAILED = "failed"


class LoadPriority(Enum):
    """Load priority levels."""
    CRITICAL = 10    # Trading operations
    HIGH = 8        # Price feeds, MEV
    NORMAL = 5      # General operations
    LOW = 2         # Background tasks
    MINIMAL = 1     # Maintenance


@dataclass
class WorkloadRequest:
    """Represents a workload request to be distributed."""
    request_id: str
    workload_type: WorkloadType
    priority: LoadPriority
    estimated_duration_ms: float
    resource_requirements: Dict[str, float]  # CPU, memory, network, storage
    preferred_components: List[str] = field(default_factory=list)
    avoid_components: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ComponentCapacity:
    """Component capacity and load information."""
    component: str
    
    # Capacity limits
    max_concurrent_tasks: int = 10
    max_cpu_utilization: float = 85.0
    max_memory_utilization: float = 90.0
    max_network_utilization: float = 80.0
    max_storage_utilization: float = 85.0
    
    # Current load
    current_tasks: int = 0
    current_cpu_utilization: float = 0.0
    current_memory_utilization: float = 0.0
    current_network_utilization: float = 0.0
    current_storage_utilization: float = 0.0
    
    # Performance metrics
    average_response_time_ms: float = 0.0
    success_rate: float = 100.0
    throughput_per_second: float = 0.0
    
    # Load balancing weights
    weight: float = 1.0
    priority_multiplier: float = 1.0
    
    # Status
    status: ComponentStatus = ComponentStatus.AVAILABLE
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class LoadBalancingMetrics:
    """Load balancing metrics."""
    component: str
    
    # Request metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    
    # Timing metrics
    average_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    
    # Load metrics
    average_load_percent: float = 0.0
    peak_load_percent: float = 0.0
    load_distribution_score: float = 0.0
    
    # Efficiency metrics
    utilization_efficiency: float = 0.0
    throughput_efficiency: float = 0.0
    
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class LoadBalancerAlert:
    """Load balancer alert."""
    component: str
    alert_type: str
    severity: str
    message: str
    load_percent: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False


@dataclass
class LoadBalancerConfig:
    """Configuration for load balancer."""
    # Monitoring settings
    monitoring_interval: int = 5  # seconds
    metrics_retention_hours: int = 24
    
    # Load balancing settings
    default_algorithm: LoadBalancingAlgorithm = LoadBalancingAlgorithm.ADAPTIVE
    enable_dynamic_weights: bool = True
    weight_adjustment_factor: float = 0.1
    
    # Capacity thresholds
    overload_threshold: float = 90.0  # percent
    busy_threshold: float = 70.0      # percent
    underload_threshold: float = 30.0  # percent
    
    # Request handling
    max_queue_size: int = 1000
    request_timeout_seconds: int = 30
    retry_delay_seconds: int = 2
    
    # Performance optimization
    enable_predictive_scaling: bool = True
    enable_load_shedding: bool = True
    load_shedding_threshold: float = 95.0
    
    # Health checking
    health_check_interval: int = 10  # seconds
    unhealthy_threshold: int = 3     # consecutive failures
    
    # Alert settings
    alert_cooldown_minutes: int = 5
    max_alerts_per_hour: int = 20


class LoadBalancer:
    """
    Load Balancer - Work distribution and load management.
    
    Manages work distribution across system components using various
    load balancing algorithms and provides dynamic workload redistribution.
    """
    
    def __init__(self, config: Optional[LoadBalancerConfig] = None):
        self.config = config or LoadBalancerConfig()
        self.running = False
        
        # Component management
        self.component_capacities: Dict[str, ComponentCapacity] = {}
        self.component_metrics: Dict[str, LoadBalancingMetrics] = {}
        self.component_health: Dict[str, bool] = {}
        
        # Load balancing
        self.current_algorithm = self.config.default_algorithm
        self.round_robin_index: Dict[WorkloadType, int] = defaultdict(int)
        self.weighted_round_robin_state: Dict[WorkloadType, Dict[str, int]] = defaultdict(dict)
        
        # Request management
        self.request_queue: asyncio.Queue = asyncio.Queue(maxsize=self.config.max_queue_size)
        self.active_requests: Dict[str, WorkloadRequest] = {}
        self.completed_requests: deque = deque(maxlen=10000)
        
        # Performance tracking
        self.load_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.response_time_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.algorithm_performance: Dict[LoadBalancingAlgorithm, Dict[str, float]] = defaultdict(dict)
        
        # Alerts
        self.active_alerts: Dict[str, LoadBalancerAlert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        
        # Monitoring tasks
        self.monitoring_tasks: List[asyncio.Task] = []
        
        # State persistence
        self.state_file = Path("data/load_balancer_state.json")
        self.state_file.parent.mkdir(exist_ok=True)
        
        # Initialize component capacities
        self._initialize_component_capacities()
        
        logger.info("⚖️ Load Balancer initialized")
    
    def _initialize_component_capacities(self):
        """Initialize component capacities for system components."""
        default_capacities = {
            "arbitrage_engine": ComponentCapacity(
                component="arbitrage_engine",
                max_concurrent_tasks=20,
                max_cpu_utilization=90.0,
                max_memory_utilization=85.0,
                max_network_utilization=85.0,
                max_storage_utilization=80.0,
                weight=3.0,  # High weight for critical component
                priority_multiplier=1.5,
                status=ComponentStatus.AVAILABLE
            ),
            "bridge_monitor": ComponentCapacity(
                component="bridge_monitor",
                max_concurrent_tasks=15,
                max_cpu_utilization=70.0,
                max_memory_utilization=80.0,
                max_network_utilization=85.0,
                max_storage_utilization=60.0,
                weight=2.0,
                priority_multiplier=1.2,
                status=ComponentStatus.AVAILABLE
            ),
            "cross_chain_mev": ComponentCapacity(
                component="cross_chain_mev",
                max_concurrent_tasks=12,
                max_cpu_utilization=85.0,
                max_memory_utilization=85.0,
                max_network_utilization=90.0,
                max_storage_utilization=75.0,
                weight=2.5,
                priority_multiplier=1.3,
                status=ComponentStatus.AVAILABLE
            ),
            "price_feeds": ComponentCapacity(
                component="price_feeds",
                max_concurrent_tasks=25,
                max_cpu_utilization=80.0,
                max_memory_utilization=90.0,
                max_network_utilization=95.0,
                max_storage_utilization=90.0,
                weight=2.0,
                priority_multiplier=1.1,
                status=ComponentStatus.AVAILABLE
            ),
            "wallet_manager": ComponentCapacity(
                component="wallet_manager",
                max_concurrent_tasks=8,
                max_cpu_utilization=60.0,
                max_memory_utilization=70.0,
                max_network_utilization=50.0,
                max_storage_utilization=50.0,
                weight=1.5,
                priority_multiplier=2.0,  # High priority for security
                status=ComponentStatus.AVAILABLE
            ),
            "memory_system": ComponentCapacity(
                component="memory_system",
                max_concurrent_tasks=30,
                max_cpu_utilization=65.0,
                max_memory_utilization=95.0,
                max_network_utilization=60.0,
                max_storage_utilization=95.0,
                weight=1.8,
                priority_multiplier=1.0,
                status=ComponentStatus.AVAILABLE
            ),
            "health_monitor": ComponentCapacity(
                component="health_monitor",
                max_concurrent_tasks=5,
                max_cpu_utilization=40.0,
                max_memory_utilization=50.0,
                max_network_utilization=30.0,
                max_storage_utilization=40.0,
                weight=0.5,
                priority_multiplier=0.8,
                status=ComponentStatus.AVAILABLE
            )
        }
        
        self.component_capacities.update(default_capacities)
        
        # Initialize metrics for each component
        for component in default_capacities:
            self.component_metrics[component] = LoadBalancingMetrics(component=component)
            self.component_health[component] = True
        
        logger.debug(f"Initialized load balancer capacities for {len(default_capacities)} components")

    async def start_load_balancing(self):
        """Start the load balancing system."""
        if self.running:
            logger.warning("Load balancing already running")
            return

        self.running = True
        logger.info("🚀 Starting Load Balancing System")

        # Load previous state
        await self._load_state()

        # Initialize load balancing
        await self._initialize_load_balancing()

        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._load_monitor_loop()),
            asyncio.create_task(self._request_processor_loop()),
            asyncio.create_task(self._health_checker_loop()),
            asyncio.create_task(self._optimization_loop())
        ]

        logger.info("✅ Load Balancing System started")

    async def stop_load_balancing(self):
        """Stop the load balancing system."""
        if not self.running:
            return

        self.running = False
        logger.info("🛑 Stopping Load Balancing System")

        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

        # Save state
        await self._save_state()

        logger.info("✅ Load Balancing System stopped")

    async def _initialize_load_balancing(self):
        """Initialize load balancing system."""
        try:
            # Update component status
            await self._update_component_status()

            # Initialize algorithm performance tracking
            for algorithm in LoadBalancingAlgorithm:
                self.algorithm_performance[algorithm] = {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'average_response_time': 0.0,
                    'load_distribution_score': 0.0
                }

            logger.info("Load balancing system initialized")

        except Exception as e:
            logger.error(f"Error initializing load balancing: {e}")

    async def submit_request(self, request: WorkloadRequest) -> bool:
        """Submit a workload request for load balancing."""
        try:
            # Check queue capacity
            if self.request_queue.qsize() >= self.config.max_queue_size:
                logger.warning(f"Request queue full, rejecting request {request.request_id}")
                return False

            # Add to queue
            await self.request_queue.put(request)
            self.active_requests[request.request_id] = request

            logger.debug(f"Request {request.request_id} submitted for load balancing")
            return True

        except Exception as e:
            logger.error(f"Error submitting request {request.request_id}: {e}")
            return False

    async def get_load_balancing_metrics(self) -> Dict[str, Any]:
        """Get current load balancing metrics."""
        try:
            # Update component loads
            await self._update_component_loads()

            # Component metrics
            component_metrics = {}
            for component, capacity in self.component_capacities.items():
                metrics = self.component_metrics.get(component)
                if metrics:
                    load_percent = (capacity.current_tasks / capacity.max_concurrent_tasks) * 100

                    component_metrics[component] = {
                        'status': capacity.status.value,
                        'current_load': {
                            'tasks': capacity.current_tasks,
                            'max_tasks': capacity.max_concurrent_tasks,
                            'load_percent': load_percent,
                            'cpu_utilization': capacity.current_cpu_utilization,
                            'memory_utilization': capacity.current_memory_utilization,
                            'network_utilization': capacity.current_network_utilization,
                            'storage_utilization': capacity.current_storage_utilization
                        },
                        'performance': {
                            'average_response_time_ms': metrics.average_response_time_ms,
                            'success_rate': (metrics.successful_requests / max(metrics.total_requests, 1)) * 100,
                            'throughput_per_second': metrics.throughput_efficiency,
                            'utilization_efficiency': metrics.utilization_efficiency
                        },
                        'requests': {
                            'total': metrics.total_requests,
                            'successful': metrics.successful_requests,
                            'failed': metrics.failed_requests,
                            'rejected': metrics.rejected_requests
                        },
                        'weight': capacity.weight,
                        'health': self.component_health.get(component, False)
                    }

            # System-wide metrics
            total_requests = sum(m.total_requests for m in self.component_metrics.values())
            total_successful = sum(m.successful_requests for m in self.component_metrics.values())
            total_failed = sum(m.failed_requests for m in self.component_metrics.values())

            # Load distribution analysis
            load_distribution_score = await self._calculate_load_distribution_score()

            return {
                'timestamp': datetime.now().isoformat(),
                'system_metrics': {
                    'current_algorithm': self.current_algorithm.value,
                    'total_requests': total_requests,
                    'success_rate': (total_successful / max(total_requests, 1)) * 100,
                    'failure_rate': (total_failed / max(total_requests, 1)) * 100,
                    'queue_size': self.request_queue.qsize(),
                    'active_requests': len(self.active_requests),
                    'load_distribution_score': load_distribution_score,
                    'healthy_components': sum(1 for h in self.component_health.values() if h),
                    'total_components': len(self.component_capacities)
                },
                'component_metrics': component_metrics,
                'algorithm_performance': {
                    alg.value: perf for alg, perf in self.algorithm_performance.items()
                },
                'active_alerts': len([a for a in self.active_alerts.values() if not a.resolved])
            }

        except Exception as e:
            logger.error(f"Error getting load balancing metrics: {e}")
            return {}

    async def _update_component_loads(self):
        """Update component load information."""
        try:
            for component, capacity in self.component_capacities.items():
                # In a real implementation, this would query actual component status
                # For now, we'll simulate based on request history

                # Update current tasks (simulated)
                recent_requests = [r for r in self.completed_requests
                                 if r.get('component') == component and
                                 datetime.now() - datetime.fromisoformat(r.get('timestamp', '2024-01-01')) < timedelta(seconds=30)]

                capacity.current_tasks = len(recent_requests)

                # Update resource utilization (simulated based on load)
                load_factor = capacity.current_tasks / max(capacity.max_concurrent_tasks, 1)
                capacity.current_cpu_utilization = min(load_factor * capacity.max_cpu_utilization, 100.0)
                capacity.current_memory_utilization = min(load_factor * capacity.max_memory_utilization, 100.0)
                capacity.current_network_utilization = min(load_factor * capacity.max_network_utilization, 100.0)
                capacity.current_storage_utilization = min(load_factor * capacity.max_storage_utilization, 100.0)

                # Update status based on load
                load_percent = (capacity.current_tasks / capacity.max_concurrent_tasks) * 100
                if load_percent >= self.config.overload_threshold:
                    capacity.status = ComponentStatus.OVERLOADED
                elif load_percent >= self.config.busy_threshold:
                    capacity.status = ComponentStatus.BUSY
                else:
                    capacity.status = ComponentStatus.AVAILABLE

                capacity.last_updated = datetime.now()

                # Store load history
                self.load_history[component].append({
                    'timestamp': datetime.now(),
                    'load_percent': load_percent,
                    'tasks': capacity.current_tasks
                })

        except Exception as e:
            logger.error(f"Error updating component loads: {e}")

    async def _calculate_load_distribution_score(self) -> float:
        """Calculate load distribution score (0-100, higher is better)."""
        try:
            if not self.component_capacities:
                return 0.0

            # Get load percentages for all components
            load_percentages = []
            for capacity in self.component_capacities.values():
                if capacity.status != ComponentStatus.FAILED:
                    load_percent = (capacity.current_tasks / max(capacity.max_concurrent_tasks, 1)) * 100
                    load_percentages.append(load_percent)

            if not load_percentages:
                return 0.0

            # Calculate standard deviation (lower is better for distribution)
            if len(load_percentages) > 1:
                std_dev = statistics.stdev(load_percentages)
                # Convert to score (0-100, where 0 std_dev = 100 score)
                max_possible_std_dev = 50.0  # Reasonable maximum
                distribution_score = max(0, 100 - (std_dev / max_possible_std_dev) * 100)
            else:
                distribution_score = 100.0

            return distribution_score

        except Exception as e:
            logger.error(f"Error calculating load distribution score: {e}")
            return 0.0

    async def select_component(self, request: WorkloadRequest) -> Optional[str]:
        """Select the best component for a workload request."""
        try:
            # Get available components
            available_components = [
                comp for comp, capacity in self.component_capacities.items()
                if capacity.status in [ComponentStatus.AVAILABLE, ComponentStatus.BUSY] and
                self.component_health.get(comp, False) and
                comp not in request.avoid_components
            ]

            if not available_components:
                logger.warning(f"No available components for request {request.request_id}")
                return None

            # Filter by preferred components if specified
            if request.preferred_components:
                preferred_available = [comp for comp in available_components if comp in request.preferred_components]
                if preferred_available:
                    available_components = preferred_available

            # Apply load balancing algorithm
            if self.current_algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
                return await self._round_robin_selection(request.workload_type, available_components)
            elif self.current_algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
                return await self._weighted_round_robin_selection(request.workload_type, available_components)
            elif self.current_algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
                return await self._least_connections_selection(available_components)
            elif self.current_algorithm == LoadBalancingAlgorithm.LEAST_RESPONSE_TIME:
                return await self._least_response_time_selection(available_components)
            elif self.current_algorithm == LoadBalancingAlgorithm.RESOURCE_BASED:
                return await self._resource_based_selection(request, available_components)
            elif self.current_algorithm == LoadBalancingAlgorithm.PERFORMANCE_BASED:
                return await self._performance_based_selection(available_components)
            else:  # ADAPTIVE
                return await self._adaptive_selection(request, available_components)

        except Exception as e:
            logger.error(f"Error selecting component for request {request.request_id}: {e}")
            return None

    async def _round_robin_selection(self, workload_type: WorkloadType, components: List[str]) -> str:
        """Round robin component selection."""
        if not components:
            return None

        index = self.round_robin_index[workload_type] % len(components)
        self.round_robin_index[workload_type] = (index + 1) % len(components)
        return components[index]

    async def _weighted_round_robin_selection(self, workload_type: WorkloadType, components: List[str]) -> str:
        """Weighted round robin component selection."""
        if not components:
            return None

        # Initialize weights if not exists
        if workload_type not in self.weighted_round_robin_state:
            self.weighted_round_robin_state[workload_type] = {}

        state = self.weighted_round_robin_state[workload_type]

        # Calculate current weights
        for component in components:
            if component not in state:
                capacity = self.component_capacities.get(component)
                state[component] = int(capacity.weight * 10) if capacity else 10

        # Find component with highest current weight
        selected_component = max(components, key=lambda c: state.get(c, 0))

        # Decrease selected component's weight and reset others
        capacity = self.component_capacities.get(selected_component)
        original_weight = int(capacity.weight * 10) if capacity else 10

        state[selected_component] -= 1
        if state[selected_component] <= 0:
            # Reset all weights
            for component in components:
                capacity = self.component_capacities.get(component)
                state[component] = int(capacity.weight * 10) if capacity else 10

        return selected_component

    async def _least_connections_selection(self, components: List[str]) -> str:
        """Least connections component selection."""
        if not components:
            return None

        # Select component with least current tasks
        return min(components, key=lambda c: self.component_capacities.get(c, ComponentCapacity()).current_tasks)

    async def _least_response_time_selection(self, components: List[str]) -> str:
        """Least response time component selection."""
        if not components:
            return None

        # Select component with lowest average response time
        return min(components, key=lambda c: self.component_capacities.get(c, ComponentCapacity()).average_response_time_ms)

    async def _resource_based_selection(self, request: WorkloadRequest, components: List[str]) -> str:
        """Resource-based component selection."""
        if not components:
            return None

        # Score components based on available resources vs requirements
        component_scores = {}

        for component in components:
            capacity = self.component_capacities.get(component)
            if not capacity:
                continue

            # Calculate resource availability score
            cpu_available = max(0, capacity.max_cpu_utilization - capacity.current_cpu_utilization)
            memory_available = max(0, capacity.max_memory_utilization - capacity.current_memory_utilization)
            network_available = max(0, capacity.max_network_utilization - capacity.current_network_utilization)
            storage_available = max(0, capacity.max_storage_utilization - capacity.current_storage_utilization)

            # Weight by request requirements
            cpu_req = request.resource_requirements.get('cpu', 10.0)
            memory_req = request.resource_requirements.get('memory', 10.0)
            network_req = request.resource_requirements.get('network', 10.0)
            storage_req = request.resource_requirements.get('storage', 10.0)

            # Calculate fit score (higher is better)
            cpu_score = max(0, cpu_available - cpu_req)
            memory_score = max(0, memory_available - memory_req)
            network_score = max(0, network_available - network_req)
            storage_score = max(0, storage_available - storage_req)

            total_score = cpu_score + memory_score + network_score + storage_score
            component_scores[component] = total_score

        if not component_scores:
            return components[0]

        # Return component with highest score
        return max(component_scores.items(), key=lambda x: x[1])[0]

    async def _performance_based_selection(self, components: List[str]) -> str:
        """Performance-based component selection."""
        if not components:
            return None

        # Score components based on performance metrics
        component_scores = {}

        for component in components:
            capacity = self.component_capacities.get(component)
            metrics = self.component_metrics.get(component)

            if not capacity or not metrics:
                component_scores[component] = 0.0
                continue

            # Calculate performance score
            success_rate = (metrics.successful_requests / max(metrics.total_requests, 1)) * 100
            response_time_score = max(0, 1000 - capacity.average_response_time_ms) / 10  # Lower is better
            throughput_score = capacity.throughput_per_second
            load_score = max(0, 100 - (capacity.current_tasks / capacity.max_concurrent_tasks) * 100)

            total_score = (success_rate * 0.3 + response_time_score * 0.3 +
                          throughput_score * 0.2 + load_score * 0.2) * capacity.weight

            component_scores[component] = total_score

        if not component_scores:
            return components[0]

        # Return component with highest performance score
        return max(component_scores.items(), key=lambda x: x[1])[0]

    async def _adaptive_selection(self, request: WorkloadRequest, components: List[str]) -> str:
        """Adaptive component selection combining multiple strategies."""
        if not components:
            return None

        # Use different strategies based on request priority and system state
        if request.priority == LoadPriority.CRITICAL:
            # For critical requests, prioritize performance and availability
            return await self._performance_based_selection(components)
        elif request.priority == LoadPriority.HIGH:
            # For high priority, balance performance and resources
            perf_component = await self._performance_based_selection(components)
            resource_component = await self._resource_based_selection(request, components)

            # Choose based on current system load
            system_load = sum(c.current_tasks for c in self.component_capacities.values())
            total_capacity = sum(c.max_concurrent_tasks for c in self.component_capacities.values())
            load_ratio = system_load / max(total_capacity, 1)

            if load_ratio > 0.7:  # High system load, prioritize resources
                return resource_component
            else:  # Normal load, prioritize performance
                return perf_component
        else:
            # For normal/low priority, use least connections for even distribution
            return await self._least_connections_selection(components)

    # Monitoring loops
    async def _load_monitor_loop(self):
        """Load monitoring loop."""
        while self.running:
            try:
                # Update component loads
                await self._update_component_loads()

                # Check for load balancing alerts
                await self._check_load_balancing_alerts()

                # Update algorithm performance
                await self._update_algorithm_performance()

                await asyncio.sleep(self.config.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in load monitor loop: {e}")
                await asyncio.sleep(10)

    async def _request_processor_loop(self):
        """Request processing loop."""
        while self.running:
            try:
                # Process requests from queue
                try:
                    request = await asyncio.wait_for(
                        self.request_queue.get(),
                        timeout=1.0
                    )
                    await self._process_request(request)
                except asyncio.TimeoutError:
                    continue

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in request processor loop: {e}")
                await asyncio.sleep(1)

    async def _health_checker_loop(self):
        """Health checking loop."""
        while self.running:
            try:
                # Check component health
                await self._check_component_health()

                # Update component status
                await self._update_component_status()

                await asyncio.sleep(self.config.health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health checker loop: {e}")
                await asyncio.sleep(30)

    async def _optimization_loop(self):
        """Load balancing optimization loop."""
        while self.running:
            try:
                # Optimize algorithm selection
                if self.config.enable_dynamic_weights:
                    await self._optimize_algorithm_selection()

                # Adjust component weights
                await self._adjust_component_weights()

                # Load shedding if needed
                if self.config.enable_load_shedding:
                    await self._check_load_shedding()

                await asyncio.sleep(60)  # Optimize every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(30)

    async def _process_request(self, request: WorkloadRequest):
        """Process a workload request."""
        try:
            start_time = time.time()

            # Select component
            selected_component = await self.select_component(request)

            if not selected_component:
                # No available component
                metrics = self.component_metrics.get('system', LoadBalancingMetrics(component='system'))
                metrics.rejected_requests += 1

                # Retry if possible
                if request.retry_count < request.max_retries:
                    request.retry_count += 1
                    await asyncio.sleep(self.config.retry_delay_seconds)
                    await self.request_queue.put(request)
                    logger.info(f"Retrying request {request.request_id} (attempt {request.retry_count})")
                else:
                    logger.error(f"Request {request.request_id} failed - no available components")
                    self._complete_request(request, selected_component, False, time.time() - start_time)
                return

            # Update component metrics
            capacity = self.component_capacities.get(selected_component)
            metrics = self.component_metrics.get(selected_component)

            if capacity and metrics:
                capacity.current_tasks += 1
                metrics.total_requests += 1

            # Simulate request processing
            processing_time = request.estimated_duration_ms / 1000.0
            await asyncio.sleep(processing_time)

            # Simulate success/failure
            success_rate = capacity.success_rate if capacity else 95.0
            success = random.random() * 100 < success_rate

            # Complete request
            total_time = time.time() - start_time
            self._complete_request(request, selected_component, success, total_time)

            # Update component load
            if capacity:
                capacity.current_tasks = max(0, capacity.current_tasks - 1)

        except Exception as e:
            logger.error(f"Error processing request {request.request_id}: {e}")
            self._complete_request(request, None, False, 0)

    def _complete_request(self, request: WorkloadRequest, component: Optional[str], success: bool, response_time: float):
        """Complete a request and update metrics."""
        try:
            # Remove from active requests
            if request.request_id in self.active_requests:
                del self.active_requests[request.request_id]

            # Update component metrics
            if component and component in self.component_metrics:
                metrics = self.component_metrics[component]

                if success:
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1

                # Update response time (exponential moving average)
                if metrics.average_response_time_ms == 0:
                    metrics.average_response_time_ms = response_time * 1000
                else:
                    alpha = 0.1
                    metrics.average_response_time_ms = (alpha * response_time * 1000) + ((1 - alpha) * metrics.average_response_time_ms)

                # Update min/max response times
                response_time_ms = response_time * 1000
                if metrics.min_response_time_ms == 0 or response_time_ms < metrics.min_response_time_ms:
                    metrics.min_response_time_ms = response_time_ms
                if response_time_ms > metrics.max_response_time_ms:
                    metrics.max_response_time_ms = response_time_ms

                metrics.last_updated = datetime.now()

                # Store response time history
                self.response_time_history[component].append({
                    'timestamp': datetime.now(),
                    'response_time_ms': response_time_ms,
                    'success': success
                })

            # Add to completed requests
            self.completed_requests.append({
                'request_id': request.request_id,
                'component': component,
                'success': success,
                'response_time_ms': response_time * 1000,
                'timestamp': datetime.now().isoformat(),
                'workload_type': request.workload_type.value,
                'priority': request.priority.value
            })

            logger.debug(f"Request {request.request_id} completed: component={component}, success={success}, time={response_time:.3f}s")

        except Exception as e:
            logger.error(f"Error completing request {request.request_id}: {e}")

    # Placeholder methods for monitoring loops
    async def _check_load_balancing_alerts(self):
        """Check for load balancing alerts."""
        try:
            for component, capacity in self.component_capacities.items():
                load_percent = (capacity.current_tasks / capacity.max_concurrent_tasks) * 100

                if load_percent >= self.config.overload_threshold:
                    await self._create_load_balancing_alert(
                        component, "overload", "critical",
                        f"Component overloaded: {load_percent:.1f}% load",
                        load_percent
                    )
                elif load_percent >= self.config.busy_threshold:
                    await self._create_load_balancing_alert(
                        component, "high_load", "warning",
                        f"Component under high load: {load_percent:.1f}%",
                        load_percent
                    )
        except Exception as e:
            logger.error(f"Error checking load balancing alerts: {e}")

    async def _create_load_balancing_alert(self, component: str, alert_type: str, severity: str, message: str, load_percent: float):
        """Create a load balancing alert."""
        try:
            alert_key = f"{component}_{alert_type}"

            # Check cooldown
            if alert_key in self.active_alerts:
                last_alert = self.active_alerts[alert_key]
                if not last_alert.resolved:
                    time_since = datetime.now() - last_alert.timestamp
                    if time_since.total_seconds() < (self.config.alert_cooldown_minutes * 60):
                        return

            # Create new alert
            alert = LoadBalancerAlert(
                component=component,
                alert_type=alert_type,
                severity=severity,
                message=message,
                load_percent=load_percent
            )

            self.active_alerts[alert_key] = alert
            self.alert_history.append(alert)

            logger.warning(f"Load Balancer Alert [{severity.upper()}] {component}: {message}")

        except Exception as e:
            logger.error(f"Error creating load balancing alert: {e}")

    async def _update_algorithm_performance(self):
        """Update algorithm performance metrics."""
        try:
            # Track current algorithm performance
            current_perf = self.algorithm_performance[self.current_algorithm]

            # Calculate recent performance
            recent_requests = [r for r in self.completed_requests if
                             datetime.now() - datetime.fromisoformat(r['timestamp']) < timedelta(minutes=5)]

            if recent_requests:
                total_requests = len(recent_requests)
                successful_requests = sum(1 for r in recent_requests if r['success'])
                avg_response_time = statistics.mean([r['response_time_ms'] for r in recent_requests])

                current_perf['total_requests'] += total_requests
                current_perf['successful_requests'] += successful_requests
                current_perf['average_response_time'] = avg_response_time
                current_perf['load_distribution_score'] = await self._calculate_load_distribution_score()

        except Exception as e:
            logger.error(f"Error updating algorithm performance: {e}")

    # Placeholder methods for optimization and health checking
    async def _check_component_health(self):
        """Check component health."""
        try:
            for component in self.component_capacities:
                # Simulate health check based on recent performance
                recent_requests = [r for r in self.completed_requests
                                 if r.get('component') == component and
                                 datetime.now() - datetime.fromisoformat(r.get('timestamp', '2024-01-01')) < timedelta(minutes=5)]

                if recent_requests:
                    success_rate = sum(1 for r in recent_requests if r['success']) / len(recent_requests)
                    self.component_health[component] = success_rate > 0.8
                else:
                    # No recent requests, assume healthy
                    self.component_health[component] = True
        except Exception as e:
            logger.error(f"Error checking component health: {e}")

    async def _update_component_status(self):
        """Update component status."""
        try:
            for component, capacity in self.component_capacities.items():
                if not self.component_health.get(component, True):
                    capacity.status = ComponentStatus.FAILED
                else:
                    # Status is updated in _update_component_loads based on load
                    pass
        except Exception as e:
            logger.error(f"Error updating component status: {e}")

    async def _optimize_algorithm_selection(self):
        """Optimize load balancing algorithm selection."""
        try:
            # Compare algorithm performance and switch if needed
            best_algorithm = self.current_algorithm
            best_score = 0.0

            for algorithm, perf in self.algorithm_performance.items():
                if perf['total_requests'] > 10:  # Minimum requests for comparison
                    success_rate = (perf['successful_requests'] / perf['total_requests']) * 100
                    response_time_score = max(0, 1000 - perf['average_response_time']) / 10
                    distribution_score = perf['load_distribution_score']

                    total_score = (success_rate * 0.4 + response_time_score * 0.3 + distribution_score * 0.3)

                    if total_score > best_score:
                        best_score = total_score
                        best_algorithm = algorithm

            if best_algorithm != self.current_algorithm:
                logger.info(f"Switching load balancing algorithm from {self.current_algorithm.value} to {best_algorithm.value}")
                self.current_algorithm = best_algorithm

        except Exception as e:
            logger.error(f"Error optimizing algorithm selection: {e}")

    async def _adjust_component_weights(self):
        """Adjust component weights based on performance."""
        try:
            if not self.config.enable_dynamic_weights:
                return

            for component, capacity in self.component_capacities.items():
                metrics = self.component_metrics.get(component)
                if not metrics or metrics.total_requests < 5:
                    continue

                # Calculate performance score
                success_rate = (metrics.successful_requests / metrics.total_requests) * 100
                response_time_score = max(0, 1000 - metrics.average_response_time_ms) / 10

                performance_score = (success_rate + response_time_score) / 2

                # Adjust weight based on performance
                if performance_score > 80:
                    # Good performance, increase weight
                    capacity.weight = min(5.0, capacity.weight + self.config.weight_adjustment_factor)
                elif performance_score < 60:
                    # Poor performance, decrease weight
                    capacity.weight = max(0.1, capacity.weight - self.config.weight_adjustment_factor)

        except Exception as e:
            logger.error(f"Error adjusting component weights: {e}")

    async def _check_load_shedding(self):
        """Check if load shedding is needed."""
        try:
            # Calculate system load
            total_load = sum(c.current_tasks for c in self.component_capacities.values())
            total_capacity = sum(c.max_concurrent_tasks for c in self.component_capacities.values())

            if total_capacity > 0:
                system_load_percent = (total_load / total_capacity) * 100

                if system_load_percent > self.config.load_shedding_threshold:
                    # Implement load shedding - reject low priority requests
                    queue_items = []
                    while not self.request_queue.empty():
                        try:
                            item = self.request_queue.get_nowait()
                            if item.priority.value >= LoadPriority.NORMAL.value:
                                queue_items.append(item)
                            else:
                                logger.info(f"Load shedding: dropping low priority request {item.request_id}")
                        except asyncio.QueueEmpty:
                            break

                    # Put back high priority requests
                    for item in queue_items:
                        try:
                            self.request_queue.put_nowait(item)
                        except asyncio.QueueFull:
                            break

        except Exception as e:
            logger.error(f"Error checking load shedding: {e}")

    async def _load_state(self):
        """Load previous state from disk."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)

                # Restore algorithm performance
                if 'algorithm_performance' in state:
                    for alg_name, perf in state['algorithm_performance'].items():
                        try:
                            algorithm = LoadBalancingAlgorithm(alg_name)
                            self.algorithm_performance[algorithm].update(perf)
                        except ValueError:
                            continue

                # Restore component weights
                if 'component_weights' in state:
                    for component, weight in state['component_weights'].items():
                        if component in self.component_capacities:
                            self.component_capacities[component].weight = weight

                logger.info("Load balancer state loaded")

        except Exception as e:
            logger.error(f"Error loading state: {e}")

    async def _save_state(self):
        """Save current state to disk."""
        try:
            state = {
                'algorithm_performance': {
                    alg.value: perf for alg, perf in self.algorithm_performance.items()
                },
                'component_weights': {
                    component: capacity.weight
                    for component, capacity in self.component_capacities.items()
                },
                'current_algorithm': self.current_algorithm.value,
                'completed_requests_count': len(self.completed_requests)
            }

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

            logger.debug("Load balancer state saved")

        except Exception as e:
            logger.error(f"Error saving state: {e}")

    async def get_load_balancer_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive load balancer data for dashboard display."""
        try:
            metrics = await self.get_load_balancing_metrics()

            # Recent request statistics
            recent_requests = [r for r in self.completed_requests
                             if datetime.now() - datetime.fromisoformat(r['timestamp']) < timedelta(minutes=10)]

            request_stats = {
                'total_recent': len(recent_requests),
                'success_rate': (sum(1 for r in recent_requests if r['success']) / max(len(recent_requests), 1)) * 100,
                'avg_response_time': statistics.mean([r['response_time_ms'] for r in recent_requests]) if recent_requests else 0,
                'by_workload_type': {},
                'by_priority': {}
            }

            # Group by workload type and priority
            for workload_type in WorkloadType:
                type_requests = [r for r in recent_requests if r['workload_type'] == workload_type.value]
                request_stats['by_workload_type'][workload_type.value] = len(type_requests)

            for priority in LoadPriority:
                priority_requests = [r for r in recent_requests if r['priority'] == priority.value]
                request_stats['by_priority'][priority.value] = len(priority_requests)

            return {
                'timestamp': datetime.now().isoformat(),
                'system_metrics': metrics.get('system_metrics', {}),
                'component_metrics': metrics.get('component_metrics', {}),
                'algorithm_performance': metrics.get('algorithm_performance', {}),
                'request_statistics': request_stats,
                'active_alerts': len([a for a in self.active_alerts.values() if not a.resolved]),
                'queue_status': {
                    'current_size': self.request_queue.qsize(),
                    'max_size': self.config.max_queue_size,
                    'utilization_percent': (self.request_queue.qsize() / self.config.max_queue_size) * 100
                }
            }

        except Exception as e:
            logger.error(f"Error getting load balancer dashboard data: {e}")
            return {}
