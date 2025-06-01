"""
Resource Manager - Main Orchestrator for Resource Management System

This is the central coordinator for all resource management operations in the MayArbi
arbitrage system. It manages CPU, memory, network, storage resources and provides
real-time monitoring, load balancing, and automatic scaling capabilities.
"""

import asyncio
import logging
import psutil
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import statistics
from collections import deque, defaultdict

logger = logging.getLogger(__name__)


class ResourceStatus(Enum):
    """Resource status levels."""
    OPTIMAL = "optimal"
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"


class ResourceType(Enum):
    """Types of system resources."""
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    STORAGE = "storage"
    PROCESS = "process"


@dataclass
class ResourceMetrics:
    """Resource utilization metrics."""
    resource_type: ResourceType
    current_usage: float
    peak_usage: float
    average_usage: float
    threshold_warning: float
    threshold_critical: float
    status: ResourceStatus
    timestamp: datetime = field(default_factory=datetime.now)
    unit: str = "%"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'resource_type': self.resource_type.value,
            'current_usage': self.current_usage,
            'peak_usage': self.peak_usage,
            'average_usage': self.average_usage,
            'threshold_warning': self.threshold_warning,
            'threshold_critical': self.threshold_critical,
            'status': self.status.value,
            'timestamp': self.timestamp.isoformat(),
            'unit': self.unit
        }


@dataclass
class ResourceAlert:
    """Resource alert information."""
    alert_id: str
    resource_type: ResourceType
    component: str
    severity: ResourceStatus
    message: str
    current_value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False


@dataclass
class ResourceAllocation:
    """Resource allocation for a component."""
    component: str
    cpu_limit: float  # Percentage
    memory_limit: float  # MB
    network_limit: float  # Mbps
    storage_limit: float  # GB
    priority: int  # 1-10, higher is more important
    auto_scale: bool = True


@dataclass
class ResourceConfig:
    """Configuration for resource management."""
    # Monitoring intervals
    monitoring_interval: int = 30  # seconds
    metrics_retention_hours: int = 24
    
    # Resource thresholds
    cpu_warning_threshold: float = 70.0
    cpu_critical_threshold: float = 85.0
    memory_warning_threshold: float = 75.0
    memory_critical_threshold: float = 90.0
    network_warning_threshold: float = 80.0
    network_critical_threshold: float = 95.0
    storage_warning_threshold: float = 80.0
    storage_critical_threshold: float = 95.0
    
    # Scaling parameters
    scale_up_threshold: float = 80.0
    scale_down_threshold: float = 40.0
    scale_cooldown_minutes: int = 5
    
    # Performance optimization
    enable_auto_scaling: bool = True
    enable_load_balancing: bool = True
    enable_garbage_collection: bool = True
    gc_interval_minutes: int = 15
    
    # Alert settings
    alert_cooldown_minutes: int = 5
    max_alerts_per_hour: int = 20


