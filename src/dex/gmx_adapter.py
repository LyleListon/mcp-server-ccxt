"""
GMX DEX Adapter
Perpetual trading and spot arbitrage on Arbitrum/Avalanche
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import json

from .base_dex import BaseDEX

logger = logging.getLogger(__name__)


class GMXAdapter(BaseDEX):
    """GMX adapter for perpetual and spot arbitrage."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("gmx", config)
        
        # GMX API endpoints
        self.api_base = "https://api.gmx.io"
        self.arbitrum_api = f"{self.api_base}/prices"
        self.avalanche_api = f"{self.api_base}/avalanche/prices"
        
        # GMX subgraph
        self.subgraph_url = "https://api.thegraph.com/subgraphs/name/gmx-io/gmx-stats"
        
        # Focus on high-volume tokens
        self.target_tokens = [
            'ETH', 'BTC', 'LINK', 'UNI', 'USDC', 'USDT', 'DAI', 'FRAX'
        ]
        
        self.session = None
        logger.info("GMX adapter initialized")

    async def connect(self) -> bool:
        """Connect to GMX APIs."""
        try:
            self.session = aiohttp.ClientSession()
            
            # Test API connection
            async with self.session.get(self.arbitrum_api) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:  # GMX returns price data
                        self.connected = True
                        logger.info("✅ Connected to GMX")
                        return True
                        
            logger.error("Failed to connect to GMX API")
            return False
            
        except Exception as e:
            logger.error(f"Error connecting to GMX: {e}")
            return False

    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get GMX trading pairs."""
        try:
            # Get price data from GMX
            async with self.session.get(self.arbitrum_api) as response:
                if response.status != 200:
                    return []
                    
                price_data = await response.json()
                
                pairs = []
                for token, data in price_data.items():
                    if token in self.target_tokens:
                        # Create USDC pairs for each token
                        pair = {
                            'base_token': token,
                            'quote_token': 'USDC',
                            'dex': self.name,
                            'chain': 'arbitrum',
                            'price': float(data.get('price', 0)),
                            'min_price': float(data.get('minPrice', 0)),
                            'max_price': float(data.get('maxPrice', 0)),
                            'spread_percentage': self._calculate_spread(data),
                            'last_updated': datetime.now().isoformat()
                        }
                        pairs.append(pair)
                        
                logger.info(f"Fetched {len(pairs)} GMX pairs")
                return pairs
                
        except Exception as e:
            logger.error(f"Error fetching GMX pairs: {e}")
            return []

    def _calculate_spread(self, price_data: Dict[str, Any]) -> float:
        """Calculate bid-ask spread percentage."""
        try:
            min_price = float(price_data.get('minPrice', 0))
            max_price = float(price_data.get('maxPrice', 0))
            
            if min_price > 0 and max_price > 0:
                spread = ((max_price - min_price) / min_price) * 100
                return spread
                
            return 0.0
            
        except Exception:
            return 0.0

    async def get_price(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get current price from GMX."""
        try:
            async with self.session.get(self.arbitrum_api) as response:
                if response.status == 200:
                    data = await response.json()
                    token_data = data.get(base_token)
                    if token_data:
                        return float(token_data.get('price', 0))
                        
            return None
            
        except Exception as e:
            logger.error(f"Error getting GMX price: {e}")
            return None

    async def get_liquidity(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get liquidity info from GMX."""
        try:
            # Query GMX subgraph for pool data
            query = f"""
            {{
                tokens(where: {{ symbol: "{base_token}" }}) {{
                    poolAmount
                    reservedAmount
                    usdgAmount
                }}
            }}
            """
            
            async with self.session.post(
                self.subgraph_url,
                json={'query': query}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    tokens = result.get('data', {}).get('tokens', [])
                    if tokens:
                        token = tokens[0]
                        pool_amount = float(token.get('poolAmount', 0))
                        return pool_amount
                        
            return None
            
        except Exception as e:
            logger.error(f"Error getting GMX liquidity: {e}")
            return None

    async def disconnect(self) -> None:
        """Disconnect from GMX."""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False
        logger.info("Disconnected from GMX")
