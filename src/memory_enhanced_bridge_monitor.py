#!/usr/bin/env python3
"""
Memory-Enhanced Bridge Cost Monitor
Real-time bridge cost monitoring with memory-driven optimization and learning
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import aiohttp

# Add memory service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-memory-service', 'src'))

try:
    from mcp_memory_service.server import MemoryServer
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BridgeCostData:
    """Bridge cost data point"""
    bridge_name: str
    source_chain: str
    target_chain: str
    cost_usd: float
    speed_minutes: int
    reliability_score: float
    timestamp: datetime
    gas_price_gwei: Optional[float] = None
    network_congestion: Optional[str] = None

@dataclass
class CostOptimization:
    """Bridge cost optimization recommendation"""
    recommended_bridge: str
    estimated_cost: float
    estimated_time: int
    confidence_score: float
    reasoning: List[str]
    alternative_bridges: List[Dict[str, Any]]

class MemoryEnhancedBridgeMonitor:
    """
    Memory-Enhanced Bridge Cost Monitor
    
    Features:
    - Real-time bridge cost tracking
    - Memory-driven cost optimization
    - Historical pattern recognition
    - Dynamic bridge selection
    - Cost prediction and alerts
    """
    
    def __init__(self):
        self.memory_server = None
        self.memory_enabled = MEMORY_AVAILABLE
        
        # Bridge configurations
        self.bridges = {
            "synapse": {
                "api_endpoint": "https://api.synapseprotocol.com/v1/bridge/quote",
                "supported_chains": [("ethereum", "arbitrum"), ("ethereum", "base"), ("ethereum", "optimism")],
                "base_reliability": 0.95
            },
            "hop": {
                "api_endpoint": "https://api.hop.exchange/v1/quote",
                "supported_chains": [("ethereum", "arbitrum"), ("ethereum", "optimism"), ("ethereum", "polygon")],
                "base_reliability": 0.90
            },
            "across": {
                "api_endpoint": "https://api.across.to/api/suggested-fees",
                "supported_chains": [("ethereum", "arbitrum"), ("ethereum", "base"), ("ethereum", "optimism")],
                "base_reliability": 0.92
            },
            "stargate": {
                "api_endpoint": "https://api.stargate.finance/v1/quote",
                "supported_chains": [("ethereum", "arbitrum"), ("ethereum", "base"), ("ethereum", "avalanche")],
                "base_reliability": 0.88
            }
        }
        
        # Chain configurations
        self.chains = {
            "ethereum": {"chain_id": 1, "gas_token": "ETH"},
            "arbitrum": {"chain_id": 42161, "gas_token": "ETH"},
            "base": {"chain_id": 8453, "gas_token": "ETH"},
            "optimism": {"chain_id": 10, "gas_token": "ETH"},
            "polygon": {"chain_id": 137, "gas_token": "MATIC"},
            "avalanche": {"chain_id": 43114, "gas_token": "AVAX"}
        }
        
        # Cost tracking
        self.cost_history: Dict[str, List[BridgeCostData]] = {}
        self.optimization_cache: Dict[str, CostOptimization] = {}
        
        # Performance metrics
        self.monitoring_stats = {
            "total_quotes_fetched": 0,
            "optimizations_provided": 0,
            "cost_savings_identified": 0,
            "alerts_sent": 0
        }
    
    async def initialize(self):
        """Initialize the bridge monitor"""
        logger.info("🌉 Initializing Memory-Enhanced Bridge Monitor")
        
        # Initialize memory system
        if self.memory_enabled:
            try:
                self.memory_server = MemoryServer()
                await self.memory_server.initialize()
                logger.info("✅ Memory system initialized")
                
                # Store initialization
                await self._store_memory(
                    "Bridge Cost Monitor initialized with memory enhancement",
                    ["bridge-monitor", "initialization", "memory-enhanced"],
                    "system_event"
                )
                
                # Load historical optimizations
                await self._load_historical_optimizations()
                
            except Exception as e:
                logger.warning(f"Memory system unavailable: {e}")
                self.memory_enabled = False
        
        logger.info(f"✅ Bridge Monitor initialized")
        logger.info(f"🌉 Monitoring {len(self.bridges)} bridge providers")
        logger.info(f"⛓️ Tracking {len(self.chains)} chains")
    
    async def _store_memory(self, content: str, tags: List[str], memory_type: str, metadata: Dict[str, Any] = None):
        """Store memory in the system"""
        if not self.memory_enabled or not self.memory_server:
            return
        
        try:
            memory_data = {
                "content": content,
                "metadata": {
                    "tags": ",".join(tags),
                    "type": memory_type,
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {})
                }
            }
            await self.memory_server.handle_store_memory(memory_data)
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
    
    async def _recall_memories(self, query: str, n_results: int = 5) -> List[str]:
        """Recall memories from the system"""
        if not self.memory_enabled or not self.memory_server:
            return []
        
        try:
            response = await self.memory_server.handle_retrieve_memory({
                "query": query,
                "n_results": n_results
            })
            
            memories = []
            if response and response[0].text:
                text = response[0].text
                if "Found the following memories:" in text:
                    lines = text.split('\n')
                    for line in lines:
                        if line.strip().startswith('Content:'):
                            content = line.replace('Content:', '').strip()
                            memories.append(content)
            return memories
        except Exception as e:
            logger.error(f"Failed to recall memories: {e}")
            return []
    
    async def _load_historical_optimizations(self):
        """Load historical bridge optimizations from memory"""
        optimization_memories = await self._recall_memories("bridge cost optimization", 20)
        
        if optimization_memories:
            logger.info(f"📚 Loaded {len(optimization_memories)} bridge optimization insights")
            
            # Parse and apply optimizations
            for memory in optimization_memories:
                if "synapse" in memory.lower() and "0.90" in memory:
                    logger.info("🎯 Applied Synapse cost optimization: $0.90")
                    self.bridges["synapse"]["base_reliability"] = 0.98
                
                if "optimal" in memory.lower() or "best" in memory.lower():
                    # Extract bridge name and apply bonus
                    for bridge_name in self.bridges.keys():
                        if bridge_name in memory.lower():
                            self.bridges[bridge_name]["base_reliability"] += 0.02
                            break
    
    async def fetch_bridge_costs(self, source_chain: str, target_chain: str, amount_usd: float = 100) -> List[BridgeCostData]:
        """Fetch current bridge costs for a chain pair"""
        costs = []
        
        for bridge_name, config in self.bridges.items():
            if (source_chain, target_chain) in config["supported_chains"]:
                try:
                    # Simulate API call (in production, use real APIs)
                    import random
                    
                    base_cost = random.uniform(0.5, 3.0)
                    speed = random.randint(5, 30)
                    reliability = config["base_reliability"] * random.uniform(0.95, 1.05)
                    
                    # Apply memory-based adjustments
                    bridge_memories = await self._recall_memories(f"bridge {bridge_name} {source_chain} {target_chain}", 3)
                    
                    for memory in bridge_memories:
                        if "low cost" in memory.lower() or "optimal" in memory.lower():
                            base_cost *= 0.9  # 10% discount for proven performance
                        elif "expensive" in memory.lower() or "high cost" in memory.lower():
                            base_cost *= 1.1  # 10% penalty for poor performance
                    
                    cost_data = BridgeCostData(
                        bridge_name=bridge_name,
                        source_chain=source_chain,
                        target_chain=target_chain,
                        cost_usd=base_cost,
                        speed_minutes=speed,
                        reliability_score=min(1.0, reliability),
                        timestamp=datetime.now(),
                        gas_price_gwei=random.uniform(10, 50),
                        network_congestion="low" if random.random() > 0.7 else "medium"
                    )
                    
                    costs.append(cost_data)
                    self.monitoring_stats["total_quotes_fetched"] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to fetch {bridge_name} costs: {e}")
        
        # Store costs in history
        route_key = f"{source_chain}_{target_chain}"
        if route_key not in self.cost_history:
            self.cost_history[route_key] = []
        
        self.cost_history[route_key].extend(costs)
        
        # Keep only recent history (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.cost_history[route_key] = [
            cost for cost in self.cost_history[route_key]
            if cost.timestamp > cutoff_time
        ]
        
        return costs
    
    async def get_optimal_bridge(self, source_chain: str, target_chain: str, amount_usd: float = 100, priority: str = "cost") -> CostOptimization:
        """Get optimal bridge recommendation with memory insights"""
        # Check cache first
        cache_key = f"{source_chain}_{target_chain}_{amount_usd}_{priority}"
        if cache_key in self.optimization_cache:
            cached = self.optimization_cache[cache_key]
            if (datetime.now() - datetime.fromisoformat(cached.reasoning[0].split("at ")[-1])).seconds < 300:  # 5 min cache
                return cached
        
        # Fetch current costs
        current_costs = await self.fetch_bridge_costs(source_chain, target_chain, amount_usd)
        
        if not current_costs:
            return CostOptimization(
                recommended_bridge="none",
                estimated_cost=999.0,
                estimated_time=999,
                confidence_score=0.0,
                reasoning=["No bridges available for this route"],
                alternative_bridges=[]
            )
        
        # Get historical insights from memory
        route_memories = await self._recall_memories(f"bridge {source_chain} {target_chain}", 10)
        
        # Score bridges based on priority
        scored_bridges = []
        
        for cost_data in current_costs:
            score = 0
            reasoning = []
            
            if priority == "cost":
                # Lower cost = higher score
                max_cost = max(c.cost_usd for c in current_costs)
                score += (max_cost - cost_data.cost_usd) / max_cost * 40
                reasoning.append(f"Cost efficiency: ${cost_data.cost_usd:.2f}")
            
            elif priority == "speed":
                # Lower time = higher score
                max_time = max(c.speed_minutes for c in current_costs)
                score += (max_time - cost_data.speed_minutes) / max_time * 40
                reasoning.append(f"Speed: {cost_data.speed_minutes} minutes")
            
            # Reliability score
            score += cost_data.reliability_score * 30
            reasoning.append(f"Reliability: {cost_data.reliability_score:.2f}")
            
            # Memory-based adjustments
            memory_bonus = 0
            for memory in route_memories:
                if cost_data.bridge_name in memory.lower():
                    if "success" in memory.lower() or "optimal" in memory.lower():
                        memory_bonus += 10
                        reasoning.append("Historical success bonus")
                    elif "failed" in memory.lower() or "expensive" in memory.lower():
                        memory_bonus -= 5
                        reasoning.append("Historical issues penalty")
            
            score += memory_bonus
            
            # Network conditions
            if cost_data.network_congestion == "low":
                score += 5
                reasoning.append("Low network congestion")
            
            scored_bridges.append({
                "bridge_data": cost_data,
                "score": score,
                "reasoning": reasoning
            })
        
        # Sort by score
        scored_bridges.sort(key=lambda x: x["score"], reverse=True)
        
        best_bridge = scored_bridges[0]
        alternatives = scored_bridges[1:3]  # Top 3 alternatives
        
        optimization = CostOptimization(
            recommended_bridge=best_bridge["bridge_data"].bridge_name,
            estimated_cost=best_bridge["bridge_data"].cost_usd,
            estimated_time=best_bridge["bridge_data"].speed_minutes,
            confidence_score=min(1.0, best_bridge["score"] / 100),
            reasoning=[f"Optimized for {priority} at {datetime.now().isoformat()}"] + best_bridge["reasoning"],
            alternative_bridges=[
                {
                    "name": alt["bridge_data"].bridge_name,
                    "cost": alt["bridge_data"].cost_usd,
                    "time": alt["bridge_data"].speed_minutes,
                    "score": alt["score"]
                }
                for alt in alternatives
            ]
        )
        
        # Cache the optimization
        self.optimization_cache[cache_key] = optimization
        self.monitoring_stats["optimizations_provided"] += 1
        
        # Store optimization in memory
        await self._store_memory(
            f"BRIDGE OPTIMIZATION: {source_chain}→{target_chain} recommended {optimization.recommended_bridge} at ${optimization.estimated_cost:.2f} (confidence: {optimization.confidence_score:.2f})",
            ["bridge-optimization", "recommendation", optimization.recommended_bridge, source_chain, target_chain],
            "optimization_result",
            {
                "recommended_bridge": optimization.recommended_bridge,
                "cost": optimization.estimated_cost,
                "confidence": optimization.confidence_score,
                "priority": priority
            }
        )
        
        return optimization

    async def monitor_bridge_costs_continuously(self):
        """Continuously monitor bridge costs and identify opportunities"""
        logger.info("🔍 Starting continuous bridge cost monitoring...")

        # Key routes to monitor
        key_routes = [
            ("ethereum", "arbitrum"),
            ("ethereum", "base"),
            ("ethereum", "optimism"),
            ("arbitrum", "ethereum"),
            ("base", "ethereum")
        ]

        while True:
            try:
                for source_chain, target_chain in key_routes:
                    # Get current costs
                    costs = await self.fetch_bridge_costs(source_chain, target_chain)

                    if costs:
                        # Find best cost
                        best_cost = min(costs, key=lambda x: x.cost_usd)
                        avg_cost = sum(c.cost_usd for c in costs) / len(costs)

                        logger.info(f"💰 {source_chain}→{target_chain}: Best ${best_cost.cost_usd:.2f} ({best_cost.bridge_name}), Avg ${avg_cost:.2f}")

                        # Check for exceptional opportunities
                        if best_cost.cost_usd < 1.0:
                            logger.info(f"🎯 EXCELLENT OPPORTUNITY: {best_cost.bridge_name} at ${best_cost.cost_usd:.2f}")

                            await self._store_memory(
                                f"EXCELLENT BRIDGE OPPORTUNITY: {best_cost.bridge_name} {source_chain}→{target_chain} at ${best_cost.cost_usd:.2f}",
                                ["bridge-opportunity", "excellent-cost", best_cost.bridge_name, source_chain, target_chain],
                                "opportunity_alert",
                                {"cost": best_cost.cost_usd, "bridge": best_cost.bridge_name}
                            )

                            self.monitoring_stats["alerts_sent"] += 1

                        # Check for cost savings vs historical average
                        route_key = f"{source_chain}_{target_chain}"
                        if route_key in self.cost_history and len(self.cost_history[route_key]) > 10:
                            historical_avg = sum(c.cost_usd for c in self.cost_history[route_key][-10:]) / 10
                            savings = historical_avg - best_cost.cost_usd

                            if savings > 0.5:  # $0.50+ savings
                                logger.info(f"💡 COST SAVINGS: ${savings:.2f} below recent average")
                                self.monitoring_stats["cost_savings_identified"] += savings

                    # Small delay between routes
                    await asyncio.sleep(5)

                # Store monitoring summary
                await self._store_memory(
                    f"Bridge monitoring cycle complete: {self.monitoring_stats['total_quotes_fetched']} quotes, ${self.monitoring_stats['cost_savings_identified']:.2f} savings identified",
                    ["monitoring", "bridge-costs", "cycle-complete"],
                    "monitoring_data",
                    self.monitoring_stats
                )

                # Wait before next monitoring cycle
                await asyncio.sleep(120)  # Monitor every 2 minutes

            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def get_cost_trends(self, source_chain: str, target_chain: str, hours: int = 24) -> Dict[str, Any]:
        """Get cost trends for a specific route"""
        route_key = f"{source_chain}_{target_chain}"

        if route_key not in self.cost_history:
            return {"error": "No historical data available"}

        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_costs = [
            cost for cost in self.cost_history[route_key]
            if cost.timestamp > cutoff_time
        ]

        if not recent_costs:
            return {"error": "No recent data available"}

        # Calculate trends by bridge
        bridge_trends = {}
        for bridge_name in self.bridges.keys():
            bridge_costs = [c for c in recent_costs if c.bridge_name == bridge_name]
            if bridge_costs:
                costs = [c.cost_usd for c in bridge_costs]
                bridge_trends[bridge_name] = {
                    "min_cost": min(costs),
                    "max_cost": max(costs),
                    "avg_cost": sum(costs) / len(costs),
                    "current_cost": bridge_costs[-1].cost_usd,
                    "data_points": len(costs)
                }

        return {
            "route": f"{source_chain}→{target_chain}",
            "time_period_hours": hours,
            "bridge_trends": bridge_trends,
            "overall_min": min(c.cost_usd for c in recent_costs),
            "overall_max": max(c.cost_usd for c in recent_costs),
            "overall_avg": sum(c.cost_usd for c in recent_costs) / len(recent_costs)
        }

    async def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary"""
        # Get recent optimizations from memory
        recent_optimizations = await self._recall_memories("BRIDGE OPTIMIZATION", 10)

        return {
            "monitoring_stats": self.monitoring_stats,
            "active_bridges": len(self.bridges),
            "monitored_chains": len(self.chains),
            "cost_history_routes": len(self.cost_history),
            "cached_optimizations": len(self.optimization_cache),
            "recent_optimizations": len(recent_optimizations),
            "memory_enabled": self.memory_enabled
        }

    async def run_production_monitor(self):
        """Run the complete bridge monitoring system"""
        logger.info("🚀 Starting Bridge Cost Monitor Production System")

        try:
            await self.monitor_bridge_costs_continuously()
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown signal received")
            await self.shutdown()
        except Exception as e:
            logger.error(f"❌ System error: {e}")
            await self.shutdown()

    async def shutdown(self):
        """Gracefully shutdown the monitor"""
        logger.info("🛑 Shutting down Bridge Cost Monitor...")

        # Get final summary
        final_summary = await self.get_monitoring_summary()

        # Store shutdown summary
        await self._store_memory(
            f"Bridge Monitor shutdown: {final_summary['monitoring_stats']['total_quotes_fetched']} quotes fetched, ${final_summary['monitoring_stats']['cost_savings_identified']:.2f} savings identified",
            ["shutdown", "bridge-monitor", "final-summary"],
            "operational_event",
            final_summary
        )

        logger.info(f"✅ Shutdown complete - Total savings identified: ${final_summary['monitoring_stats']['cost_savings_identified']:.2f}")

async def main():
    """Main function"""
    monitor = MemoryEnhancedBridgeMonitor()

    await monitor.initialize()

    # Test optimization
    logger.info("🧪 Testing bridge optimization...")
    optimization = await monitor.get_optimal_bridge("ethereum", "arbitrum", 500, "cost")
    logger.info(f"Recommended: {optimization.recommended_bridge} at ${optimization.estimated_cost:.2f}")

    # Start monitoring
    await monitor.run_production_monitor()

if __name__ == "__main__":
    asyncio.run(main())
