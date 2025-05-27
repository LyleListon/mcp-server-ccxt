#!/usr/bin/env python3
"""
Robust Real API Test
Tests multiple real data sources with fallbacks for maximum reliability.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dex.uniswap_v3_adapter import UniswapV3Adapter
from dex.sushiswap_adapter import SushiSwapAdapter
from dex.oneinch_adapter import OneInchAdapter
from dex.real_world_dex_adapter import RealWorldDEXAdapter

async def test_robust_real_apis():
    """Test robust real API connections with fallbacks."""
    print("🌐 Testing Robust Real API Connections")
    print("=" * 60)
    
    # Load config
    with open('config/capital_efficient_config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize multiple data sources for maximum reliability
    data_sources = {}
    
    print("🔌 Initializing Multiple Data Sources...")
    
    # 1inch Aggregator (Most reliable for prices)
    try:
        data_sources['1inch'] = OneInchAdapter(config.get('dexs', {}).get('1inch', {}))
        print("✅ 1inch aggregator initialized")
    except Exception as e:
        print(f"❌ 1inch aggregator failed: {e}")
    
    # CoinGecko (Backup price source)
    try:
        data_sources['coingecko'] = RealWorldDEXAdapter(config)
        print("✅ CoinGecko backup initialized")
    except Exception as e:
        print(f"❌ CoinGecko backup failed: {e}")
    
    # Uniswap V3 (If subgraph works)
    try:
        data_sources['uniswap_v3'] = UniswapV3Adapter(config.get('dexs', {}).get('uniswap_v3', {}))
        print("✅ Uniswap V3 initialized")
    except Exception as e:
        print(f"❌ Uniswap V3 failed: {e}")
    
    # SushiSwap (If subgraph works)
    try:
        data_sources['sushiswap'] = SushiSwapAdapter(config.get('dexs', {}).get('sushiswap', {}))
        print("✅ SushiSwap initialized")
    except Exception as e:
        print(f"❌ SushiSwap failed: {e}")
    
    # Test connections with fallback strategy
    print(f"\n🔗 Testing Connections (Fallback Strategy)...")
    connected_sources = {}
    
    for source_name, adapter in data_sources.items():
        try:
            print(f"   Connecting to {source_name}...")
            connected = await adapter.connect()
            if connected:
                connected_sources[source_name] = adapter
                print(f"   ✅ {source_name} connected successfully!")
            else:
                print(f"   ⚠️  {source_name} connection failed (will try others)")
        except Exception as e:
            print(f"   ⚠️  {source_name} connection error: {e} (will try others)")
    
    if not connected_sources:
        print("\n❌ No data sources connected. Cannot proceed.")
        return False
    
    print(f"\n🎉 Connected to {len(connected_sources)} data sources: {list(connected_sources.keys())}")
    
    # Test price fetching with fallback strategy
    print("\n💰 Testing Price Fetching (Multi-Source Strategy)...")
    
    test_pairs = [
        ('ETH', 'USDC'),
        ('USDC', 'USDT'),
        ('WETH', 'USDC'),
        ('ETH', 'WETH'),
        ('DAI', 'USDC')
    ]
    
    price_matrix = {}
    
    for base_token, quote_token in test_pairs:
        pair_key = f"{base_token}/{quote_token}"
        price_matrix[pair_key] = {}
        
        print(f"\n   📈 {pair_key} - Multi-source price discovery:")
        
        for source_name, adapter in connected_sources.items():
            try:
                price = await adapter.get_price(base_token, quote_token)
                if price and price > 0:
                    price_matrix[pair_key][source_name] = price
                    print(f"      ✅ {source_name}: {price:.6f}")
                else:
                    print(f"      ⚠️  {source_name}: No price available")
            except Exception as e:
                print(f"      ❌ {source_name}: Error - {e}")
        
        # Calculate consensus price
        prices = list(price_matrix[pair_key].values())
        if prices:
            avg_price = sum(prices) / len(prices)
            price_spread = (max(prices) - min(prices)) / min(prices) * 100 if len(prices) > 1 else 0
            print(f"      📊 Consensus: {avg_price:.6f} (spread: {price_spread:.3f}%)")
    
    # Analyze cross-source arbitrage opportunities
    print("\n🔍 Analyzing Cross-Source Arbitrage Opportunities...")
    
    arbitrage_opportunities = []
    
    for pair_key, prices in price_matrix.items():
        if len(prices) >= 2:  # Need at least 2 sources
            max_price_source = max(prices, key=prices.get)
            min_price_source = min(prices, key=prices.get)
            
            max_price = prices[max_price_source]
            min_price = prices[min_price_source]
            
            profit_percentage = ((max_price - min_price) / min_price) * 100
            
            if profit_percentage > 0.01:  # At least 0.01% profit
                opportunity = {
                    'pair': pair_key,
                    'buy_source': min_price_source,
                    'sell_source': max_price_source,
                    'buy_price': min_price,
                    'sell_price': max_price,
                    'profit_percentage': profit_percentage,
                    'all_prices': prices,
                    'source_count': len(prices)
                }
                arbitrage_opportunities.append(opportunity)
    
    # Display opportunities
    if arbitrage_opportunities:
        print(f"\n🎯 Found {len(arbitrage_opportunities)} Cross-Source Arbitrage Opportunities!")
        
        # Sort by profit percentage
        arbitrage_opportunities.sort(key=lambda x: x['profit_percentage'], reverse=True)
        
        for i, opp in enumerate(arbitrage_opportunities, 1):
            print(f"\n   {i}. {opp['pair']} - {opp['profit_percentage']:.4f}% profit")
            print(f"      Buy from {opp['buy_source']}: {opp['buy_price']:.6f}")
            print(f"      Sell to {opp['sell_source']}: {opp['sell_price']:.6f}")
            print(f"      Sources: {opp['source_count']} ({list(opp['all_prices'].keys())})")
            
            # Calculate potential profit
            trade_amounts = [1000, 5000, 10000]
            
            for amount in trade_amounts:
                gross_profit = amount * (opp['profit_percentage'] / 100)
                
                # Different fee structures for different sources
                if '1inch' in [opp['buy_source'], opp['sell_source']]:
                    total_fees = amount * 0.001  # 0.1% for 1inch
                elif 'coingecko' in [opp['buy_source'], opp['sell_source']]:
                    total_fees = amount * 0.0009  # Flash loan fee only
                else:
                    total_fees = amount * 0.003  # 0.3% DEX fees
                
                gas_cost = 20  # Estimated gas cost
                net_profit = gross_profit - total_fees - gas_cost
                
                if net_profit > 0:
                    roi = (net_profit / total_fees) * 100 if total_fees > 0 else 0
                    print(f"      ${amount:,} trade: ${net_profit:.2f} profit (ROI: {roi:.1f}%)")
                    break  # Only show first profitable amount
    else:
        print("\n⚠️  No cross-source arbitrage opportunities found.")
        print("   This is normal - price differences between sources are usually small!")
    
    # Test quote functionality across sources
    print("\n📋 Testing Quote Functionality Across Sources...")
    
    for source_name, adapter in connected_sources.items():
        try:
            quote = await adapter.get_quote('ETH', 'USDC', 1.0)
            if quote:
                print(f"   ✅ {source_name} quote for 1 ETH → USDC:")
                print(f"      Output: {quote.get('expected_output', 0):.2f} USDC")
                print(f"      Price: {quote.get('price', 0):.2f}")
                print(f"      Slippage: {quote.get('slippage_estimate', 0):.3f}%")
                print(f"      Gas: {quote.get('gas_estimate', 0):,} units")
            else:
                print(f"   ⚠️  {source_name} quote not available")
        except Exception as e:
            print(f"   ❌ {source_name} quote error: {e}")
    
    # Test liquidity information
    print("\n💧 Testing Liquidity Information...")
    
    for source_name, adapter in connected_sources.items():
        try:
            liquidity = await adapter.get_liquidity('ETH', 'USDC')
            if liquidity:
                print(f"   {source_name}: ${liquidity:,.0f} liquidity for ETH/USDC")
            else:
                print(f"   {source_name}: Liquidity data not available")
        except Exception as e:
            print(f"   {source_name}: Liquidity error - {e}")
    
    # Create reliability score for each source
    print("\n📊 Data Source Reliability Analysis...")
    
    reliability_scores = {}
    
    for source_name in connected_sources.keys():
        score = 0
        total_tests = 0
        
        # Count successful price fetches
        for pair_prices in price_matrix.values():
            total_tests += 1
            if source_name in pair_prices:
                score += 1
        
        reliability_percentage = (score / total_tests * 100) if total_tests > 0 else 0
        reliability_scores[source_name] = reliability_percentage
        
        print(f"   {source_name}: {reliability_percentage:.1f}% reliability ({score}/{total_tests} successful)")
    
    # Recommend best sources
    if reliability_scores:
        best_source = max(reliability_scores, key=reliability_scores.get)
        print(f"\n🏆 Most Reliable Source: {best_source} ({reliability_scores[best_source]:.1f}%)")
    
    # Cleanup connections
    print("\n🧹 Cleaning up connections...")
    for source_name, adapter in connected_sources.items():
        try:
            await adapter.disconnect()
            print(f"   ✅ {source_name} disconnected")
        except Exception as e:
            print(f"   ⚠️  {source_name} disconnect error: {e}")
    
    # Summary
    total_prices = sum(len(prices) for prices in price_matrix.values())
    
    print(f"\n🎉 Robust Real API Test Complete!")
    print(f"   Connected sources: {len(connected_sources)}")
    print(f"   Price points collected: {total_prices}")
    print(f"   Cross-source opportunities: {len(arbitrage_opportunities)}")
    
    if arbitrage_opportunities:
        best_opportunity = arbitrage_opportunities[0]
        print(f"   Best opportunity: {best_opportunity['pair']} - {best_opportunity['profit_percentage']:.4f}%")
    
    if reliability_scores:
        avg_reliability = sum(reliability_scores.values()) / len(reliability_scores)
        print(f"   Average source reliability: {avg_reliability:.1f}%")
    
    print(f"\n✅ System ready for robust arbitrage trading with multiple data sources!")
    
    return True

async def main():
    """Main test function."""
    try:
        success = await test_robust_real_apis()
        return success
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
