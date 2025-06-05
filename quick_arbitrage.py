#!/usr/bin/env python3
"""
🚀 QUICK ARBITRAGE - MINIMAL COMPLEXITY, MAXIMUM RESULTS
Just the essentials - find opportunities and execute trades!
"""

import os
import sys
import time
from decimal import Decimal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from web3 import Web3

def main():
    print("🚀 QUICK ARBITRAGE BOT - STARTING!")
    print("💰 Using your wallet for direct arbitrage")
    print("🎯 Target: Simple profitable trades")
    print()
    
    # Environment check
    wallet_address = os.getenv('WALLET_ADDRESS')
    private_key = os.getenv('PRIVATE_KEY')
    alchemy_key = os.getenv('ALCHEMY_API_KEY')
    
    if not all([wallet_address, private_key, alchemy_key]):
        print("❌ Missing environment variables")
        return
    
    print(f"✅ Wallet: {wallet_address}")
    print(f"✅ API Key: {alchemy_key[:10]}...")
    
    # Connect to Arbitrum
    w3 = Web3(Web3.HTTPProvider(f'https://arb-mainnet.g.alchemy.com/v2/{alchemy_key}'))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum")
        return
    
    print(f"✅ Connected to Arbitrum (Chain ID: {w3.eth.chain_id})")
    
    # Check ETH balance
    eth_balance = w3.eth.get_balance(wallet_address)
    eth_balance_ether = w3.from_wei(eth_balance, 'ether')
    
    print(f"💰 ETH Balance: {eth_balance_ether:.6f} ETH")
    
    if eth_balance_ether < 0.001:
        print("❌ Insufficient ETH for gas fees")
        return
    
    # Token addresses (corrected)
    tokens = {
        'USDC': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
        'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
        'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',
        'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1'
    }
    
    # ERC20 ABI (minimal)
    erc20_abi = [
        {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], 
         "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
        {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
    ]
    
    # Check token balances
    print("\n💰 TOKEN BALANCES:")
    for symbol, address in tokens.items():
        try:
            contract = w3.eth.contract(address=address, abi=erc20_abi)
            balance = contract.functions.balanceOf(wallet_address).call()
            decimals = contract.functions.decimals().call()
            balance_formatted = balance / (10 ** decimals)
            print(f"   {symbol}: {balance_formatted:.2f}")
        except Exception as e:
            print(f"   {symbol}: Error - {e}")
    
    # SushiSwap router
    sushi_router = '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506'
    
    # Router ABI (minimal)
    router_abi = [
        {"constant": True, "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "path", "type": "address[]"}
        ], "name": "getAmountsOut", "outputs": [{"name": "amounts", "type": "uint256[]"}], "type": "function"}
    ]
    
    router_contract = w3.eth.contract(address=sushi_router, abi=router_abi)
    
    print("\n🔍 CHECKING ARBITRAGE OPPORTUNITIES:")
    
    # Check USDC → USDT
    try:
        amount_in = 100 * 10**6  # 100 USDC (6 decimals)
        path = [tokens['USDC'], tokens['USDT']]
        amounts = router_contract.functions.getAmountsOut(amount_in, path).call()
        usdt_out = amounts[1] / 10**6  # USDT has 6 decimals
        profit = usdt_out - 100
        print(f"   USDC → USDT: 100 USDC → {usdt_out:.4f} USDT (Profit: ${profit:.4f})")
        
        if profit > 0.1:
            print(f"   🎯 PROFITABLE! Profit: ${profit:.4f}")
        
    except Exception as e:
        print(f"   USDC → USDT: Error - {e}")
    
    # Check USDT → USDC
    try:
        amount_in = 100 * 10**6  # 100 USDT (6 decimals)
        path = [tokens['USDT'], tokens['USDC']]
        amounts = router_contract.functions.getAmountsOut(amount_in, path).call()
        usdc_out = amounts[1] / 10**6  # USDC has 6 decimals
        profit = usdc_out - 100
        print(f"   USDT → USDC: 100 USDT → {usdc_out:.4f} USDC (Profit: ${profit:.4f})")
        
        if profit > 0.1:
            print(f"   🎯 PROFITABLE! Profit: ${profit:.4f}")
        
    except Exception as e:
        print(f"   USDT → USDC: Error - {e}")
    
    # Check DAI → USDC
    try:
        amount_in = 100 * 10**18  # 100 DAI (18 decimals)
        path = [tokens['DAI'], tokens['USDC']]
        amounts = router_contract.functions.getAmountsOut(amount_in, path).call()
        usdc_out = amounts[1] / 10**6  # USDC has 6 decimals
        profit = usdc_out - 100
        print(f"   DAI → USDC: 100 DAI → {usdc_out:.4f} USDC (Profit: ${profit:.4f})")
        
        if profit > 0.1:
            print(f"   🎯 PROFITABLE! Profit: ${profit:.4f}")
        
    except Exception as e:
        print(f"   DAI → USDC: Error - {e}")
    
    # Check USDC → DAI
    try:
        amount_in = 100 * 10**6  # 100 USDC (6 decimals)
        path = [tokens['USDC'], tokens['DAI']]
        amounts = router_contract.functions.getAmountsOut(amount_in, path).call()
        dai_out = amounts[1] / 10**18  # DAI has 18 decimals
        profit = dai_out - 100
        print(f"   USDC → DAI: 100 USDC → {dai_out:.4f} DAI (Profit: ${profit:.4f})")
        
        if profit > 0.1:
            print(f"   🎯 PROFITABLE! Profit: ${profit:.4f}")
        
    except Exception as e:
        print(f"   USDC → DAI: Error - {e}")
    
    print("\n✅ QUICK ARBITRAGE SCAN COMPLETE!")
    print("💡 This shows if there are profitable opportunities available")
    print("🚀 If you see profitable trades, we can implement execution!")

if __name__ == "__main__":
    main()
