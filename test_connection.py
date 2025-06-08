#!/usr/bin/env python3
"""
Quick connection test to diagnose Web3 connection issues
"""

import os
import asyncio
from web3 import Web3
import requests

async def test_connections():
    """Test all RPC connections to see what's working."""
    
    # Get API key
    alchemy_api_key = os.getenv('ALCHEMY_API_KEY')
    print(f"🔑 Alchemy API Key: {alchemy_api_key[:8]}...{alchemy_api_key[-4:] if alchemy_api_key else 'NOT FOUND'}")
    
    # Test networks
    networks = {
        'arbitrum': {
            'primary': f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_api_key}",
            'fallbacks': [
                'https://arbitrum.public-rpc.com',
                'https://arb1.arbitrum.io/rpc',
                'https://arbitrum-one.publicnode.com'
            ]
        },
        'base': {
            'primary': f"https://base-mainnet.g.alchemy.com/v2/{alchemy_api_key}",
            'fallbacks': [
                'https://mainnet.base.org',
                'https://base.public-rpc.com',
                'https://base-mainnet.public.blastapi.io'
            ]
        },
        'optimism': {
            'primary': f"https://opt-mainnet.g.alchemy.com/v2/{alchemy_api_key}",
            'fallbacks': [
                'https://mainnet.optimism.io',
                'https://optimism.public-rpc.com',
                'https://optimism-mainnet.public.blastapi.io'
            ]
        }
    }
    
    working_connections = {}
    
    for network, config in networks.items():
        print(f"\n🔗 Testing {network.upper()} connections...")
        
        # Test all RPCs for this network
        all_rpcs = [config['primary']] + config['fallbacks']
        
        for i, rpc_url in enumerate(all_rpcs):
            rpc_type = "PRIMARY (Alchemy)" if i == 0 else f"FALLBACK #{i}"
            print(f"   🔍 {rpc_type}: {rpc_url[:60]}...")
            
            try:
                # Test with Web3
                w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
                
                # Try to get chain ID
                chain_id = w3.eth.chain_id
                latest_block = w3.eth.block_number
                
                print(f"   ✅ {rpc_type} SUCCESS! Chain ID: {chain_id}, Latest block: {latest_block}")
                
                # Store first working connection
                if network not in working_connections:
                    working_connections[network] = {
                        'rpc_url': rpc_url,
                        'type': rpc_type,
                        'chain_id': chain_id,
                        'web3': w3
                    }
                
            except Exception as e:
                print(f"   ❌ {rpc_type} FAILED: {e}")
                
                # For primary RPC, try direct HTTP test
                if i == 0:
                    try:
                        payload = {
                            "jsonrpc": "2.0",
                            "method": "eth_chainId",
                            "params": [],
                            "id": 1
                        }
                        response = requests.post(rpc_url, json=payload, timeout=10)
                        print(f"   🌐 Direct HTTP test: {response.status_code}")
                        if response.status_code == 200:
                            result = response.json()
                            print(f"   🌐 HTTP works: {result}")
                        else:
                            print(f"   🌐 HTTP failed: {response.text[:100]}")
                    except Exception as http_error:
                        print(f"   🌐 HTTP test failed: {http_error}")
    
    print(f"\n🎯 SUMMARY:")
    print(f"   ✅ Working connections: {len(working_connections)}")
    
    for network, info in working_connections.items():
        print(f"   🔗 {network}: {info['type']} (Chain ID: {info['chain_id']})")
    
    if not working_connections:
        print("   ❌ NO WORKING CONNECTIONS FOUND!")
        print("   🚨 This explains why arbitrage execution is failing!")
    else:
        print("   🚀 Connections available - issue might be elsewhere")
    
    return working_connections

if __name__ == "__main__":
    asyncio.run(test_connections())
