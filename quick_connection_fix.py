#!/usr/bin/env python3
"""
Quick fix to test and establish Web3 connections
"""

import os
import sys
from web3 import Web3

def test_simple_connection():
    """Test the simplest possible connection to see what's working."""
    
    print("🔍 SIMPLE CONNECTION TEST...")
    
    # Test public RPCs first (no API key needed)
    test_rpcs = [
        ('arbitrum_public', 'https://arbitrum.public-rpc.com'),
        ('arbitrum_official', 'https://arb1.arbitrum.io/rpc'),
        ('base_public', 'https://mainnet.base.org'),
        ('optimism_public', 'https://mainnet.optimism.io')
    ]
    
    working_connections = {}
    
    for name, rpc_url in test_rpcs:
        print(f"\n🔗 Testing {name}: {rpc_url}")
        
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 5}))
            
            # Quick test
            chain_id = w3.eth.chain_id
            latest_block = w3.eth.block_number
            
            print(f"   ✅ SUCCESS! Chain ID: {chain_id}, Block: {latest_block}")
            
            # Map to network name
            if 'arbitrum' in name:
                working_connections['arbitrum'] = w3
            elif 'base' in name:
                working_connections['base'] = w3
            elif 'optimism' in name:
                working_connections['optimism'] = w3
                
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
    
    print(f"\n🎯 WORKING CONNECTIONS: {len(working_connections)}")
    for network, w3 in working_connections.items():
        print(f"   ✅ {network}: Chain ID {w3.eth.chain_id}")
    
    return working_connections

def test_alchemy_connection():
    """Test Alchemy specifically."""
    
    print("\n🔍 ALCHEMY CONNECTION TEST...")
    
    alchemy_api_key = os.getenv('ALCHEMY_API_KEY')
    if not alchemy_api_key:
        print("❌ No ALCHEMY_API_KEY found")
        return {}
    
    print(f"🔑 API Key: {alchemy_api_key[:8]}...{alchemy_api_key[-4:]}")
    
    alchemy_rpcs = [
        ('arbitrum', f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_api_key}"),
        ('base', f"https://base-mainnet.g.alchemy.com/v2/{alchemy_api_key}"),
        ('optimism', f"https://opt-mainnet.g.alchemy.com/v2/{alchemy_api_key}")
    ]
    
    working_alchemy = {}
    
    for network, rpc_url in alchemy_rpcs:
        print(f"\n🔗 Testing Alchemy {network}: {rpc_url[:60]}...")
        
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 5}))
            
            chain_id = w3.eth.chain_id
            latest_block = w3.eth.block_number
            
            print(f"   ✅ ALCHEMY {network} SUCCESS! Chain ID: {chain_id}, Block: {latest_block}")
            working_alchemy[network] = w3
            
        except Exception as e:
            print(f"   ❌ ALCHEMY {network} FAILED: {e}")
    
    return working_alchemy

if __name__ == "__main__":
    print("🚀 QUICK CONNECTION DIAGNOSTIC")
    print("=" * 50)
    
    # Test public RPCs first
    public_connections = test_simple_connection()
    
    # Test Alchemy
    alchemy_connections = test_alchemy_connection()
    
    print("\n" + "=" * 50)
    print("🎯 FINAL SUMMARY:")
    
    if public_connections:
        print(f"✅ Public RPCs working: {list(public_connections.keys())}")
    else:
        print("❌ No public RPCs working")
    
    if alchemy_connections:
        print(f"✅ Alchemy RPCs working: {list(alchemy_connections.keys())}")
    else:
        print("❌ No Alchemy RPCs working")
    
    # Check specifically for arbitrum
    arbitrum_working = 'arbitrum' in public_connections or 'arbitrum' in alchemy_connections
    
    if arbitrum_working:
        print("✅ ARBITRUM connection available - executor should work!")
    else:
        print("❌ NO ARBITRUM connection - this explains the error!")
        print("🔧 SOLUTION: Use working networks or fix connection issue")
    
    print("\n🚀 Ready to restart arbitrage system with working connections!")
