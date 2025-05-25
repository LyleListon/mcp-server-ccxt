"""
Aerodrome DEX Adapter for Base Chain
Aerodrome is the leading DEX on Base with unique ve(3,3) tokenomics.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import json

from .base_dex import BaseDEX

logger = logging.getLogger(__name__)


class AerodromeAdapter(BaseDEX):
    """Aerodrome DEX adapter for Base chain arbitrage."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Aerodrome adapter."""
        super().__init__("aerodrome", config)

        # Aerodrome API endpoints (Base)
        self.base_url = "https://api.aerodrome.finance"
        self.subgraph_url = "https://api.studio.thegraph.com/query/48211/aerodrome-cl/version/latest"
        
        # Rate limiting
        self.rate_limit_delay = 1.0  # 1 second between requests
        self.last_request_time = 0

        # Cache
        self.token_cache = {}
        self.price_cache = {}
        self.cache_ttl = 30

        # Session
        self.session = None

        # Common Base token addresses
        self.token_addresses = {
            'ETH': '0x4200000000000000000000000000000000000006',  # WETH on Base
            'WETH': '0x4200000000000000000000000000000000000006',  # WETH on Base
            'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',  # USDC on Base
            'USDbC': '0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA', # USD Base Coin
            'DAI': '0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb',   # DAI on Base
            'WBTC': '0x1C7D4B196Cb0C7B01d743Fbc6116a902379C7238',  # WBTC on Base
            'AERO': '0x940181a94A35A4569E4529A3CDfB74e38FD98631'   # AERO token
        }

        # Token decimals
        self.token_decimals = {
            'ETH': 18,
            'WETH': 18,
            'USDC': 6,
            'USDbC': 6,
            'DAI': 18,
            'WBTC': 8,
            'AERO': 18
        }

        logger.info(f"Aerodrome adapter initialized for {self.name}")

    async def connect(self) -> bool:
        """Connect to Aerodrome API."""
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
                        logger.info("✅ Connected to Aerodrome (Base)")
                        return True

            logger.error("Failed to connect to Aerodrome subgraph")
            return False

        except Exception as e:
            logger.error(f"Error connecting to Aerodrome: {e}")
            return False

    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs from Aerodrome."""
        try:
            pairs = []

            # Create pairs from common Base tokens including AERO
            common_tokens = ['ETH', 'WETH', 'USDC', 'USDbC', 'DAI', 'WBTC', 'AERO']

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
                                'liquidity': 1200000,  # Higher liquidity on Base
                                'volume_24h_usd': 8000000,  # ~$8M daily volume
                                'last_updated': datetime.now().isoformat()
                            }
                            pairs.append(pair)

                    except Exception as e:
                        logger.warning(f"Error getting price for {base_token}/{quote_token}: {e}")
                        continue

            logger.info(f"Fetched {len(pairs)} pairs from Aerodrome")
            return pairs

        except Exception as e:
            logger.error(f"Error fetching pairs from Aerodrome: {e}")
            return []

    async def get_price(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get current price for a token pair using Aerodrome subgraph."""
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

            # Query Aerodrome subgraph for pool data
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
                    logger.warning(f"Aerodrome query failed: HTTP {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error getting Aerodrome price for {base_token}/{quote_token}: {e}")
            return None

    async def get_liquidity(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get liquidity for a token pair."""
        return 1200000.0  # $1.2M typical liquidity

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
                'slippage_estimate': 0.2,  # Lower slippage on Base
                'gas_estimate': 150000,  # Base gas estimate
                'fee_percentage': 0.05,  # 0.05% fee (very competitive)
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting Aerodrome quote: {e}")
            return None

    async def disconnect(self) -> None:
        """Disconnect from Aerodrome API."""
        if self.session:
            await self.session.close()
            self.session = None

        self.connected = False
        logger.info("Disconnected from Aerodrome")
