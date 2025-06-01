"""
Health Monitoring System - Phase 3 Chunk 5

Advanced server health checks, predictive monitoring, automatic failover,
and comprehensive alerting for the MCP orchestration ecosystem.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import statistics
from collections import deque, defaultdict

from .server_registry import MCPServerRegistry, ServerStatus, ServerType
from .coordinator_service import MCPCoordinatorService, ServerLoad

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class HealthMetricType(Enum):
    """Types of health metrics."""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    AVAILABILITY = "availability"
    DISK_USAGE = "disk_usage"
    NETWORK_LATENCY = "network_latency"


@dataclass
class HealthMetric:
    """Individual health metric."""
    metric_type: HealthMetricType
    value: float
    timestamp: datetime
    threshold_warning: float = 0.7
    threshold_critical: float = 0.9
    unit: str = ""
    
    @property
    def status(self) -> HealthStatus:
        """Get status based on thresholds."""
        if self.value >= self.threshold_critical:
            return HealthStatus.CRITICAL
        elif self.value >= self.threshold_warning:
            return HealthStatus.WARNING
        elif self.value >= 0:
            return HealthStatus.GOOD
        else:
            return HealthStatus.UNKNOWN


@dataclass
class HealthAlert:
    """Health monitoring alert."""
    alert_id: str
    server_id: str
    severity: AlertSeverity
    metric_type: HealthMetricType
    message: str
    value: float
    threshold: float
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class ServerHealthProfile:
    """Comprehensive health profile for a server."""
    server_id: str
    overall_status: HealthStatus = HealthStatus.UNKNOWN
    metrics: Dict[HealthMetricType, HealthMetric] = field(default_factory=dict)
    metric_history: Dict[HealthMetricType, deque] = field(default_factory=lambda: defaultdict(lambda: deque(maxlen=100)))
    last_check: Optional[datetime] = None
    uptime_start: Optional[datetime] = None
    total_checks: int = 0
    failed_checks: int = 0
    consecutive_failures: int = 0
    predicted_failure_time: Optional[datetime] = None
    health_trend: str = "stable"  # improving, stable, degrading
    
    @property
    def availability(self) -> float:
        """Calculate availability percentage."""
        if self.total_checks == 0:
            return 0.0
        return (self.total_checks - self.failed_checks) / self.total_checks * 100
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_checks == 0:
            return 0.0
        return self.failed_checks / self.total_checks


class HealthMonitoringSystem:
    """
    Advanced health monitoring system for MCP servers.
    
    This is Chunk 5 of the Phase 3 MCP Orchestration Engine.
    """

    def __init__(self, server_registry: MCPServerRegistry,
                 coordinator: MCPCoordinatorService,
                 config: Dict[str, Any] = None):
        """Initialize the health monitoring system."""
        self.server_registry = server_registry
        self.coordinator = coordinator
        self.config = config or {}
        
        # Monitoring configuration
        self.check_interval = self.config.get('check_interval', 30.0)  # seconds
        self.metric_retention_hours = self.config.get('metric_retention_hours', 24)
        self.prediction_window_minutes = self.config.get('prediction_window_minutes', 60)
        self.alert_cooldown_minutes = self.config.get('alert_cooldown_minutes', 5)
        
        # Health profiles
        self.health_profiles: Dict[str, ServerHealthProfile] = {}
        
        # Alerting
        self.active_alerts: Dict[str, HealthAlert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.alert_callbacks: List[Callable[[HealthAlert], None]] = []
        self.alert_cooldowns: Dict[str, datetime] = {}
        
        # Monitoring state
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.predictor_task: Optional[asyncio.Task] = None
        
        # Thresholds (can be customized per server)
        self.default_thresholds = {
            HealthMetricType.CPU_USAGE: {'warning': 0.7, 'critical': 0.9},
            HealthMetricType.MEMORY_USAGE: {'warning': 0.8, 'critical': 0.95},
            HealthMetricType.RESPONSE_TIME: {'warning': 1000, 'critical': 5000},  # ms
            HealthMetricType.ERROR_RATE: {'warning': 0.05, 'critical': 0.1},
            HealthMetricType.AVAILABILITY: {'warning': 0.95, 'critical': 0.9}
        }
        
        # Predictive analytics
        self.trend_analysis_window = 20  # number of data points
        self.failure_prediction_enabled = True

    async def start_monitoring(self) -> None:
        """Start the health monitoring system."""
        if self.running:
            logger.warning("Health monitoring already running")
            return
        
        self.running = True
        logger.info("Starting health monitoring system")
        
        # Initialize health profiles for all servers
        await self._initialize_health_profiles()
        
        # Start monitoring tasks
        self.monitor_task = asyncio.create_task(self._health_monitor_loop())
        self.predictor_task = asyncio.create_task(self._predictive_monitor_loop())
        
        logger.info("Health monitoring system started successfully")

    async def stop_monitoring(self) -> None:
        """Stop the health monitoring system."""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping health monitoring system")
        
        # Cancel tasks
        if self.monitor_task:
            self.monitor_task.cancel()
        if self.predictor_task:
            self.predictor_task.cancel()
        
        # Wait for tasks to complete
        tasks = [t for t in [self.monitor_task, self.predictor_task] if t]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Health monitoring system stopped")

    async def _initialize_health_profiles(self) -> None:
        """Initialize health profiles for all registered servers."""
        for server in self.server_registry.servers.values():
            if server.server_id not in self.health_profiles:
                self.health_profiles[server.server_id] = ServerHealthProfile(
                    server_id=server.server_id,
                    uptime_start=datetime.now() if server.status == ServerStatus.CONNECTED else None
                )
                logger.debug(f"Initialized health profile for {server.server_id}")

    async def _health_monitor_loop(self) -> None:
        """Main health monitoring loop."""
        while self.running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _predictive_monitor_loop(self) -> None:
        """Predictive monitoring and trend analysis loop."""
        while self.running:
            try:
                await self._perform_predictive_analysis()
                await asyncio.sleep(self.prediction_window_minutes * 60)  # Run every prediction window
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in predictive monitoring: {e}")
                await asyncio.sleep(60)

    async def _perform_health_checks(self) -> None:
        """Perform health checks on all servers."""
        for server_id, profile in self.health_profiles.items():
            try:
                await self._check_server_health(server_id, profile)
            except Exception as e:
                logger.error(f"Error checking health of {server_id}: {e}")
                profile.failed_checks += 1
                profile.consecutive_failures += 1

    async def _check_server_health(self, server_id: str, profile: ServerHealthProfile) -> None:
        """Check health of a specific server."""
        server = self.server_registry.get_server(server_id)
        if not server:
            return
        
        profile.total_checks += 1
        profile.last_check = datetime.now()
        
        # Get current load from coordinator
        coordinator_metrics = self.coordinator.get_coordinator_metrics()
        server_load = coordinator_metrics.get('server_loads', {}).get(server_id)
        
        if server.status != ServerStatus.CONNECTED:
            profile.failed_checks += 1
            profile.consecutive_failures += 1
            profile.overall_status = HealthStatus.FAILED
            await self._generate_alert(server_id, AlertSeverity.CRITICAL, 
                                     HealthMetricType.AVAILABILITY,
                                     f"Server {server_id} is not connected", 0.0, 1.0)
            return
        
        # Reset consecutive failures on successful connection
        profile.consecutive_failures = 0
        
        # Collect metrics
        metrics = await self._collect_server_metrics(server_id, server_load)
        
        # Update profile with new metrics
        worst_status = HealthStatus.EXCELLENT
        for metric_type, metric in metrics.items():
            profile.metrics[metric_type] = metric
            profile.metric_history[metric_type].append((metric.timestamp, metric.value))
            
            # Track worst status
            if metric.status.value > worst_status.value:
                worst_status = metric.status
            
            # Generate alerts for problematic metrics
            if metric.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                severity = AlertSeverity.WARNING if metric.status == HealthStatus.WARNING else AlertSeverity.CRITICAL
                await self._generate_alert(server_id, severity, metric_type,
                                         f"{metric_type.value} is {metric.status.value}: {metric.value}{metric.unit}",
                                         metric.value, metric.threshold_warning)
        
        profile.overall_status = worst_status
        
        # Update trend analysis
        self._update_health_trend(profile)

    async def _collect_server_metrics(self, server_id: str, server_load: Optional[Dict[str, Any]]) -> Dict[HealthMetricType, HealthMetric]:
        """Collect health metrics for a server."""
        metrics = {}
        now = datetime.now()
        
        if server_load:
            # CPU Usage
            cpu_usage = server_load.get('cpu_usage', 0.0)
            thresholds = self.default_thresholds[HealthMetricType.CPU_USAGE]
            metrics[HealthMetricType.CPU_USAGE] = HealthMetric(
                metric_type=HealthMetricType.CPU_USAGE,
                value=cpu_usage,
                timestamp=now,
                threshold_warning=thresholds['warning'],
                threshold_critical=thresholds['critical'],
                unit="%"
            )
            
            # Memory Usage
            memory_usage = server_load.get('memory_usage', 0.0)
            thresholds = self.default_thresholds[HealthMetricType.MEMORY_USAGE]
            metrics[HealthMetricType.MEMORY_USAGE] = HealthMetric(
                metric_type=HealthMetricType.MEMORY_USAGE,
                value=memory_usage,
                timestamp=now,
                threshold_warning=thresholds['warning'],
                threshold_critical=thresholds['critical'],
                unit="%"
            )
            
            # Response Time
            response_time = server_load.get('response_time_ms', 0.0)
            thresholds = self.default_thresholds[HealthMetricType.RESPONSE_TIME]
            metrics[HealthMetricType.RESPONSE_TIME] = HealthMetric(
                metric_type=HealthMetricType.RESPONSE_TIME,
                value=response_time,
                timestamp=now,
                threshold_warning=thresholds['warning'],
                threshold_critical=thresholds['critical'],
                unit="ms"
            )
        
        # Simulate additional metrics for demonstration
        import random
        
        # Error Rate
        error_rate = max(0, min(0.2, random.gauss(0.02, 0.01)))  # 2% average with variation
        thresholds = self.default_thresholds[HealthMetricType.ERROR_RATE]
        metrics[HealthMetricType.ERROR_RATE] = HealthMetric(
            metric_type=HealthMetricType.ERROR_RATE,
            value=error_rate,
            timestamp=now,
            threshold_warning=thresholds['warning'],
            threshold_critical=thresholds['critical'],
            unit="%"
        )
        
        # Availability
        profile = self.health_profiles.get(server_id)
        availability = profile.availability / 100 if profile else 1.0
        thresholds = self.default_thresholds[HealthMetricType.AVAILABILITY]
        metrics[HealthMetricType.AVAILABILITY] = HealthMetric(
            metric_type=HealthMetricType.AVAILABILITY,
            value=availability,
            timestamp=now,
            threshold_warning=thresholds['warning'],
            threshold_critical=thresholds['critical'],
            unit="%"
        )
        
        return metrics

    def _update_health_trend(self, profile: ServerHealthProfile) -> None:
        """Update health trend analysis for a server."""
        if len(profile.metric_history[HealthMetricType.CPU_USAGE]) < self.trend_analysis_window:
            profile.health_trend = "insufficient_data"
            return
        
        # Analyze CPU usage trend as primary indicator
        cpu_history = list(profile.metric_history[HealthMetricType.CPU_USAGE])
        recent_values = [value for _, value in cpu_history[-self.trend_analysis_window:]]
        
        if len(recent_values) >= 3:
            # Calculate trend using linear regression slope
            x_values = list(range(len(recent_values)))
            slope = self._calculate_trend_slope(x_values, recent_values)
            
            if slope > 0.01:  # Increasing trend
                profile.health_trend = "degrading"
            elif slope < -0.01:  # Decreasing trend
                profile.health_trend = "improving"
            else:
                profile.health_trend = "stable"

    def _calculate_trend_slope(self, x_values: List[int], y_values: List[float]) -> float:
        """Calculate trend slope using simple linear regression."""
        n = len(x_values)
        if n < 2:
            return 0.0
        
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        return numerator / denominator if denominator != 0 else 0.0

    async def _perform_predictive_analysis(self) -> None:
        """Perform predictive analysis for potential failures."""
        if not self.failure_prediction_enabled:
            return
        
        for server_id, profile in self.health_profiles.items():
            try:
                await self._predict_server_failure(server_id, profile)
            except Exception as e:
                logger.error(f"Error in predictive analysis for {server_id}: {e}")

    async def _predict_server_failure(self, server_id: str, profile: ServerHealthProfile) -> None:
        """Predict potential server failure based on trends."""
        if profile.health_trend != "degrading":
            profile.predicted_failure_time = None
            return
        
        # Simple prediction based on CPU usage trend
        cpu_history = list(profile.metric_history[HealthMetricType.CPU_USAGE])
        if len(cpu_history) < self.trend_analysis_window:
            return
        
        recent_values = [value for _, value in cpu_history[-self.trend_analysis_window:]]
        slope = self._calculate_trend_slope(list(range(len(recent_values))), recent_values)
        
        if slope > 0:
            current_cpu = recent_values[-1]
            critical_threshold = 0.95
            
            # Estimate time to reach critical threshold
            time_to_critical = (critical_threshold - current_cpu) / slope
            
            if 0 < time_to_critical <= self.prediction_window_minutes:
                predicted_time = datetime.now() + timedelta(minutes=time_to_critical)
                profile.predicted_failure_time = predicted_time
                
                await self._generate_alert(
                    server_id, AlertSeverity.WARNING, HealthMetricType.CPU_USAGE,
                    f"Predicted failure in {time_to_critical:.1f} minutes based on CPU trend",
                    current_cpu, critical_threshold
                )

    async def _generate_alert(self, server_id: str, severity: AlertSeverity,
                            metric_type: HealthMetricType, message: str,
                            value: float, threshold: float) -> None:
        """Generate and process a health alert."""
        # Check cooldown
        cooldown_key = f"{server_id}_{metric_type.value}_{severity.value}"
        if cooldown_key in self.alert_cooldowns:
            if datetime.now() - self.alert_cooldowns[cooldown_key] < timedelta(minutes=self.alert_cooldown_minutes):
                return  # Still in cooldown
        
        # Create alert
        alert_id = f"alert_{server_id}_{metric_type.value}_{datetime.now().timestamp()}"
        alert = HealthAlert(
            alert_id=alert_id,
            server_id=server_id,
            severity=severity,
            metric_type=metric_type,
            message=message,
            value=value,
            threshold=threshold,
            timestamp=datetime.now()
        )
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.alert_cooldowns[cooldown_key] = datetime.now()
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
        
        logger.warning(f"Health alert generated: {alert.message}")

    def add_alert_callback(self, callback: Callable[[HealthAlert], None]) -> None:
        """Add a callback for health alerts."""
        self.alert_callbacks.append(callback)

    def get_server_health(self, server_id: str) -> Optional[ServerHealthProfile]:
        """Get health profile for a specific server."""
        return self.health_profiles.get(server_id)

    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        total_servers = len(self.health_profiles)
        if total_servers == 0:
            return {'status': 'no_servers', 'servers': {}}
        
        status_counts = defaultdict(int)
        trend_counts = defaultdict(int)
        total_availability = 0
        
        for profile in self.health_profiles.values():
            status_counts[profile.overall_status.value] += 1
            trend_counts[profile.health_trend] += 1
            total_availability += profile.availability
        
        # Determine overall system status
        if status_counts['failed'] > 0:
            overall_status = 'critical'
        elif status_counts['critical'] > 0:
            overall_status = 'critical'
        elif status_counts['warning'] > 0:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        return {
            'overall_status': overall_status,
            'total_servers': total_servers,
            'status_breakdown': dict(status_counts),
            'trend_breakdown': dict(trend_counts),
            'average_availability': total_availability / total_servers,
            'active_alerts': len(self.active_alerts),
            'predicted_failures': len([p for p in self.health_profiles.values() 
                                     if p.predicted_failure_time]),
            'last_check': max((p.last_check for p in self.health_profiles.values() 
                             if p.last_check), default=None)
        }

    def get_monitoring_metrics(self) -> Dict[str, Any]:
        """Get health monitoring system metrics."""
        return {
            'running': self.running,
            'total_servers_monitored': len(self.health_profiles),
            'total_checks_performed': sum(p.total_checks for p in self.health_profiles.values()),
            'total_failed_checks': sum(p.failed_checks for p in self.health_profiles.values()),
            'active_alerts': len(self.active_alerts),
            'total_alerts_generated': len(self.alert_history),
            'check_interval_seconds': self.check_interval,
            'prediction_enabled': self.failure_prediction_enabled,
            'alert_callbacks_registered': len(self.alert_callbacks)
        }
