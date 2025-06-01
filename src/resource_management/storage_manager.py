"""
Storage Manager - Storage Resource Management for MayArbi System

Manages disk usage allocation, data retention policies, cleanup automation,
and storage optimization across all system components. Monitors file system
health and ensures optimal storage resource utilization.
"""

import asyncio
import logging
import os
import shutil
import time
import psutil
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import statistics
from collections import deque, defaultdict
import glob

logger = logging.getLogger(__name__)


class StoragePriority(Enum):
    """Storage priority levels for components."""
    CRITICAL = 10  # Trading data, wallet info
    HIGH = 8      # Price feeds, bridge data
    NORMAL = 5    # General operations
    LOW = 2       # Logs, temporary files
    MINIMAL = 1   # Cache, cleanup candidates


class CleanupStrategy(Enum):
    """Storage cleanup strategies."""
    TIME_BASED = "time_based"      # Delete by age
    SIZE_BASED = "size_based"      # Delete by size limits
    LRU = "lru"                    # Least Recently Used
    PRIORITY_BASED = "priority"    # Delete by priority
    ADAPTIVE = "adaptive"          # Combination strategy


class StorageType(Enum):
    """Types of storage usage."""
    DATA = "data"           # Persistent data
    LOGS = "logs"           # Log files
    CACHE = "cache"         # Temporary cache
    CONFIG = "config"       # Configuration files
    TEMP = "temp"           # Temporary files
    BACKUP = "backup"       # Backup files


@dataclass
class StorageAllocation:
    """Storage resource allocation for a component."""
    component: str
    
    # Storage limits (MB)
    max_storage_mb: float = 1000.0
    warning_threshold_mb: float = 800.0
    critical_threshold_mb: float = 950.0
    
    # Data retention
    max_retention_days: int = 30
    log_retention_days: int = 7
    cache_retention_hours: int = 24
    temp_retention_hours: int = 6
    
    # Cleanup settings
    cleanup_strategy: CleanupStrategy = CleanupStrategy.TIME_BASED
    enable_auto_cleanup: bool = True
    cleanup_interval_hours: int = 6
    
    # Priority and optimization
    priority: StoragePriority = StoragePriority.NORMAL
    enable_compression: bool = False
    enable_backup: bool = True
    
    # Monitoring
    track_file_count: bool = True
    track_access_patterns: bool = True
    alert_on_limits: bool = True


@dataclass
class StorageMetrics:
    """Metrics for storage usage."""
    component: str
    storage_type: StorageType
    
    # Usage metrics
    total_size_mb: float = 0.0
    file_count: int = 0
    directory_count: int = 0
    
    # Performance metrics
    read_operations: int = 0
    write_operations: int = 0
    delete_operations: int = 0
    
    # Cleanup metrics
    last_cleanup: Optional[datetime] = None
    files_cleaned: int = 0
    space_freed_mb: float = 0.0
    
    # Health metrics
    fragmentation_percent: float = 0.0
    access_frequency: float = 0.0
    
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class StorageAlert:
    """Storage-related alert."""
    component: str
    alert_type: str
    severity: str
    message: str
    storage_usage_mb: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False


@dataclass
class StorageConfig:
    """Configuration for storage management."""
    # Monitoring settings
    monitoring_interval: int = 30  # seconds
    metrics_retention_hours: int = 24
    
    # Storage thresholds (percent of allocated space)
    storage_warning_threshold: float = 80.0
    storage_critical_threshold: float = 95.0
    
    # System-wide thresholds (percent of total disk)
    system_warning_threshold: float = 85.0
    system_critical_threshold: float = 95.0
    
    # Cleanup settings
    enable_auto_cleanup: bool = True
    cleanup_interval_hours: int = 6
    aggressive_cleanup_threshold: float = 90.0
    
    # File system settings
    enable_compression: bool = True
    enable_deduplication: bool = False
    enable_backup: bool = True
    backup_retention_days: int = 7
    
    # Performance optimization
    enable_defragmentation: bool = False
    defrag_threshold_percent: float = 20.0
    enable_cache_optimization: bool = True
    
    # Alert settings
    alert_cooldown_minutes: int = 10
    max_alerts_per_hour: int = 12


