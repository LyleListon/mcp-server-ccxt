"""
Smart Wallet Manager
Automatic token swapping and wallet optimization for arbitrage.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class SmartWalletManager:
    """Smart wallet management for optimal arbitrage execution."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize smart wallet manager."""
        self.config = config
        
        # Optimal wallet composition for arbitrage
        self.target_composition = {
            'USDC': 0.40,  # 40% - Stable base currency
            'ETH': 0.30,   # 30% - Most liquid, highest opportunities
            'USDT': 0.20,  # 20% - Alternative stable, different opportunities
            'DAI': 0.10    # 10% - Backup stable, unique opportunities
        }
        
        # Minimum balances to maintain (in USD)
        self.min_balances = {
            'USDC': 100,   # Always keep $100 USDC
            'ETH': 150,    # Always keep ~0.06 ETH
            'USDT': 75,    # Always keep $75 USDT
            'DAI': 50      # Always keep $50 DAI
        }
        
        # Rebalancing thresholds
        self.rebalance_threshold = 0.15  # Rebalance if >15% off target
        self.min_swap_amount = 25        # Don't swap less than $25
        
        # Token priorities for different arbitrage types
        self.arbitrage_preferences = {
            'cross_chain': ['ETH', 'USDC', 'USDT'],      # Cross-chain prefers ETH
            'same_chain': ['USDC', 'USDT', 'DAI'],       # Same-chain prefers stables
            'high_volume': ['ETH', 'USDC'],              # High volume needs liquid tokens
            'low_latency': ['USDC', 'USDT']              # Fast execution needs stables
        }
        
        # Current wallet state
        self.current_balances = {}
        self.last_rebalance = None
        self.pending_swaps = {}
        
        logger.info("Smart wallet manager initialized")

    async def analyze_wallet_composition(self, wallet_address: str) -> Dict[str, Any]:
        """Analyze current wallet composition vs optimal."""
        try:
            # Get current balances (simulated for now)
            current_balances = await self._get_wallet_balances(wallet_address)
            
            # Calculate total value
            total_value = sum(current_balances.values())
            
            if total_value == 0:
                return {'error': 'Empty wallet'}
            
            # Calculate current percentages
            current_composition = {}
            for token, balance in current_balances.items():
                current_composition[token] = balance / total_value
            
            # Compare to target
            composition_analysis = {}
            rebalance_needed = False
            
            for token, target_pct in self.target_composition.items():
                current_pct = current_composition.get(token, 0)
                difference = abs(current_pct - target_pct)
                
                composition_analysis[token] = {
                    'current_usd': current_balances.get(token, 0),
                    'current_percentage': current_pct * 100,
                    'target_percentage': target_pct * 100,
                    'difference': difference * 100,
                    'status': 'optimal' if difference < self.rebalance_threshold else 'needs_rebalance'
                }
                
                if difference > self.rebalance_threshold:
                    rebalance_needed = True
            
            return {
                'total_value_usd': total_value,
                'current_balances': current_balances,
                'composition_analysis': composition_analysis,
                'rebalance_needed': rebalance_needed,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Wallet analysis error: {e}")
            return {'error': str(e)}

    async def _get_wallet_balances(self, wallet_address: str) -> Dict[str, float]:
        """Get current wallet balances (simulated with your $675 USDC)."""
        try:
            # Simulate your current wallet: $675 mostly in USDC
            simulated_balances = {
                'USDC': 625.0,  # $625 USDC (92.6%)
                'ETH': 35.0,    # $35 ETH (5.2%) 
                'USDT': 10.0,   # $10 USDT (1.5%)
                'DAI': 5.0      # $5 DAI (0.7%)
            }
            
            logger.info(f"Current wallet balances: {simulated_balances}")
            return simulated_balances
            
        except Exception as e:
            logger.error(f"Error getting wallet balances: {e}")
            return {}

    async def generate_rebalancing_plan(self, wallet_address: str) -> Dict[str, Any]:
        """Generate optimal rebalancing plan."""
        try:
            analysis = await self.analyze_wallet_composition(wallet_address)
            
            if 'error' in analysis:
                return analysis
            
            if not analysis['rebalance_needed']:
                return {
                    'rebalance_needed': False,
                    'message': 'Wallet composition is optimal'
                }
            
            total_value = analysis['total_value_usd']
            current_balances = analysis['current_balances']
            
            # Calculate target balances
            target_balances = {}
            for token, target_pct in self.target_composition.items():
                target_balances[token] = total_value * target_pct
            
            # Generate swap plan
            swap_plan = []
            
            for token, target_balance in target_balances.items():
                current_balance = current_balances.get(token, 0)
                difference = target_balance - current_balance
                
                if abs(difference) > self.min_swap_amount:
                    if difference > 0:
                        # Need to buy this token
                        swap_plan.append({
                            'action': 'buy',
                            'token': token,
                            'amount_usd': difference,
                            'priority': self._get_swap_priority(token, 'buy')
                        })
                    else:
                        # Need to sell this token
                        swap_plan.append({
                            'action': 'sell',
                            'token': token,
                            'amount_usd': abs(difference),
                            'priority': self._get_swap_priority(token, 'sell')
                        })
            
            # Sort by priority
            swap_plan.sort(key=lambda x: x['priority'])
            
            return {
                'rebalance_needed': True,
                'current_balances': current_balances,
                'target_balances': target_balances,
                'swap_plan': swap_plan,
                'estimated_gas_cost': len(swap_plan) * 15,  # $15 per swap
                'estimated_time_minutes': len(swap_plan) * 2  # 2 minutes per swap
            }
            
        except Exception as e:
            logger.error(f"Rebalancing plan error: {e}")
            return {'error': str(e)}

    def _get_swap_priority(self, token: str, action: str) -> int:
        """Get priority for token swaps (lower number = higher priority)."""
        # Priority based on arbitrage importance
        token_priorities = {
            'ETH': 1,    # Highest priority (most opportunities)
            'USDC': 2,   # High priority (stable base)
            'USDT': 3,   # Medium priority (alternative stable)
            'DAI': 4     # Lower priority (backup)
        }
        
        base_priority = token_priorities.get(token, 5)
        
        # Buying important tokens gets higher priority
        if action == 'buy':
            return base_priority
        else:
            return base_priority + 2

    async def execute_rebalancing(self, wallet_address: str, wallet_private_key: str) -> Dict[str, Any]:
        """Execute wallet rebalancing plan."""
        try:
            logger.info("🔄 Executing wallet rebalancing...")
            
            # Get rebalancing plan
            plan = await self.generate_rebalancing_plan(wallet_address)
            
            if 'error' in plan:
                return plan
            
            if not plan['rebalance_needed']:
                return plan
            
            swap_results = []
            total_gas_cost = 0
            
            # Execute swaps
            for swap in plan['swap_plan']:
                logger.info(f"   {swap['action'].upper()} ${swap['amount_usd']:.0f} {swap['token']}")
                
                # Simulate swap execution
                result = await self._execute_token_swap(
                    swap['action'],
                    swap['token'],
                    swap['amount_usd'],
                    wallet_private_key
                )
                
                swap_results.append(result)
                total_gas_cost += result.get('gas_cost_usd', 15)
                
                # Small delay between swaps
                await asyncio.sleep(1)
            
            logger.info(f"✅ Rebalancing complete! Gas cost: ${total_gas_cost:.2f}")
            
            return {
                'success': True,
                'swaps_executed': len(swap_results),
                'total_gas_cost': total_gas_cost,
                'swap_results': swap_results,
                'new_composition': await self.analyze_wallet_composition(wallet_address)
            }
            
        except Exception as e:
            logger.error(f"Rebalancing execution error: {e}")
            return {'error': str(e)}

    async def _execute_token_swap(self, action: str, token: str, amount_usd: float, wallet_private_key: str) -> Dict[str, Any]:
        """Execute a single token swap."""
        try:
            # Simulate swap execution
            # In production, this would use Uniswap/1inch APIs
            
            gas_cost = 15  # Estimate $15 gas per swap
            slippage = 0.002  # 0.2% slippage
            
            if action == 'buy':
                received_amount = amount_usd * (1 - slippage)
            else:
                received_amount = amount_usd * (1 - slippage)
            
            # Simulate execution time
            await asyncio.sleep(0.5)
            
            return {
                'success': True,
                'action': action,
                'token': token,
                'amount_usd': amount_usd,
                'received_amount_usd': received_amount,
                'gas_cost_usd': gas_cost,
                'slippage_percentage': slippage * 100,
                'transaction_hash': f"0x{'1' * 64}",  # Simulated
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'action': action,
                'token': token,
                'amount_usd': amount_usd
            }

    async def optimize_for_opportunity(self, opportunity: Dict[str, Any], wallet_address: str) -> Dict[str, Any]:
        """Optimize wallet for a specific arbitrage opportunity."""
        try:
            token = opportunity['token']
            trade_size_usd = opportunity.get('estimated_trade_size', 1000)
            
            # Check if we have enough of the required token
            current_balances = await self._get_wallet_balances(wallet_address)
            current_token_balance = current_balances.get(token, 0)
            
            if current_token_balance >= trade_size_usd:
                return {
                    'optimization_needed': False,
                    'message': f'Sufficient {token} balance for trade'
                }
            
            # Calculate how much we need
            needed_amount = trade_size_usd - current_token_balance
            
            # Find best token to swap from
            swap_candidates = []
            for source_token, balance in current_balances.items():
                if source_token != token and balance > self.min_balances.get(source_token, 0):
                    available_to_swap = balance - self.min_balances.get(source_token, 0)
                    if available_to_swap >= needed_amount:
                        swap_candidates.append({
                            'from_token': source_token,
                            'available_amount': available_to_swap,
                            'priority': self._get_swap_priority(source_token, 'sell')
                        })
            
            if not swap_candidates:
                return {
                    'optimization_needed': True,
                    'error': 'Insufficient funds for optimization'
                }
            
            # Choose best swap candidate
            best_candidate = min(swap_candidates, key=lambda x: x['priority'])
            
            return {
                'optimization_needed': True,
                'swap_plan': {
                    'from_token': best_candidate['from_token'],
                    'to_token': token,
                    'amount_usd': needed_amount,
                    'estimated_gas_cost': 15,
                    'estimated_time_minutes': 2
                }
            }
            
        except Exception as e:
            logger.error(f"Opportunity optimization error: {e}")
            return {'error': str(e)}

    def get_wallet_recommendations(self, total_value_usd: float) -> Dict[str, Any]:
        """Get wallet optimization recommendations."""
        recommendations = []
        
        # Size-based recommendations
        if total_value_usd < 500:
            recommendations.append({
                'type': 'composition',
                'message': 'Focus on USDC/ETH for small wallets',
                'suggested_composition': {'USDC': 0.6, 'ETH': 0.4}
            })
        elif total_value_usd < 2000:
            recommendations.append({
                'type': 'composition',
                'message': 'Add USDT for more opportunities',
                'suggested_composition': {'USDC': 0.5, 'ETH': 0.3, 'USDT': 0.2}
            })
        else:
            recommendations.append({
                'type': 'composition',
                'message': 'Full diversification recommended',
                'suggested_composition': self.target_composition
            })
        
        # Strategy recommendations
        recommendations.append({
            'type': 'strategy',
            'message': 'Rebalance weekly or when >15% off target'
        })
        
        recommendations.append({
            'type': 'gas',
            'message': 'Keep $50-100 ETH for gas fees'
        })
        
        return {
            'total_value_usd': total_value_usd,
            'recommendations': recommendations,
            'optimal_composition': self.target_composition
        }

    async def get_wallet_status(self, wallet_address: str) -> Dict[str, Any]:
        """Get comprehensive wallet status."""
        try:
            analysis = await self.analyze_wallet_composition(wallet_address)
            
            if 'error' in analysis:
                return analysis
            
            recommendations = self.get_wallet_recommendations(analysis['total_value_usd'])
            
            return {
                'wallet_address': wallet_address,
                'total_value_usd': analysis['total_value_usd'],
                'current_balances': analysis['current_balances'],
                'composition_analysis': analysis['composition_analysis'],
                'rebalance_needed': analysis['rebalance_needed'],
                'recommendations': recommendations['recommendations'],
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Wallet status error: {e}")
            return {'error': str(e)}
