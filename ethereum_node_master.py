#!/usr/bin/env python3
"""
🚀 ETHEREUM NODE MASTER CONTROLLER
Your MEV Empire Command Center

Strategies:
1. Liquidation Bot (high probability opportunities)
2. ⚡ Flashloan Arbitrage (your system + node power)  
3. 🎯 Frontrun Frontrunners (your brilliant idea!)
4. 🌉 Cross-Chain Arbitrage (coming soon)
5. 🛡️ Anti-Sandwich (coming soon)

Features:
- Run multiple strategies simultaneously
- Performance monitoring and reporting
- Automatic strategy switching based on market conditions
- Real-time profit tracking
- Gas optimization across all strategies
"""

import asyncio
import logging
import time
import os
import signal
from typing import Dict, List, Optional
from dataclasses import dataclass
import json

# Import your Ethereum node strategies
from src.ethereum_node.liquidation_bot import EthereumLiquidationBot
from src.ethereum_node.ethereum_flashloan_arbitrage import EthereumFlashloanArbitrage
from src.ethereum_node.frontrun_frontrunners import FrontrunFrontrunnersBot

logger = logging.getLogger(__name__)

@dataclass
class StrategyConfig:
    """Strategy configuration"""
    name: str
    enabled: bool
    priority: int
    min_profit: float
    max_gas_gwei: float
    allocation_percentage: float

@dataclass
class PerformanceMetrics:
    """Performance metrics for a strategy"""
    strategy_name: str
    runtime: float
    opportunities_found: int
    executions_attempted: int
    executions_successful: int
    total_profit: float
    success_rate: float
    profit_per_hour: float

