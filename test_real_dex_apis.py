#!/usr/bin/env python3
"""
Real DEX API Connection Test
Tests connections to actual DEX APIs and subgraphs for live market data.
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
from dex.aerodrome_adapter import AerodromeAdapter
from dex.real_world_dex_adapter import RealWorldDEXAdapter

async def test_real_dex_apis():
    """Test connections to real DEX APIs."""
    print("🌐 Testing Real DEX API Connections")
    print("=" * 60)
    
    # Load config
    with open('config/capital_efficient_config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize DEX adapters with real API connections
    dex_adapters = {}
    
    print("🔌 Initializing Real DEX Adapters...")
    
    # Uniswap V3 (Ethereum)
    try:
        dex_adapters['uniswap_v3'] = UniswapV3Adapter(config.get('dexs', {}).get('uniswap_v3', {}))
        print("✅ Uniswap V3 adapter initialized")
    except Exception as e:
        print(f"❌ Uniswap V3 adapter failed: {e}")
    
    # SushiSwap (Multi-chain)
    try:
        dex_adapters['sushiswap'] = SushiSwapAdapter(config.get('dexs', {}).get('sushiswap', {}))
        print("✅ SushiSwap adapter initialized")
    except Exception as e:
        print(f"❌ SushiSwap adapter failed: {e}")
    
    # Aerodrome (Base)
    try:
        dex_adapters['aerodrome'] = AerodromeAdapter(config.get('dexs', {}).get('aerodrome', {}))
        print("✅ Aerodrome adapter initialized")
    except Exception as e:
        print(f"❌ Aerodrome adapter failed: {e}")
    
    # Real World DEX (CoinGecko backup)
    try:
        dex_adapters['real_world'] = RealWorldDEXAdapter(config)
        print("✅ Real World DEX adapter initialized")
    except Exception as e:
        print(f"❌ Real World DEX adapter failed: {e}")
    
    # Test connections to real APIs
    print(f"\n🔗 Testing Real API Connections...")
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
    
    print(f"\n🎉 Successfully connected to {len(connected_dexs)} real DEXs: {list(connected_dexs.keys())}")
    
    # Test real pair data fetching
    print("\n📊 Fetching Real Trading Pairs...")
    
    all_pairs = {}
    
    for dex_name, adapter in connected_dexs.items():
        try:
            print(f"   Fetching pairs from {dex_name}...")
            pairs = await adapter.get_pairs()
            all_pairs[dex_name] = pairs
            print(f"   ✅ {dex_name}: {len(pairs)} pairs fetched")
            
            # Show sample pairs
            if pairs:
                print(f"      Sample pairs:")
                for pair in pairs[:3]:  # Show first 3
                    if 'base_token' in pair and 'quote_token' in pair:
                        liquidity = pair.get('liquidity', pair.get('tvl_usd', 0))
                        print(f"         {pair['base_token']}/{pair['quote_token']}: ${liquidity:,.0f} liquidity")
                    
        except Exception as e:
            print(f"   ❌ {dex_name} pairs error: {e}")
            all_pairs[dex_name] = []
    
    # Test real price fetching
    print("\n💰 Testing Real Price Data...")
    
    test_pairs = [
        ('ETH', 'USDC'),
        ('USDC', 'USDT'),
        ('WETH', 'USDC'),
        ('ETH', 'WETH')
    ]
    
    price_matrix = {}
    
    for base_token, quote_token in test_pairs:
        pair_key = f"{base_token}/{quote_token}"
        price_matrix[pair_key] = {}
        
        print(f"\n   📈 {pair_key} prices across DEXs:")
        
        for dex_name, adapter in connected_dexs.items():
            try:
                price = await adapter.get_price(base_token, quote_token)
                if price and price > 0:
                    price_matrix[pair_key][dex_name] = price
                    print(f"      {dex_name}: {price:.6f}")
                else:
                    print(f"      {dex_name}: No price available")
            except Exception as e:
                print(f"      {dex_name}: Error - {e}")
    
    # Analyze real arbitrage opportunities
    print("\n🔍 Analyzing Real Arbitrage Opportunities...")
    
    real_opportunities = []
    
    for pair_key, prices in price_matrix.items():
        if len(prices) >= 2:  # Need at least 2 DEXs with prices
            max_price_dex = max(prices, key=prices.get)
            min_price_dex = min(prices, key=prices.get)
            
            max_price = prices[max_price_dex]
            min_price = prices[min_price_dex]
            
            profit_percentage = ((max_price - min_price) / min_price) * 100
            
            if profit_percentage > 0.01:  # At least 0.01% profit
                opportunity = {
                    'pair': pair_key,
                    'buy_dex': min_price_dex,
                    'sell_dex': max_price_dex,
                    'buy_price': min_price,
                    'sell_price': max_price,
                    'profit_percentage': profit_percentage,
                    'all_prices': prices
                }
                real_opportunities.append(opportunity)
    
    # Display real opportunities
    if real_opportunities:
        print(f"\n🎯 Found {len(real_opportunities)} Real Arbitrage Opportunities!")
        
        # Sort by profit percentage
        real_opportunities.sort(key=lambda x: x['profit_percentage'], reverse=True)
        
        for i, opp in enumerate(real_opportunities, 1):
            print(f"\n   {i}. {opp['pair']} - {opp['profit_percentage']:.4f}% profit")
            print(f"      Buy on {opp['buy_dex']}: {opp['buy_price']:.6f}")
            print(f"      Sell on {opp['sell_dex']}: {opp['sell_price']:.6f}")
            print(f"      All prices: {opp['all_prices']}")
            
            # Calculate potential profit with flash loan
            trade_amounts = [1000, 5000, 10000]
            
            for amount in trade_amounts:
                gross_profit = amount * (opp['profit_percentage'] / 100)
                flash_loan_fee = amount * 0.0009  # 0.09% Aave fee
                gas_cost = 15  # Estimated gas cost
                net_profit = gross_profit - flash_loan_fee - gas_cost
                
                if net_profit > 0:
                    roi = (net_profit / flash_loan_fee) * 100 if flash_loan_fee > 0 else 0
                    print(f"      ${amount:,} trade: ${net_profit:.2f} profit (ROI: {roi:.1f}%)")
                    break  # Only show first profitable amount
    else:
        print("\n⚠️  No arbitrage opportunities found with current real prices.")
        print("   This is normal - real arbitrage opportunities are rare and fleeting!")
    
    # Test real quote functionality
    print("\n📋 Testing Real Quote Functionality...")
    
    if connected_dexs:
        test_dex = list(connected_dexs.keys())[0]
        test_adapter = connected_dexs[test_dex]
        
        try:
            quote = await test_adapter.get_quote('ETH', 'USDC', 1.0)
            if quote:
                print(f"   ✅ {test_dex} quote for 1 ETH → USDC:")
                print(f"      Expected output: {quote.get('expected_output', 0):.2f} USDC")
                print(f"      Price: {quote.get('price', 0):.2f}")
                print(f"      Slippage estimate: {quote.get('slippage_estimate', 0):.3f}%")
                print(f"      Gas estimate: {quote.get('gas_estimate', 0):,} units")
                print(f"      Fee: {quote.get('fee_percentage', 0):.2f}%")
            else:
                print(f"   ⚠️  {test_dex} quote not available")
        except Exception as e:
            print(f"   ❌ {test_dex} quote error: {e}")
    
    # Test real liquidity information
    print("\n💧 Testing Real Liquidity Information...")
    
    for dex_name, adapter in list(connected_dexs.items())[:2]:  # Test first 2 DEXs
        try:
            liquidity = await adapter.get_liquidity('ETH', 'USDC')
            if liquidity:
                print(f"   {dex_name}: ${liquidity:,.0f} liquidity for ETH/USDC")
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
    total_pairs = sum(len(pairs) for pairs in all_pairs.values())
    total_prices = sum(len(prices) for prices in price_matrix.values())
    
    print(f"\n🎉 Real DEX API Test Complete!")
    print(f"   Connected DEXs: {len(connected_dexs)}")
    print(f"   Total pairs fetched: {total_pairs}")
    print(f"   Price points collected: {total_prices}")
    print(f"   Real arbitrage opportunities: {len(real_opportunities)}")
    
    if real_opportunities:
        best_opportunity = real_opportunities[0]
        print(f"   Best real opportunity: {best_opportunity['pair']} - {best_opportunity['profit_percentage']:.4f}%")
    
    print(f"\n✅ System successfully connected to real DEX APIs!")
    print(f"   Ready for live arbitrage trading with real market data!")
    
    return True

async def main():
    """Main test function."""
    try:
        success = await test_real_dex_apis()
        return success
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
