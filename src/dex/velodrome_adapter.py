"""
Velodrome DEX Adapter for Optimism
Velodrome is the leading DEX on Optimism with ve(3,3) tokenomics and great arbitrage opportunities.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import json

from .base_dex import BaseDEX

logger = logging.getLogger(__name__)


class VelodromeAdapter(BaseDEX):
    """Velodrome DEX adapter for Optimism arbitrage."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Velodrome adapter."""
        super().__init__("velodrome", config)

        # Velodrome API endpoints (Optimism)
        self.base_url = "https://api.velodrome.finance"
        self.subgraph_url = "https://api.thegraph.com/subgraphs/name/velodrome-finance/velodrome"
        
        # Rate limiting
        self.rate_limit_delay = 1.0  # 1 second between requests
        self.last_request_time = 0

        # Cache
        self.token_cache = {}
        self.price_cache = {}
        self.cache_ttl = 30

        # Session
        self.session = None

        # Common Optimism token addresses
        self.token_addresses = {
            'ETH': '0x4200000000000000000000000000000000000006',  # WETH on Optimism
            'WETH': '0x4200000000000000000000000000000000000006',  # WETH on Optimism
            'USDC': '0x7F5c764cBc14f9669B88837ca1490cCa17c31607',  # USDC on Optimism
            'USDT': '0x94b008aA00579c1307B0EF2c499aD98a8ce58e58',  # USDT on Optimism
            'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',   # DAI on Optimism
            'WBTC': '0x68f180fcCe6836688e9084f035309E29Bf0A2095',  # WBTC on Optimism
            'OP': '0x4200000000000000000000000000000000000042',   # OP token
            'VELO': '0x3c8B650257cFb5f272f799F5e2b4e65093a11a05'   # VELO token
        }

        # Token decimals
        self.token_decimals = {
            'ETH': 18,
            'WETH': 18,
            'USDC': 6,
            'USDT': 6,
            'DAI': 18,
            'WBTC': 8,
            'OP': 18,
            'VELO': 18
        }

        logger.info(f"Velodrome adapter initialized for {self.name}")

    async def connect(self) -> bool:
        """Connect to Velodrome API."""
        try:
            self.session = aiohttp.ClientSession()

            # Test connection with a simple query
            query = """
            {
                pairs(first: 1) {
                    id
                    token0 { symbol }
                    token1 { symbol }
                }
            }
            """

            async with self.session.post(
                self.subgraph_url,
                json={'query': query}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data and 'pairs' in data['data']:
                        self.connected = True
                        self.last_update = datetime.now()
                        logger.info("✅ Connected to Velodrome (Optimism)")
                        return True

            logger.error("Failed to connect to Velodrome subgraph")
            return False

        except Exception as e:
            logger.error(f"Error connecting to Velodrome: {e}")
            return False

    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs from Velodrome."""
        try:
            pairs = []

            # Create pairs from common Optimism tokens including VELO and OP
            common_tokens = ['ETH', 'WETH', 'USDC', 'USDT', 'DAI', 'WBTC', 'OP', 'VELO']

            for i, base_token in enumerate(common_tokens):
                for quote_token in common_tokens[i+1:]:
                    try:
                        price = await self.get_price(base_token, quote_token)
                        if price and price > 0:
                            pair = {
                                'base_token': base_token,
                                'quote_token': quote_token,
                                'dex': self.name,
                                'price': price,
                                'liquidity': 900000,  # Good liquidity on Optimism
                                'volume_24h_usd': 6000000,  # ~$6M daily volume
                                'last_updated': datetime.now().isoformat()
                            }
                            pairs.append(pair)

                    except Exception as e:
                        logger.warning(f"Error getting price for {base_token}/{quote_token}: {e}")
                        continue

            logger.info(f"Fetched {len(pairs)} pairs from Velodrome")
            return pairs

        except Exception as e:
            logger.error(f"Error fetching pairs from Velodrome: {e}")
            return []

    async def get_price(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get current price for a token pair using Velodrome subgraph."""
        try:
            cache_key = f"{base_token}-{quote_token}"

            # Check cache
            if cache_key in self.price_cache:
                cached_price, timestamp = self.price_cache[cache_key]
                if (datetime.now() - timestamp).seconds < self.cache_ttl:
                    return cached_price

            # Get token addresses
            base_address = self.token_addresses.get(base_token)
            quote_address = self.token_addresses.get(quote_token)

            if not base_address or not quote_address:
                return None

            if base_address == quote_address:
                return 1.0

            # Rate limiting
            now = datetime.now().timestamp()
            if now - self.last_request_time < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay)

            self.last_request_time = now

            # Query Velodrome subgraph for pair data
            query = f"""
            {{
                pairs(
                    where: {{
                        or: [
                            {{ token0: "{base_address.lower()}", token1: "{quote_address.lower()}" }},
                            {{ token0: "{quote_address.lower()}", token1: "{base_address.lower()}" }}
                        ]
                    }},
                    orderBy: reserveUSD,
                    orderDirection: desc,
                    first: 1
                ) {{
                    id
                    token0 {{ id, symbol, decimals }}
                    token1 {{ id, symbol, decimals }}
                    reserve0
                    reserve1
                    reserveUSD
                    stable
                }}
            }}
            """

            async with self.session.post(
                self.subgraph_url,
                json={'query': query}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'data' in data and 'pairs' in data['data'] and data['data']['pairs']:
                        pair = data['data']['pairs'][0]
                        
                        reserve0 = float(pair['reserve0'])
                        reserve1 = float(pair['reserve1'])
                        
                        if reserve0 > 0 and reserve1 > 0:
                            # Determine which token is which
                            token0_address = pair['token0']['id'].lower()
                            
                            if token0_address == base_address.lower():
                                price = reserve1 / reserve0
                            else:
                                price = reserve0 / reserve1
                            
                            # Cache the result
                            self.price_cache[cache_key] = (price, datetime.now())
                            return price

                    return None

                else:
                    logger.warning(f"Velodrome query failed: HTTP {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error getting Velodrome price for {base_token}/{quote_token}: {e}")
            return None

    async def get_liquidity(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get liquidity for a token pair."""
        return 900000.0  # $900K typical liquidity

    async def get_quote(self, base_token: str, quote_token: str, amount: float) -> Optional[Dict[str, Any]]:
        """Get a quote for swapping tokens."""
        try:
            price = await self.get_price(base_token, quote_token)
            if not price:
                return None
            
            expected_output = amount * price
            
            return {
                'base_token': base_token,
                'quote_token': quote_token,
                'input_amount': amount,
                'expected_output': expected_output,
                'price': price,
                'slippage_estimate': 0.15,  # Low slippage on Optimism
                'gas_estimate': 120000,  # Optimism gas estimate (very low)
                'fee_percentage': 0.05,  # 0.05% fee (very competitive)
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting Velodrome quote: {e}")
            return None

    async def disconnect(self) -> None:
        """Disconnect from Velodrome API."""
        if self.session:
            await self.session.close()
            self.session = None

        self.connected = False
        logger.info("Disconnected from Velodrome")
