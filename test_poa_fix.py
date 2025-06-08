#!/usr/bin/env python3
"""
🔧 Test POA Middleware Fix
Test if the POA middleware fix resolves the Linea extraData error.
"""

import os
import logging
from web3 import Web3

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_poa_middleware():
    """Test POA middleware with different chains."""
    
    print("🔧 TESTING POA MIDDLEWARE FIX")
    print("=" * 40)
    
    # Test configurations
    test_chains = {
        'linea': {
            'rpc_url': os.getenv('LINEA_RPC_KEY', 'https://rpc.linea.build'),
            'requires_poa': True
        },
        'bsc': {
            'rpc_url': 'https://bsc-dataseed.binance.org',
            'requires_poa': True
        },
        'base': {
            'rpc_url': 'https://mainnet.base.org',
            'requires_poa': True
        }
    }
    
    for chain_name, config in test_chains.items():
        print(f"\n🔗 Testing {chain_name.upper()}...")
        
        try:
            # Create Web3 connection
            w3 = Web3(Web3.HTTPProvider(config['rpc_url']))
            
            # Inject POA middleware if needed
            if config['requires_poa']:
                try:
                    # Use the correct POA middleware for Web3 v7+
                    try:
                        from web3.middleware import ExtraDataToPOAMiddleware
                        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                        print(f"   ✅ POA middleware (ExtraDataToPOAMiddleware) injected")
                    except ImportError:
                        print(f"   ❌ ExtraDataToPOAMiddleware not found")
                        
                except Exception as e:
                    print(f"   ❌ POA middleware injection failed: {e}")
            
            # Test connection
            if w3.is_connected():
                print(f"   ✅ Connected to {chain_name}")
                
                # Test getting latest block (this is where the error occurs)
                try:
                    latest_block = w3.eth.get_block('latest')
                    print(f"   ✅ Latest block: {latest_block['number']}")
                    print(f"   📦 Block hash: {latest_block['hash'].hex()[:20]}...")
                    
                    # Check extraData length
                    extra_data_len = len(latest_block['extraData'])
                    print(f"   📊 ExtraData length: {extra_data_len} bytes")
                    
                    if extra_data_len > 32:
                        print(f"   ✅ POA chain detected (extraData > 32 bytes) - middleware working!")
                    else:
                        print(f"   ℹ️ Standard chain (extraData <= 32 bytes)")
                        
                except Exception as e:
                    print(f"   ❌ Block fetch failed: {e}")
                    if "extraData" in str(e):
                        print(f"   💡 This is the POA error - middleware not working properly")
                    
            else:
                print(f"   ❌ Failed to connect to {chain_name}")
                
        except Exception as e:
            print(f"   ❌ Test failed for {chain_name}: {e}")
    
    print(f"\n🎯 TEST COMPLETE")

def test_web3_version():
    """Check Web3 version and available middleware."""
    
    print(f"\n🔍 WEB3 ENVIRONMENT CHECK")
    print("=" * 30)
    
    try:
        import web3
        print(f"✅ Web3 version: {web3.__version__}")
        
        # Check available middleware
        try:
            from web3.middleware import geth_poa_middleware
            print(f"✅ geth_poa_middleware available from web3.middleware")
        except ImportError:
            print(f"❌ geth_poa_middleware not available from web3.middleware")
        
        try:
            from web3.middleware.geth_poa import geth_poa_middleware
            print(f"✅ geth_poa_middleware available from web3.middleware.geth_poa")
        except ImportError:
            print(f"❌ geth_poa_middleware not available from web3.middleware.geth_poa")
        
        try:
            from web3.middleware.poa import geth_poa_middleware
            print(f"✅ geth_poa_middleware available from web3.middleware.poa")
        except ImportError:
            print(f"❌ geth_poa_middleware not available from web3.middleware.poa")
            
    except Exception as e:
        print(f"❌ Web3 environment check failed: {e}")

if __name__ == "__main__":
    test_web3_version()
    test_poa_middleware()
