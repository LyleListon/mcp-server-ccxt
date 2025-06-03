"""
Real-Time Gas Price Oracle

Fetches accurate gas prices from multiple sources for precise arbitrage calculations.
Critical for determining if trades are profitable after gas costs.
"""

import asyncio
import logging
from typing import Dict, Optional, List
import aiohttp
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GasPriceOracle:
    """Real-time gas price oracle with multiple data sources."""
    
    def __init__(self):
        """Initialize gas price oracle."""
        self.session = None
        
        # Multiple gas price sources for accuracy
        self.sources = {
            'etherscan': 'https://api.etherscan.io/api',
            'ethgasstation': 'https://ethgasstation.info/api/ethgasAPI.json',
            'blocknative': 'https://api.blocknative.com/gasprices/blockprices',
            'owlracle': 'https://api.owlracle.info/v4/eth/gas',
            'web3_rpc': None  # Will use your Alchemy RPC
        }
        
        # Cache for gas prices
        self.gas_cache = {}
        self.cache_ttl = 30  # 30 seconds cache
        
        # Gas estimates for different transaction types
        self.gas_estimates = {
            'simple_transfer': 21000,
            'erc20_transfer': 65000,
            'uniswap_v2_swap': 150000,
            'uniswap_v3_swap': 180000,
            'paraswap_swap': 200000,
            'complex_arbitrage': 300000,
            'flashloan_arbitrage': 400000
        }
        
        logger.info("Gas price oracle initialized")
    
    async def connect(self) -> bool:
        """Initialize HTTP session."""
        try:
            self.session = aiohttp.ClientSession()
            return True
        except Exception as e:
            logger.error(f"Error initializing gas oracle: {e}")
            return False
    
    async def get_current_gas_prices(self) -> Dict[str, float]:
        """Get current gas prices in gwei from multiple sources.
        
        Returns:
            Dictionary with slow, standard, fast, instant gas prices in gwei
        """
        try:
            # Check cache first
            if 'gas_prices' in self.gas_cache:
                cached_data, timestamp = self.gas_cache['gas_prices']
                if (datetime.now() - timestamp).seconds < self.cache_ttl:
                    return cached_data
            
            # Fetch from multiple sources
            gas_data = {}
            
            # Source 1: Etherscan
            etherscan_data = await self._fetch_etherscan_gas()
            if etherscan_data:
                gas_data['etherscan'] = etherscan_data
            
            # Source 2: Owlracle (free, reliable)
            owlracle_data = await self._fetch_owlracle_gas()
            if owlracle_data:
                gas_data['owlracle'] = owlracle_data
            
            # Source 3: ETH Gas Station
            ethgas_data = await self._fetch_ethgasstation_gas()
            if ethgas_data:
                gas_data['ethgasstation'] = ethgas_data
            
            # Aggregate and return best estimates
            aggregated = self._aggregate_gas_prices(gas_data)
            
            # Cache the result
            self.gas_cache['gas_prices'] = (aggregated, datetime.now())
            
            logger.info(f"Gas prices updated: {aggregated}")
            return aggregated
            
        except Exception as e:
            logger.error(f"Error fetching gas prices: {e}")
            # Return fallback prices
            return {
                'slow': 10.0,
                'standard': 15.0,
                'fast': 25.0,
                'instant': 35.0
            }
    
    async def _fetch_etherscan_gas(self) -> Optional[Dict[str, float]]:
        """Fetch gas prices from Etherscan API."""
        try:
            if not self.session:
                return None
            
            url = self.sources['etherscan']
            params = {
                'module': 'gastracker',
                'action': 'gasoracle',
                'apikey': 'YourApiKeyToken'  # Free tier available
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('result', {})
                    
                    return {
                        'slow': float(result.get('SafeGasPrice', 10)),
                        'standard': float(result.get('ProposeGasPrice', 15)),
                        'fast': float(result.get('FastGasPrice', 25))
                    }
                    
        except Exception as e:
            logger.debug(f"Etherscan gas fetch error: {e}")
            return None
    
    async def _fetch_owlracle_gas(self) -> Optional[Dict[str, float]]:
        """Fetch gas prices from Owlracle API (free, no key needed)."""
        try:
            if not self.session:
                return None
            
            url = self.sources['owlracle']
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Owlracle returns speeds array
                    speeds = data.get('speeds', [])
                    if len(speeds) >= 4:
                        return {
                            'slow': float(speeds[0].get('gasPrice', 10)),
                            'standard': float(speeds[1].get('gasPrice', 15)),
                            'fast': float(speeds[2].get('gasPrice', 25)),
                            'instant': float(speeds[3].get('gasPrice', 35))
                        }
                    
        except Exception as e:
            logger.debug(f"Owlracle gas fetch error: {e}")
            return None
    
    async def _fetch_ethgasstation_gas(self) -> Optional[Dict[str, float]]:
        """Fetch gas prices from ETH Gas Station."""
        try:
            if not self.session:
                return None
            
            url = self.sources['ethgasstation']
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # ETH Gas Station returns prices in 10x gwei
                    return {
                        'slow': float(data.get('safeLow', 100)) / 10,
                        'standard': float(data.get('average', 150)) / 10,
                        'fast': float(data.get('fast', 250)) / 10,
                        'instant': float(data.get('fastest', 350)) / 10
                    }
                    
        except Exception as e:
            logger.debug(f"ETH Gas Station fetch error: {e}")
            return None
    
    def _aggregate_gas_prices(self, gas_data: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Aggregate gas prices from multiple sources."""
        try:
            if not gas_data:
                return {
                    'slow': 10.0,
                    'standard': 15.0,
                    'fast': 25.0,
                    'instant': 35.0
                }
            
            # Calculate median prices for each speed
            speeds = ['slow', 'standard', 'fast', 'instant']
            aggregated = {}
            
            for speed in speeds:
                prices = []
                for source, data in gas_data.items():
                    if speed in data:
                        prices.append(data[speed])
                
                if prices:
                    # Use median for robustness
                    prices.sort()
                    median_idx = len(prices) // 2
                    aggregated[speed] = prices[median_idx]
                else:
                    # Fallback values
                    fallback = {'slow': 10, 'standard': 15, 'fast': 25, 'instant': 35}
                    aggregated[speed] = fallback[speed]
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating gas prices: {e}")
            return {
                'slow': 0.01,
                'standard': 0.05,
                'fast': 0.1,
                'instant': 0.2
            }
    
    async def calculate_transaction_cost(self, tx_type: str, gas_speed: str = 'standard') -> Dict[str, float]:
        """Calculate transaction cost in USD and ETH.
        
        Args:
            tx_type: Type of transaction (e.g., 'uniswap_v3_swap')
            gas_speed: Gas speed ('slow', 'standard', 'fast', 'instant')
            
        Returns:
            Dictionary with gas cost in ETH and USD
        """
        try:
            # Get current gas prices
            gas_prices = await self.get_current_gas_prices()
            gas_price_gwei = gas_prices.get(gas_speed, 15.0)
            
            # Get gas estimate for transaction type
            gas_limit = self.gas_estimates.get(tx_type, 150000)
            
            # Calculate costs
            gas_cost_wei = gas_limit * gas_price_gwei * 10**9  # Convert gwei to wei
            gas_cost_eth = gas_cost_wei / 10**18  # Convert wei to ETH
            
            # Get ETH price for USD calculation
            eth_price_usd = await self._get_eth_price()
            gas_cost_usd = gas_cost_eth * eth_price_usd
            
            return {
                'gas_limit': gas_limit,
                'gas_price_gwei': gas_price_gwei,
                'gas_cost_eth': gas_cost_eth,
                'gas_cost_usd': gas_cost_usd,
                'tx_type': tx_type,
                'gas_speed': gas_speed
            }
            
        except Exception as e:
            logger.error(f"Error calculating transaction cost: {e}")
            return {
                'gas_limit': 150000,
                'gas_price_gwei': 15.0,
                'gas_cost_eth': 0.00225,
                'gas_cost_usd': 5.0,
                'tx_type': tx_type,
                'gas_speed': gas_speed
            }
    
    async def _get_eth_price(self) -> float:
        """Get current ETH price in USD."""
        try:
            # Check cache
            if 'eth_price' in self.gas_cache:
                cached_price, timestamp = self.gas_cache['eth_price']
                if (datetime.now() - timestamp).seconds < 300:  # 5 min cache
                    return cached_price
            
            # Fetch ETH price from CoinGecko
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {'ids': 'ethereum', 'vs_currencies': 'usd'}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    eth_price = data['ethereum']['usd']
                    
                    # Cache the price
                    self.gas_cache['eth_price'] = (eth_price, datetime.now())
                    return eth_price
            
            # Fallback price
            return 2500.0
            
        except Exception as e:
            logger.debug(f"Error fetching ETH price: {e}")
            return 2500.0  # Fallback
    
    async def is_trade_profitable(self, expected_profit_usd: float, tx_type: str, gas_speed: str = 'fast') -> Dict[str, any]:
        """Check if a trade is profitable after gas costs.
        
        Args:
            expected_profit_usd: Expected profit in USD
            tx_type: Transaction type
            gas_speed: Gas speed to use
            
        Returns:
            Dictionary with profitability analysis
        """
        try:
            # Calculate gas cost
            gas_cost = await self.calculate_transaction_cost(tx_type, gas_speed)
            
            # Calculate net profit
            net_profit_usd = expected_profit_usd - gas_cost['gas_cost_usd']
            profit_margin = (net_profit_usd / expected_profit_usd) * 100 if expected_profit_usd > 0 else -100
            
            is_profitable = net_profit_usd > 0
            
            return {
                'is_profitable': is_profitable,
                'expected_profit_usd': expected_profit_usd,
                'gas_cost_usd': gas_cost['gas_cost_usd'],
                'net_profit_usd': net_profit_usd,
                'profit_margin_percent': profit_margin,
                'gas_details': gas_cost,
                'recommendation': 'EXECUTE' if is_profitable else 'SKIP'
            }
            
        except Exception as e:
            logger.error(f"Error checking trade profitability: {e}")
            return {
                'is_profitable': False,
                'error': str(e),
                'recommendation': 'SKIP'
            }
    
    async def disconnect(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("Gas price oracle disconnected")


# Convenience function for quick gas price checks
async def get_current_gas_cost(tx_type: str = 'uniswap_v3_swap', gas_speed: str = 'standard') -> Dict[str, float]:
    """Quick function to get current gas cost.
    
    Args:
        tx_type: Transaction type
        gas_speed: Gas speed
        
    Returns:
        Gas cost information
    """
    oracle = GasPriceOracle()
    
    try:
        await oracle.connect()
        cost = await oracle.calculate_transaction_cost(tx_type, gas_speed)
        return cost
    finally:
        await oracle.disconnect()
