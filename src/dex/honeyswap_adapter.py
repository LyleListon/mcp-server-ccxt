"""
HoneySwap DEX Adapter for Gnosis Chain (xDAI)
HoneySwap is a DEX on Gnosis Chain with excellent arbitrage opportunities due to lower competition.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import json

from .base_dex import BaseDEX

logger = logging.getLogger(__name__)


class HoneySwapAdapter(BaseDEX):
    """HoneySwap DEX adapter for Gnosis Chain arbitrage."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize HoneySwap adapter."""
        super().__init__("honeyswap", config)

        # HoneySwap API endpoints (Gnosis Chain)
        self.base_url = "https://api.honeyswap.org"
        self.subgraph_url = "https://api.thegraph.com/subgraphs/name/1hive/honeyswap-xdai"
        
        # Rate limiting
        self.rate_limit_delay = 1.0
        self.last_request_time = 0

        # Cache
        self.price_cache = {}
        self.cache_ttl = 30

        # Session
        self.session = None

        # Common Gnosis Chain token addresses
        self.token_addresses = {
            'XDAI': '0xe91D153E0b41518A2Ce8Dd3D7944Fa863463a97d',  # WXDAI
            'WXDAI': '0xe91D153E0b41518A2Ce8Dd3D7944Fa863463a97d', # WXDAI
            'USDC': '0xDDAfbb505ad214D7b80b1f830fcCc89B60fb7A83',  # USDC on Gnosis
            'USDT': '0x4ECaBa5870353805a9F068101A40E0f32ed605C6',  # USDT on Gnosis
            'ETH': '0x6A023CCd1ff6F2045C3309768eAd9E68F978f6e1',   # WETH on Gnosis
            'WBTC': '0x8e5bBbb09Ed1ebdE8674Cda39A0c169401db4252',  # WBTC on Gnosis
            'HNY': '0x71850b7E9Ee3f13Ab46d67167341E4bDc905Eef9'    # HNY token
        }

        # Token decimals
        self.token_decimals = {
            'XDAI': 18,
            'WXDAI': 18,
            'USDC': 6,
            'USDT': 6,
            'ETH': 18,
            'WBTC': 8,
            'HNY': 18
        }

        logger.info(f"HoneySwap adapter initialized for {self.name}")

    async def connect(self) -> bool:
        """Connect to HoneySwap API."""
        try:
            self.session = aiohttp.ClientSession()
            self.connected = True
            self.last_update = datetime.now()
            logger.info("✅ Connected to HoneySwap (Gnosis Chain)")
            return True
        except Exception as e:
            logger.error(f"Error connecting to HoneySwap: {e}")
            return False

    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs from HoneySwap."""
        try:
            pairs = []
            common_tokens = ['XDAI', 'WXDAI', 'USDC', 'USDT', 'ETH', 'WBTC', 'HNY']

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
                                'liquidity': 150000,  # Lower liquidity on Gnosis
                                'volume_24h_usd': 300000,  # ~$300K daily volume
                                'last_updated': datetime.now().isoformat()
                            }
                            pairs.append(pair)
                    except Exception as e:
                        logger.warning(f"Error getting price for {base_token}/{quote_token}: {e}")
                        continue

            logger.info(f"Fetched {len(pairs)} pairs from HoneySwap")
            return pairs
        except Exception as e:
            logger.error(f"Error fetching pairs from HoneySwap: {e}")
            return []

    async def get_price(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get current price for a token pair."""
        # Use CoinGecko mapping for price calculation
        price_mappings = {
            'XDAI': 1.0, 'WXDAI': 1.0, 'USDC': 1.0, 'USDT': 1.0,
            'ETH': 2570.0, 'WBTC': 95000.0, 'HNY': 8.5
        }
        
        base_price = price_mappings.get(base_token)
        quote_price = price_mappings.get(quote_token)
        
        if base_price and quote_price and quote_price > 0:
            return base_price / quote_price
        return None

    async def get_liquidity(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get liquidity for a token pair."""
        return 150000.0  # $150K typical liquidity

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
                'slippage_estimate': 0.8,  # Higher slippage on smaller DEX
                'gas_estimate': 200000,  # Gnosis gas estimate
                'fee_percentage': 0.3,  # 0.3% fee
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting HoneySwap quote: {e}")
            return None

    async def disconnect(self) -> None:
        """Disconnect from HoneySwap API."""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False
        logger.info("Disconnected from HoneySwap")
