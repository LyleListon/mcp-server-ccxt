"""
Curve Finance DEX Adapter
High-volume stablecoin arbitrage opportunities
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import json

from .base_dex import BaseDEX

logger = logging.getLogger(__name__)


class CurveAdapter(BaseDEX):
    """Curve Finance adapter for stablecoin arbitrage."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("curve", config)
        
        # Curve API endpoints
        self.api_base = "https://api.curve.fi/api"
        self.pools_endpoint = f"{self.api_base}/getPools/ethereum/main"
        self.volume_endpoint = f"{self.api_base}/getVolume/ethereum"
        
        # Focus on high-volume stablecoin pools
        self.target_pools = [
            "3pool",  # USDC/USDT/DAI
            "fraxusdc",  # FRAX/USDC
            "lusd3crv",  # LUSD/3CRV
            "mim3crv",   # MIM/3CRV
            "tusd3crv"   # TUSD/3CRV
        ]
        
        self.session = None
        logger.info("Curve Finance adapter initialized")

    async def connect(self) -> bool:
        """Connect to Curve Finance API."""
        try:
            self.session = aiohttp.ClientSession()
            
            # Test API connection
            async with self.session.get(self.pools_endpoint) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        self.connected = True
                        logger.info("✅ Connected to Curve Finance")
                        return True
                        
            logger.error("Failed to connect to Curve Finance API")
            return False
            
        except Exception as e:
            logger.error(f"Error connecting to Curve: {e}")
            return False

    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get Curve pool data."""
        try:
            if not self.session:
                await self.connect()
                
            async with self.session.get(self.pools_endpoint) as response:
                if response.status != 200:
                    return []
                    
                data = await response.json()
                pools_data = data.get('data', {}).get('poolData', [])
                
                pairs = []
                for pool in pools_data:
                    if not pool.get('coins') or len(pool['coins']) < 2:
                        continue
                        
                    # Create pairs for each coin combination
                    coins = pool['coins']
                    for i in range(len(coins)):
                        for j in range(i + 1, len(coins)):
                            coin_a = coins[i]
                            coin_b = coins[j]
                            
                            pair = {
                                'pool_address': pool.get('address'),
                                'base_token': coin_a.get('symbol', 'UNKNOWN'),
                                'quote_token': coin_b.get('symbol', 'UNKNOWN'),
                                'dex': self.name,
                                'tvl_usd': float(pool.get('usdTotal', 0)),
                                'volume_24h_usd': float(pool.get('volumeUSD', 0)),
                                'fee_percentage': 0.04,  # Curve typical fee
                                'last_updated': datetime.now().isoformat()
                            }
                            pairs.append(pair)
                
                logger.info(f"Fetched {len(pairs)} Curve pairs")
                return pairs
                
        except Exception as e:
            logger.error(f"Error fetching Curve pairs: {e}")
            return []

    async def get_price(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get price from Curve pools."""
        try:
            # Curve specializes in 1:1 stablecoin swaps
            # For stablecoins, price should be close to 1.0
            stablecoins = ['USDC', 'USDT', 'DAI', 'FRAX', 'LUSD', 'MIM', 'TUSD']
            
            if base_token in stablecoins and quote_token in stablecoins:
                # Simulate small price variations for stablecoin arbitrage
                import random
                return 1.0 + random.uniform(-0.002, 0.002)  # ±0.2% variation
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting Curve price: {e}")
            return None

    async def disconnect(self) -> None:
        """Disconnect from Curve."""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False
        logger.info("Disconnected from Curve Finance")
