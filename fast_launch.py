#!/usr/bin/env python3
"""
🚀 MAYARBI FAST LAUNCH - IMMEDIATE TRADING
No delays, no lengthy tests - straight to profit!
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Minimal logging for speed
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

async def quick_start():
    """Ultra-fast startup - skip tests, go straight to trading."""
    try:
        print("🚀 MAYARBI FAST LAUNCH")
        print("⚡ Skipping tests - Going straight to live trading!")
        print("💰 Your $832 + Flashloans = Maximum profit potential")
        print("="*50)
        
        # Quick environment check
        required = ['ALCHEMY_API_KEY', 'WALLET_ADDRESS', 'PRIVATE_KEY']
        if not all(os.getenv(var) for var in required):
            print("❌ Missing environment variables")
            return False
        
        print("✅ Environment ready")
        print("⚡ Initializing trading system...")
        
        # Import and start immediately
        from core.master_arbitrage_system import MasterArbitrageSystem
        
        # Fast configuration - no delays
        config = {
            'execution_mode': 'live',
            'networks': ['arbitrum', 'base', 'optimism'],
            'alchemy_api_key': os.getenv('ALCHEMY_API_KEY'),
            'wallet_address': os.getenv('WALLET_ADDRESS'),
            'max_trade_size_usd': 100,  # Reduced to avoid 80% wallet limit
            'min_profit_usd': 1.00,
            'scan_interval_seconds': 5,  # Very fast scanning
            'flashloan_enabled': True,
            'flashloan_provider': 'aave',
            'min_flashloan_profit': 10.00,
            'circuit_breaker_losses': 3,
            'daily_loss_limit': 0.05
        }
        
        system = MasterArbitrageSystem(config)
        
        print("🔥 Starting live arbitrage trading NOW!")
        print("💡 Press Ctrl+C to stop")
        
        # Initialize and start immediately
        if await system.initialize():
            private_key = os.getenv('PRIVATE_KEY')
            await system.start(wallet_private_key=private_key)
        else:
            print("❌ Initialization failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print(f"⚡ FAST LAUNCH: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        success = asyncio.run(quick_start())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Trading stopped")
    except Exception as e:
        print(f"💥 Error: {e}")
        sys.exit(1)
