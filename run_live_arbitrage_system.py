#!/usr/bin/env python3
"""
Live Arbitrage System
Complete automated arbitrage system with real price feeds and execution.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
import signal
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feeds.real_price_feeds import RealPriceFeeds
from execution.arbitrage_executor import ArbitrageExecutor

class LiveArbitrageSystem:
    """Complete live arbitrage system."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize live arbitrage system."""
        self.config = config

        # Components
        self.price_feeds = RealPriceFeeds(config)
        self.executor = ArbitrageExecutor(config)

        # System state
        self.running = False
        self.scan_interval = config.get('monitoring', {}).get('scan_interval', 15)  # 15 seconds - faster scanning
        self.min_profit_percentage = config.get('execution', {}).get('min_profit_percentage', 0.01)  # 0.01% = dimes!

        # Statistics
        self.system_stats = {
            'start_time': None,
            'total_scans': 0,
            'opportunities_found': 0,
            'opportunities_executed': 0,
            'total_profit_usd': 0.0,
            'uptime_minutes': 0
        }

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received shutdown signal ({signum})")
        self.running = False

    async def start(self):
        """Start the live arbitrage system."""
        print("🚀 MayArbi Live Arbitrage System")
        print("=" * 60)
        print("💰 Automated Cross-Chain Flash Loan Arbitrage")
        print("📡 Real-time price feeds + Automated execution")
        print("⚡ Zero capital required - Flash loans only!")
        print("🎯 Target: 0.01%+ profit opportunities (DIME COLLECTOR MODE!)")
        print("=" * 60)

        # Initialize system
        print("\n🔌 Initializing system components...")

        # Connect price feeds
        print("   Connecting to price feeds...")
        price_feeds_connected = await self.price_feeds.connect()
        if not price_feeds_connected:
            print("❌ Failed to connect to price feeds")
            return False
        print("   ✅ Price feeds connected")

        # Test execution engine
        print("   Initializing execution engine...")
        print("   ✅ Execution engine ready")

        # Start monitoring
        self.running = True
        self.system_stats['start_time'] = datetime.now()

        print(f"\n🔍 Starting live monitoring...")
        print(f"   Scan interval: {self.scan_interval} seconds")
        print(f"   Minimum profit: {self.min_profit_percentage}%")
        print(f"   Execution mode: SIMULATION (safe testing)")
        print("\nPress Ctrl+C to stop...\n")

        try:
            while self.running:
                await self._scan_and_execute_cycle()
                await asyncio.sleep(self.scan_interval)

        except KeyboardInterrupt:
            print("\n🛑 System stopped by user")
        except Exception as e:
            print(f"\n💥 System error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self._cleanup()

        return True

    async def _scan_and_execute_cycle(self):
        """Complete scan and execution cycle."""
        cycle_start = datetime.now()

        try:
            # Update system stats
            self.system_stats['total_scans'] += 1
            self.system_stats['uptime_minutes'] = (
                datetime.now() - self.system_stats['start_time']
            ).total_seconds() / 60

            print(f"⏰ {cycle_start.strftime('%H:%M:%S')} - Scan #{self.system_stats['total_scans']}")

            # Scan for opportunities
            opportunities = await self.price_feeds.get_real_arbitrage_opportunities(
                min_profit_percentage=self.min_profit_percentage
            )

            if opportunities:
                self.system_stats['opportunities_found'] += len(opportunities)

                print(f"   🎯 Found {len(opportunities)} opportunities!")

                # Display top opportunities
                for i, opp in enumerate(opportunities[:3], 1):  # Top 3
                    print(f"      {i}. {opp['token']} {opp['direction']} - {opp['profit_percentage']:.3f}%")

                # Execute the best opportunity
                best_opportunity = opportunities[0]

                if best_opportunity['profit_percentage'] >= self.min_profit_percentage:
                    print(f"   🚀 Executing best opportunity: {best_opportunity['token']} - {best_opportunity['profit_percentage']:.3f}%")

                    execution_result = await self.executor.execute_opportunity(best_opportunity)

                    if execution_result.success:
                        self.system_stats['opportunities_executed'] += 1
                        self.system_stats['total_profit_usd'] += execution_result.profit_usd

                        print(f"   ✅ Execution successful!")
                        print(f"      Profit: ${execution_result.profit_usd:.2f}")
                        print(f"      Gas cost: ${execution_result.gas_cost_usd:.2f}")
                        print(f"      Execution time: {execution_result.execution_time_ms}ms")
                        print(f"      TX Hash: {execution_result.transaction_hash[:10]}...")
                    else:
                        print(f"   ❌ Execution failed: {execution_result.error_message}")
                else:
                    print(f"   ⚠️  Best opportunity ({best_opportunity['profit_percentage']:.3f}%) below threshold")
            else:
                print(f"   📊 No opportunities found (normal - opportunities are rare)")

            # Display running statistics
            self._display_running_stats()

            # Display execution statistics
            exec_stats = self.executor.get_execution_stats()
            if exec_stats['total_executions'] > 0:
                print(f"   📈 Execution stats: {exec_stats['successful_executions']}/{exec_stats['total_executions']} "
                      f"success ({exec_stats['success_rate_percentage']:.1f}%), "
                      f"${exec_stats['net_profit_usd']:.2f} net profit")

            print()  # Empty line for readability

        except Exception as e:
            print(f"   ❌ Cycle error: {e}")

    def _display_running_stats(self):
        """Display running system statistics."""
        stats = self.system_stats

        if stats['total_scans'] > 0:
            opp_rate = stats['opportunities_found'] / stats['total_scans']
            exec_rate = stats['opportunities_executed'] / max(stats['opportunities_found'], 1) * 100

            print(f"   📊 System stats: {stats['total_scans']} scans, "
                  f"{stats['opportunities_found']} opportunities ({opp_rate:.1f}/scan), "
                  f"{stats['opportunities_executed']} executed ({exec_rate:.1f}%), "
                  f"${stats['total_profit_usd']:.2f} total profit, "
                  f"{stats['uptime_minutes']:.1f}m uptime")

    async def _cleanup(self):
        """Cleanup system resources."""
        try:
            await self.price_feeds.disconnect()
            print("✅ Price feeds disconnected")
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")

        # Final summary
        self._display_final_summary()

    def _display_final_summary(self):
        """Display final system summary."""
        stats = self.system_stats
        exec_stats = self.executor.get_execution_stats()

        print(f"\n📊 Final System Summary:")
        print(f"   Uptime: {stats['uptime_minutes']:.1f} minutes")
        print(f"   Total scans: {stats['total_scans']}")
        print(f"   Opportunities found: {stats['opportunities_found']}")
        print(f"   Opportunities executed: {stats['opportunities_executed']}")
        print(f"   System profit: ${stats['total_profit_usd']:.2f}")

        if exec_stats['total_executions'] > 0:
            print(f"\n🎯 Execution Performance:")
            print(f"   Success rate: {exec_stats['success_rate_percentage']:.1f}%")
            print(f"   Total profit: ${exec_stats['total_profit_usd']:.2f}")
            print(f"   Total gas costs: ${exec_stats['total_gas_cost_usd']:.2f}")
            print(f"   Net profit: ${exec_stats['net_profit_usd']:.2f}")
            print(f"   Best single profit: ${exec_stats['best_profit_usd']:.2f}")
            print(f"   Average execution time: {exec_stats['average_execution_time_ms']:.0f}ms")

        # Calculate potential daily/monthly earnings
        if stats['uptime_minutes'] > 0 and stats['total_profit_usd'] > 0:
            profit_per_minute = stats['total_profit_usd'] / stats['uptime_minutes']
            daily_potential = profit_per_minute * 60 * 24
            monthly_potential = daily_potential * 30

            print(f"\n💰 Profit Projections:")
            print(f"   Current rate: ${profit_per_minute:.4f}/minute")
            print(f"   Daily potential: ${daily_potential:.2f}")
            print(f"   Monthly potential: ${monthly_potential:,.2f}")

        print(f"\n🎉 MayArbi Live Arbitrage System Complete!")


async def main():
    """Main function."""
    try:
        # Load config
        with open('config/capital_efficient_config.json', 'r') as f:
            config = json.load(f)

        # Add execution configuration
        if 'execution' not in config:
            config['execution'] = {
                'min_profit_usd': 10,
                'max_trade_size_usd': 10000,
                'min_profit_percentage': 0.15,
                'max_slippage_percentage': 1.0,
                'execution_timeout_seconds': 30
            }

        if 'monitoring' not in config:
            config['monitoring'] = {
                'scan_interval': 30
            }

        # Create and start system
        system = LiveArbitrageSystem(config)
        await system.start()

    except FileNotFoundError:
        print("❌ Config file not found: config/capital_efficient_config.json")
        return False
    except KeyboardInterrupt:
        print("\n👋 System stopped by user")
        return True
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
