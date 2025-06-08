#!/usr/bin/env python3
"""
Debug Web3 connections to find why arbitrage is failing
"""

import os
import asyncio
from web3 import Web3
from eth_account import Account

async def debug_web3_connections():
    """Debug the exact same Web3 connection setup as the arbitrage executor."""
    
    print("🔍 DEBUGGING WEB3 CONNECTIONS...")
    
    # Get API key (same as executor)
    alchemy_api_key = os.getenv('ALCHEMY_API_KEY')
    if not alchemy_api_key:
        print("❌ ALCHEMY_API_KEY not found!")
        return
    
    print(f"🔑 API Key: {alchemy_api_key[:8]}...{alchemy_api_key[-4:]}")
    
    # Same network configs as executor
    network_configs = {
        'arbitrum': {
            'rpc_url': f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_api_key}",
            'fallback_rpcs': [
                'https://arbitrum.public-rpc.com',
                'https://arb1.arbitrum.io/rpc',
                'https://arbitrum-one.publicnode.com'
            ],
            'chain_id': 42161
        },
        'base': {
            'rpc_url': f"https://base-mainnet.g.alchemy.com/v2/{alchemy_api_key}",
            'fallback_rpcs': [
                'https://mainnet.base.org',
                'https://base.public-rpc.com',
                'https://base-mainnet.public.blastapi.io'
            ],
            'chain_id': 8453
        },
        'optimism': {
            'rpc_url': f"https://opt-mainnet.g.alchemy.com/v2/{alchemy_api_key}",
            'fallback_rpcs': [
                'https://mainnet.optimism.io',
                'https://optimism.public-rpc.com',
                'https://optimism-mainnet.public.blastapi.io'
            ],
            'chain_id': 10
        }
    }
    
    # Test wallet (same as executor)
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        print("❌ PRIVATE_KEY not found!")
        return
    
    wallet_account = Account.from_key(private_key)
    wallet_address = wallet_account.address
    print(f"💰 Wallet: {wallet_address}")
    
    web3_connections = {}
    
    # Test each network (same logic as executor)
    for network, config in network_configs.items():
        print(f"\n🔗 Testing {network.upper()}...")
        connected = False
        
        # Try primary RPC first
        rpc_urls = [config['rpc_url']] + config.get('fallback_rpcs', [])
        
        for i, rpc_url in enumerate(rpc_urls):
            try:
                rpc_type = "PRIMARY" if i == 0 else f"FALLBACK #{i}"
                print(f"   🔍 {rpc_type}: {rpc_url[:60]}...")
                
                w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
                
                # Test connection by making an actual RPC call
                try:
                    # Try to get chain ID - this will test the connection
                    chain_id = w3.eth.chain_id
                    print(f"   ✅ {rpc_type} Connected! Chain ID: {chain_id}")
                    
                    # Check if chain ID matches expected
                    if chain_id != config['chain_id']:
                        print(f"   ⚠️  Chain ID mismatch! Expected {config['chain_id']}, got {chain_id}")
                    
                    web3_connections[network] = w3
                    
                    # Check wallet balance
                    balance_wei = w3.eth.get_balance(wallet_address)
                    balance_eth = w3.from_wei(balance_wei, 'ether')
                    print(f"   💰 {network.upper()}: {balance_eth:.4f} ETH")
                    
                    # Test a simple contract call to make sure everything works
                    latest_block = w3.eth.block_number
                    print(f"   📦 Latest block: {latest_block}")
                    
                    connected = True
                    break  # Success! Stop trying other RPCs
                    
                except Exception as connection_error:
                    print(f"   ❌ {rpc_type} connection failed: {connection_error}")
                    continue  # Try next RPC
                    
            except Exception as e:
                print(f"   ❌ {rpc_type} setup error: {e}")
                continue  # Try next RPC
        
        if not connected:
            print(f"   🚨 ALL RPCs FAILED for {network}!")
    
    print(f"\n🎯 SUMMARY:")
    print(f"   ✅ Working connections: {len(web3_connections)}")
    
    for network, w3 in web3_connections.items():
        print(f"   🔗 {network}: Chain ID {w3.eth.chain_id}")
    
    if not web3_connections:
        print("   ❌ NO WORKING CONNECTIONS!")
        print("   🚨 This explains the 'No Web3 connection for arbitrum' error!")
        return False
    else:
        print("   🚀 Connections working - issue might be in executor initialization")
        
        # Test if arbitrum specifically is working
        if 'arbitrum' in web3_connections:
            print(f"   ✅ ARBITRUM connection is working!")
        else:
            print(f"   ❌ ARBITRUM connection failed - this is the problem!")
        
        return True

if __name__ == "__main__":
    asyncio.run(debug_web3_connections())
