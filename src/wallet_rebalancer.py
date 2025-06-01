"""
MayArbi Wallet Rebalancing System

Automatically rebalances wallet compositions across networks to optimize
for arbitrage opportunities and maintain optimal trading ratios.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from decimal import Decimal
import json

from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)


@dataclass
class WalletBalance:
    """Wallet balance information."""
    network: str
    address: str
    eth_balance: Decimal
    usdc_balance: Decimal
    total_usd_value: Decimal
    gas_reserve: Decimal
    available_for_trading: Decimal
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class RebalanceTarget:
    """Target allocation for wallet rebalancing."""
    network: str
    target_percentage: float
    min_eth_balance: Decimal
    min_usdc_balance: Decimal
    optimal_eth_usdc_ratio: float  # 0.5 = 50% ETH, 50% USDC


@dataclass
class RebalanceAction:
    """Rebalancing action to be executed."""
    action_type: str  # 'transfer', 'swap', 'bridge'
    from_network: str
    to_network: str
    token: str
    amount: Decimal
    estimated_cost: Decimal
    priority: int  # 1=highest, 10=lowest
    reason: str


class WalletRebalancer:
    """
    Intelligent wallet rebalancing system for optimal arbitrage performance.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize wallet rebalancer."""
        self.config = config
        
        # Network configurations
        self.networks = self._load_network_configs()
        
        # Rebalancing targets based on arbitrage performance
        self.rebalance_targets = {
            'arbitrum': RebalanceTarget(
                network='arbitrum',
                target_percentage=0.50,  # 50% of total capital
                min_eth_balance=Decimal('0.01'),
                min_usdc_balance=Decimal('25'),
                optimal_eth_usdc_ratio=0.6  # 60% ETH, 40% USDC
            ),
            'base': RebalanceTarget(
                network='base',
                target_percentage=0.30,  # 30% of total capital
                min_eth_balance=Decimal('0.008'),
                min_usdc_balance=Decimal('15'),
                optimal_eth_usdc_ratio=0.55  # 55% ETH, 45% USDC
            ),
            'optimism': RebalanceTarget(
                network='optimism',
                target_percentage=0.20,  # 20% of total capital
                min_eth_balance=Decimal('0.005'),
                min_usdc_balance=Decimal('10'),
                optimal_eth_usdc_ratio=0.5  # 50% ETH, 50% USDC
            )
        }
        
        # Rebalancing thresholds
        self.rebalance_threshold = 0.15  # Trigger rebalance if >15% off target
        self.min_rebalance_amount = Decimal('10')  # Minimum $10 to rebalance
        self.max_rebalance_frequency = timedelta(hours=6)  # Max once per 6 hours
        
        # Price feeds (in production, use real price oracles)
        self.eth_price_usd = Decimal('2500')  # Will be fetched from price feeds
        
        # Last rebalance tracking
        self.last_rebalance = {}

    def _load_network_configs(self) -> Dict[str, Any]:
        """Load network configurations."""
        return {
            'arbitrum': {
                'rpc_url': 'https://arb1.arbitrum.io/rpc',
                'chain_id': 42161,
                'usdc_address': '0xA0b86a33E6441b8e8C7F94D0b8A3C5C0C8C8C8C8',
                'bridge_contracts': ['0x...']  # Bridge contract addresses
            },
            'base': {
                'rpc_url': 'https://mainnet.base.org',
                'chain_id': 8453,
                'usdc_address': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
                'bridge_contracts': ['0x...']
            },
            'optimism': {
                'rpc_url': 'https://mainnet.optimism.io',
                'chain_id': 10,
                'usdc_address': '0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85',
                'bridge_contracts': ['0x...']
            }
        }

    async def analyze_wallet_balances(self) -> Dict[str, WalletBalance]:
        """Analyze current wallet balances across all networks."""
        logger.info("Analyzing wallet balances across networks...")
        
        balances = {}
        
        for network_name, target in self.rebalance_targets.items():
            try:
                balance = await self._get_wallet_balance(network_name)
                balances[network_name] = balance
                
                logger.info(f"{network_name.title()}: "
                          f"ETH={balance.eth_balance:.4f}, "
                          f"USDC=${balance.usdc_balance:.2f}, "
                          f"Total=${balance.total_usd_value:.2f}")
                
            except Exception as e:
                logger.error(f"Error getting balance for {network_name}: {e}")
        
        return balances

    async def _get_wallet_balance(self, network: str) -> WalletBalance:
        """Get wallet balance for a specific network."""
        # In production, this would connect to actual blockchain
        # For now, simulate realistic balances
        
        import random
        
        # Simulate wallet balances based on network priority
        if network == 'arbitrum':
            eth_balance = Decimal(str(random.uniform(0.08, 0.15)))
            usdc_balance = Decimal(str(random.uniform(180, 220)))
        elif network == 'base':
            eth_balance = Decimal(str(random.uniform(0.05, 0.10)))
            usdc_balance = Decimal(str(random.uniform(120, 160)))
        else:  # optimism
            eth_balance = Decimal(str(random.uniform(0.03, 0.08)))
            usdc_balance = Decimal(str(random.uniform(80, 120)))
        
        total_usd_value = (eth_balance * self.eth_price_usd) + usdc_balance
        gas_reserve = Decimal('0.002')  # Reserve for gas
        available_for_trading = total_usd_value - (gas_reserve * self.eth_price_usd)
        
        return WalletBalance(
            network=network,
            address=f"0x{'1234567890abcdef' * 5}",  # Mock address
            eth_balance=eth_balance,
            usdc_balance=usdc_balance,
            total_usd_value=total_usd_value,
            gas_reserve=gas_reserve,
            available_for_trading=available_for_trading
        )

    async def calculate_rebalance_needs(self, balances: Dict[str, WalletBalance]) -> List[RebalanceAction]:
        """Calculate what rebalancing actions are needed."""
        logger.info("Calculating rebalancing needs...")
        
        # Calculate total portfolio value
        total_portfolio_value = sum(balance.total_usd_value for balance in balances.values())
        
        logger.info(f"Total portfolio value: ${total_portfolio_value:.2f}")
        
        rebalance_actions = []
        
        # Check network allocation
        for network, balance in balances.items():
            target = self.rebalance_targets[network]
            
            # Current allocation percentage
            current_percentage = float(balance.total_usd_value / total_portfolio_value)
            target_percentage = target.target_percentage
            
            # Calculate deviation
            deviation = abs(current_percentage - target_percentage)
            
            logger.info(f"{network.title()}: "
                       f"Current={current_percentage:.1%}, "
                       f"Target={target_percentage:.1%}, "
                       f"Deviation={deviation:.1%}")
            
            # Check if rebalancing is needed
            if deviation > self.rebalance_threshold:
                target_value = total_portfolio_value * Decimal(str(target_percentage))
                current_value = balance.total_usd_value
                difference = target_value - current_value
                
                if abs(difference) > self.min_rebalance_amount:
                    if difference > 0:
                        # Need to add funds to this network
                        action = self._create_funding_action(network, difference, balances)
                        if action:
                            rebalance_actions.append(action)
                    else:
                        # Need to remove funds from this network
                        action = self._create_withdrawal_action(network, abs(difference), balances)
                        if action:
                            rebalance_actions.append(action)
            
            # Check ETH/USDC ratio within network
            ratio_actions = self._check_token_ratio(network, balance, target)
            rebalance_actions.extend(ratio_actions)
        
        # Sort actions by priority
        rebalance_actions.sort(key=lambda x: x.priority)
        
        return rebalance_actions

    def _create_funding_action(self, target_network: str, amount: Decimal, 
                             balances: Dict[str, WalletBalance]) -> Optional[RebalanceAction]:
        """Create action to fund a network that needs more capital."""
        # Find the network with the most excess funds
        source_network = None
        max_excess = Decimal('0')
        
        for network, balance in balances.items():
            if network == target_network:
                continue
            
            target = self.rebalance_targets[network]
            target_value = balance.total_usd_value * Decimal(str(target.target_percentage))
            excess = balance.total_usd_value - target_value
            
            if excess > max_excess and excess > self.min_rebalance_amount:
                max_excess = excess
                source_network = network
        
        if source_network:
            transfer_amount = min(amount, max_excess * Decimal('0.8'))  # Transfer 80% of excess
            
            return RebalanceAction(
                action_type='bridge',
                from_network=source_network,
                to_network=target_network,
                token='USDC',
                amount=transfer_amount,
                estimated_cost=Decimal('2.50'),  # Estimated bridge cost
                priority=2,
                reason=f"Rebalance {target_network} allocation (+${transfer_amount:.2f})"
            )
        
        return None

    def _create_withdrawal_action(self, source_network: str, amount: Decimal,
                                balances: Dict[str, WalletBalance]) -> Optional[RebalanceAction]:
        """Create action to withdraw excess funds from a network."""
        # Find the network that needs the most funding
        target_network = None
        max_deficit = Decimal('0')
        
        for network, balance in balances.items():
            if network == source_network:
                continue
            
            target = self.rebalance_targets[network]
            target_value = balance.total_usd_value * Decimal(str(target.target_percentage))
            deficit = target_value - balance.total_usd_value
            
            if deficit > max_deficit:
                max_deficit = deficit
                target_network = network
        
        if target_network and max_deficit > self.min_rebalance_amount:
            transfer_amount = min(amount * Decimal('0.8'), max_deficit)
            
            return RebalanceAction(
                action_type='bridge',
                from_network=source_network,
                to_network=target_network,
                token='USDC',
                amount=transfer_amount,
                estimated_cost=Decimal('2.50'),
                priority=3,
                reason=f"Rebalance {source_network} allocation (-${transfer_amount:.2f})"
            )
        
        return None

    def _check_token_ratio(self, network: str, balance: WalletBalance, 
                          target: RebalanceTarget) -> List[RebalanceAction]:
        """Check if ETH/USDC ratio needs rebalancing within a network."""
        actions = []
        
        # Calculate current ratio
        eth_value = balance.eth_balance * self.eth_price_usd
        total_value = eth_value + balance.usdc_balance
        
        if total_value == 0:
            return actions
        
        current_eth_ratio = float(eth_value / total_value)
        target_eth_ratio = target.optimal_eth_usdc_ratio
        
        ratio_deviation = abs(current_eth_ratio - target_eth_ratio)
        
        if ratio_deviation > 0.1:  # 10% deviation threshold
            if current_eth_ratio > target_eth_ratio:
                # Too much ETH, swap some to USDC
                excess_eth_value = (current_eth_ratio - target_eth_ratio) * total_value
                swap_amount = excess_eth_value * Decimal('0.5')  # Swap 50% of excess
                
                if swap_amount > Decimal('5'):  # Minimum $5 swap
                    actions.append(RebalanceAction(
                        action_type='swap',
                        from_network=network,
                        to_network=network,
                        token='ETH->USDC',
                        amount=swap_amount,
                        estimated_cost=Decimal('0.50'),
                        priority=4,
                        reason=f"Rebalance {network} ETH/USDC ratio (swap ${swap_amount:.2f} ETH->USDC)"
                    ))
            else:
                # Too much USDC, swap some to ETH
                excess_usdc_value = (target_eth_ratio - current_eth_ratio) * total_value
                swap_amount = excess_usdc_value * Decimal('0.5')
                
                if swap_amount > Decimal('5'):
                    actions.append(RebalanceAction(
                        action_type='swap',
                        from_network=network,
                        to_network=network,
                        token='USDC->ETH',
                        amount=swap_amount,
                        estimated_cost=Decimal('0.50'),
                        priority=4,
                        reason=f"Rebalance {network} ETH/USDC ratio (swap ${swap_amount:.2f} USDC->ETH)"
                    ))
        
        return actions

    async def execute_rebalance_plan(self, actions: List[RebalanceAction], 
                                   dry_run: bool = True) -> Dict[str, Any]:
        """Execute the rebalancing plan."""
        logger.info(f"Executing rebalance plan ({len(actions)} actions, dry_run={dry_run})")
        
        results = {
            'total_actions': len(actions),
            'executed_actions': 0,
            'failed_actions': 0,
            'total_cost': Decimal('0'),
            'actions_details': []
        }
        
        for action in actions:
            try:
                if dry_run:
                    logger.info(f"DRY RUN: {action.reason}")
                    logger.info(f"  Action: {action.action_type} {action.amount} {action.token}")
                    logger.info(f"  Route: {action.from_network} -> {action.to_network}")
                    logger.info(f"  Cost: ${action.estimated_cost}")
                    
                    results['executed_actions'] += 1
                    results['total_cost'] += action.estimated_cost
                else:
                    # Execute actual rebalancing
                    success = await self._execute_action(action)
                    if success:
                        results['executed_actions'] += 1
                        results['total_cost'] += action.estimated_cost
                    else:
                        results['failed_actions'] += 1
                
                results['actions_details'].append({
                    'action': action.reason,
                    'type': action.action_type,
                    'amount': float(action.amount),
                    'cost': float(action.estimated_cost),
                    'status': 'executed' if dry_run or success else 'failed'
                })
                
            except Exception as e:
                logger.error(f"Error executing action {action.reason}: {e}")
                results['failed_actions'] += 1
        
        return results

    async def _execute_action(self, action: RebalanceAction) -> bool:
        """Execute a specific rebalancing action."""
        # In production, this would execute actual blockchain transactions
        logger.info(f"Executing: {action.reason}")
        
        if action.action_type == 'bridge':
            return await self._execute_bridge(action)
        elif action.action_type == 'swap':
            return await self._execute_swap(action)
        else:
            logger.error(f"Unknown action type: {action.action_type}")
            return False

    async def _execute_bridge(self, action: RebalanceAction) -> bool:
        """Execute cross-chain bridge transaction."""
        # Simulate bridge execution
        await asyncio.sleep(0.5)  # Simulate transaction time
        logger.info(f"Bridged {action.amount} {action.token} from {action.from_network} to {action.to_network}")
        return True

    async def _execute_swap(self, action: RebalanceAction) -> bool:
        """Execute token swap transaction."""
        # Simulate swap execution
        await asyncio.sleep(0.3)  # Simulate transaction time
        logger.info(f"Swapped {action.amount} {action.token} on {action.from_network}")
        return True

    async def run_rebalance_analysis(self, execute: bool = False) -> Dict[str, Any]:
        """Run complete rebalancing analysis and optionally execute."""
        logger.info("Starting wallet rebalancing analysis...")
        
        try:
            # Step 1: Analyze current balances
            balances = await self.analyze_wallet_balances()
            
            # Step 2: Calculate rebalancing needs
            actions = await self.calculate_rebalance_needs(balances)
            
            # Step 3: Execute or simulate
            results = await self.execute_rebalance_plan(actions, dry_run=not execute)
            
            # Step 4: Generate report
            report = {
                'timestamp': datetime.now().isoformat(),
                'balances': {
                    network: {
                        'eth_balance': float(balance.eth_balance),
                        'usdc_balance': float(balance.usdc_balance),
                        'total_usd_value': float(balance.total_usd_value)
                    }
                    for network, balance in balances.items()
                },
                'rebalance_results': results,
                'recommendations': self._generate_recommendations(balances, actions)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error in rebalancing analysis: {e}")
            return {'error': str(e)}

    def _generate_recommendations(self, balances: Dict[str, WalletBalance], 
                                actions: List[RebalanceAction]) -> List[str]:
        """Generate rebalancing recommendations."""
        recommendations = []
        
        total_value = sum(balance.total_usd_value for balance in balances.values())
        
        if not actions:
            recommendations.append("✅ Wallets are well-balanced, no rebalancing needed")
        else:
            recommendations.append(f"🔄 {len(actions)} rebalancing actions recommended")
            
            # Check for low balances
            for network, balance in balances.items():
                target = self.rebalance_targets[network]
                if balance.eth_balance < target.min_eth_balance:
                    recommendations.append(f"⚠️ {network.title()}: Low ETH balance for gas")
                if balance.usdc_balance < target.min_usdc_balance:
                    recommendations.append(f"⚠️ {network.title()}: Low USDC balance for trading")
        
        # Portfolio health
        if total_value < 100:
            recommendations.append("💰 Consider increasing total portfolio size for better opportunities")
        elif total_value > 1000:
            recommendations.append("🚀 Portfolio size is excellent for arbitrage opportunities")
        
        return recommendations
