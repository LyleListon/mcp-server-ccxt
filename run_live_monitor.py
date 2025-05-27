#!/usr/bin/env python3
"""
Run Live Arbitrage Monitor
Starts the live monitoring system for real arbitrage opportunities.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from monitoring.live_arbitrage_monitor import LiveArbitrageMonitor

async def main():
    """Run the live arbitrage monitor."""
    print("🚀 MayArbi Live Arbitrage Monitor")
    print("=" * 50)
    print("💰 Capital Efficient Flash Loan Arbitrage")
    print("🎯 Monitoring smaller DEXs for opportunities")
    print("⚡ Zero capital required - flash loans only!")
    print("=" * 50)
    
    try:
        # Load config
        with open('config/capital_efficient_config.json', 'r') as f:
            config = json.load(f)
        
        # Create and start monitor
        monitor = LiveArbitrageMonitor(config)
        await monitor.start_monitoring()
        
    except FileNotFoundError:
        print("❌ Config file not found: config/capital_efficient_config.json")
        return False
    except KeyboardInterrupt:
        print("\n👋 Monitor stopped by user")
        return True
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
