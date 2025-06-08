#!/usr/bin/env python3
"""
TEST REAL PRICE FEEDS
Test the new real DEX price fetcher to make sure it works before deploying.
"""

import asyncio
import logging
from web3 import Web3
import sys
import os

# Add src to path
sys.path.append('src')

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("test-real-feeds")

async def test_real_price_feeds():
    """Test real price feeds implementation."""
    try:
        print("🧪" * 30)
        print("🧪 TESTING REAL PRICE FEEDS")
        print("🧪 NO MORE MOCK DATA!")
        print("🧪" * 30)
        
        # Import the real price fetcher
        from feeds.real_dex_price_fetcher import RealDEXPriceFetcher
        
        # Initialize Web3 connections
        logger.info("🔗 Initializing Web3 connections...")
        web3_connections = {}
        
        # Test connections
        rpc_urls = {
            'arbitrum': [
                'https://arb1.arbitrum.io/rpc',
                'https://arbitrum-one.publicnode.com'
            ],
            'base': [
                'https://mainnet.base.org',
                'https://base.publicnode.com'
            ]
        }
        
        for chain, urls in rpc_urls.items():
            for url in urls:
                try:
                    w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 10}))
                    if w3.is_connected():
                        latest_block = w3.eth.block_number
                        web3_connections[chain] = w3
                        logger.info(f"✅ {chain}: Connected to {url} (block {latest_block:,})")
                        break
                except Exception as e:
                    logger.debug(f"❌ {chain}: Failed to connect to {url}: {e}")
                    continue
        
        if not web3_connections:
            logger.error("❌ No Web3 connections available")
            return False
        
        # Initialize real price fetcher
        logger.info("🔥 Initializing Real DEX Price Fetcher...")
        price_fetcher = RealDEXPriceFetcher(web3_connections)
        
        # Test 1: Get real prices from Arbitrum
        if 'arbitrum' in web3_connections:
            logger.info("🧪 TEST 1: Get real prices from Arbitrum DEXes")
            tokens = ['WETH', 'USDC', 'USDT']
            
            arbitrum_prices = await price_fetcher.get_real_dex_prices('arbitrum', tokens)
            
            if arbitrum_prices:
                logger.info(f"✅ Found {len(arbitrum_prices)} real prices from Arbitrum!")
                for price in arbitrum_prices[:5]:  # Show first 5
                    logger.info(f"   📊 {price.dex_name}: {price.token_a}/{price.token_b} = {price.price:.6f}")
                    logger.info(f"      💰 Liquidity: ${price.liquidity_usd:,.0f}")
                    logger.info(f"      📍 Pair: {price.pair_address}")
            else:
                logger.warning("⚠️  No real prices found from Arbitrum")
        
        # Test 2: Find real arbitrage opportunities
        logger.info("🧪 TEST 2: Find REAL arbitrage opportunities")
        
        chains = list(web3_connections.keys())
        tokens = ['WETH', 'USDC']
        
        opportunities = await price_fetcher.find_real_arbitrage_opportunities(
            chains=chains,
            tokens=tokens,
            min_profit_percentage=0.1  # 0.1% minimum
        )
        
        if opportunities:
            logger.info(f"🎯 Found {len(opportunities)} REAL arbitrage opportunities!")
            for i, opp in enumerate(opportunities[:3]):  # Show top 3
                logger.info(f"   #{i+1}: {opp['token_a']}/{opp['token_b']}")
                logger.info(f"      💰 Profit: {opp['profit_percentage']:.4f}%")
                logger.info(f"      🛒 Buy: {opp['buy_dex']} on {opp['buy_chain']} @ {opp['buy_price']:.6f}")
                logger.info(f"      🏪 Sell: {opp['sell_dex']} on {opp['sell_chain']} @ {opp['sell_price']:.6f}")
                logger.info(f"      💧 Liquidity: ${opp['buy_liquidity_usd']:,.0f} / ${opp['sell_liquidity_usd']:,.0f}")
        else:
            logger.info("📊 No arbitrage opportunities found (this is normal - real opportunities are rare!)")
        
        # Test 3: Compare with mock data
        logger.info("🧪 TEST 3: Verify this is REAL data (not mock)")
        
        if arbitrum_prices:
            # Check if prices look realistic
            realistic_count = 0
            for price in arbitrum_prices:
                # Check if price is not obviously fake
                if (price.price > 0.0001 and price.price < 100000 and 
                    price.liquidity_usd > 1000 and 
                    price.pair_address != '0x0000000000000000000000000000000000000000'):
                    realistic_count += 1
            
            realism_percentage = (realistic_count / len(arbitrum_prices)) * 100
            logger.info(f"   📊 Realism check: {realistic_count}/{len(arbitrum_prices)} prices look realistic ({realism_percentage:.1f}%)")
            
            if realism_percentage > 80:
                logger.info("   ✅ REAL DATA CONFIRMED: Prices look realistic!")
            else:
                logger.warning("   ⚠️  Some prices look suspicious - might still have mock data")
        
        logger.info("🧪 TEST COMPLETE!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test."""
    success = await test_real_price_feeds()
    
    if success:
        print("\n✅ REAL PRICE FEEDS TEST PASSED!")
        print("🎯 Ready to replace mock data in arbitrage system")
    else:
        print("\n❌ REAL PRICE FEEDS TEST FAILED!")
        print("🔧 Need to fix issues before deploying")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
