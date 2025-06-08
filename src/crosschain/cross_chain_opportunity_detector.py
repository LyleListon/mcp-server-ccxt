#!/usr/bin/env python3
"""
🔍 CROSS-CHAIN OPPORTUNITY DETECTOR
Continuously scan for profitable cross-chain arbitrage opportunities
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from .cross_chain_arbitrage_executor import CrossChainOpportunity

logger = logging.getLogger(__name__)

class CrossChainOpportunityDetector:
    """Detect profitable cross-chain arbitrage opportunities."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize cross-chain opportunity detector."""
        self.config = config
        
        # Detection settings
        self.min_profit_pct = config.get('min_cross_chain_profit_pct', 1.0)  # 1% minimum
        self.min_profit_usd = config.get('min_cross_chain_profit_usd', 10.0)  # $10 minimum
        self.scan_interval_seconds = config.get('cross_chain_scan_interval', 30)  # 30 seconds
        self.opportunity_timeout_minutes = config.get('opportunity_timeout_minutes', 5)  # 5 minutes
        
        # Bridge cost estimates (will be updated dynamically)
        self.bridge_costs = {
            ('arbitrum', 'base'): {'fee_pct': 0.05, 'time_minutes': 2},
            ('base', 'arbitrum'): {'fee_pct': 0.05, 'time_minutes': 2},
            ('arbitrum', 'optimism'): {'fee_pct': 0.08, 'time_minutes': 3},
            ('optimism', 'arbitrum'): {'fee_pct': 0.08, 'time_minutes': 3},
            ('base', 'optimism'): {'fee_pct': 0.1, 'time_minutes': 4},
            ('optimism', 'base'): {'fee_pct': 0.1, 'time_minutes': 4},
        }
        
        # Opportunity tracking
        self.active_opportunities: List[CrossChainOpportunity] = []
        self.opportunity_callbacks: List[Callable] = []
        self.detection_stats = {
            'scans_completed': 0,
            'opportunities_found': 0,
            'opportunities_executed': 0,
            'average_profit_pct': 0.0
        }
        
        # Price history for trend analysis
        self.price_history = defaultdict(list)
        self.max_history_length = 100
        
        logger.info("🔍 Cross-chain opportunity detector initialized")
        logger.info(f"   💰 Min profit: {self.min_profit_pct}% / ${self.min_profit_usd}")
        logger.info(f"   ⏰ Scan interval: {self.scan_interval_seconds}s")
    
    def add_opportunity_callback(self, callback: Callable[[CrossChainOpportunity], None]):
        """Add callback for when opportunities are found."""
        self.opportunity_callbacks.append(callback)
    
    async def start_detection(self, price_aggregator):
        """Start continuous cross-chain opportunity detection."""
        logger.info("🔍 Starting cross-chain opportunity detection...")
        
        while True:
            try:
                await self._scan_for_opportunities(price_aggregator)
                await asyncio.sleep(self.scan_interval_seconds)
                
            except Exception as e:
                logger.error(f"Detection error: {e}")
                await asyncio.sleep(5)  # Short delay on error
    
    async def _scan_for_opportunities(self, price_aggregator):
        """Scan for cross-chain arbitrage opportunities."""
        try:
            scan_start = datetime.now()
            
            # Get current prices from all DEXs
            all_dex_prices = await price_aggregator.get_all_dex_prices()
            
            # Organize prices by token and chain
            tokens_by_chain = self._organize_prices_by_chain(all_dex_prices)
            
            # Find cross-chain opportunities
            opportunities = self._find_cross_chain_opportunities(tokens_by_chain)
            
            # Filter and rank opportunities
            viable_opportunities = self._filter_viable_opportunities(opportunities)
            
            scan_time = (datetime.now() - scan_start).total_seconds()
            
            # Update stats
            self.detection_stats['scans_completed'] += 1
            self.detection_stats['opportunities_found'] += len(viable_opportunities)
            
            if viable_opportunities:
                profits = [opp.profit_pct for opp in viable_opportunities]
                self.detection_stats['average_profit_pct'] = statistics.mean(profits)
                
                logger.info(f"🌉 CROSS-CHAIN SCAN COMPLETE:")
                logger.info(f"   ⏰ Scan time: {scan_time:.1f}s")
                logger.info(f"   🎯 Opportunities found: {len(viable_opportunities)}")
                logger.info(f"   💰 Best profit: {max(profits):.2f}%")
                
                # Process top opportunities
                for opportunity in viable_opportunities[:5]:  # Top 5
                    await self._process_opportunity(opportunity)
            else:
                logger.debug(f"🔍 Cross-chain scan: {len(opportunities)} total, 0 viable")
                
        except Exception as e:
            logger.error(f"Scan error: {e}")
    
    def _organize_prices_by_chain(self, all_dex_prices: Dict[str, List]) -> Dict[str, Dict[str, List]]:
        """Organize prices by token and chain."""
        tokens_by_chain = defaultdict(lambda: defaultdict(list))
        
        for dex_name, dex_prices in all_dex_prices.items():
            for price_data in dex_prices:
                try:
                    token = price_data.token
                    chain = price_data.chain
                    price = price_data.price
                    
                    if price > 0:
                        tokens_by_chain[token][chain].append({
                            'dex': dex_name,
                            'price': price,
                            'liquidity': getattr(price_data, 'liquidity', 0),
                            'timestamp': getattr(price_data, 'timestamp', datetime.now())
                        })
                        
                        # Update price history
                        history_key = f"{token}_{chain}"
                        self.price_history[history_key].append({
                            'price': price,
                            'timestamp': datetime.now()
                        })
                        
                        # Limit history length
                        if len(self.price_history[history_key]) > self.max_history_length:
                            self.price_history[history_key] = self.price_history[history_key][-self.max_history_length:]
                            
                except Exception as e:
                    continue
        
        return tokens_by_chain
    
    def _find_cross_chain_opportunities(self, tokens_by_chain: Dict[str, Dict[str, List]]) -> List[CrossChainOpportunity]:
        """Find cross-chain arbitrage opportunities."""
        opportunities = []
        
        for token, chains in tokens_by_chain.items():
            if len(chains) < 2:  # Need at least 2 chains
                continue
            
            chain_list = list(chains.keys())
            
            for i, buy_chain in enumerate(chain_list):
                for sell_chain in chain_list[i+1:]:
                    if buy_chain == sell_chain:
                        continue
                    
                    # Get price ranges on each chain
                    buy_chain_prices = [p['price'] for p in chains[buy_chain]]
                    sell_chain_prices = [p['price'] for p in chains[sell_chain]]
                    
                    if not buy_chain_prices or not sell_chain_prices:
                        continue
                    
                    # Find best prices
                    min_buy_price = min(buy_chain_prices)
                    max_sell_price = max(sell_chain_prices)
                    
                    # Check both directions
                    opportunities.extend([
                        self._create_opportunity(token, buy_chain, sell_chain, min_buy_price, max_sell_price, chains),
                        self._create_opportunity(token, sell_chain, buy_chain, 
                                               min(sell_chain_prices), max(buy_chain_prices), chains)
                    ])
        
        return [opp for opp in opportunities if opp is not None]
    
    def _create_opportunity(self, token: str, buy_chain: str, sell_chain: str, 
                          buy_price: float, sell_price: float, chains_data: Dict) -> Optional[CrossChainOpportunity]:
        """Create a cross-chain opportunity if profitable."""
        try:
            if buy_price >= sell_price:
                return None
            
            # Calculate gross profit
            gross_profit_pct = ((sell_price - buy_price) / buy_price) * 100
            
            # Estimate bridge costs
            bridge_key = (buy_chain, sell_chain)
            bridge_cost = self.bridge_costs.get(bridge_key, {'fee_pct': 0.15, 'time_minutes': 5})
            
            # Calculate net profit after bridge costs
            net_profit_pct = gross_profit_pct - bridge_cost['fee_pct']
            
            if net_profit_pct < self.min_profit_pct:
                return None
            
            # Estimate profit in USD based on ACTUAL WALLET BALANCE
            from src.config.trading_config import CONFIG
            max_trade_amount = CONFIG.MAX_TRADE_USD  # 75% of $458 = ~$343
            profit_usd = (net_profit_pct / 100) * max_trade_amount
            
            if profit_usd < self.min_profit_usd:
                return None
            
            # Find best DEXs for buy and sell
            buy_dex = self._find_best_dex_for_price(chains_data[buy_chain], buy_price, 'buy')
            sell_dex = self._find_best_dex_for_price(chains_data[sell_chain], sell_price, 'sell')
            
            return CrossChainOpportunity(
                token=token,
                buy_chain=buy_chain,
                sell_chain=sell_chain,
                buy_price=buy_price,
                sell_price=sell_price,
                profit_pct=net_profit_pct,
                profit_usd=profit_usd,
                buy_dex=buy_dex,
                sell_dex=sell_dex,
                timestamp=datetime.now(),
                execution_window_minutes=self.opportunity_timeout_minutes,
                bridge_fee_pct=bridge_cost['fee_pct'],
                estimated_bridge_time_minutes=bridge_cost['time_minutes']
            )
            
        except Exception as e:
            logger.error(f"Opportunity creation error: {e}")
            return None
    
    def _find_best_dex_for_price(self, chain_prices: List[Dict], target_price: float, side: str) -> str:
        """Find the DEX offering the best price."""
        best_dex = "unknown"
        best_price_diff = float('inf')
        
        for price_data in chain_prices:
            price_diff = abs(price_data['price'] - target_price)
            if price_diff < best_price_diff:
                best_price_diff = price_diff
                best_dex = price_data['dex']
        
        return best_dex
    
    def _filter_viable_opportunities(self, opportunities: List[CrossChainOpportunity]) -> List[CrossChainOpportunity]:
        """Filter and rank viable opportunities."""
        viable = []
        
        for opp in opportunities:
            # Check minimum thresholds
            if opp.profit_pct < self.min_profit_pct:
                continue
            if opp.profit_usd < self.min_profit_usd:
                continue
            
            # Check if opportunity is too old
            age_minutes = (datetime.now() - opp.timestamp).total_seconds() / 60
            if age_minutes > opp.execution_window_minutes:
                continue
            
            # Check for price trend stability
            if self._is_price_trend_stable(opp.token, opp.buy_chain, opp.sell_chain):
                viable.append(opp)
        
        # Sort by profitability
        viable.sort(key=lambda x: x.profit_pct, reverse=True)
        
        return viable
    
    def _is_price_trend_stable(self, token: str, buy_chain: str, sell_chain: str) -> bool:
        """Check if price trend is stable enough for execution."""
        try:
            # Get recent price history
            buy_history = self.price_history.get(f"{token}_{buy_chain}", [])
            sell_history = self.price_history.get(f"{token}_{sell_chain}", [])
            
            if len(buy_history) < 3 or len(sell_history) < 3:
                return True  # Not enough history, assume stable
            
            # Check recent price volatility
            recent_buy_prices = [p['price'] for p in buy_history[-5:]]
            recent_sell_prices = [p['price'] for p in sell_history[-5:]]
            
            buy_volatility = (max(recent_buy_prices) - min(recent_buy_prices)) / statistics.mean(recent_buy_prices)
            sell_volatility = (max(recent_sell_prices) - min(recent_sell_prices)) / statistics.mean(recent_sell_prices)
            
            # Consider stable if volatility < 2%
            return buy_volatility < 0.02 and sell_volatility < 0.02
            
        except Exception as e:
            logger.error(f"Price trend analysis error: {e}")
            return True  # Assume stable on error
    
    async def _process_opportunity(self, opportunity: CrossChainOpportunity):
        """Process a detected opportunity."""
        try:
            # Add to active opportunities
            self.active_opportunities.append(opportunity)
            
            # Clean up old opportunities
            cutoff_time = datetime.now() - timedelta(minutes=self.opportunity_timeout_minutes)
            self.active_opportunities = [
                opp for opp in self.active_opportunities 
                if opp.timestamp > cutoff_time
            ]
            
            # Notify callbacks
            for callback in self.opportunity_callbacks:
                try:
                    await callback(opportunity)
                except Exception as e:
                    logger.error(f"Opportunity callback error: {e}")
            
            logger.info(f"🎯 CROSS-CHAIN OPPORTUNITY DETECTED:")
            logger.info(f"   Token: {opportunity.token}")
            logger.info(f"   Route: {opportunity.buy_chain} → {opportunity.sell_chain}")
            logger.info(f"   Profit: {opportunity.profit_pct:.2f}% (${opportunity.profit_usd:.2f})")
            logger.info(f"   DEXs: {opportunity.buy_dex} → {opportunity.sell_dex}")
            logger.info(f"   Bridge time: ~{opportunity.estimated_bridge_time_minutes} min")
            
        except Exception as e:
            logger.error(f"Opportunity processing error: {e}")
    
    def get_active_opportunities(self) -> List[CrossChainOpportunity]:
        """Get currently active opportunities."""
        # Clean up expired opportunities
        cutoff_time = datetime.now() - timedelta(minutes=self.opportunity_timeout_minutes)
        self.active_opportunities = [
            opp for opp in self.active_opportunities 
            if opp.timestamp > cutoff_time
        ]
        
        return self.active_opportunities.copy()
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get detection statistics."""
        return self.detection_stats.copy()
