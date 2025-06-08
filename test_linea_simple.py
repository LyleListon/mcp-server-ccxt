#!/usr/bin/env python3
"""
🔧 Simple Linea Test
Test if the POA middleware fix works for Linea.
"""

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

def test_linea():
    print("🔧 TESTING LINEA POA FIX")
    print("=" * 30)
    
    # Connect to Linea
    w3 = Web3(Web3.HTTPProvider("https://rpc.linea.build"))
    
    if w3.is_connected():
        print("✅ Connected to Linea")
        
        # Add POA middleware
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        print("✅ POA middleware injected")
        
        # Test block fetching
        try:
            block = w3.eth.get_block('latest')
            print(f"🎉 SUCCESS! Block {block['number']} fetched")

            # Check extraData
            if 'extraData' in block:
                print(f"📏 ExtraData: {len(block['extraData'])} bytes")
                print(f"✅ POA middleware working correctly!")
                return True
            else:
                print("⚠️ No extraData field found")
                return False

        except Exception as e:
            print(f"❌ Block fetch failed: {e}")
            return False
    else:
        print("❌ Connection failed")
        return False

if __name__ == "__main__":
    success = test_linea()
    if success:
        print("\n🎉 POA MIDDLEWARE FIX SUCCESSFUL!")
    else:
        print("\n❌ POA middleware fix failed")
