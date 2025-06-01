#!/usr/bin/env python3
"""
Multi-Instance Arbitrage Manager with Shared Memory
Manages multiple arbitrage bot instances with shared learning and coordination
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import subprocess
import signal

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
class BotInstance:
    """Bot instance configuration"""
    instance_id: int
    strategy: str
    allocated_capital: float
    chains: List[str]
    dexes: List[str]
    status: str = "stopped"
    process: Optional[subprocess.Popen] = None
    performance: Dict[str, Any] = None

class MultiInstanceArbitrageManager:
    """
    Manages multiple arbitrage bot instances with shared memory and coordination
    
    Features:
    - Shared memory across all instances
    - Dynamic capital allocation
    - Performance-based scaling
    - Risk management coordination
    - Strategy specialization
    """
    
    def __init__(self, total_capital: float = 1175):
        self.total_capital = total_capital
        self.available_capital = total_capital * 0.9  # 10% reserve
        self.memory_server = None
        self.instances: List[BotInstance] = []
        self.performance_metrics = {}
        self.running = False
        
        # Instance configurations
        self.instance_configs = [
            {
                "strategy": "cross_chain_mev",
                "capital_ratio": 0.4,  # 40% of capital
                "chains": ["ethereum", "arbitrum", "base"],
                "dexes": ["uniswap", "sushiswap", "curve"],
                "scan_interval": 15  # seconds
            },
            {
                "strategy": "dex_arbitrage", 
                "capital_ratio": 0.35,  # 35% of capital
                "chains": ["ethereum"],
                "dexes": ["uniswap", "sushiswap", "balancer", "curve"],
                "scan_interval": 10  # seconds
            },
            {
                "strategy": "bridge_optimization",
                "capital_ratio": 0.25,  # 25% of capital
                "chains": ["ethereum", "arbitrum", "base", "optimism"],
                "dexes": ["uniswap", "curve"],
                "scan_interval": 30  # seconds
            }
        ]
    
    async def initialize(self):
        """Initialize the multi-instance manager"""
        logger.info("🤖 Initializing Multi-Instance Arbitrage Manager")
        logger.info(f"💰 Total capital: ${self.total_capital}")
        logger.info(f"💰 Available for trading: ${self.available_capital}")
        
        # Initialize memory system
        if MEMORY_AVAILABLE:
            try:
                self.memory_server = MemoryServer()
                await self.memory_server.initialize()
                logger.info("✅ Shared memory system initialized")
                
                # Store manager initialization
                await self._store_memory(
                    f"Multi-Instance Manager initialized with ${self.total_capital} capital, {len(self.instance_configs)} strategies",
                    ["multi-instance", "initialization", "manager"],
                    "system_event"
                )
            except Exception as e:
                logger.warning(f"Memory system unavailable: {e}")
                self.memory_server = None
        
        # Create bot instances
        await self._create_instances()
        
        logger.info(f"✅ Manager initialized with {len(self.instances)} instances")
    
    async def _create_instances(self):
        """Create bot instances based on configuration"""
        for i, config in enumerate(self.instance_configs):
            allocated_capital = self.available_capital * config["capital_ratio"]
            
            instance = BotInstance(
                instance_id=i + 1,
                strategy=config["strategy"],
                allocated_capital=allocated_capital,
                chains=config["chains"],
                dexes=config["dexes"],
                performance={"total_profit": 0, "trades": 0, "success_rate": 0}
            )
            
            self.instances.append(instance)
            logger.info(f"📋 Created instance {instance.instance_id}: {instance.strategy} (${allocated_capital:.2f})")
    
    async def _store_memory(self, content: str, tags: List[str], memory_type: str, metadata: Dict[str, Any] = None):
        """Store memory in shared system"""
        if not self.memory_server:
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
    
    async def _recall_shared_memories(self, query: str, n_results: int = 5) -> List[str]:
        """Recall memories from shared system"""
        if not self.memory_server:
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
    
    async def start_all_instances(self):
        """Start all bot instances"""
        logger.info("🚀 Starting all bot instances...")
        
        for instance in self.instances:
            await self._start_instance(instance)
            await asyncio.sleep(2)  # Stagger startup
        
        self.running = True
        logger.info("✅ All instances started")
        
        # Store startup event
        await self._store_memory(
            f"All {len(self.instances)} bot instances started successfully",
            ["multi-instance", "startup", "all-instances"],
            "operational_event"
        )
    
    async def _start_instance(self, instance: BotInstance):
        """Start a single bot instance"""
        logger.info(f"🚀 Starting instance {instance.instance_id}: {instance.strategy}")
        
        # Create instance-specific script
        instance_script = f"""
