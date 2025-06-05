#!/usr/bin/env python3
"""
Deploy Flashloan Contract
Deploys the FlashloanArbitrage contract to Arbitrum network.
"""

import os
import json
import time
from typing import Dict, List, Any
from web3 import Web3
from eth_account import Account
from solcx import compile_source, install_solc
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class FlashloanContractDeployer:
    """Deploy flashloan arbitrage contract to blockchain."""
    
    def __init__(self):
        # Get environment variables
        self.private_key = os.getenv('PRIVATE_KEY')
        self.alchemy_api_key = os.getenv('ALCHEMY_API_KEY')

        if not self.private_key or not self.alchemy_api_key:
            raise ValueError("Missing PRIVATE_KEY or ALCHEMY_API_KEY environment variables")
        
        # Setup Web3 connection to Arbitrum
        self.w3 = Web3(Web3.HTTPProvider(f"https://arb-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"))
        self.account = Account.from_key(self.private_key)
        
        # Aave V3 AddressProvider on Arbitrum
        self.aave_address_provider = '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb'
        
        logger.info("🔥 Flashloan Contract Deployer initialized")
        logger.info(f"   📍 Network: Arbitrum One (Chain ID: {self.w3.eth.chain_id})")
        logger.info(f"   💰 Deployer: {self.account.address}")
    
    def compile_contract(self) -> Dict:
        """Compile the flashloan contract."""
        try:
            logger.info("🔧 COMPILING FLASHLOAN CONTRACT")
            logger.info("=" * 40)
            
            # Install Solidity compiler if needed
            try:
                install_solc('0.8.19')
            except Exception:
                pass  # Already installed
            
            # Read contract source
            with open('contracts/ProductionFlashloan.sol', 'r') as file:
                contract_source = file.read()
            
            # Compile contract
            logger.info("   🔨 Compiling Solidity contract...")
            compiled_sol = compile_source(
                contract_source,
                output_values=['abi', 'bin'],
                solc_version='0.8.19'
            )
            
            # Get contract interface
            contract_id, contract_interface = compiled_sol.popitem()
            
            logger.info("   ✅ Contract compiled successfully")
            logger.info(f"   📊 Bytecode size: {len(contract_interface['bin'])} characters")
            
            return contract_interface
            
        except Exception as e:
            logger.error(f"❌ Contract compilation failed: {e}")
            raise
    
    def estimate_deployment_cost(self, contract_interface: Dict) -> Dict:
        """Estimate deployment gas and cost."""
        try:
            logger.info("💰 ESTIMATING DEPLOYMENT COST")
            logger.info("=" * 35)
            
            # Create contract instance
            contract = self.w3.eth.contract(
                abi=contract_interface['abi'],
                bytecode=contract_interface['bin']
            )
            
            # Estimate gas for deployment
            constructor_args = [self.aave_address_provider]
            gas_estimate = contract.constructor(*constructor_args).estimate_gas()
            
            # Get current gas price
            gas_price = self.w3.eth.gas_price
            
            # Calculate costs
            deployment_cost_wei = gas_estimate * gas_price
            deployment_cost_eth = self.w3.from_wei(deployment_cost_wei, 'ether')
            deployment_cost_usd = float(deployment_cost_eth) * 3000  # Assume $3000 ETH
            
            logger.info(f"   ⛽ Estimated gas: {gas_estimate:,}")
            logger.info(f"   💸 Gas price: {self.w3.from_wei(gas_price, 'gwei'):.1f} gwei")
            logger.info(f"   💰 Deployment cost: {deployment_cost_eth:.6f} ETH (${deployment_cost_usd:.2f})")
            
            return {
                'gas_estimate': gas_estimate,
                'gas_price': gas_price,
                'cost_eth': float(deployment_cost_eth),
                'cost_usd': deployment_cost_usd
            }
            
        except Exception as e:
            logger.error(f"❌ Cost estimation failed: {e}")
            raise
    
    def deploy_contract(self, contract_interface: Dict) -> Dict:
        """Deploy the flashloan contract."""
        try:
            logger.info("🚀 DEPLOYING FLASHLOAN CONTRACT")
            logger.info("=" * 40)
            
            # Check wallet balance
            balance_wei = self.w3.eth.get_balance(self.account.address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            
            logger.info(f"   💰 Deployer balance: {balance_eth:.6f} ETH")
            
            # Create contract instance
            contract = self.w3.eth.contract(
                abi=contract_interface['abi'],
                bytecode=contract_interface['bin']
            )
            
            # Build deployment transaction
            constructor_args = [self.aave_address_provider]  # Production contract needs Aave address provider
            
            transaction = contract.constructor(*constructor_args).build_transaction({
                'from': self.account.address,
                'gas': 2500000,  # High gas limit for deployment
                'gasPrice': int(self.w3.eth.gas_price * 1.2),  # 20% higher gas price
                'nonce': self.w3.eth.get_transaction_count(self.account.address)
            })
            
            logger.info(f"   📊 Transaction details:")
            logger.info(f"      Gas limit: {transaction['gas']:,}")
            logger.info(f"      Gas price: {self.w3.from_wei(transaction['gasPrice'], 'gwei'):.1f} gwei")
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=self.private_key)
            
            logger.info("   📡 Sending deployment transaction...")
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"   ✅ Deployment transaction sent: {tx_hash_hex}")
            logger.info(f"   🔗 Arbiscan: https://arbiscan.io/tx/{tx_hash_hex}")
            
            # Wait for confirmation
            logger.info("   ⏳ Waiting for deployment confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)  # 5 minutes
            
            if receipt.status == 1:
                contract_address = receipt.contractAddress
                
                logger.info("🎉 CONTRACT DEPLOYMENT SUCCESSFUL!")
                logger.info("=" * 45)
                logger.info(f"   📍 Contract Address: {contract_address}")
                logger.info(f"   🔗 Arbiscan: https://arbiscan.io/address/{contract_address}")
                logger.info(f"   ⛽ Gas Used: {receipt.gasUsed:,}")
                logger.info(f"   💰 Deployment Cost: {self.w3.from_wei(receipt.gasUsed * transaction['gasPrice'], 'ether'):.6f} ETH")
                
                return {
                    'success': True,
                    'contract_address': contract_address,
                    'transaction_hash': tx_hash_hex,
                    'gas_used': receipt.gasUsed,
                    'deployment_cost_eth': float(self.w3.from_wei(receipt.gasUsed * transaction['gasPrice'], 'ether')),
                    'abi': contract_interface['abi']
                }
            else:
                logger.error(f"❌ Contract deployment failed: {tx_hash_hex}")
                return {'success': False, 'error': f'Deployment transaction failed: {tx_hash_hex}'}
            
        except Exception as e:
            logger.error(f"❌ Contract deployment error: {e}")
            return {'success': False, 'error': str(e)}
    
    def save_deployment_info(self, deployment_result: Dict):
        """Save deployment information to file."""
        try:
            if not deployment_result.get('success'):
                return
            
            deployment_info = {
                'network': 'arbitrum',
                'chain_id': self.w3.eth.chain_id,
                'contract_address': deployment_result['contract_address'],
                'transaction_hash': deployment_result['transaction_hash'],
                'deployer_address': self.account.address,
                'deployment_timestamp': int(time.time()),
                'gas_used': deployment_result['gas_used'],
                'deployment_cost_eth': deployment_result['deployment_cost_eth'],
                'abi': deployment_result['abi'],
                'aave_address_provider': self.aave_address_provider
            }
            
            # Save to JSON file
            with open('flashloan_deployment.json', 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            logger.info("💾 Deployment info saved to flashloan_deployment.json")
            
        except Exception as e:
            logger.error(f"❌ Failed to save deployment info: {e}")
    
    def verify_deployment(self, contract_address: str, abi: List) -> bool:
        """Verify the deployed contract."""
        try:
            logger.info("🔍 VERIFYING DEPLOYMENT")
            logger.info("=" * 30)
            
            # Create contract instance
            contract = self.w3.eth.contract(address=contract_address, abi=abi)
            
            # Test contract functions
            owner = contract.functions.owner().call()
            min_profit_bps = contract.functions.minProfitBps().call()
            
            logger.info(f"   ✅ Contract owner: {owner}")
            logger.info(f"   ✅ Min profit BPS: {min_profit_bps}")
            logger.info(f"   ✅ Owner matches deployer: {owner.lower() == self.account.address.lower()}")
            
            return owner.lower() == self.account.address.lower()
            
        except Exception as e:
            logger.error(f"❌ Contract verification failed: {e}")
            return False

def main():
    """Main deployment function."""
    try:
        logger.info("🔥 FLASHLOAN CONTRACT DEPLOYMENT")
        logger.info("=" * 50)
        
        # Initialize deployer
        deployer = FlashloanContractDeployer()
        
        # Compile contract
        contract_interface = deployer.compile_contract()
        
        # Estimate costs
        cost_info = deployer.estimate_deployment_cost(contract_interface)
        
        # Ask for confirmation
        logger.info("\n🤔 DEPLOYMENT CONFIRMATION")
        logger.info("=" * 30)
        logger.info(f"Ready to deploy flashloan contract for ${cost_info['cost_usd']:.2f}")
        
        # For automated deployment, skip confirmation
        # In production, you might want to add input() here
        
        # Deploy contract
        deployment_result = deployer.deploy_contract(contract_interface)
        
        if deployment_result['success']:
            # Save deployment info
            deployer.save_deployment_info(deployment_result)
            
            # Verify deployment
            is_verified = deployer.verify_deployment(
                deployment_result['contract_address'],
                deployment_result['abi']
            )
            
            if is_verified:
                logger.info("🎉 DEPLOYMENT COMPLETE AND VERIFIED!")
                logger.info("✅ Ready to integrate with arbitrage bot!")
            else:
                logger.warning("⚠️ Deployment successful but verification failed")
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")

if __name__ == "__main__":
    main()