class StorageManager:
    """
    Storage Manager - Manages storage resources and optimization.
    
    Handles disk usage allocation, data retention policies, cleanup automation,
    and storage optimization for all system components.
    """
    
    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or StorageConfig()
        self.running = False
        
        # Storage tracking
        self.component_allocations: Dict[str, StorageAllocation] = {}
        self.component_metrics: Dict[str, Dict[StorageType, StorageMetrics]] = defaultdict(dict)
        self.storage_history: deque = deque(maxlen=1000)
        
        # File system tracking
        self.base_paths: Dict[str, Path] = {
            'data': Path('data'),
            'logs': Path('logs'),
            'cache': Path('cache'),
            'config': Path('config'),
            'temp': Path('temp'),
            'backup': Path('backup')
        }
        
        # Cleanup tracking
        self.cleanup_history: deque = deque(maxlen=1000)
        self.last_cleanup: Dict[str, datetime] = {}
        
        # Performance tracking
        self.access_patterns: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.fragmentation_history: deque = deque(maxlen=100)
        
        # Alerts
        self.active_alerts: Dict[str, StorageAlert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        
        # Monitoring tasks
        self.monitoring_tasks: List[asyncio.Task] = []
        
        # State persistence
        self.state_file = Path("data/storage_manager_state.json")
        self.state_file.parent.mkdir(exist_ok=True)
        
        # Initialize component allocations
        self._initialize_storage_allocations()
        
        # Ensure base directories exist
        self._ensure_base_directories()
        
        logger.info("💾 Storage Manager initialized")
    
    def _ensure_base_directories(self):
        """Ensure all base directories exist."""
        try:
            for storage_type, path in self.base_paths.items():
                path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured directory exists: {path}")
        except Exception as e:
            logger.error(f"Error creating base directories: {e}")
    
    def _initialize_storage_allocations(self):
        """Initialize storage allocations for system components."""
        default_allocations = {
            "arbitrage_engine": StorageAllocation(
                component="arbitrage_engine",
                max_storage_mb=2000.0,
                warning_threshold_mb=1600.0,
                critical_threshold_mb=1900.0,
                max_retention_days=60,
                log_retention_days=14,
                cache_retention_hours=48,
                priority=StoragePriority.CRITICAL,
                cleanup_strategy=CleanupStrategy.PRIORITY_BASED,
                enable_compression=True,
                enable_backup=True,
                cleanup_interval_hours=12
            ),
            "bridge_monitor": StorageAllocation(
                component="bridge_monitor",
                max_storage_mb=1000.0,
                warning_threshold_mb=800.0,
                critical_threshold_mb=950.0,
                max_retention_days=30,
                log_retention_days=7,
                cache_retention_hours=24,
                priority=StoragePriority.HIGH,
                cleanup_strategy=CleanupStrategy.TIME_BASED,
                enable_compression=True,
                enable_backup=True,
                cleanup_interval_hours=8
            ),
            "cross_chain_mev": StorageAllocation(
                component="cross_chain_mev",
                max_storage_mb=1500.0,
                warning_threshold_mb=1200.0,
                critical_threshold_mb=1425.0,
                max_retention_days=45,
                log_retention_days=10,
                cache_retention_hours=36,
                priority=StoragePriority.HIGH,
                cleanup_strategy=CleanupStrategy.ADAPTIVE,
                enable_compression=True,
                enable_backup=True,
                cleanup_interval_hours=10
            ),
            "price_feeds": StorageAllocation(
                component="price_feeds",
                max_storage_mb=3000.0,
                warning_threshold_mb=2400.0,
                critical_threshold_mb=2850.0,
                max_retention_days=90,
                log_retention_days=14,
                cache_retention_hours=72,
                priority=StoragePriority.HIGH,
                cleanup_strategy=CleanupStrategy.LRU,
                enable_compression=True,
                enable_backup=True,
                cleanup_interval_hours=6
            ),
            "wallet_manager": StorageAllocation(
                component="wallet_manager",
                max_storage_mb=500.0,
                warning_threshold_mb=400.0,
                critical_threshold_mb=475.0,
                max_retention_days=365,  # Keep wallet data longer
                log_retention_days=30,
                cache_retention_hours=12,
                priority=StoragePriority.CRITICAL,
                cleanup_strategy=CleanupStrategy.PRIORITY_BASED,
                enable_compression=False,  # Security consideration
                enable_backup=True,
                cleanup_interval_hours=24
            ),
            "memory_system": StorageAllocation(
                component="memory_system",
                max_storage_mb=5000.0,
                warning_threshold_mb=4000.0,
                critical_threshold_mb=4750.0,
                max_retention_days=180,
                log_retention_days=21,
                cache_retention_hours=168,  # 1 week
                priority=StoragePriority.NORMAL,
                cleanup_strategy=CleanupStrategy.ADAPTIVE,
                enable_compression=True,
                enable_backup=True,
                cleanup_interval_hours=4
            ),
            "health_monitor": StorageAllocation(
                component="health_monitor",
                max_storage_mb=200.0,
                warning_threshold_mb=160.0,
                critical_threshold_mb=190.0,
                max_retention_days=14,
                log_retention_days=3,
                cache_retention_hours=6,
                priority=StoragePriority.LOW,
                cleanup_strategy=CleanupStrategy.TIME_BASED,
                enable_compression=True,
                enable_backup=False,
                cleanup_interval_hours=4
            )
        }
        
        self.component_allocations.update(default_allocations)
        logger.debug(f"Initialized storage allocations for {len(default_allocations)} components")

    async def start_storage_management(self):
        """Start the storage management system."""
        if self.running:
            logger.warning("Storage management already running")
            return

        self.running = True
        logger.info("🚀 Starting Storage Management System")

        # Load previous state
        await self._load_state()

        # Initialize storage metrics
        await self._initialize_storage_metrics()

        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._storage_monitor_loop()),
            asyncio.create_task(self._cleanup_manager_loop()),
            asyncio.create_task(self._optimization_loop()),
            asyncio.create_task(self._health_monitor_loop())
        ]

        logger.info("✅ Storage Management System started")

    async def stop_storage_management(self):
        """Stop the storage management system."""
        if not self.running:
            return

        self.running = False
        logger.info("🛑 Stopping Storage Management System")

        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

        # Save state
        await self._save_state()

        logger.info("✅ Storage Management System stopped")

    async def _initialize_storage_metrics(self):
        """Initialize storage metrics for all components."""
        try:
            for component in self.component_allocations:
                for storage_type in StorageType:
                    self.component_metrics[component][storage_type] = StorageMetrics(
                        component=component,
                        storage_type=storage_type
                    )

            logger.info(f"Initialized storage metrics for {len(self.component_allocations)} components")

        except Exception as e:
            logger.error(f"Error initializing storage metrics: {e}")

    async def get_storage_metrics(self) -> Dict[str, Any]:
        """Get current storage metrics."""
        try:
            # System disk usage
            disk_usage = shutil.disk_usage('/')
            total_gb = disk_usage.total / (1024**3)
            used_gb = (disk_usage.total - disk_usage.free) / (1024**3)
            free_gb = disk_usage.free / (1024**3)
            usage_percent = (used_gb / total_gb) * 100

            # Component storage usage
            component_usage = {}
            total_component_usage_mb = 0

            for component, allocation in self.component_allocations.items():
                component_size = await self._get_component_storage_usage(component)
                usage_percent_comp = (component_size / allocation.max_storage_mb) * 100

                component_usage[component] = {
                    'used_mb': component_size,
                    'allocated_mb': allocation.max_storage_mb,
                    'usage_percent': usage_percent_comp,
                    'warning_threshold': allocation.warning_threshold_mb,
                    'critical_threshold': allocation.critical_threshold_mb,
                    'priority': allocation.priority.name,
                    'cleanup_strategy': allocation.cleanup_strategy.name
                }

                total_component_usage_mb += component_size

            # Storage type breakdown
            storage_type_usage = {}
            for storage_type in StorageType:
                type_size = await self._get_storage_type_usage(storage_type)
                storage_type_usage[storage_type.value] = {
                    'used_mb': type_size,
                    'file_count': await self._get_storage_type_file_count(storage_type)
                }

            return {
                'timestamp': datetime.now().isoformat(),
                'system_storage': {
                    'total_gb': total_gb,
                    'used_gb': used_gb,
                    'free_gb': free_gb,
                    'usage_percent': usage_percent
                },
                'component_usage': component_usage,
                'storage_type_usage': storage_type_usage,
                'total_managed_mb': total_component_usage_mb,
                'active_alerts': len([a for a in self.active_alerts.values() if not a.resolved]),
                'last_cleanup': max(self.last_cleanup.values()) if self.last_cleanup else None
            }

        except Exception as e:
            logger.error(f"Error getting storage metrics: {e}")
            return {}

    async def _get_component_storage_usage(self, component: str) -> float:
        """Get storage usage for a specific component in MB."""
        try:
            total_size = 0

            # Check each storage type directory for component files
            for storage_type, base_path in self.base_paths.items():
                component_path = base_path / component
                if component_path.exists():
                    total_size += await self._get_directory_size(component_path)

            return total_size / (1024 * 1024)  # Convert to MB

        except Exception as e:
            logger.error(f"Error getting storage usage for {component}: {e}")
            return 0.0

    async def _get_storage_type_usage(self, storage_type: StorageType) -> float:
        """Get storage usage for a specific storage type in MB."""
        try:
            base_path = self.base_paths.get(storage_type.value)
            if not base_path or not base_path.exists():
                return 0.0

            total_size = await self._get_directory_size(base_path)
            return total_size / (1024 * 1024)  # Convert to MB

        except Exception as e:
            logger.error(f"Error getting storage type usage for {storage_type}: {e}")
            return 0.0

    async def _get_storage_type_file_count(self, storage_type: StorageType) -> int:
        """Get file count for a specific storage type."""
        try:
            base_path = self.base_paths.get(storage_type.value)
            if not base_path or not base_path.exists():
                return 0

            return await self._count_files_recursive(base_path)

        except Exception as e:
            logger.error(f"Error getting file count for {storage_type}: {e}")
            return 0

    async def _get_directory_size(self, path: Path) -> int:
        """Get total size of directory in bytes."""
        try:
            total_size = 0
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, FileNotFoundError):
                        continue
            return total_size

        except Exception as e:
            logger.error(f"Error getting directory size for {path}: {e}")
            return 0

    async def _count_files_recursive(self, path: Path) -> int:
        """Count files recursively in directory."""
        try:
            count = 0
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    count += 1
            return count

        except Exception as e:
            logger.error(f"Error counting files in {path}: {e}")
            return 0

    async def _storage_monitor_loop(self):
        """Main storage monitoring loop."""
        while self.running:
            try:
                # Get current metrics
                metrics = await self.get_storage_metrics()

                # Store metrics history
                self.storage_history.append({
                    'timestamp': datetime.now(),
                    'metrics': metrics
                })

                # Check for alerts
                await self._check_storage_alerts(metrics)

                # Update component metrics
                await self._update_component_metrics()

                await asyncio.sleep(self.config.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in storage monitor loop: {e}")
                await asyncio.sleep(30)

    async def _cleanup_manager_loop(self):
        """Storage cleanup management loop."""
        while self.running:
            try:
                # Check if cleanup is needed
                await self._check_cleanup_needed()

                # Perform scheduled cleanups
                await self._perform_scheduled_cleanups()

                # Emergency cleanup if critical thresholds reached
                await self._emergency_cleanup_check()

                await asyncio.sleep(3600)  # Check every hour

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup manager loop: {e}")
                await asyncio.sleep(1800)  # Wait 30 minutes on error

    async def _optimization_loop(self):
        """Storage optimization loop."""
        while self.running:
            try:
                # Analyze storage patterns
                await self._analyze_storage_patterns()

                # Optimize storage allocation
                await self._optimize_storage_allocation()

                # Defragmentation if enabled
                if self.config.enable_defragmentation:
                    await self._check_defragmentation_needed()

                await asyncio.sleep(7200)  # Optimize every 2 hours

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(3600)

    async def _health_monitor_loop(self):
        """Storage health monitoring loop."""
        while self.running:
            try:
                # Check file system health
                await self._check_filesystem_health()

                # Monitor access patterns
                await self._monitor_access_patterns()

                # Check for corruption or issues
                await self._check_storage_integrity()

                await asyncio.sleep(1800)  # Check every 30 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}")
                await asyncio.sleep(900)

    async def cleanup_component_storage(self, component: str, force: bool = False) -> Dict[str, Any]:
        """Clean up storage for a specific component."""
        try:
            allocation = self.component_allocations.get(component)
            if not allocation:
                return {'error': f'No allocation found for component {component}'}

            cleanup_results = {
                'component': component,
                'files_deleted': 0,
                'space_freed_mb': 0.0,
                'cleanup_strategy': allocation.cleanup_strategy.name,
                'timestamp': datetime.now().isoformat()
            }

            # Apply cleanup strategy
            if allocation.cleanup_strategy == CleanupStrategy.TIME_BASED:
                result = await self._time_based_cleanup(component, allocation, force)
            elif allocation.cleanup_strategy == CleanupStrategy.SIZE_BASED:
                result = await self._size_based_cleanup(component, allocation, force)
            elif allocation.cleanup_strategy == CleanupStrategy.LRU:
                result = await self._lru_cleanup(component, allocation, force)
            elif allocation.cleanup_strategy == CleanupStrategy.PRIORITY_BASED:
                result = await self._priority_based_cleanup(component, allocation, force)
            else:  # ADAPTIVE
                result = await self._adaptive_cleanup(component, allocation, force)

            cleanup_results.update(result)

            # Record cleanup
            self.last_cleanup[component] = datetime.now()
            self.cleanup_history.append(cleanup_results)

            logger.info(f"Cleanup completed for {component}: {result['files_deleted']} files, "
                       f"{result['space_freed_mb']:.1f} MB freed")

            return cleanup_results

        except Exception as e:
            logger.error(f"Error cleaning up storage for {component}: {e}")
            return {'error': str(e)}

    async def _time_based_cleanup(self, component: str, allocation: StorageAllocation, force: bool) -> Dict[str, Any]:
        """Perform time-based cleanup."""
        try:
            files_deleted = 0
            space_freed = 0

            current_time = datetime.now()

            # Clean up each storage type based on retention policies
            for storage_type, base_path in self.base_paths.items():
                component_path = base_path / component
                if not component_path.exists():
                    continue

                # Determine retention period
                if storage_type == 'logs':
                    retention_hours = allocation.log_retention_days * 24
                elif storage_type == 'cache':
                    retention_hours = allocation.cache_retention_hours
                elif storage_type == 'temp':
                    retention_hours = allocation.temp_retention_hours
                else:
                    retention_hours = allocation.max_retention_days * 24

                cutoff_time = current_time - timedelta(hours=retention_hours)

                # Find and delete old files
                for file_path in component_path.rglob('*'):
                    if file_path.is_file():
                        try:
                            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if file_mtime < cutoff_time or force:
                                file_size = file_path.stat().st_size
                                file_path.unlink()
                                files_deleted += 1
                                space_freed += file_size
                        except (OSError, FileNotFoundError):
                            continue

            return {
                'files_deleted': files_deleted,
                'space_freed_mb': space_freed / (1024 * 1024),
                'strategy_details': f'Time-based cleanup with retention policies'
            }

        except Exception as e:
            logger.error(f"Error in time-based cleanup for {component}: {e}")
            return {'files_deleted': 0, 'space_freed_mb': 0.0, 'error': str(e)}

    async def _size_based_cleanup(self, component: str, allocation: StorageAllocation, force: bool) -> Dict[str, Any]:
        """Perform size-based cleanup."""
        try:
            files_deleted = 0
            space_freed = 0

            current_usage = await self._get_component_storage_usage(component)
            target_usage = allocation.warning_threshold_mb if not force else allocation.max_storage_mb * 0.5

            if current_usage <= target_usage and not force:
                return {
                    'files_deleted': 0,
                    'space_freed_mb': 0.0,
                    'strategy_details': f'No cleanup needed, usage {current_usage:.1f}MB < target {target_usage:.1f}MB'
                }

            # Collect all files with sizes and sort by size (largest first)
            files_to_delete = []
            for storage_type, base_path in self.base_paths.items():
                component_path = base_path / component
                if not component_path.exists():
                    continue

                for file_path in component_path.rglob('*'):
                    if file_path.is_file():
                        try:
                            file_size = file_path.stat().st_size
                            files_to_delete.append((file_path, file_size))
                        except (OSError, FileNotFoundError):
                            continue

            # Sort by size (largest first) and delete until target reached
            files_to_delete.sort(key=lambda x: x[1], reverse=True)
            space_to_free = (current_usage - target_usage) * 1024 * 1024  # Convert to bytes

            for file_path, file_size in files_to_delete:
                if space_freed >= space_to_free and not force:
                    break

                try:
                    file_path.unlink()
                    files_deleted += 1
                    space_freed += file_size
                except (OSError, FileNotFoundError):
                    continue

            return {
                'files_deleted': files_deleted,
                'space_freed_mb': space_freed / (1024 * 1024),
                'strategy_details': f'Size-based cleanup, target: {target_usage:.1f}MB'
            }

        except Exception as e:
            logger.error(f"Error in size-based cleanup for {component}: {e}")
            return {'files_deleted': 0, 'space_freed_mb': 0.0, 'error': str(e)}

    async def _lru_cleanup(self, component: str, allocation: StorageAllocation, force: bool) -> Dict[str, Any]:
        """Perform LRU (Least Recently Used) cleanup."""
        try:
            files_deleted = 0
            space_freed = 0

            # Collect all files with access times
            files_to_delete = []
            for storage_type, base_path in self.base_paths.items():
                component_path = base_path / component
                if not component_path.exists():
                    continue

                for file_path in component_path.rglob('*'):
                    if file_path.is_file():
                        try:
                            stat_info = file_path.stat()
                            access_time = stat_info.st_atime
                            file_size = stat_info.st_size
                            files_to_delete.append((file_path, access_time, file_size))
                        except (OSError, FileNotFoundError):
                            continue

            # Sort by access time (oldest first)
            files_to_delete.sort(key=lambda x: x[1])

            current_usage = await self._get_component_storage_usage(component)
            target_usage = allocation.warning_threshold_mb if not force else allocation.max_storage_mb * 0.5
            space_to_free = max(0, (current_usage - target_usage) * 1024 * 1024)  # Convert to bytes

            for file_path, access_time, file_size in files_to_delete:
                if space_freed >= space_to_free and not force:
                    break

                try:
                    file_path.unlink()
                    files_deleted += 1
                    space_freed += file_size
                except (OSError, FileNotFoundError):
                    continue

            return {
                'files_deleted': files_deleted,
                'space_freed_mb': space_freed / (1024 * 1024),
                'strategy_details': f'LRU cleanup, removed {files_deleted} least recently used files'
            }

        except Exception as e:
            logger.error(f"Error in LRU cleanup for {component}: {e}")
            return {'files_deleted': 0, 'space_freed_mb': 0.0, 'error': str(e)}

    async def _priority_based_cleanup(self, component: str, allocation: StorageAllocation, force: bool) -> Dict[str, Any]:
        """Perform priority-based cleanup."""
        try:
            files_deleted = 0
            space_freed = 0

            # Priority order: temp -> cache -> logs -> data (keep data longest)
            cleanup_order = ['temp', 'cache', 'logs', 'data', 'backup', 'config']

            current_usage = await self._get_component_storage_usage(component)
            target_usage = allocation.warning_threshold_mb if not force else allocation.max_storage_mb * 0.5

            if current_usage <= target_usage and not force:
                return {
                    'files_deleted': 0,
                    'space_freed_mb': 0.0,
                    'strategy_details': f'No cleanup needed, usage {current_usage:.1f}MB < target {target_usage:.1f}MB'
                }

            space_to_free = (current_usage - target_usage) * 1024 * 1024  # Convert to bytes

            for storage_type in cleanup_order:
                if space_freed >= space_to_free and not force:
                    break

                base_path = self.base_paths.get(storage_type)
                if not base_path:
                    continue

                component_path = base_path / component
                if not component_path.exists():
                    continue

                # Delete files in this storage type
                for file_path in component_path.rglob('*'):
                    if file_path.is_file():
                        try:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            files_deleted += 1
                            space_freed += file_size

                            if space_freed >= space_to_free and not force:
                                break
                        except (OSError, FileNotFoundError):
                            continue

            return {
                'files_deleted': files_deleted,
                'space_freed_mb': space_freed / (1024 * 1024),
                'strategy_details': f'Priority-based cleanup, order: {" -> ".join(cleanup_order)}'
            }

        except Exception as e:
            logger.error(f"Error in priority-based cleanup for {component}: {e}")
            return {'files_deleted': 0, 'space_freed_mb': 0.0, 'error': str(e)}

    async def _adaptive_cleanup(self, component: str, allocation: StorageAllocation, force: bool) -> Dict[str, Any]:
        """Perform adaptive cleanup combining multiple strategies."""
        try:
            # Start with time-based cleanup for old files
            time_result = await self._time_based_cleanup(component, allocation, False)

            # Check if more cleanup is needed
            current_usage = await self._get_component_storage_usage(component)
            target_usage = allocation.warning_threshold_mb if not force else allocation.max_storage_mb * 0.5

            if current_usage <= target_usage and not force:
                return {
                    'files_deleted': time_result['files_deleted'],
                    'space_freed_mb': time_result['space_freed_mb'],
                    'strategy_details': 'Adaptive cleanup: time-based sufficient'
                }

            # If still over target, use LRU cleanup
            lru_result = await self._lru_cleanup(component, allocation, False)

            # Check again
            current_usage = await self._get_component_storage_usage(component)
            if current_usage <= target_usage and not force:
                return {
                    'files_deleted': time_result['files_deleted'] + lru_result['files_deleted'],
                    'space_freed_mb': time_result['space_freed_mb'] + lru_result['space_freed_mb'],
                    'strategy_details': 'Adaptive cleanup: time-based + LRU'
                }

            # If still over target, use priority-based cleanup
            priority_result = await self._priority_based_cleanup(component, allocation, force)

            return {
                'files_deleted': time_result['files_deleted'] + lru_result['files_deleted'] + priority_result['files_deleted'],
                'space_freed_mb': time_result['space_freed_mb'] + lru_result['space_freed_mb'] + priority_result['space_freed_mb'],
                'strategy_details': 'Adaptive cleanup: time-based + LRU + priority-based'
            }

        except Exception as e:
            logger.error(f"Error in adaptive cleanup for {component}: {e}")
            return {'files_deleted': 0, 'space_freed_mb': 0.0, 'error': str(e)}

    # Placeholder methods for monitoring loops (to be implemented)
    async def _check_storage_alerts(self, metrics: Dict[str, Any]):
        """Check for storage-related alerts."""
        try:
            system_storage = metrics.get('system_storage', {})
            system_usage = system_storage.get('usage_percent', 0)

            # Check system-wide storage alerts
            if system_usage > self.config.system_critical_threshold:
                await self._create_storage_alert(
                    "system", "disk_critical", "critical",
                    f"System disk usage critical: {system_usage:.1f}%",
                    system_usage
                )
            elif system_usage > self.config.system_warning_threshold:
                await self._create_storage_alert(
                    "system", "disk_warning", "warning",
                    f"System disk usage high: {system_usage:.1f}%",
                    system_usage
                )

            # Check component storage alerts
            component_usage = metrics.get('component_usage', {})
            for component, usage_data in component_usage.items():
                usage_percent = usage_data.get('usage_percent', 0)
                used_mb = usage_data.get('used_mb', 0)
                allocated_mb = usage_data.get('allocated_mb', 0)

                if usage_percent > self.config.storage_critical_threshold:
                    await self._create_storage_alert(
                        component, "storage_critical", "critical",
                        f"Storage usage critical: {used_mb:.1f}/{allocated_mb:.1f}MB ({usage_percent:.1f}%)",
                        used_mb
                    )
                elif usage_percent > self.config.storage_warning_threshold:
                    await self._create_storage_alert(
                        component, "storage_warning", "warning",
                        f"Storage usage high: {used_mb:.1f}/{allocated_mb:.1f}MB ({usage_percent:.1f}%)",
                        used_mb
                    )

        except Exception as e:
            logger.error(f"Error checking storage alerts: {e}")

    async def _create_storage_alert(self, component: str, alert_type: str, severity: str, message: str, usage_mb: float):
        """Create a storage alert."""
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
            alert = StorageAlert(
                component=component,
                alert_type=alert_type,
                severity=severity,
                message=message,
                storage_usage_mb=usage_mb
            )

            self.active_alerts[alert_key] = alert
            self.alert_history.append(alert)

            logger.warning(f"Storage Alert [{severity.upper()}] {component}: {message}")

        except Exception as e:
            logger.error(f"Error creating storage alert: {e}")

    async def _update_component_metrics(self):
        """Update component storage metrics."""
        try:
            for component in self.component_allocations:
                for storage_type in StorageType:
                    if component in self.component_metrics and storage_type in self.component_metrics[component]:
                        metrics = self.component_metrics[component][storage_type]

                        # Update basic metrics
                        base_path = self.base_paths.get(storage_type.value)
                        if base_path:
                            component_path = base_path / component
                            if component_path.exists():
                                metrics.total_size_mb = (await self._get_directory_size(component_path)) / (1024 * 1024)
                                metrics.file_count = await self._count_files_recursive(component_path)
                                metrics.last_updated = datetime.now()
        except Exception as e:
            logger.error(f"Error updating component metrics: {e}")

    async def _check_cleanup_needed(self):
        """Check if cleanup is needed for any components."""
        try:
            for component, allocation in self.component_allocations.items():
                if not allocation.enable_auto_cleanup:
                    continue

                current_usage = await self._get_component_storage_usage(component)
                if current_usage > allocation.warning_threshold_mb:
                    logger.info(f"Cleanup needed for {component}: {current_usage:.1f}MB > {allocation.warning_threshold_mb:.1f}MB")
                    await self.cleanup_component_storage(component, force=False)
        except Exception as e:
            logger.error(f"Error checking cleanup needed: {e}")

    async def _perform_scheduled_cleanups(self):
        """Perform scheduled cleanups based on intervals."""
        try:
            current_time = datetime.now()

            for component, allocation in self.component_allocations.items():
                if not allocation.enable_auto_cleanup:
                    continue

                last_cleanup = self.last_cleanup.get(component)
                if not last_cleanup:
                    # Never cleaned up, do it now
                    await self.cleanup_component_storage(component, force=False)
                    continue

                time_since_cleanup = current_time - last_cleanup
                cleanup_interval = timedelta(hours=allocation.cleanup_interval_hours)

                if time_since_cleanup >= cleanup_interval:
                    logger.info(f"Scheduled cleanup for {component} (last: {time_since_cleanup} ago)")
                    await self.cleanup_component_storage(component, force=False)
        except Exception as e:
            logger.error(f"Error performing scheduled cleanups: {e}")

    async def _emergency_cleanup_check(self):
        """Check for emergency cleanup situations."""
        try:
            # Check system disk usage
            disk_usage = shutil.disk_usage('/')
            usage_percent = ((disk_usage.total - disk_usage.free) / disk_usage.total) * 100

            if usage_percent > self.config.aggressive_cleanup_threshold:
                logger.warning(f"Emergency cleanup triggered: system disk {usage_percent:.1f}% full")

                # Force cleanup on all components, starting with lowest priority
                components_by_priority = sorted(
                    self.component_allocations.items(),
                    key=lambda x: x[1].priority.value
                )

                for component, allocation in components_by_priority:
                    await self.cleanup_component_storage(component, force=True)

                    # Check if we've freed enough space
                    new_usage = shutil.disk_usage('/')
                    new_percent = ((new_usage.total - new_usage.free) / new_usage.total) * 100
                    if new_percent < self.config.storage_warning_threshold:
                        break
        except Exception as e:
            logger.error(f"Error in emergency cleanup check: {e}")

    async def _load_state(self):
        """Load previous state from disk."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)

                # Restore cleanup history
                if 'last_cleanup' in state:
                    for component, timestamp_str in state['last_cleanup'].items():
                        self.last_cleanup[component] = datetime.fromisoformat(timestamp_str)

                # Restore storage history
                if 'storage_history' in state:
                    for entry in state['storage_history'][-100:]:  # Last 100 entries
                        entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                        self.storage_history.append(entry)

                logger.info("Storage manager state loaded")

        except Exception as e:
            logger.error(f"Error loading state: {e}")

    async def _save_state(self):
        """Save current state to disk."""
        try:
            state = {
                'last_cleanup': {
                    component: timestamp.isoformat()
                    for component, timestamp in self.last_cleanup.items()
                },
                'storage_history': [
                    {
                        'timestamp': entry['timestamp'].isoformat(),
                        'metrics': entry['metrics']
                    }
                    for entry in list(self.storage_history)[-100:]  # Last 100 entries
                ],
                'cleanup_history': [
                    {
                        'component': entry['component'],
                        'files_deleted': entry['files_deleted'],
                        'space_freed_mb': entry['space_freed_mb'],
                        'timestamp': entry['timestamp']
                    }
                    for entry in list(self.cleanup_history)[-50:]  # Last 50 cleanups
                ]
            }

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

            logger.debug("Storage manager state saved")

        except Exception as e:
            logger.error(f"Error saving state: {e}")

    # Placeholder methods for optimization loops
    async def _analyze_storage_patterns(self):
        """Analyze storage usage patterns."""
        try:
            # Placeholder for storage pattern analysis
            pass
        except Exception as e:
            logger.error(f"Error analyzing storage patterns: {e}")

    async def _optimize_storage_allocation(self):
        """Optimize storage allocation based on usage patterns."""
        try:
            # Placeholder for storage allocation optimization
            pass
        except Exception as e:
            logger.error(f"Error optimizing storage allocation: {e}")

    async def _check_defragmentation_needed(self):
        """Check if defragmentation is needed."""
        try:
            # Placeholder for defragmentation check
            pass
        except Exception as e:
            logger.error(f"Error checking defragmentation: {e}")

    async def _check_filesystem_health(self):
        """Check file system health."""
        try:
            # Placeholder for filesystem health check
            pass
        except Exception as e:
            logger.error(f"Error checking filesystem health: {e}")

    async def _monitor_access_patterns(self):
        """Monitor file access patterns."""
        try:
            # Placeholder for access pattern monitoring
            pass
        except Exception as e:
            logger.error(f"Error monitoring access patterns: {e}")

    async def _check_storage_integrity(self):
        """Check storage integrity."""
        try:
            # Placeholder for storage integrity check
            pass
        except Exception as e:
            logger.error(f"Error checking storage integrity: {e}")

    async def get_storage_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive storage data for dashboard display."""
        try:
            metrics = await self.get_storage_metrics()

            # Calculate summary statistics
            total_allocated = sum(
                allocation.max_storage_mb for allocation in self.component_allocations.values()
            )
            total_used = metrics.get('total_managed_mb', 0)

            # Get recent cleanup data
            recent_cleanups = list(self.cleanup_history)[-10:] if self.cleanup_history else []

            return {
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_allocated_mb': total_allocated,
                    'total_used_mb': total_used,
                    'usage_percent': (total_used / total_allocated) * 100 if total_allocated > 0 else 0,
                    'active_alerts': len([a for a in self.active_alerts.values() if not a.resolved])
                },
                'system_metrics': metrics.get('system_storage', {}),
                'component_metrics': metrics.get('component_usage', {}),
                'storage_type_metrics': metrics.get('storage_type_usage', {}),
                'recent_cleanups': recent_cleanups,
                'base_directories': {k: str(v) for k, v in self.base_paths.items()}
            }

        except Exception as e:
            logger.error(f"Error getting storage dashboard data: {e}")
            return {}
