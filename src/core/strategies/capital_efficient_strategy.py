"""
Capital Efficient Arbitrage Strategy

Focuses on high-frequency, low-capital arbitrage opportunities using flash loans
and smaller DEXs with less competition.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CapitalEfficientStrategy:
    """Strategy optimized for limited capital using flash loans and smaller DEXs."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize capital efficient strategy."""
        self.config = config
        self.strategy_config = config.get('trading', {})
        self.target_pairs = config.get('target_pairs', {})
        self.flash_loan_config = config.get('flash_loans', {})
        
        # Strategy parameters
        self.min_profit_threshold = self.strategy_config.get('min_profit_threshold', 0.3)
        self.max_trade_amount = self.strategy_config.get('max_trade_amount_usd', 5000)
        self.use_flash_loans = self.strategy_config.get('use_flash_loans', True)
        self.preferred_networks = self.strategy_config.get('preferred_networks', [])
        
        logger.info("Capital Efficient Strategy initialized")
    
    def get_priority_pairs(self) -> List[Dict[str, Any]]:
        """Get trading pairs prioritized for capital efficiency."""
        priority_pairs = []
        
        # Add stablecoin pairs (highest priority - frequent opportunities)
        for pair in self.target_pairs.get('stablecoins', []):
            priority_pairs.append({
                'base_token': pair['base'],
                'quote_token': pair['quote'],
                'priority': pair['priority'],
                'category': 'stablecoin',
                'expected_profit': 0.1,  # 0.1% typical for stablecoins
                'frequency': 'high',
                'capital_required': 1000  # Low capital requirement
            })
        
        # Add wrapped token pairs (almost guaranteed profit)
        for pair in self.target_pairs.get('wrapped_tokens', []):
            priority_pairs.append({
                'base_token': pair['base'],
                'quote_token': pair['quote'],
                'priority': pair['priority'],
                'category': 'wrapped',
                'expected_profit': 0.05,  # 0.05% typical for wrapped tokens
                'frequency': 'medium',
                'capital_required': 500   # Very low capital requirement
            })
        
        # Add major pairs (lower priority but higher profit potential)
        for pair in self.target_pairs.get('major_pairs', []):
            priority_pairs.append({
                'base_token': pair['base'],
                'quote_token': pair['quote'],
                'priority': pair['priority'],
                'category': 'major',
                'expected_profit': 0.5,  # 0.5% typical for major pairs
                'frequency': 'medium',
                'capital_required': 2000  # Medium capital requirement
            })
        
        # Sort by priority
        priority_pairs.sort(key=lambda x: x['priority'])
        
        return priority_pairs
    
    def filter_opportunities_by_capital(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter opportunities based on capital efficiency."""
        filtered_opportunities = []
        
        for opportunity in opportunities:
            # Check if opportunity meets capital efficiency criteria
            if self._is_capital_efficient(opportunity):
                # Add capital efficiency score
                opportunity['capital_efficiency_score'] = self._calculate_capital_efficiency_score(opportunity)
                filtered_opportunities.append(opportunity)
        
        # Sort by capital efficiency score
        filtered_opportunities.sort(key=lambda x: x.get('capital_efficiency_score', 0), reverse=True)
        
        return filtered_opportunities
    
    def _is_capital_efficient(self, opportunity: Dict[str, Any]) -> bool:
        """Check if an opportunity is capital efficient."""
        
        # Check minimum profit threshold
        profit_percentage = opportunity.get('expected_profit_percentage', 0)
        if profit_percentage < self.min_profit_threshold:
            return False
        
        # Check if flash loan is viable
        if self.use_flash_loans:
            input_amount = opportunity.get('input_amount', 0)
            if input_amount > self.max_trade_amount:
                return False
        
        # Check network preference (lower gas costs)
        path = opportunity.get('path', [])
        if path:
            # Check if any DEX in path is on preferred network
            dex_networks = [self._get_dex_network(edge.get('dex')) for edge in path]
            if not any(network in self.preferred_networks for network in dex_networks):
                return False
        
        # Check profit after all fees
        net_profit = opportunity.get('net_profit_usd', 0)
        if net_profit <= 0:
            return False
        
        return True
    
    def _calculate_capital_efficiency_score(self, opportunity: Dict[str, Any]) -> float:
        """Calculate capital efficiency score for an opportunity."""
        score = 0.0
        
        # Profit percentage weight (40%)
        profit_percentage = opportunity.get('expected_profit_percentage', 0)
        score += (profit_percentage / 5.0) * 0.4  # Normalize to 5% max
        
        # Net profit USD weight (30%)
        net_profit = opportunity.get('net_profit_usd', 0)
        score += min(net_profit / 100.0, 1.0) * 0.3  # Normalize to $100 max
        
        # Flash loan viability weight (20%)
        if self.use_flash_loans and opportunity.get('use_flash_loan', False):
            flash_loan_fee = opportunity.get('flash_loan_info', {}).get('fee_usd', 0)
            if flash_loan_fee < net_profit * 0.5:  # Fee less than 50% of profit
                score += 0.2
        
        # Network preference weight (10%)
        path = opportunity.get('path', [])
        if path:
            dex_networks = [self._get_dex_network(edge.get('dex')) for edge in path]
            preferred_count = sum(1 for network in dex_networks if network in self.preferred_networks)
            score += (preferred_count / len(dex_networks)) * 0.1
        
        return score
    
    def _get_dex_network(self, dex_name: str) -> str:
        """Get the network for a DEX."""
        dex_config = self.config.get('dexs', {}).get(dex_name, {})
        return dex_config.get('network', 'unknown')
    
    def optimize_trade_size(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize trade size for capital efficiency."""
        
        # Get current input amount
        current_amount = opportunity.get('input_amount', 0)
        
        # Calculate optimal amount based on liquidity and capital constraints
        path = opportunity.get('path', [])
        if not path:
            return opportunity
        
        # Find minimum liquidity in path
        min_liquidity = min(edge.get('liquidity', 0) for edge in path)
        
        # Calculate maximum safe trade size (1% of minimum liquidity)
        max_safe_amount = min_liquidity * 0.01 if min_liquidity > 0 else 1000
        
        # Apply capital constraints
        max_capital_amount = self.max_trade_amount
        
        # Choose optimal amount
        optimal_amount = min(current_amount, max_safe_amount, max_capital_amount)
        
        # Update opportunity with optimized amount
        optimized_opportunity = opportunity.copy()
        optimized_opportunity['input_amount'] = optimal_amount
        optimized_opportunity['optimized'] = True
        optimized_opportunity['optimization_reason'] = f"Optimized from ${current_amount:.2f} to ${optimal_amount:.2f}"
        
        # Recalculate profits with new amount
        profit_percentage = optimized_opportunity.get('expected_profit_percentage', 0)
        optimized_opportunity['expected_profit_usd'] = optimal_amount * (profit_percentage / 100.0)
        
        # Adjust net profit (subtract fees)
        gas_cost = optimized_opportunity.get('estimated_gas_cost_usd', 0)
        flash_loan_fee = 0
        if optimized_opportunity.get('use_flash_loan', False):
            flash_loan_info = optimized_opportunity.get('flash_loan_info', {})
            flash_loan_fee = optimal_amount * (flash_loan_info.get('fee_percentage', 0.09) / 100.0)
        
        optimized_opportunity['net_profit_usd'] = (
            optimized_opportunity['expected_profit_usd'] - gas_cost - flash_loan_fee
        )
        
        return optimized_opportunity
    
    def get_flash_loan_strategy(self, opportunity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get flash loan strategy for an opportunity."""
        
        if not self.use_flash_loans:
            return None
        
        input_token = opportunity.get('input_token')
        input_amount = opportunity.get('input_amount', 0)
        
        if not input_token or input_amount <= 0:
            return None
        
        # Find best flash loan provider
        best_provider = None
        lowest_fee = float('inf')
        
        for provider_name, provider_config in self.flash_loan_config.items():
            if not provider_config.get('enabled', False):
                continue
            
            fee_percentage = provider_config.get('fee_percentage', 0.09)
            max_amount = provider_config.get('max_amount_usd', 0)
            
            if input_amount <= max_amount and fee_percentage < lowest_fee:
                best_provider = provider_name
                lowest_fee = fee_percentage
        
        if not best_provider:
            return None
        
        return {
            'provider': best_provider,
            'token': input_token,
            'amount': input_amount,
            'fee_percentage': lowest_fee,
            'fee_amount': input_amount * (lowest_fee / 100.0),
            'viable': True
        }
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """Get summary of capital efficient strategy."""
        return {
            'strategy_name': 'Capital Efficient Arbitrage',
            'focus': 'Flash loan arbitrage on smaller DEXs',
            'target_pairs': len(self.get_priority_pairs()),
            'min_profit_threshold': f"{self.min_profit_threshold}%",
            'max_trade_amount': f"${self.max_trade_amount:,}",
            'use_flash_loans': self.use_flash_loans,
            'preferred_networks': self.preferred_networks,
            'advantages': [
                'No capital required (flash loans)',
                'Lower competition on smaller DEXs',
                'Lower gas costs on L2s',
                'High frequency opportunities'
            ],
            'risks': [
                'Flash loan fees reduce profit',
                'Lower liquidity on smaller DEXs',
                'Higher slippage risk',
                'Network congestion risk'
            ]
        }
