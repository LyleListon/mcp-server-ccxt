"""
Multi-Bridge Manager
Manages multiple bridge providers for optimal cross-chain execution.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import json

logger = logging.getLogger(__name__)


class MultiBridgeManager:
    """Manages multiple bridge providers for cross-chain arbitrage."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize multi-bridge manager."""
        self.config = config
        
        # Bridge provider configurations
        self.bridges = {
            'synapse': {
                'name': 'Synapse Protocol',
                'api_url': 'https://api.synapseprotocol.com',
                'fee_percentage': 0.18,  # User's real data
                'speed_minutes': 2,
                'reliability': 0.98,
                'supported_chains': ['ethereum', 'arbitrum', 'base', 'optimism', 'polygon', 'bsc'],
                'supported_tokens': ['ETH', 'USDC', 'USDT', 'DAI'],
                'enabled': True,
                'priority': 1  # Highest priority due to proven low costs
            },
            'across': {
                'name': 'Across Protocol',
                'api_url': 'https://api.across.to',
                'fee_percentage': 0.05,  # Very low fees
                'speed_minutes': 2,
                'reliability': 0.97,
                'supported_chains': ['ethereum', 'arbitrum', 'optimism', 'base', 'polygon'],
                'supported_tokens': ['ETH', 'USDC', 'USDT', 'DAI', 'WBTC'],
                'enabled': True,
                'priority': 2
            },
            'stargate': {
                'name': 'Stargate Finance',
                'api_url': 'https://api.stargate.finance',
                'fee_percentage': 0.06,
                'speed_minutes': 1,  # Fastest
                'reliability': 0.94,
                'supported_chains': ['ethereum', 'arbitrum', 'optimism', 'polygon', 'bsc', 'avalanche'],
                'supported_tokens': ['USDC', 'USDT', 'ETH'],
                'enabled': True,
                'priority': 3
            },
            'hop': {
                'name': 'Hop Protocol',
                'api_url': 'https://api.hop.exchange',
                'fee_percentage': 0.04,  # Very competitive
                'speed_minutes': 5,
                'reliability': 0.95,
                'supported_chains': ['ethereum', 'arbitrum', 'optimism', 'polygon', 'gnosis'],
                'supported_tokens': ['ETH', 'USDC', 'USDT', 'DAI', 'MATIC'],
                'enabled': True,
                'priority': 4
            },
            'cbridge': {
                'name': 'Celer cBridge',
                'api_url': 'https://cbridge-prod2.celer.app',
                'fee_percentage': 0.1,
                'speed_minutes': 3,
                'reliability': 0.93,
                'supported_chains': ['ethereum', 'arbitrum', 'optimism', 'polygon', 'bsc', 'avalanche'],
                'supported_tokens': ['ETH', 'USDC', 'USDT', 'DAI', 'WBTC'],
                'enabled': True,
                'priority': 5
            },
            'multichain': {
                'name': 'Multichain (anySwap)',
                'api_url': 'https://bridgeapi.anyswap.exchange',
                'fee_percentage': 0.1,
                'speed_minutes': 10,
                'reliability': 0.90,
                'supported_chains': ['ethereum', 'arbitrum', 'optimism', 'polygon', 'bsc', 'avalanche', 'fantom'],
                'supported_tokens': ['ETH', 'USDC', 'USDT', 'DAI', 'WBTC'],
                'enabled': True,
                'priority': 6
            },
            'orbiter': {
                'name': 'Orbiter Finance',
                'api_url': 'https://api.orbiter.finance',
                'fee_percentage': 0.15,
                'speed_minutes': 1,  # Very fast for L2s
                'reliability': 0.92,
                'supported_chains': ['ethereum', 'arbitrum', 'optimism', 'base', 'polygon'],
                'supported_tokens': ['ETH', 'USDC'],
                'enabled': True,
                'priority': 7
            }
        }
        
        # Bridge performance tracking
        self.bridge_stats = {}
        for bridge_name in self.bridges.keys():
            self.bridge_stats[bridge_name] = {
                'total_quotes': 0,
                'successful_quotes': 0,
                'total_executions': 0,
                'successful_executions': 0,
                'average_fee': 0.0,
                'average_time_minutes': 0.0,
                'last_used': None,
                'consecutive_failures': 0
            }
        
        # Session for HTTP requests
        self.session = None
        
        logger.info(f"Multi-bridge manager initialized with {len(self.bridges)} bridges")

    async def initialize(self) -> bool:
        """Initialize bridge connections."""
        try:
            self.session = aiohttp.ClientSession()
            
            # Test connectivity to each bridge
            connected_bridges = 0
            for bridge_name, bridge_config in self.bridges.items():
                if not bridge_config['enabled']:
                    continue
                
                try:
                    # Test bridge API connectivity
                    test_url = bridge_config['api_url']
                    async with self.session.get(test_url, timeout=5) as response:
                        if response.status in [200, 404]:  # 404 is OK for API root
                            logger.info(f"✅ {bridge_config['name']} API accessible")
                            connected_bridges += 1
                        else:
                            logger.warning(f"⚠️  {bridge_config['name']} API returned {response.status}")
                except Exception as e:
                    logger.warning(f"⚠️  {bridge_config['name']} API test failed: {e}")
            
            logger.info(f"🌉 Connected to {connected_bridges}/{len([b for b in self.bridges.values() if b['enabled']])} bridges")
            return connected_bridges > 0
            
        except Exception as e:
            logger.error(f"Bridge initialization error: {e}")
            return False

    async def get_best_bridge_quote(self, source_chain: str, target_chain: str, token: str, amount_usd: float) -> Dict[str, Any]:
        """Get the best bridge quote from all available bridges."""
        try:
            logger.info(f"🔍 Getting quotes for {token} {source_chain}→{target_chain} (${amount_usd:,.0f})")
            
            # Get quotes from all compatible bridges
            quote_tasks = []
            compatible_bridges = []
            
            for bridge_name, bridge_config in self.bridges.items():
                if not bridge_config['enabled']:
                    continue
                
                # Check if bridge supports this route
                if (source_chain in bridge_config['supported_chains'] and 
                    target_chain in bridge_config['supported_chains'] and
                    token in bridge_config['supported_tokens']):
                    
                    compatible_bridges.append(bridge_name)
                    quote_tasks.append(self._get_bridge_quote(bridge_name, source_chain, target_chain, token, amount_usd))
            
            if not quote_tasks:
                return {
                    'success': False,
                    'error': f"No compatible bridges for {token} {source_chain}→{target_chain}"
                }
            
            logger.info(f"   Requesting quotes from {len(compatible_bridges)} bridges: {', '.join(compatible_bridges)}")
            
            # Execute all quote requests concurrently
            quote_results = await asyncio.gather(*quote_tasks, return_exceptions=True)
            
            # Process results and find best quote
            valid_quotes = []
            
            for i, result in enumerate(quote_results):
                bridge_name = compatible_bridges[i]
                
                if isinstance(result, Exception):
                    logger.warning(f"   ❌ {bridge_name}: {result}")
                    self._update_bridge_stats(bridge_name, 'quote_failed')
                elif result.get('success'):
                    valid_quotes.append({
                        'bridge': bridge_name,
                        'bridge_name': self.bridges[bridge_name]['name'],
                        **result
                    })
                    logger.info(f"   ✅ {bridge_name}: ${result['fee_usd']:.2f} fee ({result['fee_percentage']:.2f}%)")
                    self._update_bridge_stats(bridge_name, 'quote_success', result)
                else:
                    logger.warning(f"   ❌ {bridge_name}: {result.get('error', 'Unknown error')}")
                    self._update_bridge_stats(bridge_name, 'quote_failed')
            
            if not valid_quotes:
                return {
                    'success': False,
                    'error': "No valid quotes received from any bridge"
                }
            
            # Select best quote based on multiple factors
            best_quote = self._select_best_quote(valid_quotes, amount_usd)
            
            logger.info(f"🏆 Best quote: {best_quote['bridge_name']} - ${best_quote['fee_usd']:.2f} fee")
            
            return best_quote
            
        except Exception as e:
            logger.error(f"Error getting bridge quotes: {e}")
            return {'success': False, 'error': str(e)}

    async def _get_bridge_quote(self, bridge_name: str, source_chain: str, target_chain: str, token: str, amount_usd: float) -> Dict[str, Any]:
        """Get quote from a specific bridge."""
        try:
            bridge_config = self.bridges[bridge_name]
            
            # For now, use estimated fees based on bridge configuration
            # In production, this would call the actual bridge APIs
            
            if bridge_name == 'synapse':
                # Use user's real data
                fee_percentage = 0.18
                fee_usd = amount_usd * (fee_percentage / 100)
                time_minutes = 2
                
            elif bridge_name == 'across':
                # Across has dynamic fees, estimate based on route
                if source_chain == 'ethereum':
                    fee_percentage = 0.05
                else:
                    fee_percentage = 0.03  # L2 to L2 is cheaper
                fee_usd = amount_usd * (fee_percentage / 100)
                time_minutes = 2
                
            elif bridge_name == 'stargate':
                # Stargate fees vary by liquidity
                fee_percentage = 0.06
                fee_usd = amount_usd * (fee_percentage / 100)
                time_minutes = 1
                
            elif bridge_name == 'hop':
                # Hop has competitive fees
                fee_percentage = 0.04
                fee_usd = amount_usd * (fee_percentage / 100)
                time_minutes = 5
                
            else:
                # Use default bridge config
                fee_percentage = bridge_config['fee_percentage']
                fee_usd = amount_usd * (fee_percentage / 100)
                time_minutes = bridge_config['speed_minutes']
            
            # Add some randomness to simulate real market conditions
            import random
            fee_usd *= random.uniform(0.9, 1.1)  # ±10% variation
            time_minutes *= random.uniform(0.8, 1.2)  # ±20% variation
            
            return {
                'success': True,
                'fee_usd': fee_usd,
                'fee_percentage': fee_percentage,
                'estimated_time_minutes': time_minutes,
                'reliability_score': bridge_config['reliability'],
                'api_url': bridge_config['api_url']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _select_best_quote(self, quotes: List[Dict[str, Any]], amount_usd: float) -> Dict[str, Any]:
        """Select the best quote based on multiple factors."""
        try:
            # Score each quote
            scored_quotes = []
            
            for quote in quotes:
                bridge_name = quote['bridge']
                bridge_config = self.bridges[bridge_name]
                bridge_stats = self.bridge_stats[bridge_name]
                
                # Calculate composite score
                fee_score = 1 - (quote['fee_usd'] / (amount_usd * 0.01))  # Lower fee = higher score
                speed_score = 1 - (quote['estimated_time_minutes'] / 10)  # Faster = higher score
                reliability_score = quote['reliability_score']
                
                # Historical performance bonus
                if bridge_stats['total_executions'] > 0:
                    success_rate = bridge_stats['successful_executions'] / bridge_stats['total_executions']
                    performance_score = success_rate
                else:
                    performance_score = 0.5  # Neutral for untested bridges
                
                # Priority bonus (user preference)
                priority_score = 1 - (bridge_config['priority'] / 10)
                
                # Consecutive failure penalty
                failure_penalty = max(0, 1 - (bridge_stats['consecutive_failures'] * 0.2))
                
                # Weighted composite score
                composite_score = (
                    fee_score * 0.4 +           # 40% weight on fees
                    speed_score * 0.2 +         # 20% weight on speed
                    reliability_score * 0.2 +   # 20% weight on reliability
                    performance_score * 0.1 +   # 10% weight on historical performance
                    priority_score * 0.05 +     # 5% weight on priority
                    failure_penalty * 0.05      # 5% weight on recent failures
                )
                
                scored_quotes.append({
                    **quote,
                    'composite_score': composite_score,
                    'fee_score': fee_score,
                    'speed_score': speed_score,
                    'performance_score': performance_score
                })
            
            # Sort by composite score (highest first)
            scored_quotes.sort(key=lambda x: x['composite_score'], reverse=True)
            
            return scored_quotes[0]
            
        except Exception as e:
            logger.error(f"Error selecting best quote: {e}")
            # Fallback to lowest fee
            return min(quotes, key=lambda x: x['fee_usd'])

    def _update_bridge_stats(self, bridge_name: str, event_type: str, data: Dict[str, Any] = None):
        """Update bridge performance statistics."""
        try:
            stats = self.bridge_stats[bridge_name]
            
            if event_type == 'quote_success':
                stats['total_quotes'] += 1
                stats['successful_quotes'] += 1
                stats['consecutive_failures'] = 0
                if data:
                    # Update average fee
                    if stats['total_quotes'] == 1:
                        stats['average_fee'] = data['fee_percentage']
                    else:
                        stats['average_fee'] = (stats['average_fee'] * (stats['total_quotes'] - 1) + data['fee_percentage']) / stats['total_quotes']
                    
                    # Update average time
                    if stats['total_quotes'] == 1:
                        stats['average_time_minutes'] = data['estimated_time_minutes']
                    else:
                        stats['average_time_minutes'] = (stats['average_time_minutes'] * (stats['total_quotes'] - 1) + data['estimated_time_minutes']) / stats['total_quotes']
            
            elif event_type == 'quote_failed':
                stats['total_quotes'] += 1
                stats['consecutive_failures'] += 1
            
            elif event_type == 'execution_success':
                stats['total_executions'] += 1
                stats['successful_executions'] += 1
                stats['consecutive_failures'] = 0
                stats['last_used'] = datetime.now().isoformat()
            
            elif event_type == 'execution_failed':
                stats['total_executions'] += 1
                stats['consecutive_failures'] += 1
            
        except Exception as e:
            logger.error(f"Error updating bridge stats: {e}")

    def get_bridge_status(self) -> Dict[str, Any]:
        """Get status of all bridges."""
        status = {}
        
        for bridge_name, bridge_config in self.bridges.items():
            stats = self.bridge_stats[bridge_name]
            
            # Calculate success rates
            quote_success_rate = (stats['successful_quotes'] / max(stats['total_quotes'], 1)) * 100
            execution_success_rate = (stats['successful_executions'] / max(stats['total_executions'], 1)) * 100
            
            status[bridge_name] = {
                'name': bridge_config['name'],
                'enabled': bridge_config['enabled'],
                'priority': bridge_config['priority'],
                'base_fee_percentage': bridge_config['fee_percentage'],
                'average_fee_percentage': stats['average_fee'],
                'speed_minutes': bridge_config['speed_minutes'],
                'average_time_minutes': stats['average_time_minutes'],
                'reliability': bridge_config['reliability'],
                'quote_success_rate': quote_success_rate,
                'execution_success_rate': execution_success_rate,
                'total_quotes': stats['total_quotes'],
                'total_executions': stats['total_executions'],
                'consecutive_failures': stats['consecutive_failures'],
                'last_used': stats['last_used'],
                'supported_chains': len(bridge_config['supported_chains']),
                'supported_tokens': len(bridge_config['supported_tokens'])
            }
        
        return status

    async def cleanup(self):
        """Cleanup resources."""
        if self.session:
            await self.session.close()
        logger.info("Multi-bridge manager cleanup complete")
