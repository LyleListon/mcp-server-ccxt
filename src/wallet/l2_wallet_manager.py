"""
L2-First Wallet Manager
Optimized wallet management for L2-first arbitrage strategy.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class L2WalletManager:
    """L2-optimized wallet management for maximum arbitrage efficiency."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize L2 wallet manager."""
        self.config = config
        
        # L2-First wallet allocation strategy
        self.l2_allocation_strategy = {
            'arbitrum': 0.45,    # 45% - Primary L2 (cheapest, most liquid)
            'base': 0.25,        # 25% - Secondary L2 (growing ecosystem)
            'optimism': 0.15,    # 15% - Tertiary L2 (good opportunities)
            'ethereum': 0.15     # 15% - Mainnet (emergency/high-value only)
        }
        
        # Token allocation per chain
        self.token_allocation_per_chain = {
            'arbitrum': {
                'ETH': 0.35,     # 35% ETH (cross-chain opportunities)
                'USDC': 0.40,    # 40% USDC (stable base)
                'USDT': 0.20,    # 20% USDT (alternative stable)
                'DAI': 0.05      # 5% DAI (backup)
            },
            'base': {
                'ETH': 0.40,     # 40% ETH (Base loves ETH)
                'USDC': 0.50,    # 50% USDC (primary stable)
                'USDT': 0.10     # 10% USDT (minimal)
            },
            'optimism': {
                'ETH': 0.35,     # 35% ETH
                'USDC': 0.45,    # 45% USDC
                'USDT': 0.20     # 20% USDT
            },
            'ethereum': {
                'ETH': 0.60,     # 60% ETH (for bridging out)
                'USDC': 0.40     # 40% USDC (emergency trades)
            }
        }
        
        # L2 gas cost estimates (USD)
        self.l2_gas_costs = {
            'arbitrum': {
                'simple_swap': 0.15,
                'bridge_out': 8.00,
                'complex_arbitrage': 0.50
            },
            'base': {
                'simple_swap': 0.10,
                'bridge_out': 6.00,
                'complex_arbitrage': 0.30
            },
            'optimism': {
                'simple_swap': 0.20,
                'bridge_out': 10.00,
                'complex_arbitrage': 0.60
            },
            'ethereum': {
                'simple_swap': 15.00,
                'bridge_out': 25.00,
                'complex_arbitrage': 45.00
            }
        }
        
        # Bridge recommendations
        self.bridge_recommendations = {
            'ethereum_to_arbitrum': {
                'preferred': 'across',
                'alternatives': ['synapse', 'hop'],
                'cost_range': '$8-12',
                'time_minutes': '2-5'
            },
            'ethereum_to_base': {
                'preferred': 'across',
                'alternatives': ['synapse'],
                'cost_range': '$6-10',
                'time_minutes': '2-5'
            },
            'arbitrum_to_base': {
                'preferred': 'across',
                'alternatives': ['synapse'],
                'cost_range': '$3-6',
                'time_minutes': '1-3'
            },
            'arbitrum_to_optimism': {
                'preferred': 'hop',
                'alternatives': ['across'],
                'cost_range': '$4-8',
                'time_minutes': '2-4'
            }
        }
        
        logger.info("L2 Wallet Manager initialized")

    def calculate_optimal_l2_allocation(self, total_wallet_value: float) -> Dict[str, Dict[str, float]]:
        """Calculate optimal allocation across L2s and tokens."""
        try:
            allocation_plan = {}
            
            for chain, chain_percentage in self.l2_allocation_strategy.items():
                chain_value = total_wallet_value * chain_percentage
                allocation_plan[chain] = {
                    'total_usd': chain_value,
                    'tokens': {}
                }
                
                # Allocate tokens within each chain
                token_allocation = self.token_allocation_per_chain.get(chain, {})
                for token, token_percentage in token_allocation.items():
                    token_value = chain_value * token_percentage
                    allocation_plan[chain]['tokens'][token] = token_value
            
            return allocation_plan
            
        except Exception as e:
            logger.error(f"L2 allocation calculation error: {e}")
            return {}

    def generate_bridging_plan(self, current_balances: Dict[str, float], target_allocation: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """Generate step-by-step bridging plan."""
        try:
            bridging_steps = []
            
            # Assume current balances are on Ethereum
            current_ethereum_total = sum(current_balances.values())
            
            # Calculate how much to bridge to each L2
            for chain, allocation in target_allocation.items():
                if chain == 'ethereum':
                    continue  # Skip ethereum (source chain)
                
                target_value = allocation['total_usd']
                
                if target_value > 0:
                    # Determine best token to bridge
                    # Prefer USDC for stability, ETH for liquidity
                    if target_value > 200:
                        # Large allocation - bridge both USDC and ETH
                        usdc_amount = target_value * 0.6  # 60% USDC
                        eth_amount = target_value * 0.4   # 40% ETH
                        
                        bridging_steps.append({
                            'step': len(bridging_steps) + 1,
                            'action': 'bridge',
                            'from_chain': 'ethereum',
                            'to_chain': chain,
                            'token': 'USDC',
                            'amount_usd': usdc_amount,
                            'bridge': self.bridge_recommendations.get(f'ethereum_to_{chain}', {}).get('preferred', 'across'),
                            'estimated_cost': self._estimate_bridge_cost('ethereum', chain, usdc_amount),
                            'estimated_time_minutes': self._estimate_bridge_time('ethereum', chain)
                        })
                        
                        bridging_steps.append({
                            'step': len(bridging_steps) + 1,
                            'action': 'bridge',
                            'from_chain': 'ethereum',
                            'to_chain': chain,
                            'token': 'ETH',
                            'amount_usd': eth_amount,
                            'bridge': self.bridge_recommendations.get(f'ethereum_to_{chain}', {}).get('preferred', 'across'),
                            'estimated_cost': self._estimate_bridge_cost('ethereum', chain, eth_amount),
                            'estimated_time_minutes': self._estimate_bridge_time('ethereum', chain)
                        })
                    else:
                        # Small allocation - bridge USDC only
                        bridging_steps.append({
                            'step': len(bridging_steps) + 1,
                            'action': 'bridge',
                            'from_chain': 'ethereum',
                            'to_chain': chain,
                            'token': 'USDC',
                            'amount_usd': target_value,
                            'bridge': self.bridge_recommendations.get(f'ethereum_to_{chain}', {}).get('preferred', 'across'),
                            'estimated_cost': self._estimate_bridge_cost('ethereum', chain, target_value),
                            'estimated_time_minutes': self._estimate_bridge_time('ethereum', chain)
                        })
            
            return bridging_steps
            
        except Exception as e:
            logger.error(f"Bridging plan generation error: {e}")
            return []

    def _estimate_bridge_cost(self, from_chain: str, to_chain: str, amount_usd: float) -> float:
        """Estimate bridge cost."""
        # Base costs
        base_costs = {
            'ethereum_to_arbitrum': 10.0,
            'ethereum_to_base': 8.0,
            'ethereum_to_optimism': 12.0,
            'arbitrum_to_base': 5.0,
            'arbitrum_to_optimism': 6.0,
            'base_to_optimism': 4.0
        }
        
        route = f"{from_chain}_to_{to_chain}"
        base_cost = base_costs.get(route, 15.0)
        
        # Add percentage fee (typically 0.04-0.1%)
        percentage_fee = amount_usd * 0.0005  # 0.05%
        
        return base_cost + percentage_fee

    def _estimate_bridge_time(self, from_chain: str, to_chain: str) -> int:
        """Estimate bridge time in minutes."""
        times = {
            'ethereum_to_arbitrum': 3,
            'ethereum_to_base': 2,
            'ethereum_to_optimism': 4,
            'arbitrum_to_base': 2,
            'arbitrum_to_optimism': 3,
            'base_to_optimism': 2
        }
        
        route = f"{from_chain}_to_{to_chain}"
        return times.get(route, 5)

    def get_l2_arbitrage_advantages(self) -> Dict[str, Any]:
        """Get L2 arbitrage advantages analysis."""
        return {
            'cost_savings': {
                'arbitrum_vs_ethereum': '95% cheaper gas',
                'base_vs_ethereum': '97% cheaper gas',
                'optimism_vs_ethereum': '93% cheaper gas'
            },
            'profit_thresholds': {
                'arbitrum': '$0.02 minimum (vs $0.25 on Ethereum)',
                'base': '$0.02 minimum (vs $0.25 on Ethereum)',
                'optimism': '$0.03 minimum (vs $0.25 on Ethereum)'
            },
            'opportunity_multiplier': {
                'arbitrum': '8-12x more opportunities',
                'base': '10-15x more opportunities',
                'optimism': '6-10x more opportunities'
            },
            'execution_speed': {
                'arbitrum': '1-2 second confirmations',
                'base': '1-2 second confirmations',
                'optimism': '1-2 second confirmations'
            }
        }

    def get_bridging_recommendations(self, wallet_value: float) -> Dict[str, Any]:
        """Get personalized bridging recommendations."""
        try:
            optimal_allocation = self.calculate_optimal_l2_allocation(wallet_value)
            
            recommendations = {
                'strategy': 'L2-First Arbitrage Dominance',
                'total_wallet_value': wallet_value,
                'optimal_allocation': optimal_allocation,
                'key_benefits': [
                    f'Save 80-95% on gas costs',
                    f'Access 5-15x more arbitrage opportunities',
                    f'Enable $0.02+ profit trades (vs $0.25+ on mainnet)',
                    f'Faster execution and higher frequency trading'
                ],
                'immediate_actions': [
                    f'Bridge ${optimal_allocation["arbitrum"]["total_usd"]:.0f} to Arbitrum (primary)',
                    f'Bridge ${optimal_allocation["base"]["total_usd"]:.0f} to Base (secondary)',
                    f'Keep ${optimal_allocation["ethereum"]["total_usd"]:.0f} on Ethereum (emergency)'
                ],
                'expected_results': {
                    'daily_trades': '50-200 (vs 5-20 on mainnet)',
                    'profit_per_trade': '$0.02-5.00 (vs $0.25-5.00 on mainnet)',
                    'daily_profit_potential': '$5-50 (vs $1-20 on mainnet)'
                }
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Bridging recommendations error: {e}")
            return {}

    def get_chain_specific_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Get chain-specific arbitrage strategies."""
        return {
            'arbitrum': {
                'focus': 'High-frequency, low-cost arbitrage',
                'best_pairs': ['ETH/USDC', 'USDC/USDT', 'ETH/DAI'],
                'min_profit': '$0.02',
                'gas_cost': '$0.10-0.50',
                'advantages': ['Lowest fees', 'Highest liquidity', 'Most DEXs']
            },
            'base': {
                'focus': 'Coinbase ecosystem arbitrage',
                'best_pairs': ['ETH/USDC', 'USDC/USDT'],
                'min_profit': '$0.02',
                'gas_cost': '$0.05-0.30',
                'advantages': ['Ultra-low fees', 'Coinbase backing', 'Growing liquidity']
            },
            'optimism': {
                'focus': 'OP token incentivized trading',
                'best_pairs': ['ETH/USDC', 'OP/ETH'],
                'min_profit': '$0.03',
                'gas_cost': '$0.15-0.60',
                'advantages': ['OP rewards', 'Good liquidity', 'Established ecosystem']
            },
            'ethereum': {
                'focus': 'High-value arbitrage only',
                'best_pairs': ['ETH/USDC', 'WBTC/ETH'],
                'min_profit': '$5.00',
                'gas_cost': '$15-50',
                'advantages': ['Highest liquidity', 'Most DEXs', 'Largest opportunities']
            }
        }

    def calculate_roi_projection(self, wallet_value: float, days: int = 30) -> Dict[str, Any]:
        """Calculate ROI projection for L2-first strategy."""
        try:
            # Conservative estimates
            daily_trades = {
                'arbitrum': 25,    # 25 trades/day on Arbitrum
                'base': 15,        # 15 trades/day on Base
                'optimism': 10,    # 10 trades/day on Optimism
                'ethereum': 2      # 2 trades/day on Ethereum (high-value only)
            }
            
            avg_profit_per_trade = {
                'arbitrum': 0.15,   # $0.15 average profit
                'base': 0.12,       # $0.12 average profit
                'optimism': 0.20,   # $0.20 average profit
                'ethereum': 2.50    # $2.50 average profit
            }
            
            allocation = self.calculate_optimal_l2_allocation(wallet_value)
            
            daily_profit = 0
            for chain, trades in daily_trades.items():
                chain_allocation = allocation.get(chain, {}).get('total_usd', 0)
                if chain_allocation > 0:
                    profit = trades * avg_profit_per_trade[chain]
                    daily_profit += profit
            
            monthly_profit = daily_profit * days
            roi_percentage = (monthly_profit / wallet_value) * 100
            
            return {
                'wallet_value': wallet_value,
                'projection_days': days,
                'daily_profit_estimate': daily_profit,
                'monthly_profit_estimate': monthly_profit,
                'roi_percentage': roi_percentage,
                'break_even_days': max(1, wallet_value / (daily_profit * 365) * 365) if daily_profit > 0 else float('inf'),
                'confidence': 'Conservative estimate based on L2 cost advantages'
            }
            
        except Exception as e:
            logger.error(f"ROI projection error: {e}")
            return {}