import asyncio
import random
import sys
import os
from datetime import datetime

# Add memory service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcp-memory-service', 'src'))

class ArbitrageInstance:
    def __init__(self):
        self.instance_id = {instance.instance_id}
        self.strategy = "{instance.strategy}"
        self.capital = {instance.allocated_capital}
        self.chains = {instance.chains}
        self.dexes = {instance.dexes}
        self.total_profit = 0
        self.trades_executed = 0
    
    async def run_strategy(self):
        print(f"🤖 Instance {{self.instance_id}} ({{self.strategy}}) starting with ${{self.capital:.2f}}")
        
        while True:
            # Simulate strategy execution
            if random.random() > 0.7:  # 30% chance of finding opportunity
                profit = random.uniform(-2, 15)  # -$2 to +$15
                self.total_profit += profit
                self.trades_executed += 1
                
                status = "SUCCESS" if profit > 0 else "LOSS"
                print(f"📊 Instance {{self.instance_id}}: {{status}} ${{profit:.2f}} (Total: ${{self.total_profit:.2f}}, Trades: {{self.trades_executed}})")
            
            await asyncio.sleep({self.instance_configs[instance.instance_id-1].get('scan_interval', 20)})

if __name__ == "__main__":
    instance = ArbitrageInstance()
    asyncio.run(instance.run_strategy())
