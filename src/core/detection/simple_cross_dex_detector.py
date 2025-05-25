"""Simple cross-DEX arbitrage detector."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dex.dex_manager import DEXManager

logger = logging.getLogger(__name__)


class SimpleCrossDexDetector:
    """Simple cross-DEX arbitrage opportunity detector."""

    def __init__(self, dexs: List[str], config: Dict[str, Any]):
        """Initialize the detector.

        Args:
            dexs: List of DEX names to monitor
            config: Configuration dictionary
        """
        self.dexs = dexs
        self.config = config
        self.min_profit_threshold = config.get('min_profit_threshold', 0.5)
        self.max_slippage = config.get('max_slippage', 1.0)

        # Initialize DEX manager for real API connections
        self.dex_manager = DEXManager(config.get('dex_config', {}))

        # Tracking
        self.opportunities_detected = 0
        self.last_scan_time = None

    async def detect_opportunities_with_intelligence(self) -> List[Dict[str, Any]]:
        """Detect arbitrage opportunities across DEXs.

        Returns:
            List of detected opportunities
        """
        opportunities = []
        self.last_scan_time = datetime.now()

        try:
            # Detect real opportunities from DEX data
            real_opportunities = await self._detect_real_opportunities()
            opportunities.extend(real_opportunities)

            self.opportunities_detected += len(opportunities)

            if opportunities:
                logger.info(f"Detected {len(opportunities)} arbitrage opportunities")

            return opportunities

        except Exception as e:
            logger.error(f"Error detecting opportunities: {e}")
            return []

    async def _detect_real_opportunities(self) -> List[Dict[str, Any]]:
        """Detect real arbitrage opportunities from DEX data."""
        opportunities = []

        try:
            # Connect to DEXs if not already connected
            await self.dex_manager.connect_all()

            # Define popular trading pairs to check
            trading_pairs = [
                ('WETH', 'USDC'),
                ('WETH', 'USDT'),
                ('WBTC', 'USDC'),
                ('WBTC', 'USDT'),
                ('USDC', 'USDT'),
                ('DAI', 'USDC'),
                ('LINK', 'USDC'),
                ('UNI', 'USDC')
            ]

            # Check each trading pair across all connected DEXs
            for base_token, quote_token in trading_pairs:
                try:
                    # Get prices from all DEXs for this pair
                    prices = await self.dex_manager.get_cross_dex_prices(base_token, quote_token)

                    # Analyze price differences for arbitrage opportunities
                    pair_opportunities = self._analyze_price_spreads(base_token, quote_token, prices)
                    opportunities.extend(pair_opportunities)

                except Exception as e:
                    logger.debug(f"Error checking {base_token}/{quote_token}: {e}")
                    continue

            # Filter and rank opportunities
            filtered_opportunities = self._filter_opportunities(opportunities)

            logger.info(f"Detected {len(filtered_opportunities)} real arbitrage opportunities")
            return filtered_opportunities

        except Exception as e:
            logger.error(f"Error detecting real opportunities: {e}")
            return []

    def _get_dex_market_data(self, dex_name: str) -> Dict[str, Any]:
        """Get market data from a specific DEX."""
        # This will be implemented with real DEX API calls
        # For now, return empty to avoid mock data
        logger.debug(f"Getting market data from {dex_name}")
        return {}

    def _analyze_price_spreads(self, base_token: str, quote_token: str, prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """Analyze price spreads between DEXs for arbitrage opportunities.

        Args:
            base_token: Base token symbol
            quote_token: Quote token symbol
            prices: Dictionary mapping DEX name to price

        Returns:
            List of arbitrage opportunities
        """
        opportunities = []

        # Filter out None prices and ensure we have at least 2 DEXs
        valid_prices = {dex: price for dex, price in prices.items() if price is not None and price > 0}

        if len(valid_prices) < 2:
            return opportunities

        # Find highest and lowest prices
        max_price_dex = max(valid_prices, key=valid_prices.get)
        min_price_dex = min(valid_prices, key=valid_prices.get)

        max_price = valid_prices[max_price_dex]
        min_price = valid_prices[min_price_dex]

        # Calculate spread percentage
        spread_percentage = ((max_price - min_price) / min_price) * 100

        # Only consider opportunities above minimum threshold
        if spread_percentage >= self.min_profit_threshold:
            # Estimate profit (simplified calculation)
            trade_amount = 1000  # $1000 trade size for estimation
            gross_profit = trade_amount * (spread_percentage / 100)

            # Estimate gas costs (rough estimate)
            estimated_gas_cost = 50  # $50 for two transactions

            # Net profit after gas
            net_profit = gross_profit - estimated_gas_cost

            # Calculate confidence based on spread size and liquidity
            confidence = min(spread_percentage / 5.0, 1.0)  # Higher spread = higher confidence, cap at 100%

            opportunity = {
                'base_token': base_token,
                'quote_token': quote_token,
                'buy_dex': min_price_dex,
                'sell_dex': max_price_dex,
                'buy_price': min_price,
                'sell_price': max_price,
                'spread_percentage': spread_percentage,
                'profit_percentage': spread_percentage,  # Add this field for profit calculator
                'estimated_profit': net_profit,
                'gross_profit': gross_profit,
                'estimated_gas_cost': estimated_gas_cost,
                'gas_estimate': 150000,  # Add gas estimate for profit calculator
                'confidence': confidence,
                'trade_amount': trade_amount,
                'timestamp': datetime.now().isoformat(),
                'all_prices': valid_prices,
                'tokens': [base_token, quote_token]  # Add tokens list for MCP
            }

            opportunities.append(opportunity)

        return opportunities

    def _filter_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter opportunities based on profitability and risk."""
        # Filter out opportunities below minimum thresholds
        filtered = []
        for opp in opportunities:
            if (opp.get('estimated_profit', 0) > 10 and  # Minimum $10 profit
                opp.get('confidence', 0) > 0.6):  # Minimum 60% confidence
                filtered.append(opp)

        # Sort by estimated profit
        filtered.sort(key=lambda x: x.get('estimated_profit', 0), reverse=True)
        return filtered[:10]  # Return top 10

    def get_stats(self) -> Dict[str, Any]:
        """Get detector statistics."""
        return {
            'opportunities_detected': self.opportunities_detected,
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'monitored_dexs': len(self.dexs),
            'min_profit_threshold': self.min_profit_threshold
        }
