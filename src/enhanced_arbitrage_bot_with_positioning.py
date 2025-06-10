#!/usr/bin/env python3
"""
Enhanced Arbitrage Bot with Pre-Positioning
Integrates the PEPE-powered pre-positioning system with existing arbitrage infrastructure
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, List, Any

# Import existing arbitrage components
from src.real_arbitrage_bot import RealArbitrageBot
from src.portfolio.pre_positioning_manager import PrePositioningManager
from src.portfolio.portfolio_arbitrage_integration import PortfolioArbitrageSystem
from src.wallet.smart_wallet_manager import SmartWalletManager
from src.execution.real_dex_executor import RealDEXExecutor
from src.execution.real_arbitrage_executor import RealArbitrageExecutor

# Configuration
from src.config.trading_config import CONFIG

logger = logging.getLogger(__name__)

class EnhancedArbitrageBotWithPositioning:
    """
    Enhanced arbitrage bot with pre-positioning system
    
    INTEGRATION STRATEGY:
    1. Initialize 4-token pre-positioned portfolio (WETH, USDC, USDT, PEPE)
    2. Modify opportunity scanning to focus on these 4 tokens only
    3. Execute trades instantly with pre-positioned funds
    4. Auto-rebalance after each trade
    """
    
    def __init__(self):
        """Initialize the enhanced bot with pre-positioning."""
        self.running = False
        
        # Core arbitrage bot (existing system)
        self.arbitrage_bot = RealArbitrageBot()
        
        # Pre-positioning components (new system)
        self.portfolio_manager = None
        self.portfolio_arbitrage_system = None
        
        # Integration flags
        self.pre_positioning_enabled = True
        self.target_tokens = ['WETH', 'USDC', 'USDT', 'PEPE']  # 4-token focus
        
        # Performance tracking
        self.stats = {
            'pre_positioned_trades': 0,
            'traditional_trades': 0,
            'rebalancing_operations': 0,
            'total_profit_usd': 0.0,
            'start_time': datetime.now()
        }
        
        logger.info("🐸 Enhanced Arbitrage Bot with Pre-Positioning initialized!")
    
    async def initialize(self, private_key: str) -> bool:
        """Initialize the complete enhanced system."""
        try:
            logger.info("🚀 INITIALIZING ENHANCED ARBITRAGE SYSTEM WITH PRE-POSITIONING!")
            
            # Initialize core arbitrage bot first
            logger.info("📊 Initializing core arbitrage infrastructure...")
            core_success = await self.arbitrage_bot.initialize()
            if not core_success:
                logger.error("❌ Core arbitrage bot initialization failed")
                return False
            
            logger.info("✅ Core arbitrage infrastructure ready")
            
            # Initialize pre-positioning system
            if self.pre_positioning_enabled:
                logger.info("🐸 Initializing PEPE-powered pre-positioning system...")
                
                # Get wallet manager from core bot
                wallet_manager = self.arbitrage_bot.smart_wallet_manager
                if not wallet_manager:
                    logger.error("❌ Wallet manager not available from core bot")
                    return False
                
                # Create DEX executor for portfolio operations
                dex_executor = RealDEXExecutor({})
                
                # Initialize portfolio manager
                self.portfolio_manager = PrePositioningManager(wallet_manager, dex_executor)
                
                # Initialize integrated portfolio arbitrage system
                self.portfolio_arbitrage_system = PortfolioArbitrageSystem(
                    self.portfolio_manager,
                    None,  # Will use existing opportunity detector
                    None   # Will use existing arbitrage executor
                )
                
                # Initialize the portfolio with 4-token split
                portfolio_success = await self.portfolio_manager.initialize_portfolio()
                if portfolio_success:
                    logger.info("🎉 PRE-POSITIONING SYSTEM READY!")
                    await self.portfolio_manager.log_portfolio_status()
                else:
                    logger.warning("⚠️ Pre-positioning initialization failed - continuing with traditional arbitrage")
                    self.pre_positioning_enabled = False
            
            logger.info("✅ ENHANCED ARBITRAGE SYSTEM FULLY INITIALIZED!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Enhanced system initialization error: {e}")
            return False
    
    async def run(self) -> None:
        """Main enhanced bot loop with pre-positioning."""
        try:
            logger.info("🎯 Starting enhanced arbitrage with pre-positioning...")
            self.running = True
            
            while self.running:
                try:
                    # Run enhanced arbitrage cycle
                    await self._enhanced_arbitrage_cycle()
                    
                    # Brief pause between cycles
                    await asyncio.sleep(self.arbitrage_bot.config['trading']['scan_interval'])
                    
                except Exception as e:
                    logger.error(f"Error in enhanced arbitrage cycle: {e}")
                    await asyncio.sleep(5)
                    
        except KeyboardInterrupt:
            logger.info("Enhanced bot stopped by user")
        except Exception as e:
            logger.error(f"Enhanced bot crashed: {e}")
        finally:
            await self._shutdown()
    
    async def _enhanced_arbitrage_cycle(self) -> None:
        """Enhanced arbitrage cycle with pre-positioning."""
        try:
            if self.pre_positioning_enabled and self.portfolio_manager:
                # Use pre-positioned portfolio approach
                await self._pre_positioned_arbitrage_cycle()
            else:
                # Fall back to traditional arbitrage
                await self._traditional_arbitrage_cycle()
                
        except Exception as e:
            logger.error(f"Error in enhanced arbitrage cycle: {e}")
    
    async def _pre_positioned_arbitrage_cycle(self) -> None:
        """Arbitrage cycle using pre-positioned tokens."""
        try:
            # Check portfolio status
            portfolio_state = await self.portfolio_manager.get_portfolio_state()
            
            # Rebalance if needed (before scanning)
            if portfolio_state.rebalancing_needed:
                logger.info("🔄 Portfolio rebalancing needed before scanning...")
                rebalance_success = await self.portfolio_manager.execute_rebalancing()
                if rebalance_success:
                    self.stats['rebalancing_operations'] += 1
                    logger.info("✅ Portfolio rebalanced - ready for arbitrage")
                else:
                    logger.warning("⚠️ Rebalancing failed - continuing with current allocation")
            
            # Scan for opportunities using ONLY pre-positioned tokens
            opportunities = await self._scan_pre_positioned_opportunities()
            
            if opportunities:
                logger.info(f"🎯 Found {len(opportunities)} pre-positioned opportunities")
                
                # Execute the best opportunity
                best_opportunity = opportunities[0]
                success = await self._execute_pre_positioned_opportunity(best_opportunity)
                
                if success:
                    self.stats['pre_positioned_trades'] += 1
                    logger.info("🎉 Pre-positioned arbitrage completed successfully!")
                    
                    # Post-trade rebalancing
                    await self.portfolio_manager.post_trade_rebalance(
                        best_opportunity['token'], 
                        best_opportunity.get('estimated_profit_usd', 0)
                    )
                else:
                    logger.error("❌ Pre-positioned arbitrage failed")
            else:
                logger.info("🔍 No pre-positioned opportunities found this cycle")
                
        except Exception as e:
            logger.error(f"Error in pre-positioned arbitrage cycle: {e}")
    
    async def _scan_pre_positioned_opportunities(self) -> List[Dict[str, Any]]:
        """Scan for opportunities using only pre-positioned tokens."""
        try:
            # ENHANCED: Configure DEX manager to scan ONLY our 4 target tokens
            # This dramatically reduces scanning time and focuses on executable opportunities

            logger.info(f"🔍 Scanning for opportunities with {len(self.target_tokens)} pre-positioned tokens...")

            # Get opportunities from core bot but with token filtering
            all_opportunities = await self.arbitrage_bot.dex_manager.find_arbitrage_opportunities(
                min_profit_percentage=self.arbitrage_bot.config['trading']['min_profit_threshold'],
                target_tokens=self.target_tokens  # Focus scanning on our tokens
            )

            # Filter and enhance opportunities for pre-positioned execution
            pre_positioned_opportunities = []

            for opportunity in all_opportunities:
                base_token = opportunity.get('base_token', '')
                quote_token = opportunity.get('quote_token', '')

                # Check if either token is in our pre-positioned portfolio
                if (base_token in self.target_tokens or quote_token in self.target_tokens):
                    # Determine which token we'll use from our portfolio
                    token_to_check = base_token if base_token in self.target_tokens else quote_token
                    available_balance = await self.portfolio_manager.get_token_balance_usd(token_to_check)

                    if available_balance >= 50:  # Minimum $50 for arbitrage
                        # Calculate maximum trade size based on available balance
                        max_trade_size = min(available_balance * 0.75, opportunity.get('estimated_profit_usd', 0) * 10)

                        # Enhance opportunity with pre-positioning data
                        opportunity['pre_positioned_token'] = token_to_check
                        opportunity['available_balance_usd'] = available_balance
                        opportunity['max_trade_size_usd'] = max_trade_size
                        opportunity['execution_ready'] = True
                        opportunity['execution_type'] = 'pre_positioned'

                        pre_positioned_opportunities.append(opportunity)

                        # Log the opportunity with enhanced details
                        emoji = "🐸" if token_to_check == "PEPE" else "💎"
                        logger.info(f"   {emoji} {token_to_check}: ${opportunity['estimated_profit_usd']:.2f} profit")
                        logger.info(f"      Available: ${available_balance:.2f} | Max trade: ${max_trade_size:.2f}")

            # Sort by profit potential and execution readiness
            pre_positioned_opportunities.sort(
                key=lambda x: (x.get('execution_ready', False), x.get('estimated_profit_usd', 0)),
                reverse=True
            )

            if pre_positioned_opportunities:
                logger.info(f"🎯 {len(pre_positioned_opportunities)} pre-positioned opportunities ready for execution")

            return pre_positioned_opportunities

        except Exception as e:
            logger.error(f"Error scanning pre-positioned opportunities: {e}")
            return []
    
    async def _execute_pre_positioned_opportunity(self, opportunity: Dict[str, Any]) -> bool:
        """Execute arbitrage opportunity using pre-positioned funds."""
        try:
            token = opportunity.get('pre_positioned_token', '')
            profit = opportunity.get('estimated_profit_usd', 0)
            
            emoji = "🐸" if token == "PEPE" else "💎"
            logger.info(f"🚀 EXECUTING PRE-POSITIONED {emoji} {token} ARBITRAGE!")
            logger.info(f"   💰 Expected profit: ${profit:.2f}")
            logger.info(f"   ⚡ Using pre-positioned funds - INSTANT EXECUTION!")
            
            # Use existing arbitrage executor but with pre-positioned context
            execution_result = await self.arbitrage_bot._execute_real_arbitrage(opportunity)
            
            if execution_result:
                self.stats['total_profit_usd'] += profit
                logger.info(f"✅ {emoji} {token} PRE-POSITIONED ARBITRAGE SUCCESS!")
                return True
            else:
                logger.error(f"❌ {emoji} {token} pre-positioned arbitrage failed")
                return False
                
        except Exception as e:
            logger.error(f"Error executing pre-positioned opportunity: {e}")
            return False
    
    async def _traditional_arbitrage_cycle(self) -> None:
        """Fall back to traditional arbitrage cycle."""
        try:
            logger.info("📊 Running traditional arbitrage cycle...")
            await self.arbitrage_bot._scan_for_opportunities()
            self.stats['traditional_trades'] += 1
            
        except Exception as e:
            logger.error(f"Error in traditional arbitrage cycle: {e}")
    
    async def _log_enhanced_statistics(self) -> None:
        """Log enhanced performance statistics."""
        try:
            runtime = datetime.now() - self.stats['start_time']
            
            logger.info("📊 ENHANCED ARBITRAGE PERFORMANCE:")
            logger.info(f"   ⚡ Pre-positioned trades: {self.stats['pre_positioned_trades']}")
            logger.info(f"   📊 Traditional trades: {self.stats['traditional_trades']}")
            logger.info(f"   🔄 Rebalancing operations: {self.stats['rebalancing_operations']}")
            logger.info(f"   💰 Total profit: ${self.stats['total_profit_usd']:.2f}")
            logger.info(f"   ⏱️ Runtime: {runtime}")
            
            # Log portfolio status if available
            if self.portfolio_manager:
                await self.portfolio_manager.log_portfolio_status()
                
        except Exception as e:
            logger.error(f"Error logging enhanced statistics: {e}")
    
    async def _shutdown(self) -> None:
        """Shutdown the enhanced system."""
        try:
            logger.info("🛑 Shutting down enhanced arbitrage system...")
            
            # Log final statistics
            await self._log_enhanced_statistics()
            
            # Shutdown core bot
            if hasattr(self.arbitrage_bot, '_shutdown'):
                await self.arbitrage_bot._shutdown()
            
            logger.info("✅ Enhanced arbitrage system shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

async def main():
    """Main function to run the enhanced arbitrage bot."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Get private key from environment
    import os
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        logger.error("❌ PRIVATE_KEY environment variable not set")
        return 1
    
    # Create and run enhanced bot
    bot = EnhancedArbitrageBotWithPositioning()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info("🛑 Received shutdown signal")
        bot.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize and run
        if await bot.initialize(private_key):
            logger.info("🚀 ENHANCED ARBITRAGE BOT WITH PRE-POSITIONING STARTED!")
            await bot.run()
        else:
            logger.error("❌ Bot initialization failed")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
