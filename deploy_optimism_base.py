#!/usr/bin/env python3
"""
Deploy to Optimism and Base
===========================

Deploy the fixed flashloan contracts to Optimism and Base for multi-chain speed!
"""

import os
import json
import time
from web3 import Web3
from eth_account import Account
from solcx import compile_source, install_solc, set_solc_version

def deploy_to_optimism():
    """Deploy flashloan contract to Optimism."""
    print("🚀 DEPLOYING TO OPTIMISM")
    print("=" * 30)
    
    try:
        # Get environment variables
        private_key = os.getenv('PRIVATE_KEY')
        alchemy_api_key = os.getenv('ALCHEMY_API_KEY')
        
        if not private_key or not alchemy_api_key:
            print("❌ Missing environment variables")
            return None
        
        # Setup Web3 connection to Optimism
        rpc_url = f"https://opt-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        account = Account.from_key(private_key)
        
        print(f"🔗 Connected to Optimism")
        print(f"📍 Deployer: {account.address}")
        print(f"💰 Balance: {w3.from_wei(w3.eth.get_balance(account.address), 'ether'):.6f} ETH")
        
        # Compile contract
        print("🔨 Compiling contract...")
        install_solc('0.8.19')
        set_solc_version('0.8.19')
        
        # Use the existing fixed contract
        with open('contracts/ProductionFlashloan.sol', 'r') as f:
            contract_source = f.read()
        
        compiled_sol = compile_source(contract_source)
        contract_interface = compiled_sol['<stdin>:ProductionFlashloanArbitrage']
        
        print("✅ Contract compiled successfully")
        
        # Optimism addresses
        aave_provider = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb"
        
        print(f"📍 Aave Provider: {aave_provider}")
        
        # Create contract instance
        contract = w3.eth.contract(
            abi=contract_interface['abi'],
            bytecode=contract_interface['bin']
        )
        
        # Build deployment transaction
        constructor_tx = contract.constructor(aave_provider).build_transaction({
            'from': account.address,
            'gas': 4000000,
            'gasPrice': w3.to_wei('0.001', 'gwei'),  # Very low on Optimism
            'nonce': w3.eth.get_transaction_count(account.address)
        })
        
        # Sign and send transaction
        signed_tx = account.sign_transaction(constructor_tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"📤 Transaction sent: {tx_hash.hex()}")
        print("⏳ Waiting for confirmation...")
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            contract_address = receipt.contractAddress
            
            print(f"\n✅ OPTIMISM CONTRACT DEPLOYED!")
            print(f"📍 Contract Address: {contract_address}")
            print(f"🔗 Explorer: https://optimistic.etherscan.io/address/{contract_address}")
            print(f"⛽ Gas Used: {receipt.gasUsed:,}")
            print(f"💰 Cost: {w3.from_wei(receipt.gasUsed * constructor_tx['gasPrice'], 'ether'):.8f} ETH")
            
            # Save deployment info
            deployment_info = {
                'network': 'optimism',
                'chain_id': 10,
                'contract_address': contract_address,
                'transaction_hash': tx_hash.hex(),
                'deployer_address': account.address,
                'deployment_timestamp': int(time.time()),
                'gas_used': receipt.gasUsed,
                'deployment_cost_eth': float(w3.from_wei(receipt.gasUsed * constructor_tx['gasPrice'], 'ether')),
                'abi': contract_interface['abi'],
                'contract_version': 'OPTIMISM_FIXED_v1.0'
            }
            
            with open('optimism_deployment.json', 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            print(f"💾 Deployment saved to optimism_deployment.json")
            
            return deployment_info
            
        else:
            print(f"❌ Deployment failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def deploy_to_base():
    """Deploy flashloan contract to Base."""
    print("\n🚀 DEPLOYING TO BASE")
    print("=" * 25)
    
    try:
        # Get environment variables
        private_key = os.getenv('PRIVATE_KEY')
        alchemy_api_key = os.getenv('ALCHEMY_API_KEY')
        
        if not private_key or not alchemy_api_key:
            print("❌ Missing environment variables")
            return None
        
        # Setup Web3 connection to Base
        rpc_url = f"https://base-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        account = Account.from_key(private_key)
        
        print(f"🔗 Connected to Base")
        print(f"📍 Deployer: {account.address}")
        print(f"💰 Balance: {w3.from_wei(w3.eth.get_balance(account.address), 'ether'):.6f} ETH")
        
        # Use already compiled contract
        print("🔨 Using compiled contract...")
        
        # Use the existing fixed contract
        with open('contracts/ProductionFlashloan.sol', 'r') as f:
            contract_source = f.read()
        
        compiled_sol = compile_source(contract_source)
        contract_interface = compiled_sol['<stdin>:ProductionFlashloanArbitrage']
        
        print("✅ Contract ready")
        
        # Base addresses
        aave_provider = "0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D"
        
        print(f"📍 Aave Provider: {aave_provider}")
        
        # Create contract instance
        contract = w3.eth.contract(
            abi=contract_interface['abi'],
            bytecode=contract_interface['bin']
        )
        
        # Build deployment transaction
        constructor_tx = contract.constructor(aave_provider).build_transaction({
            'from': account.address,
            'gas': 4000000,
            'gasPrice': w3.to_wei('0.001', 'gwei'),  # Very low on Base
            'nonce': w3.eth.get_transaction_count(account.address)
        })
        
        # Sign and send transaction
        signed_tx = account.sign_transaction(constructor_tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"📤 Transaction sent: {tx_hash.hex()}")
        print("⏳ Waiting for confirmation...")
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            contract_address = receipt.contractAddress
            
            print(f"\n✅ BASE CONTRACT DEPLOYED!")
            print(f"📍 Contract Address: {contract_address}")
            print(f"🔗 Explorer: https://basescan.org/address/{contract_address}")
            print(f"⛽ Gas Used: {receipt.gasUsed:,}")
            print(f"💰 Cost: {w3.from_wei(receipt.gasUsed * constructor_tx['gasPrice'], 'ether'):.8f} ETH")
            
            # Save deployment info
            deployment_info = {
                'network': 'base',
                'chain_id': 8453,
                'contract_address': contract_address,
                'transaction_hash': tx_hash.hex(),
                'deployer_address': account.address,
                'deployment_timestamp': int(time.time()),
                'gas_used': receipt.gasUsed,
                'deployment_cost_eth': float(w3.from_wei(receipt.gasUsed * constructor_tx['gasPrice'], 'ether')),
                'abi': contract_interface['abi'],
                'contract_version': 'BASE_FIXED_v1.0'
            }
            
            with open('base_deployment.json', 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            print(f"💾 Deployment saved to base_deployment.json")
            
            return deployment_info
            
        else:
            print(f"❌ Deployment failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Deploy to both Optimism and Base."""
    print("🌐 MULTI-CHAIN DEPLOYMENT")
    print("=" * 30)
    print("Deploying fixed flashloan contracts to:")
    print("🔗 Optimism (ultra-low gas)")
    print("🔗 Base (ultra-low gas)")
    print()
    
    deployments = {}
    
    # Deploy to Optimism
    optimism_deployment = deploy_to_optimism()
    if optimism_deployment:
        deployments['optimism'] = optimism_deployment
        print("✅ Optimism deployment successful!")
    else:
        print("❌ Optimism deployment failed!")
    
    # Deploy to Base
    base_deployment = deploy_to_base()
    if base_deployment:
        deployments['base'] = base_deployment
        print("✅ Base deployment successful!")
    else:
        print("❌ Base deployment failed!")
    
    # Summary
    print(f"\n🎉 DEPLOYMENT SUMMARY:")
    print("=" * 25)
    
    if deployments:
        for chain_name, info in deployments.items():
            print(f"🔗 {chain_name.title()}:")
            print(f"   📍 Address: {info['contract_address']}")
            print(f"   💰 Cost: {info['deployment_cost_eth']:.6f} ETH")
        
        total_cost = sum(info['deployment_cost_eth'] for info in deployments.values())
        print(f"\n💰 Total cost: {total_cost:.6f} ETH")
        print(f"🌐 Chains deployed: {len(deployments)}/2")
        
        if len(deployments) == 2:
            print("\n🎉 MULTI-CHAIN DEPLOYMENT COMPLETE!")
            print("Ready for 3x speed arbitrage coverage!")
        
        return True
    else:
        print("\n❌ No successful deployments!")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🚀 READY FOR MULTI-CHAIN ARBITRAGE!")
    else:
        print("\n💥 DEPLOYMENT FAILED!")
