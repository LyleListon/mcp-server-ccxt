"""
Flashloan Integration Module
Integrates the deployed flashloan contract with the arbitrage bot.
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional
from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)

class FlashloanIntegration:
    """Integration layer between arbitrage bot and flashloan contract."""
    
    def __init__(self, wallet_account: Account, web3_connections: Dict[str, Web3]):
        self.wallet_account = wallet_account
        self.web3_connections = web3_connections
        
        # Flashloan contract addresses (to be deployed)
        self.flashloan_contracts = {
            'arbitrum': None,  # Will be set after deployment
            'ethereum': None,
            'polygon': None
        }
        
        # Aave V3 Pool addresses
        self.aave_pools = {
            'arbitrum': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
            'ethereum': '0x87870Bce3F2c6D9b75F794c8E8e8e8e8e8e8e8e8',  # Example
            'polygon': '0x794a61358D6845594F94dc1DB02A252b5b4814aD'   # Example
        }
        
        # DEX type mappings for contract
        self.dex_types = {
            'uniswap_v3': 1,
            'sushiswap': 2,
            'curve': 3,
            'camelot': 2,  # Use SushiSwap-compatible interface
            'balancer': 3,  # Use Curve-compatible interface
        }
        
        # Token addresses
        self.token_addresses = {
            'arbitrum': {
                'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
                'USDC': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
                'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
                'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'
            }
        }
        
        # Contract ABI (minimal for flashloan execution)
        self.flashloan_abi = [
            {
                "inputs": [
                    {"name": "asset", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "dexAParams", "type": "bytes"},
                    {"name": "dexBParams", "type": "bytes"}
                ],
                "name": "executeArbitrage",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "asset", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "dexAParams", "type": "bytes"},
                    {"name": "dexBParams", "type": "bytes"}
                ],
                "name": "checkProfitability",
                "outputs": [
                    {"name": "profitable", "type": "bool"},
                    {"name": "estimatedProfit", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        logger.info("🔥 Flashloan Integration initialized")
    
    async def execute_flashloan_arbitrage(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute arbitrage using flashloan contract."""
        try:
            logger.info("🔥 EXECUTING FLASHLOAN ARBITRAGE")
            logger.info("=" * 50)
            
            # Extract opportunity details
            chain = opportunity.get('source_chain', 'arbitrum')
            token = opportunity.get('token', 'WETH')
            buy_dex = opportunity.get('buy_dex', 'sushiswap')
            sell_dex = opportunity.get('sell_dex', 'camelot')
            profit_usd = opportunity.get('estimated_profit_usd', 0)
            
            logger.info(f"🎯 Opportunity: {token} {buy_dex}→{sell_dex}")
            logger.info(f"💰 Expected profit: ${profit_usd:.2f}")
            
            # Check if flashloan contract is deployed
            if not self.flashloan_contracts.get(chain):
                return {
                    'success': False,
                    'error': f'Flashloan contract not deployed on {chain}',
                    'next_steps': ['Deploy flashloan contract', 'Set contract address']
                }
            
            # Get Web3 connection
            if chain not in self.web3_connections:
                return {'success': False, 'error': f'No Web3 connection for {chain}'}
            
            w3 = self.web3_connections[chain]
            
            # Calculate flashloan amount
            flashloan_amount = await self._calculate_flashloan_amount(w3, opportunity)
            
            # Get token address
            token_address = self.token_addresses[chain].get(token)
            if not token_address:
                return {'success': False, 'error': f'Token {token} not supported on {chain}'}
            
            # Prepare DEX parameters
            dex_a_params = await self._prepare_dex_params(buy_dex, token, flashloan_amount, True)
            dex_b_params = await self._prepare_dex_params(sell_dex, token, flashloan_amount, False)
            
            # Execute flashloan
            result = await self._execute_flashloan_transaction(
                w3, chain, token_address, flashloan_amount, dex_a_params, dex_b_params
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Flashloan arbitrage error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _calculate_flashloan_amount(self, w3: Web3, opportunity: Dict[str, Any]) -> int:
        """Calculate optimal flashloan amount."""
        try:
            profit_usd = opportunity.get('estimated_profit_usd', 0)
            
            # Base flashloan amount on expected profit and available liquidity
            if profit_usd >= 10:
                flashloan_eth = 1.0    # 1 ETH for high-profit opportunities
            elif profit_usd >= 5:
                flashloan_eth = 0.5    # 0.5 ETH for medium opportunities
            elif profit_usd >= 1:
                flashloan_eth = 0.2    # 0.2 ETH for small opportunities
            else:
                flashloan_eth = 0.1    # 0.1 ETH for micro opportunities
            
            flashloan_amount = w3.to_wei(flashloan_eth, 'ether')
            
            logger.info(f"💰 Flashloan amount: {flashloan_eth} ETH")
            return flashloan_amount
            
        except Exception as e:
            logger.error(f"❌ Flashloan amount calculation error: {e}")
            return w3.to_wei(0.1, 'ether')  # Default 0.1 ETH
    
    async def _prepare_dex_params(self, dex: str, token: str, amount: int, is_buy: bool) -> bytes:
        """Prepare DEX parameters for flashloan contract."""
        try:
            dex_type = self.dex_types.get(dex, 2)  # Default to SushiSwap-compatible
            
            if dex_type == 1:  # Uniswap V3
                # Prepare Uniswap V3 parameters
                token_in = self.token_addresses['arbitrum']['WETH']
                token_out = self.token_addresses['arbitrum']['USDC']  # Example
                fee = 3000  # 0.3% fee tier
                amount_out_minimum = int(amount * 0.95)  # 5% slippage
                
                trade_data = Web3.solidity_keccak(['address', 'address', 'uint24', 'uint256'], 
                                                [token_in, token_out, fee, amount_out_minimum])
                
            elif dex_type == 2:  # SushiSwap/Camelot
                # Prepare SushiSwap-compatible parameters
                trade_data = Web3.solidity_keccak(['string', 'uint256'], [dex, amount])
                
            else:  # Other DEXes
                trade_data = Web3.solidity_keccak(['string', 'uint256'], [dex, amount])
            
            # Encode parameters for contract
            dex_params = Web3.solidity_keccak(['uint8', 'bytes'], [dex_type, trade_data])
            
            logger.info(f"📊 DEX params prepared for {dex} (type {dex_type})")
            return dex_params
            
        except Exception as e:
            logger.error(f"❌ DEX params preparation error: {e}")
            return b''
    
    async def _execute_flashloan_transaction(self, w3: Web3, chain: str, token_address: str,
                                           amount: int, dex_a_params: bytes, dex_b_params: bytes) -> Dict[str, Any]:
        """Execute the flashloan transaction."""
        try:
            logger.info("🚀 EXECUTING FLASHLOAN TRANSACTION")
            
            # Get flashloan contract
            contract_address = self.flashloan_contracts[chain]
            contract = w3.eth.contract(address=contract_address, abi=self.flashloan_abi)
            
            # Build transaction
            transaction = contract.functions.executeArbitrage(
                token_address,
                amount,
                dex_a_params,
                dex_b_params
            ).build_transaction({
                'from': self.wallet_account.address,
                'gas': 1000000,  # High gas limit for flashloan
                'gasPrice': int(w3.eth.gas_price * 2),  # Priority gas
                'nonce': w3.eth.get_transaction_count(self.wallet_account.address)
            })
            
            # Sign and send transaction
            signed_txn = w3.eth.account.sign_transaction(transaction, private_key=self.wallet_account.key)
            
            logger.info("📡 Sending flashloan transaction...")
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"✅ Flashloan transaction sent: {tx_hash_hex}")
            logger.info(f"🔗 Arbiscan: https://arbiscan.io/tx/{tx_hash_hex}")
            
            # Wait for confirmation
            logger.info("⏳ Waiting for flashloan confirmation...")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if receipt.status == 1:
                logger.info(f"✅ FLASHLOAN ARBITRAGE SUCCESSFUL: {tx_hash_hex}")
                
                # Calculate gas cost
                gas_cost_wei = receipt.gasUsed * transaction['gasPrice']
                gas_cost_eth = float(w3.from_wei(gas_cost_wei, 'ether'))
                gas_cost_usd = gas_cost_eth * 3000.0
                
                return {
                    'success': True,
                    'transaction_hash': tx_hash_hex,
                    'gas_used': receipt.gasUsed,
                    'gas_cost_eth': gas_cost_eth,
                    'gas_cost_usd': gas_cost_usd,
                    'execution_type': 'flashloan',
                    'provider': 'aave_v3'
                }
            else:
                logger.error(f"❌ Flashloan transaction failed: {tx_hash_hex}")
                return {'success': False, 'error': f'Flashloan transaction failed: {tx_hash_hex}'}
            
        except Exception as e:
            logger.error(f"❌ Flashloan transaction error: {e}")
            return {'success': False, 'error': str(e)}
    
    def set_flashloan_contract_address(self, chain: str, address: str):
        """Set the deployed flashloan contract address."""
        self.flashloan_contracts[chain] = Web3.to_checksum_address(address)
        logger.info(f"🔥 Flashloan contract set for {chain}: {address}")
    
    def get_deployment_info(self) -> Dict[str, Any]:
        """Get information needed for contract deployment."""
        return {
            'contract_file': 'contracts/FlashloanArbitrage.sol',
            'constructor_params': {
                'arbitrum': {
                    '_addressProvider': '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb'  # Aave V3 AddressProvider
                }
            },
            'deployment_networks': ['arbitrum'],
            'estimated_gas': 2000000,
            'next_steps': [
                '1. Compile contract with Hardhat/Foundry',
                '2. Deploy to Arbitrum network',
                '3. Set contract address in integration',
                '4. Test with small amounts',
                '5. Scale up for production'
            ]
        }
