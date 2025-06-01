"""
Network Manager - Network Resource Management for MayArbi System

Manages bandwidth allocation, connection pooling, rate limiting, and network
performance optimization across all system components. Coordinates API rate
limits and ensures optimal network resource utilization.
"""

import asyncio
import logging
import time
import aiohttp
import psutil
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import statistics
from collections import deque, defaultdict

logger = logging.getLogger(__name__)


class NetworkPriority(Enum):
    """Network priority levels for components."""
    CRITICAL = 10  # Trading operations
    HIGH = 8      # Price feeds, bridge monitoring
    NORMAL = 5    # General operations
    LOW = 2       # Background tasks
    MINIMAL = 1   # Cleanup, maintenance


class ConnectionType(Enum):
    """Types of network connections."""
    API_CALL = "api_call"
    BLOCKCHAIN_RPC = "blockchain_rpc"
    WEBSOCKET = "websocket"
    HTTP_REQUEST = "http_request"
    DATABASE = "database"


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    ADAPTIVE = "adaptive"


@dataclass
class NetworkAllocation:
    """Network resource allocation for a component."""
    component: str
    
    # Bandwidth limits (Mbps)
    bandwidth_limit_mbps: float = 10.0
    burst_bandwidth_mbps: float = 20.0
    
    # Connection limits
    max_concurrent_connections: int = 50
    max_connections_per_host: int = 10
    connection_timeout_seconds: int = 30
    
    # Rate limiting
    requests_per_second: float = 10.0
    requests_per_minute: float = 600.0
    rate_limit_strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    
    # Priority and optimization
    priority: NetworkPriority = NetworkPriority.NORMAL
    enable_connection_pooling: bool = True
    enable_keep_alive: bool = True
    enable_compression: bool = True
    
    # Monitoring
    track_latency: bool = True
    track_throughput: bool = True
    alert_on_failures: bool = True


@dataclass
class ConnectionMetrics:
    """Metrics for network connections."""
    component: str
    connection_type: ConnectionType
    active_connections: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_latency_ms: float = 0.0
    bandwidth_used_mbps: float = 0.0
    rate_limit_hits: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class NetworkAlert:
    """Network-related alert."""
    component: str
    alert_type: str
    severity: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False


@dataclass
class NetworkConfig:
    """Configuration for network management."""
    # Monitoring settings
    monitoring_interval: int = 10  # seconds
    metrics_retention_hours: int = 24
    
    # Bandwidth thresholds
    bandwidth_warning_threshold: float = 70.0  # percent
    bandwidth_critical_threshold: float = 90.0  # percent
    
    # Connection thresholds
    connection_warning_threshold: float = 80.0  # percent of max
    connection_critical_threshold: float = 95.0  # percent of max
    
    # Rate limiting
    enable_global_rate_limiting: bool = True
    global_requests_per_second: float = 100.0
    rate_limit_burst_factor: float = 2.0
    
    # Connection management
    enable_connection_pooling: bool = True
    connection_pool_size: int = 100
    connection_timeout_seconds: int = 30
    keep_alive_timeout_seconds: int = 60
    
    # Performance optimization
    enable_compression: bool = True
    enable_keep_alive: bool = True
    enable_tcp_nodelay: bool = True
    
    # Retry settings
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    retry_timeout_seconds: int = 60
    
    # Alert settings
    alert_cooldown_minutes: int = 5
    max_alerts_per_hour: int = 15


