#!/usr/bin/env python3
"""
🚀 WALLET-FUNDED ARBITRAGE - IMMEDIATE PROFITS
Uses your $832 capital for real arbitrage trades
NO FLASHLOANS - Just pure wallet-funded arbitrage
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
from config.trading_config import CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

async def main():
    """Launch wallet-funded arbitrage system."""
    
    print("⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡")
    print("🔥 MAYARBI WALLET-FUNDED ARBITRAGE - LIVE! 🔥")
    print("⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡")
    print("💰 CAPITAL: Your $832 wallet balance")
    print("🎯 STRATEGY: Direct DEX arbitrage")
    print("⚡ PROFIT TARGET: $0.01+ per trade")
    print("🛡️  RISK: Limited to your wallet balance")
    print("🚀 EXECUTION: REAL blockchain transactions")
    print("⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡")
    print("🎉 NO FLASHLOANS - PURE WALLET ARBITRAGE! 🎉")
    print("⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡")
    print("💡 Press Ctrl+C to stop safely")
    print("⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡")
    print()
    
    try:
        # Check environment
        required_vars = ['ALCHEMY_API_KEY', 'WALLET_ADDRESS', 'PRIVATE_KEY']
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            logger.error(f"❌ Missing environment variables: {missing}")
            return False
        
        logger.info("✅ Environment variables loaded")
        
        # Import the master system
        from core.master_arbitrage_system import MasterArbitrageSystem
        
        # Configuration for wallet-funded arbitrage - 🎯 USING CENTRALIZED CONFIG!
        config = {
            'execution_mode': 'live',
            'trading_mode': 'wallet',  # 🔥 CHANGE TO 'flashloan' FOR UNLIMITED CAPITAL!
            'trading_enabled': True,  # ENABLE REAL TRADING
            'networks': CONFIG.PREFERRED_NETWORKS,  # 🎯 CENTRALIZED CONFIG
            'alchemy_api_key': os.getenv('ALCHEMY_API_KEY'),
            'wallet_address': os.getenv('WALLET_ADDRESS'),

            # Wallet-funded settings - 🎯 CENTRALIZED CONFIG
            'flashloan_enabled': CONFIG.ENABLE_FLASHLOANS,  # 🎯 CENTRALIZED CONFIG
            'wallet_funded': True,       # ENABLE WALLET FUNDING
            'max_trade_percentage': CONFIG.MAX_TRADE_PERCENTAGE * 100,  # 🎯 CENTRALIZED CONFIG (convert to %)
            'min_profit_usd': CONFIG.MIN_PROFIT_USD,      # 🎯 CENTRALIZED CONFIG ($1 filter!)
            'min_profit_percentage': CONFIG.MIN_PROFIT_PERCENTAGE,  # 🎯 CENTRALIZED CONFIG

            # Trading parameters - 🎯 CENTRALIZED CONFIG
            'scan_interval_seconds': CONFIG.SCAN_INTERVAL_SECONDS,  # 🎯 CENTRALIZED CONFIG
            'max_slippage': CONFIG.MAX_SLIPPAGE_PERCENTAGE / 100.0,  # 🎯 CENTRALIZED CONFIG (convert to decimal)
            'gas_price_multiplier': CONFIG.GAS_PRICE_MULTIPLIER,  # 🎯 CENTRALIZED CONFIG

            # Safety settings - 🎯 CENTRALIZED CONFIG
            'circuit_breaker_losses': CONFIG.MAX_CONSECUTIVE_LOSSES,  # 🎯 CENTRALIZED CONFIG
            'daily_loss_limit_percentage': CONFIG.MAX_DAILY_LOSS_PERCENTAGE,  # 🎯 CENTRALIZED CONFIG
            'max_concurrent_trades': CONFIG.MAX_CONCURRENT_TRADES,  # 🎯 CENTRALIZED CONFIG

            # DEX settings - 🎯 PHASE 1 EXPANSION: 21x MORE OPPORTUNITIES!
            'allowed_dexes': ['sushiswap', 'camelot', 'uniswap_v3', 'traderjoe', 'aerodrome', 'baseswap', 'velodrome'],  # Phase 1: High-priority DEXes
            'safe_tokens': CONFIG.TARGET_TOKENS  # 🎯 CENTRALIZED CONFIG (your held tokens)
        }
        
        logger.info("🚀 Initializing wallet-funded arbitrage system...")
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
        logger.info("🚀 Starting LIVE wallet-funded arbitrage...")
        logger.info("💰 Using your $832 capital for real trades!")
        
        # Start the system
        await system.start(wallet_private_key=private_key)
        
        return True
        
    except KeyboardInterrupt:
        logger.info("🛑 Arbitrage stopped by user")
        return True
    except Exception as e:
        logger.error(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"⚡ WALLET ARBITRAGE START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        success = asyncio.run(main())
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)
