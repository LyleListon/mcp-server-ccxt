#!/usr/bin/env python3
"""
🕵️ Enhanced Spy Network Test
Test the competitor bot monitoring system with your discovered bots.
"""

import asyncio
import logging
import os
import json
from src.intelligence.competitor_bot_monitor import CompetitorBotMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_spy_network():
    """Test the spy network with discovered competitor bots."""
    
    print("🕵️ TESTING ENHANCED SPY NETWORK")
    print("=" * 50)
    
    # Initialize monitor
    config = {
        "monitoring_enabled": True,
        "profit_threshold": 0.01
    }
    
    try:
        monitor = CompetitorBotMonitor(config)
        
        print(f"✅ Spy network initialized")
        print(f"🤖 Monitoring {len(monitor.competitor_bots)} competitor bots")
        
        # List discovered bots
        print("\n📋 DISCOVERED COMPETITOR BOTS:")
        for i, (address, bot_info) in enumerate(monitor.competitor_bots.items(), 1):
            print(f"   {i:2d}. {address}")
            print(f"       Name: {bot_info.get('name', 'Unknown')}")
            print(f"       Functions: {', '.join(bot_info.get('functions', [])[:3])}")
            if i >= 10:  # Limit display
                print(f"       ... and {len(monitor.competitor_bots) - 10} more bots")
                break
        
        # Test ABI analysis
        print(f"\n🔍 ANALYZING COMPETITOR CAPABILITIES:")
        arbitrage_functions = set()
        profit_tracking = set()
        
        for address, bot_info in monitor.competitor_bots.items():
            abi = bot_info.get('abi', [])
            for item in abi:
                if item.get('type') == 'function':
                    func_name = item.get('name', '')
                    if 'arbitrage' in func_name.lower() or 'execute' in func_name.lower():
                        arbitrage_functions.add(func_name)
                    elif 'profit' in func_name.lower() or 'stats' in func_name.lower():
                        profit_tracking.add(func_name)
        
        print(f"   🎯 Arbitrage Functions Found: {len(arbitrage_functions)}")
        for func in list(arbitrage_functions)[:5]:
            print(f"      - {func}")
        
        print(f"   💰 Profit Tracking Functions: {len(profit_tracking)}")
        for func in list(profit_tracking)[:5]:
            print(f"      - {func}")
        
        # Test specific bot analysis
        print(f"\n🔬 DETAILED BOT ANALYSIS:")
        sample_bot = list(monitor.competitor_bots.items())[0]
        address, bot_info = sample_bot
        
        print(f"   Bot Address: {address}")
        print(f"   ABI Functions: {len(bot_info.get('abi', []))}")
        
        # Look for specific arbitrage indicators
        abi = bot_info.get('abi', [])
        indicators = {
            'flashloan': False,
            'profit_tracking': False,
            'emergency_controls': False,
            'multi_dex': False
        }
        
        abi_text = json.dumps(abi).lower()
        indicators['flashloan'] = 'flashloan' in abi_text or 'flashcallback' in abi_text
        indicators['profit_tracking'] = 'profit' in abi_text and 'total' in abi_text
        indicators['emergency_controls'] = 'emergency' in abi_text or 'withdraw' in abi_text
        indicators['multi_dex'] = 'router' in abi_text and ('uniswap' in abi_text or 'sushiswap' in abi_text)
        
        print(f"   🔍 Bot Capabilities:")
        for capability, has_it in indicators.items():
            status = "✅" if has_it else "❌"
            print(f"      {status} {capability.replace('_', ' ').title()}")
        
        # Test monitoring (short duration)
        print(f"\n🕵️ STARTING 30-SECOND MONITORING TEST...")
        
        # Create a monitoring task with timeout
        monitoring_task = asyncio.create_task(monitor.start_monitoring())
        
        try:
            await asyncio.wait_for(monitoring_task, timeout=30.0)
        except asyncio.TimeoutError:
            print("⏰ Monitoring test completed (30 seconds)")
            await monitor.stop_monitoring()
        
        # Show any activities found
        if monitor.recent_activities:
            print(f"\n🎯 ACTIVITIES DETECTED:")
            for activity in monitor.recent_activities[-5:]:  # Last 5
                print(f"   Bot: {activity.bot_address[:10]}...")
                print(f"   Function: {activity.function_called}")
                print(f"   Success: {'✅' if activity.success else '❌'}")
                if activity.profit_made:
                    print(f"   Profit: ${activity.profit_made:.4f}")
        else:
            print(f"\n📊 No bot activities detected in 30 seconds")
            print(f"   (This is normal - bots may not be active right now)")
        
        # Show intelligence gathered
        if monitor.bot_intelligence:
            print(f"\n🧠 INTELLIGENCE GATHERED:")
            for address, intel in list(monitor.bot_intelligence.items())[:3]:
                print(f"   Bot: {address[:10]}...")
                print(f"   Total Trades: {intel.total_trades}")
                print(f"   Success Rate: {intel.successful_trades}/{intel.total_trades}")
                print(f"   Total Profit: ${intel.total_profit:.4f}")
        
        print(f"\n🎉 SPY NETWORK TEST COMPLETED!")
        print(f"✅ System is operational and ready for exploitation!")
        
    except Exception as e:
        logger.error(f"Spy network test failed: {e}")
        print(f"❌ Test failed: {e}")

