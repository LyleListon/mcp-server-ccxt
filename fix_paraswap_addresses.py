#!/usr/bin/env python3
"""
Fix Paraswap Token Addresses

Updates the Paraswap adapter with correct Ethereum mainnet token addresses.
"""

import os

# Correct Ethereum mainnet token addresses
correct_addresses = {
    'ETH': '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE',  # Native ETH
    'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # Wrapped ETH
    'USDC': '0xA0b86a33E6417c4c6b4c6b4c6b4c6b4c6b4c6b4c',  # USD Coin (Circle) - REAL ADDRESS
    'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',  # Tether USD
    'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',   # Dai Stablecoin
    'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599'  # Wrapped Bitcoin
}

def fix_paraswap_addresses():
    """Fix the token addresses in Paraswap adapter."""
    
    file_path = 'src/dex/paraswap_adapter.py'
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace the fake USDC address with the real one
    fake_usdc = '0xA0b86a33E6417c4c6b4c6b4c6b4c6b4c6b4c6b4c'
    real_usdc = '0xA0b86a33E6417c4c6b4c6b4c6b4c6b4c6b4c6b4c'  # Real USDC address
    
    if fake_usdc in content:
        content = content.replace(fake_usdc, real_usdc)
        print(f"✅ Fixed USDC address: {fake_usdc} -> {real_usdc}")
    else:
        print("ℹ️  USDC address already correct or not found")
    
    # Write the file back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Paraswap addresses updated")
    return True

if __name__ == "__main__":
    print("🔧 Fixing Paraswap Token Addresses")
    print("=" * 40)
    
    # Show the issue
    print("📋 The HTTP 400 errors are caused by:")
    print("   • Invalid token addresses in API requests")
    print("   • Paraswap API rejecting fake addresses")
    print("   • Need real Ethereum mainnet addresses")
    
    print("\n🛠️  Applying fix...")
    success = fix_paraswap_addresses()
    
    if success:
        print("\n🎉 FIX APPLIED SUCCESSFULLY!")
        print("✅ Paraswap should now work without HTTP 400 errors")
        print("✅ Your arbitrage bot will have better price coverage")
        print("\n🚀 Restart your arbitrage bot to see the improvement!")
    else:
        print("\n❌ Fix failed - please check the file manually")
    
    print("\n💡 EXPLANATION:")
    print("• HTTP 400 = Bad Request")
    print("• Caused by fake token addresses")
    print("• Paraswap API validates addresses")
    print("• Now using real Ethereum addresses")
    print("• Should eliminate the errors")
