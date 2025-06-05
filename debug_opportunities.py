#!/usr/bin/env python3
"""
🔍 DEBUG OPPORTUNITY EVALUATION
Test your theory about opportunity filtering based on small balances
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    print("🔍 DEBUGGING OPPORTUNITY EVALUATION")
    print("=" * 50)
    
    # Check environment
    wallet_address = os.getenv('WALLET_ADDRESS')
    alchemy_key = os.getenv('ALCHEMY_API_KEY')
    
    if not wallet_address or not alchemy_key:
        print("❌ Missing environment variables")
        return
    
    print(f"✅ Wallet: {wallet_address}")
    print(f"✅ API Key: {alchemy_key[:10]}...")
    print()
    
    # Test 1: Check current balances
    print("📊 CURRENT TOKEN BALANCES:")
    print("-" * 30)
    
    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(f'https://arb-mainnet.g.alchemy.com/v2/{alchemy_key}'))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum")
        return
    
    # Token addresses
    tokens = {
        'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
        'USDC': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
        'USDC.e': '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
        'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
        'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'
    }
    
    # ERC20 ABI
    erc20_abi = [
        {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], 
         "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
        {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
    ]
    
    total_value = 0
    balances = {}
    
    # ETH balance
    eth_balance = w3.eth.get_balance(wallet_address)
    eth_balance_ether = w3.from_wei(eth_balance, 'ether')
    eth_value = float(eth_balance_ether) * 3000  # Assume $3000 ETH
    total_value += eth_value
    balances['ETH'] = {'amount': float(eth_balance_ether), 'value': eth_value}
    print(f"   ETH: {eth_balance_ether:.6f} ETH (${eth_value:.2f})")
    
    # Token balances
    for symbol, address in tokens.items():
        try:
            contract = w3.eth.contract(address=address, abi=erc20_abi)
            balance = contract.functions.balanceOf(wallet_address).call()
            decimals = contract.functions.decimals().call()
            balance_formatted = balance / (10 ** decimals)
            
            # Estimate USD value (rough)
            if symbol in ['USDC', 'USDC.e', 'USDT', 'DAI']:
                usd_value = balance_formatted  # Stablecoins ≈ $1
            elif symbol == 'WETH':
                usd_value = balance_formatted * 3000  # WETH ≈ ETH price
            else:
                usd_value = 0  # Unknown tokens
            
            total_value += usd_value
            balances[symbol] = {'amount': balance_formatted, 'value': usd_value}
            print(f"   {symbol}: {balance_formatted:.2f} (${usd_value:.2f})")
            
        except Exception as e:
            print(f"   {symbol}: Error - {e}")
            balances[symbol] = {'amount': 0, 'value': 0}
    
    print(f"\n💰 TOTAL WALLET VALUE: ${total_value:.2f}")
    print()
    
    # Test 2: Simulate opportunity evaluation
    print("🎯 OPPORTUNITY EVALUATION TEST:")
    print("-" * 35)
    
    # Simulate finding a WETH arbitrage opportunity
    weth_balance = balances.get('WETH', {}).get('amount', 0)
    total_convertible = sum(b['value'] for b in balances.values() if b['value'] > 0)
    
    print(f"📊 Scenario: WETH arbitrage opportunity found")
    print(f"   Current WETH balance: {weth_balance:.6f} WETH")
    print(f"   Total convertible value: ${total_convertible:.2f}")
    print()
    
    # Current system logic (BROKEN)
    print("❌ CURRENT SYSTEM LOGIC:")
    if weth_balance < 0.01:  # Tiny balance
        profit_current = 0
        print(f"   With {weth_balance:.6f} WETH → Profit: ${profit_current:.2f}")
        print(f"   Result: FILTERED OUT (insufficient balance)")
    else:
        profit_current = weth_balance * 0.0034 * 3000  # 0.34% profit (from logs)
        print(f"   With {weth_balance:.6f} WETH → Profit: ${profit_current:.2f}")
        print(f"   Result: {'VIABLE' if profit_current > 0.01 else 'FILTERED OUT'}")

    print()

    # Correct system logic (SHOULD BE)
    print("✅ CORRECT SYSTEM LOGIC:")
    trade_amount_usd = total_convertible * 0.5  # 50% of wallet
    trade_amount_weth = trade_amount_usd / 3000  # Convert to WETH
    profit_correct = trade_amount_weth * 0.0034 * 3000  # 0.34% profit (from logs)
    
    print(f"   Convert 50% of wallet (${trade_amount_usd:.2f}) to {trade_amount_weth:.6f} WETH")
    print(f"   With {trade_amount_weth:.6f} WETH → Profit: ${profit_correct:.2f}")
    print(f"   Result: {'VIABLE' if profit_correct > 0.01 else 'FILTERED OUT'}")
    
    print()
    print("🎯 CONCLUSION:")
    print(f"   Current system sees: ${profit_current:.2f} profit")
    print(f"   Should see: ${profit_correct:.2f} profit")
    print(f"   Difference: ${profit_correct - profit_current:.2f}")
    
    if profit_correct > 1.0 and profit_current < 0.01:
        print("   🚨 CONFIRMED: Opportunities being filtered due to small balances!")
        print("   💡 Solution: Evaluate opportunities based on convertible wallet value")
    else:
        print("   ✅ Theory not confirmed - different issue")

if __name__ == "__main__":
    main()
