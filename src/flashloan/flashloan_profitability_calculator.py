#!/usr/bin/env python3
"""
FLASHLOAN PROFITABILITY CALCULATOR
Calculates REAL profitability including all fees, gas costs, and slippage
"""

import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from web3 import Web3

logger = logging.getLogger(__name__)

class FlashloanProfitabilityCalculator:
    """Calculates real flashloan profitability with all costs included."""
    
    def __init__(self, web3_connections: Dict[str, Web3]):
        self.web3_connections = web3_connections
        
        # Flashloan provider fees (as percentage of borrowed amount)
        self.flashloan_fees = {
            'aave': 0.0009,      # 0.09%
            'balancer': 0.0,     # 0% but higher gas costs
            'dydx': 0.0,         # 0% (Ethereum only)
            'radiant': 0.0009,   # 0.09%
            'moonwell': 0.0009   # 0.09% (Base)
        }
        
        # Gas cost estimates per chain (in ETH)
        self.base_gas_costs = {
            'arbitrum': {
                'simple_swap': 0.0005,      # ~$1.60
                'flashloan_arbitrage': 0.001, # ~$3.20
                'complex_arbitrage': 0.002   # ~$6.40
            },
            'base': {
                'simple_swap': 0.0003,      # ~$0.96
                'flashloan_arbitrage': 0.0005, # ~$1.60
                'complex_arbitrage': 0.001   # ~$3.20
            },
            'optimism': {
                'simple_swap': 0.0003,      # ~$0.96
                'flashloan_arbitrage': 0.0005, # ~$1.60
                'complex_arbitrage': 0.001   # ~$3.20
            },
            'ethereum': {
                'simple_swap': 0.01,        # ~$32
                'flashloan_arbitrage': 0.015, # ~$48
                'complex_arbitrage': 0.025   # ~$80
            }
        }
        
        # Slippage estimates based on trade size (increased for realistic volatile markets)
        self.slippage_estimates = {
            'small': 0.02,     # 2% for trades < $1000 (realistic for volatile markets)
            'medium': 0.03,    # 3% for trades $1000-$10000
            'large': 0.05,     # 5% for trades $10000-$50000
            'xlarge': 0.08     # 8% for trades > $50000 (high volatility)
        }
        
        # DEX-specific fees
        self.dex_fees = {
            'uniswap_v3': 0.0005,  # 0.05% (can vary by pool)
            'uniswap_v2': 0.003,   # 0.3%
            'sushiswap': 0.003,    # 0.3%
            'camelot': 0.003,      # 0.3%
            'aerodrome': 0.0005,   # 0.05%
            'baseswap': 0.0025,    # 0.25%
            'balancer': 0.0001     # 0.01% (can vary)
        }
    
    async def calculate_flashloan_profitability(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate real profitability of a flashloan arbitrage opportunity."""
        try:
            chain = opportunity.get('source_chain', 'arbitrum')
            trade_amount_usd = opportunity.get('trade_amount_usd', 1000)
            gross_profit_usd = opportunity.get('estimated_profit_usd', 0)
            flashloan_provider = opportunity.get('flashloan_provider', 'aave')
            complexity = opportunity.get('complexity', 'flashloan_arbitrage')
            
            # 1. Calculate flashloan fees
            flashloan_fee_rate = self.flashloan_fees.get(flashloan_provider, 0.0009)
            flashloan_fee_usd = trade_amount_usd * flashloan_fee_rate
            
            # 2. Calculate gas costs
            gas_cost_eth = self.base_gas_costs.get(chain, {}).get(complexity, 0.001)
            
            # Adjust gas cost based on network congestion (simplified)
            if chain in self.web3_connections:
                try:
                    w3 = self.web3_connections[chain]
                    current_gas_price = w3.eth.gas_price
                    base_gas_price = w3.to_wei(1, 'gwei')  # 1 gwei baseline
                    
                    if current_gas_price > base_gas_price:
                        gas_multiplier = min(current_gas_price / base_gas_price, 5.0)  # Cap at 5x
                        gas_cost_eth *= gas_multiplier
                except:
                    pass  # Use base estimate if gas price check fails
            
            gas_cost_usd = gas_cost_eth * 3200  # ETH price estimate
            
            # 3. Calculate slippage costs
            if trade_amount_usd < 1000:
                slippage_rate = self.slippage_estimates['small']
            elif trade_amount_usd < 10000:
                slippage_rate = self.slippage_estimates['medium']
            elif trade_amount_usd < 50000:
                slippage_rate = self.slippage_estimates['large']
            else:
                slippage_rate = self.slippage_estimates['xlarge']
            
            slippage_cost_usd = trade_amount_usd * slippage_rate
            
            # 4. Calculate DEX fees
            buy_dex = opportunity.get('buy_dex', 'uniswap_v3')
            sell_dex = opportunity.get('sell_dex', 'camelot')
            
            buy_fee_rate = self.dex_fees.get(buy_dex, 0.003)
            sell_fee_rate = self.dex_fees.get(sell_dex, 0.003)
            
            dex_fees_usd = trade_amount_usd * (buy_fee_rate + sell_fee_rate)
            
            # 5. Calculate total costs
            total_costs_usd = flashloan_fee_usd + gas_cost_usd + slippage_cost_usd + dex_fees_usd
            
            # 6. Calculate net profit
            net_profit_usd = gross_profit_usd - total_costs_usd
            
            # 7. Calculate profit margin
            profit_margin = (net_profit_usd / trade_amount_usd) * 100 if trade_amount_usd > 0 else 0
            
            # 8. Determine if profitable
            is_profitable = net_profit_usd > 0
            min_profit_threshold = 0.50  # $0.50 minimum profit
            meets_threshold = net_profit_usd >= min_profit_threshold
            
            return {
                'is_profitable': is_profitable,
                'meets_threshold': meets_threshold,
                'gross_profit_usd': gross_profit_usd,
                'net_profit_usd': net_profit_usd,
                'profit_margin_percent': profit_margin,
                'total_costs_usd': total_costs_usd,
                'cost_breakdown': {
                    'flashloan_fee_usd': flashloan_fee_usd,
                    'gas_cost_usd': gas_cost_usd,
                    'slippage_cost_usd': slippage_cost_usd,
                    'dex_fees_usd': dex_fees_usd
                },
                'trade_details': {
                    'trade_amount_usd': trade_amount_usd,
                    'chain': chain,
                    'flashloan_provider': flashloan_provider,
                    'complexity': complexity
                },
                'recommendation': self._get_recommendation(net_profit_usd, profit_margin, total_costs_usd)
            }
            
        except Exception as e:
            logger.error(f"Error calculating flashloan profitability: {e}")
            return {
                'is_profitable': False,
                'meets_threshold': False,
                'error': str(e)
            }
    
    def _get_recommendation(self, net_profit_usd: float, profit_margin: float, total_costs_usd: float) -> str:
        """Get trading recommendation based on profitability analysis."""
        if net_profit_usd < 0:
            return "REJECT: Net loss expected"
        elif net_profit_usd < 0.50:
            return "REJECT: Profit below minimum threshold ($0.50)"
        elif profit_margin < 0.1:
            return "CAUTION: Very low profit margin (<0.1%)"
        elif profit_margin < 0.5:
            return "ACCEPTABLE: Low but positive profit margin"
        elif profit_margin < 1.0:
            return "GOOD: Solid profit margin"
        else:
            return "EXCELLENT: High profit margin (>1%)"
    
    async def compare_flashloan_providers(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Compare profitability across different flashloan providers."""
        chain = opportunity.get('source_chain', 'arbitrum')
        
        # Available providers per chain
        available_providers = {
            'arbitrum': ['aave', 'balancer', 'radiant'],
            'base': ['aave', 'moonwell'],
            'optimism': ['aave'],
            'ethereum': ['aave', 'balancer', 'dydx']
        }
        
        providers = available_providers.get(chain, ['aave'])
        comparisons = {}
        
        for provider in providers:
            opportunity_copy = opportunity.copy()
            opportunity_copy['flashloan_provider'] = provider
            
            result = await self.calculate_flashloan_profitability(opportunity_copy)
            comparisons[provider] = result
        
        # Find best provider
        best_provider = None
        best_profit = -float('inf')
        
        for provider, result in comparisons.items():
            if result.get('is_profitable', False):
                net_profit = result.get('net_profit_usd', 0)
                if net_profit > best_profit:
                    best_profit = net_profit
                    best_provider = provider
        
        return {
            'comparisons': comparisons,
            'best_provider': best_provider,
            'best_profit_usd': best_profit,
            'recommendation': f"Use {best_provider}" if best_provider else "No profitable provider found"
        }
    
    async def calculate_optimal_trade_size(self, opportunity: Dict[str, Any], max_capital_usd: float) -> Dict[str, Any]:
        """Calculate optimal trade size considering costs and available capital."""
        # Test different trade sizes to find optimal profit
        test_sizes = [100, 500, 1000, 2500, 5000, 10000, 25000, 50000]
        test_sizes = [size for size in test_sizes if size <= max_capital_usd]
        
        if not test_sizes:
            return {'optimal_size_usd': 0, 'error': 'Insufficient capital for any trade size'}
        
        results = []
        
        for size in test_sizes:
            opportunity_copy = opportunity.copy()
            opportunity_copy['trade_amount_usd'] = size
            
            # Scale profit proportionally (simplified)
            base_profit = opportunity.get('estimated_profit_usd', 0)
            base_size = opportunity.get('trade_amount_usd', 1000)
            scaled_profit = (base_profit / base_size) * size if base_size > 0 else 0
            opportunity_copy['estimated_profit_usd'] = scaled_profit
            
            result = await self.calculate_flashloan_profitability(opportunity_copy)
            
            if result.get('is_profitable', False):
                results.append({
                    'trade_size_usd': size,
                    'net_profit_usd': result.get('net_profit_usd', 0),
                    'profit_margin_percent': result.get('profit_margin_percent', 0),
                    'total_costs_usd': result.get('total_costs_usd', 0)
                })
        
        if not results:
            return {'optimal_size_usd': 0, 'error': 'No profitable trade size found'}
        
        # Find size with highest net profit
        optimal = max(results, key=lambda x: x['net_profit_usd'])
        
        return {
            'optimal_size_usd': optimal['trade_size_usd'],
            'expected_profit_usd': optimal['net_profit_usd'],
            'profit_margin_percent': optimal['profit_margin_percent'],
            'all_results': results
        }

    async def calculate_capital_efficiency(self, opportunity: Dict[str, Any], available_capital_usd: float) -> Dict[str, Any]:
        """Calculate how efficiently capital is being used for flashloan arbitrage."""
        trade_amount_usd = opportunity.get('trade_amount_usd', 1000)

        # Calculate capital utilization
        capital_utilization = min(trade_amount_usd / available_capital_usd, 1.0) if available_capital_usd > 0 else 0

        # Get profitability
        profitability = await self.calculate_flashloan_profitability(opportunity)
        net_profit_usd = profitability.get('net_profit_usd', 0)

        # Calculate return on capital
        return_on_capital = (net_profit_usd / available_capital_usd) * 100 if available_capital_usd > 0 else 0

        # Calculate capital efficiency score
        efficiency_score = return_on_capital * capital_utilization

        return {
            'capital_utilization_percent': capital_utilization * 100,
            'return_on_capital_percent': return_on_capital,
            'efficiency_score': efficiency_score,
            'available_capital_usd': available_capital_usd,
            'trade_amount_usd': trade_amount_usd,
            'net_profit_usd': net_profit_usd,
            'recommendation': self._get_efficiency_recommendation(efficiency_score, capital_utilization)
        }

    def _get_efficiency_recommendation(self, efficiency_score: float, capital_utilization: float) -> str:
        """Get recommendation based on capital efficiency."""
        if efficiency_score > 5.0:
            return "EXCELLENT: High efficiency, execute immediately"
        elif efficiency_score > 2.0:
            return "GOOD: Solid efficiency, recommended"
        elif efficiency_score > 0.5:
            return "ACCEPTABLE: Low but positive efficiency"
        elif capital_utilization < 0.1:
            return "UNDERUTILIZED: Consider larger trade size"
        else:
            return "INEFFICIENT: Poor capital utilization"
