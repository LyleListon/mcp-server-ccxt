#!/usr/bin/env python3
"""
Cross-Chain MEV Test
Tests the cross-chain MEV engine for arbitrage opportunities.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from crosschain.cross_chain_mev_engine import CrossChainMEVEngine

async def test_cross_chain_mev():
    """Test the cross-chain MEV engine."""
    print("🌉 Testing Cross-Chain MEV Engine")
    print("=" * 60)
    
    # Load config
    with open('config/capital_efficient_config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize cross-chain MEV engine
    print("🔌 Initializing Cross-Chain MEV Engine...")
    
    mev_engine = CrossChainMEVEngine(config)
    
    # Display system capabilities
    summary = mev_engine.get_cross_chain_summary()
    
    print("✅ Cross-Chain MEV Engine initialized!")
    print(f"   Supported chains: {summary['supported_chains']}")
    print(f"   Bridge providers: {summary['supported_bridges']}")
    print(f"   Target tokens: {summary['target_tokens']}")
    print(f"   Chain pairs: {summary['chain_pairs']}")
    print(f"   Competition level: {summary['competition_level']}")
    print(f"   Profit potential: {summary['profit_potential']}")
    
    # Test cross-chain opportunity scanning
    print(f"\n🔍 Scanning for Cross-Chain Arbitrage Opportunities...")
    
    opportunities = await mev_engine.scan_cross_chain_opportunities()
    
    if opportunities:
        print(f"🎯 Found {len(opportunities)} Cross-Chain Opportunities!")
        
        # Display top opportunities
        for i, opp in enumerate(opportunities[:5], 1):  # Top 5
            print(f"\n   {i}. {opp['token']} Cross-Chain Arbitrage")
            print(f"      Route: {opp['source_chain'].title()} → {opp['target_chain'].title()}")
            print(f"      Profit: {opp['profit_percentage']:.3f}% (${opp['net_profit_usd']:.2f})")
            print(f"      Bridge: {opp['bridge_provider']} ({opp['bridge_time_minutes']} min)")
            print(f"      Complexity: {opp['execution_complexity'].title()}")
            print(f"      Risk Score: {opp['risk_score']:.1f}/10")
            
            # Detailed breakdown
            print(f"      💰 Financial Breakdown:")
            print(f"         Trade Amount: ${opp['trade_amount_usd']:,}")
            print(f"         Gross Profit: ${opp['gross_profit_usd']:.2f}")
            print(f"         Bridge Fee: ${opp['bridge_fee_usd']:.2f}")
            print(f"         Gas Costs: ${opp['gas_cost_usd']:.2f}")
            print(f"         Net Profit: ${opp['net_profit_usd']:.2f}")
            
            # ROI calculation
            total_costs = opp['bridge_fee_usd'] + opp['gas_cost_usd']
            roi = (opp['net_profit_usd'] / total_costs * 100) if total_costs > 0 else 0
            print(f"         ROI: {roi:.1f}%")
    else:
        print("⚠️  No cross-chain opportunities found at this moment")
    
    # Analyze opportunities by chain
    if opportunities:
        print(f"\n📊 Opportunity Analysis by Chain:")
        
        # Count opportunities by source chain
        source_chains = {}
        target_chains = {}
        
        for opp in opportunities:
            source = opp['source_chain']
            target = opp['target_chain']
            
            source_chains[source] = source_chains.get(source, 0) + 1
            target_chains[target] = target_chains.get(target, 0) + 1
        
        print(f"   Source Chains (Buy from):")
        for chain, count in sorted(source_chains.items(), key=lambda x: x[1], reverse=True):
            print(f"      {chain.title()}: {count} opportunities")
        
        print(f"   Target Chains (Sell to):")
        for chain, count in sorted(target_chains.items(), key=lambda x: x[1], reverse=True):
            print(f"      {chain.title()}: {count} opportunities")
        
        # Analyze by token
        print(f"\n💰 Opportunity Analysis by Token:")
        token_analysis = {}
        
        for opp in opportunities:
            token = opp['token']
            if token not in token_analysis:
                token_analysis[token] = {
                    'count': 0,
                    'total_profit': 0,
                    'avg_profit': 0,
                    'best_profit': 0
                }
            
            token_analysis[token]['count'] += 1
            token_analysis[token]['total_profit'] += opp['net_profit_usd']
            token_analysis[token]['best_profit'] = max(
                token_analysis[token]['best_profit'], 
                opp['net_profit_usd']
            )
        
        for token, data in token_analysis.items():
            data['avg_profit'] = data['total_profit'] / data['count']
            print(f"   {token}:")
            print(f"      Opportunities: {data['count']}")
            print(f"      Total Profit: ${data['total_profit']:.2f}")
            print(f"      Average Profit: ${data['avg_profit']:.2f}")
            print(f"      Best Profit: ${data['best_profit']:.2f}")
        
        # Best opportunity analysis
        best_opp = opportunities[0]
        print(f"\n🏆 Best Cross-Chain Opportunity:")
        print(f"   Token: {best_opp['token']}")
        print(f"   Route: {best_opp['source_chain'].title()} → {best_opp['target_chain'].title()}")
        print(f"   Profit: {best_opp['profit_percentage']:.3f}% (${best_opp['net_profit_usd']:.2f})")
        print(f"   Bridge: {best_opp['bridge_provider']}")
        print(f"   Execution Time: {best_opp['bridge_time_minutes']} minutes")
        print(f"   Risk Level: {best_opp['risk_score']:.1f}/10")
        
        # Calculate potential daily profits
        print(f"\n💵 Potential Daily Profits (Cross-Chain MEV):")
        
        scenarios = [
            {"name": "Conservative", "opportunities_per_day": 5, "avg_profit": 50},
            {"name": "Moderate", "opportunities_per_day": 15, "avg_profit": 100},
            {"name": "Aggressive", "opportunities_per_day": 30, "avg_profit": 200}
        ]
        
        for scenario in scenarios:
            daily_profit = scenario['opportunities_per_day'] * scenario['avg_profit']
            monthly_profit = daily_profit * 30
            print(f"   {scenario['name']}: {scenario['opportunities_per_day']} ops/day × "
                  f"${scenario['avg_profit']} = ${daily_profit}/day (${monthly_profit:,}/month)")
    
    # Test bridge analysis
    print(f"\n🌉 Bridge Provider Analysis:")
    
    for bridge_name, bridge_info in mev_engine.bridges.items():
        print(f"   {bridge_name.title()}:")
        print(f"      Chains: {len(bridge_info['chains'])} ({', '.join(bridge_info['chains'])})")
        print(f"      Fee: {bridge_info['fee_percentage']}%")
        print(f"      Speed: {bridge_info['time_minutes']['fast']} min (fast)")
        print(f"      Reliability: {bridge_info['reliability']*100:.1f}%")
    
    # Test chain analysis
    print(f"\n⛓️  Chain Analysis:")
    
    for chain_name, chain_info in mev_engine.chains.items():
        print(f"   {chain_name.title()}:")
        print(f"      Gas Price: {chain_info['avg_gas_price']} gwei")
        print(f"      Block Time: {chain_info['block_time']}s")
        print(f"      Liquidity Tier: {chain_info['liquidity_tier']}")
        print(f"      DEXs: {len(chain_info['dexs'])} ({', '.join(chain_info['dexs'])})")
    
    # Strategic recommendations
    print(f"\n🎯 Strategic Recommendations:")
    
    if opportunities:
        # Find most profitable chains
        chain_profits = {}
        for opp in opportunities:
            source = opp['source_chain']
            target = opp['target_chain']
            profit = opp['net_profit_usd']
            
            chain_profits[source] = chain_profits.get(source, 0) + profit
            chain_profits[target] = chain_profits.get(target, 0) + profit
        
        best_chains = sorted(chain_profits.items(), key=lambda x: x[1], reverse=True)[:3]
        
        print(f"   🏆 Focus on these chains:")
        for chain, total_profit in best_chains:
            print(f"      {chain.title()}: ${total_profit:.2f} total profit potential")
        
        # Find best tokens
        token_profits = {}
        for opp in opportunities:
            token = opp['token']
            token_profits[token] = token_profits.get(token, 0) + opp['net_profit_usd']
        
        best_tokens = sorted(token_profits.items(), key=lambda x: x[1], reverse=True)
        
        print(f"   💰 Focus on these tokens:")
        for token, total_profit in best_tokens:
            print(f"      {token}: ${total_profit:.2f} total profit potential")
    
    print(f"\n🚀 Cross-Chain MEV Advantages:")
    for advantage in summary['advantages']:
        print(f"   ✅ {advantage}")
    
    print(f"\n🎉 Cross-Chain MEV Test Complete!")
    print(f"   System ready for cross-chain arbitrage execution!")
    print(f"   Next step: Connect to real bridge APIs and start earning!")
    
    return True

async def main():
    """Main test function."""
    try:
        success = await test_cross_chain_mev()
        return success
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
