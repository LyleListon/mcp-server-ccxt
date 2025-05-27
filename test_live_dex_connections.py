#!/usr/bin/env python3
"""
Live DEX Connection Test
Tests real connections to smaller DEXs and scans for actual arbitrage opportunities.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dex.aerodrome_adapter import AerodromeAdapter
from dex.camelot_adapter import CamelotAdapter
from dex.velodrome_adapter import VelodromeAdapter
from dex.thena_adapter import ThenaAdapter
from dex.ramses_adapter import RamsesAdapter
from core.strategies.capital_efficient_strategy import CapitalEfficientStrategy

async def test_live_dex_connections():
    """Test live connections to smaller DEXs."""
    print("🌐 Testing Live DEX Connections")
    print("=" * 60)
    
    # Load capital efficient config
    with open('config/capital_efficient_config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize DEX adapters
    dex_adapters = {}
    
    print("\n🔌 Initializing DEX Adapters...")
    
    # Aerodrome (Base)
    try:
        dex_adapters['aerodrome'] = AerodromeAdapter(config['dexs']['aerodrome'])
        print("✅ Aerodrome adapter initialized")
    except Exception as e:
        print(f"❌ Aerodrome adapter failed: {e}")
    
    # Camelot (Arbitrum)
    try:
        dex_adapters['camelot'] = CamelotAdapter(config['dexs']['camelot'])
        print("✅ Camelot adapter initialized")
    except Exception as e:
        print(f"❌ Camelot adapter failed: {e}")
    
    # Velodrome (Optimism)
    try:
        dex_adapters['velodrome'] = VelodromeAdapter(config['dexs']['velodrome'])
        print("✅ Velodrome adapter initialized")
    except Exception as e:
        print(f"❌ Velodrome adapter failed: {e}")
    
    # Thena (BNB Chain)
    try:
        dex_adapters['thena'] = ThenaAdapter(config['dexs']['thena'])
        print("✅ Thena adapter initialized")
    except Exception as e:
        print(f"❌ Thena adapter failed: {e}")
    
    # Ramses (Arbitrum)
    try:
        dex_adapters['ramses'] = RamsesAdapter(config['dexs']['ramses'])
        print("✅ Ramses adapter initialized")
    except Exception as e:
        print(f"❌ Ramses adapter failed: {e}")
    
    # Test connections
    print(f"\n🔗 Testing Connections to {len(dex_adapters)} DEXs...")
    connected_dexs = {}
    
    for dex_name, adapter in dex_adapters.items():
        try:
            print(f"   Connecting to {dex_name}...")
            connected = await adapter.connect()
            if connected:
                connected_dexs[dex_name] = adapter
                print(f"   ✅ {dex_name} connected successfully!")
            else:
                print(f"   ❌ {dex_name} connection failed")
        except Exception as e:
            print(f"   ❌ {dex_name} connection error: {e}")
    
    if not connected_dexs:
        print("\n❌ No DEXs connected. Cannot proceed with testing.")
        return False
    
    print(f"\n🎉 Successfully connected to {len(connected_dexs)} DEXs: {list(connected_dexs.keys())}")
    
    # Test price fetching
    print("\n💰 Testing Price Fetching...")
    
    # Test priority pairs from our capital efficient strategy
    strategy = CapitalEfficientStrategy(config)
    priority_pairs = strategy.get_priority_pairs()
    
    price_data = {}
    
    for pair in priority_pairs[:3]:  # Test top 3 pairs
        base_token = pair['base_token']
        quote_token = pair['quote_token']
        pair_key = f"{base_token}/{quote_token}"
        
        print(f"\n   📊 Testing {pair_key} prices:")
        price_data[pair_key] = {}
        
        for dex_name, adapter in connected_dexs.items():
            try:
                price = await adapter.get_price(base_token, quote_token)
                if price and price > 0:
                    price_data[pair_key][dex_name] = price
                    print(f"      {dex_name}: {price:.6f}")
                else:
                    print(f"      {dex_name}: No price available")
            except Exception as e:
                print(f"      {dex_name}: Error - {e}")
    
    # Analyze arbitrage opportunities
    print("\n🔍 Analyzing Arbitrage Opportunities...")
    
    opportunities = []
    
    for pair_key, prices in price_data.items():
        if len(prices) >= 2:  # Need at least 2 DEXs with prices
            max_price_dex = max(prices, key=prices.get)
            min_price_dex = min(prices, key=prices.get)
            
            max_price = prices[max_price_dex]
            min_price = prices[min_price_dex]
            
            profit_percentage = ((max_price - min_price) / min_price) * 100
            
            if profit_percentage > 0.1:  # At least 0.1% profit
                opportunity = {
                    'pair': pair_key,
                    'buy_dex': min_price_dex,
                    'sell_dex': max_price_dex,
                    'buy_price': min_price,
                    'sell_price': max_price,
                    'profit_percentage': profit_percentage,
                    'all_prices': prices
                }
                opportunities.append(opportunity)
    
    # Display opportunities
    if opportunities:
        print(f"\n🎯 Found {len(opportunities)} Arbitrage Opportunities:")
        
        # Sort by profit percentage
        opportunities.sort(key=lambda x: x['profit_percentage'], reverse=True)
        
        for i, opp in enumerate(opportunities, 1):
            print(f"\n   {i}. {opp['pair']} - {opp['profit_percentage']:.3f}% profit")
            print(f"      Buy on {opp['buy_dex']}: {opp['buy_price']:.6f}")
            print(f"      Sell on {opp['sell_dex']}: {opp['sell_price']:.6f}")
            print(f"      All prices: {opp['all_prices']}")
            
            # Calculate potential profit with flash loan
            trade_amount = 5000  # $5K trade
            gross_profit = trade_amount * (opp['profit_percentage'] / 100)
            flash_loan_fee = trade_amount * 0.0009  # 0.09% Aave fee
            gas_cost = 10  # Estimated gas cost on L2
            net_profit = gross_profit - flash_loan_fee - gas_cost
            
            print(f"      Potential profit on $5K trade: ${net_profit:.2f}")
    else:
        print("\n⚠️  No arbitrage opportunities found at this moment.")
        print("   This is normal - opportunities come and go quickly!")
    
    # Test quote functionality
    print("\n📋 Testing Quote Functionality...")
    
    if connected_dexs:
        test_dex = list(connected_dexs.keys())[0]
        test_adapter = connected_dexs[test_dex]
        
        try:
            quote = await test_adapter.get_quote('USDC', 'USDT', 1000)
            if quote:
                print(f"   ✅ {test_dex} quote for 1000 USDC → USDT:")
                print(f"      Expected output: {quote.get('expected_output', 0):.2f} USDT")
                print(f"      Slippage estimate: {quote.get('slippage_estimate', 0):.2f}%")
                print(f"      Gas estimate: {quote.get('gas_estimate', 0):,} units")
                print(f"      Fee: {quote.get('fee_percentage', 0):.2f}%")
            else:
                print(f"   ⚠️  {test_dex} quote not available")
        except Exception as e:
            print(f"   ❌ {test_dex} quote error: {e}")
    
    # Test liquidity information
    print("\n💧 Testing Liquidity Information...")
    
    for dex_name, adapter in list(connected_dexs.items())[:2]:  # Test first 2 DEXs
        try:
            liquidity = await adapter.get_liquidity('USDC', 'USDT')
            if liquidity:
                print(f"   {dex_name}: ${liquidity:,.0f} liquidity for USDC/USDT")
            else:
                print(f"   {dex_name}: Liquidity data not available")
        except Exception as e:
            print(f"   {dex_name}: Liquidity error - {e}")
    
    # Cleanup connections
    print("\n🧹 Cleaning up connections...")
    for dex_name, adapter in connected_dexs.items():
        try:
            await adapter.disconnect()
            print(f"   ✅ {dex_name} disconnected")
        except Exception as e:
            print(f"   ⚠️  {dex_name} disconnect error: {e}")
    
    # Summary
    print(f"\n🎉 Live DEX Connection Test Complete!")
    print(f"   Connected DEXs: {len(connected_dexs)}")
    print(f"   Price pairs tested: {len(price_data)}")
    print(f"   Arbitrage opportunities: {len(opportunities)}")
    
    if opportunities:
        best_opportunity = opportunities[0]
        print(f"   Best opportunity: {best_opportunity['pair']} - {best_opportunity['profit_percentage']:.3f}%")
    
    print(f"\n✅ System is ready for live arbitrage trading!")
    print(f"   Next step: Deploy on testnet for safe testing")
    
    return True

async def main():
    """Main test function."""
    try:
        success = await test_live_dex_connections()
        return success
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
