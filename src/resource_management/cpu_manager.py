"""
CPU Manager - Specialized CPU Allocation and Monitoring

This module provides detailed CPU resource management for the MayArbi arbitrage system,
including per-component CPU monitoring, process priority management, CPU affinity
control, load balancing across cores, and CPU-specific optimization strategies.
"""

import asyncio
import logging
import psutil
import os
import time
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import statistics
from collections import deque, defaultdict

logger = logging.getLogger(__name__)


class CPUPriority(Enum):
    """CPU priority levels for processes."""
    IDLE = "idle"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    REALTIME = "realtime"


class CPUAffinityStrategy(Enum):
    """CPU affinity assignment strategies."""
    AUTO = "auto"
    DEDICATED = "dedicated"
    SHARED = "shared"
    BALANCED = "balanced"


@dataclass
class CPUMetrics:
    """Detailed CPU metrics for a component."""
    component: str
    cpu_percent: float
    cpu_time: float
    process_count: int
    thread_count: int
    priority: CPUPriority
    affinity: List[int]
    load_average: float
    context_switches: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'component': self.component,
            'cpu_percent': self.cpu_percent,
            'cpu_time': self.cpu_time,
            'process_count': self.process_count,
            'thread_count': self.thread_count,
            'priority': self.priority.value,
            'affinity': self.affinity,
            'load_average': self.load_average,
            'context_switches': self.context_switches,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class CPUAllocation:
    """CPU allocation configuration for a component."""
    component: str
    cpu_limit_percent: float
    priority: CPUPriority
    affinity_strategy: CPUAffinityStrategy
    dedicated_cores: List[int] = field(default_factory=list)
    max_processes: int = 10
    enable_throttling: bool = True
    throttle_threshold: float = 90.0


@dataclass
class CPUConfig:
    """Configuration for CPU management."""
    # Monitoring settings
    monitoring_interval: int = 10  # seconds
    metrics_retention_hours: int = 24
    
    # CPU thresholds
    cpu_warning_threshold: float = 70.0
    cpu_critical_threshold: float = 85.0
    per_core_warning_threshold: float = 80.0
    per_core_critical_threshold: float = 95.0
    
    # Load balancing
    enable_load_balancing: bool = True
    load_balance_interval: int = 60  # seconds
    load_imbalance_threshold: float = 20.0  # percent difference
    
    # Process management
    enable_priority_management: bool = True
    enable_affinity_management: bool = True
    auto_nice_adjustment: bool = True
    
    # Performance optimization
    enable_cpu_throttling: bool = True
    throttle_recovery_threshold: float = 60.0
    context_switch_threshold: int = 10000  # per second


