"""
Advanced Opportunity Filter System
Filters arbitrage opportunities based on freshness, profitability, and execution speed.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FilterResult:
    """Result of opportunity filtering."""
    should_execute: bool
    reason: str
    priority_score: float
    estimated_execution_time: float
    profit_decay_factor: float

class AdvancedOpportunityFilter:
    """Advanced filtering system for arbitrage opportunities."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Filter thresholds
        self.max_opportunity_age_seconds = config.get('max_opportunity_age_seconds', 30)
        self.min_profit_after_decay = config.get('min_profit_after_decay', 1.0)
        self.min_execution_speed_score = config.get('min_execution_speed_score', 0.3)
        self.max_estimated_execution_time = config.get('max_estimated_execution_time', 15.0)
        
        # DEX execution speed profiles (seconds)
        self.dex_speed_profiles = {
            'sushiswap': {'avg_time': 3.0, 'reliability': 0.9},
            'uniswap_v3': {'avg_time': 2.5, 'reliability': 0.95},
            'camelot': {'avg_time': 4.0, 'reliability': 0.8},
            'balancer': {'avg_time': 5.0, 'reliability': 0.7},
            'dodo': {'avg_time': 6.0, 'reliability': 0.6},
            'woofi': {'avg_time': 4.5, 'reliability': 0.75},
            'zyberswap': {'avg_time': 5.5, 'reliability': 0.65}
        }
        
        # Market volatility windows (better execution during high volatility)
        self.optimal_volatility_range = (0.02, 0.15)  # 2-15% volatility
        
        # Opportunity tracking for freshness
        self.seen_opportunities = {}
        self.execution_history = []
        
    def filter_opportunity(self, opportunity: Dict[str, Any]) -> FilterResult:
        """
        Apply advanced filtering to an arbitrage opportunity.
        
        Args:
            opportunity: The arbitrage opportunity to filter
            
        Returns:
            FilterResult with decision and metadata
        """
        try:
            # 1. Freshness Filter
            freshness_result = self._check_freshness(opportunity)
            if not freshness_result['is_fresh']:
                return FilterResult(
                    should_execute=False,
                    reason=f"Stale opportunity: {freshness_result['reason']}",
                    priority_score=0.0,
                    estimated_execution_time=0.0,
                    profit_decay_factor=0.0
                )
            
            # 2. Profit Decay Analysis
            profit_decay = self._calculate_profit_decay(opportunity)
            adjusted_profit = opportunity.get('estimated_profit_usd', 0) * profit_decay['factor']
            
            if adjusted_profit < self.min_profit_after_decay:
                return FilterResult(
                    should_execute=False,
                    reason=f"Profit too low after decay: ${adjusted_profit:.2f} < ${self.min_profit_after_decay}",
                    priority_score=0.0,
                    estimated_execution_time=0.0,
                    profit_decay_factor=profit_decay['factor']
                )
            
            # 3. Execution Speed Analysis
            speed_analysis = self._analyze_execution_speed(opportunity)
            
            if speed_analysis['estimated_time'] > self.max_estimated_execution_time:
                return FilterResult(
                    should_execute=False,
                    reason=f"Execution too slow: {speed_analysis['estimated_time']:.1f}s > {self.max_estimated_execution_time}s",
                    priority_score=0.0,
                    estimated_execution_time=speed_analysis['estimated_time'],
                    profit_decay_factor=profit_decay['factor']
                )
            
            # 4. Market Volatility Check
            volatility_score = self._check_market_volatility(opportunity)
            
            # 5. Calculate Priority Score
            priority_score = self._calculate_priority_score(
                opportunity, profit_decay, speed_analysis, volatility_score
            )
            
            # 6. Final Decision
            should_execute = (
                priority_score >= 0.5 and  # Minimum priority threshold
                speed_analysis['speed_score'] >= self.min_execution_speed_score and
                adjusted_profit >= self.min_profit_after_decay
            )
            
            reason = "EXECUTE" if should_execute else "Low priority score or speed"
            
            return FilterResult(
                should_execute=should_execute,
                reason=reason,
                priority_score=priority_score,
                estimated_execution_time=speed_analysis['estimated_time'],
                profit_decay_factor=profit_decay['factor']
            )
            
        except Exception as e:
            logger.error(f"Error filtering opportunity: {e}")
            return FilterResult(
                should_execute=False,
                reason=f"Filter error: {e}",
                priority_score=0.0,
                estimated_execution_time=0.0,
                profit_decay_factor=0.0
            )
    
    def _check_freshness(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Check if opportunity is fresh enough to execute."""
        try:
            # Get opportunity timestamp
            timestamp_str = opportunity.get('timestamp')
            if not timestamp_str:
                return {'is_fresh': False, 'reason': 'No timestamp'}
            
            # Parse timestamp
            if isinstance(timestamp_str, str):
                opportunity_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                opportunity_time = datetime.fromtimestamp(timestamp_str)
            
            # Calculate age
            current_time = datetime.now()
            age_seconds = (current_time - opportunity_time).total_seconds()
            
            # Check if too old
            if age_seconds > self.max_opportunity_age_seconds:
                return {
                    'is_fresh': False, 
                    'reason': f'Age {age_seconds:.1f}s > {self.max_opportunity_age_seconds}s',
                    'age_seconds': age_seconds
                }
            
            # Check for duplicate opportunities (same token pair + DEXs)
            opp_key = f"{opportunity.get('base_token', '')}_{opportunity.get('quote_token', '')}_{opportunity.get('buy_dex', '')}_{opportunity.get('sell_dex', '')}"
            
            if opp_key in self.seen_opportunities:
                last_seen = self.seen_opportunities[opp_key]
                if (current_time - last_seen).total_seconds() < 5:  # Seen within 5 seconds
                    return {'is_fresh': False, 'reason': 'Duplicate opportunity', 'age_seconds': age_seconds}
            
            # Mark as seen
            self.seen_opportunities[opp_key] = current_time
            
            return {'is_fresh': True, 'reason': 'Fresh opportunity', 'age_seconds': age_seconds}
            
        except Exception as e:
            logger.error(f"Error checking freshness: {e}")
            return {'is_fresh': False, 'reason': f'Freshness check error: {e}'}
    
    def _calculate_profit_decay(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate how much profit has likely decayed due to market movement."""
        try:
            # Get opportunity age
            freshness = self._check_freshness(opportunity)
            age_seconds = freshness.get('age_seconds', 0)
            
            # Profit decay model: exponential decay based on age and volatility
            # Higher volatility = faster decay
            base_decay_rate = 0.05  # 5% per second base rate
            volatility_multiplier = opportunity.get('market_volatility', 0.1) * 10  # Scale volatility
            
            decay_rate = base_decay_rate * (1 + volatility_multiplier)
            decay_factor = max(0.1, 1.0 - (decay_rate * age_seconds))  # Minimum 10% of original profit
            
            return {
                'factor': decay_factor,
                'age_seconds': age_seconds,
                'decay_rate': decay_rate,
                'original_profit': opportunity.get('estimated_profit_usd', 0),
                'adjusted_profit': opportunity.get('estimated_profit_usd', 0) * decay_factor
            }
            
        except Exception as e:
            logger.error(f"Error calculating profit decay: {e}")
            return {'factor': 0.5, 'age_seconds': 0, 'decay_rate': 0, 'original_profit': 0, 'adjusted_profit': 0}
    
    def _analyze_execution_speed(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze expected execution speed for this opportunity."""
        try:
            buy_dex = opportunity.get('buy_dex', '').lower()
            sell_dex = opportunity.get('sell_dex', '').lower()
            
            # Get DEX speed profiles
            buy_profile = self.dex_speed_profiles.get(buy_dex, {'avg_time': 8.0, 'reliability': 0.5})
            sell_profile = self.dex_speed_profiles.get(sell_dex, {'avg_time': 8.0, 'reliability': 0.5})
            
            # Estimate total execution time (sequential execution)
            estimated_time = buy_profile['avg_time'] + sell_profile['avg_time'] + 2.0  # +2s for coordination
            
            # Calculate speed score (0-1, higher is better)
            max_acceptable_time = 20.0
            speed_score = max(0.0, 1.0 - (estimated_time / max_acceptable_time))
            
            # Adjust for DEX reliability
            reliability_factor = (buy_profile['reliability'] + sell_profile['reliability']) / 2
            speed_score *= reliability_factor
            
            return {
                'estimated_time': estimated_time,
                'speed_score': speed_score,
                'buy_dex_time': buy_profile['avg_time'],
                'sell_dex_time': sell_profile['avg_time'],
                'reliability_factor': reliability_factor
            }
            
        except Exception as e:
            logger.error(f"Error analyzing execution speed: {e}")
            return {'estimated_time': 15.0, 'speed_score': 0.3, 'buy_dex_time': 7.5, 'sell_dex_time': 7.5, 'reliability_factor': 0.6}
    
    def _check_market_volatility(self, opportunity: Dict[str, Any]) -> float:
        """Check if market volatility is optimal for execution."""
        try:
            # Get market volatility (if available)
            volatility = opportunity.get('market_volatility', 0.05)  # Default 5%
            
            # Score based on optimal volatility range
            min_vol, max_vol = self.optimal_volatility_range
            
            if min_vol <= volatility <= max_vol:
                # Optimal range - high score
                return 1.0
            elif volatility < min_vol:
                # Too low volatility - fewer opportunities
                return 0.6
            else:
                # Too high volatility - opportunities disappear quickly
                decay_factor = max(0.2, 1.0 - ((volatility - max_vol) * 5))
                return decay_factor
                
        except Exception as e:
            logger.error(f"Error checking market volatility: {e}")
            return 0.5
    
    def _calculate_priority_score(self, opportunity: Dict[str, Any], profit_decay: Dict[str, Any], 
                                speed_analysis: Dict[str, Any], volatility_score: float) -> float:
        """Calculate overall priority score for the opportunity."""
        try:
            # Weighted scoring system
            weights = {
                'profit': 0.4,      # 40% - Adjusted profit after decay
                'speed': 0.3,       # 30% - Execution speed
                'volatility': 0.2,  # 20% - Market conditions
                'freshness': 0.1    # 10% - Opportunity freshness
            }
            
            # Profit score (0-1)
            max_profit = 50.0  # $50 max for scoring
            profit_score = min(1.0, profit_decay['adjusted_profit'] / max_profit)
            
            # Speed score (already 0-1)
            speed_score = speed_analysis['speed_score']
            
            # Volatility score (already 0-1)
            vol_score = volatility_score
            
            # Freshness score (based on age)
            age_seconds = profit_decay.get('age_seconds', 0)
            freshness_score = max(0.0, 1.0 - (age_seconds / self.max_opportunity_age_seconds))
            
            # Calculate weighted score
            priority_score = (
                weights['profit'] * profit_score +
                weights['speed'] * speed_score +
                weights['volatility'] * vol_score +
                weights['freshness'] * freshness_score
            )
            
            return priority_score
            
        except Exception as e:
            logger.error(f"Error calculating priority score: {e}")
            return 0.0
    
    def get_filter_stats(self) -> Dict[str, Any]:
        """Get filtering statistics."""
        return {
            'seen_opportunities_count': len(self.seen_opportunities),
            'execution_history_count': len(self.execution_history),
            'config': self.config,
            'dex_speed_profiles': self.dex_speed_profiles
        }
    
    def update_dex_performance(self, dex: str, execution_time: float, success: bool):
        """Update DEX performance metrics based on actual execution."""
        try:
            if dex.lower() in self.dex_speed_profiles:
                profile = self.dex_speed_profiles[dex.lower()]
                
                # Update average time (exponential moving average)
                alpha = 0.2  # Learning rate
                profile['avg_time'] = (1 - alpha) * profile['avg_time'] + alpha * execution_time
                
                # Update reliability
                if success:
                    profile['reliability'] = min(0.99, profile['reliability'] + 0.01)
                else:
                    profile['reliability'] = max(0.1, profile['reliability'] - 0.05)
                
                logger.info(f"Updated {dex} performance: {execution_time:.1f}s, reliability: {profile['reliability']:.2f}")
                
        except Exception as e:
            logger.error(f"Error updating DEX performance: {e}")
