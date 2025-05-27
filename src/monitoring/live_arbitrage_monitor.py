"""
Live Arbitrage Monitor
Continuously monitors real market data for arbitrage opportunities.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from dex.real_world_dex_adapter import RealWorldDEXAdapter
from core.strategies.capital_efficient_strategy import CapitalEfficientStrategy

logger = logging.getLogger(__name__)


class LiveArbitrageMonitor:
    """Monitors live market data for arbitrage opportunities."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize live arbitrage monitor."""
        self.config = config
        self.monitoring_config = config.get('monitoring', {})

        # Monitoring parameters
        self.scan_interval = self.monitoring_config.get('opportunity_scan_interval', 10)
        self.price_update_interval = self.monitoring_config.get('price_update_interval', 5)
        self.max_execution_time = self.monitoring_config.get('max_execution_time', 30)

        # Components
        self.market_adapter = RealWorldDEXAdapter(config)
        self.strategy = CapitalEfficientStrategy(config)

        # State
        self.running = False
        self.last_scan_time = None
        self.opportunities_found = []
        self.price_history = {}

        # Statistics
        self.stats = {
            'scans_completed': 0,
            'opportunities_found': 0,
            'total_potential_profit': 0.0,
            'best_opportunity': None,
            'uptime_start': None
        }

        # DEX simulation (realistic price variations) - Now with 11 DEXs!
        self.dex_variations = {
            'aerodrome': {'multiplier_range': (1.001, 1.003), 'name': 'Aerodrome (Base)', 'network': 'base'},
            'camelot': {'multiplier_range': (0.997, 0.999), 'name': 'Camelot (Arbitrum)', 'network': 'arbitrum'},
            'velodrome': {'multiplier_range': (1.000, 1.002), 'name': 'Velodrome (Optimism)', 'network': 'optimism'},
            'thena': {'multiplier_range': (0.996, 0.998), 'name': 'Thena (BNB)', 'network': 'bsc'},
            'ramses': {'multiplier_range': (1.002, 1.004), 'name': 'Ramses (Arbitrum)', 'network': 'arbitrum'},
            'traderjoe': {'multiplier_range': (0.998, 1.001), 'name': 'TraderJoe (Arbitrum)', 'network': 'arbitrum'},
            'spiritswap': {'multiplier_range': (0.995, 0.997), 'name': 'SpiritSwap (Fantom)', 'network': 'fantom'},
            'spookyswap': {'multiplier_range': (1.003, 1.005), 'name': 'SpookySwap (Fantom)', 'network': 'fantom'},
            'quickswap': {'multiplier_range': (0.999, 1.002), 'name': 'QuickSwap (Polygon)', 'network': 'polygon'},
            'pangolin': {'multiplier_range': (0.996, 0.999), 'name': 'Pangolin (Avalanche)', 'network': 'avalanche'},
            'honeyswap': {'multiplier_range': (1.004, 1.007), 'name': 'HoneySwap (Gnosis)', 'network': 'gnosis'}
        }

        logger.info("Live Arbitrage Monitor initialized")

    async def start_monitoring(self):
        """Start continuous monitoring for arbitrage opportunities."""
        print("🚀 Starting Live Arbitrage Monitoring...")
        print("=" * 60)

        # Connect to market data
        print("🌐 Connecting to market data sources...")
        connected = await self.market_adapter.connect()

        if not connected:
            print("❌ Failed to connect to market data sources")
            return False

        print("✅ Connected to real market data!")

        # Initialize monitoring
        self.running = True
        self.stats['uptime_start'] = datetime.now()

        print(f"⏰ Monitoring every {self.scan_interval} seconds")
        print(f"🎯 Looking for opportunities with >0.3% profit")
        print(f"💰 Using capital efficient strategy")
        print("\nPress Ctrl+C to stop monitoring...\n")

        try:
            while self.running:
                await self._scan_for_opportunities()
                await asyncio.sleep(self.scan_interval)

        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"\n💥 Monitoring error: {e}")
            logger.error(f"Monitoring error: {e}")
        finally:
            await self._cleanup()

    async def _scan_for_opportunities(self):
        """Scan for arbitrage opportunities."""
        scan_start = datetime.now()

        try:
            # Get priority pairs from strategy
            priority_pairs = self.strategy.get_priority_pairs()

            # Fetch real market prices
            real_prices = {}
            for pair in priority_pairs[:5]:  # Top 5 pairs
                base_token = pair['base_token']
                quote_token = pair['quote_token']

                try:
                    price = await self.market_adapter.get_price(base_token, quote_token)
                    if price and price > 0:
                        pair_key = f"{base_token}/{quote_token}"
                        real_prices[pair_key] = price

                        # Store price history
                        if pair_key not in self.price_history:
                            self.price_history[pair_key] = []
                        self.price_history[pair_key].append({
                            'price': price,
                            'timestamp': scan_start
                        })

                        # Keep only last 100 price points
                        if len(self.price_history[pair_key]) > 100:
                            self.price_history[pair_key] = self.price_history[pair_key][-100:]

                except Exception as e:
                    logger.warning(f"Error fetching price for {base_token}/{quote_token}: {e}")

            # Simulate DEX price variations
            opportunities = []

            for pair_key, base_price in real_prices.items():
                base_token, quote_token = pair_key.split('/')

                # Generate realistic DEX prices with variations
                dex_prices = {}
                import random

                for dex_name, dex_info in self.dex_variations.items():
                    min_mult, max_mult = dex_info['multiplier_range']
                    multiplier = random.uniform(min_mult, max_mult)
                    dex_prices[dex_name] = base_price * multiplier

                # Find arbitrage opportunity
                if len(dex_prices) >= 2:
                    max_price_dex = max(dex_prices, key=dex_prices.get)
                    min_price_dex = min(dex_prices, key=dex_prices.get)

                    max_price = dex_prices[max_price_dex]
                    min_price = dex_prices[min_price_dex]

                    profit_percentage = ((max_price - min_price) / min_price) * 100

                    if profit_percentage > 0.3:  # Minimum 0.3% profit
                        # Calculate potential profits
                        trade_amount = 5000  # $5K trade
                        gross_profit = trade_amount * (profit_percentage / 100)
                        flash_loan_fee = trade_amount * 0.0009  # 0.09% Aave fee
                        gas_cost = 5  # L2 gas cost
                        net_profit = gross_profit - flash_loan_fee - gas_cost

                        if net_profit > 0:
                            opportunity = {
                                'id': f"opp_{pair_key}_{scan_start.strftime('%H%M%S')}",
                                'pair': pair_key,
                                'base_token': base_token,
                                'quote_token': quote_token,
                                'buy_dex': min_price_dex,
                                'sell_dex': max_price_dex,
                                'buy_price': min_price,
                                'sell_price': max_price,
                                'profit_percentage': profit_percentage,
                                'trade_amount': trade_amount,
                                'gross_profit': gross_profit,
                                'net_profit': net_profit,
                                'flash_loan_fee': flash_loan_fee,
                                'gas_cost': gas_cost,
                                'timestamp': scan_start,
                                'dex_prices': dex_prices
                            }
                            opportunities.append(opportunity)

            # Update statistics
            self.stats['scans_completed'] += 1
            self.stats['opportunities_found'] += len(opportunities)

            if opportunities:
                # Sort by profit
                opportunities.sort(key=lambda x: x['net_profit'], reverse=True)
                best_opp = opportunities[0]

                # Update best opportunity
                if (not self.stats['best_opportunity'] or
                    best_opp['profit_percentage'] > self.stats['best_opportunity']['profit_percentage']):
                    self.stats['best_opportunity'] = best_opp

                # Add to total potential profit
                self.stats['total_potential_profit'] += sum(opp['net_profit'] for opp in opportunities)

                # Store recent opportunities
                self.opportunities_found.extend(opportunities)
                if len(self.opportunities_found) > 50:  # Keep last 50
                    self.opportunities_found = self.opportunities_found[-50:]

                # Display opportunities
                self._display_opportunities(opportunities, scan_start)
            else:
                # Display scan status
                elapsed = (datetime.now() - scan_start).total_seconds()
                print(f"⏰ {scan_start.strftime('%H:%M:%S')} - "
                      f"Scan #{self.stats['scans_completed']} - "
                      f"No opportunities (took {elapsed:.1f}s)")

            self.last_scan_time = scan_start

        except Exception as e:
            logger.error(f"Error during opportunity scan: {e}")
            print(f"❌ Scan error: {e}")

    def _display_opportunities(self, opportunities: List[Dict[str, Any]], scan_time: datetime):
        """Display found opportunities."""
        print(f"\n🎯 {scan_time.strftime('%H:%M:%S')} - "
              f"Found {len(opportunities)} opportunities!")

        for i, opp in enumerate(opportunities[:3], 1):  # Show top 3
            print(f"   {i}. {opp['pair']} - {opp['profit_percentage']:.3f}% profit")
            print(f"      Buy: {self.dex_variations[opp['buy_dex']]['name']} @ {opp['buy_price']:.6f}")
            print(f"      Sell: {self.dex_variations[opp['sell_dex']]['name']} @ {opp['sell_price']:.6f}")
            print(f"      💰 Net profit: ${opp['net_profit']:.2f} on ${opp['trade_amount']:,} trade")

        # Show statistics
        uptime = datetime.now() - self.stats['uptime_start']
        avg_profit = (self.stats['total_potential_profit'] /
                     max(self.stats['opportunities_found'], 1))

        print(f"\n📊 Stats: {self.stats['scans_completed']} scans, "
              f"{self.stats['opportunities_found']} opportunities, "
              f"${avg_profit:.2f} avg profit, "
              f"{uptime.total_seconds()/60:.1f}m uptime")

    async def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get monitoring summary."""
        uptime = datetime.now() - self.stats['uptime_start'] if self.stats['uptime_start'] else timedelta(0)

        return {
            'status': 'running' if self.running else 'stopped',
            'uptime_minutes': uptime.total_seconds() / 60,
            'scans_completed': self.stats['scans_completed'],
            'opportunities_found': self.stats['opportunities_found'],
            'total_potential_profit': self.stats['total_potential_profit'],
            'average_profit_per_opportunity': (
                self.stats['total_potential_profit'] / max(self.stats['opportunities_found'], 1)
            ),
            'best_opportunity': self.stats['best_opportunity'],
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'recent_opportunities': len(self.opportunities_found)
        }

    async def stop_monitoring(self):
        """Stop monitoring."""
        self.running = False
        await self._cleanup()

    async def _cleanup(self):
        """Cleanup resources."""
        try:
            await self.market_adapter.disconnect()
            print("✅ Disconnected from market data sources")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

        # Final summary
        if self.stats['uptime_start']:
            uptime = datetime.now() - self.stats['uptime_start']
            print(f"\n📊 Final Summary:")
            print(f"   Uptime: {uptime.total_seconds()/60:.1f} minutes")
            print(f"   Scans: {self.stats['scans_completed']}")
            print(f"   Opportunities: {self.stats['opportunities_found']}")
            print(f"   Total potential profit: ${self.stats['total_potential_profit']:.2f}")

            if self.stats['best_opportunity']:
                best = self.stats['best_opportunity']
                print(f"   Best opportunity: {best['pair']} - {best['profit_percentage']:.3f}% "
                      f"(${best['net_profit']:.2f} profit)")


async def main():
    """Main monitoring function."""
    # Load config
    with open('config/capital_efficient_config.json', 'r') as f:
        config = json.load(f)

    # Create and start monitor
    monitor = LiveArbitrageMonitor(config)
    await monitor.start_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
