"""
SushiSwap DEX Adapter for Real Trading

Integrates with SushiSwap for real-time price data and trading execution.
Uses SushiSwap's subgraph and APIs for efficient data fetching.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import json
from decimal import Decimal

from .base_dex import BaseDEX

logger = logging.getLogger(__name__)


class SushiSwapAdapter(BaseDEX):
    """SushiSwap DEX adapter for real trading."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize SushiSwap adapter.
        
        Args:
            config: Configuration including RPC URLs, API keys, etc.
        """
        super().__init__("sushiswap", config)
        
        # SushiSwap subgraph endpoints
        self.subgraph_url = "https://api.thegraph.com/subgraphs/name/sushiswap/exchange"
        
        # Contract addresses (Ethereum mainnet)
        self.factory_address = "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac"
        self.router_address = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"
        
        # Configuration
        self.max_slippage = config.get('max_slippage', 0.5)
        self.gas_limit = config.get('gas_limit', 250000)
        
        # Rate limiting
        self.rate_limit_delay = 0.1
        self.last_request_time = 0
        
        # Cache
        self.pair_cache = {}
        self.cache_ttl = 60
        
        # HTTP session
        self.session = None
        
        logger.info(f"SushiSwap adapter initialized for {self.name}")
    
    async def connect(self) -> bool:
        """Connect to SushiSwap APIs."""
        try:
            self.session = aiohttp.ClientSession()
            
            # Test connection with a simple query
            test_query = """
            {
                pairs(first: 1, orderBy: reserveUSD, orderDirection: desc) {
                    id
                    token0 { symbol }
                    token1 { symbol }
                    reserveUSD
                }
            }
            """
            
            result = await self._query_subgraph(test_query)
            if not result or 'pairs' not in result:
                logger.error("Failed to connect to SushiSwap subgraph")
                return False
            
            self.connected = True
            self.last_update = datetime.now()
            
            logger.info("✅ Connected to SushiSwap successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to SushiSwap: {e}")
            return False
    
    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs from SushiSwap."""
        try:
            query = """
            {
                pairs(
                    first: 100,
                    orderBy: reserveUSD,
                    orderDirection: desc,
                    where: { reserveUSD_gt: "10000" }
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
                    reserve0
                    reserve1
                    reserveUSD
                    volumeUSD
                    token0Price
                    token1Price
                }
            }
            """
            
            result = await self._query_subgraph(query)
            if not result or 'pairs' not in result:
                logger.error("Failed to fetch SushiSwap pairs")
                return []
            
            pairs = []
            for pair in result['pairs']:
                try:
                    pair_data = {
                        'pair_id': pair['id'],
                        'base_token': pair['token0']['symbol'],
                        'quote_token': pair['token1']['symbol'],
                        'base_token_address': pair['token0']['id'],
                        'quote_token_address': pair['token1']['id'],
                        'dex': self.name,
                        'price': float(pair['token0Price']),
                        'reverse_price': float(pair['token1Price']),
                        'liquidity': float(pair['reserveUSD']),
                        'reserve0': float(pair['reserve0']),
                        'reserve1': float(pair['reserve1']),
                        'volume_24h_usd': float(pair['volumeUSD']),
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    pairs.append(pair_data)
                    
                except Exception as e:
                    logger.warning(f"Error processing pair {pair.get('id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Fetched {len(pairs)} SushiSwap pairs")
            return pairs
            
        except Exception as e:
            logger.error(f"Error fetching SushiSwap pairs: {e}")
            return []
    
    async def get_price(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get current price for a token pair."""
        try:
            pair_data = await self._get_pair_data(base_token, quote_token)
            if not pair_data:
                return None
            
            return pair_data.get('price')
            
        except Exception as e:
            logger.error(f"Error getting price for {base_token}/{quote_token}: {e}")
            return None
    
    async def get_liquidity(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get liquidity for a token pair."""
        try:
            pair_data = await self._get_pair_data(base_token, quote_token)
            if not pair_data:
                return None
            
            return pair_data.get('liquidity')
            
        except Exception as e:
            logger.error(f"Error getting liquidity for {base_token}/{quote_token}: {e}")
            return None
    
    async def get_quote(self, base_token: str, quote_token: str, amount: float) -> Optional[Dict[str, Any]]:
        """Get a quote for swapping tokens."""
        try:
            pair_data = await self._get_pair_data(base_token, quote_token)
            if not pair_data:
                return None
            
            # Calculate output using constant product formula
            # For SushiSwap: x * y = k (with 0.3% fee)
            reserve_in = pair_data['reserve0'] if pair_data['token0_symbol'] == base_token else pair_data['reserve1']
            reserve_out = pair_data['reserve1'] if pair_data['token0_symbol'] == base_token else pair_data['reserve0']
            
            # Apply 0.3% fee
            amount_in_with_fee = amount * 997  # 0.3% fee = 997/1000
            numerator = amount_in_with_fee * reserve_out
            denominator = (reserve_in * 1000) + amount_in_with_fee
            
            expected_output = numerator / denominator if denominator > 0 else 0
            
            # Calculate slippage
            simple_price = pair_data['price']
            actual_price = expected_output / amount if amount > 0 else 0
            slippage_estimate = abs(actual_price - simple_price) / simple_price * 100 if simple_price > 0 else 0
            
            return {
                'base_token': base_token,
                'quote_token': quote_token,
                'input_amount': amount,
                'expected_output': expected_output,
                'price': actual_price,
                'market_price': simple_price,
                'slippage_estimate': slippage_estimate,
                'gas_estimate': self.gas_limit,
                'fee_percentage': 0.3,
                'pair_id': pair_data.get('pair_id'),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting quote for {base_token}/{quote_token}: {e}")
            return None
    
    async def _get_pair_data(self, token0: str, token1: str) -> Optional[Dict[str, Any]]:
        """Get pair data for a token pair."""
        cache_key = f"{token0}-{token1}"
        
        # Check cache
        if cache_key in self.pair_cache:
            cached_data, timestamp = self.pair_cache[cache_key]
            if (datetime.now() - timestamp).seconds < self.cache_ttl:
                return cached_data
        
        try:
            query = f"""
            {{
                pairs(
                    where: {{
                        or: [
                            {{ token0_: {{ symbol: "{token0}" }}, token1_: {{ symbol: "{token1}" }} }},
                            {{ token0_: {{ symbol: "{token1}" }}, token1_: {{ symbol: "{token0}" }} }}
                        ]
                    }},
                    orderBy: reserveUSD,
                    orderDirection: desc,
                    first: 1
                ) {{
                    id
                    token0 {{ symbol, decimals }}
                    token1 {{ symbol, decimals }}
                    reserve0
                    reserve1
                    reserveUSD
                    token0Price
                    token1Price
                }}
            }}
            """
            
            result = await self._query_subgraph(query)
            if not result or not result.get('pairs'):
                return None
            
            pair = result['pairs'][0]
            
            # Determine price direction
            price = float(pair['token0Price'])
            if pair['token0']['symbol'] != token0:
                price = float(pair['token1Price'])
            
            pair_data = {
                'pair_id': pair['id'],
                'price': price,
                'liquidity': float(pair['reserveUSD']),
                'reserve0': float(pair['reserve0']),
                'reserve1': float(pair['reserve1']),
                'token0_symbol': pair['token0']['symbol'],
                'token1_symbol': pair['token1']['symbol']
            }
            
            # Cache the result
            self.pair_cache[cache_key] = (pair_data, datetime.now())
            
            return pair_data
            
        except Exception as e:
            logger.error(f"Error getting pair data for {token0}/{token1}: {e}")
            return None
    
    async def _query_subgraph(self, query: str) -> Optional[Dict[str, Any]]:
        """Query SushiSwap subgraph."""
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
                    logger.error(f"SushiSwap subgraph query failed with status {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error querying SushiSwap subgraph: {e}")
            return None
    
    async def disconnect(self) -> None:
        """Disconnect from SushiSwap."""
        if self.session:
            await self.session.close()
            self.session = None
        
        self.connected = False
        logger.info("Disconnected from SushiSwap")
