#!/usr/bin/env python3
"""
Deploy Arbitrage Bot
Complete deployment script for the MayArbi arbitrage system.
"""

import asyncio
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import argparse
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.master_arbitrage_system import MasterArbitrageSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'arbitrage_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)


async def deploy_arbitrage_bot(execution_mode: str = 'simulation', wallet_private_key: str = None):
    """Deploy the complete arbitrage bot."""

    # Auto-load private key from .env if not provided
    if not wallet_private_key and execution_mode == 'live':
        wallet_private_key = os.getenv('PRIVATE_KEY')
        if wallet_private_key:
            print("✅ Private key loaded from .env file")
        else:
            print("❌ No private key found in .env file!")
            print("   Please add: PRIVATE_KEY=your_actual_private_key to .env")
            return False

    print("🚀 MayArbi - Complete Arbitrage System Deployment")
    print("=" * 70)
    print("💰 Automated Cross-Chain Flash Loan Arbitrage")
    print("📡 Real-time price feeds + Multi-bridge optimization")
    print("⚡ Zero capital required - Flash loans only!")
    print("🎯 Target: 0.15%+ profit opportunities")
    print("🌉 Multi-bridge: Across, Stargate, Synapse + more")
    print("=" * 70)

    # Load configuration
    try:
        config_path = Path('config/capital_efficient_config.json')
        if not config_path.exists():
            print("❌ Configuration file not found!")
            print("   Creating default configuration...")

            # Create default config
            default_config = {
                "execution": {
                    "min_profit_usd": 0.50,
                    "max_trade_size_usd": 5000,
                    "min_profit_percentage": 0.15,
                    "max_slippage_percentage": 0.5,
                    "execution_timeout_seconds": 300
                },
                "monitoring": {
                    "scan_interval_seconds": 30,
                    "update_interval_minutes": 5,
                    "alert_threshold_change": 10
                },
                "bridges": {
                    "preferred_bridges": ["across", "stargate", "synapse"],
                    "enable_failover": True,
                    "max_bridge_fee_percentage": 0.5
                },
                "execution_mode": execution_mode
            }

            # Create config directory
            config_path.parent.mkdir(exist_ok=True)

            # Save default config
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)

            print("✅ Default configuration created")

        # Load config
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Override execution mode
        config['execution_mode'] = execution_mode

        print(f"✅ Configuration loaded")

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

    # Display deployment configuration
    print(f"\n⚙️  Deployment Configuration:")
    print(f"   Execution Mode: {execution_mode.upper()}")
    print(f"   Min Profit: ${config.get('execution', {}).get('min_profit_usd', 0.50)}")
    print(f"   Max Trade Size: ${config.get('execution', {}).get('max_trade_size_usd', 5000):,}")
    print(f"   Scan Interval: {config.get('monitoring', {}).get('scan_interval_seconds', 30)}s")
    print(f"   Preferred Bridges: {', '.join(config.get('bridges', {}).get('preferred_bridges', ['across', 'synapse']))}")

    if execution_mode == 'live':
        if not wallet_private_key:
            print(f"   ⚠️  LIVE MODE: Wallet private key required")
            return False
        else:
            print(f"   🔐 LIVE MODE: Wallet configured")
    else:
        print(f"   🎬 SIMULATION MODE: Safe testing")

    # Safety confirmation for live mode
    if execution_mode == 'live':
        print(f"\n🚨 LIVE MODE WARNING:")
        print(f"   This will execute REAL trades with REAL money!")
        print(f"   Make sure you understand the risks!")
        print(f"   Start with small amounts for testing!")

        confirm = input(f"\n   Type 'YES' to confirm live trading: ")
        if confirm != 'YES':
            print(f"   Deployment cancelled by user")
            return False

    # Initialize and start system
    try:
        print(f"\n🔌 Initializing Master Arbitrage System...")

        # Create master system
        master_system = MasterArbitrageSystem(config)

        # Initialize all components
        print("   Initializing components...")
        if not await master_system.initialize():
            print("❌ System initialization failed")
            return False

        print("✅ System initialization complete!")

        # Display pre-launch summary
        print(f"\n🎯 Pre-Launch Summary:")
        print(f"   📡 Price feeds: Connected")
        print(f"   🌉 Bridge monitor: Active")
        print(f"   ⚡ Executor: Ready")
        print(f"   💰 Mode: {execution_mode.upper()}")

        # Launch system
        print(f"\n🚀 Launching Arbitrage System...")
        print(f"   Press Ctrl+C to stop gracefully")
        print(f"   Logs saved to: arbitrage_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        print(f"\n" + "=" * 70)

        # Start the system
        await master_system.start(wallet_private_key)

        return True

    except KeyboardInterrupt:
        print(f"\n🛑 System stopped by user")
        print("   Shutting down gracefully...")
        return True
    except Exception as e:
        print(f"\n💥 System error: {e}")
        logger.exception("System error")
        return False
    finally:
        # Cleanup
        try:
            print("🧹 Cleaning up system resources...")
            await master_system.cleanup()
            print("✅ Cleanup complete")
        except Exception as cleanup_error:
            print(f"⚠️  Cleanup warning: {cleanup_error}")

        # Force exit to ensure clean shutdown
        print("👋 Goodbye!")


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description='Deploy MayArbi Arbitrage Bot')
    parser.add_argument(
        '--mode',
        choices=['simulation', 'live'],
        default='simulation',
        help='Execution mode (default: simulation)'
    )
    parser.add_argument(
        '--wallet-key',
        type=str,
        help='Wallet private key (required for live mode)'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Custom configuration file path'
    )

    args = parser.parse_args()

    # Validate arguments - check .env file for private key if not provided
    if args.mode == 'live' and not args.wallet_key:
        env_private_key = os.getenv('PRIVATE_KEY')
        if not env_private_key:
            print("❌ Live mode requires --wallet-key argument OR PRIVATE_KEY in .env file")
            print("   Add your private key to .env file or use: --wallet-key YOUR_PRIVATE_KEY")
            sys.exit(1)

    # Run deployment
    try:
        success = asyncio.run(deploy_arbitrage_bot(args.mode, args.wallet_key))
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
