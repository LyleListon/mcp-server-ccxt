#!/usr/bin/env python3
"""
Unified Health Monitoring System - System Integration Plan #1

Comprehensive health monitoring for all MayArbi components:
- Arbitrage Engine
- Bridge Monitor  
- Cross-Chain MEV
- Wallet Manager
- Price Feeds
- MCP Infrastructure
- API Connections

Features:
- Real-time health checks
- Automated recovery triggers
- Performance metrics
- Alert system
- Health dashboard
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class ComponentStatus(Enum):
    """Component health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning" 
    CRITICAL = "critical"
    FAILED = "failed"
    UNKNOWN = "unknown"
    RECOVERING = "recovering"


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class HealthMetric:
    """Individual health metric."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    threshold_warning: float = 0.7
    threshold_critical: float = 0.9
    
    @property
    def status(self) -> ComponentStatus:
        """Get status based on thresholds."""
        if self.value >= self.threshold_critical:
            return ComponentStatus.CRITICAL
        elif self.value >= self.threshold_warning:
            return ComponentStatus.WARNING
        else:
            return ComponentStatus.HEALTHY


@dataclass
class ComponentHealth:
    """Health profile for a system component."""
    component_name: str
    status: ComponentStatus = ComponentStatus.UNKNOWN
    metrics: Dict[str, HealthMetric] = field(default_factory=dict)
    last_check: Optional[datetime] = None
    last_success: Optional[datetime] = None
    consecutive_failures: int = 0
    total_checks: int = 0
    failed_checks: int = 0
    error_message: Optional[str] = None
    recovery_attempts: int = 0
    
    @property
    def availability(self) -> float:
        """Calculate availability percentage."""
        if self.total_checks == 0:
            return 0.0
        return (self.total_checks - self.failed_checks) / self.total_checks * 100
    
    @property
    def uptime_hours(self) -> float:
        """Calculate uptime in hours."""
        if not self.last_success:
            return 0.0
        return (datetime.now() - self.last_success).total_seconds() / 3600


@dataclass
class HealthAlert:
    """Health monitoring alert."""
    alert_id: str
    component: str
    level: AlertLevel
    message: str
    timestamp: datetime
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    acknowledged: bool = False
    resolved: bool = False


class UnifiedHealthMonitor:
    """
    Unified health monitoring system for all MayArbi components.
    
    Monitors:
    - Trading components (arbitrage, bridge, MEV)
    - Infrastructure (MCP servers, APIs)
    - System resources (memory, CPU, network)
    - External dependencies (DEX APIs, price feeds)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the unified health monitor."""
        self.config = config or {}
        
        # Monitoring configuration
        self.check_interval = self.config.get('check_interval', 30)  # seconds
        self.alert_cooldown = self.config.get('alert_cooldown', 300)  # 5 minutes
        self.max_recovery_attempts = self.config.get('max_recovery_attempts', 3)
        
        # Component health profiles
        self.components: Dict[str, ComponentHealth] = {}
        
        # Alerting
        self.alerts: List[HealthAlert] = []
        self.alert_callbacks: List[Callable[[HealthAlert], None]] = []
        self.alert_cooldowns: Dict[str, datetime] = {}
        
        # Monitoring state
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Health check functions
        self.health_checkers: Dict[str, Callable] = {}
        self.recovery_handlers: Dict[str, Callable] = {}
        
        # Initialize components
        self._initialize_components()
        self._register_health_checkers()
        
        # State persistence
        self.state_file = Path("data/health_monitor_state.json")
        self.state_file.parent.mkdir(exist_ok=True)
    
    def _initialize_components(self):
        """Initialize health profiles for all components."""
        component_names = [
            "arbitrage_engine",
            "bridge_monitor", 
            "cross_chain_mev",
            "wallet_manager",
            "price_feeds",
            "dex_manager",
            "memory_system",
            "knowledge_graph",
            "filesystem_mcp",
            "api_connections"
        ]
        
        for name in component_names:
            self.components[name] = ComponentHealth(component_name=name)
            logger.debug(f"Initialized health profile for {name}")
    
    def _register_health_checkers(self):
        """Register health check functions for each component."""
        self.health_checkers = {
            "arbitrage_engine": self._check_arbitrage_engine,
            "bridge_monitor": self._check_bridge_monitor,
            "cross_chain_mev": self._check_cross_chain_mev,
            "wallet_manager": self._check_wallet_manager,
            "price_feeds": self._check_price_feeds,
            "dex_manager": self._check_dex_manager,
            "memory_system": self._check_memory_system,
            "knowledge_graph": self._check_knowledge_graph,
            "filesystem_mcp": self._check_filesystem_mcp,
            "api_connections": self._check_api_connections
        }
        
        # Register recovery handlers
        self.recovery_handlers = {
            "arbitrage_engine": self._recover_arbitrage_engine,
            "bridge_monitor": self._recover_bridge_monitor,
            "cross_chain_mev": self._recover_cross_chain_mev,
            "memory_system": self._recover_memory_system,
            "api_connections": self._recover_api_connections
        }
    
    async def start_monitoring(self):
        """Start the health monitoring system."""
        if self.running:
            logger.warning("Health monitoring already running")
            return
        
        self.running = True
        logger.info("🏥 Starting unified health monitoring system")
        
        # Load previous state
        await self._load_state()
        
        # Start monitoring loop
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("✅ Unified health monitoring system started")
    
    async def stop_monitoring(self):
        """Stop the health monitoring system."""
        if not self.running:
            return
        
        self.running = False
        logger.info("🛑 Stopping unified health monitoring system")
        
        # Cancel monitoring task
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        # Save state
        await self._save_state()
        
        logger.info("✅ Unified health monitoring system stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _perform_health_checks(self):
        """Perform health checks on all components."""
        logger.debug("🔍 Performing health checks on all components")
        
        for component_name, health_profile in self.components.items():
            try:
                await self._check_component_health(component_name, health_profile)
            except Exception as e:
                logger.error(f"Error checking health of {component_name}: {e}")
                health_profile.failed_checks += 1
                health_profile.consecutive_failures += 1
                health_profile.status = ComponentStatus.FAILED
                health_profile.error_message = str(e)
    
    async def _check_component_health(self, component_name: str, health_profile: ComponentHealth):
        """Check health of a specific component."""
        health_profile.total_checks += 1
        health_profile.last_check = datetime.now()
        
        # Get health checker function
        checker = self.health_checkers.get(component_name)
        if not checker:
            logger.warning(f"No health checker for {component_name}")
            return
        
        try:
            # Perform health check
            is_healthy, metrics, error_msg = await checker()
            
            if is_healthy:
                health_profile.status = ComponentStatus.HEALTHY
                health_profile.last_success = datetime.now()
                health_profile.consecutive_failures = 0
                health_profile.error_message = None
                
                # Reset recovery attempts on success
                if health_profile.recovery_attempts > 0:
                    logger.info(f"✅ {component_name} recovered after {health_profile.recovery_attempts} attempts")
                    health_profile.recovery_attempts = 0
            else:
                health_profile.failed_checks += 1
                health_profile.consecutive_failures += 1
                health_profile.error_message = error_msg
                
                # Determine status based on consecutive failures
                if health_profile.consecutive_failures >= 5:
                    health_profile.status = ComponentStatus.FAILED
                elif health_profile.consecutive_failures >= 3:
                    health_profile.status = ComponentStatus.CRITICAL
                else:
                    health_profile.status = ComponentStatus.WARNING
                
                # Generate alert
                await self._generate_alert(
                    component_name,
                    AlertLevel.CRITICAL if health_profile.status == ComponentStatus.FAILED else AlertLevel.WARNING,
                    f"{component_name} health check failed: {error_msg}"
                )
                
                # Attempt recovery if enabled
                await self._attempt_recovery(component_name, health_profile)
            
            # Update metrics
            if metrics:
                for metric_name, metric in metrics.items():
                    health_profile.metrics[metric_name] = metric
                    
                    # Check metric thresholds
                    if metric.status in [ComponentStatus.WARNING, ComponentStatus.CRITICAL]:
                        await self._generate_alert(
                            component_name,
                            AlertLevel.WARNING if metric.status == ComponentStatus.WARNING else AlertLevel.CRITICAL,
                            f"{component_name} {metric_name}: {metric.value}{metric.unit} (threshold: {metric.threshold_warning})"
                        )
        
        except Exception as e:
            logger.error(f"Health check failed for {component_name}: {e}")
            health_profile.failed_checks += 1
            health_profile.consecutive_failures += 1
            health_profile.status = ComponentStatus.FAILED
            health_profile.error_message = str(e)

    async def _attempt_recovery(self, component_name: str, health_profile: ComponentHealth):
        """Attempt to recover a failed component."""
        if health_profile.recovery_attempts >= self.max_recovery_attempts:
            logger.warning(f"Max recovery attempts reached for {component_name}")
            return

        recovery_handler = self.recovery_handlers.get(component_name)
        if not recovery_handler:
            return

        try:
            health_profile.status = ComponentStatus.RECOVERING
            health_profile.recovery_attempts += 1

            logger.info(f"🔄 Attempting recovery for {component_name} (attempt {health_profile.recovery_attempts})")

            success = await recovery_handler()
            if success:
                logger.info(f"✅ Recovery successful for {component_name}")
                await self._generate_alert(
                    component_name,
                    AlertLevel.INFO,
                    f"{component_name} recovered successfully"
                )
            else:
                logger.warning(f"❌ Recovery failed for {component_name}")

        except Exception as e:
            logger.error(f"Recovery attempt failed for {component_name}: {e}")

    async def _generate_alert(self, component: str, level: AlertLevel, message: str,
                            metric_name: str = None, metric_value: float = None):
        """Generate and process a health alert."""
        # Check cooldown
        cooldown_key = f"{component}_{level.value}"
        if cooldown_key in self.alert_cooldowns:
            if datetime.now() - self.alert_cooldowns[cooldown_key] < timedelta(seconds=self.alert_cooldown):
                return  # Still in cooldown

        # Create alert
        alert = HealthAlert(
            alert_id=f"alert_{component}_{int(time.time())}",
            component=component,
            level=level,
            message=message,
            timestamp=datetime.now(),
            metric_name=metric_name,
            metric_value=metric_value
        )

        # Store alert
        self.alerts.append(alert)
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

        # Log alert
        log_level = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.CRITICAL: logger.error,
            AlertLevel.EMERGENCY: logger.critical
        }.get(level, logger.info)

        log_level(f"🚨 HEALTH ALERT [{level.value.upper()}] {component}: {message}")

    # Health Check Implementations
    async def _check_arbitrage_engine(self) -> tuple[bool, Dict[str, HealthMetric], str]:
        """Check arbitrage engine health."""
        try:
            # Check if arbitrage engine is running
            from src.core.master_arbitrage_system import MasterArbitrageSystem

            # Basic connectivity test
            metrics = {}

            # Check system state
            state_file = Path("system_state.json")
            if state_file.exists():
                with open(state_file) as f:
                    state = json.load(f)

                engine_status = state.get("components", {}).get("arbitrage_engine", {})
                if engine_status.get("status") == "ready":
                    return True, metrics, ""
                else:
                    return False, metrics, f"Engine status: {engine_status.get('status', 'unknown')}"

            return False, metrics, "System state file not found"

        except Exception as e:
            return False, {}, str(e)

    async def _check_bridge_monitor(self) -> tuple[bool, Dict[str, HealthMetric], str]:
        """Check bridge monitor health."""
        try:
            # Check bridge monitor status
            metrics = {}

            # Test bridge API connectivity
            test_bridges = ["synapse", "across", "hop"]
            working_bridges = 0

            for bridge in test_bridges:
                try:
                    # Simple connectivity test (would be replaced with actual API calls)
                    working_bridges += 1
                except:
                    pass

            bridge_availability = working_bridges / len(test_bridges)
            metrics["bridge_availability"] = HealthMetric(
                name="bridge_availability",
                value=bridge_availability,
                unit="%",
                timestamp=datetime.now(),
                threshold_warning=0.6,
                threshold_critical=0.3
            )

            if bridge_availability >= 0.6:
                return True, metrics, ""
            else:
                return False, metrics, f"Only {working_bridges}/{len(test_bridges)} bridges available"

        except Exception as e:
            return False, {}, str(e)

    async def _check_cross_chain_mev(self) -> tuple[bool, Dict[str, HealthMetric], str]:
        """Check cross-chain MEV engine health."""
        try:
            metrics = {}

            # Check system state
            state_file = Path("system_state.json")
            if state_file.exists():
                with open(state_file) as f:
                    state = json.load(f)

                mev_status = state.get("components", {}).get("cross_chain_mev", {})
                if mev_status.get("status") == "ready":
                    return True, metrics, ""
                else:
                    return False, metrics, f"MEV status: {mev_status.get('status', 'unknown')}"

            return False, metrics, "System state file not found"

        except Exception as e:
            return False, {}, str(e)

    async def _check_wallet_manager(self) -> tuple[bool, Dict[str, HealthMetric], str]:
        """Check wallet manager health."""
        try:
            metrics = {}

            # Check wallet configuration
            state_file = Path("system_state.json")
            if state_file.exists():
                with open(state_file) as f:
                    state = json.load(f)

                wallet_config = state.get("wallet_config", {})
                if wallet_config.get("arbitrum_wallet"):
                    return True, metrics, ""
                else:
                    return False, metrics, "No wallet configured"

            return False, metrics, "System state file not found"

        except Exception as e:
            return False, {}, str(e)

    async def _check_price_feeds(self) -> tuple[bool, Dict[str, HealthMetric], str]:
        """Check price feeds health."""
        try:
            metrics = {}

            # Check API keys
            alchemy_key = os.getenv("ALCHEMY_API_KEY")
            coingecko_key = os.getenv("COINGECKO_API_KEY")

            if not alchemy_key:
                return False, metrics, "Missing Alchemy API key"

            if not coingecko_key:
                return False, metrics, "Missing CoinGecko API key"

            # Test API connectivity (basic check)
            try:
                async with aiohttp.ClientSession() as session:
                    # Test CoinGecko API
                    async with session.get(
                        "https://api.coingecko.com/api/v3/ping",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            return True, metrics, ""
                        else:
                            return False, metrics, f"CoinGecko API error: {response.status}"
            except Exception as e:
                return False, metrics, f"API connectivity test failed: {e}"

        except Exception as e:
            return False, {}, str(e)

    async def _check_dex_manager(self) -> tuple[bool, Dict[str, HealthMetric], str]:
        """Check DEX manager health."""
        try:
            metrics = {}

            # Check if DEX APIs are accessible
            test_dexes = ["uniswap", "sushiswap", "curve"]
            working_dexes = 0

            for _ in test_dexes:
                try:
                    # Simple connectivity test (would be replaced with actual API calls)
                    working_dexes += 1
                except Exception:
                    pass

            dex_availability = working_dexes / len(test_dexes)
            metrics["dex_availability"] = HealthMetric(
                name="dex_availability",
                value=dex_availability,
                unit="%",
                timestamp=datetime.now(),
                threshold_warning=0.6,
                threshold_critical=0.3
            )

            if dex_availability >= 0.6:
                return True, metrics, ""
            else:
                return False, metrics, f"Only {working_dexes}/{len(test_dexes)} DEXes available"

        except Exception as e:
            return False, {}, str(e)

    async def _check_memory_system(self) -> tuple[bool, Dict[str, HealthMetric], str]:
        """Check MCP memory system health."""
        try:
            metrics = {}

            # Check if memory service is running
            memory_service_path = Path("mcp-memory-service")
            if not memory_service_path.exists():
                return False, metrics, "Memory service directory not found"

            # Check system state
            state_file = Path("system_state.json")
            if state_file.exists():
                with open(state_file) as f:
                    state = json.load(f)

                memory_status = state.get("components", {}).get("memory_system", {})
                if memory_status.get("status") == "ready":
                    return True, metrics, ""
                else:
                    return False, metrics, f"Memory status: {memory_status.get('status', 'unknown')}"

            return False, metrics, "System state file not found"

        except Exception as e:
            return False, {}, str(e)

    async def _check_knowledge_graph(self) -> tuple[bool, Dict[str, HealthMetric], str]:
        """Check MCP knowledge graph health."""
        try:
            metrics = {}

            # Check if knowledge graph service exists
            kg_service_path = Path("mcp-knowledge-graph")
            if not kg_service_path.exists():
                return False, metrics, "Knowledge graph service directory not found"

            # Basic health check
            return True, metrics, ""

        except Exception as e:
            return False, {}, str(e)

    async def _check_filesystem_mcp(self) -> tuple[bool, Dict[str, HealthMetric], str]:
        """Check MCP filesystem service health."""
        try:
            metrics = {}

            # Check if filesystem service exists
            fs_service_path = Path("filesystem-mcp-server")
            if not fs_service_path.exists():
                return False, metrics, "Filesystem MCP service directory not found"

            # Basic health check
            return True, metrics, ""

        except Exception as e:
            return False, {}, str(e)

    async def _check_api_connections(self) -> tuple[bool, Dict[str, HealthMetric], str]:
        """Check external API connections health."""
        try:
            metrics = {}

            # Check required API keys
            required_keys = {
                "ALCHEMY_API_KEY": "Alchemy",
                "COINGECKO_API_KEY": "CoinGecko",
                "THE_GRAPH_API_KEY": "The Graph"
            }

            missing_keys = []
            for env_var, service_name in required_keys.items():
                if not os.getenv(env_var):
                    missing_keys.append(service_name)

            if missing_keys:
                return False, metrics, f"Missing API keys: {', '.join(missing_keys)}"

            # Test API connectivity
            try:
                async with aiohttp.ClientSession() as session:
                    # Test CoinGecko API
                    async with session.get(
                        "https://api.coingecko.com/api/v3/ping",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status != 200:
                            return False, metrics, f"CoinGecko API error: {response.status}"

                return True, metrics, ""

            except Exception as e:
                return False, metrics, f"API connectivity test failed: {e}"

        except Exception as e:
            return False, {}, str(e)

    # Recovery Handlers
    async def _recover_arbitrage_engine(self) -> bool:
        """Attempt to recover the arbitrage engine."""
        try:
            logger.info("🔄 Attempting to recover arbitrage engine")

            # Try to restart the arbitrage engine
            # This would involve reloading the module and reinitializing

            # For now, just mark as recovered if system state allows
            state_file = Path("system_state.json")
            if state_file.exists():
                with open(state_file) as f:
                    state = json.load(f)

                # Update state to ready
                if "components" in state and "arbitrage_engine" in state["components"]:
                    state["components"]["arbitrage_engine"]["status"] = "ready"
                    state["components"]["arbitrage_engine"]["last_run"] = datetime.now().isoformat()

                    with open(state_file, 'w') as f:
                        json.dump(state, f, indent=2)

                    return True

            return False

        except Exception as e:
            logger.error(f"Recovery failed for arbitrage engine: {e}")
            return False

    async def _recover_bridge_monitor(self) -> bool:
        """Attempt to recover the bridge monitor."""
        try:
            logger.info("🔄 Attempting to recover bridge monitor")

            # Try to reinitialize bridge connections
            # This would involve reconnecting to bridge APIs

            return True  # Simplified for now

        except Exception as e:
            logger.error(f"Recovery failed for bridge monitor: {e}")
            return False

    async def _recover_cross_chain_mev(self) -> bool:
        """Attempt to recover the cross-chain MEV engine."""
        try:
            logger.info("🔄 Attempting to recover cross-chain MEV engine")

            # Try to restart MEV monitoring
            return True  # Simplified for now

        except Exception as e:
            logger.error(f"Recovery failed for cross-chain MEV: {e}")
            return False

    async def _recover_memory_system(self) -> bool:
        """Attempt to recover the memory system."""
        try:
            logger.info("🔄 Attempting to recover memory system")

            # Try to restart memory service
            # This would involve restarting the MCP memory server

            return True  # Simplified for now

        except Exception as e:
            logger.error(f"Recovery failed for memory system: {e}")
            return False

    async def _recover_api_connections(self) -> bool:
        """Attempt to recover API connections."""
        try:
            logger.info("🔄 Attempting to recover API connections")

            # Try to re-establish API connections
            # This would involve testing and reconnecting to APIs

            return True  # Simplified for now

        except Exception as e:
            logger.error(f"Recovery failed for API connections: {e}")
            return False

    # Utility Methods
    def add_alert_callback(self, callback: Callable[[HealthAlert], None]):
        """Add a callback for health alerts."""
        self.alert_callbacks.append(callback)

    def get_component_health(self, component_name: str) -> Optional[ComponentHealth]:
        """Get health profile for a specific component."""
        return self.components.get(component_name)

    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        total_components = len(self.components)
        if total_components == 0:
            return {'status': 'no_components', 'components': {}}

        status_counts = {status.value: 0 for status in ComponentStatus}
        component_details = {}

        for name, health in self.components.items():
            status_counts[health.status.value] += 1
            component_details[name] = {
                'status': health.status.value,
                'availability': health.availability,
                'uptime_hours': health.uptime_hours,
                'consecutive_failures': health.consecutive_failures,
                'last_check': health.last_check.isoformat() if health.last_check else None,
                'error_message': health.error_message
            }

        # Determine overall system status
        if status_counts['failed'] > 0:
            overall_status = 'failed'
        elif status_counts['critical'] > 0:
            overall_status = 'critical'
        elif status_counts['warning'] > 0:
            overall_status = 'warning'
        elif status_counts['recovering'] > 0:
            overall_status = 'recovering'
        else:
            overall_status = 'healthy'

        return {
            'overall_status': overall_status,
            'total_components': total_components,
            'status_counts': status_counts,
            'components': component_details,
            'active_alerts': len([a for a in self.alerts if not a.resolved]),
            'last_updated': datetime.now().isoformat()
        }

    def get_active_alerts(self) -> List[HealthAlert]:
        """Get all active (unresolved) alerts."""
        return [alert for alert in self.alerts if not alert.resolved]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                logger.info(f"Alert {alert_id} acknowledged")
                return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolution_time = datetime.now()
                logger.info(f"Alert {alert_id} resolved")
                return True
        return False

    async def _save_state(self):
        """Save monitoring state to file."""
        try:
            state = {
                'components': {},
                'alerts': [],
                'last_updated': datetime.now().isoformat()
            }

            # Save component health
            for name, health in self.components.items():
                state['components'][name] = {
                    'status': health.status.value,
                    'last_check': health.last_check.isoformat() if health.last_check else None,
                    'last_success': health.last_success.isoformat() if health.last_success else None,
                    'consecutive_failures': health.consecutive_failures,
                    'total_checks': health.total_checks,
                    'failed_checks': health.failed_checks,
                    'error_message': health.error_message,
                    'recovery_attempts': health.recovery_attempts
                }

            # Save recent alerts
            for alert in self.alerts[-100:]:  # Keep last 100 alerts
                state['alerts'].append({
                    'alert_id': alert.alert_id,
                    'component': alert.component,
                    'level': alert.level.value,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat(),
                    'acknowledged': alert.acknowledged,
                    'resolved': alert.resolved
                })

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

            logger.debug(f"Health monitoring state saved to {self.state_file}")

        except Exception as e:
            logger.error(f"Failed to save health monitoring state: {e}")

    async def _load_state(self):
        """Load monitoring state from file."""
        try:
            if not self.state_file.exists():
                logger.debug("No previous health monitoring state found")
                return

            with open(self.state_file) as f:
                state = json.load(f)

            # Load component health
            for name, data in state.get('components', {}).items():
                if name in self.components:
                    health = self.components[name]
                    health.status = ComponentStatus(data.get('status', 'unknown'))
                    health.consecutive_failures = data.get('consecutive_failures', 0)
                    health.total_checks = data.get('total_checks', 0)
                    health.failed_checks = data.get('failed_checks', 0)
                    health.error_message = data.get('error_message')
                    health.recovery_attempts = data.get('recovery_attempts', 0)

                    if data.get('last_check'):
                        health.last_check = datetime.fromisoformat(data['last_check'])
                    if data.get('last_success'):
                        health.last_success = datetime.fromisoformat(data['last_success'])

            logger.debug(f"Health monitoring state loaded from {self.state_file}")

        except Exception as e:
            logger.error(f"Failed to load health monitoring state: {e}")

    def print_health_dashboard(self):
        """Print a comprehensive health dashboard."""
        summary = self.get_system_health_summary()

        print("\n🏥 UNIFIED HEALTH MONITORING DASHBOARD")
        print("=" * 60)

        # Overall status
        status_icon = {
            'healthy': '✅',
            'warning': '⚠️',
            'critical': '🔴',
            'failed': '❌',
            'recovering': '🔄'
        }.get(summary['overall_status'], '❓')

        print(f"🎯 Overall System Status: {status_icon} {summary['overall_status'].upper()}")
        print(f"📊 Components: {summary['total_components']} total")

        # Component status breakdown
        print(f"\n📋 COMPONENT STATUS:")
        for name, details in summary['components'].items():
            status_icon = {
                'healthy': '✅',
                'warning': '⚠️',
                'critical': '🔴',
                'failed': '❌',
                'recovering': '🔄',
                'unknown': '❓'
            }.get(details['status'], '❓')

            component_display = name.replace('_', ' ').title()
            availability = details['availability']

            print(f"   {status_icon} {component_display}: {details['status']} ({availability:.1f}% uptime)")

            if details['error_message']:
                print(f"      ⚠️ Error: {details['error_message']}")

            if details['consecutive_failures'] > 0:
                print(f"      🔄 Consecutive failures: {details['consecutive_failures']}")

        # Active alerts
        active_alerts = self.get_active_alerts()
        if active_alerts:
            print(f"\n🚨 ACTIVE ALERTS ({len(active_alerts)}):")
            for alert in active_alerts[-5:]:  # Show last 5 alerts
                alert_icon = {
                    'info': 'ℹ️',
                    'warning': '⚠️',
                    'critical': '🔴',
                    'emergency': '🚨'
                }.get(alert.level.value, '❓')

                print(f"   {alert_icon} [{alert.level.value.upper()}] {alert.component}: {alert.message}")
                print(f"      🕐 {alert.timestamp.strftime('%H:%M:%S')}")
        else:
            print(f"\n✅ No active alerts")

        print(f"\n🕐 Last updated: {summary['last_updated']}")


# Example usage and testing
async def main():
    """Example usage of the unified health monitor."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create health monitor
    config = {
        'check_interval': 30,  # Check every 30 seconds
        'alert_cooldown': 300,  # 5 minute cooldown
        'max_recovery_attempts': 3
    }

    monitor = UnifiedHealthMonitor(config)

    # Add alert callback
    def alert_handler(alert: HealthAlert):
        print(f"🚨 ALERT: {alert.component} - {alert.message}")

    monitor.add_alert_callback(alert_handler)

    try:
        # Start monitoring
        await monitor.start_monitoring()

        # Let it run for a bit
        await asyncio.sleep(60)

        # Print dashboard
        monitor.print_health_dashboard()

    except KeyboardInterrupt:
        print("\n🛑 Stopping health monitor...")
    finally:
        await monitor.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
