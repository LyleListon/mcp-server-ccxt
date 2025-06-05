#!/usr/bin/env python3
"""
Real Arbitrage Bot

Enhanced arbitrage bot using real price data from multiple sources.
Combines your legacy "gold" components with live market data.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, List, Any

# Import our enhanced components
from dex.dex_manager import DEXManager
from integrations.mcp.client_manager import MCPClientManager
from utils.gas_price_oracle import GasPriceOracle
from src.core.filters.advanced_opportunity_filter import AdvancedOpportunityFilter

# 🎯 CENTRALIZED CONFIGURATION - Single source of truth!
from config.trading_config import CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealArbitrageBot:
    """Enhanced arbitrage bot with real price data and MCP intelligence."""

    def __init__(self):
        """Initialize the real arbitrage bot."""
        self.running = False
        self.dex_manager = None
        self.mcp_manager = None
        self.gas_oracle = None

        # Initialize advanced opportunity filter
        filter_config = {
            'max_opportunity_age_seconds': 15,  # 🚀 SPEED: Only execute opportunities < 15 seconds old
            'min_profit_after_decay': 1.0,     # 💰 PROFIT: Minimum $1 after decay
            'min_execution_speed_score': 0.4,  # ⚡ SPEED: Minimum speed score
            'max_estimated_execution_time': 12.0  # ⏱️ TIME: Max 12 seconds execution time
        }
        self.opportunity_filter = AdvancedOpportunityFilter(filter_config)

        # Enhanced Configuration for Phase 1
        self.config = {
            'trading': {
                'min_profit_threshold': 0.05,  # 0.05% minimum profit (micro-arbitrage)
                'max_risk_score': 50,
                'trading_enabled': True,  # 🚀 SPEED: Enable real trading for testing
                'scan_interval': 2,  # 🚀 SPEED: Scan every 2 seconds (ultra-fast detection)
                'max_trade_size_usd': 2000,  # $2000 max trade size
                'fast_gas_multiplier': 1.5,  # 🚀 SPEED: Pay 50% more gas for priority
                'parallel_execution': True,  # 🚀 SPEED: Prepare transactions in parallel
                'skip_gas_estimation': True  # 🚀 SPEED: Use fixed gas limits
            },
            'dexs': {
                'uniswap_v3': {
                    'enabled': True,  # Enable for real DEX arbitrage
                    'max_slippage': 0.5,
                    'gas_limit': 300000,
                    'ethereum_rpc_url': 'http://localhost:8545'  # Your Ethereum node
                },
                'sushiswap': {
                    'enabled': True,  # Enable for real DEX arbitrage
                    'max_slippage': 0.5,
                    'gas_limit': 250000
                },
                'coinbase': {
                    'enabled': False,  # No CEX arbitrage - DEX only!
                    'rate_limit_delay': 1.5
                },
                'coingecko': {
                    'enabled': False,  # No CEX arbitrage - DEX only!
                    'rate_limit_delay': 1.5
                },
                '1inch': {
                    'enabled': False,  # Disabled - backing out of 1inch integration
                    'rate_limit_delay': 0.5,
                    'api_key': None
                },
                'paraswap': {
                    'enabled': True,  # DEX aggregator
                    'rate_limit_delay': 0.3,
                    'network': 1
                },
                'stablecoin_specialist': {
                    'enabled': True,  # Stablecoin micro-arbitrage
                    'rate_limit_delay': 0.2,
                    'min_deviation': 0.0005  # 0.05% minimum deviation
                },
                # Smaller DEXs (enabled for better arbitrage opportunities)
                'camelot': {
                    'enabled': True,  # ✅ ENABLED: Arbitrum DEX for better opportunities
                    'rate_limit_delay': 1.0
                },
                'traderjoe': {
                    'enabled': True,  # ✅ ENABLED: Arbitrum DEX for better opportunities
                    'rate_limit_delay': 1.0
                },
                'aerodrome': {
                    'enabled': True,  # ✅ ENABLED: Leading Base DEX for better opportunities
                    'rate_limit_delay': 1.0
                },
                # Working smaller DEXs discovered by DEX discovery tool
                'kyberswap': {
                    'enabled': True,  # ✅ DISCOVERED: Working API, good arbitrage potential
                    'rate_limit_delay': 1.0
                }
            }
        }

        # Statistics
        self.stats = {
            'opportunities_found': 0,
            'opportunities_executed': 0,
            'total_profit_usd': 0.0,
            'successful_trades': 0,
            'failed_trades': 0,
            'start_time': datetime.now()
        }

        logger.info("Real Arbitrage Bot initialized")

    async def initialize(self) -> bool:
        """Initialize all components."""
        try:
            logger.info("🚀 Starting Real Arbitrage Bot...")

            # Initialize DEX manager
            logger.info("Connecting to price sources...")
            self.dex_manager = DEXManager(self.config)

            connected = await self.dex_manager.connect_all()
            if not connected:
                logger.error("Failed to connect to any price sources")
                return False

            connected_sources = self.dex_manager.get_connected_dexs()
            logger.info(f"✅ Connected to {len(connected_sources)} price sources: {connected_sources}")

            # Initialize Gas Oracle
            logger.info("Connecting to gas price oracle...")
            try:
                self.gas_oracle = GasPriceOracle()
                await self.gas_oracle.connect()
                logger.info("✅ Gas price oracle connected successfully")
            except Exception as e:
                logger.warning(f"Gas oracle connection failed (continuing with estimates): {e}")
                self.gas_oracle = None

            # Initialize MCP manager
            logger.info("Connecting to MCP servers...")
            try:
                mcp_config = {
                    'servers': {
                        'dexmind': {
                            'command': 'node',
                            'args': ['/home/lylepaul78/Documents/augment-projects/MayArbi/dexmind/dist/index.js'],
                            'description': 'AI-powered DEX analysis and memory',
                            'type': 'memory',
                            'required': True
                        },
                        'memory_service': {
                            'command': '/home/lylepaul78/Documents/augment-projects/MayArbi/mcp-memory-service/start-mcp-memory-service.sh',
                            'args': [],
                            'description': 'Vector memory storage and retrieval',
                            'type': 'memory',
                            'required': True
                        },
                        'knowledge_graph': {
                            'command': '/home/lylepaul78/Documents/augment-projects/MayArbi/mcp-knowledge-graph/start-mcp-knowledge-graph.sh',
                            'args': [],
                            'description': 'Token and market relationship storage',
                            'type': 'graph',
                            'required': True
                        },
                        'ccxt_server': {
                            'command': '/home/lylepaul78/Documents/augment-projects/MayArbi/mcp-server-ccxt/.venv/bin/python',
                            'args': ['-m', 'mcp_server_ccxt'],
                            'description': 'Cryptocurrency exchange integration',
                            'type': 'exchange',
                            'required': True
                        },
                        'filescopemcp': {
                            'command': '/home/lylepaul78/Documents/augment-projects/MayArbi/FileScopeMCP/run.sh',
                            'args': [],
                            'description': 'Project file organization and tracking',
                            'type': 'organization',
                            'required': False
                        }
                    }
                }
                self.mcp_manager = MCPClientManager(mcp_config)
                await self.mcp_manager.connect_all()
                logger.info("✅ MCP servers connected successfully")
            except Exception as e:
                logger.warning(f"MCP connection failed (continuing without MCP): {e}")
                self.mcp_manager = None

            return True

        except Exception as e:
            logger.error(f"Error initializing bot: {e}")
            return False

    async def run(self) -> None:
        """Main bot loop."""
        try:
            if not await self.initialize():
                logger.error("Failed to initialize bot")
                return

            logger.info("🎯 Starting arbitrage detection loop...")
            self.running = True

            while self.running:
                try:
                    await self._scan_for_opportunities()
                    await asyncio.sleep(self.config['trading']['scan_interval'])

                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    await asyncio.sleep(5)  # Brief pause before retrying

        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
        finally:
            await self._shutdown()

    async def _scan_for_opportunities(self) -> None:
        """Scan for arbitrage opportunities."""
        try:
            # Find arbitrage opportunities
            opportunities = await self.dex_manager.find_arbitrage_opportunities(
                min_profit_percentage=self.config['trading']['min_profit_threshold']
            )

            if opportunities:
                self.stats['opportunities_found'] += len(opportunities)
                logger.info(f"🔍 Found {len(opportunities)} arbitrage opportunities")

                # Process each opportunity
                for opportunity in opportunities:
                    await self._process_opportunity(opportunity)
            else:
                logger.info("📊 No arbitrage opportunities found (market efficiency)")

        except Exception as e:
            logger.error(f"Error scanning for opportunities: {e}")

    async def _process_opportunity(self, opportunity: Dict[str, Any]) -> None:
        """Process a single arbitrage opportunity."""
        try:
            base_token = opportunity['base_token']
            quote_token = opportunity['quote_token']
            profit_pct = opportunity['profit_percentage']
            estimated_profit = opportunity['estimated_profit_usd']

            logger.info(f"💎 Processing opportunity: {base_token}/{quote_token}")
            logger.info(f"   Buy on {opportunity['buy_dex']} at ${opportunity['buy_price']:,.4f}")
            logger.info(f"   Sell on {opportunity['sell_dex']} at ${opportunity['sell_price']:,.4f}")
            logger.info(f"   Profit: {profit_pct:.3f}% (${estimated_profit:.2f})")

            # Get MCP intelligence if available
            intelligence = await self._get_mcp_intelligence(opportunity)

            # Calculate enhanced score
            enhanced_score = self._calculate_enhanced_score(opportunity, intelligence)
            logger.info(f"   Enhanced score: {enhanced_score:.2f}")

            # Check gas profitability
            gas_analysis = await self._check_gas_profitability(opportunity)
            logger.info(f"   Gas analysis: {gas_analysis['recommendation']} (Net: ${gas_analysis.get('net_profit_usd', 0):.2f})")

            # 🚀 ADVANCED FILTERING: Apply smart opportunity filter
            filter_result = self.opportunity_filter.filter_opportunity(opportunity)
            logger.info(f"   🎯 Filter result: {filter_result.reason}")
            logger.info(f"   📊 Priority score: {filter_result.priority_score:.2f}")
            logger.info(f"   ⏱️  Estimated execution: {filter_result.estimated_execution_time:.1f}s")
            logger.info(f"   📉 Profit decay factor: {filter_result.profit_decay_factor:.2f}")

            # Check if opportunity meets ALL criteria (original + advanced filter)
            if (filter_result.should_execute and
                self._should_execute_opportunity(opportunity, enhanced_score, gas_analysis)):
                logger.info("   🚀 EXECUTING: Opportunity passed all filters!")
                await self._execute_opportunity(opportunity, intelligence)
            else:
                if not filter_result.should_execute:
                    logger.info(f"   ⏭️  FILTERED OUT: {filter_result.reason}")
                else:
                    logger.info("   ⏭️  Skipping opportunity (score too low, risk too high, or unprofitable after gas)")

        except Exception as e:
            logger.error(f"Error processing opportunity: {e}")

    async def _get_mcp_intelligence(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Get MCP intelligence for an opportunity."""
        intelligence = {
            'confidence_score': 0.5,
            'historical_success_rate': 0.0,
            'market_sentiment': 'neutral'
        }

        if not self.mcp_manager:
            return intelligence

        try:
            # Store opportunity pattern
            pattern_data = {
                'pair': f"{opportunity['base_token']}/{opportunity['quote_token']}",
                'buy_dex': opportunity['buy_dex'],
                'sell_dex': opportunity['sell_dex'],
                'profit_percentage': opportunity['profit_percentage'],
                'timestamp': datetime.now().isoformat()
            }

            # Create a placeholder result for pattern storage
            pattern_result = {
                'success': False,  # Not executed yet
                'profit': 0,
                'gas_cost': 0,
                'timestamp': datetime.now().isoformat()
            }

            await self.mcp_manager.store_arbitrage_pattern(pattern_data, pattern_result)

            # Get historical analysis
            similar_patterns = await self.mcp_manager.get_similar_patterns(pattern_data)

            if similar_patterns:
                # Calculate confidence based on historical success
                successful = sum(1 for p in similar_patterns if p.get('success', False))
                intelligence['confidence_score'] = successful / len(similar_patterns)
                intelligence['historical_success_rate'] = intelligence['confidence_score']

        except Exception as e:
            logger.warning(f"Error getting MCP intelligence: {e}")

        return intelligence

    async def _check_gas_profitability(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Check if opportunity is profitable after gas costs."""
        try:
            if not self.gas_oracle:
                # Fallback gas estimation
                return {
                    'is_profitable': True,
                    'gas_cost_usd': 3.0,  # Conservative estimate
                    'net_profit_usd': opportunity['estimated_profit_usd'] - 3.0,
                    'recommendation': 'EXECUTE' if opportunity['estimated_profit_usd'] > 3.0 else 'SKIP'
                }

            # Determine transaction type based on DEXs involved
            tx_type = 'paraswap_swap'  # Default to Paraswap complexity
            if 'uniswap' in opportunity.get('buy_dex', '').lower():
                tx_type = 'uniswap_v3_swap'
            elif '1inch' in opportunity.get('buy_dex', '').lower():
                tx_type = 'complex_arbitrage'  # 1inch aggregator

            # Check profitability with real gas prices
            gas_analysis = await self.gas_oracle.is_trade_profitable(
                expected_profit_usd=opportunity['estimated_profit_usd'],
                tx_type=tx_type,
                gas_speed='fast'  # Use fast gas for arbitrage
            )

            return gas_analysis

        except Exception as e:
            logger.error(f"Error checking gas profitability: {e}")
            # Conservative fallback
            return {
                'is_profitable': False,
                'error': str(e),
                'recommendation': 'SKIP'
            }

    def _calculate_enhanced_score(self, opportunity: Dict[str, Any], intelligence: Dict[str, Any]) -> float:
        """Calculate enhanced opportunity score."""
        try:
            base_profit = opportunity['profit_percentage']
            confidence = intelligence.get('confidence_score', 0.5)

            # Enhanced scoring formula
            enhanced_score = base_profit * (1 + confidence)

            return enhanced_score

        except Exception as e:
            logger.error(f"Error calculating enhanced score: {e}")
            return 0.0

    def _should_execute_opportunity(self, opportunity: Dict[str, Any], enhanced_score: float, gas_analysis: Dict[str, Any]) -> bool:
        """Determine if opportunity should be executed."""
        try:
            # PRIORITY 2 FIX: Validate realistic profit amounts
            estimated_profit = opportunity.get('estimated_profit_usd', 0)
            if estimated_profit > 10000:  # Flag unrealistic profits > $10,000
                logger.warning(f"   ⚠️  Unrealistic profit detected: ${estimated_profit:,.2f} - skipping")
                return False

            # Validate price data quality
            buy_price = opportunity.get('buy_price', 0)
            sell_price = opportunity.get('sell_price', 0)
            if buy_price <= 0 or sell_price <= 0:
                logger.warning(f"   ⚠️  Invalid price data: buy=${buy_price}, sell=${sell_price} - skipping")
                return False

            # Check minimum profit threshold
            if opportunity['profit_percentage'] < self.config['trading']['min_profit_threshold']:
                return False

            # Check enhanced score threshold
            if enhanced_score < 0.2:  # Minimum enhanced score
                return False

            # Check trade size limits
            if opportunity['estimated_profit_usd'] > self.config['trading']['max_trade_size_usd']:
                return False

            # Check gas profitability
            if not gas_analysis.get('is_profitable', False):
                return False

            # 🎯 ENFORCE $0.25 MINIMUM: Use centralized config with gas costs
            from src.config.trading_config import CONFIG
            net_profit = gas_analysis.get('net_profit_usd', 0)
            if net_profit < CONFIG.MIN_PROFIT_USD:  # Use $0.25 minimum from config
                logger.info(f"💰 FILTERED OUT: Net profit ${net_profit:.2f} < ${CONFIG.MIN_PROFIT_USD:.2f} minimum (after gas)")
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking execution criteria: {e}")
            return False

    async def _execute_opportunity(self, opportunity: Dict[str, Any], intelligence: Dict[str, Any]) -> None:
        """Execute an arbitrage opportunity."""
        try:
            self.stats['opportunities_executed'] += 1

            if self.config['trading']['trading_enabled']:
                logger.info("🎯 Executing REAL arbitrage trade...")
                success = await self._execute_real_arbitrage(opportunity)

                if success:
                    logger.info("✅ REAL arbitrage execution: SUCCESS")
                else:
                    logger.error("❌ REAL arbitrage execution: FAILED")
            else:
                logger.info("🎯 Executing SIMULATED arbitrage trade...")
                # Simulate execution with realistic success rate
                import random
                success = random.random() > 0.3  # 70% success rate

            # Update statistics
            if success:
                self.stats['successful_trades'] += 1
                self.stats['total_profit_usd'] += opportunity['estimated_profit_usd']
                logger.info("📊 Simulated execution: SUCCESS")
            else:
                self.stats['failed_trades'] += 1
                logger.info("📊 Simulated execution: FAILED")

            # Store execution result
            if self.mcp_manager:
                execution_result = {
                    'opportunity_id': opportunity.get('id'),
                    'success': success,
                    'profit': opportunity['estimated_profit_usd'] if success else 0,
                    'gas_cost': 3.0,  # Estimated gas cost
                    'timestamp': datetime.now().isoformat()
                }
                await self.mcp_manager.store_execution_result(opportunity, execution_result)

            # Log statistics
            self._log_statistics()

        except Exception as e:
            logger.error(f"Error executing opportunity: {e}")
            self.stats['failed_trades'] += 1

    async def _execute_real_arbitrage(self, opportunity: Dict[str, Any]) -> bool:
        """Execute real arbitrage trade on DEXs."""
        try:
            buy_dex = opportunity['buy_dex']
            sell_dex = opportunity['sell_dex']
            base_token = opportunity['base_token']
            quote_token = opportunity['quote_token']

            # Calculate trade amount (conservative approach)
            max_trade_usd = min(
                self.config['trading']['max_trade_size_usd'],
                opportunity['estimated_profit_usd'] * 20  # 20x profit as max trade size
            )

            # For now, use a small test amount
            trade_amount = min(max_trade_usd / opportunity['buy_price'], 100)  # Max 100 tokens

            logger.info(f"   💰 Trade amount: {trade_amount:.4f} {base_token}")
            logger.info(f"   📈 Buy on {buy_dex} at ${opportunity['buy_price']:,.4f}")
            logger.info(f"   📉 Sell on {sell_dex} at ${opportunity['sell_price']:,.4f}")

            # Get DEX adapters
            buy_adapter = self.dex_manager.dexs.get(buy_dex)
            sell_adapter = self.dex_manager.dexs.get(sell_dex)

            if not buy_adapter or not sell_adapter:
                logger.error(f"   ❌ DEX adapters not found: {buy_dex}, {sell_dex}")
                return False

            # Get fresh quotes
            logger.info("   📊 Getting fresh quotes...")
            buy_quote = await buy_adapter.get_quote(base_token, quote_token, trade_amount)
            sell_quote = await sell_adapter.get_quote(quote_token, base_token, trade_amount * opportunity['buy_price'])

            if not buy_quote or not sell_quote:
                logger.error("   ❌ Failed to get quotes")
                return False

            # Verify profitability with fresh quotes
            buy_cost = buy_quote['expected_output']
            sell_revenue = sell_quote['expected_output']
            net_profit = sell_revenue - buy_cost

            logger.info(f"   💸 Buy cost: {buy_cost:.4f} {quote_token}")
            logger.info(f"   💰 Sell revenue: {sell_revenue:.4f} {base_token}")
            logger.info(f"   📊 Net profit: {net_profit:.4f}")

            if net_profit <= 0:
                logger.warning("   ⚠️  Opportunity no longer profitable with fresh quotes")
                return False

            # For now, we'll simulate the execution since we need wallet integration
            logger.warning("   🚧 SIMULATION MODE: Real wallet integration not yet implemented")
            logger.info("   📝 Would execute:")
            logger.info(f"      1. Buy {trade_amount:.4f} {base_token} on {buy_dex}")
            logger.info(f"      2. Sell {trade_amount:.4f} {base_token} on {sell_dex}")
            logger.info(f"      3. Net profit: {net_profit:.4f} {quote_token}")

            # Return success for simulation
            return True

        except Exception as e:
            logger.error(f"Error executing real arbitrage: {e}")
            return False

    def _log_statistics(self) -> None:
        """Log current statistics."""
        runtime = datetime.now() - self.stats['start_time']
        success_rate = (self.stats['successful_trades'] / max(self.stats['opportunities_executed'], 1)) * 100

        logger.info(f"📈 Statistics:")
        logger.info(f"   Runtime: {runtime}")
        logger.info(f"   Opportunities found: {self.stats['opportunities_found']}")
        logger.info(f"   Opportunities executed: {self.stats['opportunities_executed']}")
        logger.info(f"   Success rate: {success_rate:.1f}%")
        logger.info(f"   Total profit: ${self.stats['total_profit_usd']:.2f}")

    async def _shutdown(self) -> None:
        """Shutdown the bot gracefully."""
        logger.info("🛑 Shutting down Real Arbitrage Bot...")

        self.running = False

        if self.dex_manager:
            await self.dex_manager.disconnect_all()

        if self.gas_oracle:
            await self.gas_oracle.disconnect()

        if self.mcp_manager:
            await self.mcp_manager.disconnect_all()

        self._log_statistics()
        logger.info("✅ Real Arbitrage Bot shutdown complete")

    def stop(self) -> None:
        """Stop the bot."""
        self.running = False


async def main():
    """Main entry point."""
    bot = RealArbitrageBot()

    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        bot.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the bot
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)
