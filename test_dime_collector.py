#!/usr/bin/env python3
"""
Dime Collector Test
Tests the aggressive dime collection strategy for small but frequent profits.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feeds.real_price_feeds import RealPriceFeeds
from execution.arbitrage_executor import ArbitrageExecutor

async def test_dime_collector():
    """Test the dime collector strategy."""
    print("🪙 MayArbi DIME COLLECTOR Test")
    print("=" * 60)
    print("💰 'A dime is profit!' - Aggressive small profit strategy")
    print("🎯 Target: 0.01%+ opportunities (10 cents minimum)")
    print("⚡ Fast execution: 15 second scans")
    print("📈 Volume strategy: Many small wins = Big profits")
    print("=" * 60)

    # Load config
    with open('config/capital_efficient_config.json', 'r') as f:
        config = json.load(f)

    # Override config for dime collecting
    config['execution'] = {
        'min_profit_usd': 0.10,  # 10 cents minimum!
        'max_trade_size_usd': 2000,  # Smaller trades
        'min_profit_percentage': 0.01,  # 0.01% minimum
        'max_slippage_percentage': 0.3,  # Tight slippage
        'execution_timeout_seconds': 10  # Fast execution
    }

    # Initialize components
    print("\n🔌 Initializing Dime Collector System...")

    price_feeds = RealPriceFeeds(config)
    executor = ArbitrageExecutor(config)

    # Connect to price feeds
    print("   Connecting to price feeds...")
    connected = await price_feeds.connect()

    if not connected:
        print("❌ Failed to connect to price feeds")
        return False

    print("✅ Dime Collector System Ready!")
    print(f"   Minimum profit: ${config['execution']['min_profit_usd']}")
    print(f"   Maximum trade size: ${config['execution']['max_trade_size_usd']:,}")
    print(f"   Minimum profit %: {config['execution']['min_profit_percentage']}%")

    # Test aggressive opportunity detection
    print(f"\n🔍 Scanning for DIME Opportunities...")

    opportunities = await price_feeds.get_real_arbitrage_opportunities(min_profit_percentage=0.005)  # 0.005% = super aggressive

    if opportunities:
        print(f"🎯 Found {len(opportunities)} Dime Opportunities!")

        # Categorize opportunities by profit size
        dimes = []  # $0.10 - $1.00
        quarters = []  # $1.00 - $5.00
        dollars = []  # $5.00+

        for opp in opportunities:
            # Calculate profit for $1000 trade
            trade_size = 1000
            gross_profit = trade_size * (opp['profit_percentage'] / 100)
            costs = 5  # $5 estimated costs
            net_profit = gross_profit - costs

            if net_profit >= 5.0:
                dollars.append((opp, net_profit))
            elif net_profit >= 1.0:
                quarters.append((opp, net_profit))
            elif net_profit >= 0.10:
                dimes.append((opp, net_profit))

        print(f"\n💰 Opportunity Categories:")
        print(f"   🪙 Dimes ($0.10-$1.00): {len(dimes)} opportunities")
        print(f"   🪙 Quarters ($1.00-$5.00): {len(quarters)} opportunities")
        print(f"   💵 Dollars ($5.00+): {len(dollars)} opportunities")

        # Show dime opportunities
        if dimes:
            print(f"\n🪙 DIME Opportunities (The Money Makers!):")
            for i, (opp, profit) in enumerate(dimes[:5], 1):
                print(f"   {i}. {opp['token']} {opp['direction']} - {opp['profit_percentage']:.4f}%")
                print(f"      $1K trade = ${profit:.2f} profit")

        # Show quarter opportunities
        if quarters:
            print(f"\n🪙 QUARTER Opportunities:")
            for i, (opp, profit) in enumerate(quarters[:3], 1):
                print(f"   {i}. {opp['token']} {opp['direction']} - {opp['profit_percentage']:.3f}%")
                print(f"      $1K trade = ${profit:.2f} profit")

        # Show dollar opportunities
        if dollars:
            print(f"\n💵 DOLLAR Opportunities:")
            for i, (opp, profit) in enumerate(dollars[:3], 1):
                print(f"   {i}. {opp['token']} {opp['direction']} - {opp['profit_percentage']:.3f}%")
                print(f"      $1K trade = ${profit:.2f} profit")

        # Test execution on dime opportunities
        print(f"\n🚀 Testing Dime Execution...")

        total_simulated_profit = 0
        successful_executions = 0

        # Execute top 5 dime opportunities
        if dimes:
            test_opportunities = [opp for opp, profit in dimes[:5]]
        else:
            test_opportunities = opportunities[:5]

        for i, opp in enumerate(test_opportunities, 1):
            print(f"\n   Executing dime #{i}: {opp['token']} - {opp['profit_percentage']:.4f}%")

            result = await executor.execute_opportunity(opp)

            if result.success:
                successful_executions += 1
                total_simulated_profit += result.profit_usd
                print(f"   ✅ Success: ${result.profit_usd:.2f} profit in {result.execution_time_ms}ms")
            else:
                print(f"   ❌ Failed: {result.error_message}")

        # Calculate dime collection potential
        print(f"\n📊 Dime Collection Analysis:")

        if successful_executions > 0:
            avg_profit_per_dime = total_simulated_profit / successful_executions
            success_rate = (successful_executions / len(test_opportunities)) * 100

            print(f"   Success rate: {success_rate:.1f}%")
            print(f"   Average profit per dime: ${avg_profit_per_dime:.2f}")
            print(f"   Total simulated profit: ${total_simulated_profit:.2f}")

            # Project daily earnings
            total_dimes_available = len(dimes) + len(quarters) + len(dollars)

            scenarios = [
                {"name": "Conservative", "dimes_per_hour": 2, "hours_per_day": 8},
                {"name": "Moderate", "dimes_per_hour": 4, "hours_per_day": 12},
                {"name": "Aggressive", "dimes_per_hour": 6, "hours_per_day": 16}
            ]

            print(f"\n💰 Daily Dime Collection Projections:")

            for scenario in scenarios:
                daily_dimes = scenario['dimes_per_hour'] * scenario['hours_per_day']
                daily_profit = daily_dimes * avg_profit_per_dime * (success_rate / 100)
                monthly_profit = daily_profit * 30

                print(f"   {scenario['name']}: {daily_dimes} dimes/day × "
                      f"${avg_profit_per_dime:.2f} × {success_rate:.0f}% = "
                      f"${daily_profit:.2f}/day (${monthly_profit:,.0f}/month)")

        # Dime stacking demonstration
        print(f"\n🪙 The Power of Dime Stacking:")

        dime_scenarios = [
            {"dimes_per_day": 20, "avg_profit": 0.50},
            {"dimes_per_day": 50, "avg_profit": 0.75},
            {"dimes_per_day": 100, "avg_profit": 1.00}
        ]

        for scenario in dime_scenarios:
            daily = scenario['dimes_per_day'] * scenario['avg_profit']
            weekly = daily * 7
            monthly = daily * 30
            yearly = daily * 365

            print(f"   {scenario['dimes_per_day']} dimes/day × ${scenario['avg_profit']:.2f} = "
                  f"${daily:.0f}/day, ${weekly:.0f}/week, ${monthly:,.0f}/month, ${yearly:,.0f}/year")

        # Best dime opportunity analysis
        if dimes:
            best_dime = max(dimes, key=lambda x: x[1])
            opp, profit = best_dime

            print(f"\n🏆 Best Dime Opportunity:")
            print(f"   Token: {opp['token']}")
            print(f"   Route: {opp['direction']}")
            print(f"   Profit: {opp['profit_percentage']:.4f}% (${profit:.2f} on $1K)")
            print(f"   Frequency potential: Every 15-30 seconds")

            # Scale analysis
            print(f"   Scale potential:")
            for trade_size in [500, 1000, 2000]:
                scaled_profit = trade_size * (opp['profit_percentage'] / 100) - 5  # $5 costs
                if scaled_profit > 0:
                    print(f"      ${trade_size:,} trade: ${scaled_profit:.2f} profit")

    else:
        print("⚠️  No dime opportunities found at this moment")
        print("   Try lowering the minimum profit threshold even more!")

    # System recommendations
    print(f"\n🎯 Dime Collector Recommendations:")

    if opportunities:
        print(f"   ✅ {len(opportunities)} opportunities detected - dime collection viable!")
        print(f"   🚀 Implement 10-15 second scanning for maximum dime capture")
        print(f"   💰 Focus on volume: 50-100 small trades > 1 big trade")
        print(f"   ⚡ Optimize for speed: Fast execution beats big profits")
        print(f"   🎯 Target stablecoins: USDT/USDC/DAI have most dime opportunities")

    print(f"   📈 Dime collection advantages:")
    print(f"      • Lower competition (most bots ignore small profits)")
    print(f"      • More frequent opportunities")
    print(f"      • Lower risk per trade")
    print(f"      • Steady income stream")
    print(f"      • Compounds quickly with volume")

    # Cleanup
    await price_feeds.disconnect()

    print(f"\n🎉 Dime Collector Test Complete!")
    print(f"   Remember: 'A dime is profit!' 🪙")
    print(f"   Stack those dimes and watch them turn into dollars! 💰")

    return True

async def main():
    """Main test function."""
    try:
        success = await test_dime_collector()
        return success
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
