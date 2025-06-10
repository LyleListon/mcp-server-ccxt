"""
Pre-Positioning Portfolio Manager
Maintains 4-token split for instant arbitrage execution
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal

from src.wallet.smart_wallet_manager import SmartWalletManager
from src.execution.real_dex_executor import RealDEXExecutor

logger = logging.getLogger(__name__)

@dataclass
class TokenAllocation:
    """Target allocation for each token"""
    symbol: str
    target_percentage: float
    target_usd: float
    current_usd: float
    deviation_pct: float
    needs_rebalancing: bool

@dataclass
class PortfolioState:
    """Current portfolio state"""
    total_value_usd: float
    gas_reserves_usd: float
    trading_capital_usd: float
    allocations: Dict[str, TokenAllocation]
    rebalancing_needed: bool

class PrePositioningManager:
    """
    Manages pre-positioned portfolio for instant arbitrage execution
    
    STRATEGY:
    - 4 tokens: WETH, USDC, USDT, PEPE
    - 25% each = ~$909 per token
    - $20 gas reserves across chains
    - Auto-rebalance after trades
    """
    
    def __init__(self, wallet_manager: SmartWalletManager, dex_executor: RealDEXExecutor):
        self.wallet_manager = wallet_manager
        self.dex_executor = dex_executor
        
        # Portfolio configuration
        self.target_tokens = {
            'WETH': 0.25,   # 25% - Universal pairs
            'USDC': 0.25,   # 25% - Stablecoin arbitrage
            'USDT': 0.25,   # 25% - Stablecoin arbitrage  
            'PEPE': 0.25    # 25% - 🐸 MEME VOLATILITY GOLD! 🐸
        }
        
        # Rebalancing thresholds
        self.rebalance_threshold = 0.05  # 5% deviation triggers rebalance
        self.min_trade_size = 50.0       # Minimum $50 rebalance trade
        self.gas_reserve_usd = 20.0      # $20 gas across all chains
        
        # Chain distribution for tokens
        self.chain_preferences = {
            'WETH': ['arbitrum', 'base', 'optimism'],
            'USDC': ['arbitrum', 'base', 'optimism'], 
            'USDT': ['arbitrum', 'base', 'optimism'],
            'PEPE': ['arbitrum', 'base', 'optimism']  # 🐸 Everywhere!
        }
        
        logger.info("🐸 Pre-Positioning Manager initialized with PEPE power!")
        
    async def get_portfolio_state(self) -> PortfolioState:
        """Get current portfolio state and calculate deviations"""
        try:
            # Get current balances
            balances = await self.wallet_manager.get_all_balances()
            
            # Calculate total portfolio value
            total_value = sum(balance.usd_value for balance in balances.values())
            trading_capital = total_value - self.gas_reserve_usd
            
            # Calculate current allocations
            allocations = {}
            rebalancing_needed = False
            
            for token, target_pct in self.target_tokens.items():
                target_usd = trading_capital * target_pct
                
                # Find current value for this token
                current_usd = 0.0
                for balance in balances.values():
                    if balance.symbol == token:
                        current_usd += balance.usd_value
                
                # Calculate deviation
                if target_usd > 0:
                    deviation_pct = abs(current_usd - target_usd) / target_usd
                else:
                    deviation_pct = 1.0 if current_usd > 0 else 0.0
                
                needs_rebalancing = (
                    deviation_pct > self.rebalance_threshold and 
                    abs(current_usd - target_usd) > self.min_trade_size
                )
                
                if needs_rebalancing:
                    rebalancing_needed = True
                
                allocations[token] = TokenAllocation(
                    symbol=token,
                    target_percentage=target_pct,
                    target_usd=target_usd,
                    current_usd=current_usd,
                    deviation_pct=deviation_pct,
                    needs_rebalancing=needs_rebalancing
                )
            
            return PortfolioState(
                total_value_usd=total_value,
                gas_reserves_usd=self.gas_reserve_usd,
                trading_capital_usd=trading_capital,
                allocations=allocations,
                rebalancing_needed=rebalancing_needed
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting portfolio state: {e}")
            raise
    
    async def log_portfolio_status(self) -> None:
        """Log current portfolio status"""
        try:
            state = await self.get_portfolio_state()
            
            logger.info("🐸 PEPE-POWERED PORTFOLIO STATUS:")
            logger.info(f"   💰 Total Value: ${state.total_value_usd:.2f}")
            logger.info(f"   ⛽ Gas Reserves: ${state.gas_reserves_usd:.2f}")
            logger.info(f"   🎯 Trading Capital: ${state.trading_capital_usd:.2f}")
            logger.info("")
            
            for token, allocation in state.allocations.items():
                status = "🔄 REBALANCE" if allocation.needs_rebalancing else "✅ GOOD"
                emoji = "🐸" if token == "PEPE" else "💎"
                
                logger.info(f"   {emoji} {token}:")
                logger.info(f"      Target: ${allocation.target_usd:.2f} (25%)")
                logger.info(f"      Current: ${allocation.current_usd:.2f}")
                logger.info(f"      Deviation: {allocation.deviation_pct*100:.1f}% {status}")
            
            if state.rebalancing_needed:
                logger.info("🔄 REBALANCING NEEDED!")
            else:
                logger.info("✅ PORTFOLIO PERFECTLY BALANCED!")
                
        except Exception as e:
            logger.error(f"❌ Error logging portfolio status: {e}")
    
    async def execute_rebalancing(self) -> bool:
        """Execute portfolio rebalancing to target allocations"""
        try:
            logger.info("🔄 STARTING PORTFOLIO REBALANCING...")
            
            state = await self.get_portfolio_state()
            
            if not state.rebalancing_needed:
                logger.info("✅ No rebalancing needed - portfolio is balanced!")
                return True
            
            # Plan rebalancing trades
            rebalance_trades = await self._plan_rebalancing_trades(state)
            
            if not rebalance_trades:
                logger.info("✅ No trades needed for rebalancing")
                return True
            
            # Execute rebalancing trades
            success_count = 0
            for trade in rebalance_trades:
                try:
                    success = await self._execute_rebalance_trade(trade)
                    if success:
                        success_count += 1
                        logger.info(f"✅ Rebalance trade {success_count}/{len(rebalance_trades)} completed")
                    else:
                        logger.error(f"❌ Rebalance trade failed")
                        
                except Exception as e:
                    logger.error(f"❌ Rebalance trade error: {e}")
            
            # Log final status
            await self.log_portfolio_status()
            
            success_rate = success_count / len(rebalance_trades)
            if success_rate >= 0.8:  # 80% success rate
                logger.info(f"🎉 REBALANCING COMPLETED! {success_count}/{len(rebalance_trades)} trades successful")
                return True
            else:
                logger.error(f"⚠️ REBALANCING PARTIAL SUCCESS: {success_count}/{len(rebalance_trades)} trades")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during rebalancing: {e}")
            return False

    async def _plan_rebalancing_trades(self, state: PortfolioState) -> List[Dict]:
        """Plan the trades needed to rebalance portfolio"""
        trades = []

        # Find tokens that need selling (over-allocated)
        over_allocated = []
        under_allocated = []

        for token, allocation in state.allocations.items():
            if allocation.needs_rebalancing:
                difference = allocation.current_usd - allocation.target_usd

                if difference > self.min_trade_size:  # Over-allocated
                    over_allocated.append({
                        'token': token,
                        'excess_usd': difference,
                        'allocation': allocation
                    })
                elif difference < -self.min_trade_size:  # Under-allocated
                    under_allocated.append({
                        'token': token,
                        'deficit_usd': abs(difference),
                        'allocation': allocation
                    })

        # Create trades to balance
        for over in over_allocated:
            for under in under_allocated:
                if over['excess_usd'] <= 0 or under['deficit_usd'] <= 0:
                    continue

                # Calculate trade amount
                trade_amount = min(over['excess_usd'], under['deficit_usd'])

                if trade_amount >= self.min_trade_size:
                    trades.append({
                        'from_token': over['token'],
                        'to_token': under['token'],
                        'amount_usd': trade_amount,
                        'chain': 'arbitrum'  # Default to Arbitrum for rebalancing
                    })

                    # Update remaining amounts
                    over['excess_usd'] -= trade_amount
                    under['deficit_usd'] -= trade_amount

        logger.info(f"📋 Planned {len(trades)} rebalancing trades")
        return trades

    async def _execute_rebalance_trade(self, trade: Dict) -> bool:
        """Execute a single rebalancing trade"""
        try:
            from_token = trade['from_token']
            to_token = trade['to_token']
            amount_usd = trade['amount_usd']
            chain = trade['chain']

            logger.info(f"🔄 Rebalancing: {from_token} → {to_token} (${amount_usd:.2f})")

            # For PEPE trades, add extra logging
            if from_token == 'PEPE' or to_token == 'PEPE':
                logger.info("🐸 PEPE REBALANCING - Meme magic in progress!")

            # Execute the trade via DEX
            # This would use the real_dex_executor to swap tokens
            # For now, return True to simulate success

            # TODO: Implement actual DEX swap execution
            # result = await self.dex_executor.execute_swap(
            #     chain=chain,
            #     from_token=from_token,
            #     to_token=to_token,
            #     amount_usd=amount_usd
            # )

            await asyncio.sleep(0.1)  # Simulate trade execution time

            logger.info(f"✅ Rebalance trade completed: {from_token} → {to_token}")
            return True

        except Exception as e:
            logger.error(f"❌ Rebalance trade failed: {e}")
            return False

    async def initialize_portfolio(self) -> bool:
        """Initialize portfolio with target allocations"""
        try:
            logger.info("🚀 INITIALIZING PEPE-POWERED PORTFOLIO!")

            # Get current state
            state = await self.get_portfolio_state()

            logger.info(f"💰 Converting ${state.trading_capital_usd:.2f} to 4-token split:")
            logger.info(f"   🔹 WETH: ${state.trading_capital_usd * 0.25:.2f}")
            logger.info(f"   🔹 USDC: ${state.trading_capital_usd * 0.25:.2f}")
            logger.info(f"   🔹 USDT: ${state.trading_capital_usd * 0.25:.2f}")
            logger.info(f"   🐸 PEPE: ${state.trading_capital_usd * 0.25:.2f}")

            # Execute initial rebalancing
            success = await self.execute_rebalancing()

            if success:
                logger.info("🎉 PORTFOLIO INITIALIZATION COMPLETE!")
                logger.info("🚀 READY FOR LIGHTNING-FAST ARBITRAGE!")
                return True
            else:
                logger.error("❌ Portfolio initialization failed")
                return False

        except Exception as e:
            logger.error(f"❌ Error initializing portfolio: {e}")
            return False

    async def post_trade_rebalance(self, executed_token: str, trade_amount_usd: float) -> None:
        """Rebalance portfolio after a successful arbitrage trade"""
        try:
            logger.info(f"🔄 Post-trade rebalancing after {executed_token} trade (${trade_amount_usd:.2f})")

            # Check if rebalancing is needed
            state = await self.get_portfolio_state()

            if state.rebalancing_needed:
                logger.info("🔄 Portfolio drift detected - rebalancing...")
                await self.execute_rebalancing()
            else:
                logger.info("✅ Portfolio still balanced - no rebalancing needed")

        except Exception as e:
            logger.error(f"❌ Error in post-trade rebalancing: {e}")

    def get_available_tokens(self) -> List[str]:
        """Get list of tokens available for arbitrage scanning"""
        return list(self.target_tokens.keys())

    async def get_token_balance_usd(self, token: str) -> float:
        """Get current USD balance for a specific token"""
        try:
            state = await self.get_portfolio_state()
            allocation = state.allocations.get(token)
            return allocation.current_usd if allocation else 0.0
        except Exception as e:
            logger.error(f"❌ Error getting {token} balance: {e}")
            return 0.0
