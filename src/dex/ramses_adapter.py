"""
Ramses DEX Adapter for Arbitrum
Ramses is a newer ve(3,3) DEX on Arbitrum with excellent arbitrage opportunities due to lower competition.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import json

from .base_dex import BaseDEX

logger = logging.getLogger(__name__)


class RamsesAdapter(BaseDEX):
    """Ramses DEX adapter for Arbitrum arbitrage."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Ramses adapter."""
        super().__init__("ramses", config)

        # Ramses API endpoints (Arbitrum)
        self.base_url = "https://api.ramses.exchange"
        self.subgraph_url = "https://api.thegraph.com/subgraphs/name/ramsesexchange/concentrated-liquidity-graph"
        
        # Rate limiting
        self.rate_limit_delay = 1.0  # 1 second between requests
        self.last_request_time = 0

        # Cache
        self.token_cache = {}
        self.price_cache = {}
        self.cache_ttl = 30

        # Session
        self.session = None

        # Common Arbitrum token addresses
        self.token_addresses = {
            'ETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',  # WETH on Arbitrum
            'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',  # WETH on Arbitrum
            'USDC': '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',  # USDC on Arbitrum
            'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',  # USDT on Arbitrum
            'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',   # DAI on Arbitrum
            'WBTC': '0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f',  # WBTC on Arbitrum
            'ARB': '0x912CE59144191C1204E64559FE8253a0e49E6548',   # ARB token
            'RAM': '0xAAA6C1E32C55A7Bfa8066A6FAE9b42650F262418'    # RAM token
        }

        # Token decimals
        self.token_decimals = {
            'ETH': 18,
            'WETH': 18,
            'USDC': 6,
            'USDT': 6,
            'DAI': 18,
            'WBTC': 8,
            'ARB': 18,
            'RAM': 18
        }

        logger.info(f"Ramses adapter initialized for {self.name}")

    async def connect(self) -> bool:
        """Connect to Ramses API."""
        try:
            self.session = aiohttp.ClientSession()

            # Test connection with a simple query
            query = """
            {
                pools(first: 1) {
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
                    if 'data' in data and 'pools' in data['data']:
                        self.connected = True
                        self.last_update = datetime.now()
                        logger.info("✅ Connected to Ramses (Arbitrum)")
                        return True

            logger.error("Failed to connect to Ramses subgraph")
            return False

        except Exception as e:
            logger.error(f"Error connecting to Ramses: {e}")
            return False

    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs from Ramses."""
        try:
            pairs = []

            # Create pairs from common Arbitrum tokens including RAM
            common_tokens = ['ETH', 'WETH', 'USDC', 'USDT', 'DAI', 'WBTC', 'ARB', 'RAM']

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
                                'liquidity': 300000,  # Newer DEX, lower liquidity but great opportunities
                                'volume_24h_usd': 800000,  # ~$800K daily volume
                                'last_updated': datetime.now().isoformat()
                            }
                            pairs.append(pair)

                    except Exception as e:
                        logger.warning(f"Error getting price for {base_token}/{quote_token}: {e}")
                        continue

            logger.info(f"Fetched {len(pairs)} pairs from Ramses")
            return pairs

        except Exception as e:
            logger.error(f"Error fetching pairs from Ramses: {e}")
            return []

    async def get_price(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get current price for a token pair using Ramses subgraph."""
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

            # Query Ramses subgraph for pool data
            query = f"""
            {{
                pools(
                    where: {{
                        or: [
                            {{ token0: "{base_address.lower()}", token1: "{quote_address.lower()}" }},
                            {{ token0: "{quote_address.lower()}", token1: "{base_address.lower()}" }}
                        ]
                    }},
                    orderBy: totalValueLockedUSD,
                    orderDirection: desc,
                    first: 1
                ) {{
                    id
                    token0 {{ id, symbol, decimals }}
                    token1 {{ id, symbol, decimals }}
                    totalValueLockedToken0
                    totalValueLockedToken1
                    totalValueLockedUSD
                    volumeUSD
                }}
            }}
            """

            async with self.session.post(
                self.subgraph_url,
                json={'query': query}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'data' in data and 'pools' in data['data'] and data['data']['pools']:
                        pool = data['data']['pools'][0]
                        
                        tvl0 = float(pool['totalValueLockedToken0'])
                        tvl1 = float(pool['totalValueLockedToken1'])
                        
                        if tvl0 > 0 and tvl1 > 0:
                            # Determine which token is which
                            token0_address = pool['token0']['id'].lower()
                            
                            if token0_address == base_address.lower():
                                price = tvl1 / tvl0
                            else:
                                price = tvl0 / tvl1
                            
                            # Cache the result
                            self.price_cache[cache_key] = (price, datetime.now())
                            return price

                    return None

                else:
                    logger.warning(f"Ramses query failed: HTTP {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error getting Ramses price for {base_token}/{quote_token}: {e}")
            return None

    async def get_liquidity(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get liquidity for a token pair."""
        return 300000.0  # $300K typical liquidity for newer DEX

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
                'slippage_estimate': 0.5,  # Higher slippage for newer/smaller DEX
                'gas_estimate': 220000,  # Arbitrum gas estimate
                'fee_percentage': 0.3,  # 0.3% fee
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting Ramses quote: {e}")
            return None

    async def disconnect(self) -> None:
        """Disconnect from Ramses API."""
        if self.session:
            await self.session.close()
            self.session = None

        self.connected = False
        logger.info("Disconnected from Ramses")