class EthereumNodeMaster:
    """
    🚀 ETHEREUM NODE MASTER CONTROLLER
    
    Your MEV Empire Command Center - orchestrates all strategies
    """
    
    def __init__(self, ethereum_node_url: str):
        self.node_url = ethereum_node_url
        self.start_time = time.time()
        
        # Strategy configurations
        self.strategy_configs = {
            'liquidation': StrategyConfig(
                name='Liquidation Bot',
                enabled=True,
                priority=1,  # Highest priority (guaranteed profits)
                min_profit=50.0,
                max_gas_gwei=300.0,  # 🔥 MAXIMUM: Liquidations = guaranteed profit
                allocation_percentage=40.0
            ),
            'flashloan_arbitrage': StrategyConfig(
                name='Flashloan Arbitrage',
                enabled=True,
                priority=2,
                min_profit=10.0,
                max_gas_gwei=200.0,  # 🔥 HIGH: Fast execution needed
                allocation_percentage=35.0
            ),
            'frontrun_frontrunners': StrategyConfig(
                name='Frontrun Frontrunners',
                enabled=True,
                priority=3,
                min_profit=25.0,
                max_gas_gwei=250.0,  # 🔥 VERY HIGH: Must beat other frontrunners
                allocation_percentage=25.0
            )
        }
        
        # Strategy instances
        self.strategies = {}
        self.strategy_tasks = {}
        
        # Performance tracking
        self.total_profit = 0.0
        self.total_gas_used = 0.0
        self.total_transactions = 0
        
        # Control flags
        self.running = False
        self.shutdown_requested = False
        
        logger.info("🚀 Ethereum Node Master Controller initialized")
    
    async def initialize(self):
        """Initialize all enabled strategies"""
        
        logger.info(f"🔗 Initializing Ethereum Node Master...")
        logger.info(f"📡 Node URL: {self.node_url}")
        
        # Initialize enabled strategies
        for strategy_id, config in self.strategy_configs.items():
            if config.enabled:
                try:
                    logger.info(f"🚀 Initializing {config.name}...")
                    
                    if strategy_id == 'liquidation':
                        strategy = EthereumLiquidationBot(self.node_url)
                    elif strategy_id == 'flashloan_arbitrage':
                        strategy = EthereumFlashloanArbitrage(self.node_url)
                    elif strategy_id == 'frontrun_frontrunners':
                        strategy = FrontrunFrontrunnersBot(self.node_url)
                    else:
                        logger.warning(f"⚠️ Unknown strategy: {strategy_id}")
                        continue
                    
                    await strategy.initialize()
                    self.strategies[strategy_id] = strategy
                    
                    logger.info(f"✅ {config.name} initialized")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to initialize {config.name}: {e}")
                    config.enabled = False
        
        if not self.strategies:
            raise Exception("No strategies successfully initialized!")
        
        logger.info(f"🎯 {len(self.strategies)} strategies ready for deployment")
    
    async def start_mev_empire(self):
        """
        🚀 START YOUR MEV EMPIRE!
        """
        
        logger.info("🚀" * 20)
        logger.info("💎 STARTING MEV EMPIRE")
        logger.info("🚀" * 20)
        
        self.running = True
        
        # Start all enabled strategies
        for strategy_id, strategy in self.strategies.items():
            config = self.strategy_configs[strategy_id]
            
            logger.info(f"🎯 Starting {config.name} (Priority {config.priority})")
            
            try:
                if strategy_id == 'liquidation':
                    task = asyncio.create_task(strategy.start_liquidation_hunting())
                elif strategy_id == 'flashloan_arbitrage':
                    task = asyncio.create_task(strategy.start_arbitrage_hunting())
                elif strategy_id == 'frontrun_frontrunners':
                    task = asyncio.create_task(strategy.start_frontrunning())
                
                self.strategy_tasks[strategy_id] = task
                
            except Exception as e:
                logger.error(f"❌ Failed to start {config.name}: {e}")
        
        # Start monitoring and reporting
        monitor_task = asyncio.create_task(self._monitor_performance())
        report_task = asyncio.create_task(self._periodic_reporting())
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Wait for all tasks
            all_tasks = list(self.strategy_tasks.values()) + [monitor_task, report_task]
            await asyncio.gather(*all_tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ Error in MEV empire: {e}")
        
        finally:
            await self._shutdown()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum}, initiating shutdown...")
        self.shutdown_requested = True
    
    async def _monitor_performance(self):
        """Monitor performance across all strategies"""
        
        logger.info("📊 Starting performance monitoring...")
        
        while self.running and not self.shutdown_requested:
            try:
                # Check strategy health
                for strategy_id, task in self.strategy_tasks.items():
                    if task.done():
                        exception = task.exception()
                        if exception:
                            logger.error(f"❌ Strategy {strategy_id} failed: {exception}")
                            # Could restart strategy here
                
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ Error in performance monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _periodic_reporting(self):
        """Generate periodic performance reports"""
        
        logger.info("📈 Starting periodic reporting...")
        
        while self.running and not self.shutdown_requested:
            try:
                await asyncio.sleep(300)  # Report every 5 minutes
                
                # Generate performance report
                await self._generate_performance_report()
                
            except Exception as e:
                logger.error(f"❌ Error in periodic reporting: {e}")
                await asyncio.sleep(300)
    
    async def _generate_performance_report(self):
        """Generate comprehensive performance report"""
        
        logger.info("\n" + "📊" * 20)
        logger.info("💎 MEV EMPIRE PERFORMANCE REPORT")
        logger.info("📊" * 20)
        
        total_runtime = time.time() - self.start_time
        empire_profit = 0.0
        empire_transactions = 0
        
        # Get stats from each strategy
        for strategy_id, strategy in self.strategies.items():
            config = self.strategy_configs[strategy_id]
            
            try:
                stats = strategy.get_performance_stats()
                
                logger.info(f"\n🎯 {config.name.upper()}:")
                logger.info(f"   Runtime: {stats.get('runtime', 'N/A')}")
                logger.info(f"   Success Rate: {stats.get('success_rate', 'N/A')}")
                logger.info(f"   Total Profit: {stats.get('total_profit', 'N/A')}")
                logger.info(f"   Profit/Hour: {stats.get('profit_per_hour', 'N/A')}")
                
                # Extract profit for empire totals
                profit_str = stats.get('total_profit', '$0.00')
                if profit_str.startswith('$'):
                    try:
                        profit = float(profit_str[1:])
                        empire_profit += profit
                    except:
                        pass
                
            except Exception as e:
                logger.warning(f"⚠️ Could not get stats for {config.name}: {e}")
        
        # Empire totals
        logger.info(f"\n💎 EMPIRE TOTALS:")
        logger.info(f"   Total Runtime: {total_runtime/3600:.1f} hours")
        logger.info(f"   Total Profit: ${empire_profit:.2f}")
        logger.info(f"   Profit/Hour: ${empire_profit / max(total_runtime/3600, 1):.2f}")
        logger.info(f"   Active Strategies: {len(self.strategies)}")
        
        # Strategy rankings
        logger.info(f"\n🏆 STRATEGY RANKINGS:")
        logger.info("   1. 💰 Liquidation Bot (Guaranteed profits)")
        logger.info("   2. ⚡ Flashloan Arbitrage (High frequency)")
        logger.info("   3. 🎯 Frontrun Frontrunners (Your brilliant idea!)")
        
        logger.info("📊" * 20)
    
    async def _shutdown(self):
        """Graceful shutdown of all strategies"""
        
        logger.info("🛑 Shutting down MEV Empire...")
        
        self.running = False
        
        # Cancel all strategy tasks
        for strategy_id, task in self.strategy_tasks.items():
            if not task.done():
                logger.info(f"🛑 Stopping {strategy_id}...")
                task.cancel()
                
                try:
                    await asyncio.wait_for(task, timeout=10.0)
                except asyncio.TimeoutError:
                    logger.warning(f"⚠️ {strategy_id} did not stop gracefully")
                except asyncio.CancelledError:
                    logger.info(f"✅ {strategy_id} stopped")
        
        # Final performance report
        await self._generate_performance_report()
        
        logger.info("🛑 MEV Empire shutdown complete")
    
    def get_empire_stats(self) -> Dict:
        """Get overall empire statistics"""
        
        runtime = time.time() - self.start_time
        
        return {
            'runtime_hours': runtime / 3600,
            'active_strategies': len(self.strategies),
            'total_profit': self.total_profit,
            'profit_per_hour': self.total_profit / max(runtime/3600, 1),
            'strategies': {
                strategy_id: config.name 
                for strategy_id, config in self.strategy_configs.items() 
                if config.enabled
            }
        }


