#!/usr/bin/env python3
"""
💰 CHECK CHAIN BALANCES
Check ETH balances across all chains for arbitrage trading
"""

import os
from web3 import Web3

def check_balances():
    """Check balances across all chains."""
    
    print("💰 CHECKING CHAIN BALANCES")
    print("=" * 50)
    
    # Get environment variables
    alchemy_key = os.getenv('ALCHEMY_API_KEY')
    wallet_address = os.getenv('WALLET_ADDRESS')
    
    if not alchemy_key or not wallet_address:
        print("❌ Missing environment variables")
        return
    
    print(f"🔑 Wallet: {wallet_address}")
    print()
    
    # Chain configurations
    chains = {
        'Arbitrum': f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_key}",
        'Base': f"https://base-mainnet.g.alchemy.com/v2/{alchemy_key}",
        'Optimism': f"https://opt-mainnet.g.alchemy.com/v2/{alchemy_key}"
    }
    
    total_balance = 0
    
    for chain_name, rpc_url in chains.items():
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if w3.is_connected():
                balance_wei = w3.eth.get_balance(wallet_address)
                balance_eth = balance_wei / 1e18
                balance_usd = balance_eth * 3500  # Approximate ETH price
                
                total_balance += balance_usd
                
                # Status indicator
                if balance_eth > 0.01:
                    status = "✅ READY"
                elif balance_eth > 0.001:
                    status = "⚠️  LOW"
                else:
                    status = "❌ EMPTY"
                
                print(f"{chain_name:10} | {balance_eth:>10.6f} ETH | ${balance_usd:>8.2f} | {status}")
                
                # Gas cost estimate
                gas_price = w3.eth.gas_price
                gas_cost_wei = 300000 * gas_price  # Typical DEX swap gas
                gas_cost_eth = gas_cost_wei / 1e18
                
                if balance_eth < gas_cost_eth:
                    print(f"           | ⚠️  Need {gas_cost_eth:.6f} ETH for gas")
                
            else:
                print(f"{chain_name:10} | ❌ CONNECTION FAILED")
                
        except Exception as e:
            print(f"{chain_name:10} | ❌ ERROR: {e}")
    
    print("-" * 50)
    print(f"{'TOTAL':10} | {'':<10} | ${total_balance:>8.2f}")
    print()
    
    # Recommendations
    print("🎯 RECOMMENDATIONS:")
    
    if total_balance < 50:
        print("❌ Insufficient funds for arbitrage trading")
        print("   Minimum recommended: $100+ across chains")
    elif total_balance < 100:
        print("⚠️  Low funds - consider adding more for better opportunities")
    else:
        print("✅ Sufficient funds for arbitrage trading")
    
    print()
    print("💡 BRIDGE SUGGESTIONS:")
    print("   • Bridge 0.01-0.02 ETH to Base for gas fees")
    print("   • Bridge 0.01-0.02 ETH to Optimism for gas fees")
    print("   • Keep most funds on Arbitrum (lowest fees)")
    print()
    print("🌉 BRIDGE OPTIONS:")
    print("   • https://bridge.base.org (Base)")
    print("   • https://app.optimism.io/bridge (Optimism)")
    print("   • https://across.to (Fast cross-chain)")

if __name__ == "__main__":
    check_balances()
