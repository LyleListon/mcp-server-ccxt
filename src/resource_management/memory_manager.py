"""
Memory Manager - Specialized Memory Usage Optimization and Management

This module provides comprehensive memory resource management for the MayArbi arbitrage system,
including memory monitoring, garbage collection optimization, memory leak detection, allocation
limits, cleanup policies, and memory pressure management.
"""

import asyncio
import logging
import psutil
import gc
import sys
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import statistics
from collections import deque, defaultdict
import tracemalloc

logger = logging.getLogger(__name__)


class MemoryPriority(Enum):
    """Memory priority levels for components."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class MemoryCleanupStrategy(Enum):
    """Memory cleanup strategies."""
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    ADAPTIVE = "adaptive"
    MANUAL = "manual"


class MemoryPressureLevel(Enum):
    """Memory pressure levels."""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MemoryMetrics:
    """Detailed memory metrics for a component."""
    component: str
    memory_usage_mb: float
    memory_percent: float
    peak_memory_mb: float
    allocated_objects: int
    memory_growth_rate: float  # MB per minute
    gc_collections: int
    memory_leaks_detected: int
    cache_size_mb: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'component': self.component,
            'memory_usage_mb': self.memory_usage_mb,
            'memory_percent': self.memory_percent,
            'peak_memory_mb': self.peak_memory_mb,
            'allocated_objects': self.allocated_objects,
            'memory_growth_rate': self.memory_growth_rate,
            'gc_collections': self.gc_collections,
            'memory_leaks_detected': self.memory_leaks_detected,
            'cache_size_mb': self.cache_size_mb,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class MemoryAllocation:
    """Memory allocation configuration for a component."""
    component: str
    memory_limit_mb: float
    priority: MemoryPriority
    cleanup_strategy: MemoryCleanupStrategy
    enable_gc_optimization: bool = True
    gc_threshold_mb: float = 100.0
    max_cache_size_mb: float = 50.0
    leak_detection_enabled: bool = True
    auto_cleanup_enabled: bool = True


@dataclass
class MemoryConfig:
    """Configuration for memory management."""
    # Monitoring settings
    monitoring_interval: int = 15  # seconds
    metrics_retention_hours: int = 24
    
    # Memory thresholds
    memory_warning_threshold: float = 75.0
    memory_critical_threshold: float = 90.0
    memory_pressure_threshold: float = 85.0
    
    # Garbage collection
    enable_auto_gc: bool = True
    gc_interval_minutes: int = 5
    gc_pressure_threshold: float = 80.0
    aggressive_gc_threshold: float = 85.0
    
    # Memory leak detection
    enable_leak_detection: bool = True
    leak_detection_interval: int = 300  # 5 minutes
    leak_threshold_mb: float = 10.0  # MB growth without cleanup
    
    # Cleanup policies
    enable_auto_cleanup: bool = True
    cleanup_interval_minutes: int = 10
    cache_cleanup_threshold: float = 80.0
    
    # Memory optimization
    enable_memory_optimization: bool = True
    optimization_interval_minutes: int = 15
    fragmentation_threshold: float = 20.0


class MemoryManager:
    """
    Specialized Memory Manager for comprehensive memory resource management.
    
    Provides memory monitoring, garbage collection optimization, leak detection,
    and memory pressure management for all system components.
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self.running = False
        
        # Memory tracking
        self.component_allocations: Dict[str, MemoryAllocation] = {}
        self.component_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.memory_history: deque = deque(maxlen=1000)
        
        # Memory pressure tracking
        self.current_pressure_level = MemoryPressureLevel.NONE
        self.pressure_history: deque = deque(maxlen=100)
        
        # Garbage collection tracking
        self.gc_stats: Dict[str, Any] = {}
        self.last_gc_time = datetime.now()
        
        # Memory leak detection
        self.leak_snapshots: Dict[str, Any] = {}
        self.detected_leaks: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Cache management
        self.component_caches: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Monitoring tasks
        self.monitoring_tasks: List[asyncio.Task] = []
        
        # State persistence
        self.state_file = Path("data/memory_manager_state.json")
        self.state_file.parent.mkdir(exist_ok=True)
        
        # Initialize tracemalloc for memory tracking
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        # Initialize component allocations
        self._initialize_memory_allocations()
        
        logger.info("🧠 Memory Manager initialized")
    
    def _initialize_memory_allocations(self):
        """Initialize memory allocations for system components."""
        default_allocations = {
            "arbitrage_engine": MemoryAllocation(
                component="arbitrage_engine",
                memory_limit_mb=512.0,
                priority=MemoryPriority.HIGH,
                cleanup_strategy=MemoryCleanupStrategy.ADAPTIVE,
                enable_gc_optimization=True,
                gc_threshold_mb=100.0,
                max_cache_size_mb=100.0,
                leak_detection_enabled=True,
                auto_cleanup_enabled=True
            ),
            "bridge_monitor": MemoryAllocation(
                component="bridge_monitor",
                memory_limit_mb=256.0,
                priority=MemoryPriority.NORMAL,
                cleanup_strategy=MemoryCleanupStrategy.CONSERVATIVE,
                enable_gc_optimization=True,
                gc_threshold_mb=50.0,
                max_cache_size_mb=50.0,
                leak_detection_enabled=True,
                auto_cleanup_enabled=True
            ),
            "cross_chain_mev": MemoryAllocation(
                component="cross_chain_mev",
                memory_limit_mb=384.0,
                priority=MemoryPriority.HIGH,
                cleanup_strategy=MemoryCleanupStrategy.ADAPTIVE,
                enable_gc_optimization=True,
                gc_threshold_mb=75.0,
                max_cache_size_mb=75.0,
                leak_detection_enabled=True,
                auto_cleanup_enabled=True
            ),
            "wallet_manager": MemoryAllocation(
                component="wallet_manager",
                memory_limit_mb=128.0,
                priority=MemoryPriority.CRITICAL,
                cleanup_strategy=MemoryCleanupStrategy.CONSERVATIVE,
                enable_gc_optimization=False,  # Critical component
                gc_threshold_mb=25.0,
                max_cache_size_mb=25.0,
                leak_detection_enabled=True,
                auto_cleanup_enabled=False  # Manual cleanup for critical component
            ),
            "price_feeds": MemoryAllocation(
                component="price_feeds",
                memory_limit_mb=256.0,
                priority=MemoryPriority.NORMAL,
                cleanup_strategy=MemoryCleanupStrategy.AGGRESSIVE,
                enable_gc_optimization=True,
                gc_threshold_mb=50.0,
                max_cache_size_mb=100.0,  # Larger cache for price data
                leak_detection_enabled=True,
                auto_cleanup_enabled=True
            ),
            "memory_system": MemoryAllocation(
                component="memory_system",
                memory_limit_mb=512.0,
                priority=MemoryPriority.NORMAL,
                cleanup_strategy=MemoryCleanupStrategy.ADAPTIVE,
                enable_gc_optimization=True,
                gc_threshold_mb=100.0,
                max_cache_size_mb=200.0,  # Large cache for memory data
                leak_detection_enabled=True,
                auto_cleanup_enabled=True
            ),
            "health_monitor": MemoryAllocation(
                component="health_monitor",
                memory_limit_mb=128.0,
                priority=MemoryPriority.LOW,
                cleanup_strategy=MemoryCleanupStrategy.CONSERVATIVE,
                enable_gc_optimization=True,
                gc_threshold_mb=25.0,
                max_cache_size_mb=25.0,
                leak_detection_enabled=False,  # System component
                auto_cleanup_enabled=True
            )
        }
        
        self.component_allocations.update(default_allocations)
        logger.debug(f"Initialized memory allocations for {len(default_allocations)} components")
    
    async def start_memory_management(self):
        """Start the memory management system."""
        if self.running:
            logger.warning("Memory management already running")
            return
        
        self.running = True
        logger.info("🚀 Starting Memory Management System")
        
        # Load previous state
        await self._load_state()
        
        # Initialize garbage collection
        await self._initialize_gc_optimization()
        
        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._memory_monitor_loop()),
            asyncio.create_task(self._gc_optimization_loop()),
            asyncio.create_task(self._leak_detection_loop()),
            asyncio.create_task(self._cleanup_loop()),
            asyncio.create_task(self._pressure_management_loop())
        ]
        
        logger.info("✅ Memory Management System started")
    
    async def stop_memory_management(self):
        """Stop the memory management system."""
        if not self.running:
            return
        
        self.running = False
        logger.info("🛑 Stopping Memory Management System")
        
        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
        # Final cleanup
        await self._perform_final_cleanup()
        
        # Save state
        await self._save_state()
        
        logger.info("✅ Memory Management System stopped")

    async def get_memory_metrics(self) -> Dict[str, Any]:
        """Get comprehensive memory metrics."""
        try:
            # System memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Process memory metrics
            process = psutil.Process()
            process_memory = process.memory_info()

            # Python memory metrics
            gc_stats = gc.get_stats()

            # Tracemalloc metrics
            current, peak = tracemalloc.get_traced_memory()

            return {
                'timestamp': datetime.now().isoformat(),
                'system_memory': {
                    'total_mb': memory.total / (1024 * 1024),
                    'available_mb': memory.available / (1024 * 1024),
                    'used_mb': memory.used / (1024 * 1024),
                    'percent': memory.percent,
                    'free_mb': memory.free / (1024 * 1024)
                },
                'swap_memory': {
                    'total_mb': swap.total / (1024 * 1024),
                    'used_mb': swap.used / (1024 * 1024),
                    'percent': swap.percent
                },
                'process_memory': {
                    'rss_mb': process_memory.rss / (1024 * 1024),
                    'vms_mb': process_memory.vms / (1024 * 1024)
                },
                'python_memory': {
                    'current_mb': current / (1024 * 1024),
                    'peak_mb': peak / (1024 * 1024),
                    'gc_collections': sum(stat['collections'] for stat in gc_stats),
                    'gc_collected': sum(stat['collected'] for stat in gc_stats),
                    'gc_uncollectable': sum(stat['uncollectable'] for stat in gc_stats)
                },
                'pressure_level': self.current_pressure_level.value
            }

        except Exception as e:
            logger.error(f"Error getting memory metrics: {e}")
            return {'error': str(e)}

    async def get_component_memory_usage(self, component: str) -> Optional[MemoryMetrics]:
        """Get detailed memory usage for a specific component."""
        try:
            allocation = self.component_allocations.get(component)
            if not allocation:
                return None

            # Get current memory snapshot
            snapshot = tracemalloc.take_snapshot()

            # Calculate component memory usage (simplified estimation)
            # In a real implementation, you would track component-specific memory
            total_memory = sum(stat.size for stat in snapshot.statistics('filename'))
            estimated_component_memory = total_memory * 0.1  # Rough estimation

            # Get historical data for growth rate calculation
            historical_metrics = list(self.component_metrics[component])
            growth_rate = 0.0
            if len(historical_metrics) >= 2:
                recent = historical_metrics[-1]
                older = historical_metrics[-min(len(historical_metrics), 10)]
                time_diff = (recent.timestamp - older.timestamp).total_seconds() / 60  # minutes
                if time_diff > 0:
                    growth_rate = (recent.memory_usage_mb - older.memory_usage_mb) / time_diff

            # Get GC stats
            gc_stats = gc.get_stats()
            total_collections = sum(stat['collections'] for stat in gc_stats)

            # Detect memory leaks
            leaks_detected = len(self.detected_leaks.get(component, []))

            # Calculate cache size
            cache_size = sum(sys.getsizeof(item) for item in self.component_caches.get(component, {}).values())
            cache_size_mb = cache_size / (1024 * 1024)

            metrics = MemoryMetrics(
                component=component,
                memory_usage_mb=estimated_component_memory / (1024 * 1024),
                memory_percent=(estimated_component_memory / psutil.virtual_memory().total) * 100,
                peak_memory_mb=allocation.memory_limit_mb,  # Simplified
                allocated_objects=len(snapshot.statistics('filename')),
                memory_growth_rate=growth_rate,
                gc_collections=total_collections,
                memory_leaks_detected=leaks_detected,
                cache_size_mb=cache_size_mb
            )

            # Store metrics
            self.component_metrics[component].append(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Error getting component memory usage for {component}: {e}")
            return None

    async def _memory_monitor_loop(self):
        """Main memory monitoring loop."""
        while self.running:
            try:
                # Monitor overall memory metrics
                memory_metrics = await self.get_memory_metrics()
                self.memory_history.append(memory_metrics)

                # Monitor per-component memory usage
                for component in self.component_allocations.keys():
                    await self.get_component_memory_usage(component)

                # Update memory pressure level
                await self._update_memory_pressure()

                # Check for memory alerts
                await self._check_memory_alerts(memory_metrics)

                await asyncio.sleep(self.config.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in memory monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _gc_optimization_loop(self):
        """Garbage collection optimization loop."""
        while self.running:
            try:
                if self.config.enable_auto_gc:
                    await self._optimize_garbage_collection()

                await asyncio.sleep(self.config.gc_interval_minutes * 60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in GC optimization loop: {e}")
                await asyncio.sleep(30)

    async def _leak_detection_loop(self):
        """Memory leak detection loop."""
        while self.running:
            try:
                if self.config.enable_leak_detection:
                    await self._detect_memory_leaks()

                await asyncio.sleep(self.config.leak_detection_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in leak detection loop: {e}")
                await asyncio.sleep(60)

    async def _cleanup_loop(self):
        """Memory cleanup loop."""
        while self.running:
            try:
                if self.config.enable_auto_cleanup:
                    await self._perform_memory_cleanup()

                await asyncio.sleep(self.config.cleanup_interval_minutes * 60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(30)

    async def _pressure_management_loop(self):
        """Memory pressure management loop."""
        while self.running:
            try:
                await self._manage_memory_pressure()

                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in pressure management loop: {e}")
                await asyncio.sleep(10)

    async def _initialize_gc_optimization(self):
        """Initialize garbage collection optimization."""
        try:
            # Set GC thresholds for better performance
            gc.set_threshold(700, 10, 10)  # More aggressive collection

            # Enable GC debugging if needed
            if logger.isEnabledFor(logging.DEBUG):
                gc.set_debug(gc.DEBUG_STATS)

            logger.info("🗑️ Garbage collection optimization initialized")

        except Exception as e:
            logger.error(f"Error initializing GC optimization: {e}")

    async def _update_memory_pressure(self):
        """Update current memory pressure level."""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Determine pressure level
            if memory_percent >= 95:
                pressure_level = MemoryPressureLevel.CRITICAL
            elif memory_percent >= 90:
                pressure_level = MemoryPressureLevel.HIGH
            elif memory_percent >= 80:
                pressure_level = MemoryPressureLevel.MODERATE
            elif memory_percent >= 70:
                pressure_level = MemoryPressureLevel.LOW
            else:
                pressure_level = MemoryPressureLevel.NONE

            # Update if changed
            if pressure_level != self.current_pressure_level:
                old_level = self.current_pressure_level
                self.current_pressure_level = pressure_level

                self.pressure_history.append({
                    'timestamp': datetime.now(),
                    'level': pressure_level.value,
                    'memory_percent': memory_percent
                })

                logger.info(f"🔄 Memory pressure changed: {old_level.value} → {pressure_level.value} ({memory_percent:.1f}%)")

        except Exception as e:
            logger.error(f"Error updating memory pressure: {e}")

    async def _check_memory_alerts(self, memory_metrics: Dict[str, Any]):
        """Check for memory-related alerts."""
        try:
            system_memory = memory_metrics.get('system_memory', {})
            memory_percent = system_memory.get('percent', 0)

            # Check system memory usage
            if memory_percent > self.config.memory_critical_threshold:
                logger.warning(f"🚨 CRITICAL: System memory usage at {memory_percent:.1f}%")
            elif memory_percent > self.config.memory_warning_threshold:
                logger.warning(f"⚠️ WARNING: System memory usage at {memory_percent:.1f}%")

            # Check swap usage
            swap_memory = memory_metrics.get('swap_memory', {})
            swap_percent = swap_memory.get('percent', 0)
            if swap_percent > 50:
                logger.warning(f"⚠️ High swap usage: {swap_percent:.1f}%")

            # Check for memory leaks
            total_leaks = sum(len(leaks) for leaks in self.detected_leaks.values())
            if total_leaks > 0:
                logger.warning(f"🔍 Memory leaks detected: {total_leaks} components affected")

        except Exception as e:
            logger.error(f"Error checking memory alerts: {e}")

    async def _optimize_garbage_collection(self):
        """Optimize garbage collection based on memory pressure."""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Determine GC strategy based on memory pressure
            if memory_percent > self.config.aggressive_gc_threshold:
                # Aggressive GC
                logger.info("🗑️ Performing aggressive garbage collection")
                collected = gc.collect()
                logger.info(f"Aggressive GC collected {collected} objects")

                # Force collection of all generations
                for generation in range(3):
                    gc.collect(generation)

            elif memory_percent > self.config.gc_pressure_threshold:
                # Normal GC
                collected = gc.collect()
                if collected > 0:
                    logger.debug(f"GC collected {collected} objects")

            # Update GC stats
            self.gc_stats = {
                'last_collection': datetime.now().isoformat(),
                'memory_before': memory_percent,
                'memory_after': psutil.virtual_memory().percent,
                'objects_collected': collected if 'collected' in locals() else 0
            }

            self.last_gc_time = datetime.now()

        except Exception as e:
            logger.error(f"Error optimizing garbage collection: {e}")

    async def _detect_memory_leaks(self):
        """Detect potential memory leaks in components."""
        try:
            current_snapshot = tracemalloc.take_snapshot()
            # Note: snapshot available for future detailed leak analysis

            for component in self.component_allocations.keys():
                allocation = self.component_allocations[component]
                if not allocation.leak_detection_enabled:
                    continue

                # Get component metrics history
                metrics_history = list(self.component_metrics[component])
                if len(metrics_history) < 5:  # Need some history
                    continue

                # Check for consistent memory growth
                recent_metrics = metrics_history[-5:]
                memory_values = [m.memory_usage_mb for m in recent_metrics]

                # Calculate trend
                if len(memory_values) >= 3:
                    growth_trend = (memory_values[-1] - memory_values[0]) / len(memory_values)

                    # Detect leak if consistent growth above threshold
                    if growth_trend > self.config.leak_threshold_mb:
                        leak_info = {
                            'timestamp': datetime.now().isoformat(),
                            'component': component,
                            'growth_rate_mb': growth_trend,
                            'current_memory_mb': memory_values[-1],
                            'severity': 'high' if growth_trend > self.config.leak_threshold_mb * 2 else 'medium'
                        }

                        self.detected_leaks[component].append(leak_info)
                        logger.warning(f"🔍 Memory leak detected in {component}: {growth_trend:.2f} MB/check")

                        # Trigger cleanup if enabled
                        if allocation.auto_cleanup_enabled:
                            await self._cleanup_component_memory(component)

        except Exception as e:
            logger.error(f"Error detecting memory leaks: {e}")

    async def _perform_memory_cleanup(self):
        """Perform memory cleanup across all components."""
        try:
            logger.info("🧹 Performing memory cleanup")

            for component, allocation in self.component_allocations.items():
                if allocation.auto_cleanup_enabled:
                    await self._cleanup_component_memory(component)

            # Clean up internal data structures
            await self._cleanup_internal_memory()

            # Force garbage collection after cleanup
            collected = gc.collect()
            logger.info(f"Memory cleanup completed, GC collected {collected} objects")

        except Exception as e:
            logger.error(f"Error performing memory cleanup: {e}")

    async def _cleanup_component_memory(self, component: str):
        """Clean up memory for a specific component."""
        try:
            allocation = self.component_allocations.get(component)
            if not allocation:
                return

            # Clean component cache based on strategy
            if allocation.cleanup_strategy == MemoryCleanupStrategy.AGGRESSIVE:
                # Clear most of the cache
                cache = self.component_caches.get(component, {})
                items_to_remove = list(cache.keys())[:-10]  # Keep last 10 items
                for key in items_to_remove:
                    del cache[key]
                logger.debug(f"Aggressive cleanup for {component}: removed {len(items_to_remove)} cache items")

            elif allocation.cleanup_strategy == MemoryCleanupStrategy.ADAPTIVE:
                # Clean based on memory pressure
                if self.current_pressure_level in [MemoryPressureLevel.HIGH, MemoryPressureLevel.CRITICAL]:
                    cache = self.component_caches.get(component, {})
                    items_to_remove = list(cache.keys())[:-20]  # Keep last 20 items
                    for key in items_to_remove:
                        del cache[key]
                    logger.debug(f"Adaptive cleanup for {component}: removed {len(items_to_remove)} cache items")

            elif allocation.cleanup_strategy == MemoryCleanupStrategy.CONSERVATIVE:
                # Minimal cleanup
                cache = self.component_caches.get(component, {})
                if len(cache) > 100:  # Only clean if cache is large
                    items_to_remove = list(cache.keys())[:-50]  # Keep last 50 items
                    for key in items_to_remove:
                        del cache[key]
                    logger.debug(f"Conservative cleanup for {component}: removed {len(items_to_remove)} cache items")

            # Clear detected leaks for this component
            if component in self.detected_leaks:
                self.detected_leaks[component] = []

        except Exception as e:
            logger.error(f"Error cleaning up component memory for {component}: {e}")

    async def _cleanup_internal_memory(self):
        """Clean up internal memory manager data structures."""
        try:
            # Clean old metrics
            cutoff_time = datetime.now() - timedelta(hours=self.config.metrics_retention_hours)

            for component in self.component_metrics:
                while (self.component_metrics[component] and
                       self.component_metrics[component][0].timestamp < cutoff_time):
                    self.component_metrics[component].popleft()

            # Clean old memory history
            while (self.memory_history and
                   len(self.memory_history) > 500):  # Keep last 500 entries
                self.memory_history.popleft()

            # Clean old pressure history
            while (self.pressure_history and
                   len(self.pressure_history) > 100):  # Keep last 100 entries
                self.pressure_history.popleft()

            # Clean old leak snapshots
            old_snapshots = []
            for snapshot_id, snapshot_data in self.leak_snapshots.items():
                if 'timestamp' in snapshot_data:
                    snapshot_time = datetime.fromisoformat(snapshot_data['timestamp'])
                    if snapshot_time < cutoff_time:
                        old_snapshots.append(snapshot_id)

            for snapshot_id in old_snapshots:
                del self.leak_snapshots[snapshot_id]

        except Exception as e:
            logger.error(f"Error cleaning up internal memory: {e}")

    async def _manage_memory_pressure(self):
        """Manage system memory pressure."""
        try:
            if self.current_pressure_level == MemoryPressureLevel.CRITICAL:
                logger.warning("🚨 CRITICAL memory pressure - emergency cleanup")
                await self._emergency_memory_cleanup()

            elif self.current_pressure_level == MemoryPressureLevel.HIGH:
                logger.warning("⚠️ HIGH memory pressure - aggressive cleanup")
                await self._aggressive_memory_cleanup()

            elif self.current_pressure_level == MemoryPressureLevel.MODERATE:
                logger.info("📊 MODERATE memory pressure - standard cleanup")
                await self._standard_memory_cleanup()

        except Exception as e:
            logger.error(f"Error managing memory pressure: {e}")

    async def _emergency_memory_cleanup(self):
        """Emergency memory cleanup for critical pressure."""
        try:
            # Force aggressive cleanup on all components
            for component in self.component_allocations.keys():
                cache = self.component_caches.get(component, {})
                cache.clear()  # Clear all caches

            # Force multiple GC cycles
            for _ in range(3):
                gc.collect()

            # Clear internal data structures
            self.memory_history.clear()
            self.pressure_history = deque(maxlen=100)

            logger.warning("🚨 Emergency memory cleanup completed")

        except Exception as e:
            logger.error(f"Error in emergency memory cleanup: {e}")

    async def _aggressive_memory_cleanup(self):
        """Aggressive memory cleanup for high pressure."""
        try:
            # Clean up non-critical component caches
            for component, allocation in self.component_allocations.items():
                if allocation.priority != MemoryPriority.CRITICAL:
                    cache = self.component_caches.get(component, {})
                    items_to_remove = list(cache.keys())[:-5]  # Keep only last 5 items
                    for key in items_to_remove:
                        del cache[key]

            # Force GC
            gc.collect()

            logger.warning("⚠️ Aggressive memory cleanup completed")

        except Exception as e:
            logger.error(f"Error in aggressive memory cleanup: {e}")

    async def _standard_memory_cleanup(self):
        """Standard memory cleanup for moderate pressure."""
        try:
            # Clean up low priority component caches
            for component, allocation in self.component_allocations.items():
                if allocation.priority == MemoryPriority.LOW:
                    cache = self.component_caches.get(component, {})
                    if len(cache) > 50:
                        items_to_remove = list(cache.keys())[:-25]  # Keep last 25 items
                        for key in items_to_remove:
                            del cache[key]

            # Normal GC
            gc.collect()

            logger.info("📊 Standard memory cleanup completed")

        except Exception as e:
            logger.error(f"Error in standard memory cleanup: {e}")

    async def _perform_final_cleanup(self):
        """Perform final cleanup before shutdown."""
        try:
            logger.info("🧹 Performing final memory cleanup")

            # Clear all caches
            self.component_caches.clear()

            # Clear all internal data
            self.memory_history.clear()
            self.pressure_history.clear()
            self.detected_leaks.clear()
            self.leak_snapshots.clear()

            # Final GC
            gc.collect()

            # Stop tracemalloc
            if tracemalloc.is_tracing():
                tracemalloc.stop()

        except Exception as e:
            logger.error(f"Error in final cleanup: {e}")

    async def _save_state(self):
        """Save memory manager state to disk."""
        try:
            state = {
                'component_allocations': {
                    name: {
                        'component': alloc.component,
                        'memory_limit_mb': alloc.memory_limit_mb,
                        'priority': alloc.priority.value,
                        'cleanup_strategy': alloc.cleanup_strategy.value,
                        'enable_gc_optimization': alloc.enable_gc_optimization,
                        'gc_threshold_mb': alloc.gc_threshold_mb,
                        'max_cache_size_mb': alloc.max_cache_size_mb,
                        'leak_detection_enabled': alloc.leak_detection_enabled,
                        'auto_cleanup_enabled': alloc.auto_cleanup_enabled
                    } for name, alloc in self.component_allocations.items()
                },
                'current_pressure_level': self.current_pressure_level.value,
                'detected_leaks': {
                    component: leaks for component, leaks in self.detected_leaks.items()
                },
                'gc_stats': self.gc_stats,
                'last_save': datetime.now().isoformat()
            }

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving memory manager state: {e}")

    async def _load_state(self):
        """Load memory manager state from disk."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)

                # Load component allocations
                if 'component_allocations' in state:
                    for name, alloc_data in state['component_allocations'].items():
                        alloc_data['priority'] = MemoryPriority(alloc_data['priority'])
                        alloc_data['cleanup_strategy'] = MemoryCleanupStrategy(alloc_data['cleanup_strategy'])
                        self.component_allocations[name] = MemoryAllocation(**alloc_data)

                # Load pressure level
                if 'current_pressure_level' in state:
                    self.current_pressure_level = MemoryPressureLevel(state['current_pressure_level'])

                # Load detected leaks
                if 'detected_leaks' in state:
                    self.detected_leaks = defaultdict(list, state['detected_leaks'])

                # Load GC stats
                if 'gc_stats' in state:
                    self.gc_stats = state['gc_stats']

                logger.info("📁 Memory manager state loaded")

        except Exception as e:
            logger.error(f"Error loading memory manager state: {e}")

    def get_memory_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive memory dashboard data."""
        try:
            # Get latest memory metrics
            latest_metrics = {}
            if self.memory_history:
                latest_metrics = self.memory_history[-1]

            # Get component memory usage
            component_memory = {}
            for component in self.component_allocations.keys():
                if self.component_metrics[component]:
                    latest = self.component_metrics[component][-1]
                    component_memory[component] = {
                        'memory_usage_mb': latest.memory_usage_mb,
                        'memory_percent': latest.memory_percent,
                        'growth_rate': latest.memory_growth_rate,
                        'cache_size_mb': latest.cache_size_mb,
                        'leaks_detected': latest.memory_leaks_detected,
                        'priority': self.component_allocations[component].priority.value
                    }

            # Get pressure history
            recent_pressure = []
            if self.pressure_history:
                recent_pressure = [
                    {
                        'timestamp': entry['timestamp'].isoformat() if isinstance(entry['timestamp'], datetime) else entry['timestamp'],
                        'level': entry['level'],
                        'memory_percent': entry['memory_percent']
                    } for entry in list(self.pressure_history)[-10:]
                ]

            return {
                'timestamp': datetime.now().isoformat(),
                'system_metrics': latest_metrics,
                'component_memory_usage': component_memory,
                'current_pressure_level': self.current_pressure_level.value,
                'pressure_history': recent_pressure,
                'total_detected_leaks': sum(len(leaks) for leaks in self.detected_leaks.values()),
                'gc_stats': self.gc_stats,
                'auto_gc_enabled': self.config.enable_auto_gc,
                'leak_detection_enabled': self.config.enable_leak_detection,
                'auto_cleanup_enabled': self.config.enable_auto_cleanup,
                'memory_optimization_enabled': self.config.enable_memory_optimization
            }

        except Exception as e:
            logger.error(f"Error generating memory dashboard: {e}")
            return {'error': str(e)}

    def get_component_cache_info(self, component: str) -> Dict[str, Any]:
        """Get cache information for a specific component."""
        try:
            cache = self.component_caches.get(component, {})
            allocation = self.component_allocations.get(component)

            if not allocation:
                return {'error': f'Component {component} not found'}

            cache_size_bytes = sum(sys.getsizeof(item) for item in cache.values())
            cache_size_mb = cache_size_bytes / (1024 * 1024)

            return {
                'component': component,
                'cache_items': len(cache),
                'cache_size_mb': cache_size_mb,
                'max_cache_size_mb': allocation.max_cache_size_mb,
                'cache_utilization_percent': (cache_size_mb / allocation.max_cache_size_mb) * 100,
                'cleanup_strategy': allocation.cleanup_strategy.value,
                'auto_cleanup_enabled': allocation.auto_cleanup_enabled
            }

        except Exception as e:
            logger.error(f"Error getting cache info for {component}: {e}")
            return {'error': str(e)}

    async def force_component_cleanup(self, component: str) -> bool:
        """Force cleanup for a specific component."""
        try:
            if component not in self.component_allocations:
                logger.error(f"Component {component} not found")
                return False

            await self._cleanup_component_memory(component)
            logger.info(f"🧹 Forced cleanup completed for {component}")
            return True

        except Exception as e:
            logger.error(f"Error forcing cleanup for {component}: {e}")
            return False

    async def force_garbage_collection(self) -> Dict[str, Any]:
        """Force garbage collection and return results."""
        try:
            memory_before = psutil.virtual_memory().percent

            # Perform GC
            collected = gc.collect()

            # Force collection of all generations
            for generation in range(3):
                gc.collect(generation)

            memory_after = psutil.virtual_memory().percent
            memory_freed = memory_before - memory_after

            result = {
                'objects_collected': collected,
                'memory_before_percent': memory_before,
                'memory_after_percent': memory_after,
                'memory_freed_percent': memory_freed,
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"🗑️ Forced GC: collected {collected} objects, freed {memory_freed:.2f}% memory")
            return result

        except Exception as e:
            logger.error(f"Error forcing garbage collection: {e}")
            return {'error': str(e)}