class CPUManager:
    """
    Specialized CPU Manager for detailed CPU resource management.
    
    Provides comprehensive CPU monitoring, allocation, load balancing,
    and optimization for all system components.
    """
    
    def __init__(self, config: Optional[CPUConfig] = None):
        self.config = config or CPUConfig()
        self.running = False
        
        # CPU information
        self.cpu_count = psutil.cpu_count()
        self.cpu_count_logical = psutil.cpu_count(logical=True)
        
        # Component tracking
        self.component_allocations: Dict[str, CPUAllocation] = {}
        self.component_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.component_processes: Dict[str, List[psutil.Process]] = defaultdict(list)
        
        # CPU core tracking
        self.core_usage: Dict[int, deque] = {i: deque(maxlen=100) for i in range(self.cpu_count)}
        self.core_assignments: Dict[int, List[str]] = defaultdict(list)
        
        # Performance tracking
        self.cpu_history: deque = deque(maxlen=1000)
        self.throttled_components: Set[str] = set()
        
        # Monitoring tasks
        self.monitoring_tasks: List[asyncio.Task] = []
        
        # State persistence
        self.state_file = Path("data/cpu_manager_state.json")
        self.state_file.parent.mkdir(exist_ok=True)
        
        # Initialize component allocations
        self._initialize_cpu_allocations()
        
        logger.info(f"🔧 CPU Manager initialized - {self.cpu_count} cores ({self.cpu_count_logical} logical)")
    
    def _initialize_cpu_allocations(self):
        """Initialize CPU allocations for system components."""
        default_allocations = {
            "arbitrage_engine": CPUAllocation(
                component="arbitrage_engine",
                cpu_limit_percent=25.0,
                priority=CPUPriority.HIGH,
                affinity_strategy=CPUAffinityStrategy.BALANCED,
                max_processes=5,
                enable_throttling=True,
                throttle_threshold=85.0
            ),
            "bridge_monitor": CPUAllocation(
                component="bridge_monitor",
                cpu_limit_percent=15.0,
                priority=CPUPriority.NORMAL,
                affinity_strategy=CPUAffinityStrategy.SHARED,
                max_processes=3,
                enable_throttling=True,
                throttle_threshold=80.0
            ),
            "cross_chain_mev": CPUAllocation(
                component="cross_chain_mev",
                cpu_limit_percent=20.0,
                priority=CPUPriority.HIGH,
                affinity_strategy=CPUAffinityStrategy.BALANCED,
                max_processes=4,
                enable_throttling=True,
                throttle_threshold=85.0
            ),
            "wallet_manager": CPUAllocation(
                component="wallet_manager",
                cpu_limit_percent=10.0,
                priority=CPUPriority.REALTIME,
                affinity_strategy=CPUAffinityStrategy.DEDICATED,
                dedicated_cores=[0] if self.cpu_count > 1 else [],
                max_processes=2,
                enable_throttling=False  # Critical component
            ),
            "price_feeds": CPUAllocation(
                component="price_feeds",
                cpu_limit_percent=15.0,
                priority=CPUPriority.NORMAL,
                affinity_strategy=CPUAffinityStrategy.SHARED,
                max_processes=6,
                enable_throttling=True,
                throttle_threshold=75.0
            ),
            "memory_system": CPUAllocation(
                component="memory_system",
                cpu_limit_percent=10.0,
                priority=CPUPriority.LOW,
                affinity_strategy=CPUAffinityStrategy.AUTO,
                max_processes=2,
                enable_throttling=True,
                throttle_threshold=70.0
            ),
            "health_monitor": CPUAllocation(
                component="health_monitor",
                cpu_limit_percent=5.0,
                priority=CPUPriority.LOW,
                affinity_strategy=CPUAffinityStrategy.AUTO,
                max_processes=1,
                enable_throttling=False  # System critical
            )
        }
        
        self.component_allocations.update(default_allocations)
        logger.debug(f"Initialized CPU allocations for {len(default_allocations)} components")
    
    async def start_cpu_management(self):
        """Start the CPU management system."""
        if self.running:
            logger.warning("CPU management already running")
            return
        
        self.running = True
        logger.info("🚀 Starting CPU Management System")
        
        # Load previous state
        await self._load_state()
        
        # Apply initial CPU configurations
        await self._apply_cpu_configurations()
        
        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._cpu_monitor_loop()),
            asyncio.create_task(self._load_balancer_loop()),
            asyncio.create_task(self._process_manager_loop()),
            asyncio.create_task(self._optimization_loop())
        ]
        
        logger.info("✅ CPU Management System started")
    
    async def stop_cpu_management(self):
        """Stop the CPU management system."""
        if not self.running:
            return
        
        self.running = False
        logger.info("🛑 Stopping CPU Management System")
        
        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
        # Save state
        await self._save_state()
        
        logger.info("✅ CPU Management System stopped")
    
    async def get_cpu_metrics(self) -> Dict[str, Any]:
        """Get comprehensive CPU metrics."""
        try:
            # Overall CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_times = psutil.cpu_times()
            cpu_freq = psutil.cpu_freq()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # Per-core CPU usage
            per_core_usage = psutil.cpu_percent(interval=0.1, percpu=True)
            
            # Process information
            total_processes = len(psutil.pids())
            total_threads = sum(p.num_threads() for p in psutil.process_iter(['num_threads']) if p.info['num_threads'])
            
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_cpu_percent': cpu_percent,
                'per_core_usage': per_core_usage,
                'cpu_count': self.cpu_count,
                'cpu_count_logical': self.cpu_count_logical,
                'cpu_frequency': cpu_freq._asdict() if cpu_freq else {},
                'load_average': load_avg,
                'total_processes': total_processes,
                'total_threads': total_threads,
                'cpu_times': cpu_times._asdict(),
                'throttled_components': list(self.throttled_components)
            }
            
        except Exception as e:
            logger.error(f"Error getting CPU metrics: {e}")
            return {'error': str(e)}
    
    async def get_component_cpu_usage(self, component: str) -> Optional[CPUMetrics]:
        """Get detailed CPU usage for a specific component."""
        try:
            processes = self.component_processes.get(component, [])
            if not processes:
                return None
            
            # Aggregate metrics from all component processes
            total_cpu_percent = 0.0
            total_cpu_time = 0.0
            total_threads = 0
            total_context_switches = 0
            
            valid_processes = []
            for proc in processes:
                try:
                    if proc.is_running():
                        cpu_percent = proc.cpu_percent()
                        cpu_times = proc.cpu_times()
                        threads = proc.num_threads()
                        ctx_switches = proc.num_ctx_switches()
                        
                        total_cpu_percent += cpu_percent
                        total_cpu_time += cpu_times.user + cpu_times.system
                        total_threads += threads
                        total_context_switches += ctx_switches.voluntary + ctx_switches.involuntary
                        
                        valid_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Update valid processes list
            self.component_processes[component] = valid_processes
            
            allocation = self.component_allocations.get(component)
            if not allocation:
                return None
            
            metrics = CPUMetrics(
                component=component,
                cpu_percent=total_cpu_percent,
                cpu_time=total_cpu_time,
                process_count=len(valid_processes),
                thread_count=total_threads,
                priority=allocation.priority,
                affinity=allocation.dedicated_cores,
                load_average=psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0,
                context_switches=total_context_switches
            )
            
            # Store metrics
            self.component_metrics[component].append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting component CPU usage for {component}: {e}")
            return None

    async def _cpu_monitor_loop(self):
        """Main CPU monitoring loop."""
        while self.running:
            try:
                # Monitor overall CPU metrics
                cpu_metrics = await self.get_cpu_metrics()
                self.cpu_history.append(cpu_metrics)

                # Monitor per-component CPU usage
                for component in self.component_allocations.keys():
                    await self.get_component_cpu_usage(component)

                # Update per-core usage tracking
                await self._update_core_usage()

                # Check for CPU alerts
                await self._check_cpu_alerts(cpu_metrics)

                await asyncio.sleep(self.config.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in CPU monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _load_balancer_loop(self):
        """CPU load balancing loop."""
        while self.running:
            try:
                if self.config.enable_load_balancing:
                    await self._balance_cpu_load()

                await asyncio.sleep(self.config.load_balance_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in load balancer loop: {e}")
                await asyncio.sleep(30)

    async def _process_manager_loop(self):
        """Process management and optimization loop."""
        while self.running:
            try:
                # Update process tracking
                await self._update_process_tracking()

                # Apply priority adjustments
                if self.config.enable_priority_management:
                    await self._manage_process_priorities()

                # Apply CPU affinity
                if self.config.enable_affinity_management:
                    await self._manage_cpu_affinity()

                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in process manager loop: {e}")
                await asyncio.sleep(10)

    async def _optimization_loop(self):
        """CPU optimization and throttling loop."""
        while self.running:
            try:
                # Check for throttling needs
                if self.config.enable_cpu_throttling:
                    await self._manage_cpu_throttling()

                # Optimize CPU usage
                await self._optimize_cpu_usage()

                await asyncio.sleep(15)  # Check every 15 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(10)

    async def _apply_cpu_configurations(self):
        """Apply initial CPU configurations to components."""
        logger.info("🔧 Applying CPU configurations")

        for component, allocation in self.component_allocations.items():
            try:
                # Set up dedicated cores if specified
                if allocation.affinity_strategy == CPUAffinityStrategy.DEDICATED and allocation.dedicated_cores:
                    self.core_assignments[allocation.dedicated_cores[0]].append(component)
                    logger.info(f"Assigned {component} to dedicated core {allocation.dedicated_cores[0]}")

            except Exception as e:
                logger.error(f"Error applying CPU configuration for {component}: {e}")

    async def _update_core_usage(self):
        """Update per-core CPU usage tracking."""
        try:
            per_core_usage = psutil.cpu_percent(interval=0.1, percpu=True)

            for core_id, usage in enumerate(per_core_usage):
                if core_id < len(self.core_usage):
                    self.core_usage[core_id].append({
                        'usage': usage,
                        'timestamp': datetime.now()
                    })

        except Exception as e:
            logger.error(f"Error updating core usage: {e}")

    async def _check_cpu_alerts(self, cpu_metrics: Dict[str, Any]):
        """Check for CPU-related alerts."""
        try:
            overall_cpu = cpu_metrics.get('overall_cpu_percent', 0)
            per_core_usage = cpu_metrics.get('per_core_usage', [])

            # Check overall CPU usage
            if overall_cpu > self.config.cpu_critical_threshold:
                logger.warning(f"🚨 CRITICAL: Overall CPU usage at {overall_cpu:.1f}%")
            elif overall_cpu > self.config.cpu_warning_threshold:
                logger.warning(f"⚠️ WARNING: Overall CPU usage at {overall_cpu:.1f}%")

            # Check per-core usage
            for core_id, usage in enumerate(per_core_usage):
                if usage > self.config.per_core_critical_threshold:
                    logger.warning(f"🚨 CRITICAL: Core {core_id} usage at {usage:.1f}%")
                elif usage > self.config.per_core_warning_threshold:
                    logger.warning(f"⚠️ WARNING: Core {core_id} usage at {usage:.1f}%")

            # Check load average
            load_avg = cpu_metrics.get('load_average', [0, 0, 0])
            if load_avg[0] > self.cpu_count * 1.5:
                logger.warning(f"🚨 High load average: {load_avg[0]:.2f} (cores: {self.cpu_count})")

        except Exception as e:
            logger.error(f"Error checking CPU alerts: {e}")

    async def _balance_cpu_load(self):
        """Balance CPU load across cores."""
        try:
            # Get current per-core usage
            per_core_usage = psutil.cpu_percent(interval=0.1, percpu=True)

            if not per_core_usage:
                return

            # Calculate load imbalance
            max_usage = max(per_core_usage)
            min_usage = min(per_core_usage)
            imbalance = max_usage - min_usage

            if imbalance > self.config.load_imbalance_threshold:
                logger.info(f"⚖️ Load imbalance detected: {imbalance:.1f}% difference")

                # Find overloaded and underloaded cores
                overloaded_cores = [i for i, usage in enumerate(per_core_usage)
                                  if usage > statistics.mean(per_core_usage) + 10]
                underloaded_cores = [i for i, usage in enumerate(per_core_usage)
                                   if usage < statistics.mean(per_core_usage) - 10]

                # Attempt to rebalance by adjusting process affinity
                await self._rebalance_process_affinity(overloaded_cores, underloaded_cores)

        except Exception as e:
            logger.error(f"Error balancing CPU load: {e}")

    async def _rebalance_process_affinity(self, overloaded_cores: List[int], underloaded_cores: List[int]):
        """Rebalance process affinity to distribute load."""
        try:
            if not underloaded_cores:
                return

            for component, processes in self.component_processes.items():
                allocation = self.component_allocations.get(component)
                if not allocation or allocation.affinity_strategy == CPUAffinityStrategy.DEDICATED:
                    continue

                for proc in processes:
                    try:
                        if proc.is_running():
                            current_affinity = proc.cpu_affinity()

                            # If process is on overloaded core, move to underloaded core
                            if any(core in overloaded_cores for core in current_affinity):
                                new_affinity = [underloaded_cores[0]]  # Move to least loaded core
                                proc.cpu_affinity(new_affinity)
                                logger.debug(f"Moved {component} process to core {new_affinity[0]}")

                    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                        continue

        except Exception as e:
            logger.error(f"Error rebalancing process affinity: {e}")

    async def _update_process_tracking(self):
        """Update tracking of component processes."""
        try:
            # Clear old process lists
            for component in self.component_processes:
                self.component_processes[component] = []

            # Scan all processes and categorize by component
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    component = self._identify_component_from_process(proc_info)

                    if component:
                        self.component_processes[component].append(proc)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            logger.error(f"Error updating process tracking: {e}")

    def _identify_component_from_process(self, proc_info: Dict[str, Any]) -> Optional[str]:
        """Identify which component a process belongs to based on process info."""
        try:
            name = proc_info.get('name', '').lower()
            cmdline = ' '.join(proc_info.get('cmdline', [])).lower()

            # Simple heuristic-based component identification
            if 'arbitrage' in name or 'arbitrage' in cmdline:
                return 'arbitrage_engine'
            elif 'bridge' in name or 'bridge' in cmdline:
                return 'bridge_monitor'
            elif 'mev' in name or 'cross_chain' in cmdline:
                return 'cross_chain_mev'
            elif 'wallet' in name or 'wallet' in cmdline:
                return 'wallet_manager'
            elif 'price' in name or 'feeds' in cmdline:
                return 'price_feeds'
            elif 'memory' in name or 'mcp' in cmdline:
                return 'memory_system'
            elif 'health' in name or 'monitor' in cmdline:
                return 'health_monitor'

            return None

        except Exception:
            return None

    async def _manage_process_priorities(self):
        """Manage process priorities based on component allocations."""
        try:
            for component, processes in self.component_processes.items():
                allocation = self.component_allocations.get(component)
                if not allocation:
                    continue

                # Map CPU priority to system nice value
                nice_values = {
                    CPUPriority.IDLE: 19,
                    CPUPriority.LOW: 10,
                    CPUPriority.NORMAL: 0,
                    CPUPriority.HIGH: -5,
                    CPUPriority.REALTIME: -10
                }

                target_nice = nice_values.get(allocation.priority, 0)

                for proc in processes:
                    try:
                        if proc.is_running():
                            current_nice = proc.nice()
                            if current_nice != target_nice:
                                proc.nice(target_nice)
                                logger.debug(f"Set {component} process priority to {allocation.priority.value}")

                    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                        continue

        except Exception as e:
            logger.error(f"Error managing process priorities: {e}")

    async def _manage_cpu_affinity(self):
        """Manage CPU affinity based on component allocations."""
        try:
            for component, processes in self.component_processes.items():
                allocation = self.component_allocations.get(component)
                if not allocation:
                    continue

                target_affinity = self._calculate_target_affinity(allocation)

                for proc in processes:
                    try:
                        if proc.is_running():
                            current_affinity = proc.cpu_affinity()
                            if set(current_affinity) != set(target_affinity):
                                proc.cpu_affinity(target_affinity)
                                logger.debug(f"Set {component} CPU affinity to cores {target_affinity}")

                    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                        continue

        except Exception as e:
            logger.error(f"Error managing CPU affinity: {e}")

    def _calculate_target_affinity(self, allocation: CPUAllocation) -> List[int]:
        """Calculate target CPU affinity for a component allocation."""
        try:
            if allocation.affinity_strategy == CPUAffinityStrategy.DEDICATED:
                return allocation.dedicated_cores if allocation.dedicated_cores else [0]

            elif allocation.affinity_strategy == CPUAffinityStrategy.SHARED:
                # Use all cores except dedicated ones
                dedicated_cores = set()
                for alloc in self.component_allocations.values():
                    if alloc.affinity_strategy == CPUAffinityStrategy.DEDICATED:
                        dedicated_cores.update(alloc.dedicated_cores)

                available_cores = [i for i in range(self.cpu_count) if i not in dedicated_cores]
                return available_cores if available_cores else list(range(self.cpu_count))

            elif allocation.affinity_strategy == CPUAffinityStrategy.BALANCED:
                # Distribute across available cores based on load
                return self._get_least_loaded_cores(2)  # Use 2 cores for balanced components

            else:  # AUTO
                return list(range(self.cpu_count))  # Use all cores

        except Exception as e:
            logger.error(f"Error calculating target affinity: {e}")
            return list(range(self.cpu_count))

    def _get_least_loaded_cores(self, count: int) -> List[int]:
        """Get the least loaded CPU cores."""
        try:
            if not self.core_usage:
                return list(range(min(count, self.cpu_count)))

            # Calculate average usage for each core
            core_averages = {}
            for core_id, usage_history in self.core_usage.items():
                if usage_history:
                    recent_usage = [entry['usage'] for entry in list(usage_history)[-10:]]
                    core_averages[core_id] = statistics.mean(recent_usage)
                else:
                    core_averages[core_id] = 0.0

            # Sort cores by average usage and return least loaded
            sorted_cores = sorted(core_averages.items(), key=lambda x: x[1])
            return [core_id for core_id, _ in sorted_cores[:count]]

        except Exception as e:
            logger.error(f"Error getting least loaded cores: {e}")
            return list(range(min(count, self.cpu_count)))

    async def _manage_cpu_throttling(self):
        """Manage CPU throttling for components that exceed limits."""
        try:
            for component in self.component_allocations.keys():
                metrics = await self.get_component_cpu_usage(component)
                if not metrics:
                    continue

                allocation = self.component_allocations[component]
                if not allocation.enable_throttling:
                    continue

                # Check if component exceeds its CPU limit
                if metrics.cpu_percent > allocation.throttle_threshold:
                    if component not in self.throttled_components:
                        await self._throttle_component(component, allocation)
                        self.throttled_components.add(component)
                        logger.warning(f"🚦 Throttling {component} - CPU usage: {metrics.cpu_percent:.1f}%")

                # Check if throttled component can be unthrottled
                elif (component in self.throttled_components and
                      metrics.cpu_percent < self.config.throttle_recovery_threshold):
                    await self._unthrottle_component(component, allocation)
                    self.throttled_components.discard(component)
                    logger.info(f"✅ Unthrottling {component} - CPU usage: {metrics.cpu_percent:.1f}%")

        except Exception as e:
            logger.error(f"Error managing CPU throttling: {e}")

    async def _throttle_component(self, component: str, allocation: CPUAllocation):
        """Apply CPU throttling to a component."""
        try:
            processes = self.component_processes.get(component, [])
            # Note: allocation parameter available for future throttling strategies

            for proc in processes:
                try:
                    if proc.is_running():
                        # Reduce process priority
                        current_nice = proc.nice()
                        new_nice = min(current_nice + 5, 19)  # Increase nice value (lower priority)
                        proc.nice(new_nice)

                except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                    continue

        except Exception as e:
            logger.error(f"Error throttling component {component}: {e}")

    async def _unthrottle_component(self, component: str, allocation: CPUAllocation):
        """Remove CPU throttling from a component."""
        try:
            processes = self.component_processes.get(component, [])

            # Map CPU priority back to normal nice value
            nice_values = {
                CPUPriority.IDLE: 19,
                CPUPriority.LOW: 10,
                CPUPriority.NORMAL: 0,
                CPUPriority.HIGH: -5,
                CPUPriority.REALTIME: -10
            }

            target_nice = nice_values.get(allocation.priority, 0)

            for proc in processes:
                try:
                    if proc.is_running():
                        proc.nice(target_nice)

                except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                    continue

        except Exception as e:
            logger.error(f"Error unthrottling component {component}: {e}")

    async def _optimize_cpu_usage(self):
        """Optimize overall CPU usage across components."""
        try:
            # Get current system CPU usage
            cpu_metrics = await self.get_cpu_metrics()
            overall_cpu = cpu_metrics.get('overall_cpu_percent', 0)

            # If system CPU is high, look for optimization opportunities
            if overall_cpu > self.config.cpu_warning_threshold:
                await self._optimize_high_cpu_usage()

            # Check for context switch optimization
            if 'total_processes' in cpu_metrics:
                await self._optimize_context_switches(cpu_metrics)

        except Exception as e:
            logger.error(f"Error optimizing CPU usage: {e}")

    async def _optimize_high_cpu_usage(self):
        """Optimize when system CPU usage is high."""
        try:
            # Find components with highest CPU usage
            component_usage = {}
            for component in self.component_allocations.keys():
                metrics = await self.get_component_cpu_usage(component)
                if metrics:
                    component_usage[component] = metrics.cpu_percent

            # Sort by CPU usage
            sorted_components = sorted(component_usage.items(), key=lambda x: x[1], reverse=True)

            # Apply optimizations to highest usage components
            for component, usage in sorted_components[:3]:  # Top 3 CPU users
                allocation = self.component_allocations.get(component)
                if allocation and allocation.enable_throttling:
                    if usage > allocation.cpu_limit_percent * 1.2:  # 20% over limit
                        logger.info(f"🔧 Optimizing high CPU usage for {component}: {usage:.1f}%")
                        await self._apply_cpu_optimization(component, allocation)

        except Exception as e:
            logger.error(f"Error optimizing high CPU usage: {e}")

    async def _apply_cpu_optimization(self, component: str, allocation: CPUAllocation):
        """Apply CPU optimization to a specific component."""
        try:
            processes = self.component_processes.get(component, [])
            # Note: allocation parameter available for future optimization strategies

            for proc in processes:
                try:
                    if proc.is_running():
                        # Temporarily reduce priority
                        current_nice = proc.nice()
                        proc.nice(min(current_nice + 2, 19))

                        # Optimize CPU affinity to less loaded cores
                        least_loaded = self._get_least_loaded_cores(1)
                        if least_loaded:
                            proc.cpu_affinity(least_loaded)

                except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                    continue

        except Exception as e:
            logger.error(f"Error applying CPU optimization to {component}: {e}")

    async def _optimize_context_switches(self, cpu_metrics: Dict[str, Any]):
        """Optimize context switches if they're too high."""
        try:
            # This is a placeholder for context switch optimization
            # In a real implementation, you would analyze context switch patterns
            # and optimize process scheduling accordingly
            # Note: cpu_metrics parameter available for future context switch analysis
            pass

        except Exception as e:
            logger.error(f"Error optimizing context switches: {e}")

    async def _save_state(self):
        """Save CPU manager state to disk."""
        try:
            state = {
                'component_allocations': {
                    name: {
                        'component': alloc.component,
                        'cpu_limit_percent': alloc.cpu_limit_percent,
                        'priority': alloc.priority.value,
                        'affinity_strategy': alloc.affinity_strategy.value,
                        'dedicated_cores': alloc.dedicated_cores,
                        'max_processes': alloc.max_processes,
                        'enable_throttling': alloc.enable_throttling,
                        'throttle_threshold': alloc.throttle_threshold
                    } for name, alloc in self.component_allocations.items()
                },
                'throttled_components': list(self.throttled_components),
                'core_assignments': {str(k): v for k, v in self.core_assignments.items()},
                'last_save': datetime.now().isoformat()
            }

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving CPU manager state: {e}")

    async def _load_state(self):
        """Load CPU manager state from disk."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)

                # Load component allocations
                if 'component_allocations' in state:
                    for name, alloc_data in state['component_allocations'].items():
                        alloc_data['priority'] = CPUPriority(alloc_data['priority'])
                        alloc_data['affinity_strategy'] = CPUAffinityStrategy(alloc_data['affinity_strategy'])
                        self.component_allocations[name] = CPUAllocation(**alloc_data)

                # Load throttled components
                if 'throttled_components' in state:
                    self.throttled_components = set(state['throttled_components'])

                # Load core assignments
                if 'core_assignments' in state:
                    self.core_assignments = {int(k): v for k, v in state['core_assignments'].items()}

                logger.info("📁 CPU manager state loaded")

        except Exception as e:
            logger.error(f"Error loading CPU manager state: {e}")

    def get_cpu_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive CPU dashboard data."""
        try:
            # Get latest CPU metrics
            latest_metrics = {}
            if self.cpu_history:
                latest_metrics = self.cpu_history[-1]

            # Get component CPU usage
            component_cpu = {}
            for component in self.component_allocations.keys():
                if self.component_metrics[component]:
                    latest = self.component_metrics[component][-1]
                    component_cpu[component] = {
                        'cpu_percent': latest.cpu_percent,
                        'process_count': latest.process_count,
                        'priority': latest.priority.value,
                        'throttled': component in self.throttled_components
                    }

            # Get per-core usage
            per_core_current = {}
            for core_id, usage_history in self.core_usage.items():
                if usage_history:
                    per_core_current[f"core_{core_id}"] = usage_history[-1]['usage']

            return {
                'timestamp': datetime.now().isoformat(),
                'system_metrics': latest_metrics,
                'component_cpu_usage': component_cpu,
                'per_core_usage': per_core_current,
                'cpu_count': self.cpu_count,
                'cpu_count_logical': self.cpu_count_logical,
                'throttled_components': list(self.throttled_components),
                'core_assignments': {f"core_{k}": v for k, v in self.core_assignments.items()},
                'load_balancing_enabled': self.config.enable_load_balancing,
                'priority_management_enabled': self.config.enable_priority_management,
                'affinity_management_enabled': self.config.enable_affinity_management
            }

        except Exception as e:
            logger.error(f"Error generating CPU dashboard: {e}")
            return {'error': str(e)}
