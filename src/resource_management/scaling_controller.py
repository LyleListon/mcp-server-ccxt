"""
Scaling Controller - Automatic Resource Adjustment for MayArbi System

The capstone component that provides intelligent, automated scaling decisions
across all system resources. Integrates with all resource managers to optimize
system performance through dynamic resource adjustment and capacity management.
"""

import asyncio
import logging
import time
import statistics
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
from collections import deque, defaultdict
import math

logger = logging.getLogger(__name__)


class ScalingAction(Enum):
    """Types of scaling actions."""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    SCALE_OUT = "scale_out"      # Add more instances
    SCALE_IN = "scale_in"        # Remove instances
    REBALANCE = "rebalance"      # Redistribute resources
    OPTIMIZE = "optimize"        # Optimize configuration
    NO_ACTION = "no_action"


class ScalingTrigger(Enum):
    """Scaling trigger types."""
    CPU_UTILIZATION = "cpu_utilization"
    MEMORY_UTILIZATION = "memory_utilization"
    NETWORK_UTILIZATION = "network_utilization"
    STORAGE_UTILIZATION = "storage_utilization"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    QUEUE_LENGTH = "queue_length"
    ERROR_RATE = "error_rate"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    PREDICTIVE = "predictive"


class ScalingStrategy(Enum):
    """Scaling strategies."""
    REACTIVE = "reactive"        # React to current conditions
    PREDICTIVE = "predictive"    # Predict future needs
    PROACTIVE = "proactive"      # Prevent issues before they occur
    ADAPTIVE = "adaptive"        # Learn and adapt over time
    CONSERVATIVE = "conservative" # Minimal changes
    AGGRESSIVE = "aggressive"    # Quick, large changes


class ResourceType(Enum):
    """Resource types for scaling."""
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    STORAGE = "storage"
    INSTANCES = "instances"
    CAPACITY = "capacity"


@dataclass
class ScalingRule:
    """Scaling rule definition."""
    rule_id: str
    component: str
    trigger: ScalingTrigger
    resource_type: ResourceType
    
    # Thresholds
    scale_up_threshold: float
    scale_down_threshold: float
    
    # Actions
    scale_up_action: ScalingAction
    scale_down_action: ScalingAction
    
    # Scaling parameters
    scale_up_amount: float = 1.2    # 20% increase
    scale_down_amount: float = 0.8  # 20% decrease
    min_value: float = 0.1
    max_value: float = 10.0
    
    # Timing
    cooldown_minutes: int = 5
    evaluation_periods: int = 3
    
    # Conditions
    enabled: bool = True
    priority: int = 5  # 1-10, higher is more important
    
    # State
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


@dataclass
class ScalingDecision:
    """Scaling decision record."""
    decision_id: str
    component: str
    trigger: ScalingTrigger
    action: ScalingAction
    resource_type: ResourceType
    
    # Decision details
    current_value: float
    target_value: float
    change_amount: float
    change_percent: float
    
    # Reasoning
    reason: str
    confidence: float  # 0-100
    expected_impact: str
    
    # Execution
    timestamp: datetime = field(default_factory=datetime.now)
    executed: bool = False
    execution_time: Optional[datetime] = None
    success: bool = False
    
    # Results
    actual_impact: Optional[str] = None
    effectiveness_score: Optional[float] = None


@dataclass
class ComponentScalingPolicy:
    """Scaling policy for a component."""
    component: str
    
    # Strategy
    strategy: ScalingStrategy = ScalingStrategy.ADAPTIVE
    
    # Resource limits
    min_cpu_allocation: float = 0.1
    max_cpu_allocation: float = 4.0
    min_memory_allocation: float = 0.1
    max_memory_allocation: float = 8.0
    min_network_allocation: float = 0.1
    max_network_allocation: float = 2.0
    min_storage_allocation: float = 0.1
    max_storage_allocation: float = 5.0
    
    # Scaling behavior
    scale_up_factor: float = 1.3
    scale_down_factor: float = 0.8
    max_scale_up_per_hour: int = 3
    max_scale_down_per_hour: int = 2
    
    # Performance targets
    target_cpu_utilization: float = 70.0
    target_memory_utilization: float = 75.0
    target_response_time_ms: float = 500.0
    target_throughput_ops_sec: float = 10.0
    
    # Scaling rules
    scaling_rules: List[ScalingRule] = field(default_factory=list)
    
    # State
    current_cpu_allocation: float = 1.0
    current_memory_allocation: float = 1.0
    current_network_allocation: float = 1.0
    current_storage_allocation: float = 1.0
    
    last_scale_up: Optional[datetime] = None
    last_scale_down: Optional[datetime] = None
    scale_up_count_hour: int = 0
    scale_down_count_hour: int = 0


@dataclass
class ScalingMetrics:
    """Scaling metrics and statistics."""
    component: str
    
    # Scaling activity
    total_scaling_decisions: int = 0
    successful_scaling_decisions: int = 0
    scale_up_count: int = 0
    scale_down_count: int = 0
    
    # Performance impact
    average_effectiveness_score: float = 0.0
    resource_efficiency_improvement: float = 0.0
    performance_improvement: float = 0.0
    
    # Timing
    average_decision_time_ms: float = 0.0
    average_execution_time_ms: float = 0.0
    
    # Current state
    current_scaling_factor: float = 1.0
    resource_utilization_score: float = 0.0
    
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ScalingAlert:
    """Scaling-related alert."""
    component: str
    alert_type: str
    severity: str
    message: str
    scaling_action: Optional[ScalingAction] = None
    resource_type: Optional[ResourceType] = None
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False


