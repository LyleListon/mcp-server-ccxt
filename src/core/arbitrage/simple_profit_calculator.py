"""Simple profit calculator for arbitrage opportunities."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SimpleProfitCalculator:
    """Simple profit calculator for arbitrage opportunities."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the profit calculator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.gas_price_gwei = config.get('gas_price_gwei', 20)
        self.eth_price_usd = config.get('eth_price_usd', 3000)
    
    def calculate_profit(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate profit for an arbitrage opportunity.
        
        Args:
            opportunity: Opportunity data
            
        Returns:
            Profit calculation results
        """
        try:
            # Extract basic data
            estimated_profit = opportunity.get('estimated_profit', 0)
            profit_percentage = opportunity.get('profit_percentage', 0)
            gas_estimate = opportunity.get('gas_estimate', 150000)
            
            # Calculate gas cost
            gas_cost_eth = (gas_estimate * self.gas_price_gwei * 1e-9)
            gas_cost_usd = gas_cost_eth * self.eth_price_usd
            
            # Calculate net profit
            net_profit_usd = estimated_profit - gas_cost_usd
            
            # Calculate profit ratios
            if estimated_profit > 0:
                net_profit_percentage = (net_profit_usd / estimated_profit) * profit_percentage
            else:
                net_profit_percentage = 0
            
            return {
                'gross_profit_usd': estimated_profit,
                'gas_cost_usd': gas_cost_usd,
                'net_profit_usd': net_profit_usd,
                'profit_percentage': profit_percentage,
                'net_profit_percentage': net_profit_percentage,
                'profit_amount': net_profit_usd,
                'gas_cost': gas_cost_usd,
                'is_profitable': net_profit_usd > 0,
                'profit_margin': net_profit_percentage
            }
            
        except Exception as e:
            logger.error(f"Error calculating profit: {e}")
            return {
                'gross_profit_usd': 0,
                'gas_cost_usd': 0,
                'net_profit_usd': 0,
                'profit_percentage': 0,
                'net_profit_percentage': 0,
                'profit_amount': 0,
                'gas_cost': 0,
                'is_profitable': False,
                'profit_margin': 0
            }
