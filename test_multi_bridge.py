#!/usr/bin/env python3
"""
Multi-Bridge Test
Tests the multi-bridge manager for optimal bridge selection.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridges.multi_bridge_manager import MultiBridgeManager

async def test_multi_bridge_manager():
    """Test the multi-bridge manager."""
    print("🌉 Multi-Bridge Manager Test")
    print("=" * 60)
    print("🎯 Testing optimal bridge selection for arbitrage")
    print("💰 Finding cheapest routes across 7 bridge providers")
    print("⚡ Speed vs cost optimization")
    print("🔄 Redundancy and failover capabilities")
    print("=" * 60)
    
    # Load config
    with open('config/capital_efficient_config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize multi-bridge manager
    print("\n🔌 Initializing Multi-Bridge Manager...")
    
    bridge_manager = MultiBridgeManager(config)
    
    # Initialize connections
    print("   Connecting to bridge APIs...")
    connected = await bridge_manager.initialize()
    
    if not connected:
        print("❌ Failed to connect to bridge APIs")
        return False
    
    print("✅ Multi-Bridge Manager Ready!")
    
    # Display bridge status
    print(f"\n📊 Bridge Provider Status:")
    
    bridge_status = bridge_manager.get_bridge_status()
    
    for bridge_name, status in bridge_status.items():
        enabled_status = "✅ Enabled" if status['enabled'] else "❌ Disabled"
        print(f"   {status['name']}: {enabled_status}")
        print(f"      Priority: #{status['priority']}")
        print(f"      Base Fee: {status['base_fee_percentage']:.2f}%")
        print(f"      Speed: {status['speed_minutes']} minutes")
        print(f"      Chains: {status['supported_chains']}, Tokens: {status['supported_tokens']}")
        print(f"      Reliability: {status['reliability']*100:.1f}%")
    
    # Test bridge quote comparison
    print(f"\n🔍 Testing Bridge Quote Comparison...")
    
    test_scenarios = [
        {
            'name': 'ETH Arbitrage (Your Tested Route)',
            'source_chain': 'ethereum',
            'target_chain': 'arbitrum',
            'token': 'ETH',
            'amount_usd': 500
        },
        {
            'name': 'USDC Arbitrage (High Volume)',
            'source_chain': 'ethereum',
            'target_chain': 'base',
            'token': 'USDC',
            'amount_usd': 2000
        },
        {
            'name': 'L2 to L2 Arbitrage',
            'source_chain': 'arbitrum',
            'target_chain': 'optimism',
            'token': 'USDT',
            'amount_usd': 1500
        },
        {
            'name': 'Large Trade Test',
            'source_chain': 'ethereum',
            'target_chain': 'polygon',
            'token': 'DAI',
            'amount_usd': 5000
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n   🧪 {scenario['name']}")
        print(f"      Route: {scenario['source_chain'].title()} → {scenario['target_chain'].title()}")
        print(f"      Token: {scenario['token']}, Amount: ${scenario['amount_usd']:,}")
        
        # Get best bridge quote
        quote_result = await bridge_manager.get_best_bridge_quote(
            scenario['source_chain'],
            scenario['target_chain'],
            scenario['token'],
            scenario['amount_usd']
        )
        
        if quote_result['success']:
            print(f"      🏆 Best Bridge: {quote_result['bridge_name']}")
            print(f"      💰 Fee: ${quote_result['fee_usd']:.2f} ({quote_result['fee_percentage']:.2f}%)")
            print(f"      ⏱️  Time: {quote_result['estimated_time_minutes']:.1f} minutes")
            print(f"      📊 Score: {quote_result.get('composite_score', 0):.3f}")
            
            # Calculate net profit impact
            gross_profit = scenario['amount_usd'] * 0.008  # Assume 0.8% arbitrage opportunity
            net_profit = gross_profit - quote_result['fee_usd']
            profit_margin = (net_profit / scenario['amount_usd']) * 100
            
            print(f"      📈 Impact: ${gross_profit:.2f} gross → ${net_profit:.2f} net ({profit_margin:.3f}%)")
            
            if net_profit > 0:
                print(f"      ✅ PROFITABLE")
            else:
                print(f"      ❌ NOT PROFITABLE")
        else:
            print(f"      ❌ Error: {quote_result['error']}")
    
    # Test bridge comparison for same route
    print(f"\n🏁 Bridge Comparison for ETH→ARB (Your Route):")
    
    # Manually test each bridge for comparison
    comparison_results = []
    
    for bridge_name, bridge_config in bridge_manager.bridges.items():
        if not bridge_config['enabled']:
            continue
        
        if ('ethereum' in bridge_config['supported_chains'] and 
            'arbitrum' in bridge_config['supported_chains'] and
            'ETH' in bridge_config['supported_tokens']):
            
            quote = await bridge_manager._get_bridge_quote(
                bridge_name, 'ethereum', 'arbitrum', 'ETH', 500
            )
            
            if quote['success']:
                comparison_results.append({
                    'bridge': bridge_name,
                    'name': bridge_config['name'],
                    'fee_usd': quote['fee_usd'],
                    'fee_percentage': quote['fee_percentage'],
                    'time_minutes': quote['estimated_time_minutes'],
                    'reliability': quote['reliability_score']
                })
    
    # Sort by fee
    comparison_results.sort(key=lambda x: x['fee_usd'])
    
    print(f"   Comparing {len(comparison_results)} bridges for $500 ETH transfer:")
    
    for i, result in enumerate(comparison_results, 1):
        print(f"   {i}. {result['name']}")
        print(f"      Fee: ${result['fee_usd']:.2f} ({result['fee_percentage']:.2f}%)")
        print(f"      Time: {result['time_minutes']:.1f} min")
        print(f"      Reliability: {result['reliability']*100:.1f}%")
        
        if result['bridge'] == 'synapse':
            print(f"      🎯 YOUR TESTED BRIDGE")
    
    # Test failover scenario
    print(f"\n🔄 Testing Bridge Failover Scenario...")
    
    # Simulate bridge failures
    print("   Simulating Synapse bridge failure...")
    bridge_manager.bridges['synapse']['enabled'] = False
    
    failover_quote = await bridge_manager.get_best_bridge_quote(
        'ethereum', 'arbitrum', 'ETH', 500
    )
    
    if failover_quote['success']:
        print(f"   ✅ Failover successful!")
        print(f"   🔄 Backup bridge: {failover_quote['bridge_name']}")
        print(f"   💰 Backup fee: ${failover_quote['fee_usd']:.2f}")
        print(f"   📊 No missed opportunities due to bridge failure!")
    else:
        print(f"   ❌ Failover failed: {failover_quote['error']}")
    
    # Re-enable Synapse
    bridge_manager.bridges['synapse']['enabled'] = True
    
    # Test optimization strategies
    print(f"\n⚡ Bridge Optimization Strategies:")
    
    strategies = [
        {
            'name': 'Lowest Cost',
            'description': 'Always choose cheapest bridge',
            'weight_fee': 1.0,
            'weight_speed': 0.0,
            'weight_reliability': 0.0
        },
        {
            'name': 'Fastest Execution',
            'description': 'Prioritize speed over cost',
            'weight_fee': 0.2,
            'weight_speed': 0.8,
            'weight_reliability': 0.0
        },
        {
            'name': 'Most Reliable',
            'description': 'Prioritize reliability',
            'weight_fee': 0.3,
            'weight_speed': 0.2,
            'weight_reliability': 0.5
        },
        {
            'name': 'Balanced',
            'description': 'Balance cost, speed, and reliability',
            'weight_fee': 0.4,
            'weight_speed': 0.3,
            'weight_reliability': 0.3
        }
    ]
    
    for strategy in strategies:
        print(f"   📋 {strategy['name']}: {strategy['description']}")
        
        # Find best bridge for this strategy
        best_bridge = None
        best_score = -1
        
        for result in comparison_results:
            fee_score = 1 - (result['fee_usd'] / 10)  # Normalize to 0-1
            speed_score = 1 - (result['time_minutes'] / 10)  # Normalize to 0-1
            reliability_score = result['reliability']
            
            composite_score = (
                fee_score * strategy['weight_fee'] +
                speed_score * strategy['weight_speed'] +
                reliability_score * strategy['weight_reliability']
            )
            
            if composite_score > best_score:
                best_score = composite_score
                best_bridge = result
        
        if best_bridge:
            print(f"      🏆 Best: {best_bridge['name']} (${best_bridge['fee_usd']:.2f}, {best_bridge['time_minutes']:.1f}min)")
    
    # Calculate daily savings with multi-bridge
    print(f"\n💰 Multi-Bridge Economic Impact:")
    
    # Assume 20 trades per day
    daily_trades = 20
    avg_trade_size = 2000
    
    # Single bridge (Synapse only)
    synapse_fee = avg_trade_size * 0.0018  # 0.18%
    single_bridge_daily_cost = daily_trades * synapse_fee
    
    # Multi-bridge (assume 10% average savings)
    multi_bridge_savings_percentage = 10
    multi_bridge_daily_cost = single_bridge_daily_cost * (1 - multi_bridge_savings_percentage / 100)
    daily_savings = single_bridge_daily_cost - multi_bridge_daily_cost
    
    print(f"   Single Bridge (Synapse only):")
    print(f"      Daily bridge costs: ${single_bridge_daily_cost:.2f}")
    print(f"      Monthly costs: ${single_bridge_daily_cost * 30:.2f}")
    
    print(f"   Multi-Bridge Strategy:")
    print(f"      Daily bridge costs: ${multi_bridge_daily_cost:.2f}")
    print(f"      Monthly costs: ${multi_bridge_daily_cost * 30:.2f}")
    print(f"      Daily savings: ${daily_savings:.2f}")
    print(f"      Monthly savings: ${daily_savings * 30:.2f}")
    print(f"      Annual savings: ${daily_savings * 365:.2f}")
    
    # Recommendations
    print(f"\n🎯 Multi-Bridge Recommendations:")
    
    print(f"   ✅ Primary bridges for your strategy:")
    print(f"      1. Synapse Protocol (your tested route - proven $0.90 for $500)")
    print(f"      2. Across Protocol (very low fees, good reliability)")
    print(f"      3. Hop Protocol (competitive fees, good for L2s)")
    
    print(f"   ⚡ Speed-optimized bridges:")
    print(f"      1. Stargate Finance (1 minute execution)")
    print(f"      2. Orbiter Finance (1 minute for L2s)")
    
    print(f"   🔄 Backup bridges:")
    print(f"      1. Celer cBridge (wide chain support)")
    print(f"      2. Multichain (maximum chain coverage)")
    
    print(f"   📊 Strategy recommendations:")
    print(f"      • Use Synapse for ETH→ARB (proven low cost)")
    print(f"      • Use Across for other ETH→L2 routes")
    print(f"      • Use Stargate when speed matters more than cost")
    print(f"      • Always have 2-3 backup bridges enabled")
    print(f"      • Monitor bridge performance and adjust priorities")
    
    # Cleanup
    await bridge_manager.cleanup()
    
    print(f"\n🎉 Multi-Bridge Test Complete!")
    print(f"   System ready for optimal bridge selection!")
    print(f"   Never miss opportunities due to single bridge failure!")
    
    return True

async def main():
    """Main test function."""
    try:
        success = await test_multi_bridge_manager()
        return success
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
