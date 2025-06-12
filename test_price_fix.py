#!/usr/bin/env python3
"""
Test the ETH price calculation fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.execution.real_dex_executor import RealDEXExecutor

async def test_price_calculation():
    """Test the ETH price calculation"""
    
    print("🧪 Testing ETH Price Calculation Fix...")
    
    # Create executor instance
    executor = RealDEXExecutor()
    
    try:
        # Test the price calculation
        eth_price = await executor._get_eth_price_usd()
        
        print(f"💰 ETH Price from our calculation: ${eth_price:.2f}")
        print(f"📊 Etherscan reference price: $1912.96")
        
        # Calculate error
        error_pct = ((eth_price / 1912.96) - 1) * 100
        print(f"📈 Error: {error_pct:+.1f}%")
        
        # Check if it's reasonable
        if abs(error_pct) < 5:
            print("✅ Price calculation looks good! (within 5%)")
        elif abs(error_pct) < 10:
            print("⚠️  Price calculation is within 10% - acceptable")
        else:
            print("❌ Price calculation is still off by more than 10%")
            
        return eth_price
        
    except Exception as e:
        print(f"❌ Error testing price calculation: {e}")
        return None

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_price_calculation())
