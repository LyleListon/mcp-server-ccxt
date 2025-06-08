#!/usr/bin/env python3
"""
🌉 CROSS-CHAIN OPPORTUNITY ANALYZER
Analyze your 43-DEX scan data for cross-chain arbitrage goldmines!
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from collections import defaultdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_cross_chain_opportunities():
    """Analyze current scan data for cross-chain opportunities."""
    
    print("🌉 CROSS-CHAIN OPPORTUNITY ANALYZER")
    print("=" * 60)
    
    try:
        from feeds.multi_dex_aggregator import MultiDEXAggregator
        
        # Initialize aggregator
        config = {
            'networks': ['arbitrum', 'base', 'optimism'],
            'alchemy_api_key': os.getenv('ALCHEMY_API_KEY')
        }
        
        print("🔍 Initializing 43-DEX aggregator...")
        aggregator = MultiDEXAggregator(config)
        
        print("📊 Fetching current prices across all DEXs...")
        all_dex_prices = await aggregator.get_all_dex_prices()

        total_prices = sum(len(prices) for prices in all_dex_prices.values())
        print(f"✅ Fetched {total_prices} price points from {len(all_dex_prices)} DEXs")
        print()

        # Organize prices by token and chain
        tokens_by_chain = defaultdict(lambda: defaultdict(list))

        for dex_name, dex_prices in all_dex_prices.items():
            for price_data in dex_prices:
                try:
                    token = price_data.token
                    chain = price_data.chain
                    price = price_data.price

                    if price > 0:
                        tokens_by_chain[token][chain].append({
                            'dex': dex_name,
                            'price': price,
                            'liquidity': getattr(price_data, 'liquidity', 0),
                            'timestamp': getattr(price_data, 'timestamp', 0)
                        })
                except Exception as e:
                    continue
        
        print(f"🎯 Tokens found across chains: {len(tokens_by_chain)}")
        
        # Find cross-chain opportunities
        cross_chain_opportunities = []
        
        for token, chains in tokens_by_chain.items():
            if len(chains) > 1:  # Token exists on multiple chains
                chain_list = list(chains.keys())
                
                for i, chain1 in enumerate(chain_list):
                    for chain2 in chain_list[i+1:]:
                        # Get price ranges on each chain
                        chain1_prices = [p['price'] for p in chains[chain1]]
                        chain2_prices = [p['price'] for p in chains[chain2]]
                        
                        if chain1_prices and chain2_prices:
                            min_chain1 = min(chain1_prices)
                            max_chain1 = max(chain1_prices)
                            min_chain2 = min(chain2_prices)
                            max_chain2 = max(chain2_prices)
                            
                            # Check both directions
                            # Direction 1: Buy on chain1, sell on chain2
                            if max_chain2 > min_chain1:
                                profit_pct = ((max_chain2 - min_chain1) / min_chain1) * 100
                                if profit_pct > 0.5:  # 0.5% minimum
                                    cross_chain_opportunities.append({
                                        'token': token,
                                        'buy_chain': chain1,
                                        'sell_chain': chain2,
                                        'buy_price': min_chain1,
                                        'sell_price': max_chain2,
                                        'profit_pct': profit_pct,
                                        'direction': f"{chain1} → {chain2}"
                                    })
                            
                            # Direction 2: Buy on chain2, sell on chain1
                            if max_chain1 > min_chain2:
                                profit_pct = ((max_chain1 - min_chain2) / min_chain2) * 100
                                if profit_pct > 0.5:  # 0.5% minimum
                                    cross_chain_opportunities.append({
                                        'token': token,
                                        'buy_chain': chain2,
                                        'sell_chain': chain1,
                                        'buy_price': min_chain2,
                                        'sell_price': max_chain1,
                                        'profit_pct': profit_pct,
                                        'direction': f"{chain2} → {chain1}"
                                    })
        
        # Sort by profitability
        cross_chain_opportunities.sort(key=lambda x: x['profit_pct'], reverse=True)
        
        print("🌉 CROSS-CHAIN ARBITRAGE OPPORTUNITIES")
        print("=" * 60)
        print(f"Total opportunities found: {len(cross_chain_opportunities)}")
        print()
        
        if cross_chain_opportunities:
            print("🏆 TOP 15 CROSS-CHAIN OPPORTUNITIES:")
            print("-" * 60)
            
            for i, opp in enumerate(cross_chain_opportunities[:15], 1):
                print(f"{i:2d}. {opp['token']} - {opp['profit_pct']:.2f}% profit")
                print(f"    Direction: {opp['direction']}")
                print(f"    Buy: ${opp['buy_price']:.6f} on {opp['buy_chain']}")
                print(f"    Sell: ${opp['sell_price']:.6f} on {opp['sell_chain']}")
                
                # Calculate potential profit on $1000 trade
                profit_usd = (opp['profit_pct'] / 100) * 1000
                print(f"    💰 Profit on $1000: ${profit_usd:.2f}")
                print()
            
            # Analyze by token
            token_counts = defaultdict(int)
            for opp in cross_chain_opportunities:
                token_counts[opp['token']] += 1
            
            print("📊 OPPORTUNITIES BY TOKEN:")
            print("-" * 30)
            for token, count in sorted(token_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"   {token}: {count} opportunities")
            
            print()
            
            # Analyze by chain pair
            chain_pair_counts = defaultdict(int)
            for opp in cross_chain_opportunities:
                pair = f"{opp['buy_chain']} → {opp['sell_chain']}"
                chain_pair_counts[pair] += 1
            
            print("🌉 OPPORTUNITIES BY CHAIN PAIR:")
            print("-" * 35)
            for pair, count in sorted(chain_pair_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   {pair}: {count} opportunities")
            
        else:
            print("❌ No cross-chain opportunities found")
            print("This could mean:")
            print("   • Markets are very efficient")
            print("   • Bridge costs exceed profit margins")
            print("   • Need to scan more frequently")
        
        print("\n" + "=" * 60)
        print("✅ Cross-chain analysis complete!")
        
        return cross_chain_opportunities
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        logger.error(f"Analysis error: {e}")
        return []

async def main():
    """Main analysis function."""
    
    if not os.getenv('ALCHEMY_API_KEY'):
        print("❌ ALCHEMY_API_KEY not found!")
        return False
    
    opportunities = await analyze_cross_chain_opportunities()
    return len(opportunities) > 0

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Analysis stopped by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)
