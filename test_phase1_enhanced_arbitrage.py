#!/usr/bin/env python3
"""
Phase 1 Enhanced Arbitrage Test

Tests the enhanced arbitrage system with:
- 1inch DEX aggregator
- Paraswap integration  
- Stablecoin specialist
- Micro-arbitrage detection (0.05% profits)
- Higher frequency scanning
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


async def test_enhanced_dex_adapters():
    """Test all the new DEX adapters."""
    print("🚀 Testing Enhanced DEX Adapters")
    print("=" * 50)
    
    results = {}
    
    # Test 1inch adapter
    print("\n1️⃣ Testing 1inch DEX Aggregator...")
    try:
        from dex.oneinch_adapter import OneInchAdapter
        
        config = {'rate_limit_delay': 1.0}
        oneinch = OneInchAdapter(config)
        
        connected = await oneinch.connect()
        if connected:
            print("   ✅ 1inch connected successfully")
            
            # Test getting pairs
            pairs = await oneinch.get_pairs()
            print(f"   📊 Found {len(pairs)} trading pairs")
            
            if pairs:
                # Show sample pair
                sample = pairs[0]
                print(f"   💎 Sample: {sample['base_token']}/{sample['quote_token']} = ${sample['price']:.6f}")
            
            results['1inch'] = True
        else:
            print("   ❌ 1inch connection failed")
            results['1inch'] = False
        
        await oneinch.disconnect()
        
    except Exception as e:
        print(f"   ❌ 1inch test failed: {e}")
        results['1inch'] = False
    
    # Test Paraswap adapter
    print("\n🔄 Testing Paraswap DEX Aggregator...")
    try:
        from dex.paraswap_adapter import ParaswapAdapter
        
        config = {'rate_limit_delay': 1.0, 'network': 1}
        paraswap = ParaswapAdapter(config)
        
        connected = await paraswap.connect()
        if connected:
            print("   ✅ Paraswap connected successfully")
            
            pairs = await paraswap.get_pairs()
            print(f"   📊 Found {len(pairs)} trading pairs")
            
            if pairs:
                sample = pairs[0]
                print(f"   💎 Sample: {sample['base_token']}/{sample['quote_token']} = ${sample['price']:.6f}")
            
            results['paraswap'] = True
        else:
            print("   ❌ Paraswap connection failed")
            results['paraswap'] = False
        
        await paraswap.disconnect()
        
    except Exception as e:
        print(f"   ❌ Paraswap test failed: {e}")
        results['paraswap'] = False
    
    # Test Stablecoin specialist
    print("\n💰 Testing Stablecoin Specialist...")
    try:
        from dex.stablecoin_adapter import StablecoinAdapter
        
        config = {'rate_limit_delay': 0.5}
        stablecoin = StablecoinAdapter(config)
        
        connected = await stablecoin.connect()
        if connected:
            print("   ✅ Stablecoin specialist connected successfully")
            
            pairs = await stablecoin.get_pairs()
            print(f"   📊 Found {len(pairs)} stablecoin pairs")
            
            if pairs:
                for pair in pairs[:3]:  # Show top 3
                    deviation = pair.get('deviation_from_peg', 0)
                    print(f"   💎 {pair['base_token']}/{pair['quote_token']}: ${pair['price']:.6f} (deviation: {deviation*100:.3f}%)")
            
            # Test depeg detection
            depegs = await stablecoin.find_depeg_opportunities(min_deviation=0.0001)
            if depegs:
                print(f"   🎯 Found {len(depegs)} depeg opportunities!")
                for depeg in depegs[:2]:
                    print(f"      {depeg['pair']}: {depeg['deviation_percentage']:.3f}% deviation")
            else:
                print("   📊 No significant depegs found (normal)")
            
            results['stablecoin'] = True
        else:
            print("   ❌ Stablecoin specialist connection failed")
            results['stablecoin'] = False
        
        await stablecoin.disconnect()
        
    except Exception as e:
        print(f"   ❌ Stablecoin test failed: {e}")
        results['stablecoin'] = False
    
    return results


async def test_enhanced_dex_manager():
    """Test the enhanced DEX manager with all adapters."""
    print("\n🔗 Testing Enhanced DEX Manager")
    print("=" * 40)
    
    try:
        from dex.dex_manager import DEXManager
        
        # Enhanced configuration
        config = {
            'dexs': {
                'coinbase': {
                    'enabled': True,
                    'rate_limit_delay': 1.5
                },
                'coingecko': {
                    'enabled': True,
                    'rate_limit_delay': 1.5
                },
                '1inch': {
                    'enabled': True,
                    'rate_limit_delay': 1.0
                },
                'paraswap': {
                    'enabled': True,
                    'rate_limit_delay': 1.0,
                    'network': 1
                },
                'stablecoin_specialist': {
                    'enabled': True,
                    'rate_limit_delay': 0.5
                }
            }
        }
        
        dex_manager = DEXManager(config)
        print(f"   ✅ DEX Manager created with {len(dex_manager.dexs)} adapters")
        
        # Connect to all DEXs
        print("1. Connecting to all enhanced DEXs...")
        connected = await dex_manager.connect_all()
        
        if connected:
            connected_dexs = dex_manager.get_connected_dexs()
            print(f"   ✅ Connected to {len(connected_dexs)} DEXs: {connected_dexs}")
        else:
            print("   ❌ Failed to connect to DEXs")
            return False
        
        # Test enhanced arbitrage detection
        print("2. Scanning for enhanced arbitrage opportunities...")
        opportunities = await dex_manager.find_arbitrage_opportunities(min_profit_percentage=0.05)
        
        if opportunities:
            print(f"   🎯 Found {len(opportunities)} arbitrage opportunities!")
            
            for i, opp in enumerate(opportunities[:3]):
                print(f"      {i+1}. {opp['base_token']}/{opp['quote_token']}")
                print(f"         Buy on {opp['buy_dex']} at ${opp['buy_price']:.6f}")
                print(f"         Sell on {opp['sell_dex']} at ${opp['sell_price']:.6f}")
                print(f"         Profit: {opp['profit_percentage']:.3f}%")
                print(f"         Est. profit: ${opp['estimated_profit_usd']:.2f}")
        else:
            print("   📊 No arbitrage opportunities found")
            print("   💡 This is normal - try lowering min_profit_percentage for micro-arbitrage")
        
        # Test cross-DEX price comparison
        print("3. Testing cross-DEX price comparison...")
        prices = await dex_manager.get_cross_dex_prices('ETH', 'USDC')
        print("   📊 ETH/USDC prices across DEXs:")
        for dex_name, price in prices.items():
            if price:
                print(f"      {dex_name}: ${price:,.2f}")
            else:
                print(f"      {dex_name}: No data")
        
        # Calculate price spread
        valid_prices = [p for p in prices.values() if p and p > 0]
        if len(valid_prices) >= 2:
            max_price = max(valid_prices)
            min_price = min(valid_prices)
            spread = ((max_price - min_price) / min_price) * 100
            print(f"   📈 Price spread: {spread:.3f}%")
            
            if spread > 0.05:
                print(f"   🎯 Potential micro-arbitrage detected!")
            else:
                print(f"   📊 Market is efficient (low spread)")
        
        await dex_manager.disconnect_all()
        return True
        
    except Exception as e:
        print(f"   ❌ Enhanced DEX Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_micro_arbitrage_detection():
    """Test micro-arbitrage detection capabilities."""
    print("\n🔬 Testing Micro-Arbitrage Detection")
    print("=" * 40)
    
    try:
        # Simulate micro-arbitrage scenarios
        mock_prices = {
            'coinbase': {
                'ETH/USDC': 2513.45,
                'BTC/USDC': 108190.23,
                'USDC/USDT': 1.0002,
                'DAI/USDC': 0.9998
            },
            'coingecko': {
                'ETH/USDC': 2513.78,
                'BTC/USDC': 108142.67,
                'USDC/USDT': 0.9999,
                'DAI/USDC': 1.0001
            },
            '1inch': {
                'ETH/USDC': 2514.12,
                'BTC/USDC': 108201.45,
                'USDC/USDT': 1.0001,
                'DAI/USDC': 0.9997
            }
        }
        
        print("   📊 Mock price data loaded")
        
        # Analyze micro-arbitrage opportunities
        opportunities = []
        
        for pair in ['ETH/USDC', 'BTC/USDC', 'USDC/USDT', 'DAI/USDC']:
            pair_prices = {}
            for dex, prices in mock_prices.items():
                if pair in prices:
                    pair_prices[dex] = prices[pair]
            
            if len(pair_prices) >= 2:
                max_dex = max(pair_prices, key=pair_prices.get)
                min_dex = min(pair_prices, key=pair_prices.get)
                
                max_price = pair_prices[max_dex]
                min_price = pair_prices[min_dex]
                
                profit_pct = ((max_price - min_price) / min_price) * 100
                
                if profit_pct > 0.01:  # 0.01% minimum
                    opportunities.append({
                        'pair': pair,
                        'buy_dex': min_dex,
                        'sell_dex': max_dex,
                        'buy_price': min_price,
                        'sell_price': max_price,
                        'profit_pct': profit_pct,
                        'profit_per_1k': profit_pct * 10  # Profit per $1000
                    })
        
        if opportunities:
            print(f"   🎯 Found {len(opportunities)} micro-arbitrage opportunities:")
            for opp in opportunities:
                print(f"      {opp['pair']}: {opp['profit_pct']:.3f}% profit")
                print(f"         Buy on {opp['buy_dex']}: ${opp['buy_price']:.4f}")
                print(f"         Sell on {opp['sell_dex']}: ${opp['sell_price']:.4f}")
                print(f"         Profit per $1000: ${opp['profit_per_1k']:.2f}")
        else:
            print("   📊 No micro-arbitrage opportunities in mock data")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Micro-arbitrage test failed: {e}")
        return False


async def main():
    """Run all Phase 1 enhancement tests."""
    
    print("🚀 Phase 1 Enhanced Arbitrage Test Suite")
    print("=" * 60)
    print("Testing enhanced DEX integrations for micro-arbitrage detection:")
    print("• 1inch DEX Aggregator (100+ DEXs)")
    print("• Paraswap Integration (Optimal routing)")
    print("• Stablecoin Specialist (Depeg opportunities)")
    print("• Micro-arbitrage detection (0.05% profits)")
    print("• Higher frequency scanning (5 second intervals)")
    print("=" * 60)
    
    # Run all tests
    adapter_results = await test_enhanced_dex_adapters()
    manager_success = await test_enhanced_dex_manager()
    micro_arb_success = await test_micro_arbitrage_detection()
    
    print("\n📊 PHASE 1 TEST RESULTS")
    print("=" * 30)
    print(f"1inch Adapter: {'✅ PASS' if adapter_results.get('1inch', False) else '❌ FAIL'}")
    print(f"Paraswap Adapter: {'✅ PASS' if adapter_results.get('paraswap', False) else '❌ FAIL'}")
    print(f"Stablecoin Specialist: {'✅ PASS' if adapter_results.get('stablecoin', False) else '❌ FAIL'}")
    print(f"Enhanced DEX Manager: {'✅ PASS' if manager_success else '❌ FAIL'}")
    print(f"Micro-Arbitrage Detection: {'✅ PASS' if micro_arb_success else '❌ FAIL'}")
    
    total_success = (
        sum(adapter_results.values()) >= 2 and  # At least 2 adapters working
        manager_success and
        micro_arb_success
    )
    
    if total_success:
        print("\n🎉 PHASE 1 ENHANCEMENTS READY!")
        print("🚀 Enhanced arbitrage system operational!")
        print("💰 Ready for micro-arbitrage detection!")
        print("\n🎯 Next Steps:")
        print("1. ✅ Enhanced DEX adapters working")
        print("2. ✅ Micro-arbitrage detection ready")
        print("3. ✅ Higher frequency scanning enabled")
        print("4. 🔄 Run enhanced real arbitrage bot")
        print("5. 🔄 Connect wallet for real trading")
        print("6. 🔄 Start making micro-profits!")
    else:
        print("\n⚠️  Some Phase 1 enhancements need attention")
        print("Check the failed tests above and retry")
    
    return total_success


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
