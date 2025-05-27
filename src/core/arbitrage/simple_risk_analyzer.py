"""Simple risk analyzer for arbitrage opportunities."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SimpleRiskAnalyzer:
    """Simple risk analyzer for arbitrage opportunities."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the risk analyzer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.max_slippage = config.get('max_slippage', 1.0)
        self.min_liquidity = config.get('min_liquidity', 10000)
    
    def analyze_risk(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze risk for an arbitrage opportunity.
        
        Args:
            opportunity: Opportunity data
            
        Returns:
            Risk analysis results
        """
        try:
            # Extract data
            liquidity = opportunity.get('liquidity', 0)
            profit_percentage = opportunity.get('profit_percentage', 0)
            gas_estimate = opportunity.get('gas_estimate', 150000)
            market_conditions = opportunity.get('market_conditions', {})
            
            # Calculate individual risk factors
            liquidity_risk = self._calculate_liquidity_risk(liquidity)
            slippage_risk = self._calculate_slippage_risk(profit_percentage, market_conditions)
            gas_risk = self._calculate_gas_risk(gas_estimate)
            market_risk = self._calculate_market_risk(market_conditions)
            
            # Calculate overall risk score (0-100, lower is better)
            risk_factors = [liquidity_risk, slippage_risk, gas_risk, market_risk]
            overall_risk = sum(risk_factors) / len(risk_factors)
            
            # Determine risk level
            if overall_risk <= 20:
                risk_level = 'low'
            elif overall_risk <= 50:
                risk_level = 'medium'
            elif overall_risk <= 75:
                risk_level = 'high'
            else:
                risk_level = 'very_high'
            
            return {
                'risk_score': overall_risk,
                'risk_level': risk_level,
                'liquidity_risk': liquidity_risk,
                'slippage_risk': slippage_risk,
                'gas_risk': gas_risk,
                'market_risk': market_risk,
                'risk_factors': {
                    'liquidity': 'low' if liquidity_risk <= 25 else 'medium' if liquidity_risk <= 50 else 'high',
                    'slippage': 'low' if slippage_risk <= 25 else 'medium' if slippage_risk <= 50 else 'high',
                    'gas': 'low' if gas_risk <= 25 else 'medium' if gas_risk <= 50 else 'high',
                    'market': 'low' if market_risk <= 25 else 'medium' if market_risk <= 50 else 'high'
                },
                'is_acceptable': overall_risk <= 60  # Configurable threshold
            }
            
        except Exception as e:
            logger.error(f"Error analyzing risk: {e}")
            return {
                'risk_score': 100,  # Maximum risk on error
                'risk_level': 'very_high',
                'liquidity_risk': 100,
                'slippage_risk': 100,
                'gas_risk': 100,
                'market_risk': 100,
                'risk_factors': {
                    'liquidity': 'high',
                    'slippage': 'high',
                    'gas': 'high',
                    'market': 'high'
                },
                'is_acceptable': False
            }
    
    def _calculate_liquidity_risk(self, liquidity: float) -> float:
        """Calculate liquidity risk (0-100)."""
        if liquidity >= self.min_liquidity * 10:  # 10x minimum is very safe
            return 10
        elif liquidity >= self.min_liquidity * 5:  # 5x minimum is safe
            return 20
        elif liquidity >= self.min_liquidity * 2:  # 2x minimum is moderate
            return 40
        elif liquidity >= self.min_liquidity:  # At minimum
            return 60
        else:  # Below minimum
            return 90
    
    def _calculate_slippage_risk(self, profit_percentage: float, market_conditions: Dict[str, Any]) -> float:
        """Calculate slippage risk (0-100)."""
        spread = market_conditions.get('spread', 0.01)
        volatility = market_conditions.get('volatility', 'medium')
        
        # Base slippage risk from spread
        if spread <= 0.005:  # 0.5% spread
            base_risk = 15
        elif spread <= 0.01:  # 1% spread
            base_risk = 25
        elif spread <= 0.02:  # 2% spread
            base_risk = 40
        else:  # >2% spread
            base_risk = 70
        
        # Adjust for volatility
        volatility_multiplier = {
            'low': 0.8,
            'medium': 1.0,
            'high': 1.5,
            'very_high': 2.0
        }.get(volatility, 1.0)
        
        # Adjust for profit margin (higher profit can absorb more slippage)
        if profit_percentage >= 2.0:  # 2%+ profit
            profit_adjustment = 0.7
        elif profit_percentage >= 1.0:  # 1%+ profit
            profit_adjustment = 0.85
        else:  # <1% profit
            profit_adjustment = 1.2
        
        return min(100, base_risk * volatility_multiplier * profit_adjustment)
    
    def _calculate_gas_risk(self, gas_estimate: int) -> float:
        """Calculate gas risk (0-100)."""
        # Risk increases with gas usage
        if gas_estimate <= 100000:
            return 10
        elif gas_estimate <= 200000:
            return 25
        elif gas_estimate <= 300000:
            return 40
        elif gas_estimate <= 500000:
            return 60
        else:
            return 80
    
    def _calculate_market_risk(self, market_conditions: Dict[str, Any]) -> float:
        """Calculate market risk (0-100)."""
        volatility = market_conditions.get('volatility', 'medium')
        
        volatility_risk = {
            'low': 15,
            'medium': 30,
            'high': 60,
            'very_high': 85
        }.get(volatility, 30)
        
        return volatility_risk
