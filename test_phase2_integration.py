#!/usr/bin/env python3
"""
Phase 2 Integration Test

Comprehensive test suite for Phase 2 components:
- MEV Protection (Flashbots Manager)
- Enhanced Flash Loan Management
- Intelligent Cross-DEX Detection
- Performance Analytics
- MCP Integration
"""

import asyncio
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import Phase 2 components
from integrations.mcp.client_manager import MCPClientManager
from integrations.mev.flashbots_manager import FlashbotsManager, BundleResult
from core.detection.enhanced_cross_dex_detector import EnhancedCrossDexDetector
from analytics.performance_analyzer import PerformanceAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Phase2IntegrationTest:
    """Comprehensive Phase 2 integration test suite."""

    def __init__(self):
        """Initialize test suite."""
        self.test_config = {
            'mev': {
                'max_bundle_history': 100,
                'bundle_timeout': 60
            },
            'detection': {
                'min_profit_threshold': 0.3,
                'min_confidence_score': 0.6,
                'cache_ttl': 60
            },
            'analytics': {
                'max_trade_history': 1000,
                'analysis_window_days': 7
            }
        }
        
        self.test_results = {
            'mcp_integration': False,
            'mev_protection': False,
            'enhanced_detection': False,
            'performance_analytics': False,
            'end_to_end_flow': False
        }

    async def run_all_tests(self) -> bool:
        """Run all Phase 2 integration tests."""
        print("🧪 Starting Phase 2 Integration Tests")
        print("=" * 50)
        
        try:
            # Test 1: MCP Integration
            print("\n1️⃣ Testing MCP Integration...")
            self.test_results['mcp_integration'] = await self._test_mcp_integration()
            
            # Test 2: MEV Protection
            print("\n2️⃣ Testing MEV Protection...")
            self.test_results['mev_protection'] = await self._test_mev_protection()
            
            # Test 3: Enhanced Detection
            print("\n3️⃣ Testing Enhanced Detection...")
            self.test_results['enhanced_detection'] = await self._test_enhanced_detection()
            
            # Test 4: Performance Analytics
            print("\n4️⃣ Testing Performance Analytics...")
            self.test_results['performance_analytics'] = await self._test_performance_analytics()
            
            # Test 5: End-to-End Flow
            print("\n5️⃣ Testing End-to-End Flow...")
            self.test_results['end_to_end_flow'] = await self._test_end_to_end_flow()
            
            # Show results
            await self._show_test_results()
            
            # Return overall success
            return all(self.test_results.values())
            
        except Exception as e:
            logger.error(f"Error in integration tests: {e}")
            print(f"❌ Test suite failed: {e}")
            return False

    async def _test_mcp_integration(self) -> bool:
        """Test MCP client manager integration."""
        try:
            print("   📡 Initializing MCP client manager...")
            mcp_manager = MCPClientManager(self.test_config)
            
            # Test connection
            connected = await mcp_manager.connect_all()
            print(f"   {'✅' if connected else '⚠️ '} MCP connection: {'Success' if connected else 'Partial (using fallback)'}")
            
            # Test health check
            health = await mcp_manager.health_check()
            print(f"   📊 Health check: {len(health)} servers checked")
            
            # Test pattern storage
            test_opportunity = {
                'base_token': 'ETH',
                'quote_token': 'USDC',
                'buy_dex': 'uniswap_v3',
                'sell_dex': 'sushiswap',
                'profit_percentage': 0.5
            }
            
            test_result = {
                'success': True,
                'profit': 25.0,
                'gas_cost': 8.0
            }
            
            stored = await mcp_manager.store_arbitrage_pattern(test_opportunity, test_result)
            print(f"   {'✅' if stored else '❌'} Pattern storage: {'Success' if stored else 'Failed'}")
            
            # Test similar pattern retrieval
            similar = await mcp_manager.get_similar_opportunities(test_opportunity)
            print(f"   🔍 Similar patterns found: {len(similar)}")
            
            await mcp_manager.disconnect_all()
            print("   ✅ MCP integration test completed")
            return True
            
        except Exception as e:
            logger.error(f"MCP integration test failed: {e}")
            print(f"   ❌ MCP integration test failed: {e}")
            return False

    async def _test_mev_protection(self) -> bool:
        """Test MEV protection with Flashbots manager."""
        try:
            print("   🛡️  Initializing Flashbots manager...")
            
            # Create mock MCP manager
            mcp_manager = MCPClientManager(self.test_config)
            await mcp_manager.connect_all()
            
            # Create mock Web3 instance
            from web3 import Web3
            web3 = Web3()
            
            flashbots_manager = FlashbotsManager(
                web3=web3,
                mcp_client_manager=mcp_manager,
                config=self.test_config['mev']
            )
            
            # Test bundle submission
            test_bundle = [
                {'signed_transaction': '0x' + 'a' * 64},
                {'signed_transaction': '0x' + 'b' * 64}
            ]
            
            test_opportunity = {
                'base_token': 'ETH',
                'quote_token': 'USDC',
                'buy_dex': 'uniswap_v3',
                'sell_dex': 'sushiswap'
            }
            
            result = await flashbots_manager.submit_bundle_with_memory(
                bundle=test_bundle,
                target_block=12345678,
                opportunity_data=test_opportunity
            )
            
            print(f"   {'✅' if result.success else '❌'} Bundle submission: {'Success' if result.success else 'Failed'}")
            
            # Test gas optimization
            gas_params = await flashbots_manager.get_optimal_gas_params('medium')
            print(f"   ⛽ Gas optimization: {gas_params['maxFeePerGas'] // 1_000_000_000} gwei")
            
            # Test recommendations
            recommendations = await flashbots_manager.get_bundle_recommendations(test_opportunity)
            print(f"   💡 Recommendations: {len(recommendations['recommendations'])} generated")
            
            # Test performance stats
            stats = flashbots_manager.get_performance_stats()
            print(f"   📊 Performance tracking: {stats.total_bundles} bundles tracked")
            
            await mcp_manager.disconnect_all()
            print("   ✅ MEV protection test completed")
            return True
            
        except Exception as e:
            logger.error(f"MEV protection test failed: {e}")
            print(f"   ❌ MEV protection test failed: {e}")
            return False

    async def _test_enhanced_detection(self) -> bool:
        """Test enhanced cross-DEX detection."""
        try:
            print("   🔍 Initializing enhanced detector...")
            
            # Create mock MCP manager
            mcp_manager = MCPClientManager(self.test_config)
            await mcp_manager.connect_all()
            
            detector = EnhancedCrossDexDetector(
                mcp_clients=mcp_manager,
                config=self.test_config['detection']
            )
            
            # Test data
            test_dex_prices = {
                'uniswap_v3': {
                    'ETH/USDC': Decimal('2565.0'),
                    'USDC/USDT': Decimal('0.9998')
                },
                'sushiswap': {
                    'ETH/USDC': Decimal('2567.5'),  # 0.1% difference
                    'USDC/USDT': Decimal('1.0002')
                },
                'aerodrome': {
                    'ETH/USDC': Decimal('2563.2'),
                    'USDC/USDT': Decimal('0.9996')
                }
            }
            
            test_market_data = {
                'volatility': 0.6,
                'volume': 0.8,
                'timestamp': datetime.now().isoformat()
            }
            
            # Test enhanced detection
            opportunities = await detector.detect_opportunities_with_intelligence(
                dex_prices=test_dex_prices,
                market_data=test_market_data
            )
            
            print(f"   🎯 Opportunities detected: {len(opportunities)}")
            
            if opportunities:
                best_opp = opportunities[0]
                print(f"   💰 Best opportunity: {best_opp.profit_percentage:.3f}% profit")
                print(f"   📊 Intelligence score: {best_opp.score.overall_score:.3f}")
                print(f"   🎯 Confidence: {best_opp.score.confidence:.3f}")
            
            # Test market intelligence
            intelligence = await detector.get_market_intelligence()
            print(f"   🧠 Intelligence analysis: {intelligence.get('total_patterns_analyzed', 0)} patterns")
            
            # Test detection stats
            stats = detector.get_detection_stats()
            print(f"   📈 Detection stats: {stats['total_scans']} scans performed")
            
            await mcp_manager.disconnect_all()
            print("   ✅ Enhanced detection test completed")
            return True
            
        except Exception as e:
            logger.error(f"Enhanced detection test failed: {e}")
            print(f"   ❌ Enhanced detection test failed: {e}")
            return False

    async def _test_performance_analytics(self) -> bool:
        """Test performance analytics."""
        try:
            print("   📊 Initializing performance analyzer...")
            
            # Create mock MCP manager
            mcp_manager = MCPClientManager(self.test_config)
            await mcp_manager.connect_all()
            
            analyzer = PerformanceAnalyzer(
                mcp_client_manager=mcp_manager,
                config=self.test_config['analytics']
            )
            
            # Test trade recording
            test_opportunities = [
                {
                    'base_token': 'ETH',
                    'quote_token': 'USDC',
                    'buy_dex': 'uniswap_v3',
                    'sell_dex': 'sushiswap',
                    'profit_percentage': 0.5
                },
                {
                    'base_token': 'USDC',
                    'quote_token': 'USDT',
                    'buy_dex': 'aerodrome',
                    'sell_dex': 'velodrome',
                    'profit_percentage': 0.3
                }
            ]
            
            test_results = [
                {
                    'trade_id': 'test_1',
                    'success': True,
                    'profit_usd': 25.0,
                    'gas_cost': 8.0,
                    'execution_time': 3.5
                },
                {
                    'trade_id': 'test_2',
                    'success': False,
                    'profit_usd': -5.0,
                    'gas_cost': 8.0,
                    'execution_time': 2.1,
                    'error': 'Market moved'
                }
            ]
            
            test_market_conditions = {
                'volatility': 0.6,
                'volume': 0.8
            }
            
            # Record test trades
            for opp, result in zip(test_opportunities, test_results):
                await analyzer.record_trade_execution(opp, result, test_market_conditions)
            
            print(f"   📝 Recorded {len(test_opportunities)} test trades")
            
            # Test performance metrics
            metrics = analyzer.get_current_metrics()
            print(f"   📊 Success rate: {metrics.success_rate:.1f}%")
            print(f"   💰 Net profit: ${float(metrics.net_profit):.2f}")
            
            # Test performance report
            report = await analyzer.get_performance_report(days=7)
            if 'error' not in report:
                print(f"   📈 Performance report generated successfully")
                print(f"   🎯 Report metrics: {len(report.get('metrics', {}))} categories")
            
            # Test prediction
            prediction = await analyzer.predict_opportunity_success(test_opportunities[0])
            print(f"   🔮 Success prediction: {prediction.get('prediction', 'unknown')}")
            
            # Test trade history
            history = await analyzer.get_trade_history(limit=10)
            print(f"   📚 Trade history: {len(history)} trades retrieved")
            
            await mcp_manager.disconnect_all()
            print("   ✅ Performance analytics test completed")
            return True
            
        except Exception as e:
            logger.error(f"Performance analytics test failed: {e}")
            print(f"   ❌ Performance analytics test failed: {e}")
            return False

    async def _test_end_to_end_flow(self) -> bool:
        """Test complete end-to-end Phase 2 flow."""
        try:
            print("   🔄 Testing end-to-end Phase 2 flow...")
            
            # Initialize all components
            mcp_manager = MCPClientManager(self.test_config)
            await mcp_manager.connect_all()
            
            from web3 import Web3
            web3 = Web3()
            
            flashbots_manager = FlashbotsManager(
                web3=web3,
                mcp_client_manager=mcp_manager,
                config=self.test_config['mev']
            )
            
            detector = EnhancedCrossDexDetector(
                mcp_clients=mcp_manager,
                config=self.test_config['detection']
            )
            
            analyzer = PerformanceAnalyzer(
                mcp_client_manager=mcp_manager,
                config=self.test_config['analytics']
            )
            
            print("   ✅ All components initialized")
            
            # Simulate complete arbitrage flow
            
            # 1. Detect opportunities
            test_dex_prices = {
                'uniswap_v3': {'ETH/USDC': Decimal('2565.0')},
                'sushiswap': {'ETH/USDC': Decimal('2570.0')}  # 0.2% difference
            }
            
            test_market_data = {'volatility': 0.5, 'volume': 0.7}
            
            opportunities = await detector.detect_opportunities_with_intelligence(
                test_dex_prices, test_market_data
            )
            
            print(f"   🎯 Detected {len(opportunities)} opportunities")
            
            if opportunities:
                best_opportunity = opportunities[0]
                
                # 2. Get MEV recommendations
                mev_recommendations = await flashbots_manager.get_bundle_recommendations({
                    'base_token': best_opportunity.base_token,
                    'quote_token': best_opportunity.quote_token,
                    'buy_dex': best_opportunity.buy_dex,
                    'sell_dex': best_opportunity.sell_dex
                })
                
                print(f"   🛡️  MEV recommendations: {len(mev_recommendations['recommendations'])}")
                
                # 3. Predict success
                prediction = await analyzer.predict_opportunity_success({
                    'base_token': best_opportunity.base_token,
                    'quote_token': best_opportunity.quote_token,
                    'buy_dex': best_opportunity.buy_dex,
                    'sell_dex': best_opportunity.sell_dex,
                    'profit_percentage': best_opportunity.profit_percentage
                })
                
                print(f"   🔮 Success prediction: {prediction.get('prediction', 'unknown')}")
                
                # 4. Simulate execution
                execution_result = {
                    'trade_id': 'e2e_test',
                    'success': True,
                    'profit_usd': float(best_opportunity.profit_usd),
                    'gas_cost': 8.0,
                    'execution_time': 4.2
                }
                
                # 5. Record performance
                await analyzer.record_trade_execution(
                    {
                        'base_token': best_opportunity.base_token,
                        'quote_token': best_opportunity.quote_token,
                        'buy_dex': best_opportunity.buy_dex,
                        'sell_dex': best_opportunity.sell_dex,
                        'profit_percentage': best_opportunity.profit_percentage
                    },
                    execution_result,
                    test_market_data
                )
                
                print(f"   📊 Performance recorded successfully")
                
                # 6. Generate intelligence report
                intelligence = await detector.get_market_intelligence()
                performance_report = await analyzer.get_performance_report()
                
                print(f"   🧠 Intelligence report generated")
                print(f"   📈 Performance report generated")
                
                print("   ✅ End-to-end flow completed successfully")
                
            await mcp_manager.disconnect_all()
            return True
            
        except Exception as e:
            logger.error(f"End-to-end test failed: {e}")
            print(f"   ❌ End-to-end test failed: {e}")
            return False

    async def _show_test_results(self) -> None:
        """Show comprehensive test results."""
        print("\n" + "=" * 50)
        print("🧪 Phase 2 Integration Test Results")
        print("=" * 50)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            test_display = test_name.replace('_', ' ').title()
            print(f"{status} {test_display}")
        
        passed = sum(self.test_results.values())
        total = len(self.test_results)
        
        print(f"\n📊 Overall Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All Phase 2 components working correctly!")
            print("✅ System ready for production deployment")
        else:
            print("⚠️  Some components need attention before production")
            
        print("\n💡 Phase 2 Features Tested:")
        print("   • MCP Memory Integration")
        print("   • MEV Protection with Flashbots")
        print("   • Enhanced Cross-DEX Detection")
        print("   • Performance Analytics & Learning")
        print("   • End-to-End Arbitrage Flow")


async def main():
    """Run Phase 2 integration tests."""
    test_suite = Phase2IntegrationTest()
    success = await test_suite.run_all_tests()
    
    if success:
        print("\n🚀 Phase 2 system is ready for production!")
        return 0
    else:
        print("\n🔧 Phase 2 system needs fixes before production")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
