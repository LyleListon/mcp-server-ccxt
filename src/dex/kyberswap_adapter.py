"""
KyberSwap DEX Adapter for Ethereum
KyberSwap is a concentrated liquidity DEX with good arbitrage potential.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import json

from .base_dex import BaseDEX

logger = logging.getLogger(__name__)


class KyberSwapAdapter(BaseDEX):
    """KyberSwap DEX adapter for Ethereum arbitrage."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize KyberSwap adapter."""
        super().__init__("kyberswap", config)

        # KyberSwap API endpoints
        self.base_url = "https://aggregator-api.kyberswap.com/ethereum/api/v1"
        
        # Rate limiting
        self.rate_limit_delay = 1.0  # 1 second between requests
        self.last_request_time = 0

        # Cache
        self.token_cache = {}
        self.price_cache = {}
        self.cache_ttl = 30

        # Session
        self.session = None

        # Common Ethereum token addresses
        self.token_addresses = {
            'ETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # WETH
            'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # WETH
            'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',  # USDC
            'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',  # USDT
            'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',   # DAI
            'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',  # WBTC
            'UNI': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984',   # UNI
            'LINK': '0x514910771AF9Ca656af840dff83E8264EcF986CA'   # LINK
        }

        # Token decimals
        self.token_decimals = {
            'ETH': 18,
            'WETH': 18,
            'USDC': 6,
            'USDT': 6,
            'DAI': 18,
            'WBTC': 8,
            'UNI': 18,
            'LINK': 18
        }

        logger.info(f"KyberSwap adapter initialized for {self.name}")

    async def connect(self) -> bool:
        """Connect to KyberSwap API."""
        try:
            self.session = aiohttp.ClientSession()

            # Test connection with a simple route query
            test_url = f"{self.base_url}/routes"
            params = {
                'tokenIn': self.token_addresses['USDC'],
                'tokenOut': self.token_addresses['WETH'],
                'amountIn': '1000000'  # 1 USDC
            }

            async with self.session.get(test_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data:
                        self.connected = True
                        self.last_update = datetime.now()
                        logger.info("✅ Connected to KyberSwap")
                        return True

            logger.error("Failed to connect to KyberSwap API")
            return False

        except Exception as e:
            logger.error(f"Error connecting to KyberSwap: {e}")
            return False

    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs from KyberSwap."""
        try:
            pairs = []

            # Create pairs from common tokens
            common_tokens = ['ETH', 'WETH', 'USDC', 'USDT', 'DAI', 'WBTC', 'UNI', 'LINK']

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
                                'liquidity': 1000000,  # $1M typical liquidity
                                'volume_24h_usd': 10000000,  # ~$10M daily volume
                                'last_updated': datetime.now().isoformat()
                            }
                            pairs.append(pair)

                    except Exception as e:
                        logger.warning(f"Error getting price for {base_token}/{quote_token}: {e}")
                        continue

            logger.info(f"Fetched {len(pairs)} pairs from KyberSwap")
            return pairs

        except Exception as e:
            logger.error(f"Error fetching pairs from KyberSwap: {e}")
            return []

    async def get_price(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get current price for a token pair using KyberSwap API."""
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

            # Get route from KyberSwap
            url = f"{self.base_url}/routes"
            base_decimals = self.token_decimals.get(base_token, 18)
            amount_in = 10 ** base_decimals  # 1 token

            params = {
                'tokenIn': base_address,
                'tokenOut': quote_address,
                'amountIn': str(amount_in)
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'data' in data and 'routeSummary' in data['data']:
                        route_summary = data['data']['routeSummary']
                        amount_out = int(route_summary.get('amountOut', 0))
                        
                        if amount_out > 0:
                            quote_decimals = self.token_decimals.get(quote_token, 18)
                            price = amount_out / (10 ** quote_decimals)
                            
                            # Cache the result
                            self.price_cache[cache_key] = (price, datetime.now())
                            return price

                    return None

                else:
                    logger.warning(f"KyberSwap query failed: HTTP {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error getting KyberSwap price for {base_token}/{quote_token}: {e}")
            return None

    async def get_liquidity(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get liquidity for a token pair."""
        return 1000000.0  # $1M typical liquidity

    async def get_quote(self, base_token: str, quote_token: str, amount: float) -> Optional[Dict[str, Any]]:
        """Get a quote for swapping tokens."""
        try:
            # Get token addresses
            base_address = self.token_addresses.get(base_token)
            quote_address = self.token_addresses.get(quote_token)

            if not base_address or not quote_address:
                return None

            # Convert amount to wei
            base_decimals = self.token_decimals.get(base_token, 18)
            amount_in = int(amount * (10 ** base_decimals))

            # Rate limiting
            now = datetime.now().timestamp()
            if now - self.last_request_time < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay)

            self.last_request_time = now

            # Get route from KyberSwap
            url = f"{self.base_url}/routes"
            params = {
                'tokenIn': base_address,
                'tokenOut': quote_address,
                'amountIn': str(amount_in)
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'data' in data and 'routeSummary' in data['data']:
                        route_summary = data['data']['routeSummary']
                        amount_out = int(route_summary.get('amountOut', 0))
                        
                        if amount_out > 0:
                            quote_decimals = self.token_decimals.get(quote_token, 18)
                            expected_output = amount_out / (10 ** quote_decimals)
                            price = expected_output / amount
                            
                            return {
                                'base_token': base_token,
                                'quote_token': quote_token,
                                'input_amount': amount,
                                'expected_output': expected_output,
                                'price': price,
                                'slippage_estimate': 0.15,  # Low slippage for concentrated liquidity
                                'gas_estimate': 200000,  # Ethereum gas estimate
                                'fee_percentage': 0.1,  # 0.1% fee (competitive)
                                'timestamp': datetime.now().isoformat()
                            }

            return None
            
        except Exception as e:
            logger.error(f"Error getting KyberSwap quote: {e}")
            return None

    async def disconnect(self) -> None:
        """Disconnect from KyberSwap API."""
        if self.session:
            await self.session.close()
            self.session = None

        self.connected = False
        logger.info("Disconnected from KyberSwap")
