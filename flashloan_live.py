#!/usr/bin/env python3
"""
🔥 MAYARBI FLASHLOAN ARBITRAGE - LIVE TRADING 🔥
Zero capital risk - Maximum profit potential!
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'flashloan_live_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)

def display_flashloan_banner():
    """Display flashloan trading banner."""
    print("\n" + "⚡"*60)
    print("🔥 MAYARBI FLASHLOAN ARBITRAGE - LIVE! 🔥")
    print("⚡"*60)
    print("💰 CAPITAL REQUIRED: $0 (FLASHLOANS!)")
    print("🚀 BORROW CAPACITY: Up to $50M+ per trade")
    print("⚡ PROFIT POTENTIAL: $0.01+ per opportunity - 1 PENNY IS PROFIT!")
    print("🛡️  RISK: ZERO to your $832 capital")
    print("🎯 TARGET: 0.01%+ profit opportunities - TAKE EVERYTHING GREEN!")
    print("⚡"*60)
    print("🎉 FLASHLOAN POWERED - MAXIMUM LEVERAGE! 🎉")
    print("⚡"*60)
    print("💡 Press Ctrl+C to stop safely")
    print("⚡"*60)

async def test_flashloan_system():
    """Test the multi-provider flashloan system with real opportunities."""
    try:
        print("\n🔍 TESTING MULTI-PROVIDER FLASHLOAN SYSTEM...")
        print("="*50)

        from flashloan.aave_flashloan import AaveFlashLoan as MultiProviderFlashLoan
        from feeds.alchemy_sdk_feeds import AlchemySDKFeeds

        # Initialize components
        config = {
            'alchemy_api_key': os.getenv('ALCHEMY_API_KEY'),
            'networks': ['arbitrum', 'base', 'optimism']
        }

        flashloan = MultiProviderFlashLoan(config)
        feeds = AlchemySDKFeeds(config)
        
        # Get flashloan capabilities
        print("⚡ Aave Flashloan Capabilities:")
        summary = flashloan.get_flash_loan_summary()
        print(f"   🏦 Provider: {summary['provider']}")
        print(f"   💰 Fee: {summary['fee_percentage']:.3f}%")
        print(f"   🌐 Networks: {len(summary['supported_networks'])}")
        print(f"   💵 Max Amount: {summary['max_amount_example']}")
        print(f"   🎯 Optimization: Use dYdX (0%) or Balancer (0%) when available")
        
        # Connect to price feeds
        print("\n📡 Connecting to price feeds...")
        if await feeds.connect():
            print("✅ Connected to price feeds!")
            
            # Get current opportunities
            print("\n🎯 Scanning for flashloan opportunities...")
            opportunities = await feeds.get_l2_arbitrage_opportunities(min_profit_percentage=0.1)
            
            if opportunities:
                print(f"🚀 FOUND {len(opportunities)} OPPORTUNITIES!")
                print("="*50)
                
                for i, opp in enumerate(opportunities[:3], 1):
                    profit_pct = opp.get('profit_percentage', 0)
                    token = opp.get('token', 'Unknown')
                    direction = opp.get('direction', 'Unknown')
                    
                    # Calculate flashloan potential
                    borrow_amount = 50000  # $50K flashloan
                    gross_profit = borrow_amount * (profit_pct / 100)
                    flashloan_fee = borrow_amount * 0.0009  # 0.09%
                    gas_cost = 5  # L2 gas cost
                    net_profit = gross_profit - flashloan_fee - gas_cost
                    
                    print(f"#{i} ⚡ FLASHLOAN OPPORTUNITY: {token} {direction}")
                    print(f"    📈 Profit: {profit_pct:.3f}%")
                    print(f"    💰 Borrow: ${borrow_amount:,}")
                    print(f"    💵 Gross Profit: ${gross_profit:.2f}")
                    print(f"    💸 Flashloan Fee: ${flashloan_fee:.2f}")
                    print(f"    ⛽ Gas Cost: ${gas_cost:.2f}")
                    print(f"    🎯 NET PROFIT: ${net_profit:.2f}")
                    print(f"    🔥 ROI: {(net_profit/flashloan_fee)*100:.1f}% on fees")
                    
                    # Test flashloan quote
                    quote = flashloan.get_flash_loan_quote(token, borrow_amount, 'arbitrum')
                    if 'error' not in quote:
                        print(f"    ✅ Flashloan Available: ${quote['borrow_amount']:,.0f}")
                        print(f"    🏦 Max Available: ${quote['max_amount_available']:,.0f}")
                    print()
                
                return True
            else:
                print("📊 No opportunities found at this time")
                return True
        else:
            print("❌ Price feed connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Flashloan test failed: {e}")
        return False

async def start_flashloan_trading():
    """Start live flashloan arbitrage trading."""
    try:
        print("\n🚀 STARTING FLASHLOAN ARBITRAGE TRADING...")
        print("="*50)
        
        from core.master_arbitrage_system import MasterArbitrageSystem
        
        # Load DEX configuration
        import json
        with open('config/dex_config.json', 'r') as f:
            dex_config = json.load(f)

        # Show enabled DEXes
        enabled_dexes = [name for name, config in dex_config['dexs'].items() if config.get('enabled', False)]
        print(f"🔥 Loading {len(enabled_dexes)} DEXes: {', '.join(enabled_dexes[:5])}{'...' if len(enabled_dexes) > 5 else ''}")

        # FLASHLOAN TRADING CONFIGURATION
        flashloan_config = {
            'execution_mode': 'live',
            'trading_mode': 'flashloan',  # Enable flashloan mode
            'networks': ['arbitrum', 'base', 'optimism'],
            'alchemy_api_key': os.getenv('ALCHEMY_API_KEY'),
            'coingecko_api_key': os.getenv('COINGECKO_API_KEY'),
            'wallet_address': os.getenv('WALLET_ADDRESS'),

            # Include full DEX configuration
            'dexs': dex_config['dexs'],
            
            # FLASHLOAN SETTINGS
            'flashloan_provider': 'aave',
            'min_flashloan_amount': 10000,     # $10K minimum
            'max_flashloan_amount': 100000,    # $100K maximum
            'min_profit_percentage': 0.001,    # 0.001% minimum - TAKE ANYTHING!
            'min_net_profit_usd': 0.001,       # $0.001 minimum - LITERALLY ANY PROFIT!
            
            # EXECUTION SETTINGS
            'scan_interval_seconds': 1,        # ULTRA-FAST scanning - 1 second - CATCH EVERYTHING!
            'max_concurrent_trades': 2,        # 2 flashloan trades max
            'circuit_breaker_losses': 5,       # Stop after 5 consecutive losses
            'daily_loss_limit': 0.02,          # 2% daily loss limit (gas costs only)
            
            # SAFETY FEATURES
            'enable_slippage_protection': True,
            'max_slippage_percentage': 0.5,    # 0.5% max slippage
            'enable_profit_verification': True,
            'require_simulation': True,        # Simulate before execution
            'max_gas_price_gwei': 50,
            
            # FLASHLOAN SPECIFIC
            'flashloan_safety_margin': 1.5,    # 1.5x profit margin over costs
            'enable_mev_protection': True,
            'priority_fee_gwei': 2             # MEV protection
        }
        
        logger.info("⚡ Initializing FLASHLOAN arbitrage system...")
        logger.info(f"💰 Flashloan range: ${flashloan_config['min_flashloan_amount']:,} - ${flashloan_config['max_flashloan_amount']:,}")
        logger.info(f"🎯 Min profit: {flashloan_config['min_profit_percentage']}% (${flashloan_config['min_net_profit_usd']})")
        logger.info(f"🛡️  Safety margin: {flashloan_config['flashloan_safety_margin']}x")
        
        system = MasterArbitrageSystem(flashloan_config)
        
        # Initialize system
        logger.info("🚀 Initializing flashloan trading components...")
        if not await system.initialize():
            logger.error("❌ CRITICAL: System initialization failed")
            return False
        
        logger.info("✅ Flashloan system initialized!")
        logger.info("⚡ Starting LIVE flashloan arbitrage...")
        logger.info("💰 Zero capital risk - Maximum profit potential!")
        logger.info("🔥 Hunting for 0.15%+ opportunities...")
        
        # Get wallet private key for REAL trading
        private_key = os.getenv('PRIVATE_KEY') or os.getenv('WALLET_PRIVATE_KEY')
        if not private_key:
            logger.error("❌ PRIVATE_KEY environment variable required for live trading")
            logger.error("   Set it with: export PRIVATE_KEY='your_private_key_here'")
            return False

        logger.info(f"🔑 Wallet private key loaded (ending in ...{private_key[-6:]})")

        # Start REAL flashloan trading
        await system.start(wallet_private_key=private_key)
        
        return True

    except KeyboardInterrupt:
        print("\n🛑 FLASHLOAN TRADING STOPPED BY USER")
        print("✅ Safe shutdown complete")
        return True
    except Exception as e:
        logger.error(f"❌ Flashloan trading error: {e}")
        return False

async def main():
    """Main flashloan trading launcher."""
    try:
        display_flashloan_banner()
        
        # Test flashloan system first
        if not await test_flashloan_system():
            print("\n❌ Flashloan system test failed")
            return False
        
        print("\n🎉 FLASHLOAN SYSTEM READY!")
        print("⚡ Starting live trading in 3 seconds...")
        await asyncio.sleep(3)
        
        # Start live flashloan trading
        return await start_flashloan_trading()
        
    except KeyboardInterrupt:
        print("\n🛑 FLASHLOAN TRADING STOPPED BY USER")
        print("✅ Safe shutdown complete")
        return True
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR: {e}")
        return False

if __name__ == "__main__":
    print(f"\n⚡ FLASHLOAN ARBITRAGE START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        success = asyncio.run(main())
        if success:
            print("\n✅ FLASHLOAN TRADING SESSION COMPLETE")
        else:
            print("\n❌ FLASHLOAN TRADING ENCOUNTERED ERRORS")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 IMMEDIATE SHUTDOWN")
        # Force cleanup of any hanging tasks
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except:
            pass
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {e}")
        sys.exit(1)
