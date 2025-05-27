"""
Real Price Feeds System
Multi-source real-time price feeds for cross-chain arbitrage.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class RealPriceFeeds:
    """Real-time price feeds from multiple sources."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize real price feeds."""
        self.config = config
        
        # Price feed sources with priorities
        self.sources = {
            'coingecko': {
                'url': 'https://api.coingecko.com/api/v3',
                'priority': 1,
                'rate_limit': 1.0,
                'enabled': True,
                'chains': ['ethereum', 'arbitrum', 'optimism', 'base', 'polygon', 'bsc', 'avalanche']
            },
            'defillama': {
                'url': 'https://coins.llama.fi',
                'priority': 2,
                'rate_limit': 0.5,
                'enabled': True,
                'chains': ['ethereum', 'arbitrum', 'optimism', 'polygon', 'bsc', 'avalanche']
            },
            'dexscreener': {
                'url': 'https://api.dexscreener.com/latest',
                'priority': 3,
                'rate_limit': 1.0,
                'enabled': True,
                'chains': ['ethereum', 'arbitrum', 'optimism', 'base', 'polygon', 'bsc']
            },
            'moralis': {
                'url': 'https://deep-index.moralis.io/api/v2',
                'priority': 4,
                'rate_limit': 2.0,
                'enabled': False,  # Requires API key
                'chains': ['ethereum', 'arbitrum', 'optimism', 'polygon', 'bsc']
            }
        }
        
        # Token contract addresses per chain
        self.token_addresses = {
            'ethereum': {
                'ETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # WETH
                'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
                'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
                'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
                'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599'
            },
            'arbitrum': {
                'ETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',  # WETH
                'USDC': '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
                'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
                'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',
                'WBTC': '0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f'
            },
            'optimism': {
                'ETH': '0x4200000000000000000000000000000000000006',  # WETH
                'USDC': '0x7F5c764cBc14f9669B88837ca1490cCa17c31607',
                'USDT': '0x94b008aA00579c1307B0EF2c499aD98a8ce58e58',
                'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',
                'WBTC': '0x68f180fcCe6836688e9084f035309E29Bf0A2095'
            },
            'base': {
                'ETH': '0x4200000000000000000000000000000000000006',  # WETH
                'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
                'USDbC': '0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA',  # Bridged USDC
                'DAI': '0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb'
            },
            'polygon': {
                'MATIC': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',  # WMATIC
                'ETH': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',  # WETH
                'USDC': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
                'USDT': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
                'DAI': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063'
            },
            'bsc': {
                'BNB': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',  # WBNB
                'ETH': '0x2170Ed0880ac9A755fd29B2688956BD959F933F8',
                'USDC': '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
                'USDT': '0x55d398326f99059fF775485246999027B3197955',
                'DAI': '0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3'
            }
        }
        
        # CoinGecko token ID mappings
        self.coingecko_ids = {
            'ETH': 'ethereum',
            'USDC': 'usd-coin',
            'USDT': 'tether',
            'DAI': 'dai',
            'WBTC': 'wrapped-bitcoin',
            'MATIC': 'matic-network',
            'BNB': 'binancecoin'
        }
        
        # Price cache
        self.price_cache = {}
        self.cache_ttl = 30  # 30 seconds
        
        # Rate limiting
        self.last_requests = {}
        
        # Session
        self.session = None
        
        logger.info("Real price feeds initialized")

    async def connect(self) -> bool:
        """Connect to price feed sources."""
        try:
            self.session = aiohttp.ClientSession()
            
            # Test CoinGecko connection
            async with self.session.get(f"{self.sources['coingecko']['url']}/ping") as response:
                if response.status == 200:
                    logger.info("✅ Connected to CoinGecko API")
                    return True
            
            logger.error("Failed to connect to primary price source")
            return False
            
        except Exception as e:
            logger.error(f"Error connecting to price feeds: {e}")
            return False

    async def get_cross_chain_prices(self, tokens: List[str] = None) -> Dict[str, Dict[str, float]]:
        """Get prices for tokens across all supported chains."""
        try:
            if tokens is None:
                tokens = ['ETH', 'USDC', 'USDT', 'DAI']
            
            cross_chain_prices = {}
            
            # Get prices from CoinGecko (most reliable)
            coingecko_prices = await self._get_coingecko_prices(tokens)
            
            # Get chain-specific prices from DexScreener
            dexscreener_prices = await self._get_dexscreener_prices(tokens)
            
            # Combine and validate prices
            for token in tokens:
                cross_chain_prices[token] = {}
                
                # Use CoinGecko as base price
                base_price = coingecko_prices.get(token)
                if not base_price:
                    continue
                
                # Add prices for each chain where token exists
                for chain in self.token_addresses.keys():
                    if token in self.token_addresses[chain]:
                        # Start with CoinGecko price
                        chain_price = base_price
                        
                        # Apply DexScreener price if available (more accurate for specific chains)
                        dex_price = dexscreener_prices.get(f"{token}_{chain}")
                        if dex_price and abs(dex_price - base_price) / base_price < 0.05:  # Within 5%
                            chain_price = dex_price
                        
                        cross_chain_prices[token][chain] = chain_price
            
            return cross_chain_prices
            
        except Exception as e:
            logger.error(f"Error getting cross-chain prices: {e}")
            return {}

    async def _get_coingecko_prices(self, tokens: List[str]) -> Dict[str, float]:
        """Get prices from CoinGecko API."""
        try:
            # Rate limiting
            await self._rate_limit('coingecko')
            
            # Map tokens to CoinGecko IDs
            token_ids = []
            for token in tokens:
                if token in self.coingecko_ids:
                    token_ids.append(self.coingecko_ids[token])
            
            if not token_ids:
                return {}
            
            # Fetch prices
            url = f"{self.sources['coingecko']['url']}/simple/price"
            params = {
                'ids': ','.join(token_ids),
                'vs_currencies': 'usd',
                'include_24hr_change': 'true'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Convert back to token symbols
                    prices = {}
                    for token in tokens:
                        token_id = self.coingecko_ids.get(token)
                        if token_id and token_id in data:
                            prices[token] = data[token_id].get('usd', 0)
                    
                    logger.info(f"✅ CoinGecko: Fetched {len(prices)} token prices")
                    return prices
                else:
                    logger.warning(f"CoinGecko API error: {response.status}")
                    return {}
            
        except Exception as e:
            logger.error(f"Error fetching CoinGecko prices: {e}")
            return {}

    async def _get_dexscreener_prices(self, tokens: List[str]) -> Dict[str, float]:
        """Get chain-specific prices from DexScreener."""
        try:
            # Rate limiting
            await self._rate_limit('dexscreener')
            
            prices = {}
            
            # Get prices for major pairs on each chain
            for chain in ['ethereum', 'arbitrum', 'optimism', 'base']:
                for token in tokens:
                    if token in self.token_addresses.get(chain, {}):
                        try:
                            # Get token address
                            token_address = self.token_addresses[chain][token]
                            
                            # Fetch from DexScreener
                            url = f"{self.sources['dexscreener']['url']}/dex/tokens/{token_address}"
                            
                            async with self.session.get(url) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    
                                    # Extract price from first pair
                                    pairs = data.get('pairs', [])
                                    if pairs:
                                        price = float(pairs[0].get('priceUsd', 0))
                                        if price > 0:
                                            prices[f"{token}_{chain}"] = price
                                
                                # Small delay to avoid rate limiting
                                await asyncio.sleep(0.2)
                                
                        except Exception as e:
                            logger.debug(f"DexScreener error for {token} on {chain}: {e}")
                            continue
            
            logger.info(f"✅ DexScreener: Fetched {len(prices)} chain-specific prices")
            return prices
            
        except Exception as e:
            logger.error(f"Error fetching DexScreener prices: {e}")
            return {}

    async def get_real_arbitrage_opportunities(self, min_profit_percentage: float = 0.1) -> List[Dict[str, Any]]:
        """Find real arbitrage opportunities using live price data."""
        try:
            # Get cross-chain prices
            cross_chain_prices = await self.get_cross_chain_prices()
            
            opportunities = []
            
            for token, chain_prices in cross_chain_prices.items():
                if len(chain_prices) < 2:
                    continue
                
                # Find arbitrage opportunities
                chains = list(chain_prices.keys())
                
                for i, source_chain in enumerate(chains):
                    for target_chain in chains[i+1:]:
                        source_price = chain_prices[source_chain]
                        target_price = chain_prices[target_chain]
                        
                        # Calculate profit in both directions
                        profit_1 = ((target_price - source_price) / source_price) * 100
                        profit_2 = ((source_price - target_price) / target_price) * 100
                        
                        # Check if profitable
                        if profit_1 > min_profit_percentage:
                            opportunity = {
                                'token': token,
                                'source_chain': source_chain,
                                'target_chain': target_chain,
                                'source_price': source_price,
                                'target_price': target_price,
                                'profit_percentage': profit_1,
                                'direction': f"{source_chain} → {target_chain}",
                                'timestamp': datetime.now().isoformat(),
                                'data_source': 'real_feeds'
                            }
                            opportunities.append(opportunity)
                        
                        elif profit_2 > min_profit_percentage:
                            opportunity = {
                                'token': token,
                                'source_chain': target_chain,
                                'target_chain': source_chain,
                                'source_price': target_price,
                                'target_price': source_price,
                                'profit_percentage': profit_2,
                                'direction': f"{target_chain} → {source_chain}",
                                'timestamp': datetime.now().isoformat(),
                                'data_source': 'real_feeds'
                            }
                            opportunities.append(opportunity)
            
            # Sort by profit percentage
            opportunities.sort(key=lambda x: x['profit_percentage'], reverse=True)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error finding real arbitrage opportunities: {e}")
            return []

    async def _rate_limit(self, source: str):
        """Apply rate limiting for a source."""
        if source not in self.last_requests:
            self.last_requests[source] = 0
        
        rate_limit = self.sources[source]['rate_limit']
        time_since_last = datetime.now().timestamp() - self.last_requests[source]
        
        if time_since_last < rate_limit:
            await asyncio.sleep(rate_limit - time_since_last)
        
        self.last_requests[source] = datetime.now().timestamp()

    async def get_price_feed_status(self) -> Dict[str, Any]:
        """Get status of all price feed sources."""
        status = {}
        
        for source_name, source_info in self.sources.items():
            if not source_info['enabled']:
                status[source_name] = {'status': 'disabled'}
                continue
            
            try:
                # Test connection
                if source_name == 'coingecko':
                    url = f"{source_info['url']}/ping"
                elif source_name == 'dexscreener':
                    url = f"{source_info['url']}/dex/tokens/0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"  # USDC
                else:
                    url = source_info['url']
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        status[source_name] = {
                            'status': 'connected',
                            'priority': source_info['priority'],
                            'rate_limit': source_info['rate_limit'],
                            'chains': len(source_info['chains'])
                        }
                    else:
                        status[source_name] = {'status': 'error', 'code': response.status}
                        
            except Exception as e:
                status[source_name] = {'status': 'error', 'error': str(e)}
        
        return status

    async def disconnect(self):
        """Disconnect from price feed sources."""
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("Disconnected from price feeds")
