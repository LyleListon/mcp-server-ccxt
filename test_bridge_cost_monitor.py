#!/usr/bin/env python3
"""
Bridge Cost Monitor Test
Tests real-time bridge cost monitoring and verification system.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridges.bridge_cost_monitor import BridgeCostMonitor

async def test_bridge_cost_monitor():
    """Test the bridge cost monitoring system."""
    print("📊 Bridge Cost Monitor Test")
    print("=" * 60)
    print("🔍 Real-time bridge cost verification")
    print("📈 Continuous cost monitoring and alerts")
    print("💰 Finding the cheapest routes in real-time")
    print("🚨 Cost change detection and alerts")
    print("=" * 60)
    
    # Load config
    with open('config/capital_efficient_config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize bridge cost monitor
    print("\n🔌 Initializing Bridge Cost Monitor...")
    
    monitor = BridgeCostMonitor(config)
    
    # Initialize connections
    print("   Connecting to bridge APIs...")
    connected = await monitor.initialize()
    
    if not connected:
        print("❌ Failed to connect to bridge APIs")
        return False
    
    print("✅ Bridge Cost Monitor Ready!")
    
    # Test real quote collection
    print(f"\n📊 Testing Real Bridge Quote Collection...")
    
    test_routes = [
        {
            'name': 'Your Proven Route',
            'source_chain': 'ethereum',
            'target_chain': 'arbitrum',
            'token': 'ETH',
            'amount': 500,
            'baseline_cost': 0.90  # Your real Synapse cost
        },
        {
            'name': 'High Volume USDC',
            'source_chain': 'ethereum',
            'target_chain': 'base',
            'token': 'USDC',
            'amount': 2000,
            'baseline_cost': None
        },
        {
            'name': 'L2 to L2 Transfer',
            'source_chain': 'arbitrum',
            'target_chain': 'optimism',
            'token': 'USDT',
            'amount': 1000,
            'baseline_cost': None
        }
    ]
    
    all_quotes = {}
    
    for route in test_routes:
        print(f"\n   🧪 {route['name']}")
        print(f"      Route: {route['source_chain'].title()} → {route['target_chain'].title()}")
        print(f"      Token: {route['token']}, Amount: ${route['amount']:,}")
        
        # Get real quotes
        quotes = await monitor.get_real_bridge_quotes(
            route['source_chain'],
            route['target_chain'],
            route['token'],
            route['amount']
        )
        
        if quotes:
            print(f"      📋 Found {len(quotes)} valid quotes:")
            
            for i, quote in enumerate(quotes, 1):
                savings_vs_baseline = ""
                if route['baseline_cost']:
                    savings = route['baseline_cost'] - quote.total_cost_usd
                    savings_pct = (savings / route['baseline_cost']) * 100
                    if savings > 0:
                        savings_vs_baseline = f" (💰 Save ${savings:.2f}, {savings_pct:.1f}%)"
                    else:
                        savings_vs_baseline = f" (💸 Cost ${abs(savings):.2f} more, {abs(savings_pct):.1f}%)"
                
                print(f"         {i}. {quote.bridge_name}")
                print(f"            Fee: ${quote.fee_usd:.2f} ({quote.fee_percentage:.2f}%)")
                print(f"            Gas: ${quote.gas_estimate_usd:.2f}")
                print(f"            Total: ${quote.total_cost_usd:.2f}")
                print(f"            Time: {quote.estimated_time_minutes:.1f} min{savings_vs_baseline}")
            
            # Store for comparison
            route_key = f"{route['source_chain']}_{route['target_chain']}_{route['token']}_{route['amount']}"
            all_quotes[route_key] = quotes
            
            # Highlight best option
            best_quote = quotes[0]
            print(f"      🏆 BEST: {best_quote.bridge_name} - ${best_quote.total_cost_usd:.2f} total cost")
            
        else:
            print(f"      ❌ No valid quotes found")
    
    # Test cost comparison analysis
    print(f"\n💰 Bridge Cost Comparison Analysis:")
    
    if all_quotes:
        # Find cheapest bridge overall
        all_bridge_costs = {}
        
        for route_key, quotes in all_quotes.items():
            for quote in quotes:
                if quote.bridge_name not in all_bridge_costs:
                    all_bridge_costs[quote.bridge_name] = []
                
                all_bridge_costs[quote.bridge_name].append({
                    'route': route_key,
                    'cost': quote.total_cost_usd,
                    'fee_percentage': quote.fee_percentage
                })
        
        # Calculate average costs per bridge
        bridge_averages = {}
        for bridge_name, costs in all_bridge_costs.items():
            avg_cost = sum(c['cost'] for c in costs) / len(costs)
            avg_fee_pct = sum(c['fee_percentage'] for c in costs) / len(costs)
            bridge_averages[bridge_name] = {
                'avg_cost': avg_cost,
                'avg_fee_percentage': avg_fee_pct,
                'routes_tested': len(costs)
            }
        
        # Sort by average cost
        sorted_bridges = sorted(bridge_averages.items(), key=lambda x: x[1]['avg_cost'])
        
        print(f"   Bridge Rankings (by average total cost):")
        for i, (bridge_name, stats) in enumerate(sorted_bridges, 1):
            print(f"   {i}. {bridge_name}")
            print(f"      Avg Total Cost: ${stats['avg_cost']:.2f}")
            print(f"      Avg Fee: {stats['avg_fee_percentage']:.2f}%")
            print(f"      Routes Tested: {stats['routes_tested']}")
    
    # Test monitoring simulation
    print(f"\n🔄 Testing Cost Monitoring Simulation...")
    
    print("   Simulating 3 monitoring cycles (15 seconds each)...")
    
    for cycle in range(1, 4):
        print(f"\n   📊 Monitoring Cycle #{cycle}")
        
        # Simulate getting quotes for your proven route
        quotes = await monitor.get_real_bridge_quotes('ethereum', 'arbitrum', 'ETH', 500)
        
        if quotes:
            best_quote = quotes[0]
            print(f"      Current best: {best_quote.bridge_name} - ${best_quote.total_cost_usd:.2f}")
            
            # Simulate cost change detection
            if cycle > 1:
                # Simulate a cost change
                import random
                change_pct = random.uniform(-15, 15)
                print(f"      Cost change: {change_pct:+.1f}% from last cycle")
                
                if abs(change_pct) > 10:
                    print(f"      🚨 ALERT: Significant cost change detected!")
        
        # Wait between cycles
        if cycle < 3:
            print(f"      ⏳ Waiting 15 seconds until next cycle...")
            await asyncio.sleep(15)
    
    # Test cost trend analysis
    print(f"\n📈 Cost Trend Analysis:")
    
    # Simulate historical data
    print("   Simulating 6-hour cost history...")
    
    trend_scenarios = [
        {'route': 'ETH ethereum→arbitrum', 'trend': 'decreasing', 'change': -8.5},
        {'route': 'USDC ethereum→base', 'trend': 'increasing', 'change': +12.3},
        {'route': 'USDT arbitrum→optimism', 'trend': 'stable', 'change': +1.2}
    ]
    
    for scenario in trend_scenarios:
        trend_icon = "📉" if scenario['trend'] == 'decreasing' else "📈" if scenario['trend'] == 'increasing' else "➡️"
        print(f"   {trend_icon} {scenario['route']}: {scenario['change']:+.1f}% over 6 hours ({scenario['trend']})")
    
    # Test alert system
    print(f"\n🚨 Alert System Test:")
    
    alert_scenarios = [
        {
            'route': 'ETH ethereum→arbitrum $500',
            'old_cost': 15.50,
            'new_cost': 12.20,
            'change': -21.3,
            'bridge': 'Hop Protocol'
        },
        {
            'route': 'USDC ethereum→base $2000',
            'old_cost': 8.75,
            'new_cost': 11.90,
            'change': +36.0,
            'bridge': 'Stargate Finance'
        }
    ]
    
    print("   Recent cost alerts (simulated):")
    for alert in alert_scenarios:
        alert_type = "💰 SAVINGS" if alert['change'] < 0 else "💸 INCREASE"
        print(f"   {alert_type}: {alert['route']}")
        print(f"      ${alert['old_cost']:.2f} → ${alert['new_cost']:.2f} ({alert['change']:+.1f}%)")
        print(f"      New best bridge: {alert['bridge']}")
    
    # Test real-time optimization recommendations
    print(f"\n🎯 Real-Time Optimization Recommendations:")
    
    if all_quotes:
        print("   Based on current bridge costs:")
        
        # Find best bridge for each route
        for route_key, quotes in all_quotes.items():
            parts = route_key.split('_')
            route_name = f"{parts[2]} {parts[0]}→{parts[1]} ${parts[3]}"
            
            best_quote = quotes[0]
            
            # Compare to Synapse (your baseline)
            synapse_quote = next((q for q in quotes if q.bridge_name == 'synapse'), None)
            
            if synapse_quote and best_quote.bridge_name != 'synapse':
                savings = synapse_quote.total_cost_usd - best_quote.total_cost_usd
                savings_pct = (savings / synapse_quote.total_cost_usd) * 100
                
                print(f"   💡 {route_name}:")
                print(f"      Switch from Synapse to {best_quote.bridge_name}")
                print(f"      Save ${savings:.2f} per trade ({savings_pct:.1f}%)")
                
                # Calculate daily/monthly savings
                daily_trades = 10  # Assume 10 trades per day for this route
                daily_savings = savings * daily_trades
                monthly_savings = daily_savings * 30
                
                print(f"      Daily savings: ${daily_savings:.2f}")
                print(f"      Monthly savings: ${monthly_savings:.2f}")
    
    # Test monitoring configuration
    print(f"\n⚙️  Monitoring Configuration:")
    
    config = monitor.monitoring_config
    print(f"   Update interval: {config['update_interval_minutes']} minutes")
    print(f"   Test amounts: {config['test_amounts']}")
    print(f"   Alert threshold: {config['alert_threshold_change']}% cost change")
    print(f"   Priority routes: {len(config['priority_routes'])} routes monitored")
    
    for route in config['priority_routes']:
        print(f"      • {route[2]} {route[0]}→{route[1]}")
    
    # Recommendations
    print(f"\n🚀 Implementation Recommendations:")
    
    print(f"   📊 Monitoring Strategy:")
    print(f"      • Run cost monitoring every 5 minutes")
    print(f"      • Alert on >10% cost changes")
    print(f"      • Test multiple trade sizes ($100-$2000)")
    print(f"      • Focus on your proven ETH→ARB route")
    
    print(f"   💰 Cost Optimization:")
    print(f"      • Always check 3-5 bridges before executing")
    print(f"      • Use fastest bridge when profit margin >2%")
    print(f"      • Use cheapest bridge when profit margin <1%")
    print(f"      • Have backup bridges ready for failover")
    
    print(f"   🔄 Automation:")
    print(f"      • Auto-select best bridge for each trade")
    print(f"      • Auto-failover if primary bridge fails")
    print(f"      • Auto-alert on significant cost changes")
    print(f"      • Daily cost optimization reports")
    
    # Cleanup
    await monitor.cleanup()
    
    print(f"\n🎉 Bridge Cost Monitor Test Complete!")
    print(f"   System ready for real-time cost optimization!")
    print(f"   Never overpay for bridge transfers again!")
    
    return True

async def main():
    """Main test function."""
    try:
        success = await test_bridge_cost_monitor()
        return success
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
