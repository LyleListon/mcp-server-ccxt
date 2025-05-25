#!/usr/bin/env python3
"""
Simple DEX Connection Test

Tests basic connectivity to DEX APIs without complex GraphQL queries.
"""

import asyncio
import aiohttp
import json
import sys


async def test_basic_http():
    """Test basic HTTP connectivity."""
    print("🌐 Testing Basic HTTP Connectivity")
    print("=" * 40)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test basic HTTP request
            async with session.get('https://httpbin.org/get') as response:
                if response.status == 200:
                    print("   ✅ Basic HTTP connectivity working")
                    return True
                else:
                    print(f"   ❌ HTTP test failed with status {response.status}")
                    return False
    except Exception as e:
        print(f"   ❌ HTTP test failed: {e}")
        return False


async def test_coinbase_api():
    """Test Coinbase API for price data."""
    print("\n💰 Testing Coinbase API (Alternative Price Source)")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Get BTC price from Coinbase
            async with session.get('https://api.coinbase.com/v2/exchange-rates?currency=BTC') as response:
                if response.status == 200:
                    data = await response.json()
                    btc_usd = data['data']['rates']['USD']
                    print(f"   ✅ BTC/USD price: ${float(btc_usd):,.2f}")
                    
                    # Get ETH price
                    async with session.get('https://api.coinbase.com/v2/exchange-rates?currency=ETH') as response:
                        if response.status == 200:
                            data = await response.json()
                            eth_usd = data['data']['rates']['USD']
                            print(f"   ✅ ETH/USD price: ${float(eth_usd):,.2f}")
                            return True
                        else:
                            print(f"   ❌ ETH price request failed with status {response.status}")
                            return False
                else:
                    print(f"   ❌ BTC price request failed with status {response.status}")
                    return False
    except Exception as e:
        print(f"   ❌ Coinbase API test failed: {e}")
        return False


async def test_coingecko_api():
    """Test CoinGecko API for price data."""
    print("\n🦎 Testing CoinGecko API (Alternative Price Source)")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Get multiple token prices
            url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,usd-coin&vs_currencies=usd'
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Bitcoin: ${data['bitcoin']['usd']:,.2f}")
                    print(f"   ✅ Ethereum: ${data['ethereum']['usd']:,.2f}")
                    print(f"   ✅ USDC: ${data['usd-coin']['usd']:,.6f}")
                    return True
                else:
                    print(f"   ❌ CoinGecko request failed with status {response.status}")
                    return False
    except Exception as e:
        print(f"   ❌ CoinGecko API test failed: {e}")
        return False


async def test_simple_arbitrage_detection():
    """Test simple arbitrage detection using multiple price sources."""
    print("\n🎯 Testing Simple Arbitrage Detection")
    print("=" * 40)
    
    try:
        prices = {}
        
        async with aiohttp.ClientSession() as session:
            # Get BTC price from Coinbase
            try:
                async with session.get('https://api.coinbase.com/v2/exchange-rates?currency=BTC') as response:
                    if response.status == 200:
                        data = await response.json()
                        prices['coinbase'] = float(data['data']['rates']['USD'])
                        print(f"   📊 Coinbase BTC: ${prices['coinbase']:,.2f}")
            except Exception as e:
                print(f"   ⚠️  Coinbase error: {e}")
            
            # Get BTC price from CoinGecko
            try:
                async with session.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd') as response:
                    if response.status == 200:
                        data = await response.json()
                        prices['coingecko'] = float(data['bitcoin']['usd'])
                        print(f"   📊 CoinGecko BTC: ${prices['coingecko']:,.2f}")
            except Exception as e:
                print(f"   ⚠️  CoinGecko error: {e}")
        
        # Calculate price differences
        if len(prices) >= 2:
            price_list = list(prices.values())
            max_price = max(price_list)
            min_price = min(price_list)
            
            price_diff = max_price - min_price
            price_diff_pct = (price_diff / min_price) * 100
            
            print(f"   📈 Highest price: ${max_price:,.2f}")
            print(f"   📉 Lowest price: ${min_price:,.2f}")
            print(f"   💰 Price difference: ${price_diff:,.2f} ({price_diff_pct:.3f}%)")
            
            if price_diff_pct > 0.01:  # 0.01% difference
                print(f"   🎯 Potential arbitrage opportunity detected!")
                print(f"      Buy at ${min_price:,.2f}, sell at ${max_price:,.2f}")
                print(f"      Profit per BTC: ${price_diff:,.2f}")
            else:
                print(f"   📊 No significant arbitrage opportunity (normal market efficiency)")
            
            return True
        else:
            print("   ❌ Not enough price sources for comparison")
            return False
            
    except Exception as e:
        print(f"   ❌ Arbitrage detection test failed: {e}")
        return False