@dataclass
class ScalingConfig:
    """Configuration for scaling controller."""
    # Monitoring settings
    monitoring_interval: int = 30  # seconds
    metrics_retention_hours: int = 48
    decision_evaluation_window: int = 300  # 5 minutes
    
    # Scaling behavior
    enable_auto_scaling: bool = True
    enable_predictive_scaling: bool = True
    enable_proactive_scaling: bool = True
    
    # Global limits
    max_total_cpu_allocation: float = 16.0
    max_total_memory_allocation: float = 32.0
    max_total_network_allocation: float = 8.0
    max_total_storage_allocation: float = 20.0
    
    # Thresholds
    system_cpu_threshold: float = 80.0
    system_memory_threshold: float = 85.0
    system_network_threshold: float = 75.0
    system_storage_threshold: float = 80.0
    
    # Decision making
    min_confidence_threshold: float = 70.0
    max_decisions_per_hour: int = 10
    cooldown_between_decisions: int = 300  # 5 minutes
    
    # Performance targets
    target_system_efficiency: float = 85.0
    target_response_time_ms: float = 1000.0
    target_success_rate: float = 95.0
    
    # Alert settings
    alert_cooldown_minutes: int = 10
    max_alerts_per_hour: int = 15


class ScalingController:
    """
    Scaling Controller - Automatic resource adjustment and optimization.
    
    The capstone component that provides intelligent, automated scaling
    decisions across all system resources. Integrates with all resource
    managers to optimize system performance.
    """
    
    def __init__(self, config: Optional[ScalingConfig] = None):
        self.config = config or ScalingConfig()
        self.running = False
        
        # Component policies and metrics
        self.component_policies: Dict[str, ComponentScalingPolicy] = {}
        self.component_metrics: Dict[str, ScalingMetrics] = {}
        
        # Scaling decisions and history
        self.scaling_decisions: deque = deque(maxlen=10000)
        self.pending_decisions: List[ScalingDecision] = []
        self.decision_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Performance tracking
        self.system_performance_history: deque = deque(maxlen=1000)
        self.resource_utilization_history: deque = deque(maxlen=1000)
        self.scaling_effectiveness: Dict[str, List[float]] = defaultdict(list)
        
        # Predictive modeling
        self.performance_trends: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.load_predictions: Dict[str, List[float]] = defaultdict(list)
        
        # Alerts
        self.active_alerts: Dict[str, ScalingAlert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        
        # Integration with other managers
        self.resource_managers: Dict[str, Any] = {}
        
        # Monitoring tasks
        self.monitoring_tasks: List[asyncio.Task] = []
        
        # State persistence
        self.state_file = Path("data/scaling_controller_state.json")
        self.state_file.parent.mkdir(exist_ok=True)
        
        # Initialize component policies
        self._initialize_scaling_policies()
        
        logger.info("🎯 Scaling Controller initialized - The Grand Finale!")
    
    def _initialize_scaling_policies(self):
        """Initialize scaling policies for system components."""
        default_policies = {
            "arbitrage_engine": ComponentScalingPolicy(
                component="arbitrage_engine",
                strategy=ScalingStrategy.PROACTIVE,
                min_cpu_allocation=0.5,
                max_cpu_allocation=6.0,
                min_memory_allocation=0.5,
                max_memory_allocation=4.0,
                scale_up_factor=1.5,
                scale_down_factor=0.7,
                max_scale_up_per_hour=5,
                max_scale_down_per_hour=3,
                target_cpu_utilization=75.0,
                target_memory_utilization=70.0,
                target_response_time_ms=200.0,
                target_throughput_ops_sec=25.0
            ),
            "bridge_monitor": ComponentScalingPolicy(
                component="bridge_monitor",
                strategy=ScalingStrategy.REACTIVE,
                min_cpu_allocation=0.2,
                max_cpu_allocation=2.0,
                min_memory_allocation=0.3,
                max_memory_allocation=2.0,
                scale_up_factor=1.3,
                scale_down_factor=0.8,
                max_scale_up_per_hour=3,
                max_scale_down_per_hour=2,
                target_cpu_utilization=60.0,
                target_memory_utilization=65.0,
                target_response_time_ms=800.0,
                target_throughput_ops_sec=15.0
            ),
            "cross_chain_mev": ComponentScalingPolicy(
                component="cross_chain_mev",
                strategy=ScalingStrategy.ADAPTIVE,
                min_cpu_allocation=0.3,
                max_cpu_allocation=3.0,
                min_memory_allocation=0.3,
                max_memory_allocation=3.0,
                scale_up_factor=1.4,
                scale_down_factor=0.75,
                max_scale_up_per_hour=4,
                max_scale_down_per_hour=2,
                target_cpu_utilization=70.0,
                target_memory_utilization=70.0,
                target_response_time_ms=400.0,
                target_throughput_ops_sec=12.0
            ),
            "price_feeds": ComponentScalingPolicy(
                component="price_feeds",
                strategy=ScalingStrategy.PREDICTIVE,
                min_cpu_allocation=0.4,
                max_cpu_allocation=4.0,
                min_memory_allocation=0.5,
                max_memory_allocation=6.0,
                scale_up_factor=1.2,
                scale_down_factor=0.85,
                max_scale_up_per_hour=6,
                max_scale_down_per_hour=3,
                target_cpu_utilization=65.0,
                target_memory_utilization=80.0,
                target_response_time_ms=100.0,
                target_throughput_ops_sec=50.0
            ),
            "wallet_manager": ComponentScalingPolicy(
                component="wallet_manager",
                strategy=ScalingStrategy.CONSERVATIVE,
                min_cpu_allocation=0.1,
                max_cpu_allocation=1.0,
                min_memory_allocation=0.1,
                max_memory_allocation=1.0,
                scale_up_factor=1.1,
                scale_down_factor=0.9,
                max_scale_up_per_hour=2,
                max_scale_down_per_hour=1,
                target_cpu_utilization=50.0,
                target_memory_utilization=60.0,
                target_response_time_ms=1500.0,
                target_throughput_ops_sec=5.0
            ),
            "memory_system": ComponentScalingPolicy(
                component="memory_system",
                strategy=ScalingStrategy.ADAPTIVE,
                min_cpu_allocation=0.2,
                max_cpu_allocation=2.0,
                min_memory_allocation=1.0,
                max_memory_allocation=8.0,
                scale_up_factor=1.3,
                scale_down_factor=0.8,
                max_scale_up_per_hour=4,
                max_scale_down_per_hour=2,
                target_cpu_utilization=55.0,
                target_memory_utilization=85.0,
                target_response_time_ms=200.0,
                target_throughput_ops_sec=30.0
            ),
            "health_monitor": ComponentScalingPolicy(
                component="health_monitor",
                strategy=ScalingStrategy.CONSERVATIVE,
                min_cpu_allocation=0.1,
                max_cpu_allocation=0.5,
                min_memory_allocation=0.1,
                max_memory_allocation=0.5,
                scale_up_factor=1.1,
                scale_down_factor=0.9,
                max_scale_up_per_hour=1,
                max_scale_down_per_hour=1,
                target_cpu_utilization=30.0,
                target_memory_utilization=40.0,
                target_response_time_ms=2000.0,
                target_throughput_ops_sec=8.0
            )
        }
        
        self.component_policies.update(default_policies)
        
        # Initialize metrics for each component
        for component in default_policies:
            self.component_metrics[component] = ScalingMetrics(component=component)
        
        # Initialize scaling rules for each component
        self._initialize_scaling_rules()
        
        logger.debug(f"Initialized scaling policies for {len(default_policies)} components")

    def _initialize_scaling_rules(self):
        """Initialize scaling rules for each component."""
        try:
            for component, policy in self.component_policies.items():
                # CPU scaling rules
                cpu_scale_up_rule = ScalingRule(
                    rule_id=f"{component}_cpu_scale_up",
                    component=component,
                    trigger=ScalingTrigger.CPU_UTILIZATION,
                    resource_type=ResourceType.CPU,
                    scale_up_threshold=policy.target_cpu_utilization + 10,
                    scale_down_threshold=policy.target_cpu_utilization - 15,
                    scale_up_action=ScalingAction.SCALE_UP,
                    scale_down_action=ScalingAction.SCALE_DOWN,
                    scale_up_amount=policy.scale_up_factor,
                    scale_down_amount=policy.scale_down_factor,
                    min_value=policy.min_cpu_allocation,
                    max_value=policy.max_cpu_allocation,
                    priority=8
                )

                # Memory scaling rules
                memory_scale_up_rule = ScalingRule(
                    rule_id=f"{component}_memory_scale_up",
                    component=component,
                    trigger=ScalingTrigger.MEMORY_UTILIZATION,
                    resource_type=ResourceType.MEMORY,
                    scale_up_threshold=policy.target_memory_utilization + 10,
                    scale_down_threshold=policy.target_memory_utilization - 15,
                    scale_up_action=ScalingAction.SCALE_UP,
                    scale_down_action=ScalingAction.SCALE_DOWN,
                    scale_up_amount=policy.scale_up_factor,
                    scale_down_amount=policy.scale_down_factor,
                    min_value=policy.min_memory_allocation,
                    max_value=policy.max_memory_allocation,
                    priority=7
                )

                # Response time scaling rules
                response_time_rule = ScalingRule(
                    rule_id=f"{component}_response_time",
                    component=component,
                    trigger=ScalingTrigger.RESPONSE_TIME,
                    resource_type=ResourceType.CAPACITY,
                    scale_up_threshold=policy.target_response_time_ms * 1.5,
                    scale_down_threshold=policy.target_response_time_ms * 0.7,
                    scale_up_action=ScalingAction.SCALE_UP,
                    scale_down_action=ScalingAction.SCALE_DOWN,
                    scale_up_amount=policy.scale_up_factor,
                    scale_down_amount=policy.scale_down_factor,
                    priority=9
                )

                policy.scaling_rules = [cpu_scale_up_rule, memory_scale_up_rule, response_time_rule]

        except Exception as e:
            logger.error(f"Error initializing scaling rules: {e}")

    async def start_scaling_controller(self):
        """Start the scaling controller system."""
        if self.running:
            logger.warning("Scaling controller already running")
            return

        self.running = True
        logger.info("🚀 Starting Scaling Controller System - The Final Component!")

        # Load previous state
        await self._load_state()

        # Initialize scaling system
        await self._initialize_scaling_system()

        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._scaling_monitor_loop()),
            asyncio.create_task(self._decision_engine_loop()),
            asyncio.create_task(self._execution_loop()),
            asyncio.create_task(self._optimization_loop())
        ]

        logger.info("✅ Scaling Controller System started - Resource Management Complete!")

    async def stop_scaling_controller(self):
        """Stop the scaling controller system."""
        if not self.running:
            return

        self.running = False
        logger.info("🛑 Stopping Scaling Controller System")

        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

        # Save state
        await self._save_state()

        logger.info("✅ Scaling Controller System stopped")

    async def _initialize_scaling_system(self):
        """Initialize the scaling system."""
        try:
            # Initialize resource manager connections
            await self._initialize_resource_manager_connections()

            # Initialize performance baselines
            await self._initialize_performance_baselines()

            # Initialize predictive models
            await self._initialize_predictive_models()

            logger.info("Scaling system initialized")

        except Exception as e:
            logger.error(f"Error initializing scaling system: {e}")

    async def get_scaling_metrics(self) -> Dict[str, Any]:
        """Get current scaling metrics and status."""
        try:
            # System-wide metrics
            total_decisions = sum(m.total_scaling_decisions for m in self.component_metrics.values())
            successful_decisions = sum(m.successful_scaling_decisions for m in self.component_metrics.values())

            # Resource allocation totals
            total_cpu_allocation = sum(p.current_cpu_allocation for p in self.component_policies.values())
            total_memory_allocation = sum(p.current_memory_allocation for p in self.component_policies.values())
            total_network_allocation = sum(p.current_network_allocation for p in self.component_policies.values())
            total_storage_allocation = sum(p.current_storage_allocation for p in self.component_policies.values())

            # Component metrics
            component_metrics = {}
            for component, policy in self.component_policies.items():
                metrics = self.component_metrics.get(component)
                if metrics:
                    component_metrics[component] = {
                        'strategy': policy.strategy.value,
                        'current_allocations': {
                            'cpu': policy.current_cpu_allocation,
                            'memory': policy.current_memory_allocation,
                            'network': policy.current_network_allocation,
                            'storage': policy.current_storage_allocation
                        },
                        'allocation_limits': {
                            'cpu': {'min': policy.min_cpu_allocation, 'max': policy.max_cpu_allocation},
                            'memory': {'min': policy.min_memory_allocation, 'max': policy.max_memory_allocation},
                            'network': {'min': policy.min_network_allocation, 'max': policy.max_network_allocation},
                            'storage': {'min': policy.min_storage_allocation, 'max': policy.max_storage_allocation}
                        },
                        'performance_targets': {
                            'cpu_utilization': policy.target_cpu_utilization,
                            'memory_utilization': policy.target_memory_utilization,
                            'response_time_ms': policy.target_response_time_ms,
                            'throughput_ops_sec': policy.target_throughput_ops_sec
                        },
                        'scaling_activity': {
                            'total_decisions': metrics.total_scaling_decisions,
                            'successful_decisions': metrics.successful_scaling_decisions,
                            'scale_up_count': metrics.scale_up_count,
                            'scale_down_count': metrics.scale_down_count,
                            'success_rate': (metrics.successful_scaling_decisions / max(metrics.total_scaling_decisions, 1)) * 100
                        },
                        'performance_metrics': {
                            'effectiveness_score': metrics.average_effectiveness_score,
                            'efficiency_improvement': metrics.resource_efficiency_improvement,
                            'performance_improvement': metrics.performance_improvement,
                            'current_scaling_factor': metrics.current_scaling_factor
                        },
                        'scaling_rules': len(policy.scaling_rules),
                        'last_scale_up': policy.last_scale_up.isoformat() if policy.last_scale_up else None,
                        'last_scale_down': policy.last_scale_down.isoformat() if policy.last_scale_down else None
                    }

            # Recent decisions
            recent_decisions = [
                {
                    'decision_id': d.decision_id,
                    'component': d.component,
                    'action': d.action.value,
                    'resource_type': d.resource_type.value,
                    'change_percent': d.change_percent,
                    'confidence': d.confidence,
                    'executed': d.executed,
                    'success': d.success,
                    'timestamp': d.timestamp.isoformat()
                }
                for d in list(self.scaling_decisions)[-10:]  # Last 10 decisions
            ]

            return {
                'timestamp': datetime.now().isoformat(),
                'system_metrics': {
                    'auto_scaling_enabled': self.config.enable_auto_scaling,
                    'predictive_scaling_enabled': self.config.enable_predictive_scaling,
                    'total_scaling_decisions': total_decisions,
                    'successful_decisions': successful_decisions,
                    'success_rate': (successful_decisions / max(total_decisions, 1)) * 100,
                    'pending_decisions': len(self.pending_decisions),
                    'active_alerts': len([a for a in self.active_alerts.values() if not a.resolved])
                },
                'resource_allocations': {
                    'cpu': {
                        'total': total_cpu_allocation,
                        'max_allowed': self.config.max_total_cpu_allocation,
                        'utilization_percent': (total_cpu_allocation / self.config.max_total_cpu_allocation) * 100
                    },
                    'memory': {
                        'total': total_memory_allocation,
                        'max_allowed': self.config.max_total_memory_allocation,
                        'utilization_percent': (total_memory_allocation / self.config.max_total_memory_allocation) * 100
                    },
                    'network': {
                        'total': total_network_allocation,
                        'max_allowed': self.config.max_total_network_allocation,
                        'utilization_percent': (total_network_allocation / self.config.max_total_network_allocation) * 100
                    },
                    'storage': {
                        'total': total_storage_allocation,
                        'max_allowed': self.config.max_total_storage_allocation,
                        'utilization_percent': (total_storage_allocation / self.config.max_total_storage_allocation) * 100
                    }
                },
                'component_metrics': component_metrics,
                'recent_decisions': recent_decisions
            }

        except Exception as e:
            logger.error(f"Error getting scaling metrics: {e}")
            return {}

    # Monitoring loops
    async def _scaling_monitor_loop(self):
        """Main scaling monitoring loop."""
        while self.running:
            try:
                # Collect current system metrics
                await self._collect_system_metrics()

                # Evaluate scaling rules
                await self._evaluate_scaling_rules()

                # Check for scaling alerts
                await self._check_scaling_alerts()

                # Update performance trends
                await self._update_performance_trends()

                await asyncio.sleep(self.config.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scaling monitor loop: {e}")
                await asyncio.sleep(30)

    async def _decision_engine_loop(self):
        """Scaling decision engine loop."""
        while self.running:
            try:
                # Generate scaling decisions
                await self._generate_scaling_decisions()

                # Evaluate decision confidence
                await self._evaluate_decision_confidence()

                # Prioritize decisions
                await self._prioritize_scaling_decisions()

                await asyncio.sleep(60)  # Run every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in decision engine loop: {e}")
                await asyncio.sleep(30)

    async def _execution_loop(self):
        """Scaling execution loop."""
        while self.running:
            try:
                # Execute pending decisions
                await self._execute_scaling_decisions()

                # Monitor execution results
                await self._monitor_execution_results()

                # Update effectiveness scores
                await self._update_effectiveness_scores()

                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in execution loop: {e}")
                await asyncio.sleep(15)

    async def _optimization_loop(self):
        """Scaling optimization loop."""
        while self.running:
            try:
                # Optimize scaling policies
                await self._optimize_scaling_policies()

                # Update predictive models
                if self.config.enable_predictive_scaling:
                    await self._update_predictive_models()

                # Optimize resource allocation
                await self._optimize_resource_allocation()

                # Clean up old data
                await self._cleanup_old_data()

                await asyncio.sleep(300)  # Optimize every 5 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(120)

    async def make_scaling_decision(self, component: str, trigger: ScalingTrigger,
                                  current_value: float, target_value: float) -> Optional[ScalingDecision]:
        """Make a scaling decision for a component."""
        try:
            policy = self.component_policies.get(component)
            if not policy:
                logger.warning(f"No scaling policy found for component {component}")
                return None

            # Find applicable scaling rule
            applicable_rule = None
            for rule in policy.scaling_rules:
                if rule.trigger == trigger and rule.enabled:
                    applicable_rule = rule
                    break

            if not applicable_rule:
                return None

            # Determine scaling action
            action = ScalingAction.NO_ACTION
            change_amount = 0.0

            if current_value > applicable_rule.scale_up_threshold:
                action = applicable_rule.scale_up_action
                change_amount = applicable_rule.scale_up_amount
            elif current_value < applicable_rule.scale_down_threshold:
                action = applicable_rule.scale_down_action
                change_amount = applicable_rule.scale_down_amount

            if action == ScalingAction.NO_ACTION:
                return None

            # Check cooldown
            if applicable_rule.last_triggered:
                time_since_last = datetime.now() - applicable_rule.last_triggered
                if time_since_last.total_seconds() < (applicable_rule.cooldown_minutes * 60):
                    logger.debug(f"Scaling rule {applicable_rule.rule_id} in cooldown")
                    return None

            # Calculate target value and confidence
            if action in [ScalingAction.SCALE_UP, ScalingAction.SCALE_DOWN]:
                new_target = target_value * change_amount
                new_target = max(applicable_rule.min_value, min(applicable_rule.max_value, new_target))
                change_percent = ((new_target - target_value) / target_value) * 100
            else:
                new_target = target_value
                change_percent = 0.0

            # Calculate confidence based on multiple factors
            confidence = await self._calculate_decision_confidence(
                component, trigger, current_value, target_value, new_target
            )

            # Create scaling decision
            decision = ScalingDecision(
                decision_id=f"{component}_{trigger.value}_{int(time.time())}",
                component=component,
                trigger=trigger,
                action=action,
                resource_type=applicable_rule.resource_type,
                current_value=current_value,
                target_value=new_target,
                change_amount=new_target - target_value,
                change_percent=change_percent,
                reason=f"{trigger.value} {current_value:.2f} vs threshold {applicable_rule.scale_up_threshold if action == ScalingAction.SCALE_UP else applicable_rule.scale_down_threshold}",
                confidence=confidence,
                expected_impact=f"{'Increase' if change_percent > 0 else 'Decrease'} {applicable_rule.resource_type.value} by {abs(change_percent):.1f}%"
            )

            # Update rule state
            applicable_rule.last_triggered = datetime.now()
            applicable_rule.trigger_count += 1

            logger.info(f"Scaling decision created: {decision.component} {decision.action.value} {decision.resource_type.value} by {decision.change_percent:.1f}% (confidence: {decision.confidence:.1f}%)")

            return decision

        except Exception as e:
            logger.error(f"Error making scaling decision for {component}: {e}")
            return None

    async def _calculate_decision_confidence(self, component: str, trigger: ScalingTrigger,
                                           current_value: float, target_value: float,
                                           new_target: float) -> float:
        """Calculate confidence score for a scaling decision."""
        try:
            confidence_factors = []

            # Factor 1: Deviation from target (higher deviation = higher confidence)
            deviation = abs(current_value - target_value) / target_value
            deviation_confidence = min(100, deviation * 200)  # Scale to 0-100
            confidence_factors.append(deviation_confidence)

            # Factor 2: Historical effectiveness for this component
            if component in self.scaling_effectiveness:
                recent_effectiveness = self.scaling_effectiveness[component][-10:]  # Last 10 decisions
                if recent_effectiveness:
                    avg_effectiveness = statistics.mean(recent_effectiveness)
                    confidence_factors.append(avg_effectiveness)

            # Factor 3: System stability (lower volatility = higher confidence)
            if component in self.decision_history:
                recent_decisions = list(self.decision_history[component])[-5:]  # Last 5 decisions
                if len(recent_decisions) > 1:
                    decision_times = [d['timestamp'] for d in recent_decisions]
                    time_diffs = [(decision_times[i] - decision_times[i-1]).total_seconds()
                                for i in range(1, len(decision_times))]
                    if time_diffs:
                        avg_time_between = statistics.mean(time_diffs)
                        stability_confidence = min(100, avg_time_between / 300)  # 5 minutes = 100% confidence
                        confidence_factors.append(stability_confidence)

            # Factor 4: Resource availability
            policy = self.component_policies.get(component)
            if policy:
                if trigger == ScalingTrigger.CPU_UTILIZATION:
                    resource_headroom = (policy.max_cpu_allocation - policy.current_cpu_allocation) / policy.max_cpu_allocation
                elif trigger == ScalingTrigger.MEMORY_UTILIZATION:
                    resource_headroom = (policy.max_memory_allocation - policy.current_memory_allocation) / policy.max_memory_allocation
                else:
                    resource_headroom = 0.5  # Default

                headroom_confidence = resource_headroom * 100
                confidence_factors.append(headroom_confidence)

            # Calculate overall confidence
            if confidence_factors:
                overall_confidence = statistics.mean(confidence_factors)
            else:
                overall_confidence = 50.0  # Default moderate confidence

            return min(100.0, max(0.0, overall_confidence))

        except Exception as e:
            logger.error(f"Error calculating decision confidence: {e}")
            return 50.0  # Default moderate confidence

    # Placeholder methods for monitoring loops (to be implemented)
    async def _collect_system_metrics(self):
        """Collect current system metrics from all resource managers."""
        try:
            # In a real implementation, this would collect metrics from:
            # - CPU Manager
            # - Memory Manager
            # - Network Manager
            # - Storage Manager
            # - Performance Monitor
            # - Load Balancer

            # For now, simulate metrics collection
            current_time = datetime.now()

            for component in self.component_policies:
                # Simulate current resource utilization
                policy = self.component_policies[component]

                # Store system performance history
                self.system_performance_history.append({
                    'timestamp': current_time,
                    'component': component,
                    'cpu_utilization': policy.target_cpu_utilization + (time.time() % 20 - 10),  # Simulate variation
                    'memory_utilization': policy.target_memory_utilization + (time.time() % 15 - 7.5),
                    'response_time_ms': policy.target_response_time_ms + (time.time() % 100 - 50)
                })

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    async def _evaluate_scaling_rules(self):
        """Evaluate scaling rules for all components."""
        try:
            for component, policy in self.component_policies.items():
                for rule in policy.scaling_rules:
                    if not rule.enabled:
                        continue

                    # Get current value for the trigger
                    current_value = await self._get_current_trigger_value(component, rule.trigger)
                    if current_value is None:
                        continue

                    # Get target value
                    target_value = await self._get_target_value(component, rule.resource_type)

                    # Make scaling decision if needed
                    decision = await self.make_scaling_decision(component, rule.trigger, current_value, target_value)
                    if decision and decision.confidence >= self.config.min_confidence_threshold:
                        self.pending_decisions.append(decision)

        except Exception as e:
            logger.error(f"Error evaluating scaling rules: {e}")

    async def _get_current_trigger_value(self, component: str, trigger: ScalingTrigger) -> Optional[float]:
        """Get current value for a scaling trigger."""
        try:
            policy = self.component_policies.get(component)
            if not policy:
                return None

            # Simulate getting current values
            if trigger == ScalingTrigger.CPU_UTILIZATION:
                return policy.target_cpu_utilization + (time.time() % 20 - 10)
            elif trigger == ScalingTrigger.MEMORY_UTILIZATION:
                return policy.target_memory_utilization + (time.time() % 15 - 7.5)
            elif trigger == ScalingTrigger.RESPONSE_TIME:
                return policy.target_response_time_ms + (time.time() % 100 - 50)
            else:
                return None

        except Exception as e:
            logger.error(f"Error getting current trigger value: {e}")
            return None

    async def _get_target_value(self, component: str, resource_type: ResourceType) -> float:
        """Get target value for a resource type."""
        try:
            policy = self.component_policies.get(component)
            if not policy:
                return 1.0

            if resource_type == ResourceType.CPU:
                return policy.current_cpu_allocation
            elif resource_type == ResourceType.MEMORY:
                return policy.current_memory_allocation
            elif resource_type == ResourceType.NETWORK:
                return policy.current_network_allocation
            elif resource_type == ResourceType.STORAGE:
                return policy.current_storage_allocation
            else:
                return 1.0

        except Exception as e:
            logger.error(f"Error getting target value: {e}")
            return 1.0

    async def _check_scaling_alerts(self):
        """Check for scaling-related alerts."""
        try:
            # Check system resource limits
            total_cpu = sum(p.current_cpu_allocation for p in self.component_policies.values())
            total_memory = sum(p.current_memory_allocation for p in self.component_policies.values())

            if total_cpu > self.config.max_total_cpu_allocation * 0.9:
                await self._create_scaling_alert(
                    "system", "cpu_limit_approaching", "warning",
                    f"Total CPU allocation approaching limit: {total_cpu:.1f}/{self.config.max_total_cpu_allocation}",
                    ScalingAction.SCALE_DOWN, ResourceType.CPU
                )

            if total_memory > self.config.max_total_memory_allocation * 0.9:
                await self._create_scaling_alert(
                    "system", "memory_limit_approaching", "warning",
                    f"Total memory allocation approaching limit: {total_memory:.1f}/{self.config.max_total_memory_allocation}",
                    ScalingAction.SCALE_DOWN, ResourceType.MEMORY
                )

        except Exception as e:
            logger.error(f"Error checking scaling alerts: {e}")

    async def _create_scaling_alert(self, component: str, alert_type: str, severity: str,
                                  message: str, scaling_action: Optional[ScalingAction] = None,
                                  resource_type: Optional[ResourceType] = None):
        """Create a scaling alert."""
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
            alert = ScalingAlert(
                component=component,
                alert_type=alert_type,
                severity=severity,
                message=message,
                scaling_action=scaling_action,
                resource_type=resource_type
            )

            self.active_alerts[alert_key] = alert
            self.alert_history.append(alert)

            logger.warning(f"Scaling Alert [{severity.upper()}] {component}: {message}")

        except Exception as e:
            logger.error(f"Error creating scaling alert: {e}")

    # Placeholder methods for other loops
    async def _update_performance_trends(self):
        """Update performance trends."""
        try:
            # Placeholder for performance trend analysis
            pass
        except Exception as e:
            logger.error(f"Error updating performance trends: {e}")

    async def _generate_scaling_decisions(self):
        """Generate scaling decisions."""
        try:
            # This is handled in _evaluate_scaling_rules
            pass
        except Exception as e:
            logger.error(f"Error generating scaling decisions: {e}")

    async def _evaluate_decision_confidence(self):
        """Evaluate decision confidence."""
        try:
            # Filter out low confidence decisions
            high_confidence_decisions = [
                d for d in self.pending_decisions
                if d.confidence >= self.config.min_confidence_threshold
            ]
            self.pending_decisions = high_confidence_decisions
        except Exception as e:
            logger.error(f"Error evaluating decision confidence: {e}")

    async def _prioritize_scaling_decisions(self):
        """Prioritize scaling decisions."""
        try:
            # Sort by confidence and priority
            self.pending_decisions.sort(key=lambda d: (d.confidence, d.trigger.value), reverse=True)
        except Exception as e:
            logger.error(f"Error prioritizing scaling decisions: {e}")

    async def _execute_scaling_decisions(self):
        """Execute pending scaling decisions."""
        try:
            if not self.config.enable_auto_scaling:
                return

            executed_count = 0
            max_executions = min(len(self.pending_decisions), 3)  # Limit concurrent executions

            for decision in self.pending_decisions[:max_executions]:
                if await self._execute_single_decision(decision):
                    executed_count += 1

            # Remove executed decisions
            self.pending_decisions = self.pending_decisions[executed_count:]

        except Exception as e:
            logger.error(f"Error executing scaling decisions: {e}")

    async def _execute_single_decision(self, decision: ScalingDecision) -> bool:
        """Execute a single scaling decision."""
        try:
            policy = self.component_policies.get(decision.component)
            if not policy:
                return False

            # Apply the scaling decision
            if decision.resource_type == ResourceType.CPU:
                old_value = policy.current_cpu_allocation
                policy.current_cpu_allocation = decision.target_value
                logger.info(f"Scaled {decision.component} CPU: {old_value:.2f} -> {decision.target_value:.2f}")
            elif decision.resource_type == ResourceType.MEMORY:
                old_value = policy.current_memory_allocation
                policy.current_memory_allocation = decision.target_value
                logger.info(f"Scaled {decision.component} Memory: {old_value:.2f} -> {decision.target_value:.2f}")
            elif decision.resource_type == ResourceType.NETWORK:
                old_value = policy.current_network_allocation
                policy.current_network_allocation = decision.target_value
                logger.info(f"Scaled {decision.component} Network: {old_value:.2f} -> {decision.target_value:.2f}")
            elif decision.resource_type == ResourceType.STORAGE:
                old_value = policy.current_storage_allocation
                policy.current_storage_allocation = decision.target_value
                logger.info(f"Scaled {decision.component} Storage: {old_value:.2f} -> {decision.target_value:.2f}")

            # Update decision status
            decision.executed = True
            decision.execution_time = datetime.now()
            decision.success = True

            # Update metrics
            metrics = self.component_metrics.get(decision.component)
            if metrics:
                metrics.total_scaling_decisions += 1
                metrics.successful_scaling_decisions += 1
                if decision.action == ScalingAction.SCALE_UP:
                    metrics.scale_up_count += 1
                elif decision.action == ScalingAction.SCALE_DOWN:
                    metrics.scale_down_count += 1

            # Add to decision history
            self.scaling_decisions.append(decision)
            self.decision_history[decision.component].append({
                'timestamp': decision.timestamp,
                'action': decision.action.value,
                'resource_type': decision.resource_type.value,
                'change_percent': decision.change_percent,
                'success': decision.success
            })

            return True

        except Exception as e:
            logger.error(f"Error executing scaling decision {decision.decision_id}: {e}")
            decision.success = False
            return False

    # Placeholder methods for remaining loops
    async def _monitor_execution_results(self):
        """Monitor execution results."""
        try:
            # Placeholder for execution result monitoring
            pass
        except Exception as e:
            logger.error(f"Error monitoring execution results: {e}")

    async def _update_effectiveness_scores(self):
        """Update effectiveness scores."""
        try:
            # Calculate effectiveness for recent decisions
            for component in self.component_policies:
                recent_decisions = [d for d in self.scaling_decisions
                                 if d.component == component and d.executed and
                                 datetime.now() - d.execution_time < timedelta(hours=1)]

                if recent_decisions:
                    # Simple effectiveness calculation
                    effectiveness = sum(80.0 if d.success else 20.0 for d in recent_decisions) / len(recent_decisions)
                    self.scaling_effectiveness[component].append(effectiveness)

                    # Update component metrics
                    metrics = self.component_metrics.get(component)
                    if metrics:
                        metrics.average_effectiveness_score = effectiveness

        except Exception as e:
            logger.error(f"Error updating effectiveness scores: {e}")

    async def _optimize_scaling_policies(self):
        """Optimize scaling policies."""
        try:
            # Placeholder for policy optimization
            pass
        except Exception as e:
            logger.error(f"Error optimizing scaling policies: {e}")

    async def _update_predictive_models(self):
        """Update predictive models."""
        try:
            # Placeholder for predictive model updates
            pass
        except Exception as e:
            logger.error(f"Error updating predictive models: {e}")

    async def _optimize_resource_allocation(self):
        """Optimize resource allocation."""
        try:
            # Placeholder for resource allocation optimization
            pass
        except Exception as e:
            logger.error(f"Error optimizing resource allocation: {e}")

    async def _cleanup_old_data(self):
        """Clean up old data."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.config.metrics_retention_hours)

            # Clean up system performance history
            while (self.system_performance_history and
                   self.system_performance_history[0]['timestamp'] < cutoff_time):
                self.system_performance_history.popleft()

            # Clean up decision history
            for component in self.decision_history:
                while (self.decision_history[component] and
                       self.decision_history[component][0]['timestamp'] < cutoff_time):
                    self.decision_history[component].popleft()

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")

    # Initialization helper methods
    async def _initialize_resource_manager_connections(self):
        """Initialize connections to other resource managers."""
        try:
            # Placeholder for resource manager connections
            # In a real implementation, this would establish connections to:
            # - CPU Manager
            # - Memory Manager
            # - Network Manager
            # - Storage Manager
            # - Performance Monitor
            # - Load Balancer
            pass
        except Exception as e:
            logger.error(f"Error initializing resource manager connections: {e}")

    async def _initialize_performance_baselines(self):
        """Initialize performance baselines."""
        try:
            # Placeholder for performance baseline initialization
            pass
        except Exception as e:
            logger.error(f"Error initializing performance baselines: {e}")

    async def _initialize_predictive_models(self):
        """Initialize predictive models."""
        try:
            # Placeholder for predictive model initialization
            pass
        except Exception as e:
            logger.error(f"Error initializing predictive models: {e}")

    # State management
    async def _load_state(self):
        """Load previous state from disk."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)

                # Restore component allocations
                if 'component_allocations' in state:
                    for component, allocations in state['component_allocations'].items():
                        if component in self.component_policies:
                            policy = self.component_policies[component]
                            policy.current_cpu_allocation = allocations.get('cpu', 1.0)
                            policy.current_memory_allocation = allocations.get('memory', 1.0)
                            policy.current_network_allocation = allocations.get('network', 1.0)
                            policy.current_storage_allocation = allocations.get('storage', 1.0)

                # Restore scaling effectiveness
                if 'scaling_effectiveness' in state:
                    for component, effectiveness_list in state['scaling_effectiveness'].items():
                        self.scaling_effectiveness[component] = effectiveness_list[-50:]  # Last 50 entries

                logger.info("Scaling controller state loaded")

        except Exception as e:
            logger.error(f"Error loading state: {e}")

    async def _save_state(self):
        """Save current state to disk."""
        try:
            state = {
                'component_allocations': {
                    component: {
                        'cpu': policy.current_cpu_allocation,
                        'memory': policy.current_memory_allocation,
                        'network': policy.current_network_allocation,
                        'storage': policy.current_storage_allocation
                    }
                    for component, policy in self.component_policies.items()
                },
                'scaling_effectiveness': {
                    component: list(effectiveness)[-50:]  # Last 50 entries
                    for component, effectiveness in self.scaling_effectiveness.items()
                },
                'total_decisions': len(self.scaling_decisions),
                'system_performance_score': sum(
                    m.average_effectiveness_score for m in self.component_metrics.values()
                ) / max(len(self.component_metrics), 1)
            }

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

            logger.debug("Scaling controller state saved")

        except Exception as e:
            logger.error(f"Error saving state: {e}")

    async def get_scaling_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive scaling data for dashboard display."""
        try:
            metrics = await self.get_scaling_metrics()

            # Recent scaling activity
            recent_decisions = [d for d in self.scaling_decisions
                              if datetime.now() - d.timestamp < timedelta(hours=1)]

            scaling_activity = {
                'recent_decisions_count': len(recent_decisions),
                'successful_decisions_count': sum(1 for d in recent_decisions if d.success),
                'pending_decisions_count': len(self.pending_decisions),
                'by_action': {},
                'by_component': {}
            }

            # Group by action and component
            for action in ScalingAction:
                action_decisions = [d for d in recent_decisions if d.action == action]
                scaling_activity['by_action'][action.value] = len(action_decisions)

            for component in self.component_policies:
                component_decisions = [d for d in recent_decisions if d.component == component]
                scaling_activity['by_component'][component] = len(component_decisions)

            # System health summary
            total_cpu = sum(p.current_cpu_allocation for p in self.component_policies.values())
            total_memory = sum(p.current_memory_allocation for p in self.component_policies.values())

            system_health = {
                'resource_utilization': {
                    'cpu_percent': (total_cpu / self.config.max_total_cpu_allocation) * 100,
                    'memory_percent': (total_memory / self.config.max_total_memory_allocation) * 100
                },
                'scaling_enabled': self.config.enable_auto_scaling,
                'predictive_enabled': self.config.enable_predictive_scaling,
                'active_alerts': len([a for a in self.active_alerts.values() if not a.resolved])
            }

            return {
                'timestamp': datetime.now().isoformat(),
                'system_metrics': metrics.get('system_metrics', {}),
                'resource_allocations': metrics.get('resource_allocations', {}),
                'component_metrics': metrics.get('component_metrics', {}),
                'scaling_activity': scaling_activity,
                'system_health': system_health,
                'recent_decisions': metrics.get('recent_decisions', [])
            }

        except Exception as e:
            logger.error(f"Error getting scaling dashboard data: {e}")
            return {}
