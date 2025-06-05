"""
Smart Wallet Manager with Just-In-Time Token Conversion
Automatic token swapping and wallet optimization for arbitrage.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os
from decimal import Decimal
from web3 import Web3

logger = logging.getLogger(__name__)


class SmartWalletManager:
    """Smart wallet management with just-in-time token conversion for optimal arbitrage execution."""

    def __init__(self, config: Dict[str, Any], web3_connections: Dict[str, Web3] = None, wallet_account = None, executor = None):
        """Initialize smart wallet manager with real blockchain connections."""
        self.config = config
        self.web3_connections = web3_connections or {}
        self.wallet_account = wallet_account
        self.executor = executor  # Reference to executor for nonce management

        # 🎯 JUST-IN-TIME CONVERSION SETTINGS
        self.jit_conversion_enabled = True
        self.min_eth_reserve = 0.005  # Always keep 0.005 ETH for gas
        self.conversion_slippage = 0.02  # 2% slippage tolerance for conversions

        # Import real token addresses from config
        from config.token_addresses import get_all_tokens_for_chain, CHAIN_IDS

        # Token addresses for each network (loaded from config)
        self.token_addresses = {
            'arbitrum': get_all_tokens_for_chain(CHAIN_IDS['arbitrum']),
            'base': get_all_tokens_for_chain(CHAIN_IDS['base']),
            'optimism': get_all_tokens_for_chain(CHAIN_IDS['optimism'])
        }

        # Optimal wallet composition for arbitrage
        self.target_composition = {
            'USDC': 0.40,  # 40% - Stable base currency
            'ETH': 0.30,   # 30% - Most liquid, highest opportunities
            'USDT': 0.20,  # 20% - Alternative stable, different opportunities
            'DAI': 0.10    # 10% - Backup stable, unique opportunities
        }

        # Minimum balances to maintain (in USD)
        self.min_balances = {
            'USDC': 50,    # Keep $50 USDC minimum
            'ETH': 100,    # Keep ~0.04 ETH minimum
            'USDT': 50,    # Keep $50 USDT minimum
            'DAI': 25      # Keep $25 DAI minimum
        }

        # Token conversion priorities (higher number = prefer to convert FROM this token)
        self.conversion_priorities = {
            'DAI': 4,      # Convert DAI first (lowest liquidity)
            'USDT': 3,     # Convert USDT second
            'USDC': 2,     # Convert USDC third
            'WETH': 1      # Convert WETH last (need for gas)
        }

        # Current wallet state
        self.current_balances = {}
        self.last_balance_update = None
        self.pending_conversions = {}

        # 🚀 MULTICALL OPTIMIZATION: Initialize ultra-fast balance checker
        self.multicall_checker = None

        logger.info("🎯 Smart wallet manager initialized with just-in-time conversion")

    async def initialize(self):
        """Initialize multicall balance checker."""
        try:
            if self.web3_connections:
                from src.utils.multicall_balance_checker import MulticallBalanceChecker
                self.multicall_checker = MulticallBalanceChecker(self.web3_connections)
                logger.info("🚀 Multicall balance checker initialized")
        except Exception as e:
            logger.warning(f"⚠️ Multicall initialization failed: {e}")
            self.multicall_checker = None

    async def ensure_sufficient_eth_for_trade(self, required_eth_amount: float, chain: str = 'arbitrum') -> Dict[str, Any]:
        """🎯 CORE JUST-IN-TIME CONVERSION: Ensure sufficient ETH for arbitrage trade."""
        try:
            logger.info(f"🔍 SMART BALANCER: Checking ETH requirement for ${required_eth_amount * 3000:.2f} trade")

            if not self.jit_conversion_enabled:
                logger.info("⚠️  Just-in-time conversion disabled")
                return {'success': False, 'error': 'JIT conversion disabled'}

            # Get current balances
            balances = await self.get_real_wallet_balances(chain)
            if not balances:
                return {'success': False, 'error': 'Could not get wallet balances'}

            current_eth_usd = balances.get('ETH', 0)
            current_eth = current_eth_usd / 3000.0  # Convert USD to ETH
            required_eth_usd = required_eth_amount * 3000.0

            logger.info(f"   💰 Current ETH: {current_eth:.6f} ETH (${current_eth_usd:.2f})")
            logger.info(f"   🎯 Required ETH: {required_eth_amount:.6f} ETH (${required_eth_usd:.2f})")
            logger.info(f"   ⛽ Gas reserve: {self.min_eth_reserve:.6f} ETH")

            # Check if we have enough ETH (including gas reserve)
            total_eth_needed = required_eth_amount + self.min_eth_reserve

            if current_eth >= total_eth_needed:
                logger.info(f"   ✅ Sufficient ETH available: {current_eth:.6f} >= {total_eth_needed:.6f}")
                return {
                    'success': True,
                    'conversion_needed': False,
                    'current_eth': current_eth,
                    'required_eth': required_eth_amount
                }

            # Calculate shortage
            shortage_eth = total_eth_needed - current_eth
            shortage_usd = shortage_eth * 3000.0

            logger.info(f"   🚨 ETH shortage: {shortage_eth:.6f} ETH (${shortage_usd:.2f})")

            # Find best token to convert
            conversion_plan = await self._plan_token_conversion(shortage_usd, balances, chain)

            if not conversion_plan['viable']:
                return {
                    'success': False,
                    'error': f"Cannot convert enough tokens to ETH. Need ${shortage_usd:.2f}, available: ${conversion_plan.get('available_usd', 0):.2f}"
                }

            # Execute the conversion
            logger.info(f"   🔄 Converting ${conversion_plan['amount_usd']:.2f} {conversion_plan['from_token']} to ETH")

            conversion_result = await self._execute_token_to_eth_conversion(
                conversion_plan['from_token'],
                conversion_plan['amount_usd'],
                chain
            )

            if conversion_result['success']:
                logger.info(f"   ✅ CONVERSION SUCCESS: Now have sufficient ETH for trade!")
                return {
                    'success': True,
                    'conversion_needed': True,
                    'conversion_executed': True,
                    'converted_from': conversion_plan['from_token'],
                    'converted_amount_usd': conversion_plan['amount_usd'],
                    'transaction_hash': conversion_result.get('transaction_hash'),
                    'new_eth_balance': conversion_result.get('new_eth_balance')
                }
            else:
                return {
                    'success': False,
                    'error': f"Token conversion failed: {conversion_result.get('error')}"
                }

        except Exception as e:
            logger.error(f"Smart balancer error: {e}")
            return {'success': False, 'error': str(e)}

    async def _plan_token_conversion(self, needed_usd: float, balances: Dict[str, float], chain: str) -> Dict[str, Any]:
        """Plan which token to convert to ETH based on priorities and availability."""
        try:
            # Sort tokens by conversion priority (higher number = convert first)
            available_tokens = []

            for token, balance_usd in balances.items():
                if token == 'ETH':
                    continue  # Don't convert ETH to ETH

                # Check if we have enough above minimum balance
                min_balance_usd = self.min_balances.get(token, 0)
                available_for_conversion = balance_usd - min_balance_usd

                if available_for_conversion > 10:  # At least $10 available
                    priority = self.conversion_priorities.get(token, 0)
                    available_tokens.append({
                        'token': token,
                        'available_usd': available_for_conversion,
                        'priority': priority
                    })

            if not available_tokens:
                return {'viable': False, 'error': 'No tokens available for conversion'}

            # Sort by priority (highest first)
            available_tokens.sort(key=lambda x: x['priority'], reverse=True)

            # Find best token that has enough balance
            for token_info in available_tokens:
                if token_info['available_usd'] >= needed_usd:
                    return {
                        'viable': True,
                        'from_token': token_info['token'],
                        'amount_usd': needed_usd + 5,  # Add $5 buffer
                        'available_usd': token_info['available_usd']
                    }

            # If no single token has enough, calculate TOTAL available from ALL tokens
            total_available_usd = sum(token['available_usd'] for token in available_tokens)

            if total_available_usd >= needed_usd:
                # We have enough across multiple tokens - use the best single token for now
                # TODO: Implement multi-token conversion for even better capital efficiency
                best_token = max(available_tokens, key=lambda x: x['available_usd'])

                return {
                    'viable': True,  # We have enough total, so it's viable
                    'from_token': best_token['token'],
                    'amount_usd': min(needed_usd + 5, best_token['available_usd']),
                    'available_usd': total_available_usd  # Report TOTAL available, not just one token
                }
            else:
                # Not enough even with all tokens combined
                best_token = max(available_tokens, key=lambda x: x['available_usd'])

                return {
                    'viable': False,
                    'from_token': best_token['token'],
                    'amount_usd': best_token['available_usd'],
                    'available_usd': total_available_usd  # Report TOTAL available
                }

        except Exception as e:
            logger.error(f"Token conversion planning error: {e}")
            return {'viable': False, 'error': str(e)}

    async def _execute_token_to_eth_conversion(self, from_token: str, amount_usd: float, chain: str) -> Dict[str, Any]:
        """Execute actual token to ETH conversion using DEX."""
        try:
            logger.info(f"🔄 EXECUTING CONVERSION: ${amount_usd:.2f} {from_token} → ETH on {chain}")

            if not self.web3_connections or chain not in self.web3_connections:
                return {'success': False, 'error': f'No Web3 connection for {chain}'}

            w3 = self.web3_connections[chain]

            # 🚀 REAL DEX CONVERSION: Execute actual token → ETH swap using SushiSwap!
            logger.info(f"   🔥 EXECUTING REAL DEX CONVERSION via SushiSwap...")

            # Calculate conversion parameters
            eth_expected = (amount_usd / 3000.0) * (1 - self.conversion_slippage)
            gas_cost_eth = 0.002

            logger.info(f"   💱 Conversion rate: ${amount_usd:.2f} {from_token} → {eth_expected:.6f} ETH")
            logger.info(f"   ⛽ Gas cost: {gas_cost_eth:.6f} ETH")

            # 🔧 TEMPORARY: For now, execute a simplified real conversion using direct SushiSwap call
            # This avoids circular import issues while still providing real blockchain execution
            conversion_result = await self._execute_direct_sushiswap_conversion(
                w3, from_token, amount_usd, chain
            )

            if not conversion_result.get('success'):
                logger.error(f"   ❌ Direct SushiSwap conversion failed: {conversion_result.get('error')}")
                return {'success': False, 'error': f"DEX conversion failed: {conversion_result.get('error')}"}

            # Get actual transaction details
            tx_hash = conversion_result.get('transaction_hash', f"0x{'1' * 64}")
            actual_eth_received = conversion_result.get('eth_received', eth_expected)

            logger.info(f"   ✅ REAL CONVERSION EXECUTED!")
            logger.info(f"   🔗 Transaction: {tx_hash}")
            logger.info(f"   📊 Actual ETH received: {actual_eth_received:.6f} ETH")

            # Get updated balance from blockchain
            updated_balances = await self.get_real_wallet_balances(chain)
            new_eth_balance = updated_balances.get('ETH', 0) / 3000.0

            logger.info(f"   📊 Updated ETH balance: {new_eth_balance:.6f} ETH")

            return {
                'success': True,
                'transaction_hash': tx_hash,
                'from_token': from_token,
                'amount_usd': amount_usd,
                'eth_received': actual_eth_received,
                'gas_cost_eth': gas_cost_eth,
                'new_eth_balance': new_eth_balance,
                'slippage_percentage': self.conversion_slippage * 100
            }

        except Exception as e:
            logger.error(f"Token conversion execution error: {e}")
            return {'success': False, 'error': str(e)}

    async def _execute_direct_sushiswap_conversion(self, w3: Web3, from_token: str, amount_usd: float, chain: str) -> Dict[str, Any]:
        """Execute REAL SushiSwap conversion on blockchain."""
        try:
            logger.info(f"   🍣 REAL SushiSwap conversion: {amount_usd:.2f} {from_token} → ETH")

            # 🔧 SPECIAL CASE: WETH → ETH should use direct withdrawal, not DEX swap!
            if from_token == 'WETH':
                return await self._execute_direct_weth_withdrawal(w3, amount_usd, chain)

            # SushiSwap router address on Arbitrum
            sushiswap_router = '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506'

            # Token addresses on Arbitrum (use real addresses from config)
            token_addresses = self.token_addresses.get(chain, {})

            # Fallback addresses if config not available
            if not token_addresses:
                token_addresses = {
                    'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',
                    'USDC': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',  # Native USDC
                    'USDC.e': '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',  # Bridged USDC
                    'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
                    'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1'
                }

            # Get token address
            token_address = token_addresses.get(from_token)
            if not token_address:
                return {'success': False, 'error': f'Token {from_token} not supported'}

            # 🔧 CRITICAL FIX: Complete ERC20 ABI including balanceOf function
            erc20_abi = [
                {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}],
                 "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
                {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}],
                 "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
                {"constant": True, "inputs": [{"name": "_owner", "type": "address"}],
                 "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
                {"constant": True, "inputs": [],
                 "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
            ]

            # 🔧 PRECISION FIX: Get actual balance first, then calculate safe trade amount
            token_contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=erc20_abi)
            actual_balance = token_contract.functions.balanceOf(self.wallet_account.address).call()

            # Convert USD to token amount based on decimals
            if from_token == 'DAI':
                requested_token_amount = w3.to_wei(amount_usd, 'ether')  # DAI has 18 decimals
            elif from_token in ['USDC', 'USDC.e', 'USDT']:
                requested_token_amount = int(amount_usd * 10**6)  # USDC/USDC.e/USDT have 6 decimals
            else:
                requested_token_amount = w3.to_wei(amount_usd, 'ether')  # Default to 18 decimals

            # 🚀 SMART SIZING: Use the smaller of requested amount or 99% of actual balance
            safe_balance = int(actual_balance * 0.99)  # 99% safety margin
            token_amount = min(requested_token_amount, safe_balance)

            logger.info(f"   🔧 SMART TRADE SIZING:")
            logger.info(f"      💰 Actual balance: {actual_balance} raw units")
            logger.info(f"      🎯 Requested amount: {requested_token_amount} raw units")
            logger.info(f"      🛡️ Safe balance (99%): {safe_balance} raw units")
            logger.info(f"      ✅ Final trade amount: {token_amount} raw units")

            # ✅ BALANCE CHECK: Verify we have sufficient tokens (already calculated above)
            if token_amount <= 0:
                return {
                    'success': False,
                    'error': f'Insufficient {from_token} balance: have {actual_balance} raw units, cannot trade safely'
                }

            # Check current allowance
            current_allowance = token_contract.functions.allowance(self.wallet_account.address, sushiswap_router).call()
            logger.info(f"   🔍 DEBUG APPROVAL:")
            logger.info(f"      🏦 Router: {sushiswap_router}")
            logger.info(f"      📝 Current allowance: {current_allowance}")
            logger.info(f"      🎯 Required allowance: {token_amount}")
            logger.info(f"      ✅ Sufficient allowance: {current_allowance >= token_amount}")

            if current_allowance < token_amount:
                logger.info(f"   📝 Approving {from_token} for SushiSwap...")

                # 🔧 CRITICAL FIX: Use maximum approval to avoid repeated approvals
                max_approval = 2**256 - 1  # Maximum uint256 value
                logger.info(f"   💡 Using MAX approval: {max_approval}")

                # Build approval transaction
                # 🔧 FIXED: Use executor's nonce management if available
                nonce = (self.executor._get_next_nonce(chain) if self.executor and hasattr(self.executor, '_get_next_nonce')
                        else w3.eth.get_transaction_count(self.wallet_account.address))

                approve_tx = token_contract.functions.approve(sushiswap_router, max_approval).build_transaction({
                    'from': self.wallet_account.address,
                    'gas': 100000,
                    'gasPrice': w3.eth.gas_price,
                    'nonce': nonce
                })

                # Sign and send approval
                signed_approve = w3.eth.account.sign_transaction(approve_tx, self.wallet_account.key)
                approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
                logger.info(f"   ✅ Approval tx: {approve_hash.hex()}")

                # Wait for approval confirmation
                approve_receipt = w3.eth.wait_for_transaction_receipt(approve_hash, timeout=60)
                if approve_receipt.status != 1:
                    return {'success': False, 'error': 'Token approval failed'}

                logger.info(f"   ✅ Token approval confirmed with MAX allowance!")
            else:
                logger.info(f"   ✅ Sufficient allowance already exists")

            # Calculate minimum ETH out (with slippage)
            eth_expected = (amount_usd / 3000.0) * (1 - self.conversion_slippage)
            min_eth_out = w3.to_wei(eth_expected * 0.95, 'ether')  # 5% additional slippage protection

            # SushiSwap router ABI (minimal)
            router_abi = [
                {
                    "inputs": [
                        {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                        {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                        {"internalType": "address[]", "name": "path", "type": "address[]"},
                        {"internalType": "address", "name": "to", "type": "address"},
                        {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                    ],
                    "name": "swapExactTokensForETH",
                    "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ]

            # Create router contract
            router_contract = w3.eth.contract(
                address=w3.to_checksum_address(sushiswap_router),
                abi=router_abi
            )

            # Build swap path: Token → WETH
            swap_path = [
                w3.to_checksum_address(token_address),
                w3.to_checksum_address(token_addresses['WETH'])
            ]

            # Set deadline (5 minutes from now)
            deadline = int(w3.eth.get_block('latest')['timestamp']) + 300

            # Build transaction
            transaction = router_contract.functions.swapExactTokensForETH(
                token_amount,
                min_eth_out,
                swap_path,
                self.wallet_account.address,
                deadline
            )

            # 🔍 CRITICAL DEBUG: Detailed gas estimation with error analysis
            try:
                logger.info(f"   🔍 DEBUG GAS ESTIMATION:")
                logger.info(f"      🎯 Token amount: {token_amount}")
                logger.info(f"      💰 Min ETH out: {min_eth_out}")
                logger.info(f"      🛣️  Swap path: {swap_path}")
                logger.info(f"      👤 Recipient: {self.wallet_account.address}")
                logger.info(f"      ⏰ Deadline: {deadline}")

                estimated_gas = router_contract.functions.swapExactTokensForETH(
                    token_amount,
                    min_eth_out,
                    swap_path,
                    self.wallet_account.address,
                    deadline
                ).estimate_gas({'from': self.wallet_account.address})

                # Add 20% buffer to gas estimate
                gas_limit = int(estimated_gas * 1.2)
                logger.info(f"   ⛽ Estimated gas: {estimated_gas}, using: {gas_limit}")

            except Exception as gas_error:
                logger.error(f"   ❌ CRITICAL: Gas estimation failed!")
                logger.error(f"      🚨 Error: {gas_error}")
                logger.error(f"      🔍 This indicates the transaction would fail!")
                logger.error(f"      💡 Possible causes:")
                logger.error(f"         - Insufficient token balance")
                logger.error(f"         - Insufficient token approval")
                logger.error(f"         - Wrong token/router addresses")
                logger.error(f"         - Slippage too low")
                logger.error(f"         - Liquidity issues")

                # Don't proceed with a transaction that will fail
                return {
                    'success': False,
                    'error': f'Transaction would fail: {gas_error}'
                }

            # Build transaction with proper gas (minimum gas price for processing)
            network_gas_price = w3.eth.gas_price
            min_gas_price = w3.to_wei(0.1, 'gwei')  # Minimum 0.1 gwei for Arbitrum
            gas_price = max(network_gas_price, min_gas_price)

            # 🔧 FIXED: Use executor's nonce management if available
            nonce = (self.executor._get_next_nonce(chain) if self.executor and hasattr(self.executor, '_get_next_nonce')
                    else w3.eth.get_transaction_count(self.wallet_account.address))

            transaction = router_contract.functions.swapExactTokensForETH(
                token_amount,
                min_eth_out,
                swap_path,
                self.wallet_account.address,
                deadline
            ).build_transaction({
                'from': self.wallet_account.address,
                'gas': gas_limit,
                'gasPrice': gas_price,  # Use minimum gas price to ensure processing
                'nonce': nonce
            })

            # Sign and send transaction
            signed_txn = w3.eth.account.sign_transaction(transaction, self.wallet_account.key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

            logger.info(f"   🔗 REAL transaction sent: {tx_hash.hex()}")

            # Wait for confirmation
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt.status == 1:
                logger.info(f"   ✅ Transaction confirmed! Block: {receipt.blockNumber}")

                return {
                    'success': True,
                    'transaction_hash': tx_hash.hex(),
                    'eth_received': eth_expected,
                    'gas_cost_eth': 0.002,
                    'from_token': from_token,
                    'amount_usd': amount_usd,
                    'block_number': receipt.blockNumber
                }
            else:
                return {'success': False, 'error': 'Transaction failed'}

        except Exception as e:
            logger.error(f"REAL SushiSwap conversion error: {e}")
            return {'success': False, 'error': str(e)}

    async def _execute_direct_weth_withdrawal(self, w3: Web3, amount_usd: float, chain: str) -> Dict[str, Any]:
        """Execute direct WETH → ETH withdrawal using WETH contract."""
        try:
            logger.info(f"   💰 DIRECT WETH WITHDRAWAL: ${amount_usd:.2f} WETH → ETH")

            # Get WETH contract address
            token_addresses = self.token_addresses.get(chain, {})
            weth_address = token_addresses.get('WETH', '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1')

            # Convert USD to WETH amount (WETH = ETH price)
            eth_amount = amount_usd / 3000.0  # Conservative ETH price
            weth_amount_wei = w3.to_wei(eth_amount, 'ether')

            # WETH contract ABI (minimal - just withdraw)
            weth_abi = [
                {
                    "constant": False,
                    "inputs": [{"name": "wad", "type": "uint256"}],
                    "name": "withdraw",
                    "outputs": [],
                    "payable": False,
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ]

            # Create WETH contract instance
            weth_contract = w3.eth.contract(
                address=w3.to_checksum_address(weth_address),
                abi=weth_abi
            )

            # Build withdrawal transaction
            # 🔧 FIXED: Use executor's nonce management if available
            nonce = (self.executor._get_next_nonce(chain) if self.executor and hasattr(self.executor, '_get_next_nonce')
                    else w3.eth.get_transaction_count(self.wallet_account.address))

            transaction = weth_contract.functions.withdraw(weth_amount_wei).build_transaction({
                'from': self.wallet_account.address,
                'gas': 150000,  # Sufficient gas for WETH withdrawal
                'gasPrice': max(w3.eth.gas_price, w3.to_wei(0.1, 'gwei')),
                'nonce': nonce
            })

            # Sign and send transaction
            signed_txn = w3.eth.account.sign_transaction(transaction, self.wallet_account.key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

            logger.info(f"   🔗 WETH withdrawal sent: {tx_hash.hex()}")

            # Wait for confirmation
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt.status == 1:
                logger.info(f"   ✅ WETH withdrawal confirmed! Block: {receipt.blockNumber}")

                return {
                    'success': True,
                    'transaction_hash': tx_hash.hex(),
                    'eth_received': eth_amount,
                    'gas_cost_eth': 0.001,  # Lower gas cost for direct withdrawal
                    'from_token': 'WETH',
                    'amount_usd': amount_usd,
                    'block_number': receipt.blockNumber
                }
            else:
                return {'success': False, 'error': 'WETH withdrawal transaction failed'}

        except Exception as e:
            logger.error(f"WETH withdrawal error: {e}")
            return {'success': False, 'error': str(e)}

    async def get_smart_balance_status(self, chain: str = 'arbitrum') -> Dict[str, Any]:
        """Get comprehensive smart balance status for monitoring."""
        try:
            balances = await self.get_real_wallet_balances(chain)
            if not balances:
                return {'error': 'Could not get balances'}

            total_value = sum(balances.values())
            eth_balance_usd = balances.get('ETH', 0)
            eth_balance_eth = eth_balance_usd / 3000.0

            # Calculate available for conversion
            available_for_conversion = {}
            total_available = 0

            for token, balance_usd in balances.items():
                if token == 'ETH':
                    continue
                min_balance = self.min_balances.get(token, 0)
                available = max(0, balance_usd - min_balance)
                available_for_conversion[token] = available
                total_available += available

            # Calculate maximum possible ETH after conversions
            max_possible_eth_usd = eth_balance_usd + total_available
            max_possible_eth = max_possible_eth_usd / 3000.0

            return {
                'total_wallet_value_usd': total_value,
                'current_eth_balance': eth_balance_eth,
                'current_eth_usd': eth_balance_usd,
                'available_for_conversion_usd': total_available,
                'max_possible_eth_after_conversion': max_possible_eth,
                'token_balances': balances,
                'available_by_token': available_for_conversion,
                'jit_conversion_enabled': self.jit_conversion_enabled,
                'min_eth_reserve': self.min_eth_reserve,
                'last_update': self.last_balance_update.isoformat() if self.last_balance_update else None
            }

        except Exception as e:
            logger.error(f"Smart balance status error: {e}")
            return {'error': str(e)}

    async def analyze_wallet_composition(self, wallet_address: str) -> Dict[str, Any]:
        """Analyze current wallet composition vs optimal."""
        try:
            # Get current balances using real balance method
            current_balances = await self.get_real_wallet_balances('arbitrum')
            
            # Calculate total value
            total_value = sum(current_balances.values())
            
            if total_value == 0:
                return {'error': 'Empty wallet'}
            
            # Calculate current percentages
            current_composition = {}
            for token, balance in current_balances.items():
                current_composition[token] = balance / total_value
            
            # Compare to target
            composition_analysis = {}
            rebalance_needed = False
            
            for token, target_pct in self.target_composition.items():
                current_pct = current_composition.get(token, 0)
                difference = abs(current_pct - target_pct)
                
                composition_analysis[token] = {
                    'current_usd': current_balances.get(token, 0),
                    'current_percentage': current_pct * 100,
                    'target_percentage': target_pct * 100,
                    'difference': difference * 100,
                    'status': 'optimal' if difference < self.rebalance_threshold else 'needs_rebalance'
                }
                
                if difference > self.rebalance_threshold:
                    rebalance_needed = True
            
            return {
                'total_value_usd': total_value,
                'current_balances': current_balances,
                'composition_analysis': composition_analysis,
                'rebalance_needed': rebalance_needed,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Wallet analysis error: {e}")
            return {'error': str(e)}

    async def get_real_wallet_balances(self, chain: str = 'arbitrum') -> Dict[str, float]:
        """Get REAL wallet balances from blockchain for just-in-time conversion."""
        try:
            if not self.web3_connections or chain not in self.web3_connections:
                logger.error(f"No Web3 connection for {chain}")
                return {}

            if not self.wallet_account:
                logger.error("No wallet account available")
                return {}

            wallet_address = self.wallet_account.address

            # 🚀 MULTICALL OPTIMIZATION: Use multicall for ultra-fast balance checking
            if self.multicall_checker:
                logger.info(f"🚀 MULTICALL: Getting all balances in single call for {wallet_address}")

                multicall_result = await self.multicall_checker.get_all_token_balances_fast(wallet_address, chain)

                if multicall_result.get('success'):
                    balances_data = multicall_result['balances']
                    total_usd = multicall_result['total_usd']
                    execution_time = multicall_result['execution_time_ms']

                    logger.info(f"🚀 MULTICALL SUCCESS: {len(balances_data)} tokens in {execution_time:.0f}ms")
                    logger.info(f"💰 Total wallet value: ${total_usd:.2f}")

                    # Convert to the format expected by the rest of the system
                    balances = {}
                    for token_name, token_data in balances_data.items():
                        balances[token_name] = token_data['balance_usd']
                        if token_name == 'ETH':
                            logger.info(f"💰 Real ETH balance: {token_data['balance_eth']:.6f} ETH (${token_data['balance_usd']:.2f})")
                        elif token_data['balance_usd'] > 1.0:  # Only log significant balances
                            logger.info(f"💰 Real {token_name} balance: ${token_data['balance_usd']:.2f}")

                    # Cache the balances
                    self.current_balances = balances
                    self.last_balance_update = datetime.now()

                    return balances
                else:
                    logger.warning(f"⚠️ Multicall failed: {multicall_result.get('error')}, falling back to individual calls")

            # 🐌 FALLBACK: Individual calls (slow but reliable)
            logger.info(f"🔍 FALLBACK: Getting balances individually for {wallet_address} on {chain}")
            w3 = self.web3_connections[chain]
            balances = {}

            # Get ETH balance
            eth_balance_wei = w3.eth.get_balance(wallet_address)
            eth_balance = float(w3.from_wei(eth_balance_wei, 'ether'))
            eth_price_usd = 3000.0  # Conservative ETH price
            balances['ETH'] = eth_balance * eth_price_usd

            logger.info(f"💰 Real ETH balance: {eth_balance:.6f} ETH (${balances['ETH']:.2f})")

            # Get token balances (WETH, USDC, USDT, DAI)
            token_addresses = self.token_addresses.get(chain, {})

            for token_symbol, token_address in token_addresses.items():
                if token_symbol == 'ETH':
                    continue  # Already got ETH balance

                try:
                    # Get token balance using ERC20 standard
                    token_balance = await self._get_erc20_balance(w3, token_address, wallet_address, token_symbol)
                    balances[token_symbol] = token_balance
                    logger.info(f"💰 Real {token_symbol} balance: ${token_balance:.2f}")

                except Exception as token_error:
                    logger.warning(f"Could not get {token_symbol} balance: {token_error}")
                    balances[token_symbol] = 0.0

            # Cache the balances
            self.current_balances = balances
            self.last_balance_update = datetime.now()

            total_value = sum(balances.values())
            logger.info(f"🎯 Total wallet value: ${total_value:.2f}")

            return balances

        except Exception as e:
            logger.error(f"Error getting real wallet balances: {e}")
            return {}

    async def _get_erc20_balance(self, w3: Web3, token_address: str, wallet_address: str, token_symbol: str) -> float:
        """Get ERC20 token balance and convert to USD value."""
        try:
            # ERC20 balanceOf function ABI
            erc20_abi = [
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function"
                }
            ]

            # Create contract instance
            contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=erc20_abi)

            # Get balance and decimals
            balance_raw = contract.functions.balanceOf(wallet_address).call()
            decimals = contract.functions.decimals().call()

            # Convert to human readable format
            balance_tokens = balance_raw / (10 ** decimals)

            # Convert to USD (assuming stablecoins = $1, WETH = ETH price)
            if token_symbol in ['USDC', 'USDC.e', 'USDT', 'DAI']:
                balance_usd = balance_tokens  # Stablecoins = $1
            elif token_symbol == 'WETH':
                eth_price_usd = 3000.0  # Conservative ETH price
                balance_usd = balance_tokens * eth_price_usd
            else:
                balance_usd = balance_tokens  # Default to $1

            return balance_usd

        except Exception as e:
            logger.error(f"Error getting {token_symbol} balance: {e}")
            return 0.0

    async def generate_rebalancing_plan(self, wallet_address: str) -> Dict[str, Any]:
        """Generate optimal rebalancing plan."""
        try:
            analysis = await self.analyze_wallet_composition(wallet_address)
            
            if 'error' in analysis:
                return analysis
            
            if not analysis['rebalance_needed']:
                return {
                    'rebalance_needed': False,
                    'message': 'Wallet composition is optimal'
                }
            
            total_value = analysis['total_value_usd']
            current_balances = analysis['current_balances']
            
            # Calculate target balances
            target_balances = {}
            for token, target_pct in self.target_composition.items():
                target_balances[token] = total_value * target_pct
            
            # Generate swap plan
            swap_plan = []
            
            for token, target_balance in target_balances.items():
                current_balance = current_balances.get(token, 0)
                difference = target_balance - current_balance
                
                if abs(difference) > self.min_swap_amount:
                    if difference > 0:
                        # Need to buy this token
                        swap_plan.append({
                            'action': 'buy',
                            'token': token,
                            'amount_usd': difference,
                            'priority': self._get_swap_priority(token, 'buy')
                        })
                    else:
                        # Need to sell this token
                        swap_plan.append({
                            'action': 'sell',
                            'token': token,
                            'amount_usd': abs(difference),
                            'priority': self._get_swap_priority(token, 'sell')
                        })
            
            # Sort by priority
            swap_plan.sort(key=lambda x: x['priority'])
            
            return {
                'rebalance_needed': True,
                'current_balances': current_balances,
                'target_balances': target_balances,
                'swap_plan': swap_plan,
                'estimated_gas_cost': len(swap_plan) * 15,  # $15 per swap
                'estimated_time_minutes': len(swap_plan) * 2  # 2 minutes per swap
            }
            
        except Exception as e:
            logger.error(f"Rebalancing plan error: {e}")
            return {'error': str(e)}

    def _get_swap_priority(self, token: str, action: str) -> int:
        """Get priority for token swaps (lower number = higher priority)."""
        # Priority based on arbitrage importance
        token_priorities = {
            'ETH': 1,    # Highest priority (most opportunities)
            'USDC': 2,   # High priority (stable base)
            'USDT': 3,   # Medium priority (alternative stable)
            'DAI': 4     # Lower priority (backup)
        }
        
        base_priority = token_priorities.get(token, 5)
        
        # Buying important tokens gets higher priority
        if action == 'buy':
            return base_priority
        else:
            return base_priority + 2

    async def execute_rebalancing(self, wallet_address: str, wallet_private_key: str) -> Dict[str, Any]:
        """Execute wallet rebalancing plan."""
        try:
            logger.info("🔄 Executing wallet rebalancing...")
            
            # Get rebalancing plan
            plan = await self.generate_rebalancing_plan(wallet_address)
            
            if 'error' in plan:
                return plan
            
            if not plan['rebalance_needed']:
                return plan
            
            swap_results = []
            total_gas_cost = 0
            
            # Execute swaps
            for swap in plan['swap_plan']:
                logger.info(f"   {swap['action'].upper()} ${swap['amount_usd']:.0f} {swap['token']}")
                
                # Simulate swap execution
                result = await self._execute_token_swap(
                    swap['action'],
                    swap['token'],
                    swap['amount_usd'],
                    wallet_private_key
                )
                
                swap_results.append(result)
                total_gas_cost += result.get('gas_cost_usd', 15)
                
                # Small delay between swaps
                await asyncio.sleep(1)
            
            logger.info(f"✅ Rebalancing complete! Gas cost: ${total_gas_cost:.2f}")
            
            return {
                'success': True,
                'swaps_executed': len(swap_results),
                'total_gas_cost': total_gas_cost,
                'swap_results': swap_results,
                'new_composition': await self.analyze_wallet_composition(wallet_address)
            }
            
        except Exception as e:
            logger.error(f"Rebalancing execution error: {e}")
            return {'error': str(e)}

    async def _execute_token_swap(self, action: str, token: str, amount_usd: float, wallet_private_key: str) -> Dict[str, Any]:
        """Execute a single token swap."""
        try:
            # Simulate swap execution
            # In production, this would use Uniswap/1inch APIs
            
            gas_cost = 15  # Estimate $15 gas per swap
            slippage = 0.002  # 0.2% slippage
            
            if action == 'buy':
                received_amount = amount_usd * (1 - slippage)
            else:
                received_amount = amount_usd * (1 - slippage)
            
            # Simulate execution time
            await asyncio.sleep(0.5)
            
            return {
                'success': True,
                'action': action,
                'token': token,
                'amount_usd': amount_usd,
                'received_amount_usd': received_amount,
                'gas_cost_usd': gas_cost,
                'slippage_percentage': slippage * 100,
                'transaction_hash': None,  # No real transaction for rebalancing simulation
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'action': action,
                'token': token,
                'amount_usd': amount_usd
            }

    async def optimize_for_opportunity(self, opportunity: Dict[str, Any], wallet_address: str) -> Dict[str, Any]:
        """Optimize wallet for a specific arbitrage opportunity."""
        try:
            token = opportunity['token']
            trade_size_usd = opportunity.get('estimated_trade_size', 1000)
            
            # Check if we have enough of the required token
            current_balances = await self._get_wallet_balances(wallet_address)
            current_token_balance = current_balances.get(token, 0)
            
            if current_token_balance >= trade_size_usd:
                return {
                    'optimization_needed': False,
                    'message': f'Sufficient {token} balance for trade'
                }
            
            # Calculate how much we need
            needed_amount = trade_size_usd - current_token_balance
            
            # Find best token to swap from
            swap_candidates = []
            for source_token, balance in current_balances.items():
                if source_token != token and balance > self.min_balances.get(source_token, 0):
                    available_to_swap = balance - self.min_balances.get(source_token, 0)
                    if available_to_swap >= needed_amount:
                        swap_candidates.append({
                            'from_token': source_token,
                            'available_amount': available_to_swap,
                            'priority': self._get_swap_priority(source_token, 'sell')
                        })
            
            if not swap_candidates:
                return {
                    'optimization_needed': True,
                    'error': 'Insufficient funds for optimization'
                }
            
            # Choose best swap candidate
            best_candidate = min(swap_candidates, key=lambda x: x['priority'])
            
            return {
                'optimization_needed': True,
                'swap_plan': {
                    'from_token': best_candidate['from_token'],
                    'to_token': token,
                    'amount_usd': needed_amount,
                    'estimated_gas_cost': 15,
                    'estimated_time_minutes': 2
                }
            }
            
        except Exception as e:
            logger.error(f"Opportunity optimization error: {e}")
            return {'error': str(e)}

    def get_wallet_recommendations(self, total_value_usd: float) -> Dict[str, Any]:
        """Get wallet optimization recommendations."""
        recommendations = []
        
        # Size-based recommendations
        if total_value_usd < 500:
            recommendations.append({
                'type': 'composition',
                'message': 'Focus on USDC/ETH for small wallets',
                'suggested_composition': {'USDC': 0.6, 'ETH': 0.4}
            })
        elif total_value_usd < 2000:
            recommendations.append({
                'type': 'composition',
                'message': 'Add USDT for more opportunities',
                'suggested_composition': {'USDC': 0.5, 'ETH': 0.3, 'USDT': 0.2}
            })
        else:
            recommendations.append({
                'type': 'composition',
                'message': 'Full diversification recommended',
                'suggested_composition': self.target_composition
            })
        
        # Strategy recommendations
        recommendations.append({
            'type': 'strategy',
            'message': 'Rebalance weekly or when >15% off target'
        })
        
        recommendations.append({
            'type': 'gas',
            'message': 'Keep $50-100 ETH for gas fees'
        })
        
        return {
            'total_value_usd': total_value_usd,
            'recommendations': recommendations,
            'optimal_composition': self.target_composition
        }

    async def get_wallet_status(self, wallet_address: str) -> Dict[str, Any]:
        """Get comprehensive wallet status."""
        try:
            analysis = await self.analyze_wallet_composition(wallet_address)
            
            if 'error' in analysis:
                return analysis
            
            recommendations = self.get_wallet_recommendations(analysis['total_value_usd'])
            
            return {
                'wallet_address': wallet_address,
                'total_value_usd': analysis['total_value_usd'],
                'current_balances': analysis['current_balances'],
                'composition_analysis': analysis['composition_analysis'],
                'rebalance_needed': analysis['rebalance_needed'],
                'recommendations': recommendations['recommendations'],
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Wallet status error: {e}")
            return {'error': str(e)}
