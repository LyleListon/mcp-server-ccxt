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
            profit_pct = opportunity.get('profit_percentage', 0)
            gross_profit = flashloan_amount * (profit_pct / 100)
            
            # Calculate costs
            if self.flashloan_provider == 'balancer':
                flashloan_fee = 0.0  # 0% Balancer fee - FREE!
            elif self.flashloan_provider == 'aave':
                flashloan_fee = flashloan_amount * 0.0009  # 0.09% Aave fee
            else:
                flashloan_fee = 0.0  # Default to free

            gas_cost = 10  # Estimated gas cost on L2
            
            net_profit = gross_profit - flashloan_fee - gas_cost
            required_profit = flashloan_fee * self.flashloan_safety_margin
            
            logger.info(f"   📊 FLASHLOAN PROFITABILITY:")
            logger.info(f"      💰 Borrow amount: ${flashloan_amount:,.2f}")
            logger.info(f"      📈 Gross profit: ${gross_profit:.2f}")
            logger.info(f"      💸 Flashloan fee: ${flashloan_fee:.2f}")
            logger.info(f"      ⛽ Gas cost: ${gas_cost:.2f}")
            logger.info(f"      🎯 Net profit: ${net_profit:.2f}")
            logger.info(f"      🛡️  Required profit: ${required_profit:.2f}")
            
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

            # Execute REAL flashloan
            result = await provider.execute_flashloan_arbitrage(opportunity, web3, self.wallet_account)

            if result['success']:
                logger.info(f"   ✅ REAL FLASHLOAN SUCCESS!")
                logger.info(f"   💰 Transaction: {result['transaction_hash']}")
                logger.info(f"   🎯 Net profit: ${result['net_profit']:.2f}")
            else:
                logger.error(f"   ❌ REAL FLASHLOAN FAILED: {result.get('error', 'Unknown')}")

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
