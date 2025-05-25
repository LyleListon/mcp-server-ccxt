#!/usr/bin/env python3
"""
Test Real DEX Integration

Tests the real DEX adapters with live data from Uniswap V3 and SushiSwap.
"""

import asyncio
import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_uniswap_v3():
    """Test Uniswap V3 adapter with real data."""
    print("🦄 Testing Uniswap V3 Integration")
    print("=" * 40)
    
    try:
        from dex.uniswap_v3_adapter import UniswapV3Adapter
        
        # Create adapter
        config = {
            'max_slippage': 0.5,
            'gas_limit': 300000
        }
        
        uniswap = UniswapV3Adapter(config)
        print("   ✅ Uniswap V3 adapter created")
        
        # Test connection
        print("1. Testing connection to Uniswap V3...")
        connected = await uniswap.connect()
        if connected:
            print("   ✅ Connected to Uniswap V3 successfully!")
        else:
            print("   ❌ Failed to connect to Uniswap V3")
            return False
        
        # Test getting pairs
        print("2. Fetching trading pairs...")
        pairs = await uniswap.get_pairs()
        print(f"   ✅ Fetched {len(pairs)} trading pairs")
        
        if pairs:
            # Show top 3 pairs
            print("   📊 Top 3 pairs by TVL:")
            for i, pair in enumerate(pairs[:3]):
                print(f"      {i+1}. {pair['base_token']}/{pair['quote_token']}")
                print(f"         Price: ${pair['price']:.6f}")
                print(f"         TVL: ${pair['tvl_usd']:,.2f}")
                print(f"         Volume 24h: ${pair['volume_24h_usd']:,.2f}")
        
        # Test getting specific price
        print("3. Testing price lookup...")
        btc_price = await uniswap.get_price('WBTC', 'USDC')
        if btc_price:
            print(f"   ✅ WBTC/USDC price: ${btc_price:,.2f}")
        else:
            print("   ⚠️  Could not get WBTC/USDC price")
        
        # Test getting quote
        print("4. Testing quote...")
        quote = await uniswap.get_quote('WBTC', 'USDC', 0.1)  # 0.1 WBTC
        if quote:
            print(f"   ✅ Quote for 0.1 WBTC:")
            print(f"      Expected output: {quote['expected_output']:.2f} USDC")
            print(f"      Slippage estimate: {quote['slippage_estimate']:.2f}%")
            print(f"      Gas estimate: {quote['gas_estimate']:,}")
        else:
            print("   ⚠️  Could not get quote")
        
        # Disconnect
        await uniswap.disconnect()
        print("   ✅ Disconnected from Uniswap V3")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Uniswap V3 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_sushiswap():
    """Test SushiSwap adapter with real data."""
    print("\n🍣 Testing SushiSwap Integration")
    print("=" * 40)
    
    try:
        from dex.sushiswap_adapter import SushiSwapAdapter
        
        # Create adapter
        config = {
            'max_slippage': 0.5,
            'gas_limit': 250000
        }
        
        sushiswap = SushiSwapAdapter(config)
        print("   ✅ SushiSwap adapter created")
        
        # Test connection
        print("1. Testing connection to SushiSwap...")
        connected = await sushiswap.connect()
        if connected:
            print("   ✅ Connected to SushiSwap successfully!")
        else:
            print("   ❌ Failed to connect to SushiSwap")
            return False
        
        # Test getting pairs
        print("2. Fetching trading pairs...")
        pairs = await sushiswap.get_pairs()
        print(f"   ✅ Fetched {len(pairs)} trading pairs")
        
        if pairs:
            # Show top 3 pairs
            print("   📊 Top 3 pairs by liquidity:")
            for i, pair in enumerate(pairs[:3]):
                print(f"      {i+1}. {pair['base_token']}/{pair['quote_token']}")
                print(f"         Price: ${pair['price']:.6f}")
                print(f"         Liquidity: ${pair['liquidity']:,.2f}")
                print(f"         Volume 24h: ${pair['volume_24h_usd']:,.2f}")
        
        # Test getting specific price
        print("3. Testing price lookup...")
        eth_price = await sushiswap.get_price('WETH', 'USDC')
        if eth_price:
            print(f"   ✅ WETH/USDC price: ${eth_price:,.2f}")
        else:
            print("   ⚠️  Could not get WETH/USDC price")
        
        # Test getting quote
        print("4. Testing quote...")
        quote = await sushiswap.get_quote('WETH', 'USDC', 1.0)  # 1 WETH
        if quote:
            print(f"   ✅ Quote for 1.0 WETH:")
            print(f"      Expected output: {quote['expected_output']:.2f} USDC")
            print(f"      Market price: ${quote['market_price']:,.2f}")
            print(f"      Actual price: ${quote['price']:,.2f}")
            print(f"      Slippage estimate: {quote['slippage_estimate']:.2f}%")
        else:
            print("   ⚠️  Could not get quote")
        
        # Disconnect
        await sushiswap.disconnect()
        print("   ✅ Disconnected from SushiSwap")
        
        return True
        
    except Exception as e:
        print(f"   ❌ SushiSwap test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_dex_manager():
    """Test DEX manager with multiple DEXs."""
    print("\n🔗 Testing DEX Manager")
    print("=" * 40)
    
    try:
        from dex.dex_manager import DEXManager
        
        # Create DEX manager
        config = {
            'dexs': {
                'uniswap_v3': {
                    'enabled': True,
                    'max_slippage': 0.5,
                    'gas_limit': 300000
                },
                'sushiswap': {
                    'enabled': True,
                    'max_slippage': 0.5,
                    'gas_limit': 250000
                }
            }
        }
        
        dex_manager = DEXManager(config)
        print("   ✅ DEX Manager created")
        
        # Test connecting to all DEXs
        print("1. Connecting to all DEXs...")
        connected = await dex_manager.connect_all()
        if connected:
            connected_dexs = dex_manager.get_connected_dexs()
            print(f"   ✅ Connected to {len(connected_dexs)} DEXs: {connected_dexs}")
        else:
            print("   ❌ Failed to connect to any DEXs")
            return False
        
        # Test cross-DEX price comparison
        print("2. Testing cross-DEX price comparison...")
        prices = await dex_manager.get_cross_dex_prices('WETH', 'USDC')
        print("   📊 WETH/USDC prices across DEXs:")
        for dex_name, price in prices.items():
            if price:
                print(f"      {dex_name}: ${price:,.2f}")
            else:
                print(f"      {dex_name}: No data")
        
        # Test arbitrage opportunity detection
        print("3. Scanning for arbitrage opportunities...")
        opportunities = await dex_manager.find_arbitrage_opportunities(min_profit_percentage=0.1)
        
        if opportunities:
            print(f"   🎯 Found {len(opportunities)} arbitrage opportunities!")
            
            # Show top 3 opportunities
            for i, opp in enumerate(opportunities[:3]):
                print(f"      {i+1}. {opp['base_token']}/{opp['quote_token']}")
                print(f"         Buy on {opp['buy_dex']} at ${opp['buy_price']:.6f}")
                print(f"         Sell on {opp['sell_dex']} at ${opp['sell_price']:.6f}")
                print(f"         Profit: {opp['profit_percentage']:.2f}%")
                print(f"         Est. profit: ${opp['estimated_profit_usd']:.2f}")
        else:
            print("   📊 No arbitrage opportunities found (this is normal)")
        
        # Disconnect
        await dex_manager.disconnect_all()
        print("   ✅ Disconnected from all DEXs")
        
        return True
        
    except Exception as e:
        print(f"   ❌ DEX Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all real DEX integration tests."""
    
    print("🚀 Real DEX Integration Test Suite")
    print("=" * 60)
    print("Testing live connections to Uniswap V3 and SushiSwap!")
    print("This will fetch real market data from The Graph APIs.")
    print("=" * 60)
    
    # Test individual DEXs
    uniswap_success = await test_uniswap_v3()
    sushiswap_success = await test_sushiswap()
    
    # Test DEX manager
    manager_success = await test_dex_manager()
    
    print("\n📊 FINAL TEST RESULTS")
    print("=" * 30)
    print(f"Uniswap V3: {'✅ PASS' if uniswap_success else '❌ FAIL'}")
    print(f"SushiSwap: {'✅ PASS' if sushiswap_success else '❌ FAIL'}")
    print(f"DEX Manager: {'✅ PASS' if manager_success else '❌ FAIL'}")
    
    if uniswap_success and sushiswap_success and manager_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 Real DEX integration is OPERATIONAL!")
        print("💰 Ready to find real arbitrage opportunities!")
        print("\nNext steps:")
        print("1. ✅ Real DEX connections working")
        print("2. ✅ Live market data flowing")
        print("3. ✅ Cross-DEX price comparison operational")
        print("4. ✅ Arbitrage detection ready")
        print("5. 🔄 Integrate with Enhanced Arbitrage Bot")
        print("6. 🔄 Add wallet connection for real trading")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("This might be due to network issues or API rate limits.")
        print("Try running the tests again in a few minutes.")
    
    return uniswap_success and sushiswap_success and manager_success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest suite crashed: {e}")
        sys.exit(1)
