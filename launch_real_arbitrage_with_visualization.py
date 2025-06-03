`#!/usr/bin/env python3
"""
🔥 LAUNCH REAL ARBITRAGE WITH FLOW VISUALIZATION 🔥

NO FAKE DATA - REAL TRADES ONLY!
"""

import asyncio
import logging
import subprocess
import time
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("real-arbitrage-launcher")

def launch_visualization():
    """Launch the flow visualization in a separate process."""
    try:
        logger.info("🎨 Launching flow visualization...")
        
        # Launch the visualization
        viz_process = subprocess.Popen([
            sys.executable, "simple_flow_demo.py"
        ], cwd=Path(__file__).parent)
        
        logger.info(f"🎨 Flow visualization launched (PID: {viz_process.pid})")
        return viz_process
        
    except Exception as e:
        logger.error(f"Failed to launch visualization: {e}")
        return None

async def launch_master_arbitrage_system():
    """Launch your Master Arbitrage System."""
    try:
        logger.info("🚀 Launching Master Arbitrage System...")
        
        # Import your master system
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from core.master_arbitrage_system import MasterArbitrageSystem
        
        # Load configuration
        config = {
            'execution_mode': 'live',  # REAL TRADES
            'scan_interval_seconds': 30,
            'min_profit_usd': 0.50,
            'max_trade_size_usd': 700,
            'min_profit_percentage': 0.1,
            'max_concurrent_executions': 3,
            'enable_cross_chain': False,
            'enable_same_chain': True,
            'preferred_bridges': ['across', 'stargate', 'synapse'],
            'max_execution_time_seconds': 300
        }
        
        # Create and initialize system
        system = MasterArbitrageSystem(config)
        
        if not await system.initialize():
            logger.error("❌ Failed to initialize Master Arbitrage System")
            return False
        
        # Get wallet private key (you'll need to provide this)
        wallet_private_key = input("🔑 Enter wallet private key (or press Enter for simulation): ").strip()
        
        if not wallet_private_key:
            logger.warning("⚠️  No private key provided - running in simulation mode")
            config['execution_mode'] = 'simulation'
        
        # Start the system
        logger.info("🔥 Starting REAL arbitrage system...")
        await system.start(wallet_private_key if wallet_private_key else None)
        
        return True
        
    except Exception as e:
        logger.error(f"Master Arbitrage System error: {e}")
        return False

async def main():
    """Main launcher function."""
    
    print("🔥" + "="*70 + "🔥")
    print("🔥  MAYARBI REAL ARBITRAGE SYSTEM WITH FLOW VISUALIZATION  🔥")
    print("🔥" + "="*70 + "🔥")
    print()
    print("🎯 REAL DATA ONLY - NO FAKE TRADES!")
    print("🚀 This will launch:")
    print("   1. 🎨 Flow Visualization (browser)")
    print("   2. 🔥 Master Arbitrage System (real trades)")
    print()
    
    # Confirm launch
    confirm = input("🚀 Ready to launch REAL arbitrage system? (y/N): ").strip().lower()
    if confirm != 'y':
        print("🛑 Launch cancelled")
        return
    
    print()
    print("🚀 LAUNCHING REAL ARBITRAGE SYSTEM...")
    print()
    
    # Step 1: Launch visualization
    viz_process = launch_visualization()
    if not viz_process:
        print("❌ Failed to launch visualization")
        return
    
    # Wait a moment for visualization to start
    await asyncio.sleep(3)
    
    try:
        # Step 2: Launch Master Arbitrage System
        success = await launch_master_arbitrage_system()
        
        if not success:
            print("❌ Failed to launch Master Arbitrage System")
            return
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested by user")
    except Exception as e:
        logger.error(f"System error: {e}")
    finally:
        # Cleanup
        logger.info("🧹 Cleaning up...")
        if viz_process and viz_process.poll() is None:
            viz_process.terminate()
            logger.info("🎨 Visualization process terminated")

def check_requirements():
    """Check if all requirements are met."""
    logger.info("🔍 Checking requirements...")
    
    # Check if Master Arbitrage System exists
    master_system_path = Path(__file__).parent / "src" / "core" / "master_arbitrage_system.py"
    if not master_system_path.exists():
        logger.error(f"❌ Master Arbitrage System not found: {master_system_path}")
        return False
    
    # Check if visualization exists
    viz_path = Path(__file__).parent / "simple_flow_demo.py"
    if not viz_path.exists():
        logger.error(f"❌ Flow visualization not found: {viz_path}")
        return False
    
    logger.info("✅ All requirements met")
    return True

if __name__ == "__main__":
    print("🔥 MAYARBI REAL ARBITRAGE LAUNCHER 🔥")
    print()
    
    # Check requirements
    if not check_requirements():
        print("❌ Requirements not met. Please check the error messages above.")
        sys.exit(1)
    
    print("✅ Requirements check passed")
    print()
    
    # Run the launcher
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Launcher stopped by user")
    except Exception as e:
        print(f"\n❌ Launcher error: {e}")
        logger.error(f"Launcher error: {e}")
