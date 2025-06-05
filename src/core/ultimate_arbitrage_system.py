"""
Ultimate Arbitrage System
Combines flashloan execution, parallel processing, and real-time feeds
for maximum profit capture speed.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import our optimization components
from src.flashloan.flashloan_arbitrage_executor import FlashloanArbitrageExecutor
from src.core.parallel_arbitrage_engine import ParallelArbitrageEngine, OpportunityTask
from src.feeds.realtime_price_feeds import RealTimePriceFeeds
from src.execution.real_arbitrage_executor import RealArbitrageExecutor

logger = logging.getLogger(__name__)

class UltimateArbitrageSystem:
    """The ultimate profit-capturing arbitrage system."""
    
    def __init__(self, wallet_account, web3_connections):
        self.wallet_account = wallet_account
        self.web3_connections = web3_connections
        
        # Initialize optimization components
        self.flashloan_executor = FlashloanArbitrageExecutor(wallet_account, web3_connections)
        self.parallel_engine = ParallelArbitrageEngine(max_workers=8)
        self.realtime_feeds = RealTimePriceFeeds()
        self.fallback_executor = RealArbitrageExecutor()
        
        # System state
        self.is_running = False
        self.execution_mode = 'flashloan'  # 'flashloan', 'parallel', 'fallback'
        
        # Performance tracking
        self.performance_stats = {
            'opportunities_detected': 0,
            'opportunities_executed': 0,
            'total_profit_usd': 0.0,
            'average_execution_time': 0.0,
            'success_rate': 0.0,
            'fastest_execution': float('inf'),
            'system_uptime': 0.0,
            'start_time': 0.0
        }
        
        # Execution thresholds
        self.execution_thresholds = {
            'min_profit_usd': 0.05,      # Minimum $0.05 profit
            'max_opportunity_age': 15.0,  # Maximum 15 seconds old
            'min_success_rate': 0.7,     # 70% minimum success rate
            'max_execution_time': 5.0    # Maximum 5 seconds execution
        }
        
        logger.info("🚀 ULTIMATE ARBITRAGE SYSTEM INITIALIZED")
        logger.info("=" * 60)
        logger.info("   ⚡ Flashloan Executor: Ready")
        logger.info("   🔄 Parallel Engine: Ready")
        logger.info("   📡 Real-Time Feeds: Ready")
        logger.info("   🛡️ Fallback Executor: Ready")
    
    async def start(self):
        """Start the ultimate arbitrage system."""
        if self.is_running:
            logger.warning("⚠️ System already running")
            return
        
        self.is_running = True
        self.performance_stats['start_time'] = time.time()
        
        logger.info("🚀 STARTING ULTIMATE ARBITRAGE SYSTEM")
        logger.info("=" * 60)
        
        try:
            # Start all components
            await self.parallel_engine.start()
            await self.realtime_feeds.start()
            
            # Subscribe to real-time price updates
            self.realtime_feeds.subscribe_to_price_updates(self._handle_price_update)
            
            # Start main arbitrage loop
            asyncio.create_task(self._main_arbitrage_loop())
            
            # Start performance monitoring
            asyncio.create_task(self._monitor_performance())
            
            logger.info("✅ ULTIMATE ARBITRAGE SYSTEM STARTED")
            logger.info("🎯 Ready to capture profits at lightning speed!")
            
        except Exception as e:
            logger.error(f"❌ System startup error: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the ultimate arbitrage system."""
        logger.info("🛑 Stopping ultimate arbitrage system...")
        
        self.is_running = False
        
        try:
            # Stop all components
            await self.parallel_engine.stop()
            await self.realtime_feeds.stop()
            
            # Calculate final stats
            uptime = time.time() - self.performance_stats['start_time']
            self.performance_stats['system_uptime'] = uptime
            
            logger.info("📊 FINAL PERFORMANCE STATS:")
            logger.info(f"   ⏱️ Uptime: {uptime:.1f}s")
            logger.info(f"   🎯 Opportunities: {self.performance_stats['opportunities_detected']}")
            logger.info(f"   ✅ Executed: {self.performance_stats['opportunities_executed']}")
            logger.info(f"   💰 Total Profit: ${self.performance_stats['total_profit_usd']:.2f}")
            logger.info(f"   📈 Success Rate: {self.performance_stats['success_rate']:.1f}%")
            
            logger.info("✅ Ultimate arbitrage system stopped")
            
        except Exception as e:
            logger.error(f"❌ System shutdown error: {e}")
    
    async def _main_arbitrage_loop(self):
        """Main arbitrage detection and execution loop."""
        logger.info("🔄 Starting main arbitrage loop...")
        
        while self.is_running:
            try:
                # This loop handles opportunities from traditional scanning
                # Real-time opportunities are handled via price update callbacks
                
                await asyncio.sleep(1.0)  # Reduced from 2s for faster scanning
                
            except Exception as e:
                logger.error(f"❌ Main loop error: {e}")
                await asyncio.sleep(5.0)
    
    async def _handle_price_update(self, price_update, opportunities: List[Dict[str, Any]]):
        """Handle real-time price updates and opportunities."""
        try:
            if not opportunities:
                return
            
            logger.info(f"📡 REAL-TIME OPPORTUNITIES: {len(opportunities)} detected")
            
            # Update detection stats
            self.performance_stats['opportunities_detected'] += len(opportunities)
            
            # Process opportunities in parallel for maximum speed
            processed_opportunities = await self.parallel_engine.process_opportunities_parallel(opportunities)
            
            # Execute the best opportunities
            for opportunity in processed_opportunities:
                if opportunity.get('success', False) and opportunity.get('ready_for_execution', False):
                    await self._execute_opportunity_ultimate(opportunity['opportunity'])
            
        except Exception as e:
            logger.error(f"❌ Price update handling error: {e}")
    
    async def _execute_opportunity_ultimate(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute opportunity using the ultimate optimization strategy."""
        try:
            start_time = time.time()
            
            profit_usd = opportunity.get('estimated_profit_usd', 0)
            
            logger.info(f"🚀 ULTIMATE EXECUTION: {opportunity.get('token', 'UNKNOWN')} "
                       f"{opportunity.get('buy_dex', 'unknown')}→{opportunity.get('sell_dex', 'unknown')} "
                       f"(${profit_usd:.2f})")
            
            # Choose execution strategy based on profit and conditions
            execution_result = await self._choose_execution_strategy(opportunity)
            
            # Track performance
            execution_time = time.time() - start_time
            
            if execution_result.get('success', False):
                self.performance_stats['opportunities_executed'] += 1
                actual_profit = execution_result.get('profit_usd', 0)
                self.performance_stats['total_profit_usd'] += actual_profit

                # Update fastest execution time
                if execution_time < self.performance_stats['fastest_execution']:
                    self.performance_stats['fastest_execution'] = execution_time

                # 🎨 COLOR-CODED ULTIMATE SUCCESS: Yellow for success
                from src.utils.color_logger import log_ultimate_result
                log_ultimate_result(
                    logger=logger,
                    success=True,
                    profit_usd=actual_profit,
                    execution_time=execution_time
                )
            else:
                # 🎨 COLOR-CODED ULTIMATE FAILURE: Red for failure
                from src.utils.color_logger import log_ultimate_result
                log_ultimate_result(
                    logger=logger,
                    success=False,
                    profit_usd=0,
                    execution_time=execution_time,
                    error_message=execution_result.get('error', 'Unknown error')
                )
            
            # Update average execution time
            total_executed = self.performance_stats['opportunities_executed']
            if total_executed > 0:
                current_avg = self.performance_stats['average_execution_time']
                self.performance_stats['average_execution_time'] = (
                    (current_avg * (total_executed - 1) + execution_time) / total_executed
                )
            
            # Update success rate
            total_detected = self.performance_stats['opportunities_detected']
            if total_detected > 0:
                self.performance_stats['success_rate'] = (
                    self.performance_stats['opportunities_executed'] / total_detected * 100
                )
            
            return execution_result
            
        except Exception as e:
            logger.error(f"❌ Ultimate execution error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _choose_execution_strategy(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Choose the best execution strategy based on opportunity characteristics."""
        try:
            profit_usd = opportunity.get('estimated_profit_usd', 0)
            age_seconds = time.time() - opportunity.get('discovered_at', time.time())
            
            logger.info(f"🎯 STRATEGY SELECTION:")
            logger.info(f"   💰 Profit: ${profit_usd:.2f}")
            logger.info(f"   ⏰ Age: {age_seconds:.1f}s")
            
            # Strategy 1: Flashloan for high-profit opportunities
            if profit_usd >= 2.0 and age_seconds <= 10.0:
                logger.info("   🔥 STRATEGY: Flashloan (high profit, fresh)")
                return await self._execute_flashloan_strategy(opportunity)
            
            # Strategy 2: Parallel execution for medium opportunities
            elif profit_usd >= 0.5 and age_seconds <= 15.0:
                logger.info("   ⚡ STRATEGY: Parallel (medium profit)")
                return await self._execute_parallel_strategy(opportunity)
            
            # Strategy 3: Fallback for small opportunities
            elif profit_usd >= 0.05:
                logger.info("   🛡️ STRATEGY: Fallback (small profit)")
                return await self._execute_fallback_strategy(opportunity)
            
            else:
                return {'success': False, 'error': f'Opportunity below threshold: ${profit_usd:.2f}'}
            
        except Exception as e:
            logger.error(f"❌ Strategy selection error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _execute_flashloan_strategy(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute using flashloan for maximum speed and capital efficiency."""
        try:
            logger.info("🔥 EXECUTING FLASHLOAN STRATEGY")
            
            # Execute flashloan arbitrage
            result = await self.flashloan_executor.execute_flashloan_arbitrage(opportunity)
            
            if result.get('success', False):
                return {
                    'success': True,
                    'strategy': 'flashloan',
                    'profit_usd': result.get('profit_usd', 0),
                    'execution_time': result.get('execution_time', 0),
                    'tx_hash': result.get('tx_hash', ''),
                    'provider': result.get('provider', 'unknown')
                }
            else:
                # Fallback to parallel strategy if flashloan fails
                logger.warning("⚠️ Flashloan failed, falling back to parallel strategy")
                return await self._execute_parallel_strategy(opportunity)
            
        except Exception as e:
            logger.error(f"❌ Flashloan strategy error: {e}")
            return await self._execute_parallel_strategy(opportunity)
    
    async def _execute_parallel_strategy(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute using parallel processing for speed."""
        try:
            logger.info("⚡ EXECUTING PARALLEL STRATEGY")
            
            # Use the existing fast execution from the real arbitrage executor
            await self.fallback_executor.initialize()
            result = await self.fallback_executor.execute_arbitrage(opportunity)
            
            return {
                'success': result.get('success', False),
                'strategy': 'parallel',
                'profit_usd': result.get('profit_usd', 0),
                'execution_time': result.get('execution_time', 0),
                'tx_hash': result.get('tx_hash', ''),
                'error': result.get('error', '')
            }
            
        except Exception as e:
            logger.error(f"❌ Parallel strategy error: {e}")
            return await self._execute_fallback_strategy(opportunity)
    
    async def _execute_fallback_strategy(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute using fallback strategy."""
        try:
            logger.info("🛡️ EXECUTING FALLBACK STRATEGY")
            
            # Use standard execution
            await self.fallback_executor.initialize()
            result = await self.fallback_executor.execute_arbitrage(opportunity)
            
            return {
                'success': result.get('success', False),
                'strategy': 'fallback',
                'profit_usd': result.get('profit_usd', 0),
                'execution_time': result.get('execution_time', 0),
                'tx_hash': result.get('tx_hash', ''),
                'error': result.get('error', '')
            }
            
        except Exception as e:
            logger.error(f"❌ Fallback strategy error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _monitor_performance(self):
        """Monitor system performance and log statistics."""
        while self.is_running:
            try:
                # Log performance stats every 30 seconds
                await asyncio.sleep(30.0)
                
                uptime = time.time() - self.performance_stats['start_time']
                
                logger.info("📊 ULTIMATE SYSTEM PERFORMANCE:")
                logger.info(f"   ⏱️ Uptime: {uptime:.1f}s")
                logger.info(f"   🎯 Opportunities: {self.performance_stats['opportunities_detected']}")
                logger.info(f"   ✅ Executed: {self.performance_stats['opportunities_executed']}")
                logger.info(f"   💰 Total Profit: ${self.performance_stats['total_profit_usd']:.2f}")
                logger.info(f"   📈 Success Rate: {self.performance_stats['success_rate']:.1f}%")
                logger.info(f"   ⚡ Avg Execution: {self.performance_stats['average_execution_time']:.2f}s")
                logger.info(f"   🚀 Fastest: {self.performance_stats['fastest_execution']:.2f}s")
                
                # Get component stats
                parallel_stats = self.parallel_engine.get_performance_stats()
                feed_stats = self.realtime_feeds.get_stats()
                
                logger.info(f"   🔄 Parallel Tasks: {parallel_stats['tasks_processed']}")
                logger.info(f"   📡 Price Updates: {feed_stats['updates_received']}")
                
            except Exception as e:
                logger.error(f"❌ Performance monitoring error: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        return {
            'performance': self.performance_stats.copy(),
            'parallel_engine': self.parallel_engine.get_performance_stats(),
            'realtime_feeds': self.realtime_feeds.get_stats(),
            'execution_thresholds': self.execution_thresholds.copy(),
            'is_running': self.is_running,
            'execution_mode': self.execution_mode
        }
