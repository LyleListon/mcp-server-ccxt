"""
Integration tests for Enhanced Arbitrage Engine with MCP integration.
"""

import asyncio
import pytest
import logging
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Set up path for imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from integrations.mcp.client_manager import MCPClientManager
from core.arbitrage.enhanced_arbitrage_engine import EnhancedArbitrageEngine

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEnhancedArbitrageEngine:
    """Test suite for Enhanced Arbitrage Engine."""
    
    @pytest.fixture
    async def mcp_manager(self):
        """Create a mock MCP manager for testing."""
        config = {
            'servers': {
                'dexmind': {'type': 'memory', 'required': True},
                'memory_service': {'type': 'memory', 'required': True},
                'knowledge_graph': {'type': 'graph', 'required': True},
                'coincap': {'type': 'market_data', 'required': True}
            }
        }
        
        manager = MCPClientManager(config)
        
        # Mock the connection methods
        manager.connect_all = AsyncMock(return_value=True)
        manager.connected = True
        
        # Mock data retrieval methods
        manager.get_market_data = AsyncMock(return_value={
            'coincap': {'BTC': {'price': 50000, 'volume': 1000000}},
            'coinmarket': {'BTC': {'market_cap': 1000000000}},
            'ccxt': {'BTC/USDT': {'bid': 49950, 'ask': 50050}}
        })
        
        manager.get_similar_opportunities = AsyncMock(return_value=[
            {
                'tokens': ['BTC', 'ETH'],
                'success': True,
                'profit_margin': 2.5,
                'timestamp': '2024-01-01T00:00:00'
            }
        ])
        
        manager.store_arbitrage_pattern = AsyncMock(return_value=True)
        
        return manager
    
    @pytest.fixture
    def engine_config(self):
        """Create test configuration for the engine."""
        return {
            'trading': {
                'min_profit_threshold': 0.5,
                'max_slippage': 1.0,
                'trading_enabled': False,  # Simulation mode for tests
                'max_trade_amount': 1.0
            },
            'max_path_length': 3,
            'max_risk_score': 50,
            'min_enhanced_profit_score': 1.0,
            'learning_enabled': True
        }
    
    @pytest.fixture
    async def enhanced_engine(self, mcp_manager, engine_config):
        """Create enhanced arbitrage engine for testing."""
        engine = EnhancedArbitrageEngine(engine_config, mcp_manager)
        await engine.start()
        return engine
    
    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data for testing."""
        return {
            'pairs': [
                {
                    'base_token': 'BTC',
                    'quote_token': 'USDT',
                    'dex': 'uniswap_v3',
                    'price': 50000,
                    'liquidity': 1000000
                },
                {
                    'base_token': 'BTC',
                    'quote_token': 'USDT',
                    'dex': 'sushiswap',
                    'price': 50100,
                    'liquidity': 800000
                },
                {
                    'base_token': 'ETH',
                    'quote_token': 'USDT',
                    'dex': 'uniswap_v3',
                    'price': 3000,
                    'liquidity': 500000
                }
            ],
            'timestamp': datetime.now().isoformat()
        }
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, enhanced_engine):
        """Test that the enhanced engine initializes correctly."""
        assert enhanced_engine is not None
        assert enhanced_engine.mcp_manager.connected
        assert enhanced_engine.learning_enabled
        assert enhanced_engine.opportunities_found == 0
        assert enhanced_engine.successful_trades == 0
        
        logger.info("✅ Enhanced arbitrage engine initialization test passed")
    
    @pytest.mark.asyncio
    async def test_market_data_enhancement(self, enhanced_engine, sample_market_data):
        """Test market data enhancement with MCP integration."""
        enhanced_data = await enhanced_engine._enhance_market_data(sample_market_data)
        
        # Check that MCP data was added
        assert 'mcp_data' in enhanced_data
        assert 'enhanced_timestamp' in enhanced_data
        assert 'market_intelligence' in enhanced_data
        
        # Verify original data is preserved
        assert enhanced_data['pairs'] == sample_market_data['pairs']
        
        logger.info("✅ Market data enhancement test passed")
    
    @pytest.mark.asyncio
    async def test_opportunity_finding(self, enhanced_engine, sample_market_data):
        """Test opportunity finding with MCP enhancement."""
        # Mock the cross-dex detector
        enhanced_engine.cross_dex_detector.detect_opportunities_with_intelligence = AsyncMock(
            return_value=[
                {
                    'tokens': ['BTC', 'USDT'],
                    'dexs': ['uniswap_v3', 'sushiswap'],
                    'path': ['BTC', 'USDT'],
                    'estimated_profit': 100  # $100 profit
                }
            ]
        )
        
        # Mock profit calculator
        enhanced_engine.profit_calculator.calculate_profit = Mock(return_value={
            'profit_percentage': 2.0,
            'profit_amount': 100,
            'gas_cost': 20
        })
        
        # Mock risk analyzer
        enhanced_engine.risk_analyzer.analyze_risk = Mock(return_value={
            'risk_score': 30,
            'liquidity_risk': 'low',
            'slippage_risk': 'medium'
        })
        
        opportunities = await enhanced_engine.find_opportunities(sample_market_data)
        
        assert len(opportunities) > 0
        
        # Check enhanced opportunity structure
        opp = opportunities[0]
        assert 'enhanced_profit_score' in opp
        assert 'similar_opportunities_count' in opp
        assert 'historical_success_rate' in opp
        assert 'mcp_intelligence' in opp
        
        # Check MCP intelligence fields
        mcp_intel = opp['mcp_intelligence']
        assert 'pattern_confidence' in mcp_intel
        assert 'market_sentiment' in mcp_intel
        assert 'execution_recommendation' in mcp_intel
        
        logger.info("✅ Opportunity finding test passed")
    
    @pytest.mark.asyncio
    async def test_opportunity_execution(self, enhanced_engine):
        """Test opportunity execution and pattern storage."""
        sample_opportunity = {
            'id': 'test_opp_1',
            'tokens': ['BTC', 'USDT'],
            'dexs': ['uniswap_v3', 'sushiswap'],
            'enhanced_profit_score': 5.0,
            'profit_info': {
                'profit_percentage': 2.0,
                'profit_amount': 100
            }
        }
        
        result = await enhanced_engine.execute_opportunity(sample_opportunity)
        
        assert 'success' in result
        assert 'simulated' in result
        assert 'timestamp' in result
        
        # Verify MCP storage was called
        enhanced_engine.mcp_manager.store_arbitrage_pattern.assert_called_once()
        
        logger.info("✅ Opportunity execution test passed")
    
    @pytest.mark.asyncio
    async def test_performance_tracking(self, enhanced_engine, sample_market_data):
        """Test performance statistics tracking."""
        # Mock some opportunities and executions
        enhanced_engine.opportunities_found = 5
        enhanced_engine.successful_trades = 3
        enhanced_engine.total_profit = 250.0
        
        stats = await enhanced_engine.get_performance_stats()
        
        assert stats['opportunities_found'] == 5
        assert stats['successful_trades'] == 3
        assert stats['total_profit'] == 250.0
        assert stats['success_rate'] == 0.6  # 3/5
        assert stats['mcp_connected'] is True
        assert stats['learning_enabled'] is True
        
        logger.info("✅ Performance tracking test passed")
    
    @pytest.mark.asyncio
    async def test_enhanced_profit_scoring(self, enhanced_engine):
        """Test enhanced profit scoring with historical data."""
        opportunity = {
            'profit_info': {'profit_percentage': 2.0}
        }
        
        similar_opportunities = [
            {'success': True, 'profit_margin': 1.5},
            {'success': True, 'profit_margin': 2.0},
            {'success': False, 'profit_margin': 0},
            {'success': True, 'profit_margin': 2.5}
        ]
        
        enhanced_score = enhanced_engine._calculate_enhanced_profit_score(
            opportunity, similar_opportunities
        )
        
        # Enhanced score should be higher than base profit due to good historical performance
        base_profit = opportunity['profit_info']['profit_percentage']
        assert enhanced_score > base_profit
        
        logger.info(f"✅ Enhanced profit scoring test passed (base: {base_profit}, enhanced: {enhanced_score:.2f})")
    
    @pytest.mark.asyncio
    async def test_pattern_confidence_calculation(self, enhanced_engine):
        """Test pattern confidence calculation."""
        opportunity = {'tokens': ['BTC', 'ETH']}
        
        # Test with successful historical patterns
        successful_patterns = [
            {'success': True}, {'success': True}, {'success': True}
        ]
        
        confidence = enhanced_engine._calculate_pattern_confidence(
            opportunity, successful_patterns
        )
        
        assert 0 <= confidence <= 1
        assert confidence > 0  # Should have some confidence with successful patterns
        
        # Test with no historical data
        no_history_confidence = enhanced_engine._calculate_pattern_confidence(
            opportunity, []
        )
        
        assert no_history_confidence == 0.5  # Neutral confidence
        
        logger.info("✅ Pattern confidence calculation test passed")


# Test runner function
async def run_tests():
    """Run all tests manually."""
    logger.info("🚀 Starting Enhanced Arbitrage Engine Tests")
    
    # Create test instances
    config = {
        'servers': {
            'dexmind': {'type': 'memory', 'required': True}
        }
    }
    
    mcp_manager = MCPClientManager(config)
    mcp_manager.connected = True
    mcp_manager.get_market_data = AsyncMock(return_value={})
    mcp_manager.get_similar_opportunities = AsyncMock(return_value=[])
    mcp_manager.store_arbitrage_pattern = AsyncMock(return_value=True)
    
    engine_config = {
        'trading': {
            'min_profit_threshold': 0.5,
            'trading_enabled': False
        },
        'learning_enabled': True
    }
    
    engine = EnhancedArbitrageEngine(engine_config, mcp_manager)
    
    try:
        # Test initialization
        await engine.start()
        logger.info("✅ Engine started successfully")
        
        # Test market data enhancement
        sample_data = {'pairs': []}
        enhanced_data = await engine._enhance_market_data(sample_data)
        assert 'mcp_data' in enhanced_data
        logger.info("✅ Market data enhancement working")
        
        # Test performance stats
        stats = await engine.get_performance_stats()
        assert 'opportunities_found' in stats
        logger.info("✅ Performance tracking working")
        
        logger.info("🎉 All tests passed! Enhanced Arbitrage Engine is ready!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_tests())
