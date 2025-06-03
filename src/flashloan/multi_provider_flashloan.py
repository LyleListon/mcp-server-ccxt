"""
Multi-Provider Flash Loan Manager
Optimizes for cheapest flash loan providers: dYdX (0%) > Balancer (0%) > Aave (0.09%)
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FlashLoanProvider:
    """Flash loan provider configuration."""
    name: str
    fee_percentage: float
    max_amount_usd: float
    supported_tokens: List[str]
    supported_networks: List[str]
    gas_cost_usd: float
    priority: int  # Lower = higher priority


class MultiProviderFlashLoan:
    """Multi-provider flash loan manager optimized for lowest costs."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize multi-provider flash loan manager."""
        self.config = config
        
        # Flash loan providers ordered by cost (cheapest first)
        self.providers = {
            'dydx': FlashLoanProvider(
                name='dYdX',
                fee_percentage=0.0,  # FREE!
                max_amount_usd=10_000_000,  # $10M
                supported_tokens=['ETH', 'USDC', 'DAI'],
                supported_networks=['ethereum'],
                gas_cost_usd=25.0,  # Ethereum mainnet
                priority=1
            ),
            'balancer': FlashLoanProvider(
                name='Balancer',
                fee_percentage=0.0,  # FREE!
                max_amount_usd=50_000_000,  # $50M
                supported_tokens=['ETH', 'USDC', 'USDT', 'DAI', 'WBTC'],
                supported_networks=['ethereum', 'arbitrum', 'optimism', 'base', 'polygon'],
                gas_cost_usd=5.0,  # L2 optimized
                priority=2
            ),
            'aave': FlashLoanProvider(
                name='Aave',
                fee_percentage=0.09,  # 0.09% fee
                max_amount_usd=100_000_000,  # $100M
                supported_tokens=['ETH', 'USDC', 'USDT', 'DAI', 'WBTC'],
                supported_networks=['ethereum', 'arbitrum', 'optimism', 'base', 'polygon'],
                gas_cost_usd=5.0,  # L2 optimized
                priority=3
            )
        }
        
        # Network-specific provider availability
        self.network_providers = {
            'ethereum': ['dydx', 'balancer', 'aave'],
            'arbitrum': ['balancer', 'aave'],
            'optimism': ['balancer', 'aave'],
            'base': ['balancer', 'aave'],
            'polygon': ['balancer', 'aave']
        }
        
        logger.info("Multi-provider flash loan manager initialized")

    def get_best_provider(self, token: str, amount_usd: float, network: str) -> Optional[FlashLoanProvider]:
        """Get the best (cheapest) flash loan provider for given parameters."""
        try:
            available_providers = self.network_providers.get(network, [])
            
            # Filter providers by token support and amount limits
            viable_providers = []
            for provider_name in available_providers:
                provider = self.providers[provider_name]
                
                if (token in provider.supported_tokens and 
                    amount_usd <= provider.max_amount_usd and
                    network in provider.supported_networks):
                    viable_providers.append(provider)
            
            if not viable_providers:
                return None
            
            # Sort by priority (lowest cost first)
            viable_providers.sort(key=lambda x: x.priority)
            
            return viable_providers[0]
            
        except Exception as e:
            logger.error(f"Error finding best provider: {e}")
            return None

    def calculate_total_cost(self, provider: FlashLoanProvider, amount_usd: float) -> Dict[str, float]:
        """Calculate total cost breakdown for a flash loan."""
        fee_cost = amount_usd * (provider.fee_percentage / 100)
        gas_cost = provider.gas_cost_usd
        total_cost = fee_cost + gas_cost
        
        return {
            'provider': provider.name,
            'amount_usd': amount_usd,
            'fee_percentage': provider.fee_percentage,
            'fee_cost_usd': fee_cost,
            'gas_cost_usd': gas_cost,
            'total_cost_usd': total_cost,
            'cost_percentage': (total_cost / amount_usd) * 100
        }

    def get_cost_comparison(self, token: str, amount_usd: float, network: str) -> List[Dict[str, Any]]:
        """Get cost comparison across all available providers."""
        available_providers = self.network_providers.get(network, [])
        comparisons = []
        
        for provider_name in available_providers:
            provider = self.providers[provider_name]
            
            if (token in provider.supported_tokens and 
                amount_usd <= provider.max_amount_usd):
                
                cost_breakdown = self.calculate_total_cost(provider, amount_usd)
                cost_breakdown['available'] = True
                comparisons.append(cost_breakdown)
            else:
                comparisons.append({
                    'provider': provider.name,
                    'available': False,
                    'reason': 'Token not supported or amount too large'
                })
        
        # Sort by total cost
        available_comparisons = [c for c in comparisons if c.get('available')]
        available_comparisons.sort(key=lambda x: x.get('total_cost_usd', float('inf')))
        
        return available_comparisons

    def get_optimal_flashloan_quote(self, token: str, amount_usd: float, network: str) -> Dict[str, Any]:
        """Get optimal flash loan quote with cost breakdown."""
        try:
            best_provider = self.get_best_provider(token, amount_usd, network)
            
            if not best_provider:
                return {
                    'error': f'No flash loan provider available for {token} on {network}',
                    'amount_usd': amount_usd
                }
            
            cost_breakdown = self.calculate_total_cost(best_provider, amount_usd)
            
            # Get comparison with other providers
            all_comparisons = self.get_cost_comparison(token, amount_usd, network)
            
            quote = {
                'success': True,
                'recommended_provider': best_provider.name,
                'token': token,
                'network': network,
                'amount_usd': amount_usd,
                'cost_breakdown': cost_breakdown,
                'savings_vs_aave': self._calculate_aave_savings(cost_breakdown, amount_usd),
                'all_providers': all_comparisons,
                'execution_ready': True,
                'timestamp': datetime.now().isoformat()
            }
            
            return quote
            
        except Exception as e:
            logger.error(f"Error getting optimal quote: {e}")
            return {'error': str(e)}

    def _calculate_aave_savings(self, cost_breakdown: Dict[str, float], amount_usd: float) -> Dict[str, float]:
        """Calculate savings compared to Aave (most expensive option)."""
        aave_provider = self.providers['aave']
        aave_cost = self.calculate_total_cost(aave_provider, amount_usd)
        
        current_cost = cost_breakdown['total_cost_usd']
        aave_total_cost = aave_cost['total_cost_usd']
        
        savings_usd = aave_total_cost - current_cost
        savings_percentage = (savings_usd / aave_total_cost) * 100 if aave_total_cost > 0 else 0
        
        return {
            'savings_usd': savings_usd,
            'savings_percentage': savings_percentage,
            'aave_cost_usd': aave_total_cost,
            'current_cost_usd': current_cost
        }

    def get_provider_summary(self) -> Dict[str, Any]:
        """Get summary of all flash loan providers."""
        return {
            'total_providers': len(self.providers),
            'providers': {
                name: {
                    'fee_percentage': provider.fee_percentage,
                    'max_amount_usd': provider.max_amount_usd,
                    'supported_tokens': provider.supported_tokens,
                    'supported_networks': provider.supported_networks,
                    'gas_cost_usd': provider.gas_cost_usd,
                    'priority': provider.priority
                }
                for name, provider in self.providers.items()
            },
            'network_coverage': self.network_providers,
            'cost_optimization': {
                'cheapest_providers': ['dYdX (0%)', 'Balancer (0%)'],
                'most_expensive': 'Aave (0.09%)',
                'max_savings_per_50k': '$45 (vs Aave)',
                'recommendation': 'Use dYdX on Ethereum, Balancer on L2s'
            }
        }

    async def simulate_flashloan_arbitrage(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate flash loan arbitrage with optimal provider selection."""
        try:
            token = opportunity.get('token', 'ETH')
            network = opportunity.get('network', 'arbitrum')
            amount_usd = opportunity.get('flashloan_amount', 50000)
            profit_percentage = opportunity.get('profit_percentage', 0.15)
            
            # Get optimal flash loan quote
            quote = self.get_optimal_flashloan_quote(token, amount_usd, network)
            
            if 'error' in quote:
                return quote
            
            # Calculate arbitrage results
            gross_profit = amount_usd * (profit_percentage / 100)
            flashloan_cost = quote['cost_breakdown']['total_cost_usd']
            net_profit = gross_profit - flashloan_cost
            
            simulation = {
                'simulation_id': f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'opportunity': opportunity,
                'flashloan_quote': quote,
                'arbitrage_results': {
                    'flashloan_amount_usd': amount_usd,
                    'profit_percentage': profit_percentage,
                    'gross_profit_usd': gross_profit,
                    'flashloan_cost_usd': flashloan_cost,
                    'net_profit_usd': net_profit,
                    'roi_percentage': (net_profit / flashloan_cost) * 100 if flashloan_cost > 0 else 0,
                    'profitable': net_profit > 0
                },
                'cost_optimization': quote['savings_vs_aave'],
                'execution_ready': net_profit > 10,  # $10 minimum profit
                'timestamp': datetime.now().isoformat()
            }
            
            return simulation
            
        except Exception as e:
            logger.error(f"Error simulating flashloan arbitrage: {e}")
            return {'error': str(e)}
