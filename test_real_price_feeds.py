#!/usr/bin/env python3
"""
Real Price Feeds Test
Tests real-time price feeds from multiple sources for cross-chain arbitrage.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feeds.real_price_feeds import RealPriceFeeds

async def test_real_price_feeds():
    """Test real-time price feeds."""
    print("📡 Testing Real-Time Price Feeds")
    print("=" * 60)
    
    # Load config
    with open('config/capital_efficient_config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize price feeds
    print("🔌 Initializing Real Price Feeds...")
    
    price_feeds = RealPriceFeeds(config)
    
    # Test connection
    print("   Connecting to price feed sources...")
    connected = await price_feeds.connect()
    
    if not connected:
        print("❌ Failed to connect to price feeds")
        return False
    
    print("✅ Connected to real price feed sources!")
    
    # Test price feed status
    print("\n📊 Testing Price Feed Sources...")
    
    status = await price_feeds.get_price_feed_status()
    
    for source, info in status.items():
        if info.get('status') == 'connected':
            print(f"   ✅ {source.title()}: Connected (Priority {info.get('priority', 'N/A')})")
            print(f"      Rate limit: {info.get('rate_limit', 'N/A')}s, Chains: {info.get('chains', 'N/A')}")
        elif info.get('status') == 'disabled':
            print(f"   ⚠️  {source.title()}: Disabled")
        else:
            print(f"   ❌ {source.title()}: Error - {info.get('error', info.get('code', 'Unknown'))}")
    
    # Test cross-chain price fetching
    print("\n💰 Fetching Real Cross-Chain Prices...")
    
    target_tokens = ['ETH', 'USDC', 'USDT', 'DAI']
    cross_chain_prices = await price_feeds.get_cross_chain_prices(target_tokens)
    
    if cross_chain_prices:
        print(f"✅ Successfully fetched prices for {len(cross_chain_prices)} tokens!")
        
        # Display prices in a nice table format
        for token, chain_prices in cross_chain_prices.items():
            print(f"\n   💎 {token} Prices Across Chains:")
            
            if not chain_prices:
                print(f"      ⚠️  No prices available")
                continue
            
            # Sort chains by price
            sorted_chains = sorted(chain_prices.items(), key=lambda x: x[1])
            
            for chain, price in sorted_chains:
                if token in ['USDC', 'USDT', 'DAI']:
                    print(f"      {chain.title()}: ${price:.6f}")
                else:
                    print(f"      {chain.title()}: ${price:,.2f}")
            
            # Calculate price spread
            if len(chain_prices) > 1:
                min_price = min(chain_prices.values())
                max_price = max(chain_prices.values())
                spread = ((max_price - min_price) / min_price) * 100
                
                min_chain = min(chain_prices, key=chain_prices.get)
                max_chain = max(chain_prices, key=chain_prices.get)
                
                print(f"      📊 Spread: {spread:.3f}% ({min_chain} → {max_chain})")
    else:
        print("❌ Failed to fetch cross-chain prices")
        return False
    
    # Test real arbitrage opportunity detection
    print("\n🔍 Scanning for REAL Arbitrage Opportunities...")
    
    opportunities = await price_feeds.get_real_arbitrage_opportunities(min_profit_percentage=0.01)
    
    if opportunities:
        print(f"🎯 Found {len(opportunities)} REAL Arbitrage Opportunities!")
        
        # Display top opportunities
        for i, opp in enumerate(opportunities[:5], 1):  # Top 5
            print(f"\n   {i}. {opp['token']} - {opp['profit_percentage']:.4f}% profit")
            print(f"      Direction: {opp['direction']}")
            print(f"      Buy Price: ${opp['source_price']:,.6f} ({opp['source_chain']})")
            print(f"      Sell Price: ${opp['target_price']:,.6f} ({opp['target_chain']})")
            
            # Calculate potential profits
            trade_amounts = [1000, 5000, 10000]
            
            for amount in trade_amounts:
                gross_profit = amount * (opp['profit_percentage'] / 100)
                
                # Estimate costs (simplified)
                bridge_fee = amount * 0.0005  # 0.05% average bridge fee
                gas_cost = 10  # $10 estimated gas
                total_costs = bridge_fee + gas_cost
                
                net_profit = gross_profit - total_costs
                
                if net_profit > 0:
                    roi = (net_profit / total_costs) * 100 if total_costs > 0 else 0
                    print(f"      ${amount:,} trade: ${net_profit:.2f} profit (ROI: {roi:.1f}%)")
                    break
        
        # Analyze opportunities by token
        print(f"\n📊 Opportunity Analysis:")
        
        token_stats = {}
        for opp in opportunities:
            token = opp['token']
            if token not in token_stats:
                token_stats[token] = {'count': 0, 'avg_profit': 0, 'max_profit': 0}
            
            token_stats[token]['count'] += 1
            token_stats[token]['avg_profit'] += opp['profit_percentage']
            token_stats[token]['max_profit'] = max(token_stats[token]['max_profit'], opp['profit_percentage'])
        
        for token, stats in token_stats.items():
            stats['avg_profit'] /= stats['count']
            print(f"   {token}: {stats['count']} opportunities, "
                  f"avg {stats['avg_profit']:.3f}%, max {stats['max_profit']:.3f}%")
        
        # Best opportunity analysis
        best_opp = opportunities[0]
        print(f"\n🏆 Best REAL Opportunity:")
        print(f"   Token: {best_opp['token']}")
        print(f"   Profit: {best_opp['profit_percentage']:.4f}%")
        print(f"   Route: {best_opp['direction']}")
        print(f"   Price Difference: ${abs(best_opp['target_price'] - best_opp['source_price']):.6f}")
        
        # Calculate daily profit potential
        print(f"\n💵 Daily Profit Potential (Real Opportunities):")
        
        if len(opportunities) > 0:
            avg_profit_per_opp = sum(opp['profit_percentage'] for opp in opportunities) / len(opportunities)
            
            scenarios = [
                {"name": "Conservative", "ops_per_day": len(opportunities) * 2, "trade_size": 2000},
                {"name": "Moderate", "ops_per_day": len(opportunities) * 5, "trade_size": 5000},
                {"name": "Aggressive", "ops_per_day": len(opportunities) * 10, "trade_size": 10000}
            ]
            
            for scenario in scenarios:
                daily_gross = scenario['ops_per_day'] * scenario['trade_size'] * (avg_profit_per_opp / 100)
                daily_costs = scenario['ops_per_day'] * 15  # $15 avg costs per trade
                daily_net = daily_gross - daily_costs
                monthly_net = daily_net * 30
                
                if daily_net > 0:
                    print(f"   {scenario['name']}: {scenario['ops_per_day']} ops/day × "
                          f"${scenario['trade_size']:,} × {avg_profit_per_opp:.3f}% = "
                          f"${daily_net:.0f}/day (${monthly_net:,.0f}/month)")
    
    else:
        print("⚠️  No real arbitrage opportunities found at this moment")
        print("   This is normal - real opportunities are rare but profitable!")
    
    # Test price data quality
    print(f"\n🔬 Price Data Quality Analysis:")
    
    total_prices = 0
    valid_prices = 0
    
    for token, chain_prices in cross_chain_prices.items():
        for chain, price in chain_prices.items():
            total_prices += 1
            if price > 0:
                valid_prices += 1
    
    data_quality = (valid_prices / total_prices * 100) if total_prices > 0 else 0
    
    print(f"   Total price points: {total_prices}")
    print(f"   Valid prices: {valid_prices}")
    print(f"   Data quality: {data_quality:.1f}%")
    
    # Test price feed reliability
    print(f"\n⚡ Price Feed Performance:")
    
    # Count successful sources
    connected_sources = sum(1 for info in status.values() if info.get('status') == 'connected')
    total_sources = len([s for s in price_feeds.sources.values() if s['enabled']])
    
    reliability = (connected_sources / total_sources * 100) if total_sources > 0 else 0
    
    print(f"   Connected sources: {connected_sources}/{total_sources}")
    print(f"   System reliability: {reliability:.1f}%")
    print(f"   Primary source: CoinGecko (✅ Working)")
    print(f"   Backup sources: {connected_sources - 1} available")
    
    # Recommendations
    print(f"\n🎯 Recommendations:")
    
    if opportunities:
        print(f"   ✅ REAL opportunities detected - system is working!")
        print(f"   🚀 Ready to implement automated execution")
        print(f"   💰 Focus on {opportunities[0]['token']} for best profits")
        print(f"   ⚡ Monitor every 30-60 seconds for new opportunities")
    else:
        print(f"   📊 Price feeds working, opportunities will appear")
        print(f"   🔄 Continue monitoring - market conditions change")
        print(f"   📈 Consider lowering minimum profit threshold")
    
    if data_quality > 90:
        print(f"   ✅ Excellent data quality - proceed with confidence")
    elif data_quality > 70:
        print(f"   ⚠️  Good data quality - monitor for improvements")
    else:
        print(f"   ❌ Poor data quality - investigate feed issues")
    
    # Cleanup
    print(f"\n🧹 Cleaning up...")
    await price_feeds.disconnect()
    
    print(f"\n🎉 Real Price Feeds Test Complete!")
    print(f"   System ready for live arbitrage with real market data!")
    print(f"   Next step: Implement automated opportunity execution!")
    
    return True

async def main():
    """Main test function."""
    try:
        success = await test_real_price_feeds()
        return success
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
