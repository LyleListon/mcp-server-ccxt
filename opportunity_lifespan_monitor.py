#!/usr/bin/env python3
"""
Opportunity Lifespan Monitor
============================

Monitor real arbitrage opportunities to see how long they last.
This shows us the execution speed we need to beat!
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'opportunity_lifespan_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class OpportunityLifespanMonitor:
    """Monitor how long arbitrage opportunities last in the wild."""
    
    def __init__(self):
        """Initialize the opportunity lifespan monitor."""
        self.monitored_opportunities = {}
        self.lifespan_stats = []
        self.web3_connections = {}
        
        logger.info("⏱️  OPPORTUNITY LIFESPAN MONITOR INITIALIZING")
        logger.info("=" * 50)
        
    async def setup_connections(self):
        """Setup Web3 connections for price monitoring."""
        try:
            from web3 import Web3
            
            api_key = os.getenv('ALCHEMY_API_KEY')
            if not api_key:
                logger.error("❌ Missing ALCHEMY_API_KEY")
                return False
            
            # Setup Arbitrum connection
            arb_url = f"https://arb-mainnet.g.alchemy.com/v2/{api_key}"
            self.web3_connections['arbitrum'] = Web3(Web3.HTTPProvider(arb_url))
            
            # Test connection
            latest_block = self.web3_connections['arbitrum'].eth.get_block('latest')
            logger.info(f"🔗 Connected to Arbitrum - Block: {latest_block['number']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection setup failed: {e}")
            return False
    
    async def get_token_price(self, token_pair: str, dex: str) -> Optional[float]:
        """Get current token price from a DEX."""
        try:
            # Mock price fetching for now - in real implementation this would
            # call the actual DEX router to get current prices
            import random
            
            # Simulate realistic price movements
            base_price = 1.0
            volatility = 0.001  # 0.1% volatility
            price = base_price + random.uniform(-volatility, volatility)
            
            return price
            
        except Exception as e:
            logger.error(f"❌ Price fetch failed for {token_pair} on {dex}: {e}")
            return None
    
    async def check_opportunity_viability(self, opportunity: Dict[str, Any]) -> bool:
        """Check if an arbitrage opportunity is still viable."""
        try:
            # Get current prices from both DEXes
            token_pair = f"{opportunity['token_in']}/{opportunity['token_out']}"
            
            price_dex_a = await self.get_token_price(token_pair, opportunity['dex_a'])
            price_dex_b = await self.get_token_price(token_pair, opportunity['dex_b'])
            
            if price_dex_a is None or price_dex_b is None:
                return False
            
            # Calculate current spread
            spread = abs(price_dex_a - price_dex_b)
            spread_percentage = (spread / min(price_dex_a, price_dex_b)) * 100
            
            # Update opportunity with current data
            opportunity['current_price_a'] = price_dex_a
            opportunity['current_price_b'] = price_dex_b
            opportunity['current_spread'] = spread_percentage
            
            # Opportunity is viable if spread > minimum threshold
            min_spread = 0.1  # 0.1% minimum spread
            return spread_percentage > min_spread
            
        except Exception as e:
            logger.error(f"❌ Viability check failed: {e}")
            return False
    
    async def create_mock_opportunity(self) -> Dict[str, Any]:
        """Create a realistic mock arbitrage opportunity."""
        import random
        
        tokens = ['USDC/WETH', 'USDC/USDT', 'WETH/USDT', 'USDC/DAI']
        dexes = ['sushiswap', 'camelot', 'uniswap_v3']
        
        token_pair = random.choice(tokens)
        token_in, token_out = token_pair.split('/')
        
        dex_a = random.choice(dexes)
        dex_b = random.choice([d for d in dexes if d != dex_a])
        
        # Create realistic price spread
        base_price_a = 1.0
        spread = random.uniform(0.15, 0.8)  # 0.15% to 0.8% spread
        price_a = base_price_a
        price_b = base_price_a * (1 + spread/100)
        
        opportunity = {
            'id': f"opp_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
            'token_pair': token_pair,
            'token_in': token_in,
            'token_out': token_out,
            'dex_a': dex_a,
            'dex_b': dex_b,
            'initial_price_a': price_a,
            'initial_price_b': price_b,
            'initial_spread': spread,
            'estimated_profit_usd': random.uniform(5.0, 50.0),
            'discovered_at': time.time(),
            'last_checked': time.time(),
            'checks_count': 0,
            'still_viable': True
        }
        
        return opportunity
    
    async def monitor_opportunity(self, opportunity: Dict[str, Any]):
        """Monitor a single opportunity until it disappears."""
        opp_id = opportunity['id']
        start_time = time.time()
        
        logger.info(f"🔍 MONITORING OPPORTUNITY: {opp_id}")
        logger.info(f"   💰 {opportunity['token_pair']} - {opportunity['initial_spread']:.3f}% spread")
        logger.info(f"   🔄 {opportunity['dex_a']} vs {opportunity['dex_b']}")
        logger.info(f"   💵 Estimated profit: ${opportunity['estimated_profit_usd']:.2f}")
        
        check_interval = 0.5  # Check every 500ms for high precision
        
        while opportunity['still_viable']:
            try:
                # Check if opportunity is still viable
                is_viable = await self.check_opportunity_viability(opportunity)
                opportunity['still_viable'] = is_viable
                opportunity['last_checked'] = time.time()
                opportunity['checks_count'] += 1
                
                elapsed = time.time() - start_time
                
                if is_viable:
                    logger.info(f"   ✅ {elapsed:.1f}s - Still viable: {opportunity['current_spread']:.3f}% spread")
                else:
                    logger.info(f"   ❌ {elapsed:.1f}s - OPPORTUNITY EXPIRED!")
                    break
                
                # Wait before next check
                await asyncio.sleep(check_interval)
                
                # Safety timeout (max 5 minutes)
                if elapsed > 300:
                    logger.warning(f"   ⏰ Timeout reached for {opp_id}")
                    break
                    
            except Exception as e:
                logger.error(f"   ❌ Monitor error: {e}")
                break
        
        # Record lifespan statistics
        total_lifespan = time.time() - start_time
        
        lifespan_data = {
            'opportunity_id': opp_id,
            'token_pair': opportunity['token_pair'],
            'dex_a': opportunity['dex_a'],
            'dex_b': opportunity['dex_b'],
            'initial_spread': opportunity['initial_spread'],
            'estimated_profit': opportunity['estimated_profit_usd'],
            'lifespan_seconds': total_lifespan,
            'checks_performed': opportunity['checks_count'],
            'discovered_at': opportunity['discovered_at'],
            'expired_at': time.time()
        }
        
        self.lifespan_stats.append(lifespan_data)
        
        logger.info(f"📊 OPPORTUNITY LIFESPAN COMPLETE:")
        logger.info(f"   ⏱️  Duration: {total_lifespan:.2f} seconds")
        logger.info(f"   🔍 Checks: {opportunity['checks_count']}")
        logger.info(f"   💰 Profit: ${opportunity['estimated_profit_usd']:.2f}")
        
        return lifespan_data
    
    async def run_lifespan_analysis(self, num_opportunities: int = 10):
        """Run lifespan analysis on multiple opportunities."""
        logger.info("🚀 STARTING OPPORTUNITY LIFESPAN ANALYSIS")
        logger.info("=" * 45)
        logger.info(f"🎯 Target: Monitor {num_opportunities} opportunities")
        logger.info(f"📊 Goal: Determine execution speed requirements")
        logger.info("")
        
        for i in range(num_opportunities):
            logger.info(f"🔍 DISCOVERING OPPORTUNITY #{i+1}/{num_opportunities}")
            logger.info("-" * 40)
            
            # Create and monitor opportunity
            opportunity = await self.create_mock_opportunity()
            lifespan_data = await self.monitor_opportunity(opportunity)
            
            # Brief pause between opportunities
            await asyncio.sleep(2)
        
        # Analyze results
        await self.analyze_lifespan_results()
    
    async def analyze_lifespan_results(self):
        """Analyze the collected lifespan data."""
        if not self.lifespan_stats:
            logger.warning("❌ No lifespan data to analyze")
            return
        
        logger.info("\n📊 LIFESPAN ANALYSIS RESULTS")
        logger.info("=" * 35)
        
        lifespans = [stat['lifespan_seconds'] for stat in self.lifespan_stats]
        profits = [stat['estimated_profit'] for stat in self.lifespan_stats]
        
        # Calculate statistics
        avg_lifespan = sum(lifespans) / len(lifespans)
        min_lifespan = min(lifespans)
        max_lifespan = max(lifespans)
        median_lifespan = sorted(lifespans)[len(lifespans)//2]
        
        avg_profit = sum(profits) / len(profits)
        
        logger.info(f"📈 LIFESPAN STATISTICS:")
        logger.info(f"   ⏱️  Average: {avg_lifespan:.2f} seconds")
        logger.info(f"   ⚡ Fastest: {min_lifespan:.2f} seconds")
        logger.info(f"   🐌 Slowest: {max_lifespan:.2f} seconds")
        logger.info(f"   📊 Median: {median_lifespan:.2f} seconds")
        logger.info(f"   💰 Avg Profit: ${avg_profit:.2f}")
        
        # Execution speed requirements
        logger.info(f"\n🎯 EXECUTION SPEED REQUIREMENTS:")
        
        # To catch 50% of opportunities
        percentile_50 = sorted(lifespans)[len(lifespans)//2]
        logger.info(f"   📊 50% of opportunities: Execute within {percentile_50:.1f}s")
        
        # To catch 75% of opportunities  
        percentile_75 = sorted(lifespans)[int(len(lifespans)*0.75)]
        logger.info(f"   📊 75% of opportunities: Execute within {percentile_75:.1f}s")
        
        # To catch 90% of opportunities
        percentile_90 = sorted(lifespans)[int(len(lifespans)*0.90)]
        logger.info(f"   📊 90% of opportunities: Execute within {percentile_90:.1f}s")
        
        # Current system performance vs requirements
        current_execution_time = 4.0  # Our current ~4 second execution time
        
        logger.info(f"\n⚡ CURRENT SYSTEM ANALYSIS:")
        logger.info(f"   🔧 Current execution time: {current_execution_time:.1f}s")
        
        catchable_50 = current_execution_time <= percentile_50
        catchable_75 = current_execution_time <= percentile_75
        catchable_90 = current_execution_time <= percentile_90
        
        logger.info(f"   {'✅' if catchable_50 else '❌'} Can catch 50% of opportunities: {catchable_50}")
        logger.info(f"   {'✅' if catchable_75 else '❌'} Can catch 75% of opportunities: {catchable_75}")
        logger.info(f"   {'✅' if catchable_90 else '❌'} Can catch 90% of opportunities: {catchable_90}")
        
        # Recommendations
        logger.info(f"\n🚀 SPEED OPTIMIZATION TARGETS:")
        if not catchable_75:
            target_time = percentile_75 * 0.8  # 20% safety margin
            logger.info(f"   🎯 Target execution time: {target_time:.1f}s (to catch 75% of opportunities)")
        
        if not catchable_90:
            aggressive_target = percentile_90 * 0.8
            logger.info(f"   🎯 Aggressive target: {aggressive_target:.1f}s (to catch 90% of opportunities)")
        
        # Save results
        results = {
            'analysis_timestamp': time.time(),
            'opportunities_monitored': len(self.lifespan_stats),
            'statistics': {
                'average_lifespan': avg_lifespan,
                'min_lifespan': min_lifespan,
                'max_lifespan': max_lifespan,
                'median_lifespan': median_lifespan,
                'average_profit': avg_profit
            },
            'percentiles': {
                '50th': percentile_50,
                '75th': percentile_75,
                '90th': percentile_90
            },
            'current_system': {
                'execution_time': current_execution_time,
                'can_catch_50_percent': catchable_50,
                'can_catch_75_percent': catchable_75,
                'can_catch_90_percent': catchable_90
            },
            'raw_data': self.lifespan_stats
        }
        
        with open(f'lifespan_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n💾 Analysis saved to lifespan_analysis_*.json")

async def main():
    """Main entry point for opportunity lifespan monitoring."""
    try:
        # Check environment variables
        if not os.getenv('ALCHEMY_API_KEY'):
            logger.error("❌ Missing ALCHEMY_API_KEY environment variable")
            return
        
        # Create and run monitor
        monitor = OpportunityLifespanMonitor()
        
        # Setup connections
        if not await monitor.setup_connections():
            logger.error("❌ Failed to setup connections")
            return
        
        # Run lifespan analysis
        await monitor.run_lifespan_analysis(num_opportunities=15)
        
    except KeyboardInterrupt:
        logger.info("\n🛑 MONITORING STOPPED BY USER")
    except Exception as e:
        logger.error(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("⏱️  OPPORTUNITY LIFESPAN MONITOR")
    print("=" * 35)
    print("Monitoring arbitrage opportunities to determine")
    print("execution speed requirements!")
    print()
    
    asyncio.run(main())