async def main():
    """
    🚀 MAIN ETHEREUM NODE MASTER CONTROLLER
    """
    
    print("🚀" * 30)
    print("💎 ETHEREUM NODE MEV EMPIRE")
    print("🚀" * 30)
    print("🎯 Strategy 1: Liquidation Bot")
    print("⚡ Strategy 2: Flashloan Arbitrage")
    print("🎯 Strategy 3: Frontrun Frontrunners")
    print("🌉 Strategy 4: Cross-Chain (Coming Soon)")
    print("🛡️ Strategy 5: Anti-Sandwich (Coming Soon)")
    print("🚀" * 30)
    
    # Your Ethereum node URL
    ethereum_node_url = os.getenv('ETHEREUM_NODE_URL', 'http://localhost:8545')
    
    if not ethereum_node_url:
        print("❌ Please set ETHEREUM_NODE_URL environment variable")
        return
    
    print(f"📡 Ethereum Node: {ethereum_node_url}")
    
    master = EthereumNodeMaster(ethereum_node_url)
    
    try:
        await master.initialize()
        await master.start_mev_empire()
        
    except KeyboardInterrupt:
        logger.info("🛑 MEV Empire stopped by user")
    except Exception as e:
        logger.error(f"💥 MEV Empire failed: {e}")
    
    finally:
        stats = master.get_empire_stats()
        logger.info(f"📊 Final Empire Stats: {stats}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
    asyncio.run(main())
