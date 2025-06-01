"""
Resource Management System - Phase 4 of System Integration Plan

This module provides comprehensive resource management for the MayArbi arbitrage system,
including CPU allocation, memory optimization, network bandwidth management, storage
optimization, performance monitoring, load balancing, and automatic scaling.

Components:
- ResourceManager: Main orchestrator for all resource management operations
- CPUManager: CPU allocation and monitoring
- MemoryManager: Memory usage optimization and garbage collection
- NetworkManager: Bandwidth allocation and connection management ✅ COMPLETE
- StorageManager: Disk usage monitoring and cleanup policies ✅ COMPLETE
- PerformanceMonitor: Real-time resource utilization tracking ✅ COMPLETE
- LoadBalancer: Work distribution across system components ✅ COMPLETE
- ScalingController: Automatic resource adjustment based on load ✅ COMPLETE

Integration:
- Health Monitor: Resource health alerts and metrics
- Error Manager: Resource-related error recovery strategies
- Data Flow Coordinator: Resource usage data flows
- Master System: Main system orchestrator integration
"""

from .resource_manager import (
    ResourceManager,
    ResourceConfig,
    ResourceMetrics,
    ResourceStatus,
    ResourceAlert,
    ResourceAllocation
)

from .network_manager import (
    NetworkManager,
    NetworkConfig,
    NetworkAllocation,
    NetworkPriority,
    ConnectionType,
    RateLimitStrategy,
    ConnectionMetrics,
    NetworkAlert
)

from .storage_manager import (
    StorageManager,
    StorageConfig,
    StorageAllocation,
    StoragePriority,
    CleanupStrategy,
    StorageType,
    StorageMetrics,
    StorageAlert
)

from .performance_monitor import (
    PerformanceMonitor,
    PerformanceConfig,
    PerformanceTarget,
    PerformanceMetrics,
    PerformanceLevel,
    BottleneckType,
    TrendDirection,
    OptimizationType,
    OptimizationRecommendation,
    PerformanceAlert
)

from .load_balancer import (
    LoadBalancer,
    LoadBalancerConfig,
    WorkloadRequest,
    ComponentCapacity,
    LoadBalancingMetrics,
    LoadBalancingAlgorithm,
    WorkloadType,
    ComponentStatus,
    LoadPriority,
    LoadBalancerAlert
)

from .scaling_controller import (
    ScalingController,
    ScalingConfig,
    ScalingRule,
    ScalingDecision,
    ComponentScalingPolicy,
    ScalingMetrics,
    ScalingAlert,
    ScalingAction,
    ScalingTrigger,
    ScalingStrategy,
    ResourceType
)

__all__ = [
    'ResourceManager',
    'ResourceConfig',
    'ResourceMetrics',
    'ResourceStatus',
    'ResourceAlert',
    'ResourceAllocation',
    'NetworkManager',
    'NetworkConfig',
    'NetworkAllocation',
    'NetworkPriority',
    'ConnectionType',
    'RateLimitStrategy',
    'ConnectionMetrics',
    'NetworkAlert',
    'StorageManager',
    'StorageConfig',
    'StorageAllocation',
    'StoragePriority',
    'CleanupStrategy',
    'StorageType',
    'StorageMetrics',
    'StorageAlert',
    'PerformanceMonitor',
    'PerformanceConfig',
    'PerformanceTarget',
    'PerformanceMetrics',
    'PerformanceLevel',
    'BottleneckType',
    'TrendDirection',
    'OptimizationType',
    'OptimizationRecommendation',
    'PerformanceAlert',
    'LoadBalancer',
    'LoadBalancerConfig',
    'WorkloadRequest',
    'ComponentCapacity',
    'LoadBalancingMetrics',
    'LoadBalancingAlgorithm',
    'WorkloadType',
    'ComponentStatus',
    'LoadPriority',
    'LoadBalancerAlert',
    'ScalingController',
    'ScalingConfig',
    'ScalingRule',
    'ScalingDecision',
    'ComponentScalingPolicy',
    'ScalingMetrics',
    'ScalingAlert',
    'ScalingAction',
    'ScalingTrigger',
    'ScalingStrategy',
    'ResourceType'
]

__version__ = "1.0.0"
__author__ = "MayArbi System Integration Team"
