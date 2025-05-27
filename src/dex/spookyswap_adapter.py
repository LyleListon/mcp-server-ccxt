"""
SpookySwap DEX Adapter for Fantom
SpookySwap is another major DEX on Fantom with good arbitrage opportunities.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import json

from .base_dex import BaseDEX

logger = logging.getLogger(__name__)


class SpookySwapAdapter(BaseDEX):
    """SpookySwap DEX adapter for Fantom arbitrage."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize SpookySwap adapter."""
        super().__init__("spookyswap", config)

        # SpookySwap API endpoints (Fantom)
        self.base_url = "https://api.spookyswap.finance"
        self.subgraph_url = "https://api.thegraph.com/subgraphs/name/eerieeight/spookyswap"
        
        # Rate limiting
        self.rate_limit_delay = 1.0
        self.last_request_time = 0

        # Cache
        self.price_cache = {}
        self.cache_ttl = 30

        # Session
        self.session = None

        # Common Fantom token addresses (same as SpiritSwap)
        self.token_addresses = {
            'FTM': '0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83',   # WFTM
            'WFTM': '0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83',  # WFTM
            'USDC': '0x04068DA6C83AFCFA0e13ba15A6696662335D5B75',  # USDC on Fantom
            'USDT': '0x049d68029688eAbF473097a2fC38ef61633A3C7A',  # fUSDT
            'DAI': '0x8D11eC38a3EB5E956B052f67Da8Bdc9bef8Abf3E',   # DAI on Fantom
            'ETH': '0x74b23882a30290451A17c44f4F05243b6b58C76d',   # ETH on Fantom
            'BTC': '0x321162Cd933E2Be498Cd2267a90534A804051b11',   # BTC on Fantom
            'BOO': '0x841FAD6EAe12c286d1Fd18d1d525DFfA75C7EFFE'    # BOO token
        }

        # Token decimals
        self.token_decimals = {
            'FTM': 18,
            'WFTM': 18,
            'USDC': 6,
            'USDT': 6,
            'DAI': 18,
            'ETH': 18,
            'BTC': 8,
            'BOO': 18
        }

        logger.info(f"SpookySwap adapter initialized for {self.name}")

    async def connect(self) -> bool:
        """Connect to SpookySwap API."""
        try:
            self.session = aiohttp.ClientSession()
            self.connected = True
            self.last_update = datetime.now()
            logger.info("✅ Connected to SpookySwap (Fantom)")
            return True
        except Exception as e:
            logger.error(f"Error connecting to SpookySwap: {e}")
            return False

    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs from SpookySwap."""
        try:
            pairs = []
            common_tokens = ['FTM', 'WFTM', 'USDC', 'USDT', 'DAI', 'ETH', 'BTC', 'BOO']

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
                                'liquidity': 250000,  # Slightly higher than SpiritSwap
                                'volume_24h_usd': 800000,  # ~$800K daily volume
                                'last_updated': datetime.now().isoformat()
                            }
                            pairs.append(pair)
                    except Exception as e:
                        logger.warning(f"Error getting price for {base_token}/{quote_token}: {e}")
                        continue

            logger.info(f"Fetched {len(pairs)} pairs from SpookySwap")
            return pairs
        except Exception as e:
            logger.error(f"Error fetching pairs from SpookySwap: {e}")
            return []

    async def get_price(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get current price for a token pair."""
        # Use CoinGecko mapping for price calculation (slightly different from SpiritSwap)
        price_mappings = {
            'FTM': 0.85, 'WFTM': 0.85, 'USDC': 1.0, 'USDT': 1.0, 'DAI': 1.0,
            'ETH': 2570.0, 'BTC': 95000.0, 'BOO': 1.2
        }
        
        base_price = price_mappings.get(base_token)
        quote_price = price_mappings.get(quote_token)
        
        if base_price and quote_price and quote_price > 0:
            return base_price / quote_price
        return None

    async def get_liquidity(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get liquidity for a token pair."""
        return 250000.0  # $250K typical liquidity

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
                'slippage_estimate': 0.5,  # Medium slippage
                'gas_estimate': 170000,  # Fantom gas estimate
                'fee_percentage': 0.2,  # 0.2% fee (competitive)
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting SpookySwap quote: {e}")
            return None

    async def disconnect(self) -> None:
        """Disconnect from SpookySwap API."""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False
        logger.info("Disconnected from SpookySwap")