class NetworkManager:
    """
    Network Manager - Manages network resources and optimization.
    
    Handles bandwidth allocation, connection pooling, rate limiting,
    and network performance optimization for all system components.
    """
    
    def __init__(self, config: Optional[NetworkConfig] = None):
        self.config = config or NetworkConfig()
        self.running = False
        
        # Network tracking
        self.component_allocations: Dict[str, NetworkAllocation] = {}
        self.component_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.connection_metrics: Dict[str, ConnectionMetrics] = {}
        
        # Rate limiting
        self.rate_limiters: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.global_rate_limiter: Dict[str, Any] = {
            'requests': deque(maxlen=1000),
            'last_reset': time.time()
        }
        
        # Connection pools
        self.connection_pools: Dict[str, aiohttp.ClientSession] = {}
        self.active_connections: Dict[str, Set[str]] = defaultdict(set)
        
        # Performance tracking
        self.network_history: deque = deque(maxlen=1000)
        self.latency_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.bandwidth_history: deque = deque(maxlen=1000)
        
        # Alerts
        self.active_alerts: Dict[str, NetworkAlert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        
        # Monitoring tasks
        self.monitoring_tasks: List[asyncio.Task] = []
        
        # State persistence
        self.state_file = Path("data/network_manager_state.json")
        self.state_file.parent.mkdir(exist_ok=True)
        
        # Initialize component allocations
        self._initialize_network_allocations()
        
        logger.info("🌐 Network Manager initialized")
    
    def _initialize_network_allocations(self):
        """Initialize network allocations for system components."""
        default_allocations = {
            "arbitrage_engine": NetworkAllocation(
                component="arbitrage_engine",
                bandwidth_limit_mbps=15.0,
                burst_bandwidth_mbps=30.0,
                max_concurrent_connections=30,
                max_connections_per_host=5,
                requests_per_second=20.0,
                requests_per_minute=1200.0,
                priority=NetworkPriority.CRITICAL,
                rate_limit_strategy=RateLimitStrategy.ADAPTIVE,
                enable_connection_pooling=True,
                track_latency=True
            ),
            "bridge_monitor": NetworkAllocation(
                component="bridge_monitor",
                bandwidth_limit_mbps=8.0,
                burst_bandwidth_mbps=16.0,
                max_concurrent_connections=20,
                max_connections_per_host=4,
                requests_per_second=10.0,
                requests_per_minute=600.0,
                priority=NetworkPriority.HIGH,
                rate_limit_strategy=RateLimitStrategy.SLIDING_WINDOW,
                enable_connection_pooling=True,
                track_latency=True
            ),
            "cross_chain_mev": NetworkAllocation(
                component="cross_chain_mev",
                bandwidth_limit_mbps=12.0,
                burst_bandwidth_mbps=24.0,
                max_concurrent_connections=25,
                max_connections_per_host=5,
                requests_per_second=15.0,
                requests_per_minute=900.0,
                priority=NetworkPriority.HIGH,
                rate_limit_strategy=RateLimitStrategy.TOKEN_BUCKET,
                enable_connection_pooling=True,
                track_latency=True
            ),
            "price_feeds": NetworkAllocation(
                component="price_feeds",
                bandwidth_limit_mbps=10.0,
                burst_bandwidth_mbps=20.0,
                max_concurrent_connections=40,
                max_connections_per_host=8,
                requests_per_second=25.0,
                requests_per_minute=1500.0,
                priority=NetworkPriority.HIGH,
                rate_limit_strategy=RateLimitStrategy.SLIDING_WINDOW,
                enable_connection_pooling=True,
                track_latency=True
            ),
            "wallet_manager": NetworkAllocation(
                component="wallet_manager",
                bandwidth_limit_mbps=5.0,
                burst_bandwidth_mbps=10.0,
                max_concurrent_connections=15,
                max_connections_per_host=3,
                requests_per_second=8.0,
                requests_per_minute=480.0,
                priority=NetworkPriority.CRITICAL,
                rate_limit_strategy=RateLimitStrategy.FIXED_WINDOW,
                enable_connection_pooling=True,
                track_latency=True
            ),
            "memory_system": NetworkAllocation(
                component="memory_system",
                bandwidth_limit_mbps=3.0,
                burst_bandwidth_mbps=6.0,
                max_concurrent_connections=10,
                max_connections_per_host=2,
                requests_per_second=5.0,
                requests_per_minute=300.0,
                priority=NetworkPriority.NORMAL,
                rate_limit_strategy=RateLimitStrategy.FIXED_WINDOW,
                enable_connection_pooling=True,
                track_latency=False
            ),
            "health_monitor": NetworkAllocation(
                component="health_monitor",
                bandwidth_limit_mbps=2.0,
                burst_bandwidth_mbps=4.0,
                max_concurrent_connections=8,
                max_connections_per_host=2,
                requests_per_second=3.0,
                requests_per_minute=180.0,
                priority=NetworkPriority.LOW,
                rate_limit_strategy=RateLimitStrategy.FIXED_WINDOW,
                enable_connection_pooling=False,
                track_latency=False
            )
        }
        
        self.component_allocations.update(default_allocations)
        logger.debug(f"Initialized network allocations for {len(default_allocations)} components")

    async def start_network_management(self):
        """Start the network management system."""
        if self.running:
            logger.warning("Network management already running")
            return

        self.running = True
        logger.info("🚀 Starting Network Management System")

        # Load previous state
        await self._load_state()

        # Initialize connection pools
        await self._initialize_connection_pools()

        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._network_monitor_loop()),
            asyncio.create_task(self._rate_limiter_loop()),
            asyncio.create_task(self._connection_manager_loop()),
            asyncio.create_task(self._performance_optimizer_loop())
        ]

        logger.info("✅ Network Management System started")

    async def stop_network_management(self):
        """Stop the network management system."""
        if not self.running:
            return

        self.running = False
        logger.info("🛑 Stopping Network Management System")

        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

        # Close connection pools
        await self._close_connection_pools()

        # Save state
        await self._save_state()

        logger.info("✅ Network Management System stopped")

    async def _initialize_connection_pools(self):
        """Initialize connection pools for components."""
        try:
            for component, allocation in self.component_allocations.items():
                if allocation.enable_connection_pooling:
                    # Create connector with appropriate settings
                    connector = aiohttp.TCPConnector(
                        limit=allocation.max_concurrent_connections,
                        limit_per_host=allocation.max_connections_per_host,
                        ttl_dns_cache=300,
                        use_dns_cache=True,
                        keepalive_timeout=self.config.keep_alive_timeout_seconds,
                        enable_cleanup_closed=True
                    )

                    # Create session with timeout
                    timeout = aiohttp.ClientTimeout(
                        total=allocation.connection_timeout_seconds,
                        connect=10,
                        sock_read=30
                    )

                    # Create session
                    session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=timeout,
                        headers={'User-Agent': f'MayArbi-{component}'}
                    )

                    self.connection_pools[component] = session

                    # Initialize metrics
                    self.connection_metrics[component] = ConnectionMetrics(
                        component=component,
                        connection_type=ConnectionType.HTTP_REQUEST
                    )

            logger.info(f"Initialized connection pools for {len(self.connection_pools)} components")

        except Exception as e:
            logger.error(f"Error initializing connection pools: {e}")

    async def _close_connection_pools(self):
        """Close all connection pools."""
        try:
            for component, session in self.connection_pools.items():
                await session.close()

            self.connection_pools.clear()
            logger.info("Closed all connection pools")

        except Exception as e:
            logger.error(f"Error closing connection pools: {e}")

    async def get_network_metrics(self) -> Dict[str, Any]:
        """Get current network metrics."""
        try:
            # System network stats
            net_io = psutil.net_io_counters()
            net_connections = len(psutil.net_connections())

            # Calculate bandwidth usage
            current_time = time.time()
            if hasattr(self, '_last_net_io') and hasattr(self, '_last_net_time'):
                time_delta = current_time - self._last_net_time
                if time_delta > 0:
                    bytes_sent_per_sec = (net_io.bytes_sent - self._last_net_io.bytes_sent) / time_delta
                    bytes_recv_per_sec = (net_io.bytes_recv - self._last_net_io.bytes_recv) / time_delta

                    # Convert to Mbps
                    bandwidth_out_mbps = (bytes_sent_per_sec * 8) / (1024 * 1024)
                    bandwidth_in_mbps = (bytes_recv_per_sec * 8) / (1024 * 1024)
                else:
                    bandwidth_out_mbps = 0
                    bandwidth_in_mbps = 0
            else:
                bandwidth_out_mbps = 0
                bandwidth_in_mbps = 0

            # Store for next calculation
            self._last_net_io = net_io
            self._last_net_time = current_time

            # Component metrics
            component_metrics = {}
            for component, metrics in self.connection_metrics.items():
                component_metrics[component] = {
                    'active_connections': metrics.active_connections,
                    'total_requests': metrics.total_requests,
                    'success_rate': (metrics.successful_requests / max(metrics.total_requests, 1)) * 100,
                    'average_latency_ms': metrics.average_latency_ms,
                    'bandwidth_used_mbps': metrics.bandwidth_used_mbps,
                    'rate_limit_hits': metrics.rate_limit_hits
                }

            return {
                'timestamp': datetime.now().isoformat(),
                'system_network': {
                    'total_connections': net_connections,
                    'bandwidth_out_mbps': bandwidth_out_mbps,
                    'bandwidth_in_mbps': bandwidth_in_mbps,
                    'total_bandwidth_mbps': bandwidth_out_mbps + bandwidth_in_mbps,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'errors_in': net_io.errin,
                    'errors_out': net_io.errout,
                    'drops_in': net_io.dropin,
                    'drops_out': net_io.dropout
                },
                'components': component_metrics,
                'active_alerts': len([a for a in self.active_alerts.values() if not a.resolved]),
                'connection_pools': len(self.connection_pools)
            }

        except Exception as e:
            logger.error(f"Error getting network metrics: {e}")
            return {}

    async def _network_monitor_loop(self):
        """Main network monitoring loop."""
        while self.running:
            try:
                # Get current metrics
                metrics = await self.get_network_metrics()

                # Store metrics history
                self.network_history.append({
                    'timestamp': datetime.now(),
                    'metrics': metrics
                })

                # Check for alerts
                await self._check_network_alerts(metrics)

                # Update component metrics
                await self._update_component_metrics()

                await asyncio.sleep(self.config.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in network monitor loop: {e}")
                await asyncio.sleep(10)

    async def _rate_limiter_loop(self):
        """Rate limiting management loop."""
        while self.running:
            try:
                # Clean up old rate limit data
                await self._cleanup_rate_limiters()

                # Update global rate limiter
                await self._update_global_rate_limiter()

                # Check component rate limits
                await self._check_component_rate_limits()

                await asyncio.sleep(1)  # Check every second

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in rate limiter loop: {e}")
                await asyncio.sleep(5)

    async def _connection_manager_loop(self):
        """Connection management loop."""
        while self.running:
            try:
                # Monitor connection health
                await self._monitor_connection_health()

                # Cleanup idle connections
                await self._cleanup_idle_connections()

                # Optimize connection pools
                await self._optimize_connection_pools()

                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in connection manager loop: {e}")
                await asyncio.sleep(10)

    async def _performance_optimizer_loop(self):
        """Network performance optimization loop."""
        while self.running:
            try:
                # Analyze performance patterns
                await self._analyze_performance_patterns()

                # Optimize bandwidth allocation
                await self._optimize_bandwidth_allocation()

                # Adjust rate limits based on performance
                await self._adjust_adaptive_rate_limits()

                await asyncio.sleep(60)  # Optimize every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance optimizer loop: {e}")
                await asyncio.sleep(30)

    async def check_rate_limit(self, component: str, request_type: str = "default") -> bool:
        """Check if a request is allowed under rate limits."""
        try:
            allocation = self.component_allocations.get(component)
            if not allocation:
                return True  # No allocation = no limits

            current_time = time.time()
            rate_limiter_key = f"{component}_{request_type}"

            # Initialize rate limiter if not exists
            if rate_limiter_key not in self.rate_limiters:
                self.rate_limiters[rate_limiter_key] = {
                    'requests': deque(maxlen=1000),
                    'tokens': allocation.requests_per_second,
                    'last_refill': current_time
                }

            rate_limiter = self.rate_limiters[rate_limiter_key]

            # Apply rate limiting strategy
            if allocation.rate_limit_strategy == RateLimitStrategy.SLIDING_WINDOW:
                return await self._check_sliding_window_limit(rate_limiter, allocation, current_time)
            elif allocation.rate_limit_strategy == RateLimitStrategy.TOKEN_BUCKET:
                return await self._check_token_bucket_limit(rate_limiter, allocation, current_time)
            elif allocation.rate_limit_strategy == RateLimitStrategy.ADAPTIVE:
                return await self._check_adaptive_limit(rate_limiter, allocation, current_time, component)
            else:  # FIXED_WINDOW
                return await self._check_fixed_window_limit(rate_limiter, allocation, current_time)

        except Exception as e:
            logger.error(f"Error checking rate limit for {component}: {e}")
            return True  # Allow on error

    async def _check_sliding_window_limit(self, rate_limiter: Dict, allocation: NetworkAllocation, current_time: float) -> bool:
        """Check sliding window rate limit."""
        # Remove old requests (older than 1 second)
        cutoff_time = current_time - 1.0
        while rate_limiter['requests'] and rate_limiter['requests'][0] < cutoff_time:
            rate_limiter['requests'].popleft()

        # Check if under limit
        if len(rate_limiter['requests']) < allocation.requests_per_second:
            rate_limiter['requests'].append(current_time)
            return True

        return False

    async def _check_token_bucket_limit(self, rate_limiter: Dict, allocation: NetworkAllocation, current_time: float) -> bool:
        """Check token bucket rate limit."""
        # Refill tokens
        time_passed = current_time - rate_limiter['last_refill']
        tokens_to_add = time_passed * allocation.requests_per_second
        rate_limiter['tokens'] = min(
            allocation.requests_per_second * 2,  # Burst capacity
            rate_limiter['tokens'] + tokens_to_add
        )
        rate_limiter['last_refill'] = current_time

        # Check if token available
        if rate_limiter['tokens'] >= 1.0:
            rate_limiter['tokens'] -= 1.0
            return True

        return False

    async def _check_adaptive_limit(self, rate_limiter: Dict, allocation: NetworkAllocation, current_time: float, component: str) -> bool:
        """Check adaptive rate limit based on system performance."""
        # Get component metrics
        metrics = self.connection_metrics.get(component)
        if not metrics:
            return await self._check_sliding_window_limit(rate_limiter, allocation, current_time)

        # Adjust rate based on success rate and latency
        success_rate = (metrics.successful_requests / max(metrics.total_requests, 1)) * 100
        avg_latency = metrics.average_latency_ms

        # Calculate adaptive rate
        base_rate = allocation.requests_per_second
        if success_rate > 95 and avg_latency < 100:
            # Good performance, allow higher rate
            adaptive_rate = base_rate * 1.5
        elif success_rate < 80 or avg_latency > 500:
            # Poor performance, reduce rate
            adaptive_rate = base_rate * 0.5
        else:
            adaptive_rate = base_rate

        # Create temporary allocation with adaptive rate
        temp_allocation = NetworkAllocation(
            component=component,
            requests_per_second=adaptive_rate
        )

        return await self._check_sliding_window_limit(rate_limiter, temp_allocation, current_time)

    async def _check_fixed_window_limit(self, rate_limiter: Dict, allocation: NetworkAllocation, current_time: float) -> bool:
        """Check fixed window rate limit."""
        window_start = int(current_time)

        # Reset if new window
        if 'window_start' not in rate_limiter or rate_limiter['window_start'] != window_start:
            rate_limiter['window_start'] = window_start
            rate_limiter['window_count'] = 0

        # Check if under limit
        if rate_limiter['window_count'] < allocation.requests_per_second:
            rate_limiter['window_count'] += 1
            return True

        return False

    async def record_request(self, component: str, success: bool, latency_ms: float = 0, bytes_transferred: int = 0):
        """Record a network request for metrics tracking."""
        try:
            metrics = self.connection_metrics.get(component)
            if not metrics:
                return

            # Update request counts
            metrics.total_requests += 1
            if success:
                metrics.successful_requests += 1
            else:
                metrics.failed_requests += 1

            # Update latency (moving average)
            if latency_ms > 0:
                if metrics.average_latency_ms == 0:
                    metrics.average_latency_ms = latency_ms
                else:
                    # Exponential moving average
                    alpha = 0.1
                    metrics.average_latency_ms = (alpha * latency_ms) + ((1 - alpha) * metrics.average_latency_ms)

                # Store latency history
                self.latency_history[component].append(latency_ms)

            # Update bandwidth usage
            if bytes_transferred > 0:
                # Convert to Mbps (rough estimate)
                mbps = (bytes_transferred * 8) / (1024 * 1024)
                metrics.bandwidth_used_mbps = mbps

            metrics.last_updated = datetime.now()

        except Exception as e:
            logger.error(f"Error recording request for {component}: {e}")

    async def get_connection_session(self, component: str) -> Optional[aiohttp.ClientSession]:
        """Get connection session for a component."""
        return self.connection_pools.get(component)

    async def _check_network_alerts(self, metrics: Dict[str, Any]):
        """Check for network-related alerts."""
        try:
            system_network = metrics.get('system_network', {})
            total_bandwidth = system_network.get('total_bandwidth_mbps', 0)

            # Check bandwidth alerts
            if total_bandwidth > 100 * (self.config.bandwidth_critical_threshold / 100):
                await self._create_alert(
                    "system", "bandwidth_critical", "critical",
                    f"System bandwidth usage critical: {total_bandwidth:.1f} Mbps"
                )
            elif total_bandwidth > 100 * (self.config.bandwidth_warning_threshold / 100):
                await self._create_alert(
                    "system", "bandwidth_warning", "warning",
                    f"System bandwidth usage high: {total_bandwidth:.1f} Mbps"
                )

            # Check component alerts
            components = metrics.get('components', {})
            for component, comp_metrics in components.items():
                allocation = self.component_allocations.get(component)
                if not allocation:
                    continue

                # Check connection limits
                active_connections = comp_metrics.get('active_connections', 0)
                connection_limit = allocation.max_concurrent_connections
                connection_usage = (active_connections / connection_limit) * 100

                if connection_usage > self.config.connection_critical_threshold:
                    await self._create_alert(
                        component, "connections_critical", "critical",
                        f"Connection usage critical: {active_connections}/{connection_limit}"
                    )
                elif connection_usage > self.config.connection_warning_threshold:
                    await self._create_alert(
                        component, "connections_warning", "warning",
                        f"Connection usage high: {active_connections}/{connection_limit}"
                    )

                # Check success rate
                success_rate = comp_metrics.get('success_rate', 100)
                if success_rate < 80:
                    await self._create_alert(
                        component, "low_success_rate", "warning",
                        f"Low success rate: {success_rate:.1f}%"
                    )

                # Check latency
                avg_latency = comp_metrics.get('average_latency_ms', 0)
                if avg_latency > 1000:
                    await self._create_alert(
                        component, "high_latency", "warning",
                        f"High latency: {avg_latency:.1f}ms"
                    )

        except Exception as e:
            logger.error(f"Error checking network alerts: {e}")

    async def _create_alert(self, component: str, alert_type: str, severity: str, message: str):
        """Create a network alert."""
        try:
            alert_key = f"{component}_{alert_type}"

            # Check cooldown
            if alert_key in self.active_alerts:
                last_alert = self.active_alerts[alert_key]
                if not last_alert.resolved:
                    time_since = datetime.now() - last_alert.timestamp
                    if time_since.total_seconds() < (self.config.alert_cooldown_minutes * 60):
                        return  # Still in cooldown

            # Create new alert
            alert = NetworkAlert(
                component=component,
                alert_type=alert_type,
                severity=severity,
                message=message
            )

            self.active_alerts[alert_key] = alert
            self.alert_history.append(alert)

            logger.warning(f"Network Alert [{severity.upper()}] {component}: {message}")

        except Exception as e:
            logger.error(f"Error creating alert: {e}")

    async def _load_state(self):
        """Load previous state from disk."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)

                # Restore metrics history
                if 'network_history' in state:
                    for entry in state['network_history'][-100:]:  # Last 100 entries
                        entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                        self.network_history.append(entry)

                logger.info("Network manager state loaded")

        except Exception as e:
            logger.error(f"Error loading state: {e}")

    async def _save_state(self):
        """Save current state to disk."""
        try:
            state = {
                'network_history': [
                    {
                        'timestamp': entry['timestamp'].isoformat(),
                        'metrics': entry['metrics']
                    }
                    for entry in list(self.network_history)[-100:]  # Last 100 entries
                ],
                'component_metrics': {
                    component: {
                        'total_requests': metrics.total_requests,
                        'successful_requests': metrics.successful_requests,
                        'failed_requests': metrics.failed_requests,
                        'average_latency_ms': metrics.average_latency_ms,
                        'rate_limit_hits': metrics.rate_limit_hits
                    }
                    for component, metrics in self.connection_metrics.items()
                }
            }

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

            logger.debug("Network manager state saved")

        except Exception as e:
            logger.error(f"Error saving state: {e}")

    # Placeholder methods for monitoring loops (to be implemented)
    async def _update_component_metrics(self):
        """Update component metrics from connection pools."""
        try:
            for component, session in self.connection_pools.items():
                if component in self.connection_metrics:
                    # Update active connections count
                    connector = session.connector
                    if hasattr(connector, '_conns'):
                        active_count = sum(len(conns) for conns in connector._conns.values())
                        self.connection_metrics[component].active_connections = active_count
        except Exception as e:
            logger.error(f"Error updating component metrics: {e}")

    async def _cleanup_rate_limiters(self):
        """Clean up old rate limiter data."""
        try:
            current_time = time.time()
            for rate_limiter in self.rate_limiters.values():
                if 'requests' in rate_limiter:
                    # Remove requests older than 60 seconds
                    cutoff_time = current_time - 60
                    while rate_limiter['requests'] and rate_limiter['requests'][0] < cutoff_time:
                        rate_limiter['requests'].popleft()
        except Exception as e:
            logger.error(f"Error cleaning up rate limiters: {e}")

    async def _update_global_rate_limiter(self):
        """Update global rate limiter."""
        try:
            current_time = time.time()
            # Clean up old requests
            cutoff_time = current_time - 1.0
            while (self.global_rate_limiter['requests'] and
                   self.global_rate_limiter['requests'][0] < cutoff_time):
                self.global_rate_limiter['requests'].popleft()
        except Exception as e:
            logger.error(f"Error updating global rate limiter: {e}")

    async def _check_component_rate_limits(self):
        """Check component rate limits and update metrics."""
        try:
            for component in self.component_allocations:
                if component in self.connection_metrics:
                    # Count rate limit hits in the last minute
                    rate_limiter_key = f"{component}_default"
                    if rate_limiter_key in self.rate_limiters:
                        # This is a placeholder - actual implementation would track hits
                        pass
        except Exception as e:
            logger.error(f"Error checking component rate limits: {e}")

    async def _monitor_connection_health(self):
        """Monitor connection pool health."""
        try:
            for component, session in self.connection_pools.items():
                if session.closed:
                    logger.warning(f"Connection pool for {component} is closed")
                    # Could trigger reconnection logic here
        except Exception as e:
            logger.error(f"Error monitoring connection health: {e}")

    async def _cleanup_idle_connections(self):
        """Clean up idle connections."""
        try:
            for component, session in self.connection_pools.items():
                connector = session.connector
                if hasattr(connector, '_cleanup_closed'):
                    await connector._cleanup_closed()
        except Exception as e:
            logger.error(f"Error cleaning up idle connections: {e}")

    async def _optimize_connection_pools(self):
        """Optimize connection pool settings."""
        try:
            # Placeholder for connection pool optimization
            # Could adjust pool sizes based on usage patterns
            pass
        except Exception as e:
            logger.error(f"Error optimizing connection pools: {e}")

    async def _analyze_performance_patterns(self):
        """Analyze network performance patterns."""
        try:
            # Analyze latency patterns
            for component, latency_data in self.latency_history.items():
                if len(latency_data) > 10:
                    avg_latency = statistics.mean(latency_data)
                    if component in self.connection_metrics:
                        self.connection_metrics[component].average_latency_ms = avg_latency
        except Exception as e:
            logger.error(f"Error analyzing performance patterns: {e}")

    async def _optimize_bandwidth_allocation(self):
        """Optimize bandwidth allocation based on usage."""
        try:
            # Placeholder for bandwidth optimization
            # Could adjust allocations based on actual usage patterns
            pass
        except Exception as e:
            logger.error(f"Error optimizing bandwidth allocation: {e}")

    async def _adjust_adaptive_rate_limits(self):
        """Adjust adaptive rate limits based on performance."""
        try:
            for component, metrics in self.connection_metrics.items():
                allocation = self.component_allocations.get(component)
                if allocation and allocation.rate_limit_strategy == RateLimitStrategy.ADAPTIVE:
                    # Adjust rate limits based on success rate and latency
                    success_rate = (metrics.successful_requests / max(metrics.total_requests, 1)) * 100
                    if success_rate > 95 and metrics.average_latency_ms < 100:
                        # Could increase rate limits here
                        pass
                    elif success_rate < 80 or metrics.average_latency_ms > 500:
                        # Could decrease rate limits here
                        pass
        except Exception as e:
            logger.error(f"Error adjusting adaptive rate limits: {e}")

    async def get_network_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive network data for dashboard display."""
        try:
            metrics = await self.get_network_metrics()

            # Calculate summary statistics
            total_requests = sum(
                m.total_requests for m in self.connection_metrics.values()
            )
            total_successful = sum(
                m.successful_requests for m in self.connection_metrics.values()
            )
            overall_success_rate = (total_successful / max(total_requests, 1)) * 100

            # Get recent performance data
            recent_bandwidth = []
            if len(self.bandwidth_history) > 0:
                recent_bandwidth = list(self.bandwidth_history)[-10:]

            return {
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_requests': total_requests,
                    'overall_success_rate': overall_success_rate,
                    'active_connections': sum(
                        m.active_connections for m in self.connection_metrics.values()
                    ),
                    'active_alerts': len([a for a in self.active_alerts.values() if not a.resolved])
                },
                'system_metrics': metrics.get('system_network', {}),
                'component_metrics': metrics.get('components', {}),
                'recent_bandwidth': recent_bandwidth,
                'rate_limiters': len(self.rate_limiters),
                'connection_pools': len(self.connection_pools)
            }

        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {}
