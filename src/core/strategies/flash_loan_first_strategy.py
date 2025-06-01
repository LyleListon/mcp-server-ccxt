"""
Flash Loan First Strategy

Every trade uses flash loans by default. This maximizes capital efficiency
and allows access to large arbitrage opportunities regardless of available capital.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)


class FlashLoanFirstStrategy:
    """
    Strategy that uses flash loans for EVERY arbitrage trade.
    
    Benefits:
    - Zero capital requirement (just gas)
    - Access to unlimited trade sizes
    - Maximum capital efficiency
    - Risk-free arbitrage (flash loan reverts if unprofitable)
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize flash loan first strategy."""
        self.config = config
        
        # Flash loan configuration
        self.flash_loan_config = config.get('flash_loans', {})
        self.providers = self.flash_loan_config.get('providers', {})
        
        # Trading parameters
        self.min_profit_after_fees = Decimal(str(self.flash_loan_config.get('min_profit_after_fees', 3.0)))
        self.max_trade_amount = Decimal(str(config.get('trading', {}).get('max_trade_amount_usd', 100000)))
        self.min_trade_amount = Decimal(str(config.get('trading', {}).get('min_trade_amount_usd', 500)))
        
        # Performance tracking
        self.total_flash_loans = 0
        self.successful_flash_loans = 0
        self.total_borrowed = Decimal('0')
        self.total_fees_paid = Decimal('0')
        self.total_profit = Decimal('0')
        
        logger.info("Flash Loan First Strategy initialized")
        logger.info(f"Min profit after fees: ${self.min_profit_after_fees}")
        logger.info(f"Trade size range: ${self.min_trade_amount} - ${self.max_trade_amount}")

    def evaluate_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate arbitrage opportunity with flash loan optimization.
        
        Every opportunity is automatically evaluated for flash loan viability.
        """
        try:
            # Extract opportunity details
            input_token = opportunity.get('input_token', 'USDC')
            output_token = opportunity.get('output_token', 'USDC')
            profit_percentage = Decimal(str(opportunity.get('profit_percentage', 0)))
            network = opportunity.get('network', 'arbitrum')
            
            # Calculate optimal trade size for flash loans
            optimal_size = self._calculate_optimal_flash_loan_size(opportunity)
            
            if optimal_size < self.min_trade_amount:
                logger.debug(f"Opportunity too small for flash loan: ${optimal_size}")
                return self._create_rejection_result(opportunity, "Trade size too small")
            
            # Find best flash loan provider
            best_provider = self._find_best_flash_loan_provider(
                token=input_token,
                amount=optimal_size,
                network=network
            )
            
            if not best_provider:
                logger.debug(f"No flash loan provider available for {input_token} on {network}")
                return self._create_rejection_result(opportunity, "No flash loan provider available")
            
            # Calculate flash loan costs
            flash_loan_fee = self._calculate_flash_loan_fee(optimal_size, best_provider)
            gas_cost = self._estimate_gas_cost(network, best_provider)
            
            # Calculate profits
            gross_profit = optimal_size * (profit_percentage / 100)
            net_profit = gross_profit - flash_loan_fee - gas_cost
            
            # Check profitability
            if net_profit < self.min_profit_after_fees:
                logger.debug(f"Flash loan not profitable: ${net_profit} < ${self.min_profit_after_fees}")
                return self._create_rejection_result(opportunity, f"Insufficient profit: ${net_profit:.2f}")
            
            # Create enhanced opportunity
            enhanced_opportunity = opportunity.copy()
            enhanced_opportunity.update({
                'strategy': 'flash_loan_first',
                'use_flash_loan': True,
                'flash_loan_provider': best_provider['name'],
                'flash_loan_amount': float(optimal_size),
                'flash_loan_fee': float(flash_loan_fee),
                'flash_loan_fee_percentage': best_provider['fee_percentage'],
                'estimated_gas_cost': float(gas_cost),
                'gross_profit_usd': float(gross_profit),
                'net_profit_usd': float(net_profit),
                'profit_margin': float((net_profit / optimal_size) * 100),
                'capital_efficiency_score': float(net_profit / gas_cost) if gas_cost > 0 else 0,
                'flash_loan_viable': True,
                'execution_plan': self._create_execution_plan(enhanced_opportunity, best_provider)
            })
            
            logger.info(f"Flash loan opportunity: {input_token}/{output_token} "
                       f"${optimal_size:.0f} → ${net_profit:.2f} profit")
            
            return enhanced_opportunity
            
        except Exception as e:
            logger.error(f"Error evaluating flash loan opportunity: {e}")
            return self._create_rejection_result(opportunity, f"Evaluation error: {e}")

    def _calculate_optimal_flash_loan_size(self, opportunity: Dict[str, Any]) -> Decimal:
        """Calculate optimal trade size for flash loan arbitrage."""
        try:
            # Base calculation on profit percentage and available liquidity
            profit_percentage = Decimal(str(opportunity.get('profit_percentage', 0)))
            min_liquidity = Decimal(str(opportunity.get('min_liquidity_usd', 100000)))
            
            # Start with a reasonable base size
            base_size = min(Decimal('10000'), min_liquidity * Decimal('0.1'))  # 10% of liquidity
            
            # Scale based on profit percentage
            if profit_percentage > 1.0:  # High profit opportunities
                optimal_size = min(base_size * 3, self.max_trade_amount)
            elif profit_percentage > 0.5:  # Medium profit opportunities
                optimal_size = min(base_size * 2, self.max_trade_amount)
            else:  # Lower profit opportunities
                optimal_size = min(base_size, self.max_trade_amount)
            
            # Ensure minimum size
            optimal_size = max(optimal_size, self.min_trade_amount)
            
            return optimal_size
            
        except Exception as e:
            logger.error(f"Error calculating optimal flash loan size: {e}")
            return self.min_trade_amount

    def _find_best_flash_loan_provider(self, token: str, amount: Decimal, network: str) -> Optional[Dict[str, Any]]:
        """Find the best flash loan provider for the given parameters."""
        try:
            best_provider = None
            lowest_cost = Decimal('inf')
            
            for provider_name, provider_config in self.providers.items():
                if not provider_config.get('enabled', False):
                    continue
                
                # Check network support
                if network not in provider_config.get('networks', []):
                    continue
                
                # Check amount limits
                max_amount = Decimal(str(provider_config.get('max_amount_usd', 0)))
                if amount > max_amount:
                    continue
                
                # Calculate total cost (fee + estimated gas premium)
                fee_percentage = Decimal(str(provider_config.get('fee_percentage', 0)))
                fee_cost = amount * (fee_percentage / 100)
                
                # Add gas premium for different providers
                gas_premium = Decimal('1') if provider_name == 'balancer' else Decimal('2')
                total_cost = fee_cost + gas_premium
                
                if total_cost < lowest_cost:
                    lowest_cost = total_cost
                    best_provider = {
                        'name': provider_name,
                        'fee_percentage': float(fee_percentage),
                        'max_amount': float(max_amount),
                        'networks': provider_config.get('networks', []),
                        'total_cost': float(total_cost),
                        'description': provider_config.get('description', '')
                    }
            
            if best_provider:
                logger.debug(f"Best flash loan provider: {best_provider['name']} "
                           f"(${best_provider['total_cost']:.2f} cost)")
            
            return best_provider
            
        except Exception as e:
            logger.error(f"Error finding flash loan provider: {e}")
            return None

    def _calculate_flash_loan_fee(self, amount: Decimal, provider: Dict[str, Any]) -> Decimal:
        """Calculate flash loan fee for the given amount and provider."""
        fee_percentage = Decimal(str(provider.get('fee_percentage', 0)))
        return amount * (fee_percentage / 100)

    def _estimate_gas_cost(self, network: str, provider: Dict[str, Any]) -> Decimal:
        """Estimate gas cost for flash loan execution."""
        # Base gas costs by network (in USD)
        base_gas_costs = {
            'arbitrum': Decimal('3'),
            'optimism': Decimal('2'),
            'base': Decimal('2'),
            'polygon': Decimal('1'),
            'bsc': Decimal('1'),
            'fantom': Decimal('1'),
            'avalanche': Decimal('2'),
            'gnosis': Decimal('1'),
            'ethereum': Decimal('50')  # Much higher for mainnet
        }
        
        base_cost = base_gas_costs.get(network, Decimal('5'))
        
        # Add provider-specific gas overhead
        provider_overhead = {
            'aave': Decimal('1.5'),
            'balancer': Decimal('1.2'),
            'dydx': Decimal('1.3')
        }
        
        overhead = provider_overhead.get(provider.get('name', ''), Decimal('1'))
        
        return base_cost * overhead

    def _create_execution_plan(self, opportunity: Dict[str, Any], provider: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed execution plan for flash loan arbitrage."""
        return {
            'steps': [
                {
                    'step': 1,
                    'action': 'flash_loan_borrow',
                    'provider': provider['name'],
                    'token': opportunity.get('input_token'),
                    'amount': opportunity.get('flash_loan_amount'),
                    'description': f"Borrow ${opportunity.get('flash_loan_amount'):,.0f} from {provider['name']}"
                },
                {
                    'step': 2,
                    'action': 'arbitrage_trade',
                    'buy_dex': opportunity.get('buy_dex'),
                    'sell_dex': opportunity.get('sell_dex'),
                    'description': f"Execute arbitrage: {opportunity.get('buy_dex')} → {opportunity.get('sell_dex')}"
                },
                {
                    'step': 3,
                    'action': 'flash_loan_repay',
                    'provider': provider['name'],
                    'amount': opportunity.get('flash_loan_amount'),
                    'fee': opportunity.get('flash_loan_fee'),
                    'description': f"Repay ${opportunity.get('flash_loan_amount'):,.0f} + ${opportunity.get('flash_loan_fee'):.2f} fee"
                },
                {
                    'step': 4,
                    'action': 'profit_capture',
                    'amount': opportunity.get('net_profit_usd'),
                    'description': f"Capture ${opportunity.get('net_profit_usd'):.2f} profit"
                }
            ],
            'estimated_execution_time': '15-30 seconds',
            'risk_level': 'low',
            'capital_required': opportunity.get('estimated_gas_cost', 0)
        }

    def _create_rejection_result(self, opportunity: Dict[str, Any], reason: str) -> Dict[str, Any]:
        """Create rejection result for non-viable opportunities."""
        rejected_opportunity = opportunity.copy()
        rejected_opportunity.update({
            'strategy': 'flash_loan_first',
            'use_flash_loan': False,
            'flash_loan_viable': False,
            'rejection_reason': reason,
            'net_profit_usd': 0,
            'capital_efficiency_score': 0
        })
        return rejected_opportunity

    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get strategy performance statistics."""
        success_rate = (self.successful_flash_loans / self.total_flash_loans * 100) if self.total_flash_loans > 0 else 0
        avg_profit = (self.total_profit / self.successful_flash_loans) if self.successful_flash_loans > 0 else 0
        
        return {
            'strategy_name': 'flash_loan_first',
            'total_flash_loans': self.total_flash_loans,
            'successful_flash_loans': self.successful_flash_loans,
            'success_rate_percentage': round(success_rate, 2),
            'total_borrowed_usd': float(self.total_borrowed),
            'total_fees_paid_usd': float(self.total_fees_paid),
            'total_profit_usd': float(self.total_profit),
            'average_profit_per_trade': float(avg_profit),
            'capital_efficiency': 'infinite' if self.total_profit > 0 else 0
        }

    def update_performance(self, execution_result: Dict[str, Any]) -> None:
        """Update strategy performance metrics."""
        self.total_flash_loans += 1
        
        if execution_result.get('success', False):
            self.successful_flash_loans += 1
            self.total_borrowed += Decimal(str(execution_result.get('flash_loan_amount', 0)))
            self.total_fees_paid += Decimal(str(execution_result.get('flash_loan_fee', 0)))
            self.total_profit += Decimal(str(execution_result.get('net_profit', 0)))
        
        logger.info(f"Strategy stats: {self.successful_flash_loans}/{self.total_flash_loans} success, "
                   f"${self.total_profit:.2f} total profit")
