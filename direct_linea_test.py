#!/usr/bin/env python3
"""
🔧 Direct Linea Test
Test Linea connection directly without DEX scanner.
"""

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

def test_linea_direct():
    """Test Linea connection directly."""
    
    print("🔧 DIRECT LINEA TEST")
    print("=" * 25)
    
    # Use public Linea RPC
    rpc_url = "https://rpc.linea.build"
    print(f"🔗 Connecting to: {rpc_url}")
    
    try:
        # Create Web3 connection
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if w3.is_connected():
            print("✅ Connected to Linea")
            
            # Test without POA middleware first
            print("\n📦 Testing WITHOUT POA middleware:")
            try:
                block = w3.eth.get_block('latest')
                print(f"✅ Block {block['number']} fetched successfully")
            except Exception as e:
                print(f"❌ Failed: {e}")
                if "extraData" in str(e):
                    print("💡 This is the POA error we need to fix")
            
            # Now add POA middleware
            print("\n🔧 Adding POA middleware...")
            try:
                # Use ExtraDataToPOAMiddleware directly (it's a curry object)
                w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                print("✅ POA middleware injected")
                
                # Test with POA middleware
                print("\n📦 Testing WITH POA middleware:")
                block = w3.eth.get_block('latest')
                print(f"✅ Block {block['number']} fetched successfully!")
                print(f"📏 ExtraData length: {len(block['extraData'])} bytes")
                print("🎉 POA MIDDLEWARE IS WORKING!")
                
            except Exception as e:
                print(f"❌ POA middleware failed: {e}")
        else:
            print("❌ Failed to connect to Linea")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_linea_direct()
