"""
Token Address Fetcher

Dynamically fetches real token contract addresses from multiple sources.
No more hardcoded fake addresses!
"""

import asyncio
import logging
from typing import Dict, Optional, List
import aiohttp
import json

logger = logging.getLogger(__name__)


class TokenAddressFetcher:
    """Fetches real token contract addresses from multiple sources."""
    
    def __init__(self, chain_id: int = 1):
        """Initialize token address fetcher.
        
        Args:
            chain_id: Blockchain chain ID (1 = Ethereum mainnet)
        """
        self.chain_id = chain_id
        self.session = None
        
        # Multiple data sources for redundancy
        self.sources = {
            'coingecko': 'https://api.coingecko.com/api/v3',
            'etherscan': 'https://api.etherscan.io/api',
            'tokenlist': 'https://tokens.coingecko.com/uniswap/all.json',
            'defillama': 'https://api.llama.fi/protocols'
        }
        
        # Token symbol to CoinGecko ID mapping
        self.token_mappings = {
            'ETH': 'ethereum',
            'WETH': 'weth',
            'USDC': 'usd-coin',
            'USDT': 'tether',
            'DAI': 'dai',
            'WBTC': 'wrapped-bitcoin',
            'UNI': 'uniswap',
            'LINK': 'chainlink',
            'AAVE': 'aave',
            'COMP': 'compound-governance-token',
            'MKR': 'maker',
            'SNX': 'havven',
            'CRV': 'curve-dao-token',
            'SUSHI': 'sushi'
        }
        
        # Cache for fetched addresses
        self.address_cache = {}
        
        logger.info(f"Token address fetcher initialized for chain {chain_id}")
    
    async def connect(self) -> bool:
        """Initialize HTTP session."""
        try:
            self.session = aiohttp.ClientSession()
            return True
        except Exception as e:
            logger.error(f"Error initializing session: {e}")
            return False
    
    async def get_token_address(self, symbol: str) -> Optional[str]:
        """Get token contract address for a symbol.
        
        Args:
            symbol: Token symbol (e.g., 'USDC', 'WETH')
            
        Returns:
            Contract address or None if not found
        """
        try:
            # Check cache first
            if symbol in self.address_cache:
                return self.address_cache[symbol]
            
            # Special case for native ETH
            if symbol == 'ETH':
                address = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'
                self.address_cache[symbol] = address
                return address
            
            # Try multiple sources
            address = None
            
            # Source 1: CoinGecko
            address = await self._fetch_from_coingecko(symbol)
            if address:
                self.address_cache[symbol] = address
                return address
            
            # Source 2: Token list
            address = await self._fetch_from_tokenlist(symbol)
            if address:
                self.address_cache[symbol] = address
                return address
            
            # Source 3: Etherscan (if we have API key)
            address = await self._fetch_from_etherscan(symbol)
            if address:
                self.address_cache[symbol] = address
                return address
            
            logger.warning(f"Could not find address for token: {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching address for {symbol}: {e}")
            return None
    
    async def _fetch_from_coingecko(self, symbol: str) -> Optional[str]:
        """Fetch token address from CoinGecko API."""
        try:
            if not self.session:
                return None
            
            # Get CoinGecko ID for symbol
            coin_id = self.token_mappings.get(symbol)
            if not coin_id:
                return None
            
            # Fetch coin data
            url = f"{self.sources['coingecko']}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'false',
                'community_data': 'false',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract Ethereum contract address
                    platforms = data.get('platforms', {})
                    eth_address = platforms.get('ethereum')
                    
                    if eth_address and eth_address.startswith('0x'):
                        logger.info(f"✅ Found {symbol} address from CoinGecko: {eth_address}")
                        return eth_address
                    
                    return None
                else:
                    logger.debug(f"CoinGecko API error for {symbol}: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.debug(f"CoinGecko fetch error for {symbol}: {e}")
            return None
    
    async def _fetch_from_tokenlist(self, symbol: str) -> Optional[str]:
        """Fetch token address from Uniswap token list."""
        try:
            if not self.session:
                return None
            
            url = self.sources['tokenlist']
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    tokens = data.get('tokens', [])
                    
                    # Find token by symbol
                    for token in tokens:
                        if (token.get('symbol', '').upper() == symbol.upper() and 
                            token.get('chainId') == self.chain_id):
                            
                            address = token.get('address')
                            if address and address.startswith('0x'):
                                logger.info(f"✅ Found {symbol} address from token list: {address}")
                                return address
                    
                    return None
                else:
                    logger.debug(f"Token list API error: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.debug(f"Token list fetch error for {symbol}: {e}")
            return None
    
    async def _fetch_from_etherscan(self, symbol: str) -> Optional[str]:
        """Fetch token address from Etherscan API."""
        try:
            # This would require an Etherscan API key
            # For now, return None
            return None
            
        except Exception as e:
            logger.debug(f"Etherscan fetch error for {symbol}: {e}")
            return None
    
    async def get_multiple_addresses(self, symbols: List[str]) -> Dict[str, str]:
        """Get addresses for multiple tokens.
        
        Args:
            symbols: List of token symbols
            
        Returns:
            Dictionary mapping symbols to addresses
        """
        try:
            addresses = {}
            
            # Fetch all addresses concurrently
            tasks = []
            for symbol in symbols:
                task = asyncio.create_task(
                    self.get_token_address(symbol),
                    name=f"fetch_{symbol}"
                )
                tasks.append((symbol, task))
            
            # Wait for all tasks
            for symbol, task in tasks:
                try:
                    address = await task
                    if address:
                        addresses[symbol] = address
                        logger.info(f"✅ {symbol}: {address}")
                    else:
                        logger.warning(f"❌ {symbol}: Address not found")
                except Exception as e:
                    logger.error(f"❌ {symbol}: Error - {e}")
            
            return addresses
            
        except Exception as e:
            logger.error(f"Error fetching multiple addresses: {e}")
            return {}
    
    async def validate_address(self, address: str) -> bool:
        """Validate if an address looks correct.
        
        Args:
            address: Contract address to validate
            
        Returns:
            True if address format is valid
        """
        try:
            if not address:
                return False
            
            # Basic format validation
            if not address.startswith('0x'):
                return False
            
            if len(address) != 42:
                return False
            
            # Check if it's not a placeholder pattern
            if address == '0xA0b86a33E6417c4c6b4c6b4c6b4c6b4c6b4c6b4c':
                logger.warning("Detected placeholder address pattern")
                return False
            
            # Check for obvious patterns
            address_part = address[2:]  # Remove 0x
            if len(set(address_part)) < 5:  # Too few unique characters
                logger.warning("Address has too few unique characters (likely fake)")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating address {address}: {e}")
            return False
    
    async def get_verified_addresses(self, symbols: List[str]) -> Dict[str, str]:
        """Get verified token addresses with validation.
        
        Args:
            symbols: List of token symbols
            
        Returns:
            Dictionary of verified addresses
        """
        try:
            logger.info(f"🔍 Fetching verified addresses for: {symbols}")
            
            # Fetch addresses
            addresses = await self.get_multiple_addresses(symbols)
            
            # Validate each address
            verified_addresses = {}
            for symbol, address in addresses.items():
                if await self.validate_address(address):
                    verified_addresses[symbol] = address
                    logger.info(f"✅ {symbol}: {address} (verified)")
                else:
                    logger.warning(f"❌ {symbol}: {address} (invalid)")
            
            logger.info(f"🎯 Verified {len(verified_addresses)}/{len(symbols)} addresses")
            return verified_addresses
            
        except Exception as e:
            logger.error(f"Error getting verified addresses: {e}")
            return {}
    
    async def disconnect(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("Token address fetcher disconnected")


# Convenience function for quick address fetching
async def fetch_token_addresses(symbols: List[str], chain_id: int = 1) -> Dict[str, str]:
    """Quick function to fetch token addresses.
    
    Args:
        symbols: List of token symbols
        chain_id: Blockchain chain ID
        
    Returns:
        Dictionary of token addresses
    """
    fetcher = TokenAddressFetcher(chain_id)
    
    try:
        await fetcher.connect()
        addresses = await fetcher.get_verified_addresses(symbols)
        return addresses
    finally:
        await fetcher.disconnect()
