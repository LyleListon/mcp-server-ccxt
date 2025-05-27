"""
Arbitrage Execution Engine
Automated execution of cross-chain arbitrage opportunities using flash loans.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of an arbitrage execution."""
    success: bool
    transaction_hash: Optional[str]
    profit_usd: float
    gas_cost_usd: float
    execution_time_ms: int
    error_message: Optional[str]
    timestamp: datetime


class ArbitrageExecutor:
    """Automated arbitrage execution engine."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize arbitrage executor."""
        self.config = config
        self.execution_config = config.get('execution', {})

        # Execution parameters - DIME COLLECTOR MODE!
        self.min_profit_usd = self.execution_config.get('min_profit_usd', 0.10)  # 10 cents minimum!
        self.max_trade_size_usd = self.execution_config.get('max_trade_size_usd', 5000)  # Smaller trades for dimes
        self.max_slippage_percentage = self.execution_config.get('max_slippage_percentage', 0.5)  # Tighter slippage
        self.execution_timeout_seconds = self.execution_config.get('execution_timeout_seconds', 15)  # Faster execution

        # Bridge configurations
        self.bridges = {
            'across': {
                'name': 'Across Protocol',
                'fee_percentage': 0.05,
                'execution_time_minutes': 2,
                'supported_chains': ['ethereum', 'arbitrum', 'optimism', 'base', 'polygon'],
                'api_url': 'https://api.across.to',
                'enabled': True
            },
            'stargate': {
                'name': 'Stargate Finance',
                'fee_percentage': 0.06,
                'execution_time_minutes': 1,
                'supported_chains': ['ethereum', 'arbitrum', 'optimism', 'polygon', 'bsc'],
                'api_url': 'https://api.stargate.finance',
                'enabled': True
            },
            'hop': {
                'name': 'Hop Protocol',
                'fee_percentage': 0.04,
                'execution_time_minutes': 5,
                'supported_chains': ['ethereum', 'arbitrum', 'optimism', 'polygon'],
                'api_url': 'https://api.hop.exchange',
                'enabled': True
            }
        }

        # Flash loan providers
        self.flash_loan_providers = {
            'aave': {
                'name': 'Aave V3',
                'fee_percentage': 0.09,
                'max_amount_usd': 100000000,  # $100M
                'supported_chains': ['ethereum', 'arbitrum', 'optimism', 'polygon', 'base'],
                'enabled': True
            },
            'balancer': {
                'name': 'Balancer',
                'fee_percentage': 0.0,  # Free!
                'max_amount_usd': 50000000,  # $50M
                'supported_chains': ['ethereum', 'arbitrum', 'polygon'],
                'enabled': True
            }
        }

        # Execution statistics
        self.stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_profit_usd': 0.0,
            'total_gas_cost_usd': 0.0,
            'average_execution_time_ms': 0,
            'best_profit_usd': 0.0,
            'execution_history': []
        }

        logger.info("Arbitrage executor initialized")

    async def execute_opportunity(self, opportunity: Dict[str, Any]) -> ExecutionResult:
        """Execute an arbitrage opportunity."""
        start_time = datetime.now()

        try:
            logger.info(f"🚀 Executing arbitrage: {opportunity['token']} {opportunity['direction']}")

            # Validate opportunity
            validation_result = await self._validate_opportunity(opportunity)
            if not validation_result['valid']:
                return ExecutionResult(
                    success=False,
                    transaction_hash=None,
                    profit_usd=0.0,
                    gas_cost_usd=0.0,
                    execution_time_ms=0,
                    error_message=validation_result['error'],
                    timestamp=start_time
                )

            # Calculate optimal trade size
            trade_size = self._calculate_optimal_trade_size(opportunity)

            # Select best execution strategy
            strategy = await self._select_execution_strategy(opportunity, trade_size)

            # Execute the arbitrage
            execution_result = await self._execute_arbitrage_strategy(opportunity, strategy, trade_size)

            # Update statistics
            self._update_statistics(execution_result)

            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            execution_result.execution_time_ms = execution_time_ms

            if execution_result.success:
                logger.info(f"✅ Arbitrage executed successfully: ${execution_result.profit_usd:.2f} profit")
            else:
                logger.error(f"❌ Arbitrage execution failed: {execution_result.error_message}")

            return execution_result

        except Exception as e:
            logger.error(f"💥 Execution error: {e}")
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            return ExecutionResult(
                success=False,
                transaction_hash=None,
                profit_usd=0.0,
                gas_cost_usd=0.0,
                execution_time_ms=execution_time_ms,
                error_message=str(e),
                timestamp=start_time
            )

    async def _validate_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an arbitrage opportunity before execution."""
        try:
            # Check minimum profit
            estimated_profit = self._estimate_net_profit(opportunity)
            if estimated_profit < self.min_profit_usd:
                return {
                    'valid': False,
                    'error': f"Profit ${estimated_profit:.2f} below minimum ${self.min_profit_usd}"
                }

            # Check supported chains
            source_chain = opportunity['source_chain']
            target_chain = opportunity['target_chain']

            if not self._chains_supported(source_chain, target_chain):
                return {
                    'valid': False,
                    'error': f"Chain pair {source_chain}-{target_chain} not supported"
                }

            # Check profit percentage - DIME COLLECTOR MODE!
            if opportunity['profit_percentage'] < 0.01:  # 0.01% minimum (dimes!)
                return {
                    'valid': False,
                    'error': f"Profit percentage {opportunity['profit_percentage']:.3f}% too low"
                }

            # Check price freshness (should be recent)
            opportunity_time = datetime.fromisoformat(opportunity['timestamp'].replace('Z', '+00:00'))
            age_seconds = (datetime.now() - opportunity_time.replace(tzinfo=None)).total_seconds()

            if age_seconds > 60:  # 1 minute max age
                return {
                    'valid': False,
                    'error': f"Opportunity too old: {age_seconds:.0f} seconds"
                }

            return {'valid': True, 'error': None}

        except Exception as e:
            return {'valid': False, 'error': f"Validation error: {e}"}

    def _estimate_net_profit(self, opportunity: Dict[str, Any]) -> float:
        """Estimate net profit after all costs."""
        trade_size = self._calculate_optimal_trade_size(opportunity)

        # Gross profit
        gross_profit = trade_size * (opportunity['profit_percentage'] / 100)

        # Bridge fees
        bridge_fee = trade_size * 0.05 / 100  # 0.05% average

        # Flash loan fees
        flash_loan_fee = trade_size * 0.09 / 100  # 0.09% Aave

        # Gas costs
        gas_cost = self._estimate_gas_cost(opportunity['source_chain'], opportunity['target_chain'])

        net_profit = gross_profit - bridge_fee - flash_loan_fee - gas_cost
        return net_profit

    def _calculate_optimal_trade_size(self, opportunity: Dict[str, Any]) -> float:
        """Calculate optimal trade size for maximum profit - DIME COLLECTOR MODE!"""
        # Start with smaller base trade size for dime collecting
        base_size = 1000  # $1K - smaller trades for more frequent dimes

        # Adjust based on profit percentage
        profit_pct = opportunity['profit_percentage']

        if profit_pct > 0.5:  # High profit - use larger size
            trade_size = min(base_size * 3, self.max_trade_size_usd)
        elif profit_pct > 0.1:  # Medium profit - use larger base size
            trade_size = base_size * 2
        elif profit_pct > 0.05:  # Small profit - use base size
            trade_size = base_size
        else:  # Tiny profit (dimes!) - use smaller size but still profitable
            trade_size = base_size * 0.5

        return trade_size

    async def _select_execution_strategy(self, opportunity: Dict[str, Any], trade_size: float) -> Dict[str, Any]:
        """Select the best execution strategy."""
        source_chain = opportunity['source_chain']
        target_chain = opportunity['target_chain']

        # Find best bridge
        best_bridge = None
        best_score = 0

        for bridge_name, bridge_info in self.bridges.items():
            if not bridge_info['enabled']:
                continue

            if source_chain in bridge_info['supported_chains'] and target_chain in bridge_info['supported_chains']:
                # Score based on fee and speed
                fee_score = 1 - (bridge_info['fee_percentage'] / 0.1)  # Lower fee = higher score
                speed_score = 1 - (bridge_info['execution_time_minutes'] / 10)  # Faster = higher score

                total_score = (fee_score * 0.6) + (speed_score * 0.4)

                if total_score > best_score:
                    best_score = total_score
                    best_bridge = bridge_name

        # Find best flash loan provider
        best_flash_loan = None

        for provider_name, provider_info in self.flash_loan_providers.items():
            if not provider_info['enabled']:
                continue

            if source_chain in provider_info['supported_chains']:
                if trade_size <= provider_info['max_amount_usd']:
                    if best_flash_loan is None or provider_info['fee_percentage'] < self.flash_loan_providers[best_flash_loan]['fee_percentage']:
                        best_flash_loan = provider_name

        strategy = {
            'type': 'cross_chain_flash_loan_arbitrage',
            'bridge': best_bridge,
            'flash_loan_provider': best_flash_loan,
            'trade_size': trade_size,
            'estimated_execution_time': self.bridges[best_bridge]['execution_time_minutes'] if best_bridge else 5,
            'estimated_total_fees': self._calculate_total_fees(trade_size, best_bridge, best_flash_loan)
        }

        return strategy

    def _calculate_total_fees(self, trade_size: float, bridge: str, flash_loan_provider: str) -> float:
        """Calculate total fees for execution."""
        total_fees = 0

        # Bridge fees
        if bridge and bridge in self.bridges:
            bridge_fee = trade_size * (self.bridges[bridge]['fee_percentage'] / 100)
            total_fees += bridge_fee

        # Flash loan fees
        if flash_loan_provider and flash_loan_provider in self.flash_loan_providers:
            flash_loan_fee = trade_size * (self.flash_loan_providers[flash_loan_provider]['fee_percentage'] / 100)
            total_fees += flash_loan_fee

        return total_fees

    async def _execute_arbitrage_strategy(self, opportunity: Dict[str, Any], strategy: Dict[str, Any], trade_size: float) -> ExecutionResult:
        """Execute the arbitrage strategy (SIMULATION MODE)."""
        try:
            # SIMULATION: In production, this would execute real transactions
            logger.info(f"🎬 SIMULATING arbitrage execution...")
            logger.info(f"   Strategy: {strategy['type']}")
            logger.info(f"   Bridge: {strategy['bridge']}")
            logger.info(f"   Flash loan: {strategy['flash_loan_provider']}")
            logger.info(f"   Trade size: ${trade_size:,.0f}")

            # Simulate execution steps
            await self._simulate_flash_loan_borrow(trade_size, strategy['flash_loan_provider'])
            await self._simulate_bridge_transfer(opportunity, trade_size, strategy['bridge'])
            await self._simulate_arbitrage_trade(opportunity, trade_size)
            await self._simulate_flash_loan_repay(trade_size, strategy['flash_loan_provider'])

            # Calculate results
            gross_profit = trade_size * (opportunity['profit_percentage'] / 100)
            total_fees = strategy['estimated_total_fees']
            gas_cost = self._estimate_gas_cost(opportunity['source_chain'], opportunity['target_chain'])
            net_profit = gross_profit - total_fees - gas_cost

            # Simulate success/failure based on market conditions
            success_probability = self._calculate_success_probability(opportunity, strategy)
            import random
            success = random.random() < success_probability

            if success:
                return ExecutionResult(
                    success=True,
                    transaction_hash=f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
                    profit_usd=net_profit,
                    gas_cost_usd=gas_cost,
                    execution_time_ms=0,  # Will be set by caller
                    error_message=None,
                    timestamp=datetime.now()
                )
            else:
                return ExecutionResult(
                    success=False,
                    transaction_hash=None,
                    profit_usd=0.0,
                    gas_cost_usd=gas_cost,
                    execution_time_ms=0,
                    error_message="Simulation: Market conditions changed during execution",
                    timestamp=datetime.now()
                )

        except Exception as e:
            return ExecutionResult(
                success=False,
                transaction_hash=None,
                profit_usd=0.0,
                gas_cost_usd=0.0,
                execution_time_ms=0,
                error_message=f"Execution error: {e}",
                timestamp=datetime.now()
            )

    async def _simulate_flash_loan_borrow(self, amount: float, provider: str):
        """Simulate flash loan borrowing."""
        logger.info(f"   📋 Flash loan borrow: ${amount:,.0f} from {provider}")
        await asyncio.sleep(0.1)  # Simulate network delay

    async def _simulate_bridge_transfer(self, opportunity: Dict[str, Any], amount: float, bridge: str):
        """Simulate bridge transfer."""
        source = opportunity['source_chain']
        target = opportunity['target_chain']
        logger.info(f"   🌉 Bridge transfer: ${amount:,.0f} from {source} to {target} via {bridge}")
        await asyncio.sleep(0.2)  # Simulate bridge time

    async def _simulate_arbitrage_trade(self, opportunity: Dict[str, Any], amount: float):
        """Simulate arbitrage trade execution."""
        token = opportunity['token']
        profit = amount * (opportunity['profit_percentage'] / 100)
        logger.info(f"   💱 Arbitrage trade: {token} for ${profit:.2f} profit")
        await asyncio.sleep(0.1)  # Simulate trade execution

    async def _simulate_flash_loan_repay(self, amount: float, provider: str):
        """Simulate flash loan repayment."""
        fee = amount * (self.flash_loan_providers[provider]['fee_percentage'] / 100)
        logger.info(f"   💰 Flash loan repay: ${amount:,.0f} + ${fee:.2f} fee to {provider}")
        await asyncio.sleep(0.1)  # Simulate repayment

    def _calculate_success_probability(self, opportunity: Dict[str, Any], strategy: Dict[str, Any]) -> float:
        """Calculate probability of successful execution."""
        base_probability = 0.85  # 85% base success rate

        # Adjust based on profit margin
        profit_pct = opportunity['profit_percentage']
        if profit_pct > 0.5:
            base_probability += 0.1  # Higher profit = more likely to succeed
        elif profit_pct < 0.2:
            base_probability -= 0.2  # Lower profit = more likely to fail

        # Adjust based on execution complexity
        if opportunity['source_chain'] == opportunity['target_chain']:
            base_probability += 0.1  # Same chain = easier

        return min(0.95, max(0.5, base_probability))

    def _chains_supported(self, source_chain: str, target_chain: str) -> bool:
        """Check if chain pair is supported."""
        for bridge_info in self.bridges.values():
            if bridge_info['enabled']:
                if source_chain in bridge_info['supported_chains'] and target_chain in bridge_info['supported_chains']:
                    return True
        return False

    def _estimate_gas_cost(self, source_chain: str, target_chain: str) -> float:
        """Estimate gas cost for execution."""
        # Gas cost estimates per chain
        gas_costs = {
            'ethereum': 25.0,
            'arbitrum': 3.0,
            'optimism': 2.0,
            'base': 1.5,
            'polygon': 5.0,
            'bsc': 3.0
        }

        source_gas = gas_costs.get(source_chain, 10.0)
        target_gas = gas_costs.get(target_chain, 10.0)

        return source_gas + target_gas

    def _update_statistics(self, result: ExecutionResult):
        """Update execution statistics."""
        self.stats['total_executions'] += 1

        if result.success:
            self.stats['successful_executions'] += 1
            self.stats['total_profit_usd'] += result.profit_usd
            self.stats['best_profit_usd'] = max(self.stats['best_profit_usd'], result.profit_usd)
        else:
            self.stats['failed_executions'] += 1

        self.stats['total_gas_cost_usd'] += result.gas_cost_usd

        # Update average execution time
        if self.stats['total_executions'] > 0:
            total_time = (self.stats['average_execution_time_ms'] * (self.stats['total_executions'] - 1) +
                         result.execution_time_ms)
            self.stats['average_execution_time_ms'] = total_time / self.stats['total_executions']

        # Store in history (keep last 100)
        self.stats['execution_history'].append({
            'timestamp': result.timestamp.isoformat(),
            'success': result.success,
            'profit_usd': result.profit_usd,
            'gas_cost_usd': result.gas_cost_usd,
            'execution_time_ms': result.execution_time_ms
        })

        if len(self.stats['execution_history']) > 100:
            self.stats['execution_history'] = self.stats['execution_history'][-100:]

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        success_rate = (self.stats['successful_executions'] / max(self.stats['total_executions'], 1)) * 100
        net_profit = self.stats['total_profit_usd'] - self.stats['total_gas_cost_usd']

        return {
            'total_executions': self.stats['total_executions'],
            'successful_executions': self.stats['successful_executions'],
            'failed_executions': self.stats['failed_executions'],
            'success_rate_percentage': success_rate,
            'total_profit_usd': self.stats['total_profit_usd'],
            'total_gas_cost_usd': self.stats['total_gas_cost_usd'],
            'net_profit_usd': net_profit,
            'best_profit_usd': self.stats['best_profit_usd'],
            'average_execution_time_ms': self.stats['average_execution_time_ms'],
            'recent_executions': len(self.stats['execution_history'])
        }
