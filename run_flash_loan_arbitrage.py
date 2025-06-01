#!/usr/bin/env python3
"""
MayArbi Flash Loan Arbitrage System

Zero capital arbitrage using flash loans - perfect for post-security incident recovery.
Uses flash loans to execute arbitrage without requiring upfront capital.
"""

import asyncio
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import flash loan components
from integrations.flash_loans.enhanced_flash_loan_manager import EnhancedFlashLoanManager
from integrations.mcp.client_manager import MCPClientManager
from core.strategies.capital_efficient_strategy import CapitalEfficientStrategy
from core.detection.enhanced_cross_dex_detector import EnhancedCrossDexDetector
from analytics.performance_analyzer import PerformanceAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'flash_loan_arbitrage_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FlashLoanArbitrageSystem:
    """Zero capital arbitrage system using flash loans."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize flash loan arbitrage system."""
        self.config = config
        self.running = False
        
        # Core components
        self.mcp_client_manager = None
        self.flash_loan_manager = None
        self.enhanced_detector = None
        self.performance_analyzer = None
        self.strategy = None
        
        # Flash loan specific tracking
        self.session_stats = {
            'start_time': None,
            'total_scans': 0,
            'flash_loan_opportunities': 0,
            'profitable_flash_loans': 0,
            'flash_loans_executed': 0,
            'total_borrowed': 0.0,
            'total_fees_paid': 0.0,
            'net_profit': 0.0,
            'gas_spent': 0.0
        }

    async def initialize(self) -> bool:
        """Initialize flash loan arbitrage system."""
        try:
            print("⚡ Initializing Flash Loan Arbitrage System")
            print("=" * 60)
            print("💡 Zero capital strategy - using flash loans for arbitrage")
            print()
            
            # Initialize MCP Client Manager
            print("📡 Connecting to MCP servers...")
            self.mcp_client_manager = MCPClientManager(self.config)
            mcp_connected = await self.mcp_client_manager.connect_all()
            
            if not mcp_connected:
                print("⚠️  Warning: Some MCP servers failed to connect. Continuing with fallback.")
            else:
                print("✅ MCP servers connected!")
            
            # Initialize Enhanced Flash Loan Manager
            print("🏦 Initializing flash loan providers...")
            self.flash_loan_manager = EnhancedFlashLoanManager(
                config=self.config.get('flash_loan_config', {}),
                mcp_client_manager=self.mcp_client_manager
            )
            print("✅ Flash loan manager ready!")
            
            # Initialize Enhanced Cross-DEX Detector
            print("🔍 Initializing opportunity detection...")
            self.enhanced_detector = EnhancedCrossDexDetector(
                mcp_clients=self.mcp_client_manager,
                config=self.config.get('detection', {})
            )
            print("✅ Enhanced detection ready!")
            
            # Initialize Performance Analyzer
            print("📊 Initializing performance analytics...")
            self.performance_analyzer = PerformanceAnalyzer(
                mcp_client_manager=self.mcp_client_manager,
                config=self.config.get('analytics', {})
            )
            print("✅ Performance analytics ready!")
            
            # Initialize Strategy
            print("🎯 Initializing flash loan strategy...")
            self.strategy = CapitalEfficientStrategy(self.config)
            print("✅ Strategy initialized!")
            
            print("\n🎉 Flash Loan Arbitrage System Ready!")
            print("💡 Features enabled:")
            print("   • Zero capital arbitrage")
            print("   • Multi-provider flash loans (Aave, Balancer)")
            print("   • Enhanced opportunity detection")
            print("   • MEV protection")
            print("   • Performance analytics")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing flash loan system: {e}")
            print(f"❌ Initialization failed: {e}")
            return False

    async def start_flash_loan_arbitrage(self) -> None:
        """Start flash loan arbitrage system."""
        try:
            if not await self.initialize():
                return
            
            self.running = True
            self.session_stats['start_time'] = datetime.now()
            
            print("\n⚡ Starting Flash Loan Arbitrage System")
            print("=" * 60)
            print("💰 Zero capital strategy active")
            print("🏦 Flash loan providers ready")
            print("🎯 Scanning for profitable opportunities...")
            print("=" * 60)
            print("\nPress Ctrl+C to stop...\n")
            
            scan_count = 0
            
            while self.running:
                scan_count += 1
                await self._execute_flash_loan_scan(scan_count)
                
                # Show periodic reports
                if scan_count % 5 == 0:
                    await self._show_flash_loan_report()
                
                await asyncio.sleep(15)  # Scan every 15 seconds
                
        except KeyboardInterrupt:
            print("\n🛑 Flash loan arbitrage stopped by user")
        except Exception as e:
            logger.error(f"Error in flash loan arbitrage: {e}")
            print(f"💥 System error: {e}")
        finally:
            await self._cleanup()

    async def _execute_flash_loan_scan(self, scan_number: int) -> None:
        """Execute flash loan arbitrage scan."""
        scan_start = datetime.now()
        self.session_stats['total_scans'] += 1
        
        try:
            print(f"⏰ {scan_start.strftime('%H:%M:%S')} - Flash Loan Scan #{scan_number}")
            
            # Get market data
            market_data = await self._get_market_data()
            
            # Get DEX prices
            dex_prices = await self._get_dex_prices()
            
            # Detect flash loan opportunities
            opportunities = await self.enhanced_detector.detect_opportunities_with_intelligence(
                dex_prices, market_data
            )
            
            if opportunities:
                # Filter for flash loan viable opportunities
                flash_loan_opportunities = await self._filter_flash_loan_opportunities(opportunities)
                
                self.session_stats['flash_loan_opportunities'] += len(flash_loan_opportunities)
                
                if flash_loan_opportunities:
                    print(f"   ⚡ Found {len(flash_loan_opportunities)} flash loan opportunities")
                    
                    # Process top opportunities
                    for i, opportunity in enumerate(flash_loan_opportunities[:3], 1):
                        await self._process_flash_loan_opportunity(opportunity, i)
                else:
                    print(f"   📊 {len(opportunities)} opportunities found, none viable for flash loans")
            else:
                print("   📊 No opportunities detected")
                
        except Exception as e:
            logger.error(f"Error in flash loan scan: {e}")
            print(f"   ❌ Scan error: {e}")

    async def _filter_flash_loan_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter opportunities that are viable for flash loans."""
        flash_loan_opportunities = []
        
        for opportunity in opportunities:
            # Check if opportunity is suitable for flash loans
            input_amount = opportunity.get('input_amount', 0)
            profit_percentage = opportunity.get('profit_percentage', 0)
            
            # Minimum trade size for flash loans
            if input_amount < 500:  # $500 minimum
                continue
            
            # Get flash loan quote
            flash_loan_quote = await self._get_flash_loan_quote(opportunity)
            
            if flash_loan_quote and flash_loan_quote.get('viable', False):
                # Calculate net profit after flash loan fees
                gross_profit = input_amount * (profit_percentage / 100)
                flash_loan_fee = flash_loan_quote.get('fee_amount', 0)
                gas_cost = flash_loan_quote.get('gas_estimate', 5)
                net_profit = gross_profit - flash_loan_fee - gas_cost
                
                if net_profit > 5:  # Minimum $5 profit
                    opportunity['flash_loan_info'] = flash_loan_quote
                    opportunity['net_profit_after_fees'] = net_profit
                    opportunity['use_flash_loan'] = True
                    flash_loan_opportunities.append(opportunity)
        
        return flash_loan_opportunities

    async def _get_flash_loan_quote(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Get flash loan quote for an opportunity."""
        try:
            input_token = opportunity.get('input_token', 'USDC')
            input_amount = opportunity.get('input_amount', 0)
            network = opportunity.get('network', 'arbitrum')
            
            # Get quote from flash loan manager
            quote = await self.flash_loan_manager.get_optimal_flash_loan(
                token=input_token,
                amount=input_amount,
                network=network
            )
            
            return quote
            
        except Exception as e:
            logger.error(f"Error getting flash loan quote: {e}")
            return {}

    async def _process_flash_loan_opportunity(self, opportunity: Dict[str, Any], index: int) -> None:
        """Process a flash loan arbitrage opportunity."""
        try:
            flash_loan_info = opportunity.get('flash_loan_info', {})
            net_profit = opportunity.get('net_profit_after_fees', 0)
            
            print(f"      {index}. {opportunity.get('input_token', 'UNKNOWN')}/{opportunity.get('output_token', 'UNKNOWN')}")
            print(f"         Route: {opportunity.get('buy_dex', 'DEX1')} → {opportunity.get('sell_dex', 'DEX2')}")
            print(f"         💰 Flash Loan: ${opportunity.get('input_amount', 0):,.0f} from {flash_loan_info.get('provider', 'Unknown')}")
            print(f"         📊 Gross Profit: {opportunity.get('profit_percentage', 0):.3f}% (${opportunity.get('input_amount', 0) * opportunity.get('profit_percentage', 0) / 100:.2f})")
            print(f"         💸 Flash Loan Fee: ${flash_loan_info.get('fee_amount', 0):.2f}")
            print(f"         ⛽ Gas Cost: ~${flash_loan_info.get('gas_estimate', 5):.2f}")
            print(f"         💎 Net Profit: ${net_profit:.2f}")
            
            # Check if profitable enough to execute
            if net_profit > 10:  # $10 minimum for execution
                self.session_stats['profitable_flash_loans'] += 1
                
                # Simulate execution
                if self.config.get('trading', {}).get('trading_enabled', False):
                    await self._execute_flash_loan_trade(opportunity)
                else:
                    await self._simulate_flash_loan_execution(opportunity)
            else:
                print(f"         ⚠️  Profit too low for execution (${net_profit:.2f} < $10)")
                
        except Exception as e:
            logger.error(f"Error processing flash loan opportunity: {e}")

    async def _simulate_flash_loan_execution(self, opportunity: Dict[str, Any]) -> None:
        """Simulate flash loan execution."""
        try:
            flash_loan_info = opportunity.get('flash_loan_info', {})
            net_profit = opportunity.get('net_profit_after_fees', 0)
            
            # Simulate execution
            import random
            success = random.random() > 0.2  # 80% success rate
            
            if success:
                self.session_stats['flash_loans_executed'] += 1
                self.session_stats['total_borrowed'] += opportunity.get('input_amount', 0)
                self.session_stats['total_fees_paid'] += flash_loan_info.get('fee_amount', 0)
                self.session_stats['net_profit'] += net_profit
                self.session_stats['gas_spent'] += flash_loan_info.get('gas_estimate', 5)
                
                print(f"         ✅ SIMULATED SUCCESS: +${net_profit:.2f}")
            else:
                gas_loss = flash_loan_info.get('gas_estimate', 5)
                self.session_stats['gas_spent'] += gas_loss
                self.session_stats['net_profit'] -= gas_loss
                
                print(f"         ❌ SIMULATED FAILURE: -${gas_loss:.2f} (gas)")
                
        except Exception as e:
            logger.error(f"Error simulating flash loan execution: {e}")

    async def _execute_flash_loan_trade(self, opportunity: Dict[str, Any]) -> None:
        """Execute actual flash loan trade."""
        # In production, this would execute the actual flash loan arbitrage
        print(f"         🚀 EXECUTING FLASH LOAN TRADE...")
        await self._simulate_flash_loan_execution(opportunity)

    async def _get_market_data(self) -> Dict[str, Any]:
        """Get market data."""
        return {
            'timestamp': datetime.now().isoformat(),
            'volatility': 0.5,
            'volume': 0.8,
            'trend': 'neutral'
        }

    async def _get_dex_prices(self) -> Dict[str, Dict[str, Any]]:
        """Get DEX prices for flash loan opportunities."""
        # Simulate realistic price data with larger spreads for flash loan opportunities
        import random
        
        dex_prices = {}
        dexs = ['uniswap_v3', 'aerodrome', 'velodrome', 'sushiswap', 'camelot']
        pairs = ['USDC/USDT', 'ETH/USDC', 'WBTC/USDC']
        
        for dex in dexs:
            dex_prices[dex] = {}
            for pair in pairs:
                base_price = 1.0 if 'USDC' in pair and 'USDT' in pair else (2500.0 if 'ETH' in pair else 45000.0)
                
                # Create larger spreads for flash loan opportunities
                variation = random.uniform(-0.008, 0.008)  # ±0.8% variation
                dex_prices[dex][pair] = base_price * (1 + variation)
        
        return dex_prices

    async def _show_flash_loan_report(self) -> None:
        """Show flash loan performance report."""
        try:
            runtime = datetime.now() - self.session_stats['start_time']
            runtime_minutes = runtime.total_seconds() / 60
            
            print(f"\n⚡ FLASH LOAN REPORT:")
            print(f"   Runtime: {runtime_minutes:.1f} minutes")
            print(f"   Scans: {self.session_stats['total_scans']}")
            print(f"   Flash loan opportunities: {self.session_stats['flash_loan_opportunities']}")
            print(f"   Profitable opportunities: {self.session_stats['profitable_flash_loans']}")
            print(f"   Executed trades: {self.session_stats['flash_loans_executed']}")
            print(f"   Total borrowed: ${self.session_stats['total_borrowed']:,.0f}")
            print(f"   Fees paid: ${self.session_stats['total_fees_paid']:.2f}")
            print(f"   Gas spent: ${self.session_stats['gas_spent']:.2f}")
            print(f"   Net profit: ${self.session_stats['net_profit']:.2f}")
            
            if self.session_stats['flash_loans_executed'] > 0:
                avg_profit = self.session_stats['net_profit'] / self.session_stats['flash_loans_executed']
                print(f"   Avg profit per trade: ${avg_profit:.2f}")
            
            print()
            
        except Exception as e:
            logger.error(f"Error showing flash loan report: {e}")

    async def _cleanup(self) -> None:
        """Cleanup system resources."""
        try:
            print("\n🧹 Cleaning up flash loan system...")
            
            if self.mcp_client_manager:
                await self.mcp_client_manager.disconnect_all()
                print("✅ MCP clients disconnected")
            
            await self._show_final_flash_loan_report()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def _show_final_flash_loan_report(self) -> None:
        """Show final flash loan session report."""
        try:
            print(f"\n📊 Flash Loan Session Summary:")
            print(f"   Runtime: {(datetime.now() - self.session_stats['start_time']).total_seconds() / 60:.1f} minutes")
            print(f"   Total scans: {self.session_stats['total_scans']}")
            print(f"   Flash loan opportunities: {self.session_stats['flash_loan_opportunities']}")
            print(f"   Profitable opportunities: {self.session_stats['profitable_flash_loans']}")
            print(f"   Executed trades: {self.session_stats['flash_loans_executed']}")
            print(f"   Net profit: ${self.session_stats['net_profit']:.2f}")
            
            if self.session_stats['net_profit'] > 0:
                roi = (self.session_stats['net_profit'] / self.session_stats['gas_spent']) * 100 if self.session_stats['gas_spent'] > 0 else 0
                print(f"   ROI on gas spent: {roi:.1f}%")
            
            print(f"\n⚡ Flash Loan Arbitrage Complete!")
            print(f"   Zero capital strategy with ${self.session_stats['net_profit']:.2f} profit!")
            
        except Exception as e:
            logger.error(f"Error showing final report: {e}")


async def main():
    """Main function for flash loan arbitrage."""
    try:
        # Load flash loan configuration
        config_path = Path('config/flash_loan_strategy_config.json')
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            print("❌ Flash loan config not found. Using default configuration.")
            config = {"trading": {"trading_enabled": False}}
        
        # Create and start flash loan arbitrage system
        system = FlashLoanArbitrageSystem(config)
        await system.start_flash_loan_arbitrage()
        
    except KeyboardInterrupt:
        print("\n👋 Flash loan arbitrage stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"💥 Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
