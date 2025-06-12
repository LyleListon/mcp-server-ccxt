"""
Enhanced Arbitrage Engine with MCP Integration

This engine builds upon the legacy arbitrage engine but adds MCP capabilities
for real-time learning, pattern recognition, and multi-source data integration.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from .simple_path_finder import SimplePathFinder
    from .simple_profit_calculator import SimpleProfitCalculator
    from .simple_risk_analyzer import SimpleRiskAnalyzer
    from ..detection.simple_cross_dex_detector import SimpleCrossDexDetector
    from ...integrations.mcp.client_manager import MCPClientManager
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from core.arbitrage.simple_path_finder import SimplePathFinder
    from core.arbitrage.simple_profit_calculator import SimpleProfitCalculator
    from core.arbitrage.simple_risk_analyzer import SimpleRiskAnalyzer
    from core.detection.simple_cross_dex_detector import SimpleCrossDexDetector
    from integrations.mcp.client_manager import MCPClientManager

logger = logging.getLogger(__name__)


class EnhancedArbitrageEngine:
    """Enhanced arbitrage engine with MCP integration for learning and intelligence."""

    def __init__(self, config: Dict[str, Any], mcp_manager: MCPClientManager):
        """Initialize the enhanced arbitrage engine.

        Args:
            config: Configuration dictionary
            mcp_manager: MCP client manager for server connections
        """
        self.config = config
        self.mcp_manager = mcp_manager

        # Initialize core components (from legacy)
        self.path_finder = SimplePathFinder(max_path_length=config.get('max_path_length', 3))
        self.profit_calculator = SimpleProfitCalculator(config)
        self.risk_analyzer = SimpleRiskAnalyzer(config)

        # Initialize enhanced components
        self.cross_dex_detector = SimpleCrossDexDetector([], config)

        # Trading configuration
        trading_config = config.get("trading", {})
        self.min_profit_threshold = trading_config.get("min_profit_threshold", 0.5)
        self.max_slippage = trading_config.get("max_slippage", 1.0)
        self.trading_enabled = trading_config.get("trading_enabled", False)

        # Learning and intelligence
        self.learning_enabled = config.get("learning_enabled", True)
        self.pattern_cache = {}
        self.market_intelligence = {}

        # Performance tracking
        self.opportunities_found = 0
        self.successful_trades = 0
        self.total_profit = 0.0

        logger.info("Enhanced arbitrage engine initialized with MCP integration")

    async def start(self) -> bool:
        """Start the enhanced arbitrage engine.

        Returns:
            bool: True if started successfully
        """
        logger.info("Starting enhanced arbitrage engine...")

        # Ensure MCP connections are ready
        if not self.mcp_manager.connected:
            logger.info("Connecting to MCP servers...")
            if not await self.mcp_manager.connect_all():
                logger.error("Failed to connect to required MCP servers")
                return False

        # Load historical patterns for learning
        if self.learning_enabled:
            await self._load_historical_patterns()

        # Initialize market intelligence
        await self._initialize_market_intelligence()

        logger.info("Enhanced arbitrage engine started successfully")
        return True

    async def find_opportunities(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find arbitrage opportunities with MCP-enhanced intelligence.

        Args:
            market_data: Current market data

        Returns:
            List of enhanced arbitrage opportunities
        """
        try:
            # Get enhanced market data from MCP servers
            enhanced_market_data = await self._enhance_market_data(market_data)

            # Use legacy path finder with enhanced data
            self.path_finder.update_graph(enhanced_market_data)
            raw_opportunities = await self._find_raw_opportunities(enhanced_market_data)

            # Enhance opportunities with MCP intelligence
            enhanced_opportunities = []
            for opportunity in raw_opportunities:
                enhanced_opp = await self._enhance_opportunity(opportunity)
                if enhanced_opp:
                    enhanced_opportunities.append(enhanced_opp)

            # Sort by enhanced profit score
            enhanced_opportunities.sort(
                key=lambda x: x.get('enhanced_profit_score', 0),
                reverse=True
            )

            self.opportunities_found += len(enhanced_opportunities)

            if enhanced_opportunities:
                logger.info(f"Found {len(enhanced_opportunities)} enhanced arbitrage opportunities")

            return enhanced_opportunities

        except Exception as e:
            logger.error(f"Error finding opportunities: {e}")
            return []

    async def _enhance_market_data(self, base_market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance market data with MCP server information.

        Args:
            base_market_data: Base market data

        Returns:
            Enhanced market data with MCP intelligence
        """
        enhanced_data = base_market_data.copy()

        try:
            # Get tokens from market data
            tokens = self._extract_tokens_from_market_data(base_market_data)

            # Get real-time data from MCP servers
            mcp_market_data = await self.mcp_manager.get_market_data(tokens)

            # Merge MCP data with base data
            enhanced_data['mcp_data'] = mcp_market_data
            enhanced_data['enhanced_timestamp'] = datetime.now().isoformat()

            # Add market intelligence
            enhanced_data['market_intelligence'] = self.market_intelligence

            return enhanced_data

        except Exception as e:
            logger.error(f"Error enhancing market data: {e}")
            return base_market_data

    def _extract_tokens_from_market_data(self, market_data: Dict[str, Any]) -> List[str]:
        """Extract token symbols from market data."""
        tokens = set()

        for pair in market_data.get("pairs", []):
            if pair.get("base_token"):
                tokens.add(pair["base_token"])
            if pair.get("quote_token"):
                tokens.add(pair["quote_token"])

        return list(tokens)

    async def _find_raw_opportunities(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find raw arbitrage opportunities using legacy logic."""
        opportunities = []

        try:
            # Use cross-DEX detector for opportunity finding
            detected_opportunities = await self.cross_dex_detector.detect_opportunities_with_intelligence()

            for opp in detected_opportunities:
                # Calculate profit using legacy calculator
                profit_info = self.profit_calculator.calculate_profit(opp)

                # Analyze risk using legacy analyzer
                risk_info = self.risk_analyzer.analyze_risk(opp)

                # Check if opportunity meets thresholds
                if (profit_info.get('profit_percentage', 0) >= self.min_profit_threshold and
                    risk_info.get('risk_score', 100) <= self.config.get('max_risk_score', 50)):

                    opportunity = {
                        'id': f"arb_{datetime.now().timestamp()}",
                        'timestamp': datetime.now().isoformat(),
                        'tokens': opp.get('tokens', []),
                        'dexs': opp.get('dexs', []),
                        'path': opp.get('path', []),
                        'profit_info': profit_info,
                        'risk_info': risk_info,
                        'market_conditions': self._get_market_conditions(market_data),
                        'raw_opportunity': opp
                    }

                    opportunities.append(opportunity)

            return opportunities

        except Exception as e:
            logger.error(f"Error finding raw opportunities: {e}")
            return []

    async def _enhance_opportunity(self, opportunity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enhance opportunity with MCP intelligence and learning.

        Args:
            opportunity: Raw opportunity data

        Returns:
            Enhanced opportunity or None if filtered out
        """
        try:
            enhanced_opp = opportunity.copy()

            # Get similar historical opportunities
            similar_opportunities = await self.mcp_manager.get_similar_opportunities(opportunity)

            # Calculate enhanced profit score based on historical success
            enhanced_profit_score = self._calculate_enhanced_profit_score(
                opportunity, similar_opportunities
            )

            # Add MCP intelligence
            enhanced_opp.update({
                'enhanced_profit_score': enhanced_profit_score,
                'similar_opportunities_count': len(similar_opportunities),
                'historical_success_rate': self._calculate_historical_success_rate(similar_opportunities),
                'mcp_intelligence': {
                    'pattern_confidence': self._calculate_pattern_confidence(opportunity, similar_opportunities),
                    'market_sentiment': self._get_market_sentiment(opportunity),
                    'execution_recommendation': self._get_execution_recommendation(opportunity, similar_opportunities)
                }
            })

            # Filter based on enhanced criteria
            if enhanced_profit_score < self.config.get('min_enhanced_profit_score', 1.0):
                logger.debug(f"Opportunity filtered out due to low enhanced profit score: {enhanced_profit_score}")
                return None

            return enhanced_opp

        except Exception as e:
            logger.error(f"Error enhancing opportunity: {e}")
            return opportunity  # Return original if enhancement fails

    def _calculate_enhanced_profit_score(self, opportunity: Dict[str, Any], similar_opportunities: List[Dict[str, Any]]) -> float:
        """Calculate enhanced profit score based on historical data."""
        base_profit = opportunity.get('profit_info', {}).get('profit_percentage', 0)

        if not similar_opportunities:
            return base_profit

        # Calculate average historical success
        successful_trades = [opp for opp in similar_opportunities if opp.get('success', False)]
        success_rate = len(successful_trades) / len(similar_opportunities) if similar_opportunities else 0

        # Calculate average historical profit
        avg_historical_profit = sum(
            opp.get('profit_margin', 0) for opp in successful_trades
        ) / len(successful_trades) if successful_trades else 0

        # Enhanced score combines current profit with historical performance
        enhanced_score = base_profit * (1 + success_rate) * (1 + avg_historical_profit / 100)

        return enhanced_score

    def _calculate_historical_success_rate(self, similar_opportunities: List[Dict[str, Any]]) -> float:
        """Calculate historical success rate for similar opportunities."""
        if not similar_opportunities:
            return 0.0

        successful = sum(1 for opp in similar_opportunities if opp.get('success', False))
        return successful / len(similar_opportunities)

    def _calculate_pattern_confidence(self, opportunity: Dict[str, Any], similar_opportunities: List[Dict[str, Any]]) -> float:
        """Calculate confidence in the arbitrage pattern."""
        if not similar_opportunities:
            return 0.5  # Neutral confidence for new patterns

        # Higher confidence with more similar successful opportunities
        successful_count = sum(1 for opp in similar_opportunities if opp.get('success', False))
        confidence = min(successful_count / 10, 1.0)  # Cap at 1.0

        return confidence

    def _get_market_sentiment(self, opportunity: Dict[str, Any]) -> str:
        """Get market sentiment for the opportunity tokens."""
        # Placeholder for market sentiment analysis
        return "neutral"

    def _get_execution_recommendation(self, opportunity: Dict[str, Any], similar_opportunities: List[Dict[str, Any]]) -> str:
        """Get execution recommendation based on historical data."""
        success_rate = self._calculate_historical_success_rate(similar_opportunities)

        if success_rate >= 0.8:
            return "highly_recommended"
        elif success_rate >= 0.6:
            return "recommended"
        elif success_rate >= 0.4:
            return "cautious"
        else:
            return "not_recommended"

    def _get_market_conditions(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract current market conditions."""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_pairs': len(market_data.get('pairs', [])),
            'avg_liquidity': self._calculate_average_liquidity(market_data),
            'volatility_indicator': self._calculate_volatility_indicator(market_data)
        }

    def _calculate_average_liquidity(self, market_data: Dict[str, Any]) -> float:
        """Calculate average liquidity across all pairs."""
        pairs = market_data.get('pairs', [])
        if not pairs:
            return 0.0

        total_liquidity = sum(pair.get('liquidity', 0) for pair in pairs)
        return total_liquidity / len(pairs)

    def _calculate_volatility_indicator(self, market_data: Dict[str, Any]) -> float:
        """Calculate volatility indicator."""
        # Placeholder for volatility calculation
        return 0.5

    async def execute_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute arbitrage opportunity and store results.

        Args:
            opportunity: Enhanced opportunity to execute

        Returns:
            Execution result
        """
        if not self.trading_enabled:
            logger.info("Trading disabled, simulating execution")
            return await self._simulate_execution(opportunity)

        try:
            # Actual execution logic would go here
            result = await self._execute_trade(opportunity)

            # Store pattern in MCP for learning
            if self.learning_enabled:
                await self.mcp_manager.store_arbitrage_pattern(opportunity, result)

            # Update performance tracking
            if result.get('success', False):
                self.successful_trades += 1
                self.total_profit += result.get('profit', 0)

            return result

        except Exception as e:
            logger.error(f"Error executing opportunity: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def _simulate_execution(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """NO SIMULATION ALLOWED - REAL EXECUTION ONLY!"""
        logger.error(f"🚨 SIMULATION DISABLED for opportunity {opportunity.get('id')}")
        logger.error("   Real execution must be implemented - no mock data!")

        return {
            'success': False,
            'error': 'Simulation disabled - real execution required',
            'timestamp': datetime.now().isoformat()
        }

        result = {
            'success': success,
            'simulated': True,
            'profit': opportunity.get('profit_info', {}).get('profit_amount', 0) if success else 0,
            'gas_used': random.randint(100000, 300000),
            'execution_time': random.uniform(1.0, 5.0),
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"Simulation result: {'SUCCESS' if success else 'FAILED'}")
        return result

    async def _execute_trade(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute actual trade (placeholder for real implementation)."""
        # This would contain the actual trading logic
        # For now, return simulation
        return await self._simulate_execution(opportunity)

    async def _load_historical_patterns(self) -> None:
        """Load historical arbitrage patterns for learning."""
        try:
            # Query memory servers for historical patterns
            if self.mcp_manager.connected:
                # Placeholder for loading historical data
                logger.info("Loading historical arbitrage patterns...")
                # self.pattern_cache = await self.mcp_manager.load_historical_patterns()

        except Exception as e:
            logger.error(f"Error loading historical patterns: {e}")

    async def _initialize_market_intelligence(self) -> None:
        """Initialize market intelligence from MCP servers."""
        try:
            # Get market intelligence data
            self.market_intelligence = {
                'initialized_at': datetime.now().isoformat(),
                'data_sources': ['coincap', 'coinmarket', 'ccxt'],
                'learning_enabled': self.learning_enabled
            }

            logger.info("Market intelligence initialized")

        except Exception as e:
            logger.error(f"Error initializing market intelligence: {e}")

    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            'opportunities_found': self.opportunities_found,
            'successful_trades': self.successful_trades,
            'total_profit': self.total_profit,
            'success_rate': self.successful_trades / max(self.opportunities_found, 1),
            'mcp_connected': self.mcp_manager.connected,
            'learning_enabled': self.learning_enabled
        }
