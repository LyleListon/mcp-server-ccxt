"""
Thena DEX Adapter for BNB Chain
Thena is a ve(3,3) DEX on BNB Chain with excellent arbitrage opportunities and lower competition.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import json

from .base_dex import BaseDEX

logger = logging.getLogger(__name__)


class ThenaAdapter(BaseDEX):
    """Thena DEX adapter for BNB Chain arbitrage."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Thena adapter."""
        super().__init__("thena", config)

        # Thena API endpoints (BNB Chain)
        self.base_url = "https://api.thena.fi"
        self.subgraph_url = "https://api.thegraph.com/subgraphs/name/thenaursa/thena"
        
        # Rate limiting
        self.rate_limit_delay = 1.0  # 1 second between requests
        self.last_request_time = 0

        # Cache
        self.token_cache = {}
        self.price_cache = {}
        self.cache_ttl = 30

        # Session
        self.session = None

        # Common BNB Chain token addresses
        self.token_addresses = {
            'BNB': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',   # WBNB
            'WBNB': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',  # WBNB
            'USDT': '0x55d398326f99059fF775485246999027B3197955',  # USDT on BSC
            'USDC': '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',  # USDC on BSC
            'BUSD': '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56',  # BUSD
            'ETH': '0x2170Ed0880ac9A755fd29B2688956BD959F933F8',   # ETH on BSC
            'BTCB': '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c',  # BTCB
            'THE': '0xF4C8E32EaDEC4BFe97E0F595AdD0f4450a863a11'    # THE token
        }

        # Token decimals
        self.token_decimals = {
            'BNB': 18,
            'WBNB': 18,
            'USDT': 18,
            'USDC': 18,
            'BUSD': 18,
            'ETH': 18,
            'BTCB': 18,
            'THE': 18
        }

        logger.info(f"Thena adapter initialized for {self.name}")

    async def connect(self) -> bool:
        """Connect to Thena API."""
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
                        logger.info("✅ Connected to Thena (BNB Chain)")
                        return True

            logger.error("Failed to connect to Thena subgraph")
            return False

        except Exception as e:
            logger.error(f"Error connecting to Thena: {e}")
            return False

    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs from Thena."""
        try:
            pairs = []

            # Create pairs from common BNB Chain tokens including THE
            common_tokens = ['BNB', 'WBNB', 'USDT', 'USDC', 'BUSD', 'ETH', 'BTCB', 'THE']

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
                                'liquidity': 400000,  # Smaller DEX, lower liquidity
                                'volume_24h_usd': 1500000,  # ~$1.5M daily volume
                                'last_updated': datetime.now().isoformat()
                            }
                            pairs.append(pair)

                    except Exception as e:
                        logger.warning(f"Error getting price for {base_token}/{quote_token}: {e}")
                        continue

            logger.info(f"Fetched {len(pairs)} pairs from Thena")
            return pairs

        except Exception as e:
            logger.error(f"Error fetching pairs from Thena: {e}")
            return []

    async def get_price(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get current price for a token pair using Thena subgraph."""
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

            # Query Thena subgraph for pair data
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
                    logger.warning(f"Thena query failed: HTTP {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error getting Thena price for {base_token}/{quote_token}: {e}")
            return None

    async def get_liquidity(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get liquidity for a token pair."""
        return 400000.0  # $400K typical liquidity for smaller DEX

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
                'slippage_estimate': 0.4,  # Higher slippage for smaller DEX
                'gas_estimate': 250000,  # BNB Chain gas estimate
                'fee_percentage': 0.2,  # 0.2% fee
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting Thena quote: {e}")
            return None

    async def disconnect(self) -> None:
        """Disconnect from Thena API."""
        if self.session:
            await self.session.close()
            self.session = None

        self.connected = False
        logger.info("Disconnected from Thena")