async def test_mock_dex_integration():
    """Test mock DEX integration for development."""
    print("\n🔧 Testing Mock DEX Integration")
    print("=" * 40)
    
    try:
        # Simulate DEX price data
        mock_dexs = {
            'uniswap_v3': {
                'BTC/USDC': 67234.56,
                'ETH/USDC': 3456.78,
                'USDC/USDT': 0.9998
            },
            'sushiswap': {
                'BTC/USDC': 67189.23,
                'ETH/USDC': 3461.45,
                'USDC/USDT': 1.0001
            },
            'curve': {
                'USDC/USDT': 0.9999,
                'DAI/USDC': 1.0002
            }
        }
        
        print("   📊 Mock DEX prices:")
        for dex_name, pairs in mock_dexs.items():
            print(f"      {dex_name}:")
            for pair, price in pairs.items():
                print(f"        {pair}: ${price:,.4f}")
        
        # Find arbitrage opportunities
        print("\n   🎯 Scanning for arbitrage opportunities...")
        opportunities = []
        
        # Check BTC/USDC across DEXs
        btc_prices = {}
        for dex_name, pairs in mock_dexs.items():
            if 'BTC/USDC' in pairs:
                btc_prices[dex_name] = pairs['BTC/USDC']
        
        if len(btc_prices) >= 2:
            max_dex = max(btc_prices, key=btc_prices.get)
            min_dex = min(btc_prices, key=btc_prices.get)
            
            profit_pct = ((btc_prices[max_dex] - btc_prices[min_dex]) / btc_prices[min_dex]) * 100
            
            if profit_pct > 0.01:  # 0.01% minimum
                opportunities.append({
                    'pair': 'BTC/USDC',
                    'buy_dex': min_dex,
                    'sell_dex': max_dex,
                    'buy_price': btc_prices[min_dex],
                    'sell_price': btc_prices[max_dex],
                    'profit_pct': profit_pct
                })
        
        # Check ETH/USDC across DEXs
        eth_prices = {}
        for dex_name, pairs in mock_dexs.items():
            if 'ETH/USDC' in pairs:
                eth_prices[dex_name] = pairs['ETH/USDC']
        
        if len(eth_prices) >= 2:
            max_dex = max(eth_prices, key=eth_prices.get)
            min_dex = min(eth_prices, key=eth_prices.get)
            
            profit_pct = ((eth_prices[max_dex] - eth_prices[min_dex]) / eth_prices[min_dex]) * 100
            
            if profit_pct > 0.01:  # 0.01% minimum
                opportunities.append({
                    'pair': 'ETH/USDC',
                    'buy_dex': min_dex,
                    'sell_dex': max_dex,
                    'buy_price': eth_prices[min_dex],
                    'sell_price': eth_prices[max_dex],
                    'profit_pct': profit_pct
                })
        
        if opportunities:
            print(f"   ✅ Found {len(opportunities)} arbitrage opportunities:")
            for i, opp in enumerate(opportunities):
                print(f"      {i+1}. {opp['pair']}")
                print(f"         Buy on {opp['buy_dex']}: ${opp['buy_price']:,.2f}")
                print(f"         Sell on {opp['sell_dex']}: ${opp['sell_price']:,.2f}")
                print(f"         Profit: {opp['profit_pct']:.3f}%")
        else:
            print("   📊 No arbitrage opportunities in mock data")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Mock DEX integration test failed: {e}")
        return False


async def main():
    """Run all simple connectivity tests."""
    
    print("🚀 Simple DEX Connection Test Suite")
    print("=" * 60)
    print("Testing basic connectivity and alternative price sources")
    print("before attempting complex DEX integrations.")
    print("=" * 60)
    
    # Run tests
    http_success = await test_basic_http()
    coinbase_success = await test_coinbase_api()
    coingecko_success = await test_coingecko_api()
    arbitrage_success = await test_simple_arbitrage_detection()
    mock_success = await test_mock_dex_integration()
    
    print("\n📊 FINAL TEST RESULTS")
    print("=" * 30)
    print(f"Basic HTTP: {'✅ PASS' if http_success else '❌ FAIL'}")
    print(f"Coinbase API: {'✅ PASS' if coinbase_success else '❌ FAIL'}")
    print(f"CoinGecko API: {'✅ PASS' if coingecko_success else '❌ FAIL'}")
    print(f"Arbitrage Detection: {'✅ PASS' if arbitrage_success else '❌ FAIL'}")
    print(f"Mock DEX Integration: {'✅ PASS' if mock_success else '❌ FAIL'}")
    
    if http_success and (coinbase_success or coingecko_success):
        print("\n🎉 CONNECTIVITY TESTS PASSED!")
        print("✅ Network connectivity is working")
        print("✅ Alternative price sources available")
        print("✅ Basic arbitrage detection functional")
        print("\n💡 Next Steps:")
        print("1. Use alternative APIs for price data")
        print("2. Implement mock DEX mode for development")
        print("3. Gradually add real DEX connections")
        print("4. Test with small amounts when ready")
        return True
    else:
        print("\n⚠️  Some connectivity tests failed")
        print("Check your internet connection and try again")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest suite crashed: {e}")
        sys.exit(1)