class ResourceManager:
    """
    Main Resource Manager - Orchestrates all resource management operations.
    
    This class coordinates CPU, memory, network, and storage management across
    all system components, providing real-time monitoring, automatic scaling,
    and performance optimization.
    """
    
    def __init__(self, config: Optional[ResourceConfig] = None):
        self.config = config or ResourceConfig()
        self.running = False
        
        # Resource tracking
        self.resource_metrics: Dict[ResourceType, deque] = {
            resource_type: deque(maxlen=1000) for resource_type in ResourceType
        }
        self.component_allocations: Dict[str, ResourceAllocation] = {}
        self.active_alerts: Dict[str, ResourceAlert] = {}
        
        # Performance tracking
        self.performance_history: deque = deque(maxlen=1000)
        self.bottlenecks: Dict[str, List[str]] = defaultdict(list)
        
        # Monitoring tasks
        self.monitoring_tasks: List[asyncio.Task] = []
        
        # Alert callbacks
        self.alert_callbacks: List[Callable] = []
        
        # State persistence
        self.state_file = Path("data/resource_manager_state.json")
        self.state_file.parent.mkdir(exist_ok=True)
        
        # Initialize component allocations
        self._initialize_component_allocations()
        
        logger.info("🔧 Resource Manager initialized")
    
    def _initialize_component_allocations(self):
        """Initialize default resource allocations for system components."""
        default_allocations = {
            "arbitrage_engine": ResourceAllocation(
                component="arbitrage_engine",
                cpu_limit=25.0, memory_limit=512, network_limit=10.0, storage_limit=1.0,
                priority=9, auto_scale=True
            ),
            "bridge_monitor": ResourceAllocation(
                component="bridge_monitor", 
                cpu_limit=15.0, memory_limit=256, network_limit=5.0, storage_limit=0.5,
                priority=7, auto_scale=True
            ),
            "cross_chain_mev": ResourceAllocation(
                component="cross_chain_mev",
                cpu_limit=20.0, memory_limit=384, network_limit=8.0, storage_limit=0.8,
                priority=8, auto_scale=True
            ),
            "wallet_manager": ResourceAllocation(
                component="wallet_manager",
                cpu_limit=10.0, memory_limit=128, network_limit=3.0, storage_limit=0.2,
                priority=10, auto_scale=False  # Critical, don't auto-scale
            ),
            "price_feeds": ResourceAllocation(
                component="price_feeds",
                cpu_limit=15.0, memory_limit=256, network_limit=15.0, storage_limit=0.5,
                priority=8, auto_scale=True
            ),
            "memory_system": ResourceAllocation(
                component="memory_system",
                cpu_limit=10.0, memory_limit=512, network_limit=2.0, storage_limit=2.0,
                priority=6, auto_scale=True
            ),
            "health_monitor": ResourceAllocation(
                component="health_monitor",
                cpu_limit=5.0, memory_limit=128, network_limit=1.0, storage_limit=0.3,
                priority=5, auto_scale=False
            )
        }
        
        self.component_allocations.update(default_allocations)
        logger.debug(f"Initialized allocations for {len(default_allocations)} components")

    async def start_resource_management(self):
        """Start the resource management system."""
        if self.running:
            logger.warning("Resource management already running")
            return

        self.running = True
        logger.info("🚀 Starting Resource Management System")

        # Load previous state
        await self._load_state()

        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._resource_monitor_loop()),
            asyncio.create_task(self._performance_monitor_loop()),
            asyncio.create_task(self._scaling_controller_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]

        logger.info("✅ Resource Management System started")

    async def stop_resource_management(self):
        """Stop the resource management system."""
        if not self.running:
            return

        self.running = False
        logger.info("🛑 Stopping Resource Management System")

        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

        # Save state
        await self._save_state()

        logger.info("✅ Resource Management System stopped")

    async def get_system_resources(self) -> Dict[str, ResourceMetrics]:
        """Get current system resource utilization."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_metrics = ResourceMetrics(
                resource_type=ResourceType.CPU,
                current_usage=cpu_percent,
                peak_usage=max([m.current_usage for m in self.resource_metrics[ResourceType.CPU]] + [cpu_percent]),
                average_usage=statistics.mean([m.current_usage for m in self.resource_metrics[ResourceType.CPU]] + [cpu_percent]),
                threshold_warning=self.config.cpu_warning_threshold,
                threshold_critical=self.config.cpu_critical_threshold,
                status=self._determine_resource_status(cpu_percent, self.config.cpu_warning_threshold, self.config.cpu_critical_threshold)
            )

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_metrics = ResourceMetrics(
                resource_type=ResourceType.MEMORY,
                current_usage=memory_percent,
                peak_usage=max([m.current_usage for m in self.resource_metrics[ResourceType.MEMORY]] + [memory_percent]),
                average_usage=statistics.mean([m.current_usage for m in self.resource_metrics[ResourceType.MEMORY]] + [memory_percent]),
                threshold_warning=self.config.memory_warning_threshold,
                threshold_critical=self.config.memory_critical_threshold,
                status=self._determine_resource_status(memory_percent, self.config.memory_warning_threshold, self.config.memory_critical_threshold)
            )

            # Network metrics (simplified - would need more sophisticated monitoring in production)
            network_percent = 0.0  # Placeholder - would implement actual network monitoring
            network_metrics = ResourceMetrics(
                resource_type=ResourceType.NETWORK,
                current_usage=network_percent,
                peak_usage=0.0,
                average_usage=0.0,
                threshold_warning=self.config.network_warning_threshold,
                threshold_critical=self.config.network_critical_threshold,
                status=ResourceStatus.OPTIMAL
            )

            # Storage metrics
            disk = psutil.disk_usage('/')
            storage_percent = (disk.used / disk.total) * 100
            storage_metrics = ResourceMetrics(
                resource_type=ResourceType.STORAGE,
                current_usage=storage_percent,
                peak_usage=max([m.current_usage for m in self.resource_metrics[ResourceType.STORAGE]] + [storage_percent]),
                average_usage=statistics.mean([m.current_usage for m in self.resource_metrics[ResourceType.STORAGE]] + [storage_percent]),
                threshold_warning=self.config.storage_warning_threshold,
                threshold_critical=self.config.storage_critical_threshold,
                status=self._determine_resource_status(storage_percent, self.config.storage_warning_threshold, self.config.storage_critical_threshold)
            )

            return {
                'cpu': cpu_metrics,
                'memory': memory_metrics,
                'network': network_metrics,
                'storage': storage_metrics
            }

        except Exception as e:
            logger.error(f"Error getting system resources: {e}")
            return {}

    def _determine_resource_status(self, current: float, warning: float, critical: float) -> ResourceStatus:
        """Determine resource status based on thresholds."""
        if current >= critical:
            return ResourceStatus.CRITICAL
        elif current >= warning:
            return ResourceStatus.WARNING
        else:
            return ResourceStatus.OPTIMAL

    async def _resource_monitor_loop(self):
        """Main resource monitoring loop."""
        while self.running:
            try:
                # Get current resource metrics
                resources = await self.get_system_resources()

                # Store metrics
                for resource_type, metrics in resources.items():
                    self.resource_metrics[ResourceType(resource_type)].append(metrics)

                # Check for alerts
                await self._check_resource_alerts(resources)

                await asyncio.sleep(self.config.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resource monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _performance_monitor_loop(self):
        """Performance monitoring and bottleneck detection loop."""
        while self.running:
            try:
                # Collect performance data
                performance_data = await self._collect_performance_data()
                self.performance_history.append(performance_data)

                # Detect bottlenecks
                await self._detect_bottlenecks(performance_data)

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(10)

    async def _scaling_controller_loop(self):
        """Automatic scaling controller loop."""
        while self.running:
            try:
                if self.config.enable_auto_scaling:
                    await self._evaluate_scaling_needs()

                await asyncio.sleep(self.config.scale_cooldown_minutes * 60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scaling controller: {e}")
                await asyncio.sleep(30)

    async def _cleanup_loop(self):
        """Cleanup and maintenance loop."""
        while self.running:
            try:
                # Garbage collection
                if self.config.enable_garbage_collection:
                    await self._perform_garbage_collection()

                # Clean old metrics
                await self._cleanup_old_metrics()

                # Save state periodically
                await self._save_state()

                await asyncio.sleep(self.config.gc_interval_minutes * 60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)

    # Helper methods for monitoring loops
    async def _check_resource_alerts(self, resources: Dict[str, ResourceMetrics]):
        """Check for resource alerts and generate notifications."""
        for resource_name, metrics in resources.items():
            if metrics.status in [ResourceStatus.WARNING, ResourceStatus.CRITICAL]:
                alert_id = f"{resource_name}_{metrics.status.value}_{int(time.time())}"

                if alert_id not in self.active_alerts:
                    alert = ResourceAlert(
                        alert_id=alert_id,
                        resource_type=metrics.resource_type,
                        component="system",
                        severity=metrics.status,
                        message=f"{resource_name.upper()} usage at {metrics.current_usage:.1f}%",
                        current_value=metrics.current_usage,
                        threshold=metrics.threshold_warning if metrics.status == ResourceStatus.WARNING else metrics.threshold_critical
                    )

                    self.active_alerts[alert_id] = alert
                    await self._trigger_alert_callbacks(alert)

    async def _collect_performance_data(self) -> Dict[str, Any]:
        """Collect comprehensive performance data."""
        try:
            return {
                'timestamp': datetime.now(),
                'cpu_count': psutil.cpu_count(),
                'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
                'network_io': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {},
                'process_count': len(psutil.pids()),
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            }
        except Exception as e:
            logger.error(f"Error collecting performance data: {e}")
            return {'timestamp': datetime.now(), 'error': str(e)}

    async def _detect_bottlenecks(self, performance_data: Dict[str, Any]):
        """Detect system bottlenecks based on performance data."""
        bottlenecks = []

        # CPU bottleneck detection
        if 'load_average' in performance_data and performance_data['load_average']:
            load_avg = performance_data['load_average'][0]  # 1-minute average
            cpu_count = performance_data.get('cpu_count', 1)
            if load_avg > cpu_count * 0.8:
                bottlenecks.append("CPU overload detected")

        # Memory bottleneck detection
        if 'memory_available' in performance_data and 'memory_total' in performance_data:
            memory_usage = (1 - performance_data['memory_available'] / performance_data['memory_total']) * 100
            if memory_usage > 85:
                bottlenecks.append("Memory pressure detected")

        # Store bottlenecks
        if bottlenecks:
            timestamp = performance_data.get('timestamp', datetime.now())
            self.bottlenecks[timestamp.isoformat()] = bottlenecks
            logger.warning(f"🚨 Bottlenecks detected: {', '.join(bottlenecks)}")

    async def _evaluate_scaling_needs(self):
        """Evaluate if any components need scaling adjustments."""
        try:
            resources = await self.get_system_resources()

            for component, allocation in self.component_allocations.items():
                if not allocation.auto_scale:
                    continue

                # Check if component needs scaling based on resource usage
                cpu_usage = resources.get('cpu', ResourceMetrics(ResourceType.CPU, 0, 0, 0, 70, 85, ResourceStatus.OPTIMAL)).current_usage
                memory_usage = resources.get('memory', ResourceMetrics(ResourceType.MEMORY, 0, 0, 0, 75, 90, ResourceStatus.OPTIMAL)).current_usage

                if cpu_usage > self.config.scale_up_threshold or memory_usage > self.config.scale_up_threshold:
                    await self._scale_component_up(component, allocation)
                elif cpu_usage < self.config.scale_down_threshold and memory_usage < self.config.scale_down_threshold:
                    await self._scale_component_down(component, allocation)

        except Exception as e:
            logger.error(f"Error evaluating scaling needs: {e}")

    async def _scale_component_up(self, component: str, allocation: ResourceAllocation):
        """Scale up a component's resource allocation."""
        logger.info(f"📈 Scaling up {component}")
        # Increase allocation by 20%
        allocation.cpu_limit = min(allocation.cpu_limit * 1.2, 50.0)  # Cap at 50%
        allocation.memory_limit = min(allocation.memory_limit * 1.2, 2048)  # Cap at 2GB

    async def _scale_component_down(self, component: str, allocation: ResourceAllocation):
        """Scale down a component's resource allocation."""
        logger.info(f"📉 Scaling down {component}")
        # Decrease allocation by 10%
        allocation.cpu_limit = max(allocation.cpu_limit * 0.9, 5.0)  # Floor at 5%
        allocation.memory_limit = max(allocation.memory_limit * 0.9, 64)  # Floor at 64MB

    async def _perform_garbage_collection(self):
        """Perform garbage collection and memory optimization."""
        import gc
        before = psutil.virtual_memory().percent
        gc.collect()
        after = psutil.virtual_memory().percent

        if before - after > 1.0:  # If we freed more than 1% memory
            logger.info(f"🧹 Garbage collection freed {before - after:.1f}% memory")

    async def _cleanup_old_metrics(self):
        """Clean up old metrics to prevent memory bloat."""
        cutoff_time = datetime.now() - timedelta(hours=self.config.metrics_retention_hours)

        for resource_type in self.resource_metrics:
            # Remove old metrics
            while (self.resource_metrics[resource_type] and
                   self.resource_metrics[resource_type][0].timestamp < cutoff_time):
                self.resource_metrics[resource_type].popleft()

        # Clean old alerts
        old_alerts = [alert_id for alert_id, alert in self.active_alerts.items()
                     if alert.timestamp < cutoff_time]
        for alert_id in old_alerts:
            del self.active_alerts[alert_id]

    async def _trigger_alert_callbacks(self, alert: ResourceAlert):
        """Trigger registered alert callbacks."""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    def add_alert_callback(self, callback: Callable):
        """Add an alert callback function."""
        self.alert_callbacks.append(callback)

    async def _save_state(self):
        """Save current state to disk."""
        try:
            state = {
                'component_allocations': {
                    name: {
                        'component': alloc.component,
                        'cpu_limit': alloc.cpu_limit,
                        'memory_limit': alloc.memory_limit,
                        'network_limit': alloc.network_limit,
                        'storage_limit': alloc.storage_limit,
                        'priority': alloc.priority,
                        'auto_scale': alloc.auto_scale
                    } for name, alloc in self.component_allocations.items()
                },
                'active_alerts': {
                    alert_id: {
                        'alert_id': alert.alert_id,
                        'resource_type': alert.resource_type.value,
                        'component': alert.component,
                        'severity': alert.severity.value,
                        'message': alert.message,
                        'current_value': alert.current_value,
                        'threshold': alert.threshold,
                        'timestamp': alert.timestamp.isoformat(),
                        'resolved': alert.resolved
                    } for alert_id, alert in self.active_alerts.items()
                },
                'last_save': datetime.now().isoformat()
            }

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving state: {e}")

    async def _load_state(self):
        """Load previous state from disk."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)

                # Load component allocations
                if 'component_allocations' in state:
                    for name, alloc_data in state['component_allocations'].items():
                        self.component_allocations[name] = ResourceAllocation(**alloc_data)

                # Load active alerts
                if 'active_alerts' in state:
                    for alert_id, alert_data in state['active_alerts'].items():
                        alert_data['resource_type'] = ResourceType(alert_data['resource_type'])
                        alert_data['severity'] = ResourceStatus(alert_data['severity'])
                        alert_data['timestamp'] = datetime.fromisoformat(alert_data['timestamp'])
                        self.active_alerts[alert_id] = ResourceAlert(**alert_data)

                logger.info("📁 Resource manager state loaded")

        except Exception as e:
            logger.error(f"Error loading state: {e}")

    def get_resource_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive resource dashboard data."""
        try:
            # Get latest metrics for each resource type
            latest_metrics = {}
            for resource_type, metrics_deque in self.resource_metrics.items():
                if metrics_deque:
                    latest_metrics[resource_type.value] = metrics_deque[-1].to_dict()

            return {
                'timestamp': datetime.now().isoformat(),
                'system_status': self._get_overall_system_status(),
                'resource_metrics': latest_metrics,
                'component_allocations': {
                    name: {
                        'cpu_limit': alloc.cpu_limit,
                        'memory_limit': alloc.memory_limit,
                        'priority': alloc.priority,
                        'auto_scale': alloc.auto_scale
                    } for name, alloc in self.component_allocations.items()
                },
                'active_alerts': len(self.active_alerts),
                'recent_bottlenecks': list(self.bottlenecks.keys())[-5:] if self.bottlenecks else [],
                'performance_summary': self._get_performance_summary()
            }

        except Exception as e:
            logger.error(f"Error generating dashboard: {e}")
            return {'error': str(e)}

    def _get_overall_system_status(self) -> str:
        """Get overall system status based on all metrics."""
        if any(alert.severity == ResourceStatus.CRITICAL for alert in self.active_alerts.values()):
            return "CRITICAL"
        elif any(alert.severity == ResourceStatus.WARNING for alert in self.active_alerts.values()):
            return "WARNING"
        else:
            return "OPTIMAL"

    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary from recent history."""
        if not self.performance_history:
            return {}

        recent_data = list(self.performance_history)[-10:]  # Last 10 data points

        return {
            'avg_process_count': statistics.mean([d.get('process_count', 0) for d in recent_data]),
            'recent_bottlenecks': len(self.bottlenecks),
            'data_points': len(recent_data)
        }
