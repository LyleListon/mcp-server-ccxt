#!/usr/bin/env python3
"""
Basic connection test with fast timeout
"""

import os
from web3 import Web3

def quick_test():
    """Quick test with very short timeouts."""
    
    print("🚀 QUICK CONNECTION TEST (5 second timeout)")
    
    # Test one simple RPC
    test_url = "https://arb1.arbitrum.io/rpc"
    print(f"Testing: {test_url}")
    
    try:
        w3 = Web3(Web3.HTTPProvider(test_url, request_kwargs={'timeout': 5}))
        chain_id = w3.eth.chain_id
        print(f"✅ SUCCESS! Chain ID: {chain_id}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    if quick_test():
        print("🚀 Connection working - restarting arbitrage system!")
    else:
        print("❌ Connection failed - network issue confirmed")
