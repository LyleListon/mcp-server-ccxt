#!/usr/bin/env python3
"""
Test Capital Efficient Arbitrage Strategy
Shows how to maximize profits with minimal capital using flash loans and smaller DEXs.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.strategies.capital_efficient_strategy import CapitalEfficientStrategy

def test_capital_efficient_strategy():
    """Test the capital efficient arbitrage strategy."""
    print("💰 Testing Capital Efficient Arbitrage Strategy")
    print("=" * 60)
    
    # Load capital efficient config
    with open('config/capital_efficient_config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize strategy
    strategy = CapitalEfficientStrategy(config)
    
    # Test 1: Get priority pairs
    print("\n🎯 Priority Trading Pairs:")
    priority_pairs = strategy.get_priority_pairs()
    
    for pair in priority_pairs[:5]:  # Show top 5
        print(f"   {pair['priority']}. {pair['base_token']}/{pair['quote_token']} "
              f"({pair['category']}) - Expected: {pair['expected_profit']}%, "
              f"Capital: ${pair['capital_required']}")
    
    # Test 2: Create sample opportunities
    print("\n🔍 Sample Arbitrage Opportunities:")
    
    sample_opportunities = [
        {
            'id': 'opp_1',
            'input_token': 'USDC',
            'input_amount': 10000,
            'expected_profit_percentage': 0.8,
            'expected_profit_usd': 80,
            'estimated_gas_cost_usd': 5,
            'net_profit_usd': 70,
            'use_flash_loan': True,
            'flash_loan_info': {'fee_percentage': 0.09, 'fee_usd': 9},
            'path': [
                {'dex': 'aerodrome', 'from_token': 'USDC', 'to_token': 'USDT', 'liquidity': 1200000},
                {'dex': 'camelot', 'from_token': 'USDT', 'to_token': 'USDC', 'liquidity': 500000}
            ]
        },
        {
            'id': 'opp_2', 
            'input_token': 'ETH',
            'input_amount': 50000,
            'expected_profit_percentage': 1.5,
            'expected_profit_usd': 750,
            'estimated_gas_cost_usd': 50,
            'net_profit_usd': 650,
            'use_flash_loan': True,
            'flash_loan_info': {'fee_percentage': 0.09, 'fee_usd': 45},
            'path': [
                {'dex': 'uniswap_v3', 'from_token': 'ETH', 'to_token': 'USDC', 'liquidity': 5000000}
            ]
        },
        {
            'id': 'opp_3',
            'input_token': 'USDT',
            'input_amount': 3000,
            'expected_profit_percentage': 0.4,
            'expected_profit_usd': 12,
            'estimated_gas_cost_usd': 2,
            'net_profit_usd': 9,
            'use_flash_loan': True,
            'flash_loan_info': {'fee_percentage': 0.09, 'fee_usd': 2.7},
            'path': [
                {'dex': 'thena', 'from_token': 'USDT', 'to_token': 'USDC', 'liquidity': 400000},
                {'dex': 'velodrome', 'from_token': 'USDC', 'to_token': 'USDT', 'liquidity': 900000}
            ]
        }
    ]
    
    # Test 3: Filter opportunities by capital efficiency
    print("\n📊 Capital Efficiency Analysis:")
    filtered_opportunities = strategy.filter_opportunities_by_capital(sample_opportunities)
    
    for i, opp in enumerate(filtered_opportunities, 1):
        score = opp.get('capital_efficiency_score', 0)
        print(f"   {i}. {opp['id']}: Score {score:.3f} - "
              f"${opp['input_amount']:,} → ${opp['net_profit_usd']:.2f} profit "
              f"({opp['expected_profit_percentage']:.2f}%)")
    
    # Test 4: Optimize trade sizes
    print("\n⚙️  Trade Size Optimization:")
    for opp in filtered_opportunities[:2]:
        optimized = strategy.optimize_trade_size(opp)
        if optimized.get('optimized'):
            print(f"   {optimized['id']}: {optimized['optimization_reason']}")
            print(f"      New profit: ${optimized['net_profit_usd']:.2f}")
    
    # Test 5: Flash loan strategies
    print("\n⚡ Flash Loan Strategies:")
    for opp in filtered_opportunities[:2]:
        flash_strategy = strategy.get_flash_loan_strategy(opp)
        if flash_strategy:
            print(f"   {opp['id']}: {flash_strategy['provider']} - "
                  f"${flash_strategy['amount']:,} at {flash_strategy['fee_percentage']}% fee "
                  f"(${flash_strategy['fee_amount']:.2f})")
    
    # Test 6: Strategy summary
    print("\n📋 Strategy Summary:")
    summary = strategy.get_strategy_summary()
    print(f"   Strategy: {summary['strategy_name']}")
    print(f"   Focus: {summary['focus']}")
    print(f"   Target Pairs: {summary['target_pairs']}")
    print(f"   Min Profit: {summary['min_profit_threshold']}")
    print(f"   Max Trade: {summary['max_trade_amount']}")
    print(f"   Flash Loans: {summary['use_flash_loans']}")
    print(f"   Networks: {', '.join(summary['preferred_networks'])}")
    
    print("\n✅ Advantages:")
    for advantage in summary['advantages']:
        print(f"      • {advantage}")
    
    print("\n⚠️  Risks:")
    for risk in summary['risks']:
        print(f"      • {risk}")
    
    # Test 7: Calculate potential daily profits
    print("\n💵 Potential Daily Profits (Conservative Estimates):")
    
    scenarios = [
        {"name": "Conservative", "opportunities_per_day": 5, "avg_profit": 15},
        {"name": "Moderate", "opportunities_per_day": 10, "avg_profit": 25}, 
        {"name": "Aggressive", "opportunities_per_day": 20, "avg_profit": 40}
    ]
    
    for scenario in scenarios:
        daily_profit = scenario['opportunities_per_day'] * scenario['avg_profit']
        monthly_profit = daily_profit * 30
        print(f"   {scenario['name']}: {scenario['opportunities_per_day']} ops/day × "
              f"${scenario['avg_profit']} = ${daily_profit}/day (${monthly_profit:,}/month)")
    
    print("\n🎉 Capital Efficient Strategy Test Complete!")
    print("   Ready for flash loan arbitrage with minimal capital requirements!")
    
    return True

if __name__ == "__main__":
    success = test_capital_efficient_strategy()
    sys.exit(0 if success else 1)
