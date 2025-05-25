"""
DEX Manager for Real Trading

Manages connections to multiple DEXs and provides unified interface
for price data, liquidity information, and trade execution.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .uniswap_v3_adapter import UniswapV3Adapter
from .sushiswap_adapter import SushiSwapAdapter
from .real_price_adapter import CoinbaseAdapter, CoinGeckoAdapter
from .oneinch_adapter import OneInchAdapter
from .paraswap_adapter import ParaswapAdapter
from .stablecoin_adapter import StablecoinAdapter

logger = logging.getLogger(__name__)


class DEXManager:
    """Manages multiple DEX connections for arbitrage trading."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize DEX manager.

        Args:
            config: Configuration for all DEXs
        """
        self.config = config
        self.dexs = {}
        self.connected_dexs = []

        # Initialize DEX adapters
        self._initialize_dexs()

        # Market data cache
        self.market_data_cache = {}
        self.cache_ttl = 30  # 30 seconds

        logger.info("DEX Manager initialized")

    def _initialize_dexs(self) -> None:
        """Initialize all DEX adapters."""
        dex_configs = self.config.get('dexs', {})

        # Uniswap V3
        if dex_configs.get('uniswap_v3', {}).get('enabled', True):
            self.dexs['uniswap_v3'] = UniswapV3Adapter(dex_configs.get('uniswap_v3', {}))

        # SushiSwap
        if dex_configs.get('sushiswap', {}).get('enabled', True):
            self.dexs['sushiswap'] = SushiSwapAdapter(dex_configs.get('sushiswap', {}))

        # Real price adapters
        if dex_configs.get('coinbase', {}).get('enabled', True):
            self.dexs['coinbase'] = CoinbaseAdapter(dex_configs.get('coinbase', {}))

        if dex_configs.get('coingecko', {}).get('enabled', True):
            self.dexs['coingecko'] = CoinGeckoAdapter(dex_configs.get('coingecko', {}))

        # DEX aggregators
        if dex_configs.get('1inch', {}).get('enabled', True):
            self.dexs['1inch'] = OneInchAdapter(dex_configs.get('1inch', {}))

        if dex_configs.get('paraswap', {}).get('enabled', True):
            self.dexs['paraswap'] = ParaswapAdapter(dex_configs.get('paraswap', {}))

        # Stablecoin specialist
        if dex_configs.get('stablecoin_specialist', {}).get('enabled', True):
            self.dexs['stablecoin_specialist'] = StablecoinAdapter(dex_configs.get('stablecoin_specialist', {}))

        logger.info(f"Initialized {len(self.dexs)} DEX adapters: {list(self.dexs.keys())}")

    async def connect_all(self) -> bool:
        """Connect to all configured DEXs.

        Returns:
            True if at least one DEX connected successfully
        """
        logger.info("Connecting to all DEXs...")

        connection_tasks = []
        for dex_name, dex_adapter in self.dexs.items():
            task = asyncio.create_task(
                self._connect_dex(dex_name, dex_adapter),
                name=f"connect_{dex_name}"
            )
            connection_tasks.append(task)

        # Wait for all connections
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)

        # Check results
        self.connected_dexs = []
        for i, result in enumerate(results):
            dex_name = list(self.dexs.keys())[i]
            if isinstance(result, Exception):
                logger.error(f"Failed to connect to {dex_name}: {result}")
            elif result:
                self.connected_dexs.append(dex_name)
                logger.info(f"✅ Connected to {dex_name}")
            else:
                logger.warning(f"Failed to connect to {dex_name}")

        success = len(self.connected_dexs) > 0
        if success:
            logger.info(f"DEX Manager ready with {len(self.connected_dexs)} DEXs: {self.connected_dexs}")
        else:
            logger.error("Failed to connect to any DEXs")

        return success

    async def _connect_dex(self, dex_name: str, dex_adapter) -> bool:
        """Connect to a specific DEX."""
        try:
            return await dex_adapter.connect()
        except Exception as e:
            logger.error(f"Error connecting to {dex_name}: {e}")
            return False

    async def get_all_pairs(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all trading pairs from all connected DEXs.

        Returns:
            Dictionary mapping DEX name to list of pairs
        """
        all_pairs = {}

        tasks = []
        for dex_name in self.connected_dexs:
            dex_adapter = self.dexs[dex_name]
            task = asyncio.create_task(
                dex_adapter.get_pairs(),
                name=f"get_pairs_{dex_name}"
            )
            tasks.append((dex_name, task))

        # Wait for all pair data
        for dex_name, task in tasks:
            try:
                pairs = await task
                all_pairs[dex_name] = pairs
                logger.info(f"Got {len(pairs)} pairs from {dex_name}")
            except Exception as e:
                logger.error(f"Error getting pairs from {dex_name}: {e}")
                all_pairs[dex_name] = []

        return all_pairs

    async def get_cross_dex_prices(self, base_token: str, quote_token: str) -> Dict[str, Optional[float]]:
        """Get prices for a token pair across all DEXs.

        Args:
            base_token: Base token symbol
            quote_token: Quote token symbol

        Returns:
            Dictionary mapping DEX name to price
        """
        prices = {}

        tasks = []
        for dex_name in self.connected_dexs:
            dex_adapter = self.dexs[dex_name]
            task = asyncio.create_task(
                dex_adapter.get_price(base_token, quote_token),
                name=f"get_price_{dex_name}"
            )
            tasks.append((dex_name, task))

        # Wait for all price data
        for dex_name, task in tasks:
            try:
                price = await task
                prices[dex_name] = price
            except Exception as e:
                logger.error(f"Error getting price from {dex_name}: {e}")
                prices[dex_name] = None

        return prices

    async def find_arbitrage_opportunities(self, min_profit_percentage: float = 0.5) -> List[Dict[str, Any]]:
        """Find arbitrage opportunities across connected DEXs.

        Args:
            min_profit_percentage: Minimum profit percentage to consider

        Returns:
            List of arbitrage opportunities
        """
        opportunities = []

        try:
            # Get all pairs from all DEXs
            all_pairs = await self.get_all_pairs()

            # Find common token pairs across DEXs
            common_pairs = self._find_common_pairs(all_pairs)

            logger.info(f"Found {len(common_pairs)} common pairs across DEXs")

            # Check each common pair for arbitrage opportunities
            for base_token, quote_token in common_pairs:
                try:
                    opportunity = await self._check_arbitrage_opportunity(
                        base_token, quote_token, all_pairs, min_profit_percentage
                    )
                    if opportunity:
                        opportunities.append(opportunity)

                except Exception as e:
                    logger.error(f"Error checking arbitrage for {base_token}/{quote_token}: {e}")
                    continue

            # Sort by profit potential
            opportunities.sort(key=lambda x: x.get('profit_percentage', 0), reverse=True)

            logger.info(f"Found {len(opportunities)} arbitrage opportunities")
            return opportunities

        except Exception as e:
            logger.error(f"Error finding arbitrage opportunities: {e}")
            return []

    def _find_common_pairs(self, all_pairs: Dict[str, List[Dict[str, Any]]]) -> List[tuple]:
        """Find token pairs that exist on multiple DEXs."""
        pair_sets = {}

        for dex_name, pairs in all_pairs.items():
            pair_set = set()
            for pair in pairs:
                base = pair.get('base_token')
                quote = pair.get('quote_token')
                if base and quote:
                    # Normalize pair order
                    normalized_pair = tuple(sorted([base, quote]))
                    pair_set.add(normalized_pair)

            pair_sets[dex_name] = pair_set

        # Find intersection of all DEX pair sets
        if not pair_sets:
            return []

        common_pairs = set.intersection(*pair_sets.values())
        return list(common_pairs)

    async def _check_arbitrage_opportunity(self, base_token: str, quote_token: str,
                                         all_pairs: Dict[str, List[Dict[str, Any]]],
                                         min_profit_percentage: float) -> Optional[Dict[str, Any]]:
        """Check for arbitrage opportunity for a specific token pair."""
        try:
            # Get prices from all DEXs
            prices = await self.get_cross_dex_prices(base_token, quote_token)

            # Filter out None prices
            valid_prices = {dex: price for dex, price in prices.items() if price is not None and price > 0}

            if len(valid_prices) < 2:
                return None  # Need at least 2 DEXs with valid prices

            # Find highest and lowest prices
            max_price_dex = max(valid_prices, key=valid_prices.get)
            min_price_dex = min(valid_prices, key=valid_prices.get)

            max_price = valid_prices[max_price_dex]
            min_price = valid_prices[min_price_dex]

            # Calculate profit percentage
            profit_percentage = ((max_price - min_price) / min_price) * 100

            if profit_percentage < min_profit_percentage:
                return None

            # Get liquidity information
            buy_liquidity = await self.dexs[min_price_dex].get_liquidity(base_token, quote_token)
            sell_liquidity = await self.dexs[max_price_dex].get_liquidity(base_token, quote_token)

            # Estimate trade size based on liquidity
            min_liquidity = min(buy_liquidity or 0, sell_liquidity or 0)
            max_trade_size_usd = min_liquidity * 0.01 if min_liquidity > 0 else 1000  # 1% of liquidity or $1000

            opportunity = {
                'id': f"arb_{base_token}_{quote_token}_{datetime.now().timestamp()}",
                'base_token': base_token,
                'quote_token': quote_token,
                'buy_dex': min_price_dex,
                'sell_dex': max_price_dex,
                'buy_price': min_price,
                'sell_price': max_price,
                'profit_percentage': profit_percentage,
                'estimated_profit_usd': (max_price - min_price) * (max_trade_size_usd / min_price),
                'max_trade_size_usd': max_trade_size_usd,
                'buy_liquidity': buy_liquidity,
                'sell_liquidity': sell_liquidity,
                'all_prices': valid_prices,
                'timestamp': datetime.now().isoformat(),
                'dex_count': len(valid_prices)
            }

            return opportunity

        except Exception as e:
            logger.error(f"Error checking arbitrage opportunity for {base_token}/{quote_token}: {e}")
            return None

    async def get_quote(self, dex_name: str, base_token: str, quote_token: str, amount: float) -> Optional[Dict[str, Any]]:
        """Get a quote from a specific DEX.

        Args:
            dex_name: Name of the DEX
            base_token: Token to sell
            quote_token: Token to buy
            amount: Amount to trade

        Returns:
            Quote information
        """
        if dex_name not in self.connected_dexs:
            logger.error(f"DEX {dex_name} not connected")
            return None

        try:
            dex_adapter = self.dexs[dex_name]
            return await dex_adapter.get_quote(base_token, quote_token, amount)
        except Exception as e:
            logger.error(f"Error getting quote from {dex_name}: {e}")
            return None

    async def disconnect_all(self) -> None:
        """Disconnect from all DEXs."""
        logger.info("Disconnecting from all DEXs...")

        for dex_name, dex_adapter in self.dexs.items():
            try:
                await dex_adapter.disconnect()
                logger.info(f"Disconnected from {dex_name}")
            except Exception as e:
                logger.error(f"Error disconnecting from {dex_name}: {e}")

        self.connected_dexs = []
        logger.info("All DEXs disconnected")

    def get_connected_dexs(self) -> List[str]:
        """Get list of connected DEX names."""
        return self.connected_dexs.copy()

    def is_connected(self) -> bool:
        """Check if any DEXs are connected."""
        return len(self.connected_dexs) > 0
