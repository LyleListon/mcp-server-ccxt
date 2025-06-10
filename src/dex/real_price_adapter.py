"""
Real Price Adapter

Uses multiple real price APIs (Coinbase, CoinGecko, etc.) to provide
live market data for arbitrage detection while we develop full DEX integration.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp

from .base_dex import BaseDEX

logger = logging.getLogger(__name__)


class RealPriceAdapter(BaseDEX):
    """Real price adapter using multiple price APIs."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize real price adapter.
        
        Args:
            name: Name of this price source (e.g., 'coinbase', 'coingecko')
            config: Configuration
        """
        super().__init__(name, config)
        
        # API endpoints
        self.coinbase_url = "https://api.coinbase.com/v2/exchange-rates"
        self.coingecko_url = "https://api.coingecko.com/api/v3/simple/price"
        
        # Rate limiting
        self.rate_limit_delay = 1.0  # 1 second between requests
        self.last_request_time = 0
        
        # Cache
        self.price_cache = {}
        self.cache_ttl = 30  # 30 seconds
        
        # Session
        self.session = None
        
        # Token mappings
        self.token_mappings = {
            'coinbase': {
                'BTC': 'BTC',
                'WBTC': 'BTC',
                'ETH': 'ETH',
                'WETH': 'ETH',
                'USDC': 'USD',
                'USDT': 'USD',
                'DAI': 'USD'
            },
            'coingecko': {
                'BTC': 'bitcoin',
                'WBTC': 'bitcoin',
                'ETH': 'ethereum',
                'WETH': 'ethereum',
                'USDC': 'usd-coin',
                'USDT': 'tether',
                'DAI': 'dai'
            }
        }
        
        logger.info(f"Real price adapter initialized for {self.name}")
    
    async def connect(self) -> bool:
        """Connect to price APIs."""
        try:
            self.session = aiohttp.ClientSession()
            
            # Test connection
            if self.name == 'coinbase':
                test_url = f"{self.coinbase_url}?currency=BTC"
            elif self.name == 'coingecko':
                test_url = f"{self.coingecko_url}?ids=bitcoin&vs_currencies=usd"
            else:
                # Generic test
                test_url = "https://httpbin.org/get"
            
            async with self.session.get(test_url) as response:
                if response.status == 200:
                    self.connected = True
                    self.last_update = datetime.now()
                    logger.info(f"✅ Connected to {self.name} price API")
                    return True
                else:
                    logger.error(f"Failed to connect to {self.name}: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error connecting to {self.name}: {e}")
            return False
    
    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs."""
        try:
            # Return common trading pairs with current prices
            common_pairs = [
                ('BTC', 'USDC'),
                ('WBTC', 'USDC'),
                ('ETH', 'USDC'),
                ('WETH', 'USDC'),
                ('ETH', 'USDT'),
                ('BTC', 'USDT'),
                ('USDC', 'USDT'),
                ('DAI', 'USDC')
            ]
            
            pairs = []
            for base_token, quote_token in common_pairs:
                try:
                    price = await self.get_price(base_token, quote_token)
                    if price:
                        pair = {
                            'base_token': base_token,
                            'quote_token': quote_token,
                            'dex': self.name,
                            'price': price,
                            'liquidity': None,  # Real liquidity data not available from price APIs
                            'volume_24h_usd': None,  # Real volume data not available from price APIs
                            'last_updated': datetime.now().isoformat()
                        }
                        pairs.append(pair)
                except Exception as e:
                    logger.warning(f"Error getting price for {base_token}/{quote_token}: {e}")
                    continue
            
            logger.info(f"Fetched {len(pairs)} pairs from {self.name}")
            return pairs
            
        except Exception as e:
            logger.error(f"Error fetching pairs from {self.name}: {e}")
            return []
    
    async def get_price(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get current price for a token pair."""
        try:
            cache_key = f"{base_token}-{quote_token}"
            
            # Check cache
            if cache_key in self.price_cache:
                cached_price, timestamp = self.price_cache[cache_key]
                if (datetime.now() - timestamp).seconds < self.cache_ttl:
                    return cached_price
            
            # Rate limiting
            now = datetime.now().timestamp()
            if now - self.last_request_time < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay)
            
            self.last_request_time = now
            
            price = None
            
            if self.name == 'coinbase':
                price = await self._get_coinbase_price(base_token, quote_token)
            elif self.name == 'coingecko':
                price = await self._get_coingecko_price(base_token, quote_token)
            
            if price:
                # Cache the result
                self.price_cache[cache_key] = (price, datetime.now())
            
            return price
            
        except Exception as e:
            logger.error(f"Error getting price for {base_token}/{quote_token} from {self.name}: {e}")
            return None
    
    async def _get_coinbase_price(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get price from Coinbase API."""
        try:
            # Map tokens to Coinbase symbols
            base_symbol = self.token_mappings['coinbase'].get(base_token, base_token)
            quote_symbol = self.token_mappings['coinbase'].get(quote_token, quote_token)
            
            if base_symbol == quote_symbol:
                return 1.0  # Same token
            
            # Get base token price in USD
            if base_symbol == 'USD':
                base_price_usd = 1.0
            else:
                url = f"{self.coinbase_url}?currency={base_symbol}"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        base_price_usd = float(data['data']['rates']['USD'])
                    else:
                        return None
            
            # Get quote token price in USD
            if quote_symbol == 'USD':
                quote_price_usd = 1.0
            else:
                url = f"{self.coinbase_url}?currency={quote_symbol}"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        quote_price_usd = float(data['data']['rates']['USD'])
                    else:
                        return None
            
            # Calculate cross rate
            if quote_price_usd > 0:
                return base_price_usd / quote_price_usd
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting Coinbase price: {e}")
            return None
    
    async def _get_coingecko_price(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get price from CoinGecko API."""
        try:
            # Map tokens to CoinGecko IDs
            base_id = self.token_mappings['coingecko'].get(base_token)
            quote_id = self.token_mappings['coingecko'].get(quote_token)
            
            if not base_id or not quote_id:
                return None
            
            if base_id == quote_id:
                return 1.0  # Same token
            
            # Get both token prices in USD
            ids = f"{base_id},{quote_id}"
            url = f"{self.coingecko_url}?ids={ids}&vs_currencies=usd"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    base_price_usd = data.get(base_id, {}).get('usd')
                    quote_price_usd = data.get(quote_id, {}).get('usd')
                    
                    if base_price_usd and quote_price_usd:
                        return base_price_usd / quote_price_usd
                    else:
                        return None
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting CoinGecko price: {e}")
            return None
    
    async def get_liquidity(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get liquidity for a token pair (real liquidity data not available from price APIs)."""
        logger.warning(f"Liquidity data not available for {base_token}/{quote_token} from price API")
        return None  # Real liquidity requires DEX-specific queries
    
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
                'slippage_estimate': None,  # Real slippage requires DEX-specific calculation
                'gas_estimate': None,  # Real gas estimate requires DEX-specific calculation
                'fee_percentage': 0.0,  # No fees for price APIs
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting quote from {self.name}: {e}")
            return None
    
    async def disconnect(self) -> None:
        """Disconnect from price APIs."""
        if self.session:
            await self.session.close()
            self.session = None
        
        self.connected = False
        logger.info(f"Disconnected from {self.name}")


class CoinbaseAdapter(RealPriceAdapter):
    """Coinbase price adapter."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("coinbase", config)


class CoinGeckoAdapter(RealPriceAdapter):
    """CoinGecko price adapter."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("coingecko", config)
