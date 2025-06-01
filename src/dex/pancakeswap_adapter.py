"""
PancakeSwap DEX Adapter
BSC's largest DEX for cross-chain arbitrage
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import json

from .base_dex import BaseDEX

logger = logging.getLogger(__name__)


class PancakeSwapAdapter(BaseDEX):
    """PancakeSwap adapter for BSC arbitrage."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("pancakeswap", config)
        
        # PancakeSwap subgraph endpoints
        self.subgraph_urls = [
            "https://api.thegraph.com/subgraphs/name/pancakeswap/exchange",
            "https://proxy-worker-api.pancakeswap.com/bsc-exchange",
            "https://bsc.streamingfast.io/subgraphs/name/pancakeswap/exchange"
        ]
        
        # BSC RPC endpoints
        self.rpc_urls = [
            "https://bsc-dataseed1.binance.org/",
            "https://bsc-dataseed2.binance.org/",
            "https://bsc-dataseed.binance.org/"
        ]
        
        self.session = None
        logger.info("PancakeSwap adapter initialized")

    async def connect(self) -> bool:
        """Connect to PancakeSwap APIs."""
        try:
            self.session = aiohttp.ClientSession()
            
            # Test subgraph connection
            test_query = """
            {
                pairs(first: 1) {
                    id
                    token0 { symbol }
                    token1 { symbol }
                }
            }
            """
            
            result = await self._query_subgraph(test_query)
            if result and 'pairs' in result:
                self.connected = True
                logger.info("✅ Connected to PancakeSwap")
                return True
                
            logger.error("Failed to connect to PancakeSwap")
            return False
            
        except Exception as e:
            logger.error(f"Error connecting to PancakeSwap: {e}")
            return False

    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get PancakeSwap pair data."""
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
                    }
                    token1 {
                        id
                        symbol
                        name
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
                        'chain': 'bsc',
                        'price': float(pair.get('token0Price', 0)),
                        'reserve_0': float(pair.get('reserve0', 0)),
                        'reserve_1': float(pair.get('reserve1', 0)),
                        'tvl_usd': float(pair.get('reserveUSD', 0)),
                        'volume_24h_usd': float(pair.get('volumeUSD', 0)),
                        'fee_percentage': 0.25,  # PancakeSwap standard fee
                        'last_updated': datetime.now().isoformat()
                    }
                    pairs.append(pair_data)
                    
                except Exception as e:
                    logger.warning(f"Error processing PancakeSwap pair: {e}")
                    continue
                    
            logger.info(f"Fetched {len(pairs)} PancakeSwap pairs")
            return pairs
            
        except Exception as e:
            logger.error(f"Error fetching PancakeSwap pairs: {e}")
            return []

    async def _query_subgraph(self, query: str) -> Optional[Dict[str, Any]]:
        """Query PancakeSwap subgraph with fallback."""
        for i, url in enumerate(self.subgraph_urls):
            try:
                async with self.session.post(
                    url,
                    json={'query': query},
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('data')
                        
            except Exception as e:
                logger.warning(f"PancakeSwap subgraph {i} failed: {e}")
                continue
                
        return None

    async def get_price(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get price from PancakeSwap."""
        try:
            # Query specific pair
            query = f"""
            {{
                pairs(
                    where: {{
                        token0_: {{ symbol: "{base_token}" }},
                        token1_: {{ symbol: "{quote_token}" }}
                    }}
                    first: 1
                ) {{
                    token0Price
                    token1Price
                }}
            }}
            """
            
            result = await self._query_subgraph(query)
            if result and result.get('pairs'):
                pair = result['pairs'][0]
                return float(pair.get('token0Price', 0))
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting PancakeSwap price: {e}")
            return None

    async def disconnect(self) -> None:
        """Disconnect from PancakeSwap."""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False
        logger.info("Disconnected from PancakeSwap")
