#!/usr/bin/env python3
"""
ENHANCED FLASHLOAN SYSTEM
Integrates gas reserves, profitability calculation, and capital safety buffers
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from web3 import Web3

from .gas_reserve_manager import GasReserveManager
from .flashloan_profitability_calculator import FlashloanProfitabilityCalculator
from .capital_safety_buffer import CapitalSafetyBuffer

logger = logging.getLogger(__name__)

class EnhancedFlashloanSystem:
    """Complete flashloan system with gas management, profitability analysis, and safety buffers."""
    
    def __init__(self, web3_connections: Dict[str, Web3], wallet_account, smart_wallet_manager):
        self.web3_connections = web3_connections
        self.wallet_account = wallet_account
        self.smart_wallet_manager = smart_wallet_manager
        
        # Initialize subsystems
        self.gas_manager = GasReserveManager(web3_connections, wallet_account, smart_wallet_manager)
        self.profitability_calculator = FlashloanProfitabilityCalculator(web3_connections)
        self.safety_buffer = CapitalSafetyBuffer(smart_wallet_manager, self.gas_manager)
        
        # System status
        self.system_ready = False
        self.last_health_check = None
        
    async def initialize(self) -> bool:
        """Initialize the enhanced flashloan system."""
        try:
            logger.info("🔥 Initializing Enhanced Flashloan System...")
            
            # 1. Update portfolio status
            logger.info("   📊 Updating portfolio status...")
            portfolio_status = await self.safety_buffer.update_portfolio_status()
            
            if 'error' in portfolio_status:
                logger.error(f"   ❌ Portfolio update failed: {portfolio_status['error']}")
                return False
            
            total_value = portfolio_status.get('total_portfolio_usd', 0)
            logger.info(f"   💰 Total portfolio value: ${total_value:.2f}")
            
            # 2. Check gas reserves
            logger.info("   ⛽ Checking gas reserves...")
            gas_summary = await self.gas_manager.get_gas_reserve_summary()
            
            logger.info(f"   📊 Gas reserves: {gas_summary['chains_optimal']} optimal, {gas_summary['chains_low']} low, {gas_summary['chains_critical']} critical")
            
            # 3. Auto-rebalance gas if needed
            if gas_summary['chains_low'] > 0 or gas_summary['chains_critical'] > 0:
                logger.info("   🔄 Auto-rebalancing gas reserves...")
                rebalance_result = await self.gas_manager.rebalance_gas_reserves()
                logger.info(f"   ✅ Gas rebalance: {rebalance_result['success']} successful actions")
            
            self.system_ready = True
            self.last_health_check = asyncio.get_event_loop().time()
            
            logger.info("✅ Enhanced Flashloan System ready!")
            return True
            
        except Exception as e:
            logger.error(f"Enhanced flashloan system initialization failed: {e}")
            return False
    
    async def evaluate_flashloan_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive evaluation of a flashloan opportunity."""
        try:
            chain = opportunity.get('source_chain', 'arbitrum')
            
            # 1. Check gas reserves
            gas_check = await self.gas_manager.can_execute_flashloan(chain)
            
            if not gas_check['can_execute']:
                return {
                    'recommended': False,
                    'reason': 'Insufficient gas reserves',
                    'gas_check': gas_check
                }
            
            # 2. Calculate profitability with all costs
            profitability = await self.profitability_calculator.calculate_flashloan_profitability(opportunity)
            
            if not profitability['meets_threshold']:
                return {
                    'recommended': False,
                    'reason': 'Below profitability threshold',
                    'profitability': profitability
                }
            
            # 3. Compare flashloan providers
            provider_comparison = await self.profitability_calculator.compare_flashloan_providers(opportunity)
            best_provider = provider_comparison['best_provider']
            
            if not best_provider:
                return {
                    'recommended': False,
                    'reason': 'No profitable flashloan provider',
                    'provider_comparison': provider_comparison
                }
            
            # 4. Check capital safety
            trade_amount = opportunity.get('trade_amount_usd', 1000)
            safety_check = await self.safety_buffer.check_trade_safety(trade_amount, chain)
            
            if not safety_check['safe_to_trade']:
                return {
                    'recommended': False,
                    'reason': 'Trade safety requirements not met',
                    'safety_check': safety_check
                }
            
            # 5. Calculate optimal trade size
            max_capital = safety_check['available_trading_usd']
            optimal_size = await self.profitability_calculator.calculate_optimal_trade_size(opportunity, max_capital)
            
            # 6. Final recommendation
            final_opportunity = opportunity.copy()
            final_opportunity['flashloan_provider'] = best_provider
            final_opportunity['trade_amount_usd'] = optimal_size.get('optimal_size_usd', trade_amount)
            
            # Recalculate profitability with optimal settings
            final_profitability = await self.profitability_calculator.calculate_flashloan_profitability(final_opportunity)
            
            return {
                'recommended': True,
                'optimized_opportunity': final_opportunity,
                'expected_profit_usd': final_profitability['net_profit_usd'],
                'profit_margin_percent': final_profitability['profit_margin_percent'],
                'best_provider': best_provider,
                'optimal_trade_size_usd': optimal_size.get('optimal_size_usd', trade_amount),
                'gas_check': gas_check,
                'profitability': final_profitability,
                'safety_check': safety_check,
                'provider_comparison': provider_comparison
            }
            
        except Exception as e:
            logger.error(f"Error evaluating flashloan opportunity: {e}")
            return {
                'recommended': False,
                'reason': f'Evaluation error: {str(e)}',
                'error': str(e)
            }
    
    async def execute_flashloan_arbitrage(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute flashloan arbitrage with full safety and profitability checks."""
        try:
            # 1. Evaluate opportunity
            evaluation = await self.evaluate_flashloan_opportunity(opportunity)
            
            if not evaluation['recommended']:
                return {
                    'success': False,
                    'error': f"Opportunity not recommended: {evaluation['reason']}",
                    'evaluation': evaluation
                }
            
            optimized_opportunity = evaluation['optimized_opportunity']
            chain = optimized_opportunity['source_chain']
            trade_amount = optimized_opportunity['trade_amount_usd']
            
            # 2. Allocate capital with safety buffers
            capital_allocation = await self.safety_buffer.allocate_capital_for_trade(trade_amount, chain)
            
            if not capital_allocation['success']:
                return {
                    'success': False,
                    'error': f"Capital allocation failed: {capital_allocation['error']}",
                    'capital_allocation': capital_allocation
                }
            
            # 3. Execute the flashloan (placeholder - integrate with actual flashloan executor)
            logger.info(f"🔥 EXECUTING FLASHLOAN ARBITRAGE:")
            logger.info(f"   💰 Trade amount: ${trade_amount:.2f}")
            logger.info(f"   ⛽ Provider: {optimized_opportunity['flashloan_provider']}")
            logger.info(f"   📈 Expected profit: ${evaluation['expected_profit_usd']:.2f}")
            logger.info(f"   🎯 Profit margin: {evaluation['profit_margin_percent']:.2f}%")
            
            # TODO: Integrate with actual flashloan execution
            # For now, simulate execution
            execution_result = {
                'success': True,
                'profit_usd': evaluation['expected_profit_usd'] * 0.9,  # 90% of expected (slippage)
                'gas_cost_usd': evaluation['profitability']['cost_breakdown']['gas_cost_usd'],
                'flashloan_fee_usd': evaluation['profitability']['cost_breakdown']['flashloan_fee_usd'],
                'transaction_hash': '0x' + '0' * 64  # Placeholder
            }
            
            # 4. Record trade result for risk management
            await self.safety_buffer.record_trade_result(execution_result)
            
            return {
                'success': execution_result['success'],
                'profit_usd': execution_result['profit_usd'],
                'evaluation': evaluation,
                'capital_allocation': capital_allocation,
                'execution_result': execution_result
            }
            
        except Exception as e:
            logger.error(f"Flashloan arbitrage execution error: {e}")
            
            # Record failed trade
            await self.safety_buffer.record_trade_result({
                'success': False,
                'profit_usd': 0,
                'error': str(e)
            })
            
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        try:
            # Get status from all subsystems
            gas_summary = await self.gas_manager.get_gas_reserve_summary()
            portfolio_summary = self.safety_buffer.get_portfolio_summary()
            
            return {
                'system_ready': self.system_ready,
                'last_health_check': self.last_health_check,
                'gas_reserves': gas_summary,
                'portfolio': portfolio_summary,
                'total_possible_flashloans': gas_summary['total_possible_flashloans'],
                'available_trading_capital_usd': portfolio_summary['safety_buffers']['available_trading_usd'],
                'daily_performance': portfolio_summary['daily_performance'],
                'risk_status': portfolio_summary['risk_status']
            }
            
        except Exception as e:
            return {
                'system_ready': False,
                'error': str(e)
            }
    
    async def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive system health check."""
        try:
            logger.info("🔍 Performing Enhanced Flashloan System health check...")
            
            # 1. Check gas reserves
            gas_summary = await self.gas_manager.get_gas_reserve_summary()
            
            # 2. Update portfolio
            await self.safety_buffer.update_portfolio_status()
            
            # 3. Auto-rebalance if needed
            rebalance_needed = gas_summary['chains_low'] > 0 or gas_summary['chains_critical'] > 0
            
            if rebalance_needed:
                logger.info("🔄 Auto-rebalancing during health check...")
                await self.gas_manager.rebalance_gas_reserves()
            
            self.last_health_check = asyncio.get_event_loop().time()
            
            health_status = {
                'healthy': gas_summary['chains_critical'] == 0,
                'gas_reserves_ok': gas_summary['chains_critical'] == 0,
                'rebalance_performed': rebalance_needed,
                'total_possible_flashloans': gas_summary['total_possible_flashloans'],
                'warnings': gas_summary['needs_attention']
            }
            
            logger.info(f"✅ Health check complete: {'Healthy' if health_status['healthy'] else 'Issues detected'}")
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'healthy': False,
                'error': str(e)
            }
