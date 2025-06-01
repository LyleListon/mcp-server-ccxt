"""
Performance Monitor - Real-time Resource Utilization Tracking for MayArbi System

Monitors performance across all resource types (CPU, Memory, Network, Storage),
detects bottlenecks, analyzes trends, and provides optimization recommendations
for all system components.
"""

import asyncio
import logging
import time
import psutil
import statistics
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
from collections import deque, defaultdict
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

logger = logging.getLogger(__name__)


class PerformanceLevel(Enum):
    """Performance level classifications."""
    EXCELLENT = 5    # >95% efficiency
    GOOD = 4        # 85-95% efficiency
    AVERAGE = 3     # 70-85% efficiency
    POOR = 2        # 50-70% efficiency
    CRITICAL = 1    # <50% efficiency


class BottleneckType(Enum):
    """Types of performance bottlenecks."""
    CPU_BOUND = "cpu_bound"
    MEMORY_BOUND = "memory_bound"
    NETWORK_BOUND = "network_bound"
    STORAGE_BOUND = "storage_bound"
    MIXED = "mixed"
    NONE = "none"


class TrendDirection(Enum):
    """Performance trend directions."""
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    VOLATILE = "volatile"


class OptimizationType(Enum):
    """Types of optimization recommendations."""
    RESOURCE_REALLOCATION = "resource_reallocation"
    SCALING_ADJUSTMENT = "scaling_adjustment"
    CONFIGURATION_TUNING = "configuration_tuning"
    WORKLOAD_BALANCING = "workload_balancing"
    CLEANUP_REQUIRED = "cleanup_required"


@dataclass
class PerformanceTarget:
    """Performance targets for a component."""
    component: str
    
    # Resource utilization targets (percentages)
    target_cpu_utilization: float = 70.0
    max_cpu_utilization: float = 85.0
    target_memory_utilization: float = 75.0
    max_memory_utilization: float = 90.0
    target_network_utilization: float = 60.0
    max_network_utilization: float = 80.0
    target_storage_utilization: float = 70.0
    max_storage_utilization: float = 85.0
    
    # Performance thresholds
    min_throughput_ops_sec: float = 10.0
    max_latency_ms: float = 1000.0
    min_success_rate: float = 95.0
    
    # Efficiency targets
    target_efficiency: float = 85.0
    min_efficiency: float = 70.0
    
    # Monitoring settings
    enable_trend_analysis: bool = True
    enable_bottleneck_detection: bool = True
    enable_optimization_recommendations: bool = True


@dataclass
class PerformanceMetrics:
    """Real-time performance metrics for a component."""
    component: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Resource utilization (percentages)
    cpu_utilization: float = 0.0
    memory_utilization: float = 0.0
    network_utilization: float = 0.0
    storage_utilization: float = 0.0
    
    # Performance metrics
    throughput_ops_sec: float = 0.0
    latency_ms: float = 0.0
    success_rate: float = 100.0
    error_rate: float = 0.0
    
    # Efficiency metrics
    overall_efficiency: float = 0.0
    resource_efficiency: float = 0.0
    performance_score: float = 0.0
    
    # Bottleneck analysis
    primary_bottleneck: BottleneckType = BottleneckType.NONE
    bottleneck_severity: float = 0.0
    
    # Trend analysis
    trend_direction: TrendDirection = TrendDirection.STABLE
    trend_strength: float = 0.0
    
    # Health indicators
    performance_level: PerformanceLevel = PerformanceLevel.GOOD
    health_score: float = 85.0