async def analyze_competitor_strategies():
    """Analyze the strategies used by competitor bots."""
    
    print(f"\n🔬 COMPETITOR STRATEGY ANALYSIS")
    print("=" * 50)
    
    try:
        # Load ABI files directly for analysis
        abi_dir = "abi_exports/arbitrum"
        if not os.path.exists(abi_dir):
            print(f"❌ ABI directory not found: {abi_dir}")
            return
        
        strategy_patterns = {
            'flashloan_arbitrage': 0,
            'multi_dex_arbitrage': 0,
            'pump_and_dump': 0,
            'sandwich_attacks': 0,
            'liquidation_bots': 0
        }
        
        function_frequency = {}
        
        for filename in os.listdir(abi_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(abi_dir, filename), 'r') as f:
                        abi = json.load(f)
                    
                    abi_text = json.dumps(abi).lower()
                    
                    # Analyze strategy patterns
                    if 'flashloan' in abi_text and 'arbitrage' in abi_text:
                        strategy_patterns['flashloan_arbitrage'] += 1
                    
                    if 'pump' in abi_text and 'arb' in abi_text:
                        strategy_patterns['pump_and_dump'] += 1
                    
                    if 'sandwich' in abi_text or 'frontrun' in abi_text:
                        strategy_patterns['sandwich_attacks'] += 1
                    
                    if 'liquidat' in abi_text:
                        strategy_patterns['liquidation_bots'] += 1
                    
                    if ('uniswap' in abi_text and 'sushiswap' in abi_text) or 'router' in abi_text:
                        strategy_patterns['multi_dex_arbitrage'] += 1
                    
                    # Count function frequencies
                    for item in abi:
                        if item.get('type') == 'function':
                            func_name = item.get('name', '')
                            if func_name:
                                function_frequency[func_name] = function_frequency.get(func_name, 0) + 1
                
                except Exception as e:
                    logger.error(f"Error analyzing {filename}: {e}")
        
        print(f"📊 STRATEGY PATTERNS DETECTED:")
        for strategy, count in strategy_patterns.items():
            if count > 0:
                print(f"   {strategy.replace('_', ' ').title()}: {count} bots")
        
        print(f"\n🔧 MOST COMMON FUNCTIONS:")
        sorted_functions = sorted(function_frequency.items(), key=lambda x: x[1], reverse=True)
        for func_name, count in sorted_functions[:10]:
            print(f"   {func_name}: {count} bots")
        
        # Identify the most sophisticated bots
        print(f"\n🏆 MOST SOPHISTICATED BOTS:")
        bot_complexity = {}
        
        for filename in os.listdir(abi_dir):
            if filename.endswith('.json'):
                try:
                    address = filename.split('_')[-1].replace('.json', '')
                    with open(os.path.join(abi_dir, filename), 'r') as f:
                        abi = json.load(f)
                    
                    # Calculate complexity score
                    complexity = 0
                    abi_text = json.dumps(abi).lower()
                    
                    # Points for different features
                    if 'flashloan' in abi_text: complexity += 3
                    if 'profit' in abi_text: complexity += 2
                    if 'emergency' in abi_text: complexity += 1
                    if 'stats' in abi_text: complexity += 1
                    if 'router' in abi_text: complexity += 1
                    
                    complexity += len([item for item in abi if item.get('type') == 'function']) // 10
                    
                    if complexity > 5:
                        bot_complexity[address] = complexity
                
                except Exception as e:
                    continue
        
        sorted_bots = sorted(bot_complexity.items(), key=lambda x: x[1], reverse=True)
        for i, (address, complexity) in enumerate(sorted_bots[:5], 1):
            print(f"   #{i} {address} (complexity: {complexity})")
        
    except Exception as e:
        logger.error(f"Strategy analysis failed: {e}")

if __name__ == "__main__":
    async def main():
        await test_spy_network()
        await analyze_competitor_strategies()
    
    asyncio.run(main())
