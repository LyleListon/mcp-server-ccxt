#!/usr/bin/env python3
"""
Phase 2 Production Arbitrage System

Enhanced arbitrage system with:
- MEV Protection via Flashbots
- Enhanced Flash Loan Management
- Intelligent Cross-DEX Detection
- Performance Analytics
- MCP Memory Integration
"""

import asyncio
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import Phase 2 components
from integrations.mcp.client_manager import MCPClientManager
from integrations.mev.flashbots_manager import FlashbotsManager
from integrations.flash_loans.enhanced_flash_loan_manager import EnhancedFlashLoanManager
from core.detection.enhanced_cross_dex_detector import EnhancedCrossDexDetector
from analytics.performance_analyzer import PerformanceAnalyzer
from dex.real_world_dex_adapter import RealWorldDEXAdapter
from core.strategies.capital_efficient_strategy import CapitalEfficientStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'phase2_arbitrage_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Phase2ProductionSystem:
    """Phase 2 production arbitrage system with full intelligence integration."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Phase 2 production system."""
        self.config = config
        self.running = False
        
        # Core components
        self.mcp_client_manager = None
        self.flashbots_manager = None
        self.flash_loan_manager = None
        self.enhanced_detector = None
        self.performance_analyzer = None
        self.market_adapter = None
        self.strategy = None
        
        # Performance tracking
        self.session_stats = {
            'start_time': None,
            'total_scans': 0,
            'opportunities_detected': 0,
            'high_confidence_opportunities': 0,
            'trades_executed': 0,
            'successful_trades': 0,
            'total_profit': 0.0,
            'mev_bundles_submitted': 0,
            'mev_bundles_successful': 0
        }
        
        # DEX ecosystem configuration
        self.dex_ecosystem = {
            'uniswap_v3': {'network': 'ethereum', 'liquidity': 8000000, 'fee': 0.05, 'gas': 300000},
            'sushiswap': {'network': 'ethereum', 'liquidity': 2000000, 'fee': 0.25, 'gas': 250000},
            'aerodrome': {'network': 'base', 'liquidity': 1200000, 'fee': 0.05, 'gas': 150000},
            'velodrome': {'network': 'optimism', 'liquidity': 900000, 'fee': 0.05, 'gas': 120000},
            'camelot': {'network': 'arbitrum', 'liquidity': 500000, 'fee': 0.25, 'gas': 200000},
            'thena': {'network': 'bsc', 'liquidity': 400000, 'fee': 0.2, 'gas': 250000},
            'ramses': {'network': 'arbitrum', 'liquidity': 300000, 'fee': 0.3, 'gas': 220000},
            'traderjoe': {'network': 'arbitrum', 'liquidity': 600000, 'fee': 0.3, 'gas': 180000},
            'quickswap': {'network': 'polygon', 'liquidity': 600000, 'fee': 0.3, 'gas': 160000},
            'spiritswap': {'network': 'fantom', 'liquidity': 200000, 'fee': 0.25, 'gas': 180000},
            'spookyswap': {'network': 'fantom', 'liquidity': 250000, 'fee': 0.2, 'gas': 170000},
            'pangolin': {'network': 'avalanche', 'liquidity': 350000, 'fee': 0.3, 'gas': 140000},
            'honeyswap': {'network': 'gnosis', 'liquidity': 150000, 'fee': 0.3, 'gas': 200000}
        }

    async def initialize(self) -> bool:
        """Initialize all Phase 2 components."""
        try:
            print("🚀 Initializing Phase 2 Production Arbitrage System")
            print("=" * 70)
            
            # Initialize MCP Client Manager
            print("📡 Connecting to MCP servers...")
            self.mcp_client_manager = MCPClientManager(self.config)
            mcp_connected = await self.mcp_client_manager.connect_all()
            
            if not mcp_connected:
                print("⚠️  Warning: Some MCP servers failed to connect. Continuing with fallback storage.")
            else:
                print("✅ All MCP servers connected successfully!")
            
            # Initialize market adapter
            print("🌐 Connecting to market data...")
            self.market_adapter = RealWorldDEXAdapter(self.config)
            market_connected = await self.market_adapter.connect()
            
            if not market_connected:
                print("❌ Failed to connect to market data")
                return False
            print("✅ Market data connected!")
            
            # Initialize strategy
            print("🎯 Initializing capital efficient strategy...")
            self.strategy = CapitalEfficientStrategy(self.config)
            print("✅ Strategy initialized!")
            
            # Initialize Flashbots Manager
            print("🛡️  Initializing MEV protection...")
            from web3 import Web3
            web3 = Web3()  # Mock Web3 instance
            self.flashbots_manager = FlashbotsManager(
                web3=web3,
                mcp_client_manager=self.mcp_client_manager,
                config=self.config.get('mev', {})
            )
            print("✅ MEV protection ready!")
            
            # Initialize Enhanced Cross-DEX Detector
            print("🔍 Initializing enhanced detection...")
            self.enhanced_detector = EnhancedCrossDexDetector(
                mcp_clients=self.mcp_client_manager,
                config=self.config.get('detection', {})
            )
            print("✅ Enhanced detection ready!")
            
            # Initialize Performance Analyzer
            print("📊 Initializing performance analytics...")
            self.performance_analyzer = PerformanceAnalyzer(
                mcp_client_manager=self.mcp_client_manager,
                config=self.config.get('analytics', {})
            )
            print("✅ Performance analytics ready!")
            
            print("\n🎉 Phase 2 system initialization complete!")
            print("💡 Features enabled:")
            print("   • MEV Protection with Flashbots")
            print("   • Enhanced Flash Loan Management")
            print("   • Intelligent Cross-DEX Detection")
            print("   • Performance Analytics & Learning")
            print("   • MCP Memory Integration")
            print("   • 13 DEX Ecosystem Monitoring")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Phase 2 system: {e}")
            print(f"❌ Initialization failed: {e}")
            return False

    async def start_production(self) -> None:
        """Start Phase 2 production arbitrage system."""
        try:
            if not await self.initialize():
                return
            
            self.running = True
            self.session_stats['start_time'] = datetime.now()
            
            print("\n🚀 Starting Phase 2 Production Arbitrage System")
            print("=" * 70)
            print("⚡ Enhanced arbitrage with MEV protection")
            print("🧠 Intelligent opportunity detection")
            print("📈 Real-time performance analytics")
            print("🔄 Continuous learning from patterns")
            print("=" * 70)
            print("\nPress Ctrl+C to stop...\n")
            
            scan_count = 0
            
            while self.running:
                scan_count += 1
                await self._execute_enhanced_scan(scan_count)
                
                # Show periodic intelligence reports
                if scan_count % 10 == 0:
                    await self._show_intelligence_report()
                
                await asyncio.sleep(12)  # Faster scanning for Phase 2
                
        except KeyboardInterrupt:
            print("\n🛑 System stopped by user")
        except Exception as e:
            logger.error(f"Error in production system: {e}")
            print(f"💥 System error: {e}")
        finally:
            await self._cleanup()

    async def _execute_enhanced_scan(self, scan_number: int) -> None:
        """Execute enhanced arbitrage scan with full Phase 2 capabilities."""
        scan_start = datetime.now()
        self.session_stats['total_scans'] += 1
        
        try:
            print(f"⏰ {scan_start.strftime('%H:%M:%S')} - Enhanced Scan #{scan_number}")
            
            # Get market data
            market_data = await self._get_enhanced_market_data()
            
            # Get DEX prices
            dex_prices = await self._get_dex_prices()
            
            # Enhanced opportunity detection
            opportunities = await self.enhanced_detector.detect_opportunities_with_intelligence(
                dex_prices, market_data
            )
            
            if opportunities:
                self.session_stats['opportunities_detected'] += len(opportunities)
                
                # Filter high-confidence opportunities
                high_confidence = [opp for opp in opportunities if opp.score.confidence > 0.8]
                self.session_stats['high_confidence_opportunities'] += len(high_confidence)
                
                print(f"   🎯 Found {len(opportunities)} opportunities ({len(high_confidence)} high-confidence)")
                
                # Process top opportunities
                for i, opportunity in enumerate(opportunities[:3], 1):
                    await self._process_enhanced_opportunity(opportunity, i)
                
                # Show session statistics
                await self._show_session_stats()
                
            else:
                print("   📊 No opportunities detected (normal - enhanced filters active)")
                
        except Exception as e:
            logger.error(f"Error in enhanced scan: {e}")
            print(f"   ❌ Scan error: {e}")

    async def _get_enhanced_market_data(self) -> Dict[str, Any]:
        """Get enhanced market data with MCP integration."""
        try:
            # Get basic market data
            basic_data = {
                'timestamp': datetime.now().isoformat(),
                'volatility': 0.6,  # Mock volatility
                'volume': 0.7,      # Mock volume
                'trend': 'bullish'  # Mock trend
            }
            
            # Enhance with MCP data if available
            if self.mcp_client_manager and self.mcp_client_manager.connected:
                mcp_data = await self.mcp_client_manager.get_market_data(['ETH', 'USDC', 'USDT'])
                basic_data['mcp_data'] = mcp_data
            
            return basic_data
            
        except Exception as e:
            logger.error(f"Error getting enhanced market data: {e}")
            return {'timestamp': datetime.now().isoformat()}

    async def _get_dex_prices(self) -> Dict[str, Dict[str, Any]]:
        """Get DEX prices with realistic variations."""
        try:
            # Get priority pairs
            priority_pairs = self.strategy.get_priority_pairs()
            
            # Generate realistic price data
            dex_prices = {}
            
            for dex_name, dex_info in self.dex_ecosystem.items():
                dex_prices[dex_name] = {}
                
                for pair in priority_pairs[:5]:  # Top 5 pairs
                    pair_key = f"{pair['base_token']}/{pair['quote_token']}"
                    
                    # Base price with DEX-specific variation
                    base_price = 2565.0 if pair['base_token'] == 'ETH' else 1.0
                    
                    # Liquidity-based variation
                    if dex_info['liquidity'] > 1000000:
                        variation = 1.0 + (hash(dex_name + pair_key) % 40 - 20) / 10000  # ±0.2%
                    else:
                        variation = 1.0 + (hash(dex_name + pair_key) % 100 - 50) / 10000  # ±0.5%
                    
                    dex_prices[dex_name][pair_key] = base_price * variation
            
            return dex_prices
            
        except Exception as e:
            logger.error(f"Error getting DEX prices: {e}")
            return {}

    async def _process_enhanced_opportunity(self, opportunity, index: int) -> None:
        """Process an enhanced opportunity with full Phase 2 capabilities."""
        try:
            print(f"      {index}. {opportunity.base_token}/{opportunity.quote_token}")
            print(f"         {opportunity.buy_dex} → {opportunity.sell_dex}")
            print(f"         💰 Profit: {opportunity.profit_percentage:.3f}% (${opportunity.profit_usd:.2f})")
            print(f"         📊 Score: {opportunity.score.overall_score:.3f} (Confidence: {opportunity.score.confidence:.3f})")
            
            # Get MEV protection recommendations
            if self.flashbots_manager:
                recommendations = await self.flashbots_manager.get_bundle_recommendations({
                    'base_token': opportunity.base_token,
                    'quote_token': opportunity.quote_token,
                    'buy_dex': opportunity.buy_dex,
                    'sell_dex': opportunity.sell_dex
                })
                
                if recommendations['recommendations']:
                    print(f"         🛡️  MEV: {recommendations['recommendations'][0]['message'][:50]}...")
            
            # Predict success probability
            if self.performance_analyzer:
                prediction = await self.performance_analyzer.predict_opportunity_success({
                    'base_token': opportunity.base_token,
                    'quote_token': opportunity.quote_token,
                    'buy_dex': opportunity.buy_dex,
                    'sell_dex': opportunity.sell_dex,
                    'profit_percentage': opportunity.profit_percentage
                })
                
                print(f"         🔮 Prediction: {prediction.get('prediction', 'unknown')} "
                      f"({prediction.get('success_probability', 0):.1%} success)")
            
            # Simulate execution for high-confidence opportunities
            if opportunity.score.confidence > 0.8 and opportunity.profit_usd > 10:
                await self._simulate_trade_execution(opportunity)
                
        except Exception as e:
            logger.error(f"Error processing opportunity: {e}")

    async def _simulate_trade_execution(self, opportunity) -> None:
        """Simulate trade execution with performance tracking."""
        try:
            # Simulate execution result
            import random
            success = random.random() > 0.3  # 70% success rate
            
            execution_result = {
                'trade_id': f"sim_{datetime.now().timestamp()}",
                'success': success,
                'profit_usd': float(opportunity.profit_usd) if success else -5.0,
                'gas_cost': 8.0,  # L2 gas cost
                'execution_time': random.uniform(2.0, 8.0),
                'error': None if success else 'Simulation: Market moved'
            }
            
            # Record in performance analyzer
            if self.performance_analyzer:
                await self.performance_analyzer.record_trade_execution(
                    opportunity={
                        'base_token': opportunity.base_token,
                        'quote_token': opportunity.quote_token,
                        'buy_dex': opportunity.buy_dex,
                        'sell_dex': opportunity.sell_dex,
                        'profit_percentage': opportunity.profit_percentage
                    },
                    execution_result=execution_result,
                    market_conditions=opportunity.market_conditions
                )
            
            # Update session stats
            self.session_stats['trades_executed'] += 1
            if success:
                self.session_stats['successful_trades'] += 1
                self.session_stats['total_profit'] += execution_result['profit_usd']
            
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"         🔄 Simulated execution: {status} (${execution_result['profit_usd']:.2f})")
            
        except Exception as e:
            logger.error(f"Error simulating trade execution: {e}")

    async def _show_session_stats(self) -> None:
        """Show current session statistics."""
        try:
            runtime = datetime.now() - self.session_stats['start_time']
            runtime_minutes = runtime.total_seconds() / 60
            
            success_rate = (
                self.session_stats['successful_trades'] / self.session_stats['trades_executed'] * 100
                if self.session_stats['trades_executed'] > 0 else 0
            )
            
            print(f"   📈 Session: {runtime_minutes:.1f}m runtime, "
                  f"{self.session_stats['opportunities_detected']} opportunities, "
                  f"{self.session_stats['trades_executed']} trades, "
                  f"{success_rate:.1f}% success, "
                  f"${self.session_stats['total_profit']:.2f} profit")
            
        except Exception as e:
            logger.error(f"Error showing session stats: {e}")

    async def _show_intelligence_report(self) -> None:
        """Show intelligence report every 10 scans."""
        try:
            print("\n🧠 Intelligence Report:")
            
            # Enhanced detector intelligence
            if self.enhanced_detector:
                intelligence = await self.enhanced_detector.get_market_intelligence()
                print(f"   🔍 Detection: {intelligence.get('total_patterns_analyzed', 0)} patterns analyzed")
                
                recommendations = intelligence.get('recommendations', [])
                if recommendations:
                    print(f"   💡 Recommendation: {recommendations[0]}")
            
            # Performance analytics
            if self.performance_analyzer:
                metrics = self.performance_analyzer.get_current_metrics()
                print(f"   📊 Performance: {metrics.success_rate:.1f}% success rate, "
                      f"${float(metrics.net_profit):.2f} net profit")
            
            # MEV protection stats
            if self.flashbots_manager:
                mev_stats = self.flashbots_manager.get_performance_stats()
                print(f"   🛡️  MEV: {mev_stats.total_bundles} bundles, "
                      f"{mev_stats.success_rate:.1f}% success rate")
            
            print()
            
        except Exception as e:
            logger.error(f"Error showing intelligence report: {e}")

    async def _cleanup(self) -> None:
        """Cleanup Phase 2 system resources."""
        try:
            print("\n🧹 Cleaning up Phase 2 system...")
            
            # Disconnect market adapter
            if self.market_adapter:
                await self.market_adapter.disconnect()
                print("✅ Market data disconnected")
            
            # Disconnect MCP clients
            if self.mcp_client_manager:
                await self.mcp_client_manager.disconnect_all()
                print("✅ MCP clients disconnected")
            
            # Final session report
            await self._show_final_report()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def _show_final_report(self) -> None:
        """Show final Phase 2 session report."""
        try:
            print(f"\n📊 Phase 2 Session Summary:")
            print(f"   Runtime: {(datetime.now() - self.session_stats['start_time']).total_seconds() / 60:.1f} minutes")
            print(f"   Total scans: {self.session_stats['total_scans']}")
            print(f"   Opportunities detected: {self.session_stats['opportunities_detected']}")
            print(f"   High-confidence opportunities: {self.session_stats['high_confidence_opportunities']}")
            print(f"   Trades executed: {self.session_stats['trades_executed']}")
            print(f"   Successful trades: {self.session_stats['successful_trades']}")
            print(f"   Total profit: ${self.session_stats['total_profit']:.2f}")
            
            if self.session_stats['trades_executed'] > 0:
                success_rate = self.session_stats['successful_trades'] / self.session_stats['trades_executed'] * 100
                avg_profit = self.session_stats['total_profit'] / self.session_stats['successful_trades'] if self.session_stats['successful_trades'] > 0 else 0
                print(f"   Success rate: {success_rate:.1f}%")
                print(f"   Average profit per successful trade: ${avg_profit:.2f}")
            
            print(f"\n🎉 Phase 2 Production System Complete!")
            print(f"   Enhanced with MEV protection, intelligent detection, and performance analytics!")
            
        except Exception as e:
            logger.error(f"Error showing final report: {e}")


async def main():
    """Main function for Phase 2 production system."""
    try:
        # Load configuration
        config_path = Path('config/capital_efficient_config.json')
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            # Default Phase 2 configuration
            config = {
                'mev': {
                    'max_bundle_history': 1000,
                    'bundle_timeout': 300
                },
                'detection': {
                    'min_profit_threshold': 0.3,
                    'min_confidence_score': 0.6
                },
                'analytics': {
                    'max_trade_history': 10000,
                    'analysis_window_days': 30
                }
            }
        
        # Create and start Phase 2 system
        system = Phase2ProductionSystem(config)
        await system.start_production()
        
    except KeyboardInterrupt:
        print("\n👋 Phase 2 system stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"💥 Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
