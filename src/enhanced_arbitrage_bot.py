#!/usr/bin/env python3
"""
Enhanced Arbitrage Bot - Main Application

This is the main application that brings together all the migrated "gold" components
with MCP enhancement for intelligent arbitrage trading.
"""

import asyncio
import logging
import signal
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

# Import our components
from src.integrations.mcp.client_manager import MCPClientManager
from core.arbitrage.simple_path_finder import SimplePathFinder
from core.arbitrage.simple_profit_calculator import SimpleProfitCalculator
from core.arbitrage.simple_risk_analyzer import SimpleRiskAnalyzer
from core.detection.simple_cross_dex_detector import SimpleCrossDexDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedArbitrageBot:
    """Enhanced Arbitrage Bot with MCP integration."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the enhanced arbitrage bot.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.running = False
        self.shutdown_event = asyncio.Event()

        # Initialize components
        self.mcp_manager = MCPClientManager(config.get('mcp', {}))
        self.path_finder = SimplePathFinder(config.get('max_path_length', 3))
        self.profit_calculator = SimpleProfitCalculator(config)
        self.risk_analyzer = SimpleRiskAnalyzer(config)
        self.detector = SimpleCrossDexDetector(
            config.get('dexs', ['uniswap_v3', 'sushiswap']),
            config
        )

        # Trading configuration
        trading_config = config.get("trading", {})
        self.min_profit_threshold = trading_config.get("min_profit_threshold", 0.5)
        self.max_risk_score = trading_config.get("max_risk_score", 50)
        self.trading_enabled = trading_config.get("trading_enabled", False)
        self.scan_interval = trading_config.get("scan_interval", 10)  # seconds

        # Performance tracking
        self.stats = {
            'opportunities_found': 0,
            'opportunities_executed': 0,
            'total_profit': 0.0,
            'successful_trades': 0,
            'failed_trades': 0,
            'start_time': None,
            'last_scan': None
        }

        logger.info("Enhanced Arbitrage Bot initialized")

    async def start(self) -> None:
        """Start the arbitrage bot."""
        logger.info("🚀 Starting Enhanced Arbitrage Bot...")

        # Connect to MCP servers
        logger.info("Connecting to MCP servers...")
        if not await self.mcp_manager.connect_all():
            logger.error("Failed to connect to required MCP servers")
            return

        logger.info("✅ MCP servers connected successfully")

        # Set up signal handlers for graceful shutdown
        self._setup_signal_handlers()

        # Start main loop
        self.running = True
        self.stats['start_time'] = datetime.now()

        logger.info("🎯 Starting arbitrage detection loop...")
        await self._main_loop()

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self.shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def _main_loop(self) -> None:
        """Main arbitrage detection and execution loop."""
        while self.running and not self.shutdown_event.is_set():
            try:
                # Scan for opportunities
                await self._scan_and_execute()

                # Wait for next scan
                try:
                    await asyncio.wait_for(
                        self.shutdown_event.wait(),
                        timeout=self.scan_interval
                    )
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    continue  # Normal timeout, continue scanning

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying

        logger.info("Main loop stopped")
        await self._shutdown()

    async def _scan_and_execute(self) -> None:
        """Scan for arbitrage opportunities and execute viable ones."""
        self.stats['last_scan'] = datetime.now()

        try:
            # Detect opportunities
            logger.debug("Scanning for arbitrage opportunities...")
            opportunities = await self.detector.detect_opportunities_with_intelligence()

            if not opportunities:
                logger.debug("No opportunities detected")
                return

            logger.info(f"🔍 Found {len(opportunities)} potential opportunities")
            self.stats['opportunities_found'] += len(opportunities)

            # Analyze and filter opportunities
            viable_opportunities = []
            for opp in opportunities:
                enhanced_opp = await self._analyze_opportunity(opp)
                if enhanced_opp:
                    viable_opportunities.append(enhanced_opp)

            if not viable_opportunities:
                logger.info("No viable opportunities after analysis")
                return

            logger.info(f"✅ {len(viable_opportunities)} viable opportunities identified")

            # Execute opportunities (sorted by profit potential)
            viable_opportunities.sort(
                key=lambda x: x.get('enhanced_profit_score', 0),
                reverse=True
            )

            for opp in viable_opportunities[:3]:  # Execute top 3
                await self._execute_opportunity(opp)

        except Exception as e:
            logger.error(f"Error in scan and execute: {e}")

    async def _analyze_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any] | None:
        """Analyze an opportunity and enhance it with MCP intelligence.

        Args:
            opportunity: Raw opportunity data

        Returns:
            Enhanced opportunity or None if filtered out
        """
        try:
            # Calculate profit
            profit_result = self.profit_calculator.calculate_profit(opportunity)

            # Analyze risk
            risk_result = self.risk_analyzer.analyze_risk(opportunity)

            # Check basic thresholds with detailed logging
            profit_percentage = profit_result.get('net_profit_percentage', 0)
            risk_score = risk_result.get('risk_score', 100)
            is_profitable = profit_result.get('is_profitable', False)

            logger.info(f"🔍 Analyzing opportunity: profit={profit_percentage:.3f}%, risk={risk_score:.1f}, profitable={is_profitable}")
            logger.info(f"   Thresholds: min_profit={self.min_profit_threshold}%, max_risk={self.max_risk_score}")

            if not is_profitable:
                logger.info(f"❌ Opportunity filtered: not profitable (is_profitable={is_profitable})")
                return None

            if profit_percentage < self.min_profit_threshold:
                logger.info(f"❌ Opportunity filtered: profit {profit_percentage:.3f}% below threshold {self.min_profit_threshold}%")
                return None

            if risk_score > self.max_risk_score:
                logger.info(f"❌ Opportunity filtered: risk {risk_score:.1f} above threshold {self.max_risk_score}")
                return None

            # Get MCP intelligence
            mcp_intelligence = await self._get_mcp_intelligence(opportunity)

            # Calculate enhanced profit score
            enhanced_profit_score = self._calculate_enhanced_score(
                profit_result, risk_result, mcp_intelligence
            )

            # Create enhanced opportunity
            enhanced_opportunity = {
                **opportunity,
                'profit_analysis': profit_result,
                'risk_analysis': risk_result,
                'mcp_intelligence': mcp_intelligence,
                'enhanced_profit_score': enhanced_profit_score,
                'analysis_timestamp': datetime.now().isoformat()
            }

            logger.info(
                f"💎 Viable opportunity: {opportunity.get('tokens', [])} "
                f"profit=${profit_result.get('net_profit_usd', 0):.2f} "
                f"risk={risk_result.get('risk_score', 0):.1f} "
                f"score={enhanced_profit_score:.2f}"
            )

            return enhanced_opportunity

        except Exception as e:
            logger.error(f"Error analyzing opportunity: {e}")
            return None

    async def _get_mcp_intelligence(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Get MCP intelligence for an opportunity."""
        intelligence = {
            'market_data_available': False,
            'historical_patterns': [],
            'confidence_score': 0.5
        }

        try:
            if self.mcp_manager.connected:
                # Get market data
                tokens = opportunity.get('tokens', [])
                market_data = await self.mcp_manager.get_market_data(tokens)
                intelligence['market_data_available'] = bool(market_data)

                # Get similar opportunities
                similar_opps = await self.mcp_manager.get_similar_opportunities(opportunity)
                intelligence['historical_patterns'] = similar_opps

                # Calculate confidence based on historical success
                if similar_opps:
                    successful = sum(1 for opp in similar_opps if opp.get('success', False))
                    intelligence['confidence_score'] = successful / len(similar_opps)

        except Exception as e:
            logger.warning(f"Error getting MCP intelligence: {e}")

        return intelligence

    def _calculate_enhanced_score(self, profit_result: Dict[str, Any],
                                 risk_result: Dict[str, Any],
                                 mcp_intelligence: Dict[str, Any]) -> float:
        """Calculate enhanced profit score."""
        base_profit = profit_result.get('net_profit_percentage', 0)
        risk_factor = max(0.1, (100 - risk_result.get('risk_score', 50)) / 100)
        confidence_factor = mcp_intelligence.get('confidence_score', 0.5)

        enhanced_score = base_profit * risk_factor * (1 + confidence_factor)
        return enhanced_score

    async def _execute_opportunity(self, opportunity: Dict[str, Any]) -> None:
        """Execute an arbitrage opportunity.

        Args:
            opportunity: Enhanced opportunity to execute
        """
        opp_id = opportunity.get('id', 'unknown')

        try:
            logger.info(f"🎯 Executing opportunity {opp_id}")

            if not self.trading_enabled:
                # Simulation mode
                result = await self._simulate_execution(opportunity)
                logger.info(f"📊 Simulated execution: {'SUCCESS' if result['success'] else 'FAILED'}")
            else:
                # Real execution (placeholder)
                result = await self._real_execution(opportunity)
                logger.info(f"💰 Real execution: {'SUCCESS' if result['success'] else 'FAILED'}")

            # Update stats
            self.stats['opportunities_executed'] += 1
            if result.get('success', False):
                self.stats['successful_trades'] += 1
                self.stats['total_profit'] += result.get('profit', 0)
            else:
                self.stats['failed_trades'] += 1

            # Store pattern in MCP for learning
            if self.mcp_manager.connected:
                await self.mcp_manager.store_arbitrage_pattern(opportunity, result)

        except Exception as e:
            logger.error(f"Error executing opportunity {opp_id}: {e}")
            self.stats['failed_trades'] += 1

    async def _simulate_execution(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate opportunity execution."""
        # Simulate execution delay
        await asyncio.sleep(0.1)

        # Simulate success based on enhanced score
        enhanced_score = opportunity.get('enhanced_profit_score', 0)
        success_probability = min(enhanced_score / 5, 0.9)  # Cap at 90%

        import random
        success = random.random() < success_probability

        profit_analysis = opportunity.get('profit_analysis', {})

        return {
            'success': success,
            'simulated': True,
            'profit': profit_analysis.get('net_profit_usd', 0) if success else 0,
            'gas_used': random.randint(100000, 300000),
            'execution_time': random.uniform(1.0, 5.0),
            'timestamp': datetime.now().isoformat()
        }

    async def _real_execution(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute real trade (placeholder for actual implementation)."""
        # This would contain actual trading logic
        logger.warning("Real execution not implemented yet - using simulation")
        return await self._simulate_execution(opportunity)

    async def get_stats(self) -> Dict[str, Any]:
        """Get bot performance statistics."""
        runtime = None
        if self.stats['start_time']:
            runtime = (datetime.now() - self.stats['start_time']).total_seconds()

        return {
            **self.stats,
            'runtime_seconds': runtime,
            'success_rate': (
                self.stats['successful_trades'] / max(self.stats['opportunities_executed'], 1)
            ),
            'mcp_connected': self.mcp_manager.connected,
            'trading_enabled': self.trading_enabled
        }

    async def _shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("🛑 Shutting down Enhanced Arbitrage Bot...")

        self.running = False

        # Disconnect from MCP servers
        if self.mcp_manager.connected:
            await self.mcp_manager.disconnect_all()

        # Print final stats
        stats = await self.get_stats()
        logger.info("📊 Final Statistics:")
        logger.info(f"   Runtime: {stats.get('runtime_seconds', 0):.1f} seconds")
        logger.info(f"   Opportunities found: {stats['opportunities_found']}")
        logger.info(f"   Opportunities executed: {stats['opportunities_executed']}")
        logger.info(f"   Success rate: {stats['success_rate']:.1%}")
        logger.info(f"   Total profit: ${stats['total_profit']:.2f}")

        logger.info("✅ Shutdown complete")


async def main():
    """Main entry point."""

    # Configuration
    config = {
        'max_path_length': 3,
        'gas_price_gwei': 20,
        'eth_price_usd': 3000,
        'dexs': ['uniswap_v3', 'sushiswap', 'curve'],
        'trading': {
            'min_profit_threshold': 0.5,  # 0.5% minimum profit
            'max_risk_score': 60,          # Maximum acceptable risk
            'trading_enabled': False,      # Simulation mode
            'scan_interval': 15            # Scan every 15 seconds (reduced API pressure)
        },
        'mcp': {
            'servers': {
                'dexmind': {'type': 'memory', 'required': True},
                'memory_service': {'type': 'memory', 'required': True},
                'coincap': {'type': 'market_data', 'required': False}
            }
        }
    }

    # Create and start bot
    bot = EnhancedArbitrageBot(config)
    await bot.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)
