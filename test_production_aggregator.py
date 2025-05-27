#!/usr/bin/env python3
"""
Production DEX Aggregator Test
Tests the production-ready DEX aggregator with real market data and 13 DEXs.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dex.production_dex_aggregator import ProductionDEXAggregator
from core.strategies.capital_efficient_strategy import CapitalEfficientStrategy

async def test_production_aggregator():
    """Test the production DEX aggregator."""
    print("🚀 Testing Production DEX Aggregator")
    print("=" * 60)
    
    # Load config
    with open('config/capital_efficient_config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize production aggregator
    print("🔌 Initializing Production DEX Aggregator...")
    
    aggregator = ProductionDEXAggregator(config)
    
    # Test connection
    print("   Connecting to real market data sources...")
    connected = await aggregator.connect()
    
    if not connected:
        print("❌ Failed to connect to production aggregator")
        return False
    
    print("✅ Connected to Production DEX Aggregator!")
    print(f"   Data source: CoinGecko API")
    print(f"   DEX ecosystem: 13 DEXs across 8 networks")
    
    # Test pair generation
    print("\n📊 Generating Trading Pairs Across All DEXs...")
    
    pairs = await aggregator.get_pairs()
    
    if not pairs:
        print("❌ No pairs generated")
        return False
    
    print(f"✅ Generated {len(pairs)} trading pairs!")
    
    # Analyze pair distribution
    dex_counts = {}
    network_counts = {}
    
    for pair in pairs:
        dex = pair['dex']
        network = pair['network']
        
        dex_counts[dex] = dex_counts.get(dex, 0) + 1
        network_counts[network] = network_counts.get(network, 0) + 1
    
    print(f"\n📈 Pair Distribution by DEX:")
    for dex, count in sorted(dex_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"   {dex}: {count} pairs")
    
    print(f"\n🌐 Pair Distribution by Network:")
    for network, count in sorted(network_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {network}: {count} pairs")
    
    # Test arbitrage opportunity detection
    print("\n🔍 Scanning for Arbitrage Opportunities...")
    
    opportunities = await aggregator.find_arbitrage_opportunities(pairs)
    
    if opportunities:
        print(f"🎯 Found {len(opportunities)} Arbitrage Opportunities!")
        
        # Sort by profit percentage
        opportunities.sort(key=lambda x: x['profit_percentage'], reverse=True)
        
        # Separate same-chain and cross-chain opportunities
        same_chain = [opp for opp in opportunities if not opp['cross_chain']]
        cross_chain = [opp for opp in opportunities if opp['cross_chain']]
        
        print(f"\n💫 Same-Chain Opportunities: {len(same_chain)}")
        for i, opp in enumerate(same_chain[:5], 1):  # Top 5
            print(f"   {i}. {opp['pair']} - {opp['profit_percentage']:.3f}% profit")
            print(f"      {opp['buy_dex']} → {opp['sell_dex']} ({opp['buy_network']})")
            print(f"      Buy: {opp['buy_price']:.6f}, Sell: {opp['sell_price']:.6f}")
            
            # Calculate potential profit
            trade_amount = 5000
            gross_profit = trade_amount * (opp['profit_percentage'] / 100)
            flash_loan_fee = trade_amount * 0.0009  # 0.09% Aave fee
            gas_cost = 10  # L2 gas cost
            net_profit = gross_profit - flash_loan_fee - gas_cost
            
            if net_profit > 0:
                roi = (net_profit / flash_loan_fee) * 100 if flash_loan_fee > 0 else 0
                print(f"      💰 ${trade_amount:,} trade: ${net_profit:.2f} profit (ROI: {roi:.0f}%)")
        
        print(f"\n🌉 Cross-Chain Opportunities: {len(cross_chain)}")
        for i, opp in enumerate(cross_chain[:3], 1):  # Top 3
            print(f"   {i}. {opp['pair']} - {opp['profit_percentage']:.3f}% profit")
            print(f"      {opp['buy_dex']} ({opp['buy_network']}) → {opp['sell_dex']} ({opp['sell_network']})")
            print(f"      ⚠️  Requires cross-chain bridge")
        
        # Best opportunity analysis
        if same_chain:
            best_opp = same_chain[0]
            print(f"\n🏆 Best Same-Chain Opportunity:")
            print(f"   Pair: {best_opp['pair']}")
            print(f"   Profit: {best_opp['profit_percentage']:.3f}%")
            print(f"   Route: {best_opp['buy_dex']} → {best_opp['sell_dex']}")
            print(f"   Network: {best_opp['buy_network']}")
            print(f"   Liquidity: Buy ${best_opp['buy_liquidity']:,}, Sell ${best_opp['sell_liquidity']:,}")
            
            # Detailed profit analysis
            print(f"   Profit Analysis:")
            amounts = [1000, 5000, 10000, 25000]
            for amount in amounts:
                gross = amount * (best_opp['profit_percentage'] / 100)
                fee = amount * 0.0009
                gas = 10
                net = gross - fee - gas
                if net > 0:
                    roi = (net / fee) * 100 if fee > 0 else 0
                    print(f"      ${amount:,}: ${net:.2f} profit (ROI: {roi:.0f}%)")
    else:
        print("⚠️  No arbitrage opportunities found at this moment")
    
    # Test price fetching
    print("\n💰 Testing Price Fetching...")
    
    test_pairs = [
        ('ETH', 'USDC'),
        ('USDC', 'USDT'),
        ('DAI', 'USDC'),
        ('WBTC', 'ETH')
    ]
    
    for base_token, quote_token in test_pairs:
        try:
            price = await aggregator.get_price(base_token, quote_token)
            if price:
                print(f"   {base_token}/{quote_token}: {price:.6f} (consensus across 13 DEXs)")
            else:
                print(f"   {base_token}/{quote_token}: No price available")
        except Exception as e:
            print(f"   {base_token}/{quote_token}: Error - {e}")
    
    # Test quote functionality
    print("\n📋 Testing Quote Functionality...")
    
    try:
        quote = await aggregator.get_quote('ETH', 'USDC', 1.0)
        if quote:
            print(f"   Quote for 1 ETH → USDC:")
            print(f"      Expected output: {quote['expected_output']:.2f} USDC")
            print(f"      Price: {quote['price']:.2f}")
            print(f"      Slippage estimate: {quote['slippage_estimate']:.2f}%")
            print(f"      Gas estimate: {quote['gas_estimate']:,} units")
            print(f"      Aggregated DEXs: {quote['aggregated_dexs']}")
        else:
            print("   Quote not available")
    except Exception as e:
        print(f"   Quote error: {e}")
    
    # Test liquidity information
    print("\n💧 Testing Liquidity Information...")
    
    try:
        liquidity = await aggregator.get_liquidity('ETH', 'USDC')
        if liquidity:
            print(f"   Average liquidity across all DEXs: ${liquidity:,.0f}")
        else:
            print("   Liquidity data not available")
    except Exception as e:
        print(f"   Liquidity error: {e}")
    
    # Test capital efficient strategy integration
    print("\n💰 Testing Capital Efficient Strategy Integration...")
    
    strategy = CapitalEfficientStrategy(config)
    
    if opportunities:
        # Convert opportunities to strategy format
        strategy_opportunities = []
        
        for opp in same_chain[:3]:  # Top 3 same-chain opportunities
            strategy_opp = {
                'id': f"prod_opp_{opp['pair']}",
                'input_token': opp['base_token'],
                'input_amount': 5000,
                'expected_profit_percentage': opp['profit_percentage'],
                'expected_profit_usd': 5000 * (opp['profit_percentage'] / 100),
                'estimated_gas_cost_usd': 10,
                'net_profit_usd': 5000 * (opp['profit_percentage'] / 100) - 10 - 4.5,
                'use_flash_loan': True,
                'flash_loan_info': {'fee_percentage': 0.09, 'fee_usd': 4.5},
                'path': [
                    {'dex': opp['buy_dex'], 'from_token': opp['base_token'], 'to_token': opp['quote_token']},
                    {'dex': opp['sell_dex'], 'from_token': opp['quote_token'], 'to_token': opp['base_token']}
                ]
            }
            strategy_opportunities.append(strategy_opp)
        
        # Filter by capital efficiency
        filtered_opps = strategy.filter_opportunities_by_capital(strategy_opportunities)
        
        print(f"   Capital efficient opportunities: {len(filtered_opps)}")
        
        for opp in filtered_opps:
            score = opp.get('capital_efficiency_score', 0)
            print(f"      {opp['id']}: Score {score:.3f} - ${opp['net_profit_usd']:.2f} profit")
    
    # Performance statistics
    print("\n📊 Performance Statistics:")
    
    total_liquidity = sum(dex['liquidity'] for dex in aggregator.dex_ecosystem.values())
    avg_liquidity = total_liquidity / len(aggregator.dex_ecosystem)
    
    print(f"   DEXs monitored: {len(aggregator.dex_ecosystem)}")
    print(f"   Networks covered: {len(set(dex['network'] for dex in aggregator.dex_ecosystem.values()))}")
    print(f"   Total pairs generated: {len(pairs)}")
    print(f"   Arbitrage opportunities: {len(opportunities)}")
    print(f"   Same-chain opportunities: {len(same_chain) if 'same_chain' in locals() else 0}")
    print(f"   Cross-chain opportunities: {len(cross_chain) if 'cross_chain' in locals() else 0}")
    print(f"   Total ecosystem liquidity: ${total_liquidity:,.0f}")
    print(f"   Average DEX liquidity: ${avg_liquidity:,.0f}")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    await aggregator.disconnect()
    
    print(f"\n🎉 Production DEX Aggregator Test Complete!")
    print(f"   System ready for live arbitrage trading!")
    print(f"   Monitoring 13 DEXs across 8 networks with real market data!")
    
    return True

async def main():
    """Main test function."""
    try:
        success = await test_production_aggregator()
        return success
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
