#!/usr/bin/env python3
"""
Deploy Triangular Flashloan Arbitrage Contract
Fixes the IDENTICAL_ADDRESSES error by properly handling triangular arbitrage
"""

import os
import json
import time
from web3 import Web3
from eth_account import Account
from solcx import compile_source, install_solc, set_solc_version

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def colored_print(text, color):
    print(f"{color}{text}{Colors.END}")

def main():
    """Deploy the triangular flashloan arbitrage contract."""
    
    colored_print("🚀 DEPLOYING TRIANGULAR FLASHLOAN ARBITRAGE CONTRACT", Colors.BOLD + Colors.CYAN)
    colored_print("=" * 60, Colors.CYAN)
    
    try:
        # Load environment variables
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            colored_print("❌ PRIVATE_KEY environment variable not set", Colors.RED)
            return False
            
        # Setup Web3 connection (Arbitrum)
        arbitrum_rpc = "https://arb1.arbitrum.io/rpc"
        w3 = Web3(Web3.HTTPProvider(arbitrum_rpc))
        
        if not w3.is_connected():
            colored_print("❌ Failed to connect to Arbitrum RPC", Colors.RED)
            return False
            
        colored_print("✅ Connected to Arbitrum", Colors.GREEN)
        
        # Setup account
        account = Account.from_key(private_key)
        colored_print(f"📝 Deployer address: {account.address}", Colors.WHITE)
        
        # Check balance
        balance = w3.eth.get_balance(account.address)
        balance_eth = w3.from_wei(balance, 'ether')
        colored_print(f"💰 Balance: {balance_eth:.4f} ETH", Colors.WHITE)
        
        if balance_eth < 0.01:
            colored_print("⚠️ Low balance - deployment may fail", Colors.YELLOW)
        
        # Install and set Solidity compiler
        colored_print("🔧 Setting up Solidity compiler...", Colors.BLUE)
        try:
            install_solc('0.8.19')
            set_solc_version('0.8.19')
        except Exception as e:
            colored_print(f"⚠️ Compiler setup warning: {e}", Colors.YELLOW)
        
        # Read contract source
        contract_path = "contracts/TriangularFlashloanArbitrage.sol"
        if not os.path.exists(contract_path):
            colored_print(f"❌ Contract file not found: {contract_path}", Colors.RED)
            return False
            
        with open(contract_path, 'r') as f:
            contract_source = f.read()
        
        colored_print("📄 Contract source loaded", Colors.GREEN)
        
        # Compile contract
        colored_print("🔨 Compiling contract...", Colors.BLUE)
        
        # Create compilation input with viaIR to fix stack too deep
        compilation_input = {
            'language': 'Solidity',
            'sources': {
                'TriangularFlashloanArbitrage.sol': {
                    'content': contract_source
                }
            },
            'settings': {
                'outputSelection': {
                    '*': {
                        '*': ['abi', 'evm.bytecode']
                    }
                },
                'optimizer': {
                    'enabled': True,
                    'runs': 200
                },
                'viaIR': True  # Fix for stack too deep error
            }
        }
        
        try:
            from solcx import compile_standard
            compiled_sol = compile_standard(compilation_input)
        except Exception as e:
            colored_print(f"❌ Compilation failed: {e}", Colors.RED)
            return False
        
        # Extract contract data
        contract_data = compiled_sol['contracts']['TriangularFlashloanArbitrage.sol']['TriangularFlashloanArbitrage']
        abi = contract_data['abi']
        bytecode = contract_data['evm']['bytecode']['object']
        
        colored_print("✅ Contract compiled successfully", Colors.GREEN)
        
        # Deploy contract
        colored_print("🚀 Deploying contract...", Colors.BLUE)
        
        # Aave V3 Pool Address Provider on Arbitrum
        aave_address_provider = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb"
        
        # Create contract instance
        contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        
        # Get current gas price
        gas_price = w3.eth.gas_price
        priority_gas_price = int(gas_price * 1.2)  # 20% higher for faster confirmation
        
        # Build deployment transaction
        constructor_txn = contract.constructor(aave_address_provider).build_transaction({
            'from': account.address,
            'gas': 4000000,  # High gas limit for deployment
            'gasPrice': priority_gas_price,
            'nonce': w3.eth.get_transaction_count(account.address)
        })
        
        colored_print(f"⛽ Gas price: {w3.from_wei(priority_gas_price, 'gwei'):.2f} Gwei", Colors.WHITE)
        colored_print(f"💸 Estimated cost: {w3.from_wei(constructor_txn['gas'] * priority_gas_price, 'ether'):.6f} ETH", Colors.WHITE)
        
        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(constructor_txn, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        colored_print(f"📤 Transaction sent: {tx_hash.hex()}", Colors.YELLOW)
        colored_print("⏳ Waiting for confirmation...", Colors.BLUE)
        
        # Wait for transaction receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if tx_receipt.status == 1:
            colored_print("✅ CONTRACT DEPLOYED SUCCESSFULLY!", Colors.BOLD + Colors.GREEN)
            colored_print(f"📍 Contract Address: {tx_receipt.contractAddress}", Colors.GREEN)
            colored_print(f"🔗 Arbiscan: https://arbiscan.io/address/{tx_receipt.contractAddress}", Colors.CYAN)
            colored_print(f"⛽ Gas Used: {tx_receipt.gasUsed:,}", Colors.WHITE)
            
            # Calculate actual cost
            actual_cost = tx_receipt.gasUsed * priority_gas_price
            colored_print(f"💸 Actual Cost: {w3.from_wei(actual_cost, 'ether'):.6f} ETH", Colors.WHITE)
            
            # Save deployment info
            deployment_info = {
                "network": "arbitrum",
                "chain_id": 42161,
                "contract_address": tx_receipt.contractAddress,
                "transaction_hash": tx_hash.hex(),
                "deployer_address": account.address,
                "deployment_timestamp": int(time.time()),
                "gas_used": tx_receipt.gasUsed,
                "deployment_cost_eth": w3.from_wei(actual_cost, 'ether'),
                "abi": abi,
                "aave_address_provider": aave_address_provider,
                "contract_version": "TRIANGULAR_v1.0",
                "fixes_applied": [
                    "Proper triangular arbitrage support (A→B→C→A)",
                    "IDENTICAL_ADDRESSES error fixed",
                    "Three-step swap execution",
                    "Enhanced slippage protection",
                    "Comprehensive error handling",
                    "Emergency functions"
                ]
            }
            
            with open('triangular_flashloan_deployment.json', 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            colored_print("💾 Deployment info saved to triangular_flashloan_deployment.json", Colors.GREEN)
            
            return True
            
        else:
            colored_print("❌ DEPLOYMENT FAILED!", Colors.RED)
            colored_print(f"Transaction receipt: {tx_receipt}", Colors.RED)
            return False
            
    except Exception as e:
        colored_print(f"💥 Deployment error: {e}", Colors.RED)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        colored_print("\n🎉 TRIANGULAR FLASHLOAN CONTRACT READY FOR USE!", Colors.BOLD + Colors.GREEN)
        colored_print("🔧 This contract properly handles WETH→USDC→USDT→WETH triangular arbitrage", Colors.GREEN)
        colored_print("✅ IDENTICAL_ADDRESSES error is now fixed!", Colors.GREEN)
    else:
        colored_print("\n💥 DEPLOYMENT FAILED", Colors.BOLD + Colors.RED)
        exit(1)
