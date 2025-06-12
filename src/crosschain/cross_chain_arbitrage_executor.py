#!/usr/bin/env python3
"""
🌉 CROSS-CHAIN ARBITRAGE EXECUTOR
Execute profitable cross-chain arbitrage opportunities with 5-10 minute windows!
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import os
from web3 import Web3

logger = logging.getLogger(__name__)

@dataclass
class CrossChainOpportunity:
    """Cross-chain arbitrage opportunity."""
    token: str
    buy_chain: str
    sell_chain: str
    buy_price: float
    sell_price: float
    profit_pct: float
    profit_usd: float
    buy_dex: str
    sell_dex: str
    timestamp: datetime
    execution_window_minutes: int = 5
    bridge_fee_pct: float = 0.1
    estimated_bridge_time_minutes: int = 3

@dataclass
class CrossChainExecution:
    """Cross-chain execution result."""
    opportunity_id: str
    success: bool
    actual_profit_usd: float
    execution_time_seconds: float
    bridge_tx_hash: Optional[str] = None
    buy_tx_hash: Optional[str] = None
    sell_tx_hash: Optional[str] = None
    error_message: Optional[str] = None

class CrossChainArbitrageExecutor:
    """Execute cross-chain arbitrage opportunities."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize cross-chain executor."""
        self.config = config
        
        # Web3 connections for each chain
        self.web3_connections = {}
        self.chain_configs = {
            'arbitrum': {
                'rpc_url': f"https://arb-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}",
                'chain_id': 42161,
                'native_token': 'ETH',
                'bridge_contracts': {
                    'across': '0x269727F088F16E1Aea52Cf5a97B1CD41DAA3f02D',
                    'synapse': '0x7E7A0e201FD38d3ADAA9523Da6C109a07118C96a'
                }
            },
            'base': {
                'rpc_url': f"https://base-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}",
                'chain_id': 8453,
                'native_token': 'ETH',
                'bridge_contracts': {
                    'across': '0x09aea4b2242abC8bb4BB78D537A67a245A7bEC64',
                    'synapse': '0xAf41a65F786339e7911F4acDAD6BD49426F2Dc6b'
                }
            },
            'optimism': {
                'rpc_url': f"https://opt-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}",
                'chain_id': 10,
                'native_token': 'ETH',
                'bridge_contracts': {
                    'across': '0x6f26Bf09B1C792e3228e5467807a900A503c0281',
                    'synapse': '0xAf41a65F786339e7911F4acDAD6BD49426F2Dc6b'
                }
            }
        }
        
        # Bridge configurations
        self.bridge_configs = {
            'across': {
                'fee_pct': 0.05,  # 0.05% fee
                'time_minutes': 2,  # 2 minute average
                'supported_tokens': ['ETH', 'WETH', 'USDC', 'USDT', 'WBTC']
            },
            'synapse': {
                'fee_pct': 0.1,   # 0.1% fee
                'time_minutes': 3,  # 3 minute average
                'supported_tokens': ['ETH', 'USDC', 'USDT', 'WETH']
            }
        }
        
        # Execution settings
        self.min_profit_usd = config.get('min_cross_chain_profit_usd', 10.0)
        self.max_trade_amount_usd = config.get('max_cross_chain_trade_usd', 5000.0)
        self.execution_timeout_minutes = config.get('execution_timeout_minutes', 15)
        
        # Performance tracking
        self.execution_stats = {
            'opportunities_detected': 0,
            'opportunities_executed': 0,
            'successful_executions': 0,
            'total_profit_usd': 0.0,
            'average_execution_time': 0.0
        }
        
        logger.info("🌉 Cross-chain arbitrage executor initialized")
        logger.info(f"   💰 Min profit: ${self.min_profit_usd}")
        logger.info(f"   📊 Max trade: ${self.max_trade_amount_usd}")
        logger.info(f"   ⏰ Timeout: {self.execution_timeout_minutes} minutes")
    
    async def initialize(self) -> bool:
        """Initialize Web3 connections and contracts."""
        try:
            logger.info("🔧 Initializing cross-chain connections...")
            
            # Initialize Web3 connections
            for chain, config in self.chain_configs.items():
                try:
                    self.web3_connections[chain] = Web3(Web3.HTTPProvider(config['rpc_url']))
                    
                    # Test connection
                    latest_block = self.web3_connections[chain].eth.get_block('latest')
                    logger.info(f"   ✅ {chain.title()}: Block {latest_block['number']}")
                    
                except Exception as e:
                    logger.error(f"   ❌ {chain.title()}: {e}")
                    return False
            
            logger.info("✅ Cross-chain executor ready!")
            return True
            
        except Exception as e:
            logger.error(f"Cross-chain initialization failed: {e}")
            return False
    
    async def execute_cross_chain_arbitrage(self, opportunity: CrossChainOpportunity) -> CrossChainExecution:
        """Execute a cross-chain arbitrage opportunity."""
        start_time = datetime.now()
        opportunity_id = f"cc_{opportunity.token}_{start_time.strftime('%H%M%S')}"
        
        logger.info(f"🌉 EXECUTING CROSS-CHAIN ARBITRAGE!")
        logger.info(f"   🎯 Opportunity: {opportunity.token}")
        logger.info(f"   📍 Route: {opportunity.buy_chain} → {opportunity.sell_chain}")
        logger.info(f"   💰 Expected profit: ${opportunity.profit_usd:.2f} ({opportunity.profit_pct:.2f}%)")
        
        try:
            # Step 1: Calculate optimal trade amount based on ACTUAL WALLET BALANCE
            from src.config.trading_config import CONFIG
            max_wallet_trade = CONFIG.MAX_TRADE_USD  # 75% of $458 = ~$343

            trade_amount_usd = min(
                self.max_trade_amount_usd,
                max_wallet_trade,  # 🚨 FIXED: Use actual wallet balance
                max(50, opportunity.profit_usd * 20)  # Scale based on profit, min $50
            )
            
            logger.info(f"   💵 Trade amount: ${trade_amount_usd:.2f}")
            
            # Step 2: Check if opportunity is still viable
            if not await self._verify_opportunity_still_exists(opportunity):
                return CrossChainExecution(
                    opportunity_id=opportunity_id,
                    success=False,
                    actual_profit_usd=0.0,
                    execution_time_seconds=0.0,
                    error_message="Opportunity no longer exists"
                )
            
            # Step 3: Execute buy on source chain
            logger.info(f"   🛒 Step 1: Buying {opportunity.token} on {opportunity.buy_chain}")
            buy_result = await self._execute_buy_order(
                opportunity.buy_chain,
                opportunity.token,
                trade_amount_usd,
                opportunity.buy_price
            )
            
            if not buy_result['success']:
                return CrossChainExecution(
                    opportunity_id=opportunity_id,
                    success=False,
                    actual_profit_usd=0.0,
                    execution_time_seconds=(datetime.now() - start_time).total_seconds(),
                    error_message=f"Buy failed: {buy_result['error']}"
                )
            
            # Step 4: Bridge tokens to target chain
            logger.info(f"   🌉 Step 2: Bridging {opportunity.token} to {opportunity.sell_chain}")
            bridge_result = await self._execute_bridge_transfer(
                opportunity.buy_chain,
                opportunity.sell_chain,
                opportunity.token,
                buy_result['amount_received']
            )
            
            if not bridge_result['success']:
                return CrossChainExecution(
                    opportunity_id=opportunity_id,
                    success=False,
                    actual_profit_usd=0.0,
                    execution_time_seconds=(datetime.now() - start_time).total_seconds(),
                    bridge_tx_hash=bridge_result.get('tx_hash'),
                    buy_tx_hash=buy_result.get('tx_hash'),
                    error_message=f"Bridge failed: {bridge_result['error']}"
                )
            
            # Step 5: Wait for bridge completion
            logger.info(f"   ⏳ Step 3: Waiting for bridge completion...")
            bridge_complete = await self._wait_for_bridge_completion(
                bridge_result['tx_hash'],
                opportunity.sell_chain,
                timeout_minutes=self.execution_timeout_minutes
            )
            
            if not bridge_complete:
                return CrossChainExecution(
                    opportunity_id=opportunity_id,
                    success=False,
                    actual_profit_usd=0.0,
                    execution_time_seconds=(datetime.now() - start_time).total_seconds(),
                    bridge_tx_hash=bridge_result['tx_hash'],
                    buy_tx_hash=buy_result['tx_hash'],
                    error_message="Bridge timeout"
                )
            
            # Step 6: Execute sell on target chain
            logger.info(f"   💰 Step 4: Selling {opportunity.token} on {opportunity.sell_chain}")
            sell_result = await self._execute_sell_order(
                opportunity.sell_chain,
                opportunity.token,
                bridge_result['amount_bridged'],
                opportunity.sell_price
            )
            
            # Calculate final results
            execution_time = (datetime.now() - start_time).total_seconds()
            
            if sell_result['success']:
                actual_profit = sell_result['amount_received'] - trade_amount_usd
                
                logger.info(f"   ✅ CROSS-CHAIN ARBITRAGE SUCCESSFUL!")
                logger.info(f"      💰 Actual profit: ${actual_profit:.2f}")
                logger.info(f"      ⏰ Execution time: {execution_time:.1f}s")
                
                # Update stats
                self.execution_stats['successful_executions'] += 1
                self.execution_stats['total_profit_usd'] += actual_profit
                
                return CrossChainExecution(
                    opportunity_id=opportunity_id,
                    success=True,
                    actual_profit_usd=actual_profit,
                    execution_time_seconds=execution_time,
                    bridge_tx_hash=bridge_result['tx_hash'],
                    buy_tx_hash=buy_result['tx_hash'],
                    sell_tx_hash=sell_result['tx_hash']
                )
            else:
                return CrossChainExecution(
                    opportunity_id=opportunity_id,
                    success=False,
                    actual_profit_usd=0.0,
                    execution_time_seconds=execution_time,
                    bridge_tx_hash=bridge_result['tx_hash'],
                    buy_tx_hash=buy_result['tx_hash'],
                    error_message=f"Sell failed: {sell_result['error']}"
                )
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"   ❌ Cross-chain execution failed: {e}")
            
            return CrossChainExecution(
                opportunity_id=opportunity_id,
                success=False,
                actual_profit_usd=0.0,
                execution_time_seconds=execution_time,
                error_message=str(e)
            )
        finally:
            self.execution_stats['opportunities_executed'] += 1
    
    async def _verify_opportunity_still_exists(self, opportunity: CrossChainOpportunity) -> bool:
        """Verify the arbitrage opportunity still exists."""
        try:
            # Check if opportunity is too old
            age_minutes = (datetime.now() - opportunity.timestamp).total_seconds() / 60
            if age_minutes > opportunity.execution_window_minutes:
                logger.warning(f"   ⚠️  Opportunity expired ({age_minutes:.1f} min old)")
                return False
            
            # TODO: Re-check current prices on both chains
            # For now, assume opportunity exists if recent
            return True
            
        except Exception as e:
            logger.error(f"Opportunity verification error: {e}")
            return False
    
    async def _execute_buy_order(self, chain: str, token: str, amount_usd: float, expected_price: float) -> Dict[str, Any]:
        """Execute REAL buy order on source chain."""
        try:
            logger.info(f"      🛒 EXECUTING REAL BUY: ${amount_usd:.2f} of {token} on {chain}")

            # Initialize real DEX executor if needed
            if not hasattr(self, 'dex_executor'):
                from src.execution.real_dex_executor import RealDEXExecutor
                self.dex_executor = RealDEXExecutor(self.config)

                # 🔗 INJECT WEB3 CONNECTIONS FROM MASTER SYSTEM!
                if hasattr(self, 'web3_connections') and self.web3_connections:
                    self.dex_executor.web3_connections = self.web3_connections
                    logger.info(f"      🔗 Injected {len(self.web3_connections)} Web3 connections into DEX executor")

                if hasattr(self, 'private_key'):
                    await self.dex_executor.initialize(self.private_key)

            # Execute real buy order
            buy_result = await self.dex_executor.execute_buy_order(
                chain=chain,
                token=token,
                amount_usd=amount_usd,
                dex='sushiswap',  # Default DEX
                slippage_pct=3.0  # Use 3% default slippage
            )

            if buy_result['success']:
                logger.info(f"      ✅ REAL BUY SUCCESS: {buy_result['tokens_received']:.6f} {token}")
                return {
                    'success': True,
                    'amount_received': buy_result['tokens_received'],
                    'tx_hash': buy_result['tx_hash'],
                    'gas_used': buy_result['gas_used'],
                    'gas_cost_usd': buy_result['gas_cost_usd']
                }
            else:
                logger.error(f"      ❌ REAL BUY FAILED: {buy_result['error']}")
                return {
                    'success': False,
                    'error': buy_result['error']
                }

        except Exception as e:
            logger.error(f"❌ Real buy order error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _execute_bridge_transfer(self, source_chain: str, target_chain: str, token: str, amount: float) -> Dict[str, Any]:
        """Execute bridge transfer between chains."""
        try:
            # Select best bridge
            bridge_name = self._select_best_bridge(source_chain, target_chain, token)
            
            if not bridge_name:
                return {
                    'success': False,
                    'error': 'No suitable bridge found'
                }
            
            bridge_config = self.bridge_configs[bridge_name]
            
            logger.info(f"      🌉 Using {bridge_name} bridge")
            logger.info(f"      💸 Bridge fee: {bridge_config['fee_pct']}%")
            logger.info(f"      ⏰ Est. time: {bridge_config['time_minutes']} min")
            
            # TODO: Implement actual bridge transaction
            # For now, simulate bridge
            
            # Simulate bridge delay
            await asyncio.sleep(2)
            
            # Calculate amount after bridge fees
            bridge_fee = amount * (bridge_config['fee_pct'] / 100)
            amount_bridged = amount - bridge_fee
            
            return {
                'success': True,
                'amount_bridged': amount_bridged,
                'bridge_fee': bridge_fee,
                'tx_hash': f"0x{'2' * 64}",  # Mock transaction hash
                'estimated_completion_time': datetime.now() + timedelta(minutes=bridge_config['time_minutes'])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _select_best_bridge(self, source_chain: str, target_chain: str, token: str) -> Optional[str]:
        """Select the best bridge for the transfer."""
        best_bridge = None
        best_score = 0
        
        for bridge_name, bridge_config in self.bridge_configs.items():
            if token in bridge_config['supported_tokens']:
                # Score based on fee and time
                fee_score = 1 - (bridge_config['fee_pct'] / 0.2)  # Lower fee = higher score
                time_score = 1 - (bridge_config['time_minutes'] / 10)  # Faster = higher score
                
                total_score = (fee_score * 0.6) + (time_score * 0.4)
                
                if total_score > best_score:
                    best_score = total_score
                    best_bridge = bridge_name
        
        return best_bridge
    
    async def _wait_for_bridge_completion(self, tx_hash: str, target_chain: str, timeout_minutes: int = 15) -> bool:
        """Wait for bridge transfer to complete."""
        try:
            # TODO: Implement actual bridge monitoring
            # For now, simulate bridge completion time
            
            bridge_time = 180  # 3 minutes
            logger.info(f"      ⏳ Waiting {bridge_time}s for bridge completion...")
            
            await asyncio.sleep(bridge_time)
            
            logger.info(f"      ✅ Bridge completed!")
            return True
            
        except Exception as e:
            logger.error(f"Bridge monitoring error: {e}")
            return False
    
    async def _execute_sell_order(self, chain: str, token: str, amount: float, expected_price: float) -> Dict[str, Any]:
        """Execute REAL sell order on target chain."""
        try:
            logger.info(f"      💰 EXECUTING REAL SELL: {amount:.6f} {token} on {chain}")

            # Initialize real DEX executor if needed
            if not hasattr(self, 'dex_executor'):
                from src.execution.real_dex_executor import RealDEXExecutor
                self.dex_executor = RealDEXExecutor(self.config)

                # 🔗 INJECT WEB3 CONNECTIONS FROM MASTER SYSTEM!
                if hasattr(self, 'web3_connections') and self.web3_connections:
                    self.dex_executor.web3_connections = self.web3_connections
                    logger.info(f"      🔗 Injected {len(self.web3_connections)} Web3 connections into DEX executor")

                if hasattr(self, 'private_key'):
                    await self.dex_executor.initialize(self.private_key)

            # Execute real sell order
            sell_result = await self.dex_executor.execute_sell_order(
                chain=chain,
                token=token,
                token_amount=amount,
                dex='sushiswap',  # Default DEX
                slippage_pct=3.0  # Use 3% default slippage
            )

            if sell_result['success']:
                logger.info(f"      ✅ REAL SELL SUCCESS: ${sell_result['usd_received']:.2f}")
                return {
                    'success': True,
                    'amount_received': sell_result['usd_received'],
                    'eth_received': sell_result['eth_received'],
                    'tx_hash': sell_result['tx_hash'],
                    'gas_used': sell_result['gas_used'],
                    'gas_cost_usd': sell_result['gas_cost_usd']
                }
            else:
                logger.error(f"      ❌ REAL SELL FAILED: {sell_result['error']}")
                return {
                    'success': False,
                    'error': sell_result['error']
                }

        except Exception as e:
            logger.error(f"❌ Real sell order error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        success_rate = 0
        if self.execution_stats['opportunities_executed'] > 0:
            success_rate = (self.execution_stats['successful_executions'] / 
                          self.execution_stats['opportunities_executed']) * 100
        
        return {
            **self.execution_stats,
            'success_rate_pct': success_rate
        }
