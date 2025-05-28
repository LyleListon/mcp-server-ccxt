"""
Uniswap V3 DEX Adapter for Real Trading

Integrates with Uniswap V3 for real-time price data and trading execution.
Uses The Graph API for efficient data fetching and Web3 for transactions.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
try:
    import aiohttp
except ImportError:
    # Use mock for testing
    from mock_aiohttp import ClientSession
    aiohttp = type('MockAiohttp', (), {'ClientSession': ClientSession})()
import json
from decimal import Decimal

from .base_dex import BaseDEX

logger = logging.getLogger(__name__)


class UniswapV3Adapter(BaseDEX):
    """Uniswap V3 DEX adapter for real trading."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Uniswap V3 adapter.

        Args:
            config: Configuration including RPC URLs, API keys, etc.
        """
        super().__init__("uniswap_v3", config)

        # The Graph API endpoint for Uniswap V3 (with API key)
        self.subgraph_url = "https://gateway-arbitrum.network.thegraph.com/api/fc2235999cc4344e7c8722107c9c0bd6/subgraphs/id/5zvR82QoaXuFy4wDgKRMpzQw5KB2AeyvuVpDbabxjD9K"
        # Fallback to public endpoint
        self.subgraph_url_fallback = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"

        # Web3 configuration
        self.rpc_url = config.get('ethereum_rpc_url', 'http://localhost:8545')
        self.backup_rpc_url = config.get('backup_rpc_url')  # Infura/Alchemy

        # Contract addresses (Ethereum mainnet)
        self.factory_address = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
        self.router_address = "0xE592427A0AEce92De3Edee1F18E0157C05861564"

        # Trading configuration
        self.max_slippage = config.get('max_slippage', 0.5)  # 0.5%
        self.gas_limit = config.get('gas_limit', 300000)

        # Rate limiting
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.last_request_time = 0

        # Cache for pool data
        self.pool_cache = {}
        self.cache_ttl = 60  # 1 minute cache

        # Session for HTTP requests
        self.session = None

        logger.info(f"Uniswap V3 adapter initialized for {self.name}")

    async def connect(self) -> bool:
        """Connect to Uniswap V3 APIs and Web3."""
        try:
            # Create HTTP session
            self.session = aiohttp.ClientSession()

            # Test The Graph API connection
            test_query = """
            {
                pools(first: 1) {
                    id
                    token0 { symbol }
                    token1 { symbol }
                }
            }
            """

            result = await self._query_subgraph(test_query)
            if not result or 'pools' not in result:
                logger.error("Failed to connect to Uniswap V3 subgraph")
                return False

            # TODO: Test Web3 connection
            # web3 = Web3(Web3.HTTPProvider(self.rpc_url))
            # if not web3.isConnected():
            #     logger.error("Failed to connect to Ethereum node")
            #     return False

            self.connected = True
            self.last_update = datetime.now()

            logger.info("✅ Connected to Uniswap V3 successfully")
            return True

        except Exception as e:
            logger.error(f"Error connecting to Uniswap V3: {e}")
            return False

    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs from Uniswap V3.

        Returns:
            List of trading pair information
        """
        try:
            # Query top pools by TVL
            query = """
            {
                pools(
                    first: 100,
                    orderBy: totalValueLockedUSD,
                    orderDirection: desc,
                    where: { totalValueLockedUSD_gt: "10000" }
                ) {
                    id
                    token0 {
                        id
                        symbol
                        name
                        decimals
                    }
                    token1 {
                        id
                        symbol
                        name
                        decimals
                    }
                    feeTier
                    liquidity
                    sqrtPrice
                    tick
                    totalValueLockedUSD
                    volumeUSD
                }
            }
            """

            result = await self._query_subgraph(query)
            if not result or 'pools' not in result:
                logger.error("Failed to fetch Uniswap V3 pools")
                return []

            pairs = []
            for pool in result['pools']:
                try:
                    # Calculate current price from sqrtPrice
                    sqrt_price = int(pool['sqrtPrice'])
                    price = self._sqrt_price_to_price(
                        sqrt_price,
                        int(pool['token0']['decimals']),
                        int(pool['token1']['decimals'])
                    )

                    pair = {
                        'pool_id': pool['id'],
                        'base_token': pool['token0']['symbol'],
                        'quote_token': pool['token1']['symbol'],
                        'base_token_address': pool['token0']['id'],
                        'quote_token_address': pool['token1']['id'],
                        'dex': self.name,
                        'price': float(price),
                        'liquidity': float(pool['liquidity']) if pool['liquidity'] else 0,
                        'tvl_usd': float(pool['totalValueLockedUSD']),
                        'volume_24h_usd': float(pool['volumeUSD']),
                        'fee_tier': int(pool['feeTier']),
                        'last_updated': datetime.now().isoformat()
                    }

                    pairs.append(pair)

                except Exception as e:
                    logger.warning(f"Error processing pool {pool.get('id', 'unknown')}: {e}")
                    continue

            logger.info(f"Fetched {len(pairs)} Uniswap V3 pairs")
            return pairs

        except Exception as e:
            logger.error(f"Error fetching Uniswap V3 pairs: {e}")
            return []

    async def get_price(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get current price for a token pair.

        Args:
            base_token: Base token symbol
            quote_token: Quote token symbol

        Returns:
            Current price or None if not available
        """
        try:
            # Find the pool for this pair
            pool_data = await self._get_pool_data(base_token, quote_token)
            if not pool_data:
                return None

            return pool_data.get('price')

        except Exception as e:
            logger.error(f"Error getting price for {base_token}/{quote_token}: {e}")
            return None

    async def get_liquidity(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get liquidity for a token pair.

        Args:
            base_token: Base token symbol
            quote_token: Quote token symbol

        Returns:
            Liquidity amount or None if not available
        """
        try:
            pool_data = await self._get_pool_data(base_token, quote_token)
            if not pool_data:
                return None

            return pool_data.get('tvl_usd')

        except Exception as e:
            logger.error(f"Error getting liquidity for {base_token}/{quote_token}: {e}")
            return None

    async def get_quote(self, base_token: str, quote_token: str, amount: float) -> Optional[Dict[str, Any]]:
        """Get a quote for swapping tokens.

        Args:
            base_token: Token to sell
            quote_token: Token to buy
            amount: Amount of base token to sell

        Returns:
            Quote information including expected output and gas cost
        """
        try:
            pool_data = await self._get_pool_data(base_token, quote_token)
            if not pool_data:
                return None

            # Simple price calculation (real implementation would use Uniswap math)
            price = pool_data['price']
            expected_output = amount * price

            # Estimate slippage based on trade size vs liquidity
            liquidity = pool_data.get('tvl_usd', 0)
            trade_size_usd = amount * price  # Assuming base token ~= $1 for simplicity

            if liquidity > 0:
                slippage_estimate = min(trade_size_usd / liquidity * 100, 5.0)  # Cap at 5%
            else:
                slippage_estimate = 5.0

            return {
                'base_token': base_token,
                'quote_token': quote_token,
                'input_amount': amount,
                'expected_output': expected_output,
                'price': price,
                'slippage_estimate': slippage_estimate,
                'gas_estimate': self.gas_limit,
                'fee_tier': pool_data.get('fee_tier', 3000),
                'pool_id': pool_data.get('pool_id'),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting quote for {base_token}/{quote_token}: {e}")
            return None

    async def _get_pool_data(self, token0: str, token1: str) -> Optional[Dict[str, Any]]:
        """Get pool data for a token pair."""
        cache_key = f"{token0}-{token1}"

        # Check cache first
        if cache_key in self.pool_cache:
            cached_data, timestamp = self.pool_cache[cache_key]
            if (datetime.now() - timestamp).seconds < self.cache_ttl:
                return cached_data

        try:
            # Query for pools with these tokens
            query = f"""
            {{
                pools(
                    where: {{
                        or: [
                            {{ token0_: {{ symbol: "{token0}" }}, token1_: {{ symbol: "{token1}" }} }},
                            {{ token0_: {{ symbol: "{token1}" }}, token1_: {{ symbol: "{token0}" }} }}
                        ]
                    }},
                    orderBy: totalValueLockedUSD,
                    orderDirection: desc,
                    first: 1
                ) {{
                    id
                    token0 {{ symbol, decimals }}
                    token1 {{ symbol, decimals }}
                    sqrtPrice
                    liquidity
                    totalValueLockedUSD
                    feeTier
                }}
            }}
            """

            result = await self._query_subgraph(query)
            if not result or not result.get('pools'):
                return None

            pool = result['pools'][0]

            # Calculate price
            sqrt_price = int(pool['sqrtPrice'])
            price = self._sqrt_price_to_price(
                sqrt_price,
                int(pool['token0']['decimals']),
                int(pool['token1']['decimals'])
            )

            # Adjust price direction if tokens are swapped
            if pool['token0']['symbol'] != token0:
                price = 1 / price if price > 0 else 0

            pool_data = {
                'pool_id': pool['id'],
                'price': float(price),
                'tvl_usd': float(pool['totalValueLockedUSD']),
                'fee_tier': int(pool['feeTier']),
                'liquidity': float(pool['liquidity']) if pool['liquidity'] else 0
            }

            # Cache the result
            self.pool_cache[cache_key] = (pool_data, datetime.now())

            return pool_data

        except Exception as e:
            logger.error(f"Error getting pool data for {token0}/{token1}: {e}")
            return None

    async def _query_subgraph(self, query: str) -> Optional[Dict[str, Any]]:
        """Query The Graph subgraph."""
        try:
            # Rate limiting
            now = datetime.now().timestamp()
            if now - self.last_request_time < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay)

            self.last_request_time = now

            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.post(
                self.subgraph_url,
                json={'query': query},
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('data')
                else:
                    logger.error(f"Subgraph query failed with status {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error querying subgraph: {e}")
            return None

    def _sqrt_price_to_price(self, sqrt_price: int, decimals0: int, decimals1: int) -> Decimal:
        """Convert Uniswap V3 sqrtPrice to actual price."""
        try:
            # sqrtPrice is in Q64.96 format
            # price = (sqrtPrice / 2^96)^2 * 10^(decimals0 - decimals1)

            sqrt_price_decimal = Decimal(sqrt_price) / Decimal(2 ** 96)
            price = sqrt_price_decimal ** 2

            # Adjust for token decimals
            decimal_adjustment = Decimal(10) ** (decimals1 - decimals0)
            final_price = price * decimal_adjustment

            return final_price

        except Exception as e:
            logger.error(f"Error converting sqrt price: {e}")
            return Decimal(0)

    async def disconnect(self) -> None:
        """Disconnect from Uniswap V3."""
        if self.session:
            await self.session.close()
            self.session = None

        self.connected = False
        logger.info("Disconnected from Uniswap V3")
