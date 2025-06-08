#!/usr/bin/env python3
"""
🔧 Test Linea POA Fix
Quick test to verify the POA middleware fix works for Linea.
"""

import os
import asyncio
from dex_scanner import DEXScanner

async def test_linea_connection():
    """Test Linea connection with POA middleware."""
    
    print("🔧 TESTING LINEA POA FIX")
    print("=" * 30)
    
    try:
        # Create DEX scanner for Linea
        scanner = DEXScanner('linea')
        
        print("🔗 Connecting to Linea...")
        await scanner.connect()
        
        if scanner.w3 and scanner.w3.is_connected():
            print("✅ Connected to Linea successfully!")
            
            # Test getting latest block
            print("📦 Fetching latest block...")
            latest_block = scanner.w3.eth.get_block('latest')
            
            print(f"✅ Latest block: {latest_block['number']}")
            print(f"📊 Block hash: {latest_block['hash'].hex()[:20]}...")
            print(f"📏 ExtraData length: {len(latest_block['extraData'])} bytes")
            
            if len(latest_block['extraData']) > 32:
                print("🎉 SUCCESS! POA middleware is working correctly!")
                print("   Large extraData handled without errors")
            else:
                print("ℹ️ Standard block format detected")
                
        else:
            print("❌ Failed to connect to Linea")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if "extraData" in str(e):
            print("💡 This is the POA error - middleware still not working")
        else:
            print("💡 Different error - check connection or RPC")

if __name__ == "__main__":
    asyncio.run(test_linea_connection())
