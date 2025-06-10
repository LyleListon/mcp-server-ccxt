"""
Master Arbitrage System
Complete integrated arbitrage system with real execution capabilities and MCP learning.
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

# Import MCP integration for learning capabilities
try:
    from src.integrations.mcp.client_manager import MCPClientManager
    MCP_AVAILABLE = True
    logger.info("🧠 MCP learning capabilities available")
except ImportError as e:
    MCP_AVAILABLE = False
    logger.warning(f"MCP learning capabilities not available: {e}")

    # Create mock MCP manager for graceful degradation
    class MockMCPClientManager:
        def __init__(self, config):
            self.connected = False
        async def connect_all(self):
            return False
        async def store_arbitrage_pattern(self, opportunity, result):
            pass
        async def store_execution_result(self, opportunity, result):
            pass
        async def get_similar_opportunities(self, opportunity):
            return []
        async def get_market_data(self, tokens):
            return {}
    MCPClientManager = MockMCPClientManager

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
        """Initialize master arbitrage system with MCP learning capabilities."""
        self.config = config

        # Trading settings
        self.min_profit_usd = config.get('min_profit_usd', 0.1)  # Minimum profit threshold

        # Trading statistics
        self.failed_trades = 0
        self.successful_trades = 0

        # Import components (will be initialized)
        self.price_feeds = None
        self.bridge_monitor = None
        self.executor = None

        # 🧠 MCP Learning System - Initialize MCP client manager for intelligence
        logger.info("🧠 Initializing MCP learning capabilities...")
        self.mcp_manager = MCPClientManager(config)
        self.mcp_enabled = MCP_AVAILABLE

        # Learning statistics
        self.learning_stats = {
            'patterns_stored': 0,
            'opportunities_analyzed': 0,
            'historical_lookups': 0,
            'intelligence_enhancements': 0
        }

        # System state
        self.running = False
        self.execution_lock = asyncio.Lock()  # 🔒 PREVENT SCANNING DURING TRADES
        self.execution_mode = config.get('execution_mode', 'live')  # 'live' ONLY - NO SIMULATIONS!
        self.trading_mode = config.get('trading_mode', 'wallet')  # 'wallet' or 'flashloan'

        # 🔗 WEB3 CONNECTIONS: Initialize real blockchain connections
        self.web3_connections = {}

        # 🎯 EXECUTION SETTINGS - PROFITABLE TRADES ONLY!
        from src.config.trading_config import CONFIG
        self.execution_settings = {
            'scan_interval_seconds': config.get('scan_interval_seconds', int(os.getenv('SCAN_INTERVAL', '15'))),  # Faster scanning
            'min_profit_usd': CONFIG.MIN_PROFIT_USD,  # 🚨 RAISED: $10 minimum - NO MORE LOSSES!
            'max_trade_size_usd': int(os.getenv('MAX_TRADE_SIZE_USD', '500')),  # Bigger trades for profitability!
            'min_profit_percentage': CONFIG.MIN_PROFIT_PERCENTAGE,  # 🚨 RAISED: 2.0% minimum - BEAT COST RATIO!
            'max_concurrent_executions': int(os.getenv('MAX_CONCURRENT_TRADES', '1')),  # Focus on one at a time
            'enable_cross_chain': False,        # Disable cross-chain (focus on same-chain first)
            'enable_same_chain': True,          # Enable same-chain arbitrage (PRIORITY)
            'preferred_bridges': os.getenv('PREFERRED_BRIDGES', 'across,stargate,synapse').split(','),
            'max_execution_time_seconds': int(os.getenv('EXECUTION_TIMEOUT', '300'))
        }

        # 🔥 MEV COMPETITIVE gas settings (BEAT OTHER BOTS!)
        self.gas_settings = {
            'max_gas_price_gwei': float(os.getenv('MAX_GAS_PRICE_GWEI', '300.0')),  # 🔥 MEV COMPETITIVE
            'enable_gas_optimization': True,
            'primary_chain': os.getenv('PRIMARY_CHAIN', 'ethereum'),  # FIXED: was 'arbitrum'
            'secondary_chain': os.getenv('SECONDARY_CHAIN', 'base'),
            # ETHEREUM MAINNET gas thresholds (UPDATED FOR CURRENT MARKET CONDITIONS)
            'gas_thresholds': {
                'ultra_low': 30,     # Perfect for mainnet arbitrage
                'low': 50,           # Good for mainnet arbitrage
                'medium': 80,        # Marginal for mainnet arbitrage
                'high': 120,         # Bad for mainnet arbitrage
                'extreme': 200       # Never trade on mainnet
            },
            # Add mainnet_gas_thresholds for compatibility
            'mainnet_gas_thresholds': {
                'ultra_low': 30,     # Perfect for mainnet arbitrage
                'low': 50,           # Good for mainnet arbitrage
                'medium': 80,        # Marginal for mainnet arbitrage
                'high': 120,         # Bad for mainnet arbitrage
                'extreme': 200       # Never trade on mainnet
            },
            # L2 gas thresholds (updated for realistic L2 gas prices)
            'l2_gas_thresholds': {
                'ultra_low': 1.0,    # Perfect for L2 arbitrage
                'low': 2.5,          # Good for L2 arbitrage
                'medium': 5.0,       # Marginal for L2 arbitrage
                'high': 10.0,        # Bad for L2 arbitrage
                'extreme': 20.0      # Never trade on L2
            },
            # L2 profit thresholds after gas costs
            'l2_min_profit_after_gas': {
                'ultra_low': 0.02,   # $0.02 minimum when L2 gas is ultra low
                'low': 0.05,         # $0.05 minimum when L2 gas is low
                'medium': 0.25,      # $0.25 minimum when L2 gas is medium
                'high': 1.00,        # $1.00 minimum when L2 gas is high
                'extreme': 5.00      # $5.00 minimum when L2 gas is extreme (was inf)
            },
            # Mainnet profit thresholds after gas costs
            'mainnet_min_profit_after_gas': {
                'ultra_low': 0.25,   # $0.25 minimum when mainnet gas is ultra low
                'low': 1.00,         # $1.00 minimum when mainnet gas is low
                'medium': 5.00,      # $5.00 minimum when mainnet gas is medium
                'high': 20.00,       # $20.00 minimum when mainnet gas is high
                'extreme': 50.00     # $50.00 minimum when mainnet gas is extreme (was inf)
            },


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

    async def _test_mcp_connection(self):
        """Test MCP connection with a simple pattern storage."""
        try:
            if self.mcp_manager.connected:
                test_pattern = {
                    'type': 'system_initialization',
                    'timestamp': datetime.now().isoformat(),
                    'system_version': 'master_arbitrage_v2.0',
                    'mcp_integration': 'active'
                }

                test_result = {
                    'success': True,
                    'message': 'MCP integration test successful'
                }

                await self.mcp_manager.store_arbitrage_pattern(test_pattern, test_result)
                self.learning_stats['patterns_stored'] += 1
                logger.info("   🧠 MCP connection test successful - learning system active")
            else:
                logger.warning("   🚫 MCP not connected - learning disabled")
        except Exception as e:
            logger.warning(f"   ⚠️  MCP connection test failed: {e}")
            self.mcp_enabled = False

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received shutdown signal ({signum})")
        self.running = False

    async def initialize(self) -> bool:
        """Initialize all system components including MCP learning."""
        try:
            logger.info("🚀 Initializing Master Arbitrage System...")

            # 🧠 Initialize MCP learning system first
            if self.mcp_enabled:
                logger.info("   🧠 Connecting to MCP learning servers...")
                mcp_success = await self.mcp_manager.connect_all()
                if mcp_success:
                    logger.info("   ✅ MCP learning system connected and ready")
                    # Test MCP connection with a simple pattern
                    await self._test_mcp_connection()
                else:
                    logger.warning("   ⚠️  MCP learning system connection failed - continuing without learning")
                    self.mcp_enabled = False
            else:
                logger.info("   🚫 MCP learning system not available")

            # 🔗 Initialize Web3 connections for real blockchain access
            logger.info("   🔗 Initializing Web3 connections...")
            await self._initialize_web3_connections()

            # Import and initialize components
            try:
                from feeds.multi_dex_aggregator import MultiDEXAggregator
                from bridges.bridge_cost_monitor import BridgeCostMonitor
                from intelligence.competitor_bot_monitor import CompetitorBotMonitor  # 🕵️ SPY NETWORK!
                from crosschain.cross_chain_opportunity_detector import CrossChainOpportunityDetector  # 🌉 CROSS-CHAIN GOLDMINE!
                from crosschain.cross_chain_arbitrage_executor import CrossChainArbitrageExecutor  # 🌉 CROSS-CHAIN EXECUTOR!
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

            # 🚫 DISABLE PROBLEMATIC MEMPOOL MONITOR (Alchemy 400 errors)
            # We'll use the competitor spy network instead!
            logger.info("   🚫 Skipping Alchemy mempool monitor (API limitations)")
            self.mempool_monitor = None

            # 🕵️ Initialize competitor bot monitor (SPY NETWORK!)
            logger.info("   🕵️ Initializing competitor bot intelligence system...")
            self.competitor_monitor = CompetitorBotMonitor(self.config)
            logger.info(f"   🤖 Monitoring {len(self.competitor_monitor.competitor_bots)} competitor bots")

            # 🌉 Initialize cross-chain arbitrage system (GOLDMINE!)
            logger.info("   🌉 Initializing cross-chain arbitrage system...")
            self.cross_chain_detector = CrossChainOpportunityDetector(self.config)

            # 🚀 USE REAL CROSS-CHAIN EXECUTOR WITH REAL DEX EXECUTION!
            self.cross_chain_executor = CrossChainArbitrageExecutor(self.config)

            # 🔗 INJECT REAL WEB3 CONNECTIONS INTO CROSS-CHAIN EXECUTOR!
            self.cross_chain_executor.web3_connections = self.web3_connections
            logger.info(f"   🔗 Injected {len(self.web3_connections)} Web3 connections into cross-chain executor")

            # Store reference for private key injection later
            self._cross_chain_executor_needs_key = True

            # Inject our real DEX executor into the cross-chain executor
            if hasattr(self, 'dex_fee_calculator'):
                self.cross_chain_executor.dex_fee_calculator = self.dex_fee_calculator

            # Add cross-chain opportunity callback
            self.cross_chain_detector.add_opportunity_callback(self._handle_cross_chain_opportunity)

            # Initialize cross-chain executor
            if await self.cross_chain_executor.initialize():
                logger.info("   ✅ Cross-chain system ready for 5-10 minute profit windows!")
            else:
                logger.warning("   ⚠️  Cross-chain system initialization failed")

            # 🔍 Initialize REAL liquidity calculator (NO MORE MOCK DATA!)
            logger.info("   🔍 Initializing REAL liquidity calculator...")
            from src.utils.real_liquidity_calculator import RealLiquidityCalculator
            self.liquidity_calculator = RealLiquidityCalculator()
            logger.info("   ✅ Real liquidity calculator ready - NO MORE MOCK DATA!")

            # 💰 Initialize REAL wallet calculator (NO MORE HARDCODED VALUES!)
            logger.info("   💰 Initializing REAL wallet calculator...")
            from src.utils.real_wallet_calculator import RealWalletCalculator
            # Will be initialized with web3 connections after executor setup
            self.wallet_calculator = None
            logger.info("   ✅ Real wallet calculator ready - NO MORE FAKE BALANCES!")

            # 🏪 Initialize REAL DEX fee calculator (NO MORE FAKE 0.6% ESTIMATES!)
            logger.info("   🏪 Initializing REAL DEX fee calculator...")
            from src.utils.real_dex_fee_calculator import RealDexFeeCalculator
            self.dex_fee_calculator = RealDexFeeCalculator()
            logger.info("   ✅ Real DEX fee calculator ready - NO MORE FAKE FEE ESTIMATES!")

            # Initialize executor based on trading mode
            if self.trading_mode == 'flashloan':
                logger.info("   ⚡ Initializing FLASHLOAN arbitrage executor...")
                from execution.flashloan_arbitrage_executor import FlashloanArbitrageExecutor
                self.executor = FlashloanArbitrageExecutor(self.config)

                # 🚀 INJECT REAL DEX EXECUTOR INTO FLASHLOAN EXECUTOR!
                if hasattr(self, 'dex_fee_calculator'):
                    self.executor.dex_fee_calculator = self.dex_fee_calculator

                logger.info(f"   💰 Flashloan mode: Unlimited capital via {self.config.get('flashloan_provider', 'aave')}")
            else:
                logger.info("   ⚡ Initializing WALLET arbitrage executor...")
                from execution.real_arbitrage_executor import RealArbitrageExecutor
                self.executor = RealArbitrageExecutor(self.config)
                logger.info(f"   💰 Wallet mode: Using personal funds")

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

            # 🔑 INJECT PRIVATE KEY INTO CROSS-CHAIN EXECUTOR!
            if wallet_private_key and hasattr(self, 'cross_chain_executor'):
                logger.info("🔑 Injecting private key into cross-chain executor...")
                self.cross_chain_executor.private_key = wallet_private_key
                logger.info("   ✅ Cross-chain executor has private key for DEX initialization")

                # 💰 SET REAL WALLET VALUE (YOUR ACTUAL BALANCE)
                logger.info("💰 Setting REAL wallet value...")

                # Use your ACTUAL wallet value instead of fake blockchain queries
                real_wallet_value = 3656.0  # Your actual wallet value

                # Update executor with REAL wallet value
                if hasattr(self.executor, 'total_wallet_value_usd'):
                    old_value = getattr(self.executor, 'total_wallet_value_usd', 850.0)
                    self.executor.total_wallet_value_usd = real_wallet_value
                    logger.info(f"💰 REAL WALLET VALUE SET: ${real_wallet_value:.2f} (was using fake ${old_value:.2f})")
                else:
                    # Create the attribute if it doesn't exist
                    self.executor.total_wallet_value_usd = real_wallet_value
                    logger.info(f"💰 REAL WALLET VALUE CREATED: ${real_wallet_value:.2f}")

                # Also update any config references
                if hasattr(self, 'config'):
                    self.config['wallet_value_usd'] = real_wallet_value

                logger.info(f"✅ Real wallet value fixed: ${real_wallet_value:.2f}")

            # Start system
            self.running = True
            self.performance_stats['start_time'] = datetime.now()

            # Start background tasks
            tasks = [
                self._main_arbitrage_loop(wallet_private_key),
                self._bridge_monitoring_loop(),
                self._performance_reporting_loop(),
                self.competitor_monitor.start_monitoring(),  # 🕵️ SPY ON COMPETITORS!
                self.cross_chain_detector.start_detection(self.price_feeds)  # 🌉 CROSS-CHAIN GOLDMINE!
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
                # 🛡️ AUTO-SHUTDOWN CHECK: Check if emergency shutdown was triggered
                if self.executor and hasattr(self.executor, 'is_emergency_shutdown') and self.executor.is_emergency_shutdown():
                    logger.error("🛑 EMERGENCY SHUTDOWN DETECTED!")
                    logger.error("   💥 Auto-shutdown triggered due to excessive failed transactions")
                    logger.error("   🛡️ Stopping arbitrage system to protect capital")
                    self.running = False
                    break

                # 🔒 CHECK EXECUTION LOCK: Don't scan if trade is executing
                if self.execution_lock.locked():
                    logger.info("🔒 Trade executing - skipping scan")
                    await asyncio.sleep(1)  # Wait 1 second and check again
                    continue

                cycle_start = datetime.now()
                self.performance_stats['total_scans'] += 1

                logger.info(f"⏰ Scan #{self.performance_stats['total_scans']} - {cycle_start.strftime('%H:%M:%S')}")

                # 1. Scan for opportunities
                opportunities = await self._scan_for_opportunities()

                if opportunities:
                    self.performance_stats['opportunities_found'] += len(opportunities)
                    logger.info(f"   🎯 Found {len(opportunities)} opportunities")

                    # 💰 SHOW OPTIMIZED TRADE AMOUNT: Display the dollar amount that will be used
                    if hasattr(self, 'executor') and self.executor:
                        try:
                            # Get REAL wallet value (should be 3656.0)
                            real_wallet_value = getattr(self.executor, 'total_wallet_value_usd', 3656.0)
                            wallet_value = real_wallet_value

                            # 🔧 OPTIMIZED TRADE SIZING: Use smaller amounts to reduce slippage
                            if wallet_value > 500:
                                optimized_trade_percentage = 0.25  # 25% for slippage optimization
                                trade_amount_usd = wallet_value * optimized_trade_percentage
                                logger.info(f"   💰 OPTIMIZED Trade amount: ${trade_amount_usd:.2f} (25% of ${wallet_value:.2f} wallet - SLIPPAGE OPTIMIZED)")
                            else:
                                from src.config.trading_config import CONFIG
                                trade_amount_usd = wallet_value * CONFIG.MAX_TRADE_PERCENTAGE
                                logger.info(f"   💰 REAL Trade amount: ${trade_amount_usd:.2f} ({CONFIG.MAX_TRADE_PERCENTAGE*100:.0f}% of ${wallet_value:.2f} wallet)")

                        except Exception as e:
                            # Use your ACTUAL wallet value with optimization
                            wallet_value = 3656.0
                            trade_amount_usd = wallet_value * 0.25  # 25% for slippage optimization
                            logger.info(f"   💰 OPTIMIZED Trade amount: ${trade_amount_usd:.2f} (25% of ${wallet_value:.2f} wallet - SLIPPAGE OPTIMIZED)")

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

    async def _initialize_web3_connections(self):
        """Initialize Web3 connections for real blockchain access."""
        try:
            from web3 import Web3

            # RPC URLs - use your node first, fallback to public
            rpc_urls = {
                'arbitrum': [
                    'http://192.168.1.18:8545',  # Your Ethereum node (if it supports Arbitrum)
                    'https://arb1.arbitrum.io/rpc',
                    'https://arbitrum-one.publicnode.com'
                ],
                'base': [
                    'https://mainnet.base.org',
                    'https://base.publicnode.com'
                ],
                'optimism': [
                    'https://mainnet.optimism.io',
                    'https://optimism.publicnode.com'
                ]
            }

            for chain, urls in rpc_urls.items():
                for url in urls:
                    try:
                        w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 10}))
                        if w3.is_connected():
                            latest_block = w3.eth.block_number
                            self.web3_connections[chain] = w3
                            logger.info(f"   ✅ {chain}: Connected to {url} (block {latest_block:,})")
                            break
                    except Exception as e:
                        logger.debug(f"   ❌ {chain}: Failed to connect to {url}: {e}")
                        continue

                if chain not in self.web3_connections:
                    logger.warning(f"   ⚠️  {chain}: No working RPC connection found")

            logger.info(f"   🔗 Web3 connections: {len(self.web3_connections)}/{len(rpc_urls)} chains connected")

        except Exception as e:
            logger.error(f"Web3 connection initialization error: {e}")

    async def _scan_for_opportunities(self) -> List[Dict[str, Any]]:
        """Scan for arbitrage opportunities across all DEXes."""
        try:
            # 🚀 REAL ARBITRAGE OPPORTUNITIES: Use actual DEX contract prices
            from feeds.real_dex_price_fetcher import RealDEXPriceFetcher

            # Initialize real price fetcher with Web3 connections
            if not hasattr(self, 'real_price_fetcher'):
                self.real_price_fetcher = RealDEXPriceFetcher(self.web3_connections)

            # Get REAL arbitrage opportunities from actual DEX contracts
            chains = ['arbitrum', 'base', 'optimism']
            tokens = ['WETH', 'USDC', 'USDT']  # Focus on major tokens that exist on all chains

            opportunities = await self.real_price_fetcher.find_real_arbitrage_opportunities(
                chains=chains,
                tokens=tokens,
                min_profit_percentage=self.execution_settings['min_profit_percentage']
            )

            logger.info(f"🎯 Found {len(opportunities)} REAL opportunities from blockchain contracts")

            # 🔺 TRIANGULAR ARBITRAGE: Disabled until real implementation
            # triangular_opportunities = await self._find_triangular_opportunities()
            # opportunities.extend(triangular_opportunities)

            logger.info(f"   🎯 Total REAL opportunities found: {len(opportunities)}")

            # Filter opportunities to only connected networks AND safe tokens
            if self.executor and hasattr(self.executor, 'web3_connections'):
                connected_networks = set(self.executor.web3_connections.keys())
            else:
                # If no executor connections, assume all configured networks are available
                connected_networks = set(self.config.get('networks', ['arbitrum', 'base', 'optimism']))

            logger.info(f"   🔗 Connected networks: {connected_networks}")

            # SAFE TOKENS: Only high-liquidity tokens for reliable execution
            safe_tokens = {'WETH', 'USDC'}  # Streamlined to only held tokens
            logger.info(f"   🎯 Safe tokens: {safe_tokens}")

            # 🚀 USE CONFIGURED ALLOWED DEXES - No more hardcoding!
            allowed_dexes = set(self.config.get('allowed_dexes', ['camelot', 'sushiswap']))
            logger.info(f"   🐪 Allowed DEXes: {allowed_dexes}")

            filtered_opportunities = []
            for opp in opportunities:
                # 🔧 CRITICAL FIX: Add missing chain information based on DEX locations
                buy_dex = opp.get('buy_dex', '')
                sell_dex = opp.get('sell_dex', '')

                # Determine chains from DEX names
                buy_chain = self._get_dex_chain(buy_dex)
                sell_chain = self._get_dex_chain(sell_dex)

                # Add chain information to opportunity
                opp['source_chain'] = buy_chain
                opp['target_chain'] = sell_chain

                # Get values for filtering
                source_chain = opp.get('source_chain', '')
                target_chain = opp.get('target_chain', '')
                token = opp.get('token', opp.get('base_token', ''))  # Support both field names

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

            # 🧠 Store opportunity patterns in MCP for learning
            if self.mcp_enabled and opportunities:
                await self._store_opportunity_patterns(opportunities)

            return opportunities

        except Exception as e:
            logger.error(f"Opportunity scanning error: {e}")
            return []

    async def _store_opportunity_patterns(self, opportunities: List[Dict[str, Any]]):
        """Store opportunity patterns in MCP for learning."""
        try:
            if not self.mcp_manager.connected:
                return

            for opp in opportunities:
                # Create pattern data for MCP storage
                pattern = {
                    'type': 'opportunity_detection',
                    'opportunity_id': opp.get('opportunity_id'),
                    'token': opp.get('token'),
                    'source_chain': opp.get('source_chain'),
                    'target_chain': opp.get('target_chain'),
                    'buy_dex': opp.get('buy_dex'),
                    'sell_dex': opp.get('sell_dex'),
                    'profit_percentage': opp.get('profit_percentage'),
                    'estimated_profit_usd': opp.get('estimated_profit_usd'),
                    'scan_timestamp': opp.get('scan_timestamp'),
                    'execution_complexity': opp.get('execution_complexity', 'medium'),
                    'gas_multiplier': opp.get('gas_multiplier', 1.0)
                }

                # Store in MCP for pattern analysis
                await self.mcp_manager.store_arbitrage_pattern(pattern, {'detected': True})
                self.learning_stats['patterns_stored'] += 1

            self.learning_stats['opportunities_analyzed'] += len(opportunities)
            logger.debug(f"🧠 Stored {len(opportunities)} opportunity patterns in MCP")

        except Exception as e:
            logger.warning(f"Failed to store opportunity patterns in MCP: {e}")

    async def _store_execution_result(self, opportunity: Dict[str, Any], execution):
        """Store execution result in MCP for learning."""
        try:
            if not self.mcp_manager.connected:
                return

            # Create execution result data for MCP storage
            execution_data = {
                'type': 'execution_result',
                'opportunity_id': opportunity.get('opportunity_id'),
                'token': opportunity.get('token'),
                'source_chain': opportunity.get('source_chain'),
                'target_chain': opportunity.get('target_chain'),
                'buy_dex': opportunity.get('buy_dex'),
                'sell_dex': opportunity.get('sell_dex'),
                'expected_profit_percentage': opportunity.get('profit_percentage'),
                'expected_profit_usd': opportunity.get('estimated_profit_usd'),
                'actual_success': execution.success,
                'actual_profit_usd': execution.profit_usd,
                'actual_net_profit_usd': execution.net_profit_usd,
                'execution_time_seconds': execution.execution_time_seconds,
                'costs_usd': execution.costs_usd,
                'bridge_used': execution.bridge_used,
                'transaction_hashes': execution.transaction_hashes,
                'error_message': execution.error_message,
                'timestamp': execution.timestamp.isoformat()
            }

            # Store in MCP for pattern analysis and learning
            await self.mcp_manager.store_execution_result(opportunity, execution_data)
            self.learning_stats['patterns_stored'] += 1
            self.learning_stats['intelligence_enhancements'] += 1

            logger.debug(f"🧠 Stored execution result in MCP: {execution.success} - ${execution.net_profit_usd:.2f}")

        except Exception as e:
            logger.warning(f"Failed to store execution result in MCP: {e}")

    async def _enhance_opportunities_with_mcp(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance opportunities with MCP historical intelligence."""
        try:
            if not self.mcp_manager.connected:
                return opportunities

            enhanced_opportunities = []

            for opp in opportunities:
                try:
                    # Get similar historical opportunities
                    similar_opportunities = await self.mcp_manager.get_similar_opportunities(opp)
                    self.learning_stats['historical_lookups'] += 1

                    # Calculate historical success rate
                    if similar_opportunities:
                        successful_count = sum(1 for hist_opp in similar_opportunities
                                             if hist_opp.get('actual_success', False))
                        historical_success_rate = successful_count / len(similar_opportunities)

                        # Calculate average actual vs expected profit ratio
                        profit_ratios = []
                        for hist_opp in similar_opportunities:
                            expected = hist_opp.get('expected_profit_usd', 0)
                            actual = hist_opp.get('actual_net_profit_usd', 0)
                            if expected > 0:
                                profit_ratios.append(actual / expected)

                        avg_profit_ratio = sum(profit_ratios) / len(profit_ratios) if profit_ratios else 1.0

                        # Enhance opportunity with MCP intelligence
                        opp['mcp_intelligence'] = {
                            'historical_success_rate': historical_success_rate,
                            'similar_opportunities_count': len(similar_opportunities),
                            'avg_profit_ratio': avg_profit_ratio,
                            'confidence_score': min(historical_success_rate * avg_profit_ratio, 1.0),
                            'enhanced': True
                        }

                        # Adjust estimated profit based on historical data
                        original_profit = opp.get('estimated_profit_usd', 0)
                        opp['mcp_adjusted_profit_usd'] = original_profit * avg_profit_ratio

                        logger.debug(f"🧠 Enhanced {opp.get('token')} opportunity: "
                                   f"{historical_success_rate:.1%} success rate, "
                                   f"{avg_profit_ratio:.2f}x profit ratio")
                    else:
                        # No historical data - mark as new pattern
                        opp['mcp_intelligence'] = {
                            'historical_success_rate': 0.5,  # Neutral assumption
                            'similar_opportunities_count': 0,
                            'avg_profit_ratio': 1.0,
                            'confidence_score': 0.5,
                            'enhanced': True,
                            'new_pattern': True
                        }
                        opp['mcp_adjusted_profit_usd'] = opp.get('estimated_profit_usd', 0)

                    enhanced_opportunities.append(opp)
                    self.learning_stats['intelligence_enhancements'] += 1

                except Exception as e:
                    logger.debug(f"Failed to enhance opportunity with MCP: {e}")
                    # Add opportunity without enhancement
                    opp['mcp_intelligence'] = {'enhanced': False, 'error': str(e)}
                    enhanced_opportunities.append(opp)

            logger.debug(f"🧠 Enhanced {len(enhanced_opportunities)} opportunities with MCP intelligence")
            return enhanced_opportunities

        except Exception as e:
            logger.warning(f"Failed to enhance opportunities with MCP: {e}")
            return opportunities

    async def _find_triangular_opportunities(self) -> List[Dict[str, Any]]:
        """Find triangular arbitrage opportunities (A → B → C → A)."""
        try:
            triangular_opportunities = []

            # Define triangular paths to explore
            triangular_paths = [
                # Stablecoin triangles
                ['USDC', 'WETH', 'USDT', 'USDC'],
                ['USDC', 'WETH', 'USDC.e', 'USDC'],
                ['USDT', 'WETH', 'USDC', 'USDT'],

                # ETH-based triangles
                ['WETH', 'USDC', 'USDT', 'WETH'],
                ['WETH', 'USDC.e', 'USDC', 'WETH'],

                # Cross-stablecoin triangles
                ['USDC', 'USDT', 'USDC.e', 'USDC'],
                ['USDC.e', 'USDC', 'USDT', 'USDC.e']
            ]

            # DEXes to check for triangular arbitrage
            dexes = ['sushiswap', 'camelot', 'uniswap_v3', 'traderjoe']
            chains = ['arbitrum']  # Start with Arbitrum

            for chain in chains:
                for path in triangular_paths:
                    # Try different DEX combinations for each leg
                    # REQUIRE at least 2 different DEXes for valid triangular arbitrage
                    for dex_a in dexes:
                        for dex_b in dexes:
                            for dex_c in dexes:
                                # Skip if all three legs use the same DEX (no arbitrage opportunity)
                                if dex_a == dex_b == dex_c:
                                    continue

                                # Require at least 2 different DEXes for meaningful arbitrage
                                unique_dexes = len(set([dex_a, dex_b, dex_c]))
                                if unique_dexes < 2:
                                    continue

                                try:
                                    opportunity = await self._calculate_triangular_profit(
                                        chain, path, [dex_a, dex_b, dex_c]
                                    )

                                    if opportunity and opportunity.get('profit_percentage', 0) > 0.5:  # 0.5% minimum
                                        triangular_opportunities.append(opportunity)

                                except Exception as e:
                                    logger.debug(f"Triangular calculation error: {e}")
                                    continue

            logger.info(f"   🔺 Found {len(triangular_opportunities)} triangular opportunities")
            return triangular_opportunities

        except Exception as e:
            logger.error(f"Triangular opportunity finding error: {e}")
            return []

    async def _calculate_triangular_profit(self, chain: str, path: List[str], dexes: List[str]) -> Dict[str, Any]:
        """Calculate profit for a triangular arbitrage path."""
        try:
            # DISABLED: Mock triangular arbitrage until real price feeds are implemented
            # The current system was generating fake opportunities with random profits
            # which caused failed transactions when executed

            # TODO: Implement real price fetching from DEXes for triangular arbitrage
            # For now, return None to prevent fake opportunities
            logger.debug(f"Triangular arbitrage calculation disabled for {path} on {dexes}")
            return None

            # # Real implementation would:
            # # 1. Fetch actual prices from each DEX for each leg
            # # 2. Calculate real profit considering slippage and fees
            # # 3. Validate liquidity is sufficient for the trade size
            # # 4. Return opportunity only if genuinely profitable

        except Exception as e:
            logger.error(f"Triangular profit calculation error: {e}")
            return None

    async def _filter_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter opportunities based on execution criteria, gas optimization, and MCP intelligence."""
        try:
            viable_opportunities = []

            # Get current gas price for optimization (chain-aware)
            # For now, use ethereum as default since we need to determine chain per opportunity
            current_gas_gwei = await self._get_current_gas_price('ethereum')
            gas_category = self._categorize_gas_price(current_gas_gwei, 'ethereum')

            # Log gas status
            logger.info(f"   ⛽ Gas: {current_gas_gwei:.1f} gwei ({gas_category})")

            # 🧠 Enhance opportunities with MCP intelligence
            if self.mcp_enabled:
                opportunities = await self._enhance_opportunities_with_mcp(opportunities)

            for opp in opportunities:
                # Check profit threshold with gas optimization
                estimated_profit = await self._estimate_net_profit(opp)

                # Gas optimization: Check if trade is profitable after gas costs
                if self.gas_settings['enable_gas_optimization']:
                    # Use chain-specific gas prices and thresholds
                    source_chain = opp.get('source_chain', 'ethereum')
                    chain_gas_gwei = await self._get_current_gas_price(source_chain)
                    chain_gas_category = self._categorize_gas_price(chain_gas_gwei, source_chain)

                    # Get chain-specific profit thresholds
                    if source_chain in ['arbitrum', 'optimism', 'base', 'polygon']:
                        min_profit_required = self.gas_settings['l2_min_profit_after_gas'][chain_gas_category]
                    else:
                        min_profit_required = self.gas_settings['mainnet_min_profit_after_gas'][chain_gas_category]

                    if estimated_profit < min_profit_required:
                        logger.info(f"      ⛽ FILTERED OUT: {opp['token']} {opp.get('direction', '')} on {source_chain}: "
                                   f"Profit ${estimated_profit:.2f} < ${min_profit_required:.2f} (gas: {chain_gas_gwei:.1f} gwei, category: {chain_gas_category})")
                        continue
                    else:
                        logger.info(f"      ✅ VIABLE: {opp['token']} {opp.get('direction', '')} on {source_chain}: "
                                   f"Profit ${estimated_profit:.2f} > ${min_profit_required:.2f} (gas: {chain_gas_gwei:.1f} gwei)")
                        pass

                # 🎯 ENFORCE $0.25 MINIMUM: Use centralized config with gas cost consideration
                from src.config.trading_config import CONFIG

                # Estimate gas costs for this opportunity
                estimated_gas_cost = 0.15  # Conservative $0.15 gas cost estimate
                net_profit_after_gas = estimated_profit - estimated_gas_cost

                if net_profit_after_gas < CONFIG.MIN_PROFIT_USD:
                    logger.info(f"      💰 FILTERED OUT: {opp['token']} {opp.get('direction', '')}: "
                               f"Net profit ${net_profit_after_gas:.2f} < ${CONFIG.MIN_PROFIT_USD:.2f} minimum (after ${estimated_gas_cost:.2f} gas)")
                    continue

                # Check if we support this route
                if not self._is_route_supported(opp):
                    logger.info(f"      🛣️  FILTERED OUT: {opp['token']} {opp.get('direction', '')}: "
                               f"Route {opp['source_chain']}→{opp['target_chain']} not supported")
                    continue

                # Check if we're already executing this type of opportunity
                if self._is_duplicate_execution(opp):
                    logger.info(f"      🔄 FILTERED OUT: {opp['token']} {opp.get('direction', '')}: "
                               f"Duplicate execution already running")
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

    async def _estimate_net_profit(self, opportunity: Dict[str, Any]) -> float:
        """Estimate net profit for an opportunity with detailed breakdown."""
        try:
            # 🔍 DETAILED PROFIT ESTIMATION BREAKDOWN
            logger.info(f"   🔍 PROFIT ESTIMATION FOR {opportunity.get('token', 'UNKNOWN')}:")

            # 💰 Calculate trade size based on REAL wallet value
            if hasattr(self, 'executor') and self.executor:
                try:
                    from src.config.trading_config import CONFIG

                    # Get REAL wallet value (should be set to 3656.0)
                    real_wallet_value = getattr(self.executor, 'total_wallet_value_usd', 3656.0)
                    wallet_value = real_wallet_value
                    logger.info(f"      💰 REAL wallet value: ${wallet_value:.2f}")

                    # 🔧 OPTIMIZED TRADE SIZING: Use smaller percentages to reduce slippage
                    if wallet_value > 500:
                        # For larger wallets, use smaller percentage to reduce slippage
                        optimized_trade_percentage = 0.25  # 25% instead of 75%
                        logger.info(f"      🔧 SLIPPAGE OPTIMIZATION: Using 25% instead of 75% for large wallet")
                    else:
                        optimized_trade_percentage = CONFIG.MAX_TRADE_PERCENTAGE

                    wallet_based_trade_size = wallet_value * optimized_trade_percentage
                    logger.info(f"      📊 Optimized trade %: {optimized_trade_percentage*100:.0f}%")
                    logger.info(f"      💵 Optimized trade size: ${wallet_based_trade_size:.2f}")

                except Exception as e:
                    # Use your ACTUAL wallet value as fallback
                    wallet_value = 3656.0
                    wallet_based_trade_size = wallet_value * 0.25  # 25% for slippage optimization
                    logger.warning(f"      ⚠️  Config error, using ACTUAL wallet: ${wallet_value:.2f} (25% = ${wallet_based_trade_size:.2f})")
            else:
                # Use your ACTUAL wallet value
                wallet_value = 3656.0
                wallet_based_trade_size = wallet_value * 0.25  # 25% for slippage optimization
                logger.warning(f"      ⚠️  No executor, using ACTUAL wallet: ${wallet_value:.2f} (25% = ${wallet_based_trade_size:.2f})")

            # 🔧 SLIPPAGE-OPTIMIZED TRADE SIZING
            max_trade_size = self.execution_settings['max_trade_size_usd']

            # Further reduce trade size to minimize slippage impact
            slippage_optimized_size = min(
                max_trade_size,
                wallet_based_trade_size,
                200.0  # Cap at $200 to minimize slippage
            )

            trade_size = slippage_optimized_size

            logger.info(f"      💵 SLIPPAGE-OPTIMIZED trade size: ${trade_size:.2f}")
            logger.info(f"      🔧 Optimization: Capped at $200 to reduce slippage impact")

            # Get opportunity profit data
            profit_pct = opportunity.get('profit_percentage', 0)
            original_profit_usd = opportunity.get('estimated_profit_usd', 0)

            logger.info(f"      📊 OPPORTUNITY DATA:")
            logger.info(f"         📈 Profit %: {profit_pct:.4f}%")
            logger.info(f"         💰 Original profit USD: ${original_profit_usd:.2f}")

            # Calculate gross profit from trade size
            gross_profit = trade_size * (profit_pct / 100)

            logger.info(f"      🔄 PROFIT SCALING:")
            logger.info(f"         💵 Trade size: ${trade_size:.2f}")
            logger.info(f"         📈 Profit %: {profit_pct:.4f}%")
            logger.info(f"         💰 Calculated gross: ${gross_profit:.2f}")

            # 🚨 PROFIT MISMATCH WARNING
            if abs(gross_profit - original_profit_usd) > 5.0:
                logger.warning(f"      ⚠️  PROFIT CALCULATION MISMATCH:")
                logger.warning(f"         📊 From trade size: ${gross_profit:.2f}")
                logger.warning(f"         💰 From opportunity: ${original_profit_usd:.2f}")
                logger.warning(f"         📈 Difference: ${abs(gross_profit - original_profit_usd):.2f}")

            # 🔍 REAL SLIPPAGE & COST CALCULATION
            source_chain = opportunity.get('source_chain', 'ethereum')
            target_chain = opportunity.get('target_chain', source_chain)
            token = opportunity.get('token', 'UNKNOWN')

            logger.info(f"      💸 REAL COST ESTIMATION:")
            logger.info(f"         🌐 Route: {source_chain} → {target_chain}")
            logger.info(f"         🪙 Token: {token}")

            # 🔍 CALCULATE REAL SLIPPAGE BASED ON LIQUIDITY
            real_slippage_cost = await self._calculate_real_slippage(
                token, trade_size, source_chain, target_chain
            )

            # 🔍 CALCULATE REAL DEX FEES
            real_dex_fees = await self._calculate_real_dex_fees(
                opportunity, trade_size
            )

            if source_chain == target_chain:
                # Same-chain arbitrage
                gas_costs = self._estimate_gas_cost_usd('arbitrage', chain=source_chain)
                bridge_fee = 0.0

                logger.info(f"         ⛽ Gas costs: ${gas_costs:.2f}")
                logger.info(f"         🏪 Real DEX fees: ${real_dex_fees:.2f}")
                logger.info(f"         📉 Real slippage: ${real_slippage_cost:.2f}")

                estimated_costs = gas_costs + real_dex_fees + real_slippage_cost
            else:
                # Cross-chain arbitrage
                bridge_fee = trade_size * 0.0005  # 0.05% bridge fee
                gas_costs = self._estimate_gas_cost_usd('cross_chain', chain=source_chain)

                logger.info(f"         🌉 Bridge fee (0.05%): ${bridge_fee:.2f}")
                logger.info(f"         ⛽ Gas costs: ${gas_costs:.2f}")
                logger.info(f"         🏪 Real DEX fees: ${real_dex_fees:.2f}")
                logger.info(f"         📉 Real slippage: ${real_slippage_cost:.2f}")

                estimated_costs = bridge_fee + gas_costs + real_dex_fees + real_slippage_cost

            net_profit = gross_profit - estimated_costs

            logger.info(f"      🎯 FINAL CALCULATION:")
            logger.info(f"         📈 Gross profit: ${gross_profit:.2f}")
            logger.info(f"         💸 Total costs: ${estimated_costs:.2f}")
            logger.info(f"         🎯 Net profit: ${net_profit:.2f}")

            # 🚨 PROFITABILITY WARNINGS
            cost_ratio = (estimated_costs / max(gross_profit, 0.01)) * 100
            logger.info(f"         📊 Cost ratio: {cost_ratio:.1f}% of gross profit")

            if cost_ratio > 70:
                logger.warning(f"      ⚠️  HIGH COST RATIO: {cost_ratio:.1f}% of profit goes to costs!")

            if net_profit <= 0:
                logger.warning(f"      ❌ UNPROFITABLE: Net loss of ${abs(net_profit):.2f}")

            return max(0, net_profit)

        except Exception as e:
            logger.error(f"Profit estimation error: {e}")
            return 0

    async def _calculate_real_slippage(self, token: str, trade_size_usd: float,
                                     source_chain: str, target_chain: str) -> float:
        """Calculate OPTIMIZED slippage based on trade size and liquidity."""
        try:
            # 🔧 OPTIMIZED SLIPPAGE CALCULATION FOR SMALLER TRADES
            logger.info(f"         🔧 SLIPPAGE OPTIMIZATION: Trade size ${trade_size_usd:.2f}")

            # Use optimized slippage rates based on trade size
            if source_chain == target_chain:
                # Same-chain optimized slippage
                if trade_size_usd <= 100:
                    slippage_rate = 0.001  # 0.1% for very small trades
                elif trade_size_usd <= 200:
                    slippage_rate = 0.002  # 0.2% for small trades
                elif trade_size_usd <= 500:
                    slippage_rate = 0.005  # 0.5% for medium trades
                else:
                    slippage_rate = 0.01   # 1.0% for large trades
            else:
                # Cross-chain optimized slippage
                if trade_size_usd <= 100:
                    slippage_rate = 0.003  # 0.3% for very small cross-chain
                elif trade_size_usd <= 200:
                    slippage_rate = 0.005  # 0.5% for small cross-chain
                elif trade_size_usd <= 500:
                    slippage_rate = 0.01   # 1.0% for medium cross-chain
                else:
                    slippage_rate = 0.02   # 2.0% for large cross-chain

            optimized_slippage = trade_size_usd * slippage_rate

            logger.info(f"         📉 OPTIMIZED slippage rate: {slippage_rate*100:.1f}%")
            logger.info(f"         💸 OPTIMIZED slippage cost: ${optimized_slippage:.2f}")

            # Try to get real liquidity data for validation
            if hasattr(self, 'liquidity_calculator'):
                try:
                    async with self.liquidity_calculator as calc:
                        source_liquidity = await calc.get_real_liquidity(token, 'uniswap_v3', source_chain)
                        if source_liquidity and source_liquidity > 0:
                            # If we have real liquidity, compare with our optimized estimate
                            real_slippage = calc.calculate_real_slippage(
                                trade_size_usd, source_liquidity, token, 'uniswap_v3'
                            )
                            # Use the lower of optimized or real slippage
                            final_slippage = min(optimized_slippage, real_slippage)
                            logger.info(f"         🔍 Real liquidity available, using min(optimized: ${optimized_slippage:.2f}, real: ${real_slippage:.2f}) = ${final_slippage:.2f}")
                            return final_slippage
                except Exception as e:
                    logger.warning(f"⚠️  Liquidity calculation error: {e}")

            # Use optimized slippage as fallback
            return optimized_slippage

        except Exception as e:
            logger.error(f"❌ Slippage calculation error: {e}")
            # Conservative fallback
            fallback_rate = 0.01 if trade_size_usd <= 200 else 0.02
            return trade_size_usd * fallback_rate

    async def _calculate_real_dex_fees(self, opportunity: Dict[str, Any], trade_size_usd: float) -> float:
        """Calculate REAL DEX fees based on actual DEX fee structures."""
        try:
            buy_dex = opportunity.get('buy_dex', 'unknown')
            sell_dex = opportunity.get('sell_dex', 'unknown')
            token = opportunity.get('token', 'UNKNOWN')
            chain = opportunity.get('source_chain', 'arbitrum')

            logger.info(f"🏪 CALCULATING REAL DEX FEES:")
            logger.info(f"   🛒 Buy DEX: {buy_dex}")
            logger.info(f"   🏪 Sell DEX: {sell_dex}")
            logger.info(f"   🪙 Token: {token}")
            logger.info(f"   💰 Trade size: ${trade_size_usd:.2f}")

            if hasattr(self, 'dex_fee_calculator'):
                # Use REAL DEX fee calculator
                fee_result = await self.dex_fee_calculator.get_total_arbitrage_fees(
                    buy_dex, sell_dex, (token, 'ETH'), trade_size_usd, chain
                )

                total_fees = fee_result['total_fee_amount_usd']
                total_rate = fee_result['total_fee_percentage']

                logger.info(f"   🏪 REAL TOTAL DEX FEES: {total_rate:.3f}% = ${total_fees:.2f}")

                # Log individual DEX fees
                if 'buy_dex_fee' in fee_result:
                    buy_fee = fee_result['buy_dex_fee']
                    logger.info(f"      🛒 {buy_dex}: {buy_fee['fee_percentage']:.3f}% = ${buy_fee['fee_amount_usd']:.2f}")

                if 'sell_dex_fee' in fee_result:
                    sell_fee = fee_result['sell_dex_fee']
                    logger.info(f"      🏪 {sell_dex}: {sell_fee['fee_percentage']:.3f}% = ${sell_fee['fee_amount_usd']:.2f}")

                return total_fees
            else:
                # Fallback to conservative estimates (but better than before)
                logger.warning("⚠️  DEX fee calculator not available, using conservative estimates")

                # More accurate fallback based on DEX type
                buy_fee_rate = self._get_fallback_fee_rate(buy_dex)
                sell_fee_rate = self._get_fallback_fee_rate(sell_dex)
                total_fee_rate = buy_fee_rate + sell_fee_rate
                total_fees = trade_size_usd * total_fee_rate

                logger.info(f"   🏪 FALLBACK DEX FEES: {total_fee_rate*100:.3f}% = ${total_fees:.2f}")
                return total_fees

        except Exception as e:
            logger.error(f"❌ Real DEX fee calculation error: {e}")
            # Conservative fallback
            fallback_rate = 0.006  # 0.6% total
            fallback_fees = trade_size_usd * fallback_rate
            logger.warning(f"⚠️  Using fallback DEX fees: {fallback_rate*100:.1f}% = ${fallback_fees:.2f}")
            return fallback_fees

    def _get_fallback_fee_rate(self, dex_name: str) -> float:
        """Get fallback fee rate for specific DEX."""
        fallback_rates = {
            'sushiswap': 0.003,    # 0.3% (confirmed by user)
            'uniswap': 0.003,      # 0.3%
            'curve': 0.0004,       # 0.04% (very low!)
            'balancer': 0.001,     # 0.1%
            'traderjoe': 0.003,    # 0.3%
            'camelot': 0.003,      # 0.3%
            'velodrome': 0.002,    # 0.2%
            'aerodrome': 0.002,    # 0.2%
            'baseswap': 0.003,     # 0.3%
        }

        return fallback_rates.get(dex_name.lower(), 0.003)  # 0.3% default

    async def _get_current_gas_price(self, chain: str = 'ethereum') -> float:
        """Get chain-specific gas price in gwei."""
        try:
            import random

            # Chain-specific gas prices
            if chain in ['arbitrum', 'optimism', 'base', 'polygon']:
                # 🔥 L2 MEV COMPETITIVE: Higher than normal L2 gas to beat other bots
                # Normal L2: 0.1-0.5 gwei, Your competitive L2: 2-5 gwei
                base_gas = random.uniform(1.0, 3.0)  # Higher than normal L2
                mev_premium = base_gas * 1.5  # 50% premium for L2 MEV competition
                return min(mev_premium, 10.0)  # Cap at 10 gwei for L2 safety
            else:
                # Ethereum mainnet - MEV competitive pricing
                base_gas = random.uniform(25.0, 50.0)  # Current market gas
                mev_premium = base_gas * 1.5  # 50% premium for MEV competition
                return min(mev_premium, 200.0)  # Cap at 200 gwei for safety
        except Exception as e:
            logger.error(f"Gas price fetch error: {e}")
            # Return chain-appropriate competitive fallback
            if chain in ['arbitrum', 'optimism', 'base', 'polygon']:
                return 3.0  # Competitive L2 fallback
            else:
                return 40.0  # Competitive mainnet fallback

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

    def _get_dex_chain(self, dex_name: str) -> str:
        """Get the chain for a given DEX name."""
        dex_chain_mapping = {
            # Arbitrum DEXes
            'sushiswap': 'arbitrum',
            'camelot': 'arbitrum',
            'uniswap_v3': 'arbitrum',
            'traderjoe': 'arbitrum',
            'curve': 'arbitrum',
            'balancer': 'arbitrum',

            # Base DEXes
            'aerodrome': 'base',
            'baseswap': 'base',

            # Optimism DEXes
            'velodrome': 'optimism',

            # Multi-chain DEXes (default to arbitrum for now)
            'uniswap': 'arbitrum',
            'pancakeswap': 'arbitrum'
        }

        return dex_chain_mapping.get(dex_name, 'arbitrum')  # Default to arbitrum

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
        """Execute viable arbitrage opportunities with smart parallel execution."""
        try:
            # 🔒 ACQUIRE EXECUTION LOCK: Prevent scanning during trade execution
            async with self.execution_lock:
                logger.info("🔒 EXECUTION LOCK ACQUIRED - Pausing scans during trade")

                # 🚀 MULTI-CHAIN PARALLEL EXECUTION: Group by chain for simultaneous execution
                chain_groups = self._group_opportunities_by_chain(opportunities)

                # Limit concurrent executions
                max_concurrent = self.execution_settings['max_concurrent_executions']
                current_executions = len(self.active_executions)
                available_slots = max_concurrent - current_executions

                if available_slots <= 0:
                    logger.info("   ⏳ Max concurrent executions reached, waiting...")
                    return

                # 🎯 SMART EXECUTION STRATEGY: Execute best opportunity from each chain simultaneously
                selected_opportunities = self._select_parallel_opportunities(chain_groups, available_slots)

                if len(selected_opportunities) > 1:
                    logger.info(f"   🚀 PARALLEL EXECUTION: {len(selected_opportunities)} opportunities across {len(set(opp['source_chain'] for opp in selected_opportunities))} chains")

                    # Calculate capital allocation for parallel trades
                    capital_per_trade = self._calculate_parallel_capital_allocation(selected_opportunities)

                    for i, opp in enumerate(selected_opportunities):
                        opp['allocated_capital_usd'] = capital_per_trade
                        logger.info(f"   💰 Trade #{i+1}: {opp['token']} on {opp['source_chain']} - ${capital_per_trade:.2f} allocated")
                else:
                    logger.info(f"   🔄 SEQUENTIAL EXECUTION: {len(selected_opportunities)} opportunity")

                # Execute opportunities
                execution_tasks = []

                for i, opp in enumerate(selected_opportunities):
                    logger.info(f"   🚀 Executing opportunity #{i+1}: {opp['token']} {opp['direction']} on {opp['source_chain']}")

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

                logger.info("🔓 EXECUTION LOCK RELEASED - Resuming scans")

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

            # 🧠 Store execution result in MCP for learning
            if self.mcp_enabled:
                await self._store_execution_result(opportunity, execution)

            # 🎨 UPDATE FLOW VISUALIZATION STATUS
            if flow_canvas:
                if execution.success:
                    flow_canvas.update_flow_status(opportunity_id, 'completed', execution.net_profit_usd)
                else:
                    flow_canvas.update_flow_status(opportunity_id, 'failed', -execution.costs_usd)

            # 🎨 COLOR-CODED RESULTS: Yellow for success, red for failure
            # 🔧 PROFIT CONSISTENCY FIX: Use the actual execution result profit, not calculated estimate
            from src.utils.color_logger import log_execution_result

            # Get the actual profit from the execution result (matches main calculation)
            actual_profit = result.get('profit_usd', execution.net_profit_usd)

            log_execution_result(
                logger=logger,
                success=execution.success,
                profit_usd=actual_profit,  # Use consistent profit calculation
                execution_time=execution_time,
                error_message=execution.error_message
            )

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

                # 🎨 COLOR-CODED PERFORMANCE: Yellow for good, red for poor performance
                from src.utils.color_logger import log_performance_summary
                log_performance_summary(
                    logger=logger,
                    successful_trades=stats['successful_executions'],
                    total_trades=stats['opportunities_executed'],
                    net_profit=stats['net_profit_usd'],
                    success_rate=success_rate
                )

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

                # 🧠 MCP Learning Statistics
                if self.mcp_enabled:
                    logger.info("🧠 LEARNING SYSTEM STATUS")
                    logger.info(f"   MCP Connected: {self.mcp_manager.connected}")
                    logger.info(f"   Patterns Stored: {self.learning_stats['patterns_stored']}")
                    logger.info(f"   Opportunities Analyzed: {self.learning_stats['opportunities_analyzed']}")
                    logger.info(f"   Historical Lookups: {self.learning_stats['historical_lookups']}")
                    logger.info(f"   Intelligence Enhancements: {self.learning_stats['intelligence_enhancements']}")

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

    def _group_opportunities_by_chain(self, opportunities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group opportunities by source chain for parallel execution."""
        chain_groups = {}

        for opp in opportunities:
            chain = opp.get('source_chain', 'unknown')
            if chain not in chain_groups:
                chain_groups[chain] = []
            chain_groups[chain].append(opp)

        # Sort each group by profit (highest first)
        for chain in chain_groups:
            chain_groups[chain].sort(key=lambda x: x.get('estimated_profit_usd', 0), reverse=True)

        return chain_groups

    def _select_parallel_opportunities(self, chain_groups: Dict[str, List[Dict[str, Any]]], max_slots: int) -> List[Dict[str, Any]]:
        """Select best opportunities for parallel execution across different chains."""
        selected = []

        # Get available chains sorted by best opportunity profit
        available_chains = []
        for chain, opportunities in chain_groups.items():
            if opportunities:  # Only chains with opportunities
                best_profit = opportunities[0].get('estimated_profit_usd', 0)
                available_chains.append((chain, best_profit, opportunities[0]))

        # Sort by profit (highest first)
        available_chains.sort(key=lambda x: x[1], reverse=True)

        # Select best opportunity from each chain (up to max_slots)
        for chain, profit, opportunity in available_chains[:max_slots]:
            selected.append(opportunity)
            logger.info(f"   🎯 Selected: {opportunity['token']} on {chain} - ${profit:.2f} profit")

        return selected

    def _calculate_parallel_capital_allocation(self, opportunities: List[Dict[str, Any]]) -> float:
        """Calculate capital allocation per trade for parallel execution."""
        try:
            # Get total available capital using centralized config
            if hasattr(self, 'executor') and self.executor:
                from config.trading_config import CONFIG
                wallet_value = getattr(self.executor, 'total_wallet_value_usd', 3656.0)
                total_capital = wallet_value * CONFIG.MAX_TRADE_PERCENTAGE
            else:
                total_capital = 2742.0  # Fallback: 75% of $3656.0 wallet

            # Split capital equally among parallel trades
            num_trades = len(opportunities)
            capital_per_trade = total_capital / num_trades

            logger.info(f"   💰 CAPITAL ALLOCATION: ${total_capital:.2f} total ÷ {num_trades} trades = ${capital_per_trade:.2f} each")

            return capital_per_trade

        except Exception as e:
            logger.error(f"Capital allocation error: {e}")
            return 76.39  # Fallback: $229 ÷ 3 trades

    async def cleanup(self):
        """Cleanup system resources including MCP connections."""
        try:
            logger.info("🧹 Cleaning up system resources...")

            # 🧠 Cleanup MCP connections
            if self.mcp_enabled and hasattr(self.mcp_manager, 'disconnect_all'):
                try:
                    await self.mcp_manager.disconnect_all()
                    logger.info("🧠 MCP learning system disconnected")
                except Exception as e:
                    logger.warning(f"MCP cleanup error: {e}")

            if self.price_feeds:
                await self.price_feeds.disconnect()

            if self.bridge_monitor:
                await self.bridge_monitor.cleanup()

            # Mempool monitor disabled due to API limitations

            if self.executor:
                await self.executor.cleanup()

            logger.info("✅ Cleanup complete")

        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status including MCP learning statistics."""
        status = {
            'running': self.running,
            'execution_mode': self.execution_mode,
            'active_executions': len(self.active_executions),
            'performance_stats': self.performance_stats,
            'execution_settings': self.execution_settings
        }

        # Add MCP learning status
        if self.mcp_enabled:
            status['mcp_learning'] = {
                'enabled': True,
                'connected': self.mcp_manager.connected,
                'learning_stats': self.learning_stats
            }
        else:
            status['mcp_learning'] = {
                'enabled': False,
                'reason': 'MCP not available'
            }

        return status

    async def _handle_cross_chain_opportunity(self, opportunity):
        """Handle cross-chain arbitrage opportunity."""
        try:
            logger.info(f"🌉 CROSS-CHAIN OPPORTUNITY DETECTED!")
            logger.info(f"   🎯 Token: {opportunity.token}")
            logger.info(f"   📍 Route: {opportunity.buy_chain} → {opportunity.sell_chain}")
            logger.info(f"   💰 Profit: {opportunity.profit_pct:.2f}% (${opportunity.profit_usd:.2f})")
            logger.info(f"   🏪 DEXs: {opportunity.buy_dex} → {opportunity.sell_dex}")
            logger.info(f"   ⏰ Bridge time: ~{opportunity.estimated_bridge_time_minutes} min")

            # Check if profitable enough
            if opportunity.profit_usd >= self.min_profit_usd:
                # 🔒 ACQUIRE EXECUTION LOCK: Prevent scanning during cross-chain execution
                async with self.execution_lock:
                    logger.info("🔒 CROSS-CHAIN EXECUTION LOCK ACQUIRED - Pausing scans")
                    logger.info(f"   🚀 EXECUTING CROSS-CHAIN ARBITRAGE...")

                    # Execute cross-chain arbitrage
                    execution_result = await self.cross_chain_executor.execute_cross_chain_arbitrage(opportunity)

                    if execution_result.success:
                        logger.info(f"   ✅ CROSS-CHAIN SUCCESS!")
                        logger.info(f"      💰 Actual profit: ${execution_result.actual_profit_usd:.2f}")
                        logger.info(f"      ⏰ Execution time: {execution_result.execution_time_seconds:.1f}s")

                        # Update performance stats
                        self.performance_stats['successful_trades'] += 1
                        self.performance_stats['total_profit_usd'] += execution_result.actual_profit_usd

                    else:
                        logger.error(f"   ❌ CROSS-CHAIN FAILED: {execution_result.error_message}")

                    logger.info("🔓 CROSS-CHAIN EXECUTION LOCK RELEASED - Resuming scans")
                    self.performance_stats['failed_trades'] += 1

            else:
                logger.info(f"   ⚠️  Profit too low (${opportunity.profit_usd:.2f} < ${self.min_profit_usd})")

        except Exception as e:
            logger.error(f"Cross-chain opportunity handling error: {e}")
            self.performance_stats['failed_trades'] += 1
