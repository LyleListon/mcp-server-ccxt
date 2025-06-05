#!/usr/bin/env python3
"""
🔥 FLASHLOAN ARBITRAGE - UNLIMITED CAPITAL
Uses flashloans for unlimited capital arbitrage trades
ZERO CAPITAL RISK - Only gas costs required!
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# 🎯 CENTRALIZED CONFIGURATION - Single source of truth!
from src.config.trading_config import CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'flashloan_live_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

def show_flashloan_banner():
    """Display the flashloan arbitrage banner."""
    print("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
    print("🔥                    FLASHLOAN ARBITRAGE - UNLIMITED CAPITAL                    🔥")
    print("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
    print("💰 CAPITAL: UNLIMITED (via flashloans)")
    print("🎯 STRATEGY: Atomic arbitrage with zero capital risk")
    print("⚡ PROFIT TARGET: $0.25+ per trade (after fees)")
    print("🛡️  RISK: Only gas costs (no capital at risk)")
    print("🚀 EXECUTION: REAL blockchain transactions")
    print("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
    print("🎉 FLASHLOAN MODE: BALANCER (0% FEES) + AAVE (0.09% FEES) 🎉")
    print("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
    print("💡 Press Ctrl+C to stop safely")
    print("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
    print()

async def main():
    """Main flashloan arbitrage function."""
    
    try:
        # Check environment
        required_vars = ['ALCHEMY_API_KEY', 'WALLET_ADDRESS', 'PRIVATE_KEY']
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            logger.error(f"❌ Missing environment variables: {missing}")
            return False
        
        logger.info("✅ Environment variables loaded")
        
        # Import the master system
        from src.core.master_arbitrage_system import MasterArbitrageSystem
        
        # Configuration for flashloan arbitrage - 🎯 USING CENTRALIZED CONFIG!
        config = {
            'execution_mode': 'live',
            'trading_mode': 'flashloan',  # 🔥 FLASHLOAN MODE: UNLIMITED CAPITAL!
            'trading_enabled': True,  # ENABLE REAL TRADING
            'networks': CONFIG.PREFERRED_NETWORKS,  # 🎯 CENTRALIZED CONFIG
            'alchemy_api_key': os.getenv('ALCHEMY_API_KEY'),
            'wallet_address': os.getenv('WALLET_ADDRESS'),

            # Flashloan settings - 🎯 CENTRALIZED CONFIG
            'flashloan_enabled': True,  # 🔥 ENABLE FLASHLOANS!
            'flashloan_provider': 'balancer',  # Start with 0% fees
            'min_profit_usd': CONFIG.MIN_PROFIT_USD,      # 🎯 CENTRALIZED CONFIG ($0.25 filter!)
            'min_profit_percentage': CONFIG.MIN_PROFIT_PERCENTAGE,  # 🎯 CENTRALIZED CONFIG
            'max_trade_percentage': 100,  # 🔥 UNLIMITED CAPITAL!
            'min_flashloan_amount': 1000,   # $1K minimum flashloan
            'max_flashloan_amount': 100000, # $100K maximum flashloan

            # Risk management for flashloans
            'max_concurrent_executions': 1,  # One flashloan at a time
            'flashloan_safety_margin': 1.05,  # 5% safety margin
            'gas_price_multiplier': 1.2,  # Priority gas for flashloans

            # DEX settings - 🎯 CENTRALIZED CONFIG
            'allowed_dexes': ['sushiswap', 'camelot', 'uniswap_v3'],  # Flashloan-compatible DEXes
            'safe_tokens': CONFIG.TARGET_TOKENS  # 🎯 CENTRALIZED CONFIG (your held tokens)
        }
        
        logger.info("🔥 Initializing flashloan arbitrage system...")
        system = MasterArbitrageSystem(config)
        
        logger.info("🔧 Initializing system components...")
        if not await system.initialize():
            logger.error("❌ System initialization failed")
            return False
        
        logger.info("✅ System initialized successfully!")
        logger.info("🔑 Loading wallet private key...")
        
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            logger.error("❌ Private key not found")
            return False
        
        logger.info("✅ Private key loaded")
        logger.info("🔥 Starting LIVE flashloan arbitrage...")
        logger.info("💰 Using UNLIMITED CAPITAL via flashloans!")
        logger.info("🏊 Balancer flashloans: 0% fees")
        logger.info("🏦 Aave flashloans: 0.09% fees")
        
        # Start the system
        await system.start(wallet_private_key=private_key)
        
        return True
        
    except KeyboardInterrupt:
        logger.info("🛑 Flashloan arbitrage stopped by user")
        return True
    except Exception as e:
        logger.error(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"🔥 FLASHLOAN ARBITRAGE START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    show_flashloan_banner()
    
    try:
        success = asyncio.run(main())
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)
