#!/usr/bin/env python3
"""
🔥 DEPLOY FIXED FLASHLOAN CONTRACT
Deploys the corrected flashloan contract to Arbitrum mainnet
"""

import os
import json
import time
from web3 import Web3
from solcx import compile_source, install_solc, set_solc_version
from eth_account import Account

# Configuration
ARBITRUM_RPC = "https://arb1.arbitrum.io/rpc"
AAVE_POOL_ADDRESS_PROVIDER = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb"  # Arbitrum Aave V3

def load_private_key():
    """Load private key from environment"""
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        raise ValueError("PRIVATE_KEY environment variable not set")
    return private_key

def compile_contract():
    """Compile the fixed flashloan contract"""
    print("🔧 Compiling FixedFlashloanArbitrage contract...")
    
    # Install and set Solidity version
    install_solc('0.8.19')
    set_solc_version('0.8.19')
    
    # Read contract source
    with open('contracts/FixedFlashloanArbitrage.sol', 'r') as f:
        contract_source = f.read()
    
    # Compile contract
    compiled_sol = compile_source(
        contract_source,
        output_values=['abi', 'bin'],
        solc_version='0.8.19'
    )
    
    contract_interface = compiled_sol['<stdin>:FixedFlashloanArbitrage']
    
    print("✅ Contract compiled successfully!")
    return contract_interface

def deploy_contract():
    """Deploy the contract to Arbitrum mainnet"""
    print("🚀 DEPLOYING TO ARBITRUM MAINNET...")
    print("⚠️  WARNING: This is LIVE deployment with real funds!")
    
    # Confirm deployment
    confirm = input("Type 'DEPLOY' to confirm mainnet deployment: ")
    if confirm != 'DEPLOY':
        print("❌ Deployment cancelled")
        return None
    
    # Setup Web3
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    if not w3.is_connected():
        raise Exception("Failed to connect to Arbitrum RPC")
    
    print(f"✅ Connected to Arbitrum (Chain ID: {w3.eth.chain_id})")
    
    # Load account
    private_key = load_private_key()
    account = Account.from_key(private_key)
    
    print(f"🔑 Deploying from: {account.address}")
    
    # Check balance
    balance = w3.eth.get_balance(account.address)
    balance_eth = w3.from_wei(balance, 'ether')
    print(f"💰 Account balance: {balance_eth:.4f} ETH")
    
    if balance_eth < 0.01:
        raise Exception("Insufficient ETH for deployment (need at least 0.01 ETH)")
    
    # Compile contract
    contract_interface = compile_contract()
    
    # Create contract instance
    contract = w3.eth.contract(
        abi=contract_interface['abi'],
        bytecode=contract_interface['bin']
    )
    
    # Get gas price
    gas_price = w3.eth.gas_price
    print(f"⛽ Gas price: {w3.from_wei(gas_price, 'gwei'):.2f} gwei")
    
    # Build transaction
    constructor_txn = contract.constructor(AAVE_POOL_ADDRESS_PROVIDER).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 3000000,  # Conservative gas limit
        'gasPrice': gas_price,
    })
    
    # Estimate actual gas
    try:
        estimated_gas = w3.eth.estimate_gas(constructor_txn)
        constructor_txn['gas'] = int(estimated_gas * 1.2)  # 20% buffer
        print(f"⛽ Estimated gas: {estimated_gas:,}")
    except Exception as e:
        print(f"⚠️  Gas estimation failed: {e}")
        print("Using conservative gas limit...")
    
    # Sign and send transaction
    signed_txn = w3.eth.account.sign_transaction(constructor_txn, private_key)
    
    print("📡 Sending deployment transaction...")
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    print(f"🔗 Transaction hash: {tx_hash.hex()}")
    print(f"🔗 Arbiscan: https://arbiscan.io/tx/{tx_hash.hex()}")
    
    # Wait for confirmation
    print("⏳ Waiting for confirmation...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    
    if tx_receipt.status == 1:
        contract_address = tx_receipt.contractAddress
        print(f"✅ CONTRACT DEPLOYED SUCCESSFULLY!")
        print(f"📍 Contract Address: {contract_address}")
        print(f"🔗 Arbiscan: https://arbiscan.io/address/{contract_address}")
        
        # Save deployment info
        deployment_info = {
            'contract_address': contract_address,
            'transaction_hash': tx_hash.hex(),
            'deployer': account.address,
            'block_number': tx_receipt.blockNumber,
            'gas_used': tx_receipt.gasUsed,
            'deployment_time': time.time(),
            'network': 'arbitrum',
            'aave_provider': AAVE_POOL_ADDRESS_PROVIDER
        }
        
        with open('deployment_info.json', 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        print("💾 Deployment info saved to deployment_info.json")
        
        return contract_address
    else:
        print("❌ Deployment failed!")
        return None

def verify_deployment(contract_address):
    """Verify the deployed contract"""
    print(f"🔍 Verifying deployment at {contract_address}...")
    
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    
    # Check if contract exists
    code = w3.eth.get_code(contract_address)
    if len(code) > 0:
        print("✅ Contract code found on blockchain")
        
        # Load ABI and test basic functions
        contract_interface = compile_contract()
        contract = w3.eth.contract(
            address=contract_address,
            abi=contract_interface['abi']
        )
        
        try:
            # Test view functions
            owner = contract.functions.owner().call()
            min_profit = contract.functions.minProfitBps().call()
            
            print(f"✅ Contract owner: {owner}")
            print(f"✅ Min profit threshold: {min_profit} bps")
            print("✅ Contract verification successful!")
            
            return True
        except Exception as e:
            print(f"❌ Contract verification failed: {e}")
            return False
    else:
        print("❌ No contract code found at address")
        return False

def update_system_config(contract_address):
    """Update system configuration with new contract address"""
    print("🔧 Updating system configuration...")
    
    config_updates = {
        'flashloan_contract_address': contract_address,
        'flashloan_contract_updated': time.time(),
        'flashloan_version': 'FixedFlashloanArbitrage_v2'
    }
    
    # Update config file if it exists
    config_file = 'config/arbitrage_config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        config.update(config_updates)
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration updated")
    else:
        print("⚠️  Config file not found, creating new one...")
        with open(config_file, 'w') as f:
            json.dump(config_updates, f, indent=2)

def main():
    """Main deployment process"""
    print("🔥 FIXED FLASHLOAN CONTRACT DEPLOYMENT")
    print("=====================================")
    
    try:
        # Deploy contract
        contract_address = deploy_contract()
        
        if contract_address:
            # Verify deployment
            if verify_deployment(contract_address):
                # Update system config
                update_system_config(contract_address)
                
                print("\n🎉 DEPLOYMENT COMPLETE!")
                print(f"📍 New contract address: {contract_address}")
                print("🔧 System configuration updated")
                print("⚡ Ready for arbitrage trading!")
                
                return contract_address
            else:
                print("❌ Deployment verification failed")
                return None
        else:
            print("❌ Deployment failed")
            return None
            
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return None

if __name__ == "__main__":
    main()