@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation."""
    component: str
    optimization_type: OptimizationType
    priority: int  # 1-10, 10 being highest
    title: str
    description: str
    expected_improvement: float  # Expected percentage improvement
    implementation_effort: str  # "low", "medium", "high"
    estimated_impact: str  # "low", "medium", "high"
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PerformanceAlert:
    """Performance-related alert."""
    component: str
    alert_type: str
    severity: str
    message: str
    performance_level: PerformanceLevel
    bottleneck_type: Optional[BottleneckType] = None
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False


@dataclass
class PerformanceConfig:
    """Configuration for performance monitoring."""
    # Monitoring settings
    monitoring_interval: int = 15  # seconds
    metrics_retention_hours: int = 48
    trend_analysis_window_minutes: int = 30
    
    # Performance thresholds
    efficiency_warning_threshold: float = 75.0
    efficiency_critical_threshold: float = 60.0
    bottleneck_detection_threshold: float = 80.0
    
    # Trend analysis settings
    enable_trend_prediction: bool = True
    trend_analysis_points: int = 20
    trend_significance_threshold: float = 5.0  # Minimum % change to be significant
    
    # Optimization settings
    enable_auto_optimization: bool = False
    optimization_recommendation_interval: int = 300  # 5 minutes
    max_recommendations_per_component: int = 5
    
    # Alert settings
    alert_cooldown_minutes: int = 15
    max_alerts_per_hour: int = 10
    
    # Analysis settings
    enable_cross_component_analysis: bool = True
    enable_predictive_analysis: bool = True
    correlation_analysis_window: int = 100  # data points


class PerformanceMonitor:
    """
    Performance Monitor - Real-time resource utilization tracking and optimization.
    
    Monitors performance across all resource types, detects bottlenecks,
    analyzes trends, and provides optimization recommendations.
    """
    
    def __init__(self, config: Optional[PerformanceConfig] = None):
        self.config = config or PerformanceConfig()
        self.running = False
        
        # Performance tracking
        self.component_targets: Dict[str, PerformanceTarget] = {}
        self.current_metrics: Dict[str, PerformanceMetrics] = {}
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Trend analysis
        self.trend_data: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(lambda: deque(maxlen=100)))
        self.performance_trends: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Bottleneck detection
        self.bottleneck_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self.bottleneck_patterns: Dict[str, Dict[BottleneckType, int]] = defaultdict(lambda: defaultdict(int))
        
        # Optimization recommendations
        self.active_recommendations: Dict[str, List[OptimizationRecommendation]] = defaultdict(list)
        self.recommendation_history: deque = deque(maxlen=1000)
        
        # Cross-component analysis
        self.component_correlations: Dict[Tuple[str, str], float] = {}
        self.system_performance_score: float = 85.0
        self.system_bottlenecks: List[Tuple[str, BottleneckType, float]] = []
        
        # Alerts
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        
        # Monitoring tasks
        self.monitoring_tasks: List[asyncio.Task] = []
        
        # State persistence
        self.state_file = Path("data/performance_monitor_state.json")
        self.state_file.parent.mkdir(exist_ok=True)
        
        # Initialize component targets
        self._initialize_performance_targets()
        
        logger.info("📊 Performance Monitor initialized")
    
    def _initialize_performance_targets(self):
        """Initialize performance targets for system components."""
        default_targets = {
            "arbitrage_engine": PerformanceTarget(
                component="arbitrage_engine",
                target_cpu_utilization=75.0,
                max_cpu_utilization=90.0,
                target_memory_utilization=70.0,
                max_memory_utilization=85.0,
                target_network_utilization=65.0,
                max_network_utilization=85.0,
                target_storage_utilization=60.0,
                max_storage_utilization=80.0,
                min_throughput_ops_sec=20.0,
                max_latency_ms=500.0,
                min_success_rate=98.0,
                target_efficiency=90.0,
                min_efficiency=80.0
            ),
            "bridge_monitor": PerformanceTarget(
                component="bridge_monitor",
                target_cpu_utilization=50.0,
                max_cpu_utilization=70.0,
                target_memory_utilization=60.0,
                max_memory_utilization=80.0,
                target_network_utilization=70.0,
                max_network_utilization=85.0,
                target_storage_utilization=40.0,
                max_storage_utilization=60.0,
                min_throughput_ops_sec=15.0,
                max_latency_ms=1000.0,
                min_success_rate=95.0,
                target_efficiency=85.0,
                min_efficiency=75.0
            ),
            "cross_chain_mev": PerformanceTarget(
                component="cross_chain_mev",
                target_cpu_utilization=70.0,
                max_cpu_utilization=85.0,
                target_memory_utilization=65.0,
                max_memory_utilization=85.0,
                target_network_utilization=75.0,
                max_network_utilization=90.0,
                target_storage_utilization=55.0,
                max_storage_utilization=75.0,
                min_throughput_ops_sec=12.0,
                max_latency_ms=800.0,
                min_success_rate=96.0,
                target_efficiency=87.0,
                min_efficiency=77.0
            ),
            "price_feeds": PerformanceTarget(
                component="price_feeds",
                target_cpu_utilization=60.0,
                max_cpu_utilization=80.0,
                target_memory_utilization=70.0,
                max_memory_utilization=90.0,
                target_network_utilization=80.0,
                max_network_utilization=95.0,
                target_storage_utilization=75.0,
                max_storage_utilization=90.0,
                min_throughput_ops_sec=50.0,
                max_latency_ms=200.0,
                min_success_rate=99.0,
                target_efficiency=88.0,
                min_efficiency=78.0
            ),
            "wallet_manager": PerformanceTarget(
                component="wallet_manager",
                target_cpu_utilization=40.0,
                max_cpu_utilization=60.0,
                target_memory_utilization=50.0,
                max_memory_utilization=70.0,
                target_network_utilization=30.0,
                max_network_utilization=50.0,
                target_storage_utilization=30.0,
                max_storage_utilization=50.0,
                min_throughput_ops_sec=5.0,
                max_latency_ms=2000.0,
                min_success_rate=99.5,
                target_efficiency=85.0,
                min_efficiency=75.0
            ),
            "memory_system": PerformanceTarget(
                component="memory_system",
                target_cpu_utilization=45.0,
                max_cpu_utilization=65.0,
                target_memory_utilization=80.0,
                max_memory_utilization=95.0,
                target_network_utilization=40.0,
                max_network_utilization=60.0,
                target_storage_utilization=85.0,
                max_storage_utilization=95.0,
                min_throughput_ops_sec=25.0,
                max_latency_ms=300.0,
                min_success_rate=97.0,
                target_efficiency=83.0,
                min_efficiency=73.0
            ),
            "health_monitor": PerformanceTarget(
                component="health_monitor",
                target_cpu_utilization=20.0,
                max_cpu_utilization=40.0,
                target_memory_utilization=30.0,
                max_memory_utilization=50.0,
                target_network_utilization=15.0,
                max_network_utilization=30.0,
                target_storage_utilization=20.0,
                max_storage_utilization=40.0,
                min_throughput_ops_sec=10.0,
                max_latency_ms=1500.0,
                min_success_rate=95.0,
                target_efficiency=80.0,
                min_efficiency=70.0
            )
        }
        
        self.component_targets.update(default_targets)
        logger.debug(f"Initialized performance targets for {len(default_targets)} components")

    async def start_performance_monitoring(self):
        """Start the performance monitoring system."""
        if self.running:
            logger.warning("Performance monitoring already running")
            return

        self.running = True
        logger.info("🚀 Starting Performance Monitoring System")

        # Load previous state
        await self._load_state()

        # Initialize metrics collection
        await self._initialize_metrics_collection()

        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._performance_monitor_loop()),
            asyncio.create_task(self._trend_analysis_loop()),
            asyncio.create_task(self._bottleneck_detection_loop()),
            asyncio.create_task(self._optimization_loop())
        ]

        logger.info("✅ Performance Monitoring System started")

    async def stop_performance_monitoring(self):
        """Stop the performance monitoring system."""
        if not self.running:
            return

        self.running = False
        logger.info("🛑 Stopping Performance Monitoring System")

        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

        # Save state
        await self._save_state()

        logger.info("✅ Performance Monitoring System stopped")

    async def _initialize_metrics_collection(self):
        """Initialize metrics collection for all components."""
        try:
            for component in self.component_targets:
                self.current_metrics[component] = PerformanceMetrics(component=component)

            logger.info(f"Initialized metrics collection for {len(self.component_targets)} components")

        except Exception as e:
            logger.error(f"Error initializing metrics collection: {e}")

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics for all components."""
        try:
            # Update current metrics
            await self._collect_system_metrics()

            # Calculate system-wide metrics
            system_metrics = await self._calculate_system_metrics()

            # Component metrics
            component_metrics = {}
            for component, metrics in self.current_metrics.items():
                target = self.component_targets.get(component)

                component_metrics[component] = {
                    'timestamp': metrics.timestamp.isoformat(),
                    'resource_utilization': {
                        'cpu': metrics.cpu_utilization,
                        'memory': metrics.memory_utilization,
                        'network': metrics.network_utilization,
                        'storage': metrics.storage_utilization
                    },
                    'performance': {
                        'throughput_ops_sec': metrics.throughput_ops_sec,
                        'latency_ms': metrics.latency_ms,
                        'success_rate': metrics.success_rate,
                        'error_rate': metrics.error_rate
                    },
                    'efficiency': {
                        'overall_efficiency': metrics.overall_efficiency,
                        'resource_efficiency': metrics.resource_efficiency,
                        'performance_score': metrics.performance_score
                    },
                    'analysis': {
                        'primary_bottleneck': metrics.primary_bottleneck.value,
                        'bottleneck_severity': metrics.bottleneck_severity,
                        'trend_direction': metrics.trend_direction.value,
                        'trend_strength': metrics.trend_strength,
                        'performance_level': metrics.performance_level.value,
                        'health_score': metrics.health_score
                    },
                    'targets': {
                        'target_efficiency': target.target_efficiency if target else 85.0,
                        'min_efficiency': target.min_efficiency if target else 70.0,
                        'max_latency_ms': target.max_latency_ms if target else 1000.0,
                        'min_success_rate': target.min_success_rate if target else 95.0
                    } if target else {}
                }

            return {
                'timestamp': datetime.now().isoformat(),
                'system_metrics': system_metrics,
                'component_metrics': component_metrics,
                'active_alerts': len([a for a in self.active_alerts.values() if not a.resolved]),
                'active_recommendations': sum(len(recs) for recs in self.active_recommendations.values()),
                'system_performance_score': self.system_performance_score
            }

        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}

    async def _collect_system_metrics(self):
        """Collect system-wide performance metrics."""
        try:
            # Get system resource usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Network stats (if available)
            try:
                net_io = psutil.net_io_counters()
                network_utilization = 0.0  # Placeholder - would need baseline for calculation
            except:
                network_utilization = 0.0

            # Update component metrics with system data
            for component, metrics in self.current_metrics.items():
                # For now, distribute system usage across components
                # In a real implementation, this would be component-specific
                target = self.component_targets.get(component)
                if target:
                    # Estimate component resource usage based on targets and system load
                    metrics.cpu_utilization = min(cpu_percent * (target.target_cpu_utilization / 100), 100.0)
                    metrics.memory_utilization = min(memory.percent * (target.target_memory_utilization / 100), 100.0)
                    metrics.network_utilization = min(network_utilization * (target.target_network_utilization / 100), 100.0)
                    metrics.storage_utilization = min((disk.used / disk.total) * 100 * (target.target_storage_utilization / 100), 100.0)

                    # Calculate efficiency metrics
                    await self._calculate_efficiency_metrics(component, metrics, target)

                    # Update timestamp
                    metrics.timestamp = datetime.now()

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    async def _calculate_efficiency_metrics(self, component: str, metrics: PerformanceMetrics, target: PerformanceTarget):
        """Calculate efficiency metrics for a component."""
        try:
            # Resource efficiency (how well resources are utilized vs targets)
            cpu_efficiency = min(metrics.cpu_utilization / target.target_cpu_utilization, 1.0) * 100
            memory_efficiency = min(metrics.memory_utilization / target.target_memory_utilization, 1.0) * 100
            network_efficiency = min(metrics.network_utilization / target.target_network_utilization, 1.0) * 100
            storage_efficiency = min(metrics.storage_utilization / target.target_storage_utilization, 1.0) * 100

            metrics.resource_efficiency = statistics.mean([
                cpu_efficiency, memory_efficiency, network_efficiency, storage_efficiency
            ])

            # Performance efficiency (meeting performance targets)
            throughput_efficiency = min(metrics.throughput_ops_sec / target.min_throughput_ops_sec, 1.0) * 100
            latency_efficiency = max(0, (target.max_latency_ms - metrics.latency_ms) / target.max_latency_ms) * 100
            success_rate_efficiency = min(metrics.success_rate / target.min_success_rate, 1.0) * 100

            performance_efficiency = statistics.mean([
                throughput_efficiency, latency_efficiency, success_rate_efficiency
            ])

            # Overall efficiency
            metrics.overall_efficiency = statistics.mean([
                metrics.resource_efficiency, performance_efficiency
            ])

            # Performance score (0-100)
            metrics.performance_score = min(metrics.overall_efficiency, 100.0)

            # Health score (weighted combination)
            metrics.health_score = (
                metrics.overall_efficiency * 0.4 +
                success_rate_efficiency * 0.3 +
                (100 - metrics.bottleneck_severity) * 0.2 +
                (100 if metrics.trend_direction != TrendDirection.DEGRADING else 80) * 0.1
            )

            # Determine performance level
            if metrics.overall_efficiency >= 95:
                metrics.performance_level = PerformanceLevel.EXCELLENT
            elif metrics.overall_efficiency >= 85:
                metrics.performance_level = PerformanceLevel.GOOD
            elif metrics.overall_efficiency >= 70:
                metrics.performance_level = PerformanceLevel.AVERAGE
            elif metrics.overall_efficiency >= 50:
                metrics.performance_level = PerformanceLevel.POOR
            else:
                metrics.performance_level = PerformanceLevel.CRITICAL

        except Exception as e:
            logger.error(f"Error calculating efficiency metrics for {component}: {e}")

    async def _calculate_system_metrics(self) -> Dict[str, Any]:
        """Calculate system-wide performance metrics."""
        try:
            if not self.current_metrics:
                return {}

            # Aggregate component metrics
            total_efficiency = statistics.mean([m.overall_efficiency for m in self.current_metrics.values()])
            total_health = statistics.mean([m.health_score for m in self.current_metrics.values()])

            # Resource utilization averages
            avg_cpu = statistics.mean([m.cpu_utilization for m in self.current_metrics.values()])
            avg_memory = statistics.mean([m.memory_utilization for m in self.current_metrics.values()])
            avg_network = statistics.mean([m.network_utilization for m in self.current_metrics.values()])
            avg_storage = statistics.mean([m.storage_utilization for m in self.current_metrics.values()])

            # Performance averages
            avg_throughput = statistics.mean([m.throughput_ops_sec for m in self.current_metrics.values()])
            avg_latency = statistics.mean([m.latency_ms for m in self.current_metrics.values()])
            avg_success_rate = statistics.mean([m.success_rate for m in self.current_metrics.values()])

            # Bottleneck analysis
            bottleneck_counts = defaultdict(int)
            for metrics in self.current_metrics.values():
                bottleneck_counts[metrics.primary_bottleneck] += 1

            primary_system_bottleneck = max(bottleneck_counts.items(), key=lambda x: x[1])[0] if bottleneck_counts else BottleneckType.NONE

            # Update system performance score
            self.system_performance_score = total_efficiency

            return {
                'overall_efficiency': total_efficiency,
                'health_score': total_health,
                'resource_utilization': {
                    'cpu': avg_cpu,
                    'memory': avg_memory,
                    'network': avg_network,
                    'storage': avg_storage
                },
                'performance': {
                    'throughput_ops_sec': avg_throughput,
                    'latency_ms': avg_latency,
                    'success_rate': avg_success_rate
                },
                'bottleneck_analysis': {
                    'primary_bottleneck': primary_system_bottleneck.value,
                    'bottleneck_distribution': {bt.value: count for bt, count in bottleneck_counts.items()}
                },
                'component_count': len(self.current_metrics),
                'components_healthy': len([m for m in self.current_metrics.values() if m.performance_level.value >= 3]),
                'components_critical': len([m for m in self.current_metrics.values() if m.performance_level == PerformanceLevel.CRITICAL])
            }

        except Exception as e:
            logger.error(f"Error calculating system metrics: {e}")
            return {}

    async def _performance_monitor_loop(self):
        """Main performance monitoring loop."""
        while self.running:
            try:
                # Collect current metrics
                metrics = await self.get_performance_metrics()

                # Store metrics history
                for component, component_metrics in metrics.get('component_metrics', {}).items():
                    self.metrics_history[component].append({
                        'timestamp': datetime.now(),
                        'metrics': component_metrics
                    })

                # Check for performance alerts
                await self._check_performance_alerts()

                # Update bottleneck detection
                await self._update_bottleneck_detection()

                await asyncio.sleep(self.config.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance monitor loop: {e}")
                await asyncio.sleep(30)

    async def _trend_analysis_loop(self):
        """Trend analysis loop."""
        while self.running:
            try:
                # Analyze performance trends
                await self._analyze_performance_trends()

                # Update trend predictions
                if self.config.enable_trend_prediction:
                    await self._predict_performance_trends()

                # Cross-component correlation analysis
                if self.config.enable_cross_component_analysis:
                    await self._analyze_component_correlations()

                await asyncio.sleep(self.config.trend_analysis_window_minutes * 60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in trend analysis loop: {e}")
                await asyncio.sleep(300)

    async def _bottleneck_detection_loop(self):
        """Bottleneck detection loop."""
        while self.running:
            try:
                # Detect current bottlenecks
                await self._detect_bottlenecks()

                # Analyze bottleneck patterns
                await self._analyze_bottleneck_patterns()

                # Update system bottlenecks
                await self._update_system_bottlenecks()

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in bottleneck detection loop: {e}")
                await asyncio.sleep(120)

    async def _optimization_loop(self):
        """Performance optimization loop."""
        while self.running:
            try:
                # Generate optimization recommendations
                await self._generate_optimization_recommendations()

                # Clean up old recommendations
                await self._cleanup_old_recommendations()

                # Auto-optimization if enabled
                if self.config.enable_auto_optimization:
                    await self._apply_auto_optimizations()

                await asyncio.sleep(self.config.optimization_recommendation_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(300)

    async def _detect_bottlenecks(self):
        """Detect performance bottlenecks for each component."""
        try:
            for component, metrics in self.current_metrics.items():
                target = self.component_targets.get(component)
                if not target:
                    continue

                # Check each resource type for bottlenecks
                bottleneck_scores = {
                    BottleneckType.CPU_BOUND: metrics.cpu_utilization,
                    BottleneckType.MEMORY_BOUND: metrics.memory_utilization,
                    BottleneckType.NETWORK_BOUND: metrics.network_utilization,
                    BottleneckType.STORAGE_BOUND: metrics.storage_utilization
                }

                # Find primary bottleneck
                max_bottleneck = max(bottleneck_scores.items(), key=lambda x: x[1])

                if max_bottleneck[1] > self.config.bottleneck_detection_threshold:
                    metrics.primary_bottleneck = max_bottleneck[0]
                    metrics.bottleneck_severity = max_bottleneck[1]

                    # Check for mixed bottlenecks
                    high_utilization_count = sum(1 for score in bottleneck_scores.values()
                                               if score > self.config.bottleneck_detection_threshold)
                    if high_utilization_count > 1:
                        metrics.primary_bottleneck = BottleneckType.MIXED
                        metrics.bottleneck_severity = statistics.mean([
                            score for score in bottleneck_scores.values()
                            if score > self.config.bottleneck_detection_threshold
                        ])
                else:
                    metrics.primary_bottleneck = BottleneckType.NONE
                    metrics.bottleneck_severity = 0.0

                # Record bottleneck history
                self.bottleneck_history[component].append({
                    'timestamp': datetime.now(),
                    'bottleneck_type': metrics.primary_bottleneck,
                    'severity': metrics.bottleneck_severity
                })

                # Update bottleneck patterns
                self.bottleneck_patterns[component][metrics.primary_bottleneck] += 1

        except Exception as e:
            logger.error(f"Error detecting bottlenecks: {e}")

    async def _analyze_performance_trends(self):
        """Analyze performance trends for each component."""
        try:
            for component, history in self.metrics_history.items():
                if len(history) < self.config.trend_analysis_points:
                    continue

                # Get recent efficiency data
                recent_data = list(history)[-self.config.trend_analysis_points:]
                efficiency_values = [
                    entry['metrics']['efficiency']['overall_efficiency']
                    for entry in recent_data
                ]

                # Calculate trend
                if len(efficiency_values) >= 3:
                    # Simple linear trend analysis
                    # Simple slope calculation (fallback if numpy not available)
                    slope = (efficiency_values[-1] - efficiency_values[0]) / len(efficiency_values)

                    # Determine trend direction and strength
                    if abs(slope) < self.config.trend_significance_threshold:
                        trend_direction = TrendDirection.STABLE
                        trend_strength = 0.0
                    elif slope > 0:
                        trend_direction = TrendDirection.IMPROVING
                        trend_strength = min(abs(slope), 100.0)
                    else:
                        trend_direction = TrendDirection.DEGRADING
                        trend_strength = min(abs(slope), 100.0)

                    # Check for volatility
                    if len(efficiency_values) > 5:
                        volatility = statistics.stdev(efficiency_values)
                        if volatility > 15.0:  # High volatility threshold
                            trend_direction = TrendDirection.VOLATILE
                            trend_strength = volatility

                    # Update component metrics
                    if component in self.current_metrics:
                        self.current_metrics[component].trend_direction = trend_direction
                        self.current_metrics[component].trend_strength = trend_strength

                    # Store trend data
                    self.performance_trends[component]['direction'] = trend_direction.value
                    self.performance_trends[component]['strength'] = trend_strength
                    self.performance_trends[component]['slope'] = slope

        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")

    async def _generate_optimization_recommendations(self):
        """Generate optimization recommendations for components."""
        try:
            for component, metrics in self.current_metrics.items():
                target = self.component_targets.get(component)
                if not target:
                    continue

                recommendations = []

                # Check efficiency-based recommendations
                if metrics.overall_efficiency < target.min_efficiency:
                    if metrics.primary_bottleneck == BottleneckType.CPU_BOUND:
                        recommendations.append(OptimizationRecommendation(
                            component=component,
                            optimization_type=OptimizationType.RESOURCE_REALLOCATION,
                            priority=8,
                            title="CPU Resource Reallocation",
                            description=f"CPU utilization at {metrics.cpu_utilization:.1f}%. Consider increasing CPU allocation or optimizing CPU-intensive operations.",
                            expected_improvement=15.0,
                            implementation_effort="medium",
                            estimated_impact="high"
                        ))

                    elif metrics.primary_bottleneck == BottleneckType.MEMORY_BOUND:
                        recommendations.append(OptimizationRecommendation(
                            component=component,
                            optimization_type=OptimizationType.CLEANUP_REQUIRED,
                            priority=7,
                            title="Memory Optimization",
                            description=f"Memory utilization at {metrics.memory_utilization:.1f}%. Consider memory cleanup or increasing allocation.",
                            expected_improvement=12.0,
                            implementation_effort="low",
                            estimated_impact="medium"
                        ))

                # Check trend-based recommendations
                if metrics.trend_direction == TrendDirection.DEGRADING:
                    recommendations.append(OptimizationRecommendation(
                        component=component,
                        optimization_type=OptimizationType.CONFIGURATION_TUNING,
                        priority=6,
                        title="Performance Degradation",
                        description=f"Performance trending downward. Review recent changes and configuration.",
                        expected_improvement=10.0,
                        implementation_effort="medium",
                        estimated_impact="medium"
                    ))

                # Limit recommendations per component
                recommendations = sorted(recommendations, key=lambda x: x.priority, reverse=True)
                recommendations = recommendations[:self.config.max_recommendations_per_component]

                # Update active recommendations
                self.active_recommendations[component] = recommendations

                # Add to history
                for rec in recommendations:
                    self.recommendation_history.append(rec)

        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")

    # Placeholder methods for monitoring loops (to be implemented)
    async def _check_performance_alerts(self):
        """Check for performance-related alerts."""
        try:
            for component, metrics in self.current_metrics.items():
                target = self.component_targets.get(component)
                if not target:
                    continue

                # Check efficiency alerts
                if metrics.overall_efficiency < self.config.efficiency_critical_threshold:
                    await self._create_performance_alert(
                        component, "efficiency_critical", "critical",
                        f"Performance efficiency critical: {metrics.overall_efficiency:.1f}%",
                        metrics.performance_level, metrics.primary_bottleneck
                    )
                elif metrics.overall_efficiency < self.config.efficiency_warning_threshold:
                    await self._create_performance_alert(
                        component, "efficiency_warning", "warning",
                        f"Performance efficiency low: {metrics.overall_efficiency:.1f}%",
                        metrics.performance_level, metrics.primary_bottleneck
                    )

                # Check bottleneck alerts
                if metrics.bottleneck_severity > self.config.bottleneck_detection_threshold:
                    await self._create_performance_alert(
                        component, "bottleneck_detected", "warning",
                        f"Performance bottleneck detected: {metrics.primary_bottleneck.value} ({metrics.bottleneck_severity:.1f}%)",
                        metrics.performance_level, metrics.primary_bottleneck
                    )
        except Exception as e:
            logger.error(f"Error checking performance alerts: {e}")

    async def _create_performance_alert(self, component: str, alert_type: str, severity: str,
                                      message: str, performance_level: PerformanceLevel,
                                      bottleneck_type: Optional[BottleneckType]):
        """Create a performance alert."""
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
            alert = PerformanceAlert(
                component=component,
                alert_type=alert_type,
                severity=severity,
                message=message,
                performance_level=performance_level,
                bottleneck_type=bottleneck_type
            )

            self.active_alerts[alert_key] = alert
            self.alert_history.append(alert)

            logger.warning(f"Performance Alert [{severity.upper()}] {component}: {message}")

        except Exception as e:
            logger.error(f"Error creating performance alert: {e}")

    async def _update_bottleneck_detection(self):
        """Update bottleneck detection data."""
        try:
            # This is handled in _detect_bottlenecks method
            pass
        except Exception as e:
            logger.error(f"Error updating bottleneck detection: {e}")

    async def _predict_performance_trends(self):
        """Predict future performance trends."""
        try:
            # Placeholder for trend prediction
            pass
        except Exception as e:
            logger.error(f"Error predicting performance trends: {e}")

    async def _analyze_component_correlations(self):
        """Analyze correlations between component performance."""
        try:
            # Placeholder for correlation analysis
            pass
        except Exception as e:
            logger.error(f"Error analyzing component correlations: {e}")

    async def _analyze_bottleneck_patterns(self):
        """Analyze bottleneck patterns."""
        try:
            # Placeholder for bottleneck pattern analysis
            pass
        except Exception as e:
            logger.error(f"Error analyzing bottleneck patterns: {e}")

    async def _update_system_bottlenecks(self):
        """Update system-wide bottleneck analysis."""
        try:
            # Collect current bottlenecks
            current_bottlenecks = []
            for component, metrics in self.current_metrics.items():
                if metrics.primary_bottleneck != BottleneckType.NONE:
                    current_bottlenecks.append((component, metrics.primary_bottleneck, metrics.bottleneck_severity))

            # Sort by severity
            current_bottlenecks.sort(key=lambda x: x[2], reverse=True)
            self.system_bottlenecks = current_bottlenecks[:5]  # Top 5 bottlenecks

        except Exception as e:
            logger.error(f"Error updating system bottlenecks: {e}")

    async def _cleanup_old_recommendations(self):
        """Clean up old optimization recommendations."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)

            # Clean up recommendation history
            while (self.recommendation_history and
                   self.recommendation_history[0].timestamp < cutoff_time):
                self.recommendation_history.popleft()

            # Clean up active recommendations older than 1 hour
            active_cutoff = datetime.now() - timedelta(hours=1)
            for component in self.active_recommendations:
                self.active_recommendations[component] = [
                    rec for rec in self.active_recommendations[component]
                    if rec.timestamp > active_cutoff
                ]
        except Exception as e:
            logger.error(f"Error cleaning up old recommendations: {e}")

    async def _apply_auto_optimizations(self):
        """Apply automatic optimizations if enabled."""
        try:
            # Placeholder for auto-optimization
            # This would implement safe, automatic optimizations
            pass
        except Exception as e:
            logger.error(f"Error applying auto optimizations: {e}")

    async def _load_state(self):
        """Load previous state from disk."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)

                # Restore performance trends
                if 'performance_trends' in state:
                    for component, trends in state['performance_trends'].items():
                        self.performance_trends[component].update(trends)

                # Restore metrics history
                if 'metrics_history' in state:
                    for component, history in state['metrics_history'].items():
                        for entry in history[-100:]:  # Last 100 entries
                            entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                            self.metrics_history[component].append(entry)

                logger.info("Performance monitor state loaded")

        except Exception as e:
            logger.error(f"Error loading state: {e}")

    async def _save_state(self):
        """Save current state to disk."""
        try:
            state = {
                'performance_trends': dict(self.performance_trends),
                'metrics_history': {
                    component: [
                        {
                            'timestamp': entry['timestamp'].isoformat(),
                            'metrics': entry['metrics']
                        }
                        for entry in list(history)[-100:]  # Last 100 entries
                    ]
                    for component, history in self.metrics_history.items()
                },
                'system_performance_score': self.system_performance_score,
                'bottleneck_patterns': {
                    component: {bt.value: count for bt, count in patterns.items()}
                    for component, patterns in self.bottleneck_patterns.items()
                }
            }

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

            logger.debug("Performance monitor state saved")

        except Exception as e:
            logger.error(f"Error saving state: {e}")

    async def get_performance_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive performance data for dashboard display."""
        try:
            metrics = await self.get_performance_metrics()

            # Get recent recommendations
            recent_recommendations = []
            for component_recs in self.active_recommendations.values():
                recent_recommendations.extend(component_recs)
            recent_recommendations.sort(key=lambda x: x.priority, reverse=True)
            recent_recommendations = recent_recommendations[:10]  # Top 10

            # System bottlenecks
            system_bottlenecks = [
                {
                    'component': component,
                    'bottleneck_type': bottleneck_type.value,
                    'severity': severity
                }
                for component, bottleneck_type, severity in self.system_bottlenecks
            ]

            return {
                'timestamp': datetime.now().isoformat(),
                'system_metrics': metrics.get('system_metrics', {}),
                'component_metrics': metrics.get('component_metrics', {}),
                'system_performance_score': self.system_performance_score,
                'active_alerts': len([a for a in self.active_alerts.values() if not a.resolved]),
                'recent_recommendations': [
                    {
                        'component': rec.component,
                        'title': rec.title,
                        'priority': rec.priority,
                        'optimization_type': rec.optimization_type.value,
                        'expected_improvement': rec.expected_improvement,
                        'implementation_effort': rec.implementation_effort
                    }
                    for rec in recent_recommendations
                ],
                'system_bottlenecks': system_bottlenecks,
                'performance_trends': dict(self.performance_trends)
            }

        except Exception as e:
            logger.error(f"Error getting performance dashboard data: {e}")
            return {}
