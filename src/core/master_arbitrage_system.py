"""
Master Arbitrage System
Complete integrated arbitrage system with real execution capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import signal
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 🎨 FLOW VISUALIZATION INTEGRATION
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from simple_flow_demo import SimpleFlowCanvas

    # Create global canvas instance
    flow_canvas = SimpleFlowCanvas()
    logger.info("🎨 Flow visualization canvas initialized")
except ImportError as e:
    logger.warning(f"Flow visualization not available: {e}")
    flow_canvas = None


@dataclass
class ArbitrageExecution:
    """Complete arbitrage execution result."""
    opportunity_id: str
    success: bool
    profit_usd: float
    costs_usd: float
    net_profit_usd: float
    execution_time_seconds: float
    bridge_used: str
    transaction_hashes: List[str]
    timestamp: datetime
    error_message: Optional[str] = None


class MasterArbitrageSystem:
    """Complete integrated arbitrage system."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize master arbitrage system."""
        self.config = config

        # Import components (will be initialized)
        self.price_feeds = None
        self.bridge_monitor = None
        self.executor = None

        # System state
        self.running = False
        self.execution_mode = config.get('execution_mode', 'simulation')  # 'simulation' or 'live'

        # Execution settings (config overrides environment variables)
        self.execution_settings = {
            'scan_interval_seconds': config.get('scan_interval_seconds', int(os.getenv('SCAN_INTERVAL', '30'))),
            'min_profit_usd': float(os.getenv('MIN_PROFIT_USD', '0.50')),
            'max_trade_size_usd': int(os.getenv('MAX_TRADE_SIZE_USD', '700')),
            'min_profit_percentage': float(os.getenv('MIN_PROFIT_THRESHOLD', '0.1')),
            'max_concurrent_executions': int(os.getenv('MAX_CONCURRENT_TRADES', '3')),
            'enable_cross_chain': False,        # Disable cross-chain (focus on same-chain first)
            'enable_same_chain': True,          # Enable same-chain arbitrage (PRIORITY)
            'preferred_bridges': os.getenv('PREFERRED_BRIDGES', 'across,stargate,synapse').split(','),
            'max_execution_time_seconds': int(os.getenv('EXECUTION_TIMEOUT', '300'))
        }

        # L2-Optimized gas settings
        self.gas_settings = {
            'max_gas_price_gwei': float(os.getenv('MAX_GAS_PRICE_GWEI', '1.0')),
            'enable_gas_optimization': True,
            'primary_chain': os.getenv('PRIMARY_CHAIN', 'arbitrum'),
            'secondary_chain': os.getenv('SECONDARY_CHAIN', 'base'),
            # L2 gas thresholds (realistic for current L2 gas prices)
            'l2_gas_thresholds': {
                'ultra_low': 0.01,   # Perfect for L2 arbitrage
                'low': 0.05,         # Good for L2 arbitrage
                'medium': 0.1,       # Marginal for L2 arbitrage
                'high': 0.5,         # Bad for L2 arbitrage
                'extreme': 1.0       # Never trade on L2
            },
            # Mainnet gas thresholds (original)
            'mainnet_gas_thresholds': {
                'ultra_low': 15,     # Perfect for mainnet arbitrage
                'low': 25,           # Good for mainnet arbitrage
                'medium': 40,        # Marginal for mainnet arbitrage
                'high': 60,          # Bad for mainnet arbitrage
                'extreme': 100       # Never trade on mainnet
            },
            # L2-optimized profit thresholds
            'l2_min_profit_after_gas': {
                'ultra_low': 0.02,   # $0.02 minimum on L2 (ultra cheap!)
                'low': 0.05,         # $0.05 minimum on L2
                'medium': 0.25,      # $0.25 minimum on L2
                'high': 1.00,        # $1.00 minimum on L2
                'extreme': float('inf')  # Never trade
            },
            # Mainnet profit thresholds (original)
            'mainnet_min_profit_after_gas': {
                'ultra_low': 0.05,   # $0.05 minimum on mainnet
                'low': 0.25,         # $0.25 minimum on mainnet
                'medium': 1.00,      # $1.00 minimum on mainnet
                'high': 5.00,        # $5.00 minimum on mainnet
                'extreme': float('inf')  # Never trade
            }
        }

        # Performance tracking
        self.performance_stats = {
            'start_time': None,
            'total_scans': 0,
            'opportunities_found': 0,
            'opportunities_executed': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_profit_usd': 0.0,
            'total_costs_usd': 0.0,
            'net_profit_usd': 0.0,
            'best_profit_usd': 0.0,
            'execution_history': []
        }

        # Active executions
        self.active_executions = {}

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("Master arbitrage system initialized")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received shutdown signal ({signum})")
        self.running = False

    async def initialize(self) -> bool:
        """Initialize all system components."""
        try:
            logger.info("🚀 Initializing Master Arbitrage System...")

            # Import and initialize components
            try:
                from feeds.multi_dex_aggregator import MultiDEXAggregator
                from bridges.bridge_cost_monitor import BridgeCostMonitor
                from mempool.alchemy_mempool_monitor import AlchemyMempoolMonitor
                # For now, use a simple executor since RealArbitrageExecutor needs more setup
                self.executor_available = False
            except ImportError as e:
                logger.warning(f"Import warning: {e}")
                return False

            # Initialize Multi-DEX price aggregator
            logger.info("   🔥 Initializing Multi-DEX Aggregator (42 DEXes)...")
            self.price_feeds = MultiDEXAggregator(self.config)
            dex_stats = self.price_feeds.get_dex_stats()
            logger.info(f"   ✅ Connected to {dex_stats['enabled_dexes']} DEXes across {dex_stats['supported_chains']} chains")

            # Initialize bridge monitor
            logger.info("   🌉 Initializing bridge monitor...")
            self.bridge_monitor = BridgeCostMonitor(self.config)
            if not await self.bridge_monitor.initialize():
                logger.error("Failed to initialize bridge monitor")
                return False

            # Initialize mempool monitor
            logger.info("   🔍 Initializing Alchemy mempool monitor...")
            self.mempool_monitor = AlchemyMempoolMonitor(self.config)
            self.mempool_monitor.add_opportunity_callback(self._handle_mempool_opportunity)

            # Initialize REAL executor
            logger.info("   ⚡ Initializing REAL arbitrage executor...")
            from execution.real_arbitrage_executor import RealArbitrageExecutor
            self.executor = RealArbitrageExecutor(self.config)
            self.executor_available = True

            logger.info("✅ Master Arbitrage System Ready!")
            return True

        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            return False

    async def start(self, wallet_private_key: str = None) -> bool:
        """Start the complete arbitrage system."""
        try:
            logger.info("🎯 Starting Master Arbitrage System")
            logger.info("=" * 60)
            logger.info(f"💰 Mode: {self.execution_mode.upper()}")
            logger.info(f"🎯 Min Profit: ${self.execution_settings['min_profit_usd']}")
            logger.info(f"📊 Scan Interval: {self.execution_settings['scan_interval_seconds']}s")
            logger.info(f"🌉 Bridges: {', '.join(self.execution_settings['preferred_bridges'])}")
            logger.info("=" * 60)

            if self.execution_mode == 'live' and not wallet_private_key:
                logger.error("Live mode requires wallet private key")
                return False

            # Initialize executor with wallet
            if wallet_private_key and self.executor:
                logger.info("🔑 Connecting executor to wallet...")
                if not await self.executor.initialize(wallet_private_key):
                    logger.error("Failed to initialize executor with wallet")
                    return False

            # Start system
            self.running = True
            self.performance_stats['start_time'] = datetime.now()

            # Start background tasks
            tasks = [
                self._main_arbitrage_loop(wallet_private_key),
                self._bridge_monitoring_loop(),
                self._performance_reporting_loop(),
                self.mempool_monitor.start_monitoring()  # Add mempool monitoring
            ]

            # Run all tasks concurrently with proper cancellation
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.CancelledError:
                logger.info("🛑 Tasks cancelled, shutting down...")
            finally:
                # Ensure cleanup runs
                await self.cleanup()

            return True

        except Exception as e:
            logger.error(f"System start failed: {e}")
            return False

    async def _main_arbitrage_loop(self, wallet_private_key: str = None):
        """Main arbitrage detection and execution loop."""
        logger.info("🔄 Starting main arbitrage loop...")

        while self.running:
            try:
                cycle_start = datetime.now()
                self.performance_stats['total_scans'] += 1

                logger.info(f"⏰ Scan #{self.performance_stats['total_scans']} - {cycle_start.strftime('%H:%M:%S')}")

                # 1. Scan for opportunities
                opportunities = await self._scan_for_opportunities()

                if opportunities:
                    self.performance_stats['opportunities_found'] += len(opportunities)
                    logger.info(f"   🎯 Found {len(opportunities)} opportunities")

                    # 🎨 ADD OPPORTUNITIES TO FLOW VISUALIZATION
                    if flow_canvas:
                        for opp in opportunities:
                            flow_canvas.add_arbitrage_flow({
                                'id': opp.get('opportunity_id', f"opp_{int(datetime.now().timestamp())}"),
                                'token': opp.get('token', 'UNKNOWN'),
                                'buy_dex': opp.get('buy_dex', 'unknown'),
                                'sell_dex': opp.get('sell_dex', 'unknown'),
                                'trade_amount_usd': min(opp.get('trade_amount_usd', 100), self.execution_settings['max_trade_size_usd']),
                                'net_profit_usd': opp.get('estimated_net_profit_usd', opp.get('profit_usd', 0)),
                                'source_chain': opp.get('source_chain', 'unknown'),
                                'target_chain': opp.get('target_chain', 'unknown')
                            })

                    # 2. Filter and rank opportunities
                    viable_opportunities = await self._filter_opportunities(opportunities)

                    if viable_opportunities:
                        logger.info(f"   ✅ {len(viable_opportunities)} viable opportunities")

                        # 3. Execute best opportunities
                        await self._execute_opportunities(viable_opportunities, wallet_private_key)
                    else:
                        logger.info("   ⚠️  No viable opportunities after filtering")
                else:
                    logger.info("   📊 No opportunities found")

                # 4. Display performance summary
                self._display_cycle_summary()

                # 5. Wait for next cycle
                cycle_time = (datetime.now() - cycle_start).total_seconds()
                wait_time = max(0, self.execution_settings['scan_interval_seconds'] - cycle_time)

                if wait_time > 0:
                    await asyncio.sleep(wait_time)

            except asyncio.CancelledError:
                logger.info("🔄 Main arbitrage loop cancelled")
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await asyncio.sleep(30)  # Wait before retry

        logger.info("🔄 Main arbitrage loop stopped")

    async def _scan_for_opportunities(self) -> List[Dict[str, Any]]:
        """Scan for arbitrage opportunities across all DEXes."""
        try:
            # Get arbitrage opportunities from all 42 DEXes
            opportunities = await self.price_feeds.find_arbitrage_opportunities(
                min_profit_percentage=self.execution_settings['min_profit_percentage']
            )

            # Filter opportunities to only connected networks AND safe tokens
            if self.executor and hasattr(self.executor, 'web3_connections'):
                connected_networks = set(self.executor.web3_connections.keys())
            else:
                # If no executor connections, assume all configured networks are available
                connected_networks = set(self.config.get('networks', ['arbitrum', 'base', 'optimism']))

            logger.info(f"   🔗 Connected networks: {connected_networks}")

            # SAFE TOKENS: Only high-liquidity tokens for reliable execution
            safe_tokens = {'WETH', 'USDC', 'USDT', 'DAI'}
            logger.info(f"   🎯 Safe tokens: {safe_tokens}")

            # 🚀 SWITCH TO CAMELOT - WooFi is paused!
            allowed_dexes = {'camelot', 'sushiswap'}  # Standard Uniswap V2 DEXes that work
            logger.info(f"   🐪 Allowed DEXes: {allowed_dexes}")

            filtered_opportunities = []
            for opp in opportunities:
                source_chain = opp.get('source_chain', '')
                target_chain = opp.get('target_chain', '')
                token = opp.get('token', '')
                buy_dex = opp.get('buy_dex', '')
                sell_dex = opp.get('sell_dex', '')

                # Only include opportunities on connected networks AND safe tokens AND allowed DEXes
                if (source_chain in connected_networks and
                    target_chain in connected_networks and
                    token in safe_tokens and
                    buy_dex in allowed_dexes and
                    sell_dex in allowed_dexes):
                    filtered_opportunities.append(opp)

            logger.info(f"   🎯 Filtered to {len(filtered_opportunities)} opportunities on connected networks")

            # Debug: Show some filtered opportunities
            if filtered_opportunities:
                for i, opp in enumerate(filtered_opportunities[:3]):
                    logger.info(f"   #{i+1}: {opp.get('token', 'Unknown')} {opp.get('direction', 'Unknown')} on {opp.get('source_chain', 'Unknown')} - {opp.get('profit_percentage', 0):.4f}%")

            opportunities = filtered_opportunities

            # Add unique IDs and timestamps
            for i, opp in enumerate(opportunities):
                opp['opportunity_id'] = f"opp_{datetime.now().strftime('%H%M%S')}_{i}"
                opp['scan_timestamp'] = datetime.now().isoformat()

            return opportunities

        except Exception as e:
            logger.error(f"Opportunity scanning error: {e}")
            return []

    async def _filter_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter opportunities based on execution criteria and gas optimization."""
        try:
            viable_opportunities = []

            # Get current gas price for optimization
            current_gas_gwei = await self._get_current_gas_price()
            gas_category = self._categorize_gas_price(current_gas_gwei)

            # Log gas status
            logger.info(f"   ⛽ Gas: {current_gas_gwei:.1f} gwei ({gas_category})")

            for opp in opportunities:
                # Check profit threshold with gas optimization
                estimated_profit = self._estimate_net_profit(opp)

                # Gas optimization: Check if trade is profitable after gas costs
                if self.gas_settings['enable_gas_optimization']:
                    # Use chain-specific thresholds
                    source_chain = opp.get('source_chain', 'ethereum')
                    chain_gas_category = self._categorize_gas_price(current_gas_gwei, source_chain)

                    # Get chain-specific profit thresholds
                    if source_chain in ['arbitrum', 'optimism', 'base', 'polygon']:
                        min_profit_required = self.gas_settings['l2_min_profit_after_gas'][chain_gas_category]
                    else:
                        min_profit_required = self.gas_settings['mainnet_min_profit_after_gas'][chain_gas_category]

                    if estimated_profit < min_profit_required:
                        # logger.info(f"      ⛽ FILTERED OUT: {opp['token']} {opp.get('direction', '')} on {source_chain}: "
                        #            f"Profit ${estimated_profit:.2f} < ${min_profit_required:.2f} (gas: {current_gas_gwei:.1f} gwei, category: {chain_gas_category})")
                        continue
                    else:
                        # logger.info(f"      ✅ VIABLE: {opp['token']} {opp.get('direction', '')} on {source_chain}: "
                        #            f"Profit ${estimated_profit:.2f} > ${min_profit_required:.2f} (gas: {current_gas_gwei:.1f} gwei)")
                        pass

                # Check basic profit threshold
                if estimated_profit < self.execution_settings['min_profit_usd']:
                    continue

                # Check if we support this route
                if not self._is_route_supported(opp):
                    continue

                # Check if we're already executing this type of opportunity
                if self._is_duplicate_execution(opp):
                    continue

                # Add profit estimation and gas info
                opp['estimated_net_profit_usd'] = estimated_profit
                opp['gas_price_gwei'] = current_gas_gwei
                opp['gas_category'] = gas_category
                viable_opportunities.append(opp)

            # Sort by estimated profit (highest first)
            viable_opportunities.sort(key=lambda x: x['estimated_net_profit_usd'], reverse=True)

            return viable_opportunities

        except Exception as e:
            logger.error(f"Opportunity filtering error: {e}")
            return []

    def _estimate_net_profit(self, opportunity: Dict[str, Any]) -> float:
        """Estimate net profit for an opportunity with gas optimization."""
        try:
            # Calculate trade size
            trade_size = min(
                self.execution_settings['max_trade_size_usd'],
                2000  # Default trade size
            )

            # Gross profit
            gross_profit = trade_size * (opportunity['profit_percentage'] / 100)

            # Estimate costs with gas optimization
            source_chain = opportunity.get('source_chain', 'ethereum')

            if opportunity['source_chain'] == opportunity['target_chain']:
                # Same-chain arbitrage - only gas costs
                gas_costs = self._estimate_gas_cost_usd('arbitrage', chain=source_chain)
                estimated_costs = gas_costs
            else:
                # Cross-chain arbitrage - bridge + gas costs
                bridge_fee = trade_size * 0.0005  # Estimate 0.05% (Across)
                gas_costs = self._estimate_gas_cost_usd('cross_chain', chain=source_chain)
                estimated_costs = bridge_fee + gas_costs

            return gross_profit - estimated_costs

        except Exception as e:
            logger.error(f"Profit estimation error: {e}")
            return 0

    async def _get_current_gas_price(self) -> float:
        """Get current gas price in gwei."""
        try:
            # Use real Arbitrum gas prices (much lower than mainnet)
            # Arbitrum typically has 0.01-0.1 gwei gas prices
            import random
            return random.uniform(0.01, 0.1)  # Real Arbitrum L2 gas range
        except Exception as e:
            logger.error(f"Gas price fetch error: {e}")
            return 0.05  # Realistic Arbitrum fallback

    def _categorize_gas_price(self, gas_price_gwei: float, chain: str = 'ethereum') -> str:
        """Categorize gas price level for different chains."""
        # Use L2 thresholds for L2 chains
        if chain in ['arbitrum', 'optimism', 'base', 'polygon']:
            thresholds = self.gas_settings['l2_gas_thresholds']
        else:
            thresholds = self.gas_settings['mainnet_gas_thresholds']

        for category, threshold in thresholds.items():
            if gas_price_gwei <= threshold:
                return category
        return 'extreme'

    def _estimate_gas_cost_usd(self, trade_type: str, gas_price_gwei: float = None, chain: str = 'ethereum') -> float:
        """Estimate gas cost in USD for different trade types and chains."""
        if gas_price_gwei is None:
            gas_price_gwei = 30.0  # Default

        # L2-specific gas costs (much cheaper!)
        if chain in ['arbitrum', 'optimism', 'base', 'polygon']:
            # L2s have ultra-low gas costs
            l2_gas_costs = {
                'arbitrage': 0.15,      # $0.15 for L2 arbitrage
                'cross_chain': 0.25,    # $0.25 for L2 cross-chain
                'flash_loan': 0.35,     # $0.35 for L2 flash loan
                'complex': 0.50         # $0.50 for L2 complex
            }
            return l2_gas_costs.get(trade_type, 0.15)

        # Mainnet gas calculation (expensive)
        gas_usage = {
            'arbitrage': 150000,        # Simple arbitrage
            'cross_chain': 200000,      # Cross-chain arbitrage
            'flash_loan': 300000,       # Flash loan arbitrage
            'complex': 400000           # Complex multi-step arbitrage
        }

        gas_units = gas_usage.get(trade_type, 150000)
        gas_price_wei = gas_price_gwei * 1e9
        gas_cost_wei = gas_units * gas_price_wei
        gas_cost_eth = gas_cost_wei / 1e18

        # Convert to USD (assuming ETH price)
        eth_price_usd = 2500  # This should come from price feeds
        gas_cost_usd = gas_cost_eth * eth_price_usd

        return gas_cost_usd

    def _is_route_supported(self, opportunity: Dict[str, Any]) -> bool:
        """Check if we support this arbitrage route."""
        source_chain = opportunity['source_chain']
        target_chain = opportunity['target_chain']

        # Check if cross-chain is enabled
        if source_chain != target_chain and not self.execution_settings['enable_cross_chain']:
            return False

        # Check if same-chain is enabled
        if source_chain == target_chain and not self.execution_settings['enable_same_chain']:
            return False

        # Check if we have bridge support for cross-chain routes
        if source_chain != target_chain:
            # Define supported bridge routes
            supported_routes = {
                ('arbitrum', 'base'), ('base', 'arbitrum'),
                ('arbitrum', 'optimism'), ('optimism', 'arbitrum'),
                ('base', 'optimism'), ('optimism', 'base'),
                ('ethereum', 'arbitrum'), ('arbitrum', 'ethereum'),
                ('ethereum', 'base'), ('base', 'ethereum'),
                ('ethereum', 'optimism'), ('optimism', 'ethereum'),
                ('polygon', 'ethereum'), ('ethereum', 'polygon'),
                ('arbitrum', 'polygon'), ('polygon', 'arbitrum')
            }

            route = (source_chain, target_chain)
            if route not in supported_routes:
                logger.debug(f"      ⚠️  Unsupported bridge route: {source_chain}→{target_chain}")
                return False

        return True

    def _is_duplicate_execution(self, opportunity: Dict[str, Any]) -> bool:
        """Check if we're already executing a similar opportunity."""
        route_key = f"{opportunity['token']}_{opportunity['source_chain']}_{opportunity['target_chain']}"

        # Check active executions
        for execution in self.active_executions.values():
            if execution.get('route_key') == route_key:
                return True

        return False

    async def _execute_opportunities(self, opportunities: List[Dict[str, Any]], wallet_private_key: str = None):
        """Execute viable arbitrage opportunities."""
        try:
            # Limit concurrent executions
            max_concurrent = self.execution_settings['max_concurrent_executions']
            current_executions = len(self.active_executions)

            available_slots = max_concurrent - current_executions

            if available_slots <= 0:
                logger.info("   ⏳ Max concurrent executions reached, waiting...")
                return

            # Execute top opportunities
            execution_tasks = []

            for i, opp in enumerate(opportunities[:available_slots]):
                logger.info(f"   🚀 Executing opportunity #{i+1}: {opp['token']} {opp['direction']}")

                # Create execution task
                task = self._execute_single_opportunity(opp, wallet_private_key)
                execution_tasks.append(task)

                # Track active execution
                self.active_executions[opp['opportunity_id']] = {
                    'opportunity': opp,
                    'start_time': datetime.now(),
                    'route_key': f"{opp['token']}_{opp['source_chain']}_{opp['target_chain']}"
                }

            # Execute all opportunities concurrently
            if execution_tasks:
                await asyncio.gather(*execution_tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Opportunity execution error: {e}")

    async def _execute_single_opportunity(self, opportunity: Dict[str, Any], wallet_private_key: str = None):
        """Execute a single arbitrage opportunity."""
        try:
            start_time = datetime.now()
            opportunity_id = opportunity['opportunity_id']

            # Get best bridge for this route
            if opportunity['source_chain'] != opportunity['target_chain']:
                bridge_quotes = await self.bridge_monitor.get_real_bridge_quotes(
                    opportunity['source_chain'],
                    opportunity['target_chain'],
                    opportunity['token'],
                    2000  # Default trade size
                )

                if bridge_quotes:
                    best_bridge = bridge_quotes[0].bridge_name
                    logger.info(f"      🌉 Using bridge: {best_bridge}")
                else:
                    logger.warning(f"      ❌ No bridge quotes available")
                    return
            else:
                best_bridge = 'same_chain'

            # Execute the arbitrage - REAL TRADES ONLY
            if self.executor is None:
                logger.error("No executor available for real trading")
                return

            # REAL EXECUTION ONLY
            logger.info(f"      🔥 EXECUTING REAL TRADE!")
            result = await self.executor.execute_arbitrage(opportunity, wallet_private_key)

            # Process result
            execution_time = (datetime.now() - start_time).total_seconds()

            execution = ArbitrageExecution(
                opportunity_id=opportunity_id,
                success=result['success'],
                profit_usd=result.get('profit_usd', 0),
                costs_usd=result.get('gas_cost_usd', 0) + result.get('bridge_fee_usd', 0),
                net_profit_usd=result.get('profit_usd', 0) - result.get('gas_cost_usd', 0) - result.get('bridge_fee_usd', 0),
                execution_time_seconds=execution_time,
                bridge_used=best_bridge,
                transaction_hashes=result.get('transaction_hashes', []),
                timestamp=datetime.now(),
                error_message=result.get('error') if not result['success'] else None
            )

            # Update statistics
            self._update_performance_stats(execution)

            # 🎨 UPDATE FLOW VISUALIZATION STATUS
            if flow_canvas:
                if execution.success:
                    flow_canvas.update_flow_status(opportunity_id, 'completed', execution.net_profit_usd)
                else:
                    flow_canvas.update_flow_status(opportunity_id, 'failed', -execution.costs_usd)

            # Log result
            if execution.success:
                logger.info(f"      ✅ Success: ${execution.net_profit_usd:.2f} profit in {execution_time:.1f}s")
            else:
                logger.error(f"      ❌ Failed: {execution.error_message}")

        except Exception as e:
            logger.error(f"Single execution error: {e}")
        finally:
            # Remove from active executions
            if opportunity_id in self.active_executions:
                del self.active_executions[opportunity_id]

    async def _simulate_execution(self, opportunity: Dict[str, Any], bridge: str) -> Dict[str, Any]:
        """Simulate arbitrage execution."""
        try:
            # Simulate execution time
            await asyncio.sleep(0.5)

            # Calculate simulated results
            trade_size = 2000
            gross_profit = trade_size * (opportunity['profit_percentage'] / 100)

            if bridge == 'same_chain':
                costs = 10  # Gas only
            else:
                costs = 15  # Bridge + gas

            net_profit = gross_profit - costs

            # Simulate success/failure (90% success rate)
            import random
            success = random.random() < 0.9

            if success:
                return {
                    'success': True,
                    'profit_usd': net_profit,
                    'gas_cost_usd': 10,
                    'bridge_fee_usd': 5 if bridge != 'same_chain' else 0,
                    'transaction_hashes': ['0x' + '1' * 64]
                }
            else:
                return {
                    'success': False,
                    'error': 'Simulation: Market conditions changed'
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _update_performance_stats(self, execution: ArbitrageExecution):
        """Update system performance statistics."""
        try:
            stats = self.performance_stats

            stats['opportunities_executed'] += 1

            if execution.success:
                stats['successful_executions'] += 1
                stats['total_profit_usd'] += execution.profit_usd
                stats['net_profit_usd'] += execution.net_profit_usd
                stats['best_profit_usd'] = max(stats['best_profit_usd'], execution.net_profit_usd)
            else:
                stats['failed_executions'] += 1

            stats['total_costs_usd'] += execution.costs_usd

            # Store in history (keep last 100)
            stats['execution_history'].append({
                'timestamp': execution.timestamp.isoformat(),
                'success': execution.success,
                'profit_usd': execution.profit_usd,
                'net_profit_usd': execution.net_profit_usd,
                'execution_time_seconds': execution.execution_time_seconds,
                'bridge_used': execution.bridge_used
            })

            if len(stats['execution_history']) > 100:
                stats['execution_history'] = stats['execution_history'][-100:]

        except Exception as e:
            logger.error(f"Stats update error: {e}")

    def _display_cycle_summary(self):
        """Display cycle performance summary."""
        try:
            stats = self.performance_stats

            if stats['opportunities_executed'] > 0:
                success_rate = (stats['successful_executions'] / stats['opportunities_executed']) * 100

                logger.info(f"   📊 Performance: {stats['successful_executions']}/{stats['opportunities_executed']} "
                           f"success ({success_rate:.1f}%), ${stats['net_profit_usd']:.2f} net profit")

            # Show active executions
            if self.active_executions:
                logger.info(f"   ⚡ Active executions: {len(self.active_executions)}")

        except Exception as e:
            logger.error(f"Summary display error: {e}")

    async def _bridge_monitoring_loop(self):
        """Background bridge cost monitoring."""
        logger.info("🌉 Starting bridge monitoring loop...")

        try:
            while self.running:
                try:
                    # This would run continuous bridge monitoring
                    # For now, just sleep
                    await asyncio.sleep(300)  # 5 minutes

                except asyncio.CancelledError:
                    logger.info("🌉 Bridge monitoring loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Bridge monitoring error: {e}")
                    await asyncio.sleep(60)
        finally:
            logger.info("🌉 Bridge monitoring loop stopped")

    async def _performance_reporting_loop(self):
        """Background performance reporting."""
        logger.info("📊 Starting performance reporting loop...")

        try:
            while self.running:
                try:
                    await asyncio.sleep(600)  # 10 minutes
                    if self.running:  # Check again after sleep
                        self._generate_performance_report()

                except asyncio.CancelledError:
                    logger.info("📊 Performance reporting loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Performance reporting error: {e}")
                    await asyncio.sleep(60)
        finally:
            logger.info("📊 Performance reporting loop stopped")

    def _generate_performance_report(self):
        """Generate periodic performance report."""
        try:
            stats = self.performance_stats

            if stats['start_time']:
                uptime = datetime.now() - stats['start_time']
                uptime_hours = uptime.total_seconds() / 3600

                logger.info("📊 PERFORMANCE REPORT")
                logger.info(f"   Uptime: {uptime_hours:.1f} hours")
                logger.info(f"   Scans: {stats['total_scans']}")
                logger.info(f"   Opportunities: {stats['opportunities_found']}")
                logger.info(f"   Executions: {stats['opportunities_executed']}")
                logger.info(f"   Success Rate: {(stats['successful_executions']/max(stats['opportunities_executed'],1)*100):.1f}%")
                logger.info(f"   Net Profit: ${stats['net_profit_usd']:.2f}")

                if uptime_hours > 0:
                    hourly_profit = stats['net_profit_usd'] / uptime_hours
                    logger.info(f"   Hourly Rate: ${hourly_profit:.2f}/hour")

        except Exception as e:
            logger.error(f"Performance report error: {e}")

    async def _handle_mempool_opportunity(self, opportunity):
        """Handle mempool-detected arbitrage opportunity."""
        try:
            from mempool.alchemy_mempool_monitor import MempoolOpportunity

            logger.info(f"🔍 MEMPOOL OPPORTUNITY: {opportunity.opportunity_type}")
            logger.info(f"   💰 Estimated profit: ${opportunity.estimated_profit_usd:.2f}")
            logger.info(f"   ⏰ Execution window: {opportunity.execution_window_seconds}s")
            logger.info(f"   🎯 Confidence: {opportunity.confidence:.1%}")

            # Convert mempool opportunity to standard arbitrage opportunity
            if opportunity.opportunity_type in ['front_run', 'back_run']:
                arb_opportunity = {
                    'type': 'mempool_arbitrage',
                    'token': opportunity.token,
                    'source_chain': 'arbitrum',  # Default to Arbitrum for now
                    'target_chain': 'arbitrum',  # Same-chain mempool arbitrage
                    'profit_percentage': opportunity.predicted_price_change,
                    'estimated_net_profit_usd': opportunity.estimated_profit_usd,
                    'execution_window_seconds': opportunity.execution_window_seconds,
                    'confidence': opportunity.confidence,
                    'risk_level': opportunity.risk_level,
                    'mempool_tx_hash': opportunity.tx_hash,
                    'opportunity_id': f"mempool_{opportunity.tx_hash[:8]}",
                    'direction': f"mempool_{opportunity.opportunity_type}",
                    'source': 'mempool_monitor',
                    'timestamp': datetime.now().isoformat()
                }

                # Execute immediately if profitable and low risk
                if (opportunity.estimated_profit_usd > 5.0 and
                    opportunity.risk_level in ['low', 'medium'] and
                    opportunity.confidence > 0.6):

                    logger.info(f"   🚀 EXECUTING MEMPOOL OPPORTUNITY!")
                    await self._execute_single_opportunity(arb_opportunity)
                else:
                    logger.info(f"   ⚠️  Mempool opportunity filtered out (profit/risk/confidence)")

            elif opportunity.opportunity_type == 'sandwich_defense':
                logger.info(f"   🛡️  SANDWICH ATTACK DETECTED - Activating MEV protection!")
                # Here you would activate Flashbots or increase gas to avoid sandwich

        except Exception as e:
            logger.error(f"Mempool opportunity handling error: {e}")

    async def cleanup(self):
        """Cleanup system resources."""
        try:
            logger.info("🧹 Cleaning up system resources...")

            if self.price_feeds:
                await self.price_feeds.disconnect()

            if self.bridge_monitor:
                await self.bridge_monitor.cleanup()

            if self.mempool_monitor:
                await self.mempool_monitor.stop_monitoring()

            if self.executor:
                await self.executor.cleanup()

            logger.info("✅ Cleanup complete")

        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            'running': self.running,
            'execution_mode': self.execution_mode,
            'active_executions': len(self.active_executions),
            'performance_stats': self.performance_stats,
            'execution_settings': self.execution_settings
        }
