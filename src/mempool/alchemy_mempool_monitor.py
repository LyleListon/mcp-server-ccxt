#!/usr/bin/env python3
"""
Alchemy Mempool Monitor
Monitor pending transactions for arbitrage opportunities and MEV protection.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import json
from dataclasses import dataclass
from web3 import Web3
import requests

logger = logging.getLogger(__name__)

@dataclass
class PendingTransaction:
    """Pending transaction data."""
    hash: str
    from_address: str
    to_address: str
    value: float
    gas_price: int
    gas_limit: int
    input_data: str
    timestamp: datetime
    predicted_impact: Optional[Dict[str, Any]] = None

@dataclass
class MempoolOpportunity:
    """Arbitrage opportunity detected from mempool."""
    tx_hash: str
    opportunity_type: str  # 'front_run', 'back_run', 'sandwich_defense'
    token: str
    predicted_price_change: float
    confidence: float
    execution_window_seconds: float
    estimated_profit_usd: float
    risk_level: str  # 'low', 'medium', 'high'

class AlchemyMempoolMonitor:
    """Monitor Alchemy mempool for arbitrage opportunities."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize mempool monitor."""
        self.config = config

        # Get API key from environment or config
        import os
        self.alchemy_api_key = config.get('alchemy_api_key') or os.getenv('ALCHEMY_API_KEY')

        if not self.alchemy_api_key:
            logger.error("❌ ALCHEMY_API_KEY not found in config or environment!")
            raise ValueError("ALCHEMY_API_KEY is required for mempool monitoring")

        logger.info(f"🔑 Mempool monitor using API key: {self.alchemy_api_key[:8]}...{self.alchemy_api_key[-4:]}")

        self.networks = config.get('networks', ['arbitrum', 'base', 'optimism'])

        # Mempool monitoring settings - 🎯 OPTIMIZED FOR YOUR ARBITRAGE SCALE!
        self.min_transaction_value = config.get('min_mempool_tx_value', 100)  # $100+ (much more realistic!)
        self.max_gas_price_gwei = config.get('max_gas_price_gwei', 50)  # Lower gas limit for L2s
        self.opportunity_callbacks = []

        # Network endpoints
        self.network_endpoints = {
            'arbitrum': f"https://arb-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
            'base': f"https://base-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
            'optimism': f"https://opt-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}",
            'ethereum': f"https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
        }
        
        # DEX contract addresses for monitoring
        self.dex_contracts = {
            'arbitrum': {
                'uniswap_v3': '0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45',
                'camelot': '0xc873fEcbd354f5A56E00E710B90EF4201db2448d',
                'sushiswap': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506'
            },
            'base': {
                'uniswap_v3': '0x2626664c2603336E57B271c5C0b26F421741e481',
                'aerodrome': '0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43'
            },
            'optimism': {
                'uniswap_v3': '0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45',
                'velodrome': '0xa132DAB612dB5cB9fC9Ac426A0Cc215A3423F9c9'
            }
        }
        
        self.running = False
        self.pending_transactions = {}
        
        logger.info(f"🔍 Mempool monitor initialized for {len(self.networks)} networks")
    
    def add_opportunity_callback(self, callback: Callable[[MempoolOpportunity], None]):
        """Add callback for mempool opportunities."""
        self.opportunity_callbacks.append(callback)
    
    async def start_monitoring(self):
        """Start mempool monitoring."""
        try:
            logger.info("🔍 Starting mempool monitoring...")
            self.running = True
            
            # Start monitoring tasks for each network
            tasks = []
            for network in self.networks:
                task = self._monitor_network_mempool(network)
                tasks.append(task)
            
            # Run all monitoring tasks
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Mempool monitoring error: {e}")
        finally:
            self.running = False
    
    async def stop_monitoring(self):
        """Stop mempool monitoring."""
        logger.info("🛑 Stopping mempool monitoring...")
        self.running = False
    
    async def _monitor_network_mempool(self, network: str):
        """Monitor mempool for a specific network."""
        try:
            endpoint = self.network_endpoints.get(network)
            if not endpoint:
                logger.warning(f"No endpoint for network: {network}")
                return
            
            logger.info(f"🔍 Monitoring {network} mempool...")
            
            while self.running:
                try:
                    # Get pending transactions
                    pending_txs = await self._get_pending_transactions(network, endpoint)
                    
                    if pending_txs:
                        logger.debug(f"📊 {network}: {len(pending_txs)} pending transactions")
                        
                        # Analyze transactions for opportunities
                        opportunities = await self._analyze_pending_transactions(network, pending_txs)
                        
                        # Notify callbacks of opportunities
                        for opportunity in opportunities:
                            await self._notify_opportunity(opportunity)
                    
                    # Wait before next check
                    await asyncio.sleep(2)  # Check every 2 seconds
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Network {network} mempool monitoring error: {e}")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            logger.error(f"Network {network} mempool monitor failed: {e}")
    
    async def _get_pending_transactions(self, network: str, endpoint: str) -> List[PendingTransaction]:
        """Get pending transactions from Alchemy using proper mempool API."""
        try:
            logger.info(f"   🔍 Fetching pending transactions for {network}...")

            # 🚀 ALCHEMY FREE TIER COMPATIBLE - Use alchemy_pendingTransactions
            payload = {
                "jsonrpc": "2.0",
                "method": "alchemy_pendingTransactions",
                "params": [{
                    "hashesOnly": False,
                    "fromAddress": None,
                    "toAddress": None
                }],
                "id": 1
            }

            # Make async request
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()

                        if 'result' in data and 'pending' in data['result']:
                            pending_txs = []
                            pending_pool = data['result']['pending']

                            # Extract transactions from pending pool
                            tx_count = 0
                            for address, nonce_txs in pending_pool.items():
                                if tx_count >= 50:  # Limit to 50 transactions
                                    break

                                for nonce, tx_data in nonce_txs.items():
                                    if tx_count >= 50:
                                        break

                                    tx = self._parse_transaction(tx_data)
                                    if tx and self._is_relevant_transaction(tx):
                                        pending_txs.append(tx)
                                        tx_count += 1

                            logger.debug(f"📊 {network}: Found {len(pending_txs)} relevant pending transactions")
                            return pending_txs
                        else:
                            logger.debug(f"📊 {network}: No pending transactions found")
                    else:
                        logger.warning(f"Alchemy API error: {response.status}")

                        # 🔄 FALLBACK: Try alternative method
                        return await self._get_pending_transactions_fallback(network, endpoint)

            return []

        except Exception as e:
            logger.error(f"Pending transactions fetch error: {e}")
            # Try fallback method
            return await self._get_pending_transactions_fallback(network, endpoint)

    async def _get_pending_transactions_fallback(self, network: str, endpoint: str) -> List[PendingTransaction]:
        """Fallback method using eth_getBlockByNumber with pending."""
        try:
            logger.debug(f"🔄 Using fallback method for {network} mempool...")

            payload = {
                "jsonrpc": "2.0",
                "method": "eth_getBlockByNumber",
                "params": ["pending", True],  # Get pending block with full transactions
                "id": 1
            }

            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()

                        if 'result' in data and data['result'] and 'transactions' in data['result']:
                            pending_txs = []
                            transactions = data['result']['transactions'][:50]  # Limit to 50

                            for tx_data in transactions:
                                tx = self._parse_transaction(tx_data)
                                if tx and self._is_relevant_transaction(tx):
                                    pending_txs.append(tx)

                            logger.debug(f"📊 {network} fallback: Found {len(pending_txs)} relevant transactions")
                            return pending_txs
                    else:
                        logger.warning(f"Fallback API error: {response.status}")

            return []

        except Exception as e:
            logger.error(f"Fallback pending transactions error: {e}")
            return []

    def _parse_transaction(self, tx_data: Dict[str, Any]) -> Optional[PendingTransaction]:
        """Parse transaction data."""
        try:
            return PendingTransaction(
                hash=tx_data.get('hash', ''),
                from_address=tx_data.get('from', ''),
                to_address=tx_data.get('to', ''),
                value=float(int(tx_data.get('value', '0'), 16)) / 1e18,  # Convert to ETH
                gas_price=int(tx_data.get('gasPrice', '0'), 16) // 1e9,  # Convert to gwei
                gas_limit=int(tx_data.get('gas', '0'), 16),
                input_data=tx_data.get('input', ''),
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Transaction parsing error: {e}")
            return None
    
    def _is_relevant_transaction(self, tx: PendingTransaction) -> bool:
        """Check if transaction is relevant for arbitrage."""
        try:
            # 🎯 OPTIMIZED FILTERS FOR YOUR ARBITRAGE SCALE!

            # Filter by transaction value (much lower threshold!)
            eth_price = 3500  # Approximate ETH price
            min_value_eth = self.min_transaction_value / eth_price  # $100 / $3500 = ~0.03 ETH
            if tx.value < min_value_eth:
                return False

            # Filter by gas price (avoid extremely high gas)
            if tx.gas_price > self.max_gas_price_gwei:
                return False

            # Check if it's a DEX interaction (has input data)
            if len(tx.input_data) < 10:  # Simple transfers
                return False

            # 🎯 ADDITIONAL FILTERS: Look for DEX-related transactions
            # Check if transaction is to known DEX contracts
            dex_addresses = set()
            for network_dexes in self.dex_contracts.values():
                dex_addresses.update(network_dexes.values())

            if tx.to_address.lower() in [addr.lower() for addr in dex_addresses]:
                logger.debug(f"🎯 Found DEX transaction: {tx.hash[:10]}... to {tx.to_address}")
                return True

            # Check for swap-like function signatures in input data
            swap_signatures = [
                '0x38ed1739',  # swapExactTokensForTokens
                '0x8803dbee',  # swapTokensForExactTokens
                '0x7ff36ab5',  # swapExactETHForTokens
                '0x18cbafe5',  # swapExactTokensForETH
                '0x414bf389',  # swapExactTokensForTokensSupportingFeeOnTransferTokens
            ]

            for sig in swap_signatures:
                if tx.input_data.startswith(sig):
                    logger.debug(f"🎯 Found swap transaction: {tx.hash[:10]}... with signature {sig}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Transaction relevance check error: {e}")
            return False
    
    async def _analyze_pending_transactions(self, network: str, transactions: List[PendingTransaction]) -> List[MempoolOpportunity]:
        """Analyze pending transactions for arbitrage opportunities."""
        try:
            opportunities = []
            
            for tx in transactions:
                # Analyze transaction for different opportunity types
                
                # 1. Large swap detection (front-running opportunity)
                if await self._is_large_swap(tx):
                    opportunity = await self._create_front_run_opportunity(network, tx)
                    if opportunity:
                        opportunities.append(opportunity)
                
                # 2. Sandwich attack detection (defense needed)
                if await self._is_sandwich_attack(tx):
                    opportunity = await self._create_sandwich_defense(network, tx)
                    if opportunity:
                        opportunities.append(opportunity)
                
                # 3. Arbitrage setup detection (back-running opportunity)
                if await self._is_arbitrage_setup(tx):
                    opportunity = await self._create_back_run_opportunity(network, tx)
                    if opportunity:
                        opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Transaction analysis error: {e}")
            return []
    
    async def _is_large_swap(self, tx: PendingTransaction) -> bool:
        """Check if transaction is a large swap."""
        # 🎯 OPTIMIZED FOR YOUR SCALE: Much lower thresholds!
        return tx.value > 0.1 and tx.gas_limit > 150000  # ~$350+ swap (realistic!)

    async def _is_sandwich_attack(self, tx: PendingTransaction) -> bool:
        """Check if transaction is part of a sandwich attack."""
        # Check for suspicious gas pricing patterns on L2s
        return tx.gas_price > 20  # High gas price for L2 (potential front-runner)

    async def _is_arbitrage_setup(self, tx: PendingTransaction) -> bool:
        """Check if transaction creates arbitrage opportunity."""
        # 🎯 PERFECT FOR YOUR ARBITRAGE RANGE: $35-$1750 swaps
        return 0.01 < tx.value < 0.5 and tx.gas_limit > 100000  # Much more realistic range!
    
    async def _create_front_run_opportunity(self, network: str, tx: PendingTransaction) -> Optional[MempoolOpportunity]:
        """Create front-running opportunity."""
        try:
            return MempoolOpportunity(
                tx_hash=tx.hash,
                opportunity_type='front_run',
                token='ETH',  # Simplified
                predicted_price_change=0.5,  # 0.5% predicted impact
                confidence=0.7,
                execution_window_seconds=12,  # Block time
                estimated_profit_usd=tx.value * 0.005,  # 0.5% of transaction value
                risk_level='medium'
            )
        except Exception as e:
            logger.error(f"Front-run opportunity creation error: {e}")
            return None
    
    async def _create_sandwich_defense(self, network: str, tx: PendingTransaction) -> Optional[MempoolOpportunity]:
        """Create sandwich defense opportunity."""
        try:
            return MempoolOpportunity(
                tx_hash=tx.hash,
                opportunity_type='sandwich_defense',
                token='ETH',
                predicted_price_change=0,
                confidence=0.9,
                execution_window_seconds=5,
                estimated_profit_usd=0,  # Defense, not profit
                risk_level='high'
            )
        except Exception as e:
            logger.error(f"Sandwich defense creation error: {e}")
            return None
    
    async def _create_back_run_opportunity(self, network: str, tx: PendingTransaction) -> Optional[MempoolOpportunity]:
        """Create back-running opportunity."""
        try:
            return MempoolOpportunity(
                tx_hash=tx.hash,
                opportunity_type='back_run',
                token='ETH',
                predicted_price_change=0.2,  # 0.2% predicted impact
                confidence=0.8,
                execution_window_seconds=15,
                estimated_profit_usd=tx.value * 0.002,  # 0.2% of transaction value
                risk_level='low'
            )
        except Exception as e:
            logger.error(f"Back-run opportunity creation error: {e}")
            return None
    
    async def _notify_opportunity(self, opportunity: MempoolOpportunity):
        """Notify callbacks of mempool opportunity."""
        try:
            logger.info(f"🎯 MEMPOOL OPPORTUNITY: {opportunity.opportunity_type} - "
                       f"{opportunity.token} - ${opportunity.estimated_profit_usd:.2f} profit")
            
            for callback in self.opportunity_callbacks:
                try:
                    await callback(opportunity)
                except Exception as e:
                    logger.error(f"Opportunity callback error: {e}")
                    
        except Exception as e:
            logger.error(f"Opportunity notification error: {e}")
    
    def get_mempool_stats(self) -> Dict[str, Any]:
        """Get mempool monitoring statistics."""
        return {
            'networks_monitored': len(self.networks),
            'pending_transactions': len(self.pending_transactions),
            'monitoring_active': self.running,
            'callbacks_registered': len(self.opportunity_callbacks)
        }
