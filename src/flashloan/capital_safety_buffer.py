#!/usr/bin/env python3
"""
CAPITAL SAFETY BUFFER SYSTEM
Manages your $4,183 portfolio as safety buffer for flashloan operations
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CapitalSafetyBuffer:
    """Manages capital allocation and safety buffers for flashloan operations."""
    
    def __init__(self, smart_wallet_manager, gas_reserve_manager):
        self.smart_wallet_manager = smart_wallet_manager
        self.gas_reserve_manager = gas_reserve_manager
        
        # Safety buffer allocation (percentages of total portfolio)
        self.buffer_allocation = {
            'gas_reserves': 0.05,      # 5% for gas across all chains (~$209)
            'slippage_buffer': 0.15,   # 15% for slippage protection (~$627) - INCREASED!
            'emergency_reserve': 0.10, # 10% emergency fund (~$418)
            'trading_capital': 0.70    # 70% available for trading (~$2,928) - ADJUSTED
        }

        # Dynamic slippage buffer settings - SIMPLE 75% EXTRA
        self.dynamic_slippage = {
            'extra_buffer_multiplier': 0.75,  # 75% extra on top of calculated slippage cost
            'min_buffer_usd': 0.50,            # Minimum $0.50 buffer
            'max_buffer_usd': 50.0,            # Maximum $50 buffer
            'volatility_multiplier': 1.5       # Increase buffer during high volatility
        }
        
        # Risk management limits
        self.risk_limits = {
            'max_single_trade_percent': 0.25,    # Max 25% of trading capital per trade
            'max_daily_loss_percent': 0.10,      # Max 10% daily loss
            'max_consecutive_losses': 5,         # Stop after 5 consecutive losses
            'min_buffer_threshold': 0.15         # Maintain 15% minimum buffer
        }
        
        # Performance tracking
        self.daily_stats = {
            'trades_executed': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_profit_usd': 0.0,
            'total_loss_usd': 0.0,
            'consecutive_losses': 0,
            'last_reset': datetime.now().date()
        }
        
        # Capital allocation tracking
        self.capital_allocation = {
            'total_portfolio_usd': 0.0,
            'allocated_gas_usd': 0.0,
            'allocated_slippage_usd': 0.0,
            'allocated_emergency_usd': 0.0,
            'available_trading_usd': 0.0,
            'last_update': None
        }
    
    async def update_portfolio_status(self) -> Dict[str, Any]:
        """Update current portfolio status across all chains."""
        try:
            # Get total portfolio value from smart wallet manager
            total_value_usd = 0.0
            chain_balances = {}
            
            for chain in ['arbitrum', 'base', 'optimism', 'ethereum']:
                try:
                    balance_status = await self.smart_wallet_manager.get_smart_balance_status(chain)
                    chain_value = balance_status.get('total_wallet_value_usd', 0)
                    chain_balances[chain] = chain_value
                    total_value_usd += chain_value
                except Exception as e:
                    logger.warning(f"Could not get balance for {chain}: {e}")
                    chain_balances[chain] = 0
            
            # Calculate allocations
            gas_allocation = total_value_usd * self.buffer_allocation['gas_reserves']
            slippage_allocation = total_value_usd * self.buffer_allocation['slippage_buffer']
            emergency_allocation = total_value_usd * self.buffer_allocation['emergency_reserve']
            trading_allocation = total_value_usd * self.buffer_allocation['trading_capital']
            
            # Update capital allocation
            self.capital_allocation = {
                'total_portfolio_usd': total_value_usd,
                'allocated_gas_usd': gas_allocation,
                'allocated_slippage_usd': slippage_allocation,
                'allocated_emergency_usd': emergency_allocation,
                'available_trading_usd': trading_allocation,
                'last_update': datetime.now(),
                'chain_balances': chain_balances
            }
            
            return self.capital_allocation
            
        except Exception as e:
            logger.error(f"Error updating portfolio status: {e}")
            return {'error': str(e)}
    
    async def check_trade_safety(self, trade_amount_usd: float, chain: str) -> Dict[str, Any]:
        """Check if a trade meets safety requirements."""
        await self.update_portfolio_status()
        
        available_trading = self.capital_allocation['available_trading_usd']
        max_single_trade = available_trading * self.risk_limits['max_single_trade_percent']
        
        # Check daily stats reset
        if datetime.now().date() > self.daily_stats['last_reset']:
            self._reset_daily_stats()
        
        # Safety checks
        checks = {
            'trade_size_ok': trade_amount_usd <= max_single_trade,
            'daily_loss_ok': self._check_daily_loss_limit(),
            'consecutive_loss_ok': self.daily_stats['consecutive_losses'] < self.risk_limits['max_consecutive_losses'],
            'buffer_ok': self._check_buffer_adequacy(),
            'gas_reserves_ok': await self._check_gas_reserves(chain)
        }
        
        all_checks_pass = all(checks.values())
        
        safety_result = {
            'safe_to_trade': all_checks_pass,
            'trade_amount_usd': trade_amount_usd,
            'max_allowed_usd': max_single_trade,
            'available_trading_usd': available_trading,
            'safety_checks': checks,
            'warnings': self._generate_warnings(checks, trade_amount_usd, max_single_trade)
        }
        
        return safety_result
    
    async def allocate_capital_for_trade(self, trade_amount_usd: float, chain: str) -> Dict[str, Any]:
        """Allocate capital for a specific trade with dynamic slippage buffers."""
        safety_check = await self.check_trade_safety(trade_amount_usd, chain)

        if not safety_check['safe_to_trade']:
            return {
                'success': False,
                'error': 'Trade does not meet safety requirements',
                'safety_check': safety_check
            }

        # Calculate dynamic slippage buffer (your brilliant idea!)
        dynamic_slippage_buffer = self._calculate_dynamic_slippage_buffer(trade_amount_usd)
        gas_buffer = await self._calculate_gas_buffer(chain)

        total_required = trade_amount_usd + dynamic_slippage_buffer + gas_buffer
        
        # Check if we have enough capital
        available_trading = self.capital_allocation['available_trading_usd']
        
        if total_required > available_trading:
            return {
                'success': False,
                'error': f'Insufficient capital: need ${total_required:.2f}, have ${available_trading:.2f}'
            }
        
        return {
            'success': True,
            'allocated_trade_usd': trade_amount_usd,
            'allocated_slippage_buffer_usd': dynamic_slippage_buffer,
            'allocated_gas_buffer_usd': gas_buffer,
            'total_allocated_usd': total_required,
            'remaining_capital_usd': available_trading - total_required
        }
    
    async def record_trade_result(self, trade_result: Dict[str, Any]) -> None:
        """Record the result of a trade for risk management."""
        success = trade_result.get('success', False)
        profit_usd = trade_result.get('profit_usd', 0)
        
        # Update daily stats
        self.daily_stats['trades_executed'] += 1
        
        if success and profit_usd > 0:
            self.daily_stats['successful_trades'] += 1
            self.daily_stats['total_profit_usd'] += profit_usd
            self.daily_stats['consecutive_losses'] = 0  # Reset consecutive losses
        else:
            self.daily_stats['failed_trades'] += 1
            if profit_usd < 0:
                self.daily_stats['total_loss_usd'] += abs(profit_usd)
            self.daily_stats['consecutive_losses'] += 1
        
        # Log significant events
        if self.daily_stats['consecutive_losses'] >= 3:
            logger.warning(f"⚠️ {self.daily_stats['consecutive_losses']} consecutive losses - review strategy")
        
        if self.daily_stats['consecutive_losses'] >= self.risk_limits['max_consecutive_losses']:
            logger.critical(f"🚨 TRADING HALTED: {self.daily_stats['consecutive_losses']} consecutive losses")
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio and safety buffer summary."""
        net_daily_pnl = self.daily_stats['total_profit_usd'] - self.daily_stats['total_loss_usd']
        success_rate = (self.daily_stats['successful_trades'] / max(self.daily_stats['trades_executed'], 1)) * 100
        
        return {
            'portfolio': self.capital_allocation,
            'daily_performance': {
                **self.daily_stats,
                'net_pnl_usd': net_daily_pnl,
                'success_rate_percent': success_rate
            },
            'risk_status': {
                'consecutive_losses': self.daily_stats['consecutive_losses'],
                'max_allowed_losses': self.risk_limits['max_consecutive_losses'],
                'daily_loss_limit_usd': self.capital_allocation['total_portfolio_usd'] * self.risk_limits['max_daily_loss_percent'],
                'current_daily_loss_usd': self.daily_stats['total_loss_usd']
            },
            'safety_buffers': {
                'gas_reserves_usd': self.capital_allocation['allocated_gas_usd'],
                'slippage_buffer_usd': self.capital_allocation['allocated_slippage_usd'],
                'emergency_reserve_usd': self.capital_allocation['allocated_emergency_usd'],
                'available_trading_usd': self.capital_allocation['available_trading_usd']
            }
        }
    
    def _reset_daily_stats(self) -> None:
        """Reset daily statistics for new trading day."""
        self.daily_stats = {
            'trades_executed': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_profit_usd': 0.0,
            'total_loss_usd': 0.0,
            'consecutive_losses': 0,
            'last_reset': datetime.now().date()
        }
        logger.info("📊 Daily trading statistics reset")
    
    def _check_daily_loss_limit(self) -> bool:
        """Check if daily loss limit has been exceeded."""
        max_daily_loss = self.capital_allocation['total_portfolio_usd'] * self.risk_limits['max_daily_loss_percent']
        return self.daily_stats['total_loss_usd'] < max_daily_loss
    
    def _check_buffer_adequacy(self) -> bool:
        """Check if safety buffers are adequate."""
        total_buffers = (self.capital_allocation['allocated_gas_usd'] + 
                        self.capital_allocation['allocated_slippage_usd'] + 
                        self.capital_allocation['allocated_emergency_usd'])
        
        buffer_percentage = total_buffers / max(self.capital_allocation['total_portfolio_usd'], 1)
        return buffer_percentage >= self.risk_limits['min_buffer_threshold']
    
    async def _check_gas_reserves(self, chain: str) -> bool:
        """Check if gas reserves are adequate for the chain."""
        if not self.gas_reserve_manager:
            return True  # Assume OK if no gas manager
        
        gas_check = await self.gas_reserve_manager.can_execute_flashloan(chain)
        return gas_check.get('can_execute', False)
    
    async def _calculate_gas_buffer(self, chain: str) -> float:
        """Calculate required gas buffer for a chain."""
        # Base gas costs per chain (in USD)
        base_gas_costs = {
            'arbitrum': 5.0,   # ~$5 for flashloan
            'base': 3.0,       # ~$3 for flashloan
            'optimism': 3.0,   # ~$3 for flashloan
            'ethereum': 50.0   # ~$50 for flashloan (expensive!)
        }
        
        return base_gas_costs.get(chain, 5.0)
    
    def _calculate_dynamic_slippage_buffer(self, trade_amount_usd: float, calculated_slippage_cost_usd: float = None) -> float:
        """Calculate slippage buffer - simple 75% extra on top of slippage cost!"""

        # If slippage cost is provided, use 75% extra
        if calculated_slippage_cost_usd is not None:
            extra_buffer = calculated_slippage_cost_usd * self.dynamic_slippage['extra_buffer_multiplier']
        else:
            # Fallback: estimate 3% slippage cost, then add 75% extra
            estimated_slippage_cost = trade_amount_usd * 0.03  # 3% default slippage
            extra_buffer = estimated_slippage_cost * self.dynamic_slippage['extra_buffer_multiplier']

        # Apply minimum and maximum caps
        min_buffer = self.dynamic_slippage['min_buffer_usd']
        max_buffer = self.dynamic_slippage['max_buffer_usd']
        final_buffer = max(min_buffer, min(extra_buffer, max_buffer))

        return final_buffer

    def _generate_warnings(self, checks: Dict[str, bool], trade_amount: float, max_allowed: float) -> List[str]:
        """Generate warning messages based on safety checks."""
        warnings = []

        if not checks['trade_size_ok']:
            warnings.append(f"Trade size ${trade_amount:.2f} exceeds limit ${max_allowed:.2f}")

        if not checks['daily_loss_ok']:
            warnings.append("Daily loss limit exceeded")

        if not checks['consecutive_loss_ok']:
            warnings.append(f"Too many consecutive losses ({self.daily_stats['consecutive_losses']})")

        if not checks['buffer_ok']:
            warnings.append("Safety buffers below minimum threshold")

        if not checks['gas_reserves_ok']:
            warnings.append("Insufficient gas reserves")

        return warnings
