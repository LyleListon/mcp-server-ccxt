"""
Triangular Flashloan Integration
Fixes the IDENTICAL_ADDRESSES error by using proper triangular arbitrage contract
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional
from web3 import Web3
from eth_account import Account
import logging

logger = logging.getLogger(__name__)

class TriangularFlashloanIntegration:
    """Integration for triangular flashloan arbitrage contract."""
    
    def __init__(self, wallet_account, web3_connections: Dict[str, Web3]):
        self.wallet_account = wallet_account
        self.web3_connections = web3_connections
        
        # Load contract deployment info
        self.contract_info = self._load_contract_info()
        
        # DEX router addresses (Arbitrum)
        self.dex_routers = {
            'sushiswap': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
            'camelot': '0xc873fEcbd354f5A56E00E710B90EF4201db2448d',
            'uniswap_v3': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
            'traderjoe': '0xb4315e873dBcf96Ffd0acd8EA43f689D8c20fB30'
        }
        
        # Token addresses (Arbitrum)
        self.token_addresses = {
            'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
            'USDC': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
            'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
            'USDC.e': '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8'
        }
    
    def _load_contract_info(self) -> Optional[Dict[str, Any]]:
        """Load triangular flashloan contract deployment info."""
        try:
            deployment_file = 'triangular_flashloan_deployment.json'
            if os.path.exists(deployment_file):
                with open(deployment_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Triangular flashloan deployment file not found: {deployment_file}")
                return None
        except Exception as e:
            logger.error(f"Error loading contract info: {e}")
            return None
    
    async def execute_triangular_arbitrage(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute triangular arbitrage using the proper contract."""
        try:
            logger.info("🔺 EXECUTING TRIANGULAR FLASHLOAN ARBITRAGE")
            logger.info("=" * 50)
            
            if not self.contract_info:
                return {'success': False, 'error': 'Triangular contract not deployed'}
            
            # Extract triangular path from opportunity
            path = opportunity.get('path', [])
            dexes = opportunity.get('dexes', [])
            chain = opportunity.get('source_chain', 'arbitrum')
            
            if len(path) != 4 or len(dexes) != 3:
                return {'success': False, 'error': f'Invalid triangular path: {path} with DEXes: {dexes}'}
            
            # Validate triangular path (start == end)
            if path[0] != path[3]:
                return {'success': False, 'error': f'Triangular path must start and end with same token: {path}'}
            
            start_token = path[0]
            middle_token = path[1] 
            end_token = path[2]
            
            logger.info(f"🎯 Triangular Path: {start_token} → {middle_token} → {end_token} → {start_token}")
            logger.info(f"🏪 DEXes: {dexes[0]} → {dexes[1]} → {dexes[2]}")
            
            # Get token addresses
            start_token_address = self.token_addresses.get(start_token)
            middle_token_address = self.token_addresses.get(middle_token)
            end_token_address = self.token_addresses.get(end_token)
            
            if not all([start_token_address, middle_token_address, end_token_address]):
                return {'success': False, 'error': f'Token addresses not found for path: {path}'}
            
            # Get DEX router addresses
            dex_a_address = self.dex_routers.get(dexes[0])
            dex_b_address = self.dex_routers.get(dexes[1])
            dex_c_address = self.dex_routers.get(dexes[2])
            
            if not all([dex_a_address, dex_b_address, dex_c_address]):
                return {'success': False, 'error': f'DEX router addresses not found for: {dexes}'}
            
            logger.info(f"🪙 Start Token: {start_token} ({start_token_address})")
            logger.info(f"🪙 Middle Token: {middle_token} ({middle_token_address})")
            logger.info(f"🪙 End Token: {end_token} ({end_token_address})")
            logger.info(f"🏪 DEX A: {dexes[0]} ({dex_a_address})")
            logger.info(f"🏪 DEX B: {dexes[1]} ({dex_b_address})")
            logger.info(f"🏪 DEX C: {dexes[2]} ({dex_c_address})")
            
            # Calculate flashloan amount
            profit_usd = opportunity.get('estimated_profit_usd', 0)
            flashloan_amount_usd = max(100, profit_usd * 10)  # 10x profit as capital
            
            # Convert to token amount (simplified)
            if start_token == 'WETH':
                flashloan_amount = int(flashloan_amount_usd / 3000 * 1e18)  # ETH price ~$3000
            else:  # USDC/USDT
                flashloan_amount = int(flashloan_amount_usd * 1e6)  # 6 decimals
            
            logger.info(f"💰 Flashloan Amount: {flashloan_amount} ({start_token})")
            logger.info(f"💵 USD Value: ${flashloan_amount_usd:.2f}")
            
            # Execute triangular flashloan
            w3 = self.web3_connections.get(chain)
            if not w3:
                return {'success': False, 'error': f'No web3 connection for chain: {chain}'}
            
            result = await self._execute_triangular_flashloan_transaction(
                w3, start_token_address, middle_token_address, end_token_address,
                flashloan_amount, dex_a_address, dex_b_address, dex_c_address
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Triangular arbitrage error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _execute_triangular_flashloan_transaction(
        self, w3: Web3, start_token: str, middle_token: str, end_token: str,
        amount: int, dex_a: str, dex_b: str, dex_c: str
    ) -> Dict[str, Any]:
        """Execute the triangular flashloan transaction."""
        try:
            logger.info("🚀 Building triangular flashloan transaction...")
            
            # Create contract instance
            contract = w3.eth.contract(
                address=self.contract_info['contract_address'],
                abi=self.contract_info['abi']
            )
            
            logger.info(f"📍 Contract Address: {self.contract_info['contract_address']}")
            logger.info(f"🔧 Contract Version: {self.contract_info['contract_version']}")
            
            # Get current gas price
            gas_price = w3.eth.gas_price
            priority_gas_price = int(gas_price * 1.5)  # 50% higher for MEV protection
            
            # Encode arbitrage data to reduce stack depth
            arbitrage_data = w3.codec.encode(
                ['address', 'address', 'address', 'address', 'address'],
                [middle_token, end_token, dex_a, dex_b, dex_c]
            )

            # Build transaction
            transaction = contract.functions.executeTriangularArbitrage(
                start_token,    # startToken
                amount,         # amount
                arbitrage_data  # arbitrageData (encoded)
            ).build_transaction({
                'from': self.wallet_account.address,
                'gas': 1500000,  # High gas limit for triangular arbitrage
                'gasPrice': priority_gas_price,
                'nonce': w3.eth.get_transaction_count(self.wallet_account.address)
            })
            
            logger.info(f"⛽ Gas Price: {w3.from_wei(priority_gas_price, 'gwei'):.2f} Gwei")
            logger.info(f"💸 Estimated Cost: {w3.from_wei(transaction['gas'] * priority_gas_price, 'ether'):.6f} ETH")
            
            # Sign transaction
            signed_txn = w3.eth.account.sign_transaction(transaction, self.wallet_account.key)
            
            # Send transaction
            logger.info("📤 Sending triangular arbitrage transaction...")
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"🔗 Transaction Hash: {tx_hash.hex()}")
            logger.info(f"🔍 Arbiscan: https://arbiscan.io/tx/{tx_hash.hex()}")
            logger.info("⏳ Waiting for confirmation...")
            
            # Wait for transaction receipt
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if tx_receipt.status == 1:
                logger.info("✅ TRIANGULAR ARBITRAGE SUCCESS!")
                
                # Calculate actual cost
                actual_cost = tx_receipt.gasUsed * priority_gas_price
                actual_cost_eth = w3.from_wei(actual_cost, 'ether')
                actual_cost_usd = actual_cost_eth * 3000  # ETH price ~$3000
                
                logger.info(f"⛽ Gas Used: {tx_receipt.gasUsed:,}")
                logger.info(f"💸 Actual Cost: {actual_cost_eth:.6f} ETH (${actual_cost_usd:.2f})")
                
                # Parse events to get profit
                profit_usd = 0
                try:
                    # Decode events from transaction receipt
                    events = contract.events.TriangularArbitrageExecuted().process_receipt(tx_receipt)
                    if events:
                        event = events[0]
                        profit_tokens = event['args']['profit']
                        # Convert profit to USD (simplified)
                        if start_token == self.token_addresses['WETH']:
                            profit_usd = (profit_tokens / 1e18) * 3000  # ETH price
                        else:
                            profit_usd = profit_tokens / 1e6  # USDC/USDT
                        
                        logger.info(f"💰 Profit: {profit_tokens} tokens (${profit_usd:.2f})")
                except Exception as e:
                    logger.warning(f"Could not parse profit from events: {e}")
                
                net_profit = profit_usd - actual_cost_usd
                logger.info(f"🎯 Net Profit: ${net_profit:.2f}")
                
                return {
                    'success': True,
                    'transaction_hash': tx_hash.hex(),
                    'gas_used': tx_receipt.gasUsed,
                    'gas_cost_usd': actual_cost_usd,
                    'profit_usd': profit_usd,
                    'net_profit': net_profit,
                    'contract_address': self.contract_info['contract_address']
                }
                
            else:
                logger.error("❌ TRIANGULAR ARBITRAGE FAILED!")
                logger.error(f"Transaction receipt: {tx_receipt}")
                return {
                    'success': False,
                    'error': 'Transaction failed',
                    'transaction_hash': tx_hash.hex(),
                    'gas_used': tx_receipt.gasUsed if tx_receipt else 0
                }
                
        except Exception as e:
            logger.error(f"❌ Transaction execution error: {e}")
            return {'success': False, 'error': str(e)}
