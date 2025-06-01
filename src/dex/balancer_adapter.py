"""
Balancer DEX Adapter
Multi-token pool arbitrage opportunities
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import json

from .base_dex import BaseDEX

logger = logging.getLogger(__name__)


class BalancerAdapter(BaseDEX):
    """Balancer DEX adapter for multi-token arbitrage."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("balancer", config)
        
        # Balancer subgraph endpoints
        self.subgraph_urls = [
            "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-v2",
            "https://api.studio.thegraph.com/query/24660/balancer-v2/version/latest"
        ]
        self.current_url_index = 0
        
        # Focus on high-volume pools
        self.min_tvl = 100000  # $100k minimum TVL
        
        self.session = None
        logger.info("Balancer adapter initialized")

    async def connect(self) -> bool:
        """Connect to Balancer subgraph."""
        try:
            self.session = aiohttp.ClientSession()
            
            # Test subgraph connection
            test_query = """
            {
                pools(first: 1) {
                    id
                    tokens { symbol }
                }
            }
            """
            
            result = await self._query_subgraph(test_query)
            if result and 'pools' in result:
                self.connected = True
                logger.info("✅ Connected to Balancer")
                return True
                
            logger.error("Failed to connect to Balancer subgraph")
            return False
            
        except Exception as e:
            logger.error(f"Error connecting to Balancer: {e}")
            return False

    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get Balancer pool data."""
        try:
            query = """
            {
                pools(
                    first: 100,
                    orderBy: totalLiquidity,
                    orderDirection: desc,
                    where: { totalLiquidity_gt: "100000" }
                ) {
                    id
                    address
                    poolType
                    swapFee
                    totalLiquidity
                    totalSwapVolume
                    tokens {
                        address
                        symbol
                        balance
                        weight
                    }
                }
            }
            """
            
            result = await self._query_subgraph(query)
            if not result or 'pools' not in result:
                return []
                
            pairs = []
            for pool in result['pools']:
                tokens = pool.get('tokens', [])
                if len(tokens) < 2:
                    continue
                    
                # Create pairs for each token combination
                for i in range(len(tokens)):
                    for j in range(i + 1, len(tokens)):
                        token_a = tokens[i]
                        token_b = tokens[j]
                        
                        pair = {
                            'pool_id': pool['id'],
                            'pool_address': pool['address'],
                            'base_token': token_a.get('symbol', 'UNKNOWN'),
                            'quote_token': token_b.get('symbol', 'UNKNOWN'),
                            'dex': self.name,
                            'pool_type': pool.get('poolType', 'Weighted'),
                            'tvl_usd': float(pool.get('totalLiquidity', 0)),
                            'volume_24h_usd': float(pool.get('totalSwapVolume', 0)),
                            'fee_percentage': float(pool.get('swapFee', 0)) * 100,
                            'weight_a': float(token_a.get('weight', 0.5)),
                            'weight_b': float(token_b.get('weight', 0.5)),
                            'last_updated': datetime.now().isoformat()
                        }
                        pairs.append(pair)
                        
            logger.info(f"Fetched {len(pairs)} Balancer pairs")
            return pairs
            
        except Exception as e:
            logger.error(f"Error fetching Balancer pairs: {e}")
            return []

    async def _query_subgraph(self, query: str) -> Optional[Dict[str, Any]]:
        """Query Balancer subgraph with fallback."""
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
                logger.warning(f"Balancer subgraph {i} failed: {e}")
                continue
                
        return None

    async def get_price(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get price from Balancer pools."""
        try:
            # Simplified price calculation
            # Real implementation would use Balancer math
            import random
            return random.uniform(0.95, 1.05)  # Mock price variation
            
        except Exception as e:
            logger.error(f"Error getting Balancer price: {e}")
            return None

    async def disconnect(self) -> None:
        """Disconnect from Balancer."""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False
        logger.info("Disconnected from Balancer")
