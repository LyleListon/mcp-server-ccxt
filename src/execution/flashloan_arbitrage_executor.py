#!/usr/bin/env python3
"""
⚡ FLASHLOAN ARBITRAGE EXECUTOR ⚡
Executes arbitrage trades using flashloans - UNLIMITED CAPITAL!
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from web3 import Web3
from eth_account import Account
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class FlashloanArbitrageExecutor:
    """Execute arbitrage trades using flashloans for unlimited capital."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize flashloan arbitrage executor."""
        self.config = config
        self.web3_connections = {}
        self.flashloan_providers = {}
        self.wallet_account = None
        
        # Flashloan settings
        self.flashloan_provider = config.get('flashloan_provider', 'aave')
        self.min_flashloan_amount = config.get('min_flashloan_amount', 10000)
        self.max_flashloan_amount = config.get('max_flashloan_amount', 100000)
        self.flashloan_safety_margin = config.get('flashloan_safety_margin', 1.01)  # Just 1% safety margin!
        
        logger.info(f"⚡ FlashloanArbitrageExecutor initialized")
        logger.info(f"   🏦 Provider: {self.flashloan_provider}")
        logger.info(f"   💰 Range: ${self.min_flashloan_amount:,} - ${self.max_flashloan_amount:,}")
        logger.info(f"   🛡️  Safety margin: {self.flashloan_safety_margin}x")

    async def initialize(self, wallet_private_key: str = None) -> bool:
        """Initialize flashloan executor components."""
        try:
            logger.info("⚡ Initializing flashloan executor...")
            
            # Initialize Web3 connections
            await self._initialize_web3_connections()
            
            # Initialize wallet account
            await self._initialize_wallet(wallet_private_key)
            
            # Initialize flashloan providers
            await self._initialize_flashloan_providers()
            
            logger.info("✅ Flashloan executor initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Flashloan executor initialization failed: {e}")
            return False

    async def _initialize_web3_connections(self):
        """Initialize Web3 connections for all networks."""
        networks = self.config.get('networks', ['arbitrum'])
        alchemy_api_key = self.config.get('alchemy_api_key')
        
        for network in networks:
            if network == 'arbitrum':
                rpc_url = f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
            elif network == 'base':
                rpc_url = f"https://base-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
            elif network == 'optimism':
                rpc_url = f"https://opt-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
            else:
                continue
                
            self.web3_connections[network] = Web3(Web3.HTTPProvider(rpc_url))
            logger.info(f"   🌐 Connected to {network}")

    async def _initialize_wallet(self, wallet_private_key: str = None):
        """Initialize wallet account for signing transactions."""
        import os
        private_key = wallet_private_key or os.getenv('PRIVATE_KEY') or os.getenv('WALLET_PRIVATE_KEY')
        if private_key:
            self.wallet_account = Account.from_key(private_key)
            logger.info(f"   🔑 Wallet loaded: {self.wallet_account.address}")
        else:
            logger.warning("   ⚠️  No private key found - simulation mode only")

    async def _initialize_flashloan_providers(self):
        """Initialize flashloan provider connections."""
        try:
            # Initialize Aave flashloan provider
            from flashloan.aave_flashloan import AaveFlashLoan
            self.flashloan_providers['aave'] = AaveFlashLoan(self.config)
            logger.info("   🏦 Aave flashloan provider initialized (0.09% fee)")

            # Initialize Balancer flashloan provider (0% fees!)
            from flashloan.balancer_flashloan import BalancerFlashLoan
            self.flashloan_providers['balancer'] = BalancerFlashLoan(self.config)
            logger.info("   🏊 Balancer flashloan provider initialized (0% fees!)")

            # TODO: Add dYdX provider (also 0% fees)
            
        except Exception as e:
            logger.error(f"   ❌ Flashloan provider initialization failed: {e}")

    async def execute_arbitrage(self, opportunity: Dict[str, Any], private_key: str = None) -> Dict[str, Any]:
        """Execute arbitrage using flashloans - NO BALANCE LIMITS!"""
        try:
            logger.info(f"⚡ EXECUTING FLASHLOAN ARBITRAGE!")
            logger.info(f"   🎯 Opportunity: {opportunity.get('token', 'Unknown')} {opportunity.get('direction', '')}")
            
            # Calculate required flashloan amount
            flashloan_amount = await self._calculate_flashloan_amount(opportunity)
            
            logger.info(f"   💰 Flashloan amount: ${flashloan_amount:,.2f}")
            
            # Validate flashloan profitability
            if not await self._validate_flashloan_profitability(opportunity, flashloan_amount):
                return {'success': False, 'error': 'Flashloan not profitable after fees'}
            
            # Execute flashloan arbitrage
            result = await self._execute_flashloan_arbitrage(opportunity, flashloan_amount)
            
            if result['success']:
                logger.info(f"   ✅ FLASHLOAN ARBITRAGE SUCCESS!")
                logger.info(f"   💰 Net profit: ${result.get('net_profit', 0):.2f}")
            else:
                logger.error(f"   ❌ FLASHLOAN ARBITRAGE FAILED: {result.get('error', 'Unknown')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Flashloan arbitrage execution error: {e}")
            return {'success': False, 'error': f'Execution error: {e}'}

    async def _calculate_flashloan_amount(self, opportunity: Dict[str, Any]) -> float:
        """Calculate optimal flashloan amount for the opportunity."""
        # For now, use a fixed amount - can be optimized later
        base_amount = 50000  # $50K base amount
        
        # Adjust based on opportunity size and profit potential
        profit_pct = opportunity.get('profit_percentage', 0.1)
        if profit_pct > 1.0:  # High profit opportunities
            return min(base_amount * 2, self.max_flashloan_amount)
        else:
            return max(base_amount, self.min_flashloan_amount)

    async def _validate_flashloan_profitability(self, opportunity: Dict[str, Any], flashloan_amount: float) -> bool:
        """Validate that flashloan will be profitable after all fees."""
        try:
            # 🔍 PROFIT TRACKING: Show where expected profit comes from
            logger.info(f"   🔍 PROFIT CALCULATION BREAKDOWN:")

            # Original opportunity data
            original_profit_pct = opportunity.get('profit_percentage', 0)
            original_profit_usd = opportunity.get('estimated_profit_usd', 0)
            original_trade_amount = opportunity.get('trade_amount_usd', 0)

            logger.info(f"      📊 ORIGINAL OPPORTUNITY:")
            logger.info(f"         💰 Trade amount: ${original_trade_amount:,.2f}")
            logger.info(f"         📈 Profit %: {original_profit_pct:.4f}%")
            logger.info(f"         💵 Expected profit: ${original_profit_usd:.2f}")

            # Flashloan calculation
            profit_pct = opportunity.get('profit_percentage', 0)
            gross_profit = flashloan_amount * (profit_pct / 100)

            logger.info(f"      🏦 FLASHLOAN SCALING:")
            logger.info(f"         💰 Flashloan amount: ${flashloan_amount:,.2f}")
            logger.info(f"         📈 Same profit %: {profit_pct:.4f}%")
            logger.info(f"         💵 Scaled gross profit: ${gross_profit:.2f}")
            logger.info(f"         🔄 Scaling factor: {flashloan_amount / max(original_trade_amount, 1):.2f}x")

            # Calculate costs
            if self.flashloan_provider == 'balancer':
                flashloan_fee = 0.0  # 0% Balancer fee - FREE!
                fee_pct = 0.0
            elif self.flashloan_provider == 'aave':
                flashloan_fee = flashloan_amount * 0.0009  # 0.09% Aave fee
                fee_pct = 0.09
            else:
                flashloan_fee = 0.0  # Default to free
                fee_pct = 0.0

            gas_cost = 10  # Estimated gas cost on L2

            logger.info(f"      💸 COST BREAKDOWN:")
            logger.info(f"         🏦 Flashloan fee ({fee_pct}%): ${flashloan_fee:.2f}")
            logger.info(f"         ⛽ Gas cost estimate: ${gas_cost:.2f}")
            logger.info(f"         💰 Total costs: ${flashloan_fee + gas_cost:.2f}")

            net_profit = gross_profit - flashloan_fee - gas_cost
            required_profit = flashloan_fee * self.flashloan_safety_margin

            logger.info(f"      🎯 FINAL CALCULATION:")
            logger.info(f"         📈 Gross profit: ${gross_profit:.2f}")
            logger.info(f"         💸 Total costs: ${flashloan_fee + gas_cost:.2f}")
            logger.info(f"         🎯 Expected net profit: ${net_profit:.2f}")
            logger.info(f"         🛡️  Required profit: ${required_profit:.2f}")

            # 🚨 PROFIT ESTIMATION WARNINGS
            if abs(gross_profit - original_profit_usd) > 10:
                logger.warning(f"      ⚠️  PROFIT MISMATCH: Original ${original_profit_usd:.2f} vs Scaled ${gross_profit:.2f}")

            if net_profit < original_profit_usd * 0.5:
                logger.warning(f"      ⚠️  HIGH COST IMPACT: Net profit ${net_profit:.2f} much lower than expected ${original_profit_usd:.2f}")

            is_profitable = net_profit >= required_profit
            logger.info(f"      {'✅' if is_profitable else '❌'} Profitable: {is_profitable}")

            return is_profitable

        except Exception as e:
            logger.error(f"   ❌ Profitability validation error: {e}")
            return False

    async def _execute_flashloan_arbitrage(self, opportunity: Dict[str, Any], flashloan_amount: float) -> Dict[str, Any]:
        """Execute the actual flashloan arbitrage trade."""
        try:
            logger.info(f"   ⚡ Executing flashloan arbitrage...")
            
            # Get flashloan provider
            provider = self.flashloan_providers.get(self.flashloan_provider)
            if not provider:
                return {'success': False, 'error': f'Flashloan provider {self.flashloan_provider} not available'}
            
            # EXECUTE REAL FLASHLOAN - NO MORE SIMULATION BULLSHIT!
            logger.info(f"   ⚡ EXECUTING REAL FLASHLOAN!")

            # Get Web3 connection
            network = opportunity.get('source_chain', 'arbitrum')
            web3 = self.web3_connections.get(network)

            if not web3:
                return {'success': False, 'error': f'No Web3 connection for {network}'}

            if not self.wallet_account:
                return {'success': False, 'error': 'No wallet account available'}

            # 🔍 EXECUTION TRACKING: Show expected vs actual
            expected_profit = opportunity.get('estimated_profit_usd', 0)
            logger.info(f"   🎯 EXECUTION TRACKING:")
            logger.info(f"      📊 Expected profit: ${expected_profit:.2f}")

            # Execute REAL flashloan
            result = await provider.execute_flashloan_arbitrage(opportunity, web3, self.wallet_account)

            # 🔍 RESULT ANALYSIS: Compare expected vs actual
            actual_profit = result.get('net_profit', 0)
            profit_difference = actual_profit - expected_profit

            if result['success']:
                logger.info(f"   ✅ REAL FLASHLOAN SUCCESS!")
                logger.info(f"   💰 Transaction: {result.get('transaction_hash', 'N/A')}")
                logger.info(f"   🔍 PROFIT ANALYSIS:")
                logger.info(f"      📊 Expected profit: ${expected_profit:.2f}")
                logger.info(f"      🎯 Actual net profit: ${actual_profit:.2f}")
                logger.info(f"      📈 Difference: ${profit_difference:.2f} ({((profit_difference/max(expected_profit,0.01))*100):+.1f}%)")

                # 🚨 PROFIT LOSS ANALYSIS
                if actual_profit < expected_profit * 0.5:
                    logger.warning(f"      ⚠️  MAJOR PROFIT LOSS: {((1-actual_profit/max(expected_profit,0.01))*100):.1f}% of expected profit lost!")

                    # Try to identify causes
                    gas_cost = result.get('gas_cost_usd', 0)
                    slippage_loss = result.get('slippage_loss_usd', 0)
                    fee_cost = result.get('fee_cost_usd', 0)

                    logger.warning(f"      🔍 LOSS BREAKDOWN:")
                    if gas_cost > 0:
                        logger.warning(f"         ⛽ Gas costs: ${gas_cost:.2f}")
                    if slippage_loss > 0:
                        logger.warning(f"         📉 Slippage loss: ${slippage_loss:.2f}")
                    if fee_cost > 0:
                        logger.warning(f"         💸 Fee costs: ${fee_cost:.2f}")

            else:
                logger.error(f"   ❌ REAL FLASHLOAN FAILED: {result.get('error', 'Unknown')}")
                logger.error(f"   💔 Expected profit lost: ${expected_profit:.2f}")

            return result
            
        except Exception as e:
            logger.error(f"   ❌ Flashloan execution error: {e}")
            return {'success': False, 'error': f'Execution error: {e}'}

    async def cleanup(self):
        """Cleanup flashloan executor resources."""
        logger.info("🧹 Cleaning up flashloan executor...")
        # Close any open connections
        self.web3_connections.clear()
        self.flashloan_providers.clear()
        logger.info("✅ Flashloan executor cleanup complete")