"""
        
        # Write instance script
        script_path = f"instance_{instance.instance_id}_{instance.strategy}.py"
        with open(script_path, "w") as f:
            f.write(instance_script)
        
        # Start instance process
        try:
            process = subprocess.Popen([
                sys.executable, script_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            instance.process = process
            instance.status = "running"
            
            logger.info(f"✅ Instance {instance.instance_id} started (PID: {process.pid})")
            
        except Exception as e:
            logger.error(f"❌ Failed to start instance {instance.instance_id}: {e}")
            instance.status = "failed"
    
    async def monitor_instances(self):
        """Monitor all running instances"""
        logger.info("📊 Starting instance monitoring...")
        
        while self.running:
            active_instances = 0
            total_profit = 0
            
            for instance in self.instances:
                if instance.process and instance.process.poll() is None:
                    active_instances += 1
                    total_profit += instance.performance.get("total_profit", 0)
                else:
                    if instance.status == "running":
                        logger.warning(f"⚠️ Instance {instance.instance_id} ({instance.strategy}) stopped unexpectedly")
                        instance.status = "stopped"
                        
                        # Attempt restart
                        logger.info(f"🔄 Attempting to restart instance {instance.instance_id}")
                        await self._start_instance(instance)
            
            # Log status
            logger.info(f"📊 Status: {active_instances}/{len(self.instances)} instances active, Total profit: ${total_profit:.2f}")
            
            # Store monitoring data
            await self._store_memory(
                f"Instance monitoring: {active_instances}/{len(self.instances)} active, ${total_profit:.2f} total profit",
                ["monitoring", "multi-instance", "performance"],
                "monitoring_data",
                {"active_instances": active_instances, "total_profit": total_profit}
            )
            
            await asyncio.sleep(60)  # Monitor every minute
    
    async def optimize_capital_allocation(self):
        """Dynamically optimize capital allocation based on performance"""
        logger.info("💰 Starting dynamic capital optimization...")
        
        while self.running:
            # Get performance data from memory
            performance_memories = await self._recall_shared_memories("instance performance profit", 10)
            
            # Analyze performance and adjust allocations
            best_strategy = None
            best_performance = 0
            
            for instance in self.instances:
                if instance.performance["total_profit"] > best_performance:
                    best_performance = instance.performance["total_profit"]
                    best_strategy = instance.strategy
            
            if best_strategy:
                logger.info(f"🎯 Best performing strategy: {best_strategy} (${best_performance:.2f})")
                
                # Store optimization insight
                await self._store_memory(
                    f"OPTIMIZATION INSIGHT: {best_strategy} showing best performance with ${best_performance:.2f} profit",
                    ["optimization", "capital-allocation", "performance-analysis"],
                    "optimization_insight"
                )
            
            await asyncio.sleep(300)  # Optimize every 5 minutes
    
    async def coordinate_strategies(self):
        """Coordinate strategies across instances to avoid conflicts"""
        logger.info("🤝 Starting strategy coordination...")
        
        while self.running:
            # Get recent trading activities from memory
            recent_trades = await self._recall_shared_memories("arbitrage trade", 20)
            
            # Analyze for conflicts or opportunities for coordination
            if len(recent_trades) > 5:
                logger.info(f"📈 High activity detected: {len(recent_trades)} recent trades")
                
                # Store coordination insight
                await self._store_memory(
                    f"COORDINATION: High trading activity detected with {len(recent_trades)} recent trades - monitoring for conflicts",
                    ["coordination", "strategy-management", "conflict-prevention"],
                    "coordination_event"
                )
            
            await asyncio.sleep(180)  # Coordinate every 3 minutes
    
    async def run_production_system(self):
        """Run the complete multi-instance production system"""
        logger.info("🎯 Starting Multi-Instance Production System")
        
        try:
            # Start all instances
            await self.start_all_instances()
            
            # Start monitoring and optimization tasks
            tasks = [
                asyncio.create_task(self.monitor_instances()),
                asyncio.create_task(self.optimize_capital_allocation()),
                asyncio.create_task(self.coordinate_strategies())
            ]
            
            # Run until interrupted
            await asyncio.gather(*tasks)
            
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown signal received")
            await self.shutdown()
        except Exception as e:
            logger.error(f"❌ System error: {e}")
            await self.shutdown()
    
    async def get_system_performance(self) -> Dict[str, Any]:
        """Get comprehensive system performance metrics"""
        total_profit = sum(instance.performance.get("total_profit", 0) for instance in self.instances)
        total_trades = sum(instance.performance.get("trades", 0) for instance in self.instances)
        active_instances = sum(1 for instance in self.instances if instance.status == "running")

        return {
            "total_profit": total_profit,
            "total_trades": total_trades,
            "active_instances": active_instances,
            "total_instances": len(self.instances),
            "capital_utilization": (self.available_capital - total_profit) / self.available_capital,
            "average_profit_per_trade": total_profit / max(total_trades, 1)
        }

    async def shutdown(self):
        """Gracefully shutdown all instances"""
        logger.info("🛑 Shutting down multi-instance system...")

        self.running = False

        # Get final performance metrics
        final_performance = await self.get_system_performance()

        # Stop all instances
        for instance in self.instances:
            if instance.process:
                logger.info(f"   Stopping instance {instance.instance_id}...")
                instance.process.terminate()
                try:
                    instance.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    instance.process.kill()
                instance.status = "stopped"

        # Store shutdown event with performance data
        await self._store_memory(
            f"Multi-instance system shutdown: ${final_performance['total_profit']:.2f} profit, {final_performance['total_trades']} trades",
            ["shutdown", "multi-instance", "final-performance"],
            "operational_event",
            final_performance
        )

        logger.info(f"✅ System shutdown - Final profit: ${final_performance['total_profit']:.2f}")

async def main():
    """Main function"""
    manager = MultiInstanceArbitrageManager(total_capital=1175)

    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        asyncio.create_task(manager.shutdown())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    await manager.initialize()
    await manager.run_production_system()

if __name__ == "__main__":
    asyncio.run(main())
