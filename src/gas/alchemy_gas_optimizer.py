"""
Alchemy Gas Optimizer
Advanced gas optimization using Alchemy's premium APIs.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import os
import statistics

logger = logging.getLogger(__name__)


class AlchemyGasOptimizer:
    """Advanced gas optimization using Alchemy's premium features."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Alchemy gas optimizer."""
        self.config = config
        
        # Alchemy configuration
        self.alchemy_api_key = os.getenv('ALCHEMY_API_KEY', 'kRXhWVt8YU_8LnGS20145F5uBDFbL_k0')
        self.alchemy_url = f"https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
        
        # Gas tracking
        self.gas_history = []
        self.max_history = 100
        
        # Gas thresholds (in gwei)
        self.gas_thresholds = {
            'ultra_low': 15,    # Perfect for arbitrage
            'low': 25,          # Good for arbitrage
            'medium': 40,       # Marginal for arbitrage
            'high': 60,         # Bad for arbitrage
            'extreme': 100      # Never trade
        }
        
        # Profitability thresholds
        self.min_profit_after_gas = {
            'ultra_low': 0.05,   # $0.05 minimum when gas is ultra low
            'low': 0.25,         # $0.25 minimum when gas is low
            'medium': 1.00,      # $1.00 minimum when gas is medium
            'high': 5.00,        # $5.00 minimum when gas is high
            'extreme': float('inf')  # Never trade
        }
        
        # Session
        self.session = None
        
        logger.info("Alchemy Gas Optimizer initialized")

    async def connect(self) -> bool:
        """Connect to Alchemy gas APIs."""
        try:
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Test gas price API
            current_gas = await self.get_current_gas_price()
            if current_gas:
                logger.info(f"✅ Alchemy Gas APIs connected - Current: {current_gas['standard']:.1f} gwei")
                return True
            else:
                logger.error("Failed to connect to Alchemy gas APIs")
                return False
                
        except Exception as e:
            logger.error(f"Gas optimizer connection failed: {e}")
            return False

    async def get_current_gas_price(self) -> Optional[Dict[str, float]]:
        """Get current gas prices with multiple speed options."""
        try:
            # Get base gas price from Alchemy
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_gasPrice",
                "params": [],
                "id": 1
            }
            
            async with self.session.post(self.alchemy_url, json=payload) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                base_gas_wei = int(data['result'], 16)
                base_gas_gwei = base_gas_wei / 1e9
                
                # Calculate different speed tiers
                gas_prices = {
                    'slow': base_gas_gwei * 0.8,      # 20% below base
                    'standard': base_gas_gwei,         # Base price
                    'fast': base_gas_gwei * 1.2,      # 20% above base
                    'instant': base_gas_gwei * 1.5    # 50% above base
                }
                
                # Store in history
                self._update_gas_history(gas_prices['standard'])
                
                return gas_prices
                
        except Exception as e:
            logger.error(f"Gas price fetch error: {e}")
            return None

    async def get_enhanced_gas_estimates(self) -> Dict[str, Any]:
        """Get enhanced gas estimates using Alchemy's advanced features."""
        try:
            # Get current gas prices
            current_gas = await self.get_current_gas_price()
            if not current_gas:
                return {}
            
            # Get gas price history trend
            trend = self._analyze_gas_trend()
            
            # Get network congestion
            congestion = await self._get_network_congestion()
            
            # Calculate optimal gas prices for arbitrage
            optimal_prices = self._calculate_optimal_gas_prices(current_gas, trend, congestion)
            
            return {
                'current_prices': current_gas,
                'trend': trend,
                'congestion': congestion,
                'optimal_prices': optimal_prices,
                'recommendations': self._generate_gas_recommendations(current_gas, trend),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Enhanced gas estimates error: {e}")
            return {}

    async def _get_network_congestion(self) -> Dict[str, Any]:
        """Get network congestion metrics."""
        try:
            # Get pending transaction count
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_getBlockByNumber",
                "params": ["pending", False],
                "id": 1
            }
            
            async with self.session.post(self.alchemy_url, json=payload) as response:
                if response.status != 200:
                    return {'level': 'unknown'}
                
                data = await response.json()
                pending_block = data.get('result', {})
                
                # Analyze congestion based on pending transactions
                tx_count = len(pending_block.get('transactions', []))
                
                if tx_count < 100:
                    congestion_level = 'low'
                elif tx_count < 300:
                    congestion_level = 'medium'
                else:
                    congestion_level = 'high'
                
                return {
                    'level': congestion_level,
                    'pending_transactions': tx_count,
                    'impact_on_gas': self._congestion_gas_impact(congestion_level)
                }
                
        except Exception as e:
            logger.error(f"Network congestion check error: {e}")
            return {'level': 'unknown'}

    def _congestion_gas_impact(self, congestion_level: str) -> str:
        """Determine gas impact based on congestion."""
        impacts = {
            'low': 'minimal',
            'medium': 'moderate',
            'high': 'significant',
            'unknown': 'uncertain'
        }
        return impacts.get(congestion_level, 'uncertain')

    def _update_gas_history(self, gas_price: float):
        """Update gas price history."""
        self.gas_history.append({
            'price': gas_price,
            'timestamp': datetime.now()
        })
        
        # Keep only recent history
        if len(self.gas_history) > self.max_history:
            self.gas_history = self.gas_history[-self.max_history:]

    def _analyze_gas_trend(self) -> Dict[str, Any]:
        """Analyze gas price trends."""
        if len(self.gas_history) < 5:
            return {'direction': 'unknown', 'confidence': 'low'}
        
        # Get recent prices
        recent_prices = [entry['price'] for entry in self.gas_history[-10:]]
        
        # Calculate trend
        if len(recent_prices) >= 3:
            # Simple trend analysis
            first_half = statistics.mean(recent_prices[:len(recent_prices)//2])
            second_half = statistics.mean(recent_prices[len(recent_prices)//2:])
            
            change_pct = (second_half - first_half) / first_half * 100
            
            if change_pct > 5:
                direction = 'rising'
            elif change_pct < -5:
                direction = 'falling'
            else:
                direction = 'stable'
            
            confidence = 'high' if abs(change_pct) > 10 else 'medium'
            
            return {
                'direction': direction,
                'change_percentage': change_pct,
                'confidence': confidence,
                'recent_average': statistics.mean(recent_prices)
            }
        
        return {'direction': 'unknown', 'confidence': 'low'}

    def _calculate_optimal_gas_prices(self, current_gas: Dict[str, float], trend: Dict[str, Any], congestion: Dict[str, Any]) -> Dict[str, float]:
        """Calculate optimal gas prices for arbitrage."""
        base_price = current_gas['standard']
        
        # Adjust based on trend
        if trend['direction'] == 'rising':
            # Gas is rising, be more aggressive
            multiplier = 1.1
        elif trend['direction'] == 'falling':
            # Gas is falling, be more conservative
            multiplier = 0.9
        else:
            # Stable gas, use standard pricing
            multiplier = 1.0
        
        # Adjust based on congestion
        if congestion['level'] == 'high':
            multiplier *= 1.2
        elif congestion['level'] == 'low':
            multiplier *= 0.8
        
        return {
            'conservative': base_price * multiplier * 0.8,
            'optimal': base_price * multiplier,
            'aggressive': base_price * multiplier * 1.3
        }

    def _generate_gas_recommendations(self, current_gas: Dict[str, float], trend: Dict[str, Any]) -> List[str]:
        """Generate gas optimization recommendations."""
        recommendations = []
        current_standard = current_gas['standard']
        
        # Gas level recommendations
        if current_standard <= self.gas_thresholds['ultra_low']:
            recommendations.append("🟢 EXCELLENT gas prices - Execute all profitable trades")
        elif current_standard <= self.gas_thresholds['low']:
            recommendations.append("🟡 GOOD gas prices - Execute trades with >$0.25 profit")
        elif current_standard <= self.gas_thresholds['medium']:
            recommendations.append("🟠 MEDIUM gas prices - Execute only high-profit trades")
        elif current_standard <= self.gas_thresholds['high']:
            recommendations.append("🔴 HIGH gas prices - Execute only exceptional trades")
        else:
            recommendations.append("⛔ EXTREME gas prices - Avoid trading")
        
        # Trend recommendations
        if trend['direction'] == 'falling':
            recommendations.append("📉 Gas prices falling - Consider waiting for better rates")
        elif trend['direction'] == 'rising':
            recommendations.append("📈 Gas prices rising - Execute trades quickly")
        
        return recommendations

    async def should_execute_trade(self, estimated_profit_usd: float, trade_type: str = 'arbitrage') -> Dict[str, Any]:
        """Determine if a trade should be executed based on gas costs."""
        try:
            # Get current gas estimates
            gas_estimates = await self.get_enhanced_gas_estimates()
            if not gas_estimates:
                return {'should_execute': False, 'reason': 'Gas data unavailable'}
            
            current_gas = gas_estimates['current_prices']['standard']
            
            # Estimate gas cost for trade
            gas_cost_usd = await self._estimate_trade_gas_cost(trade_type, current_gas)
            
            # Calculate net profit
            net_profit = estimated_profit_usd - gas_cost_usd
            
            # Determine gas category
            gas_category = self._categorize_gas_price(current_gas)
            
            # Check if profitable
            min_profit_required = self.min_profit_after_gas[gas_category]
            should_execute = net_profit >= min_profit_required
            
            return {
                'should_execute': should_execute,
                'estimated_profit_usd': estimated_profit_usd,
                'estimated_gas_cost_usd': gas_cost_usd,
                'net_profit_usd': net_profit,
                'current_gas_gwei': current_gas,
                'gas_category': gas_category,
                'min_profit_required': min_profit_required,
                'recommendations': gas_estimates.get('recommendations', []),
                'optimal_gas_price': gas_estimates.get('optimal_prices', {}).get('optimal', current_gas)
            }
            
        except Exception as e:
            logger.error(f"Trade execution analysis error: {e}")
            return {'should_execute': False, 'reason': f'Analysis error: {e}'}

    async def _estimate_trade_gas_cost(self, trade_type: str, gas_price_gwei: float) -> float:
        """Estimate gas cost for different trade types."""
        # Gas usage estimates (in gas units)
        gas_usage = {
            'arbitrage': 150000,        # Simple arbitrage
            'cross_chain': 200000,      # Cross-chain arbitrage
            'flash_loan': 300000,       # Flash loan arbitrage
            'complex': 400000           # Complex multi-step arbitrage
        }
        
        gas_units = gas_usage.get(trade_type, 150000)
        gas_price_wei = gas_price_gwei * 1e9
        gas_cost_wei = gas_units * gas_price_wei
        gas_cost_eth = gas_cost_wei / 1e18
        
        # Convert to USD (assuming ETH price)
        eth_price_usd = 2500  # This should come from price feeds
        gas_cost_usd = gas_cost_eth * eth_price_usd
        
        return gas_cost_usd

    def _categorize_gas_price(self, gas_price_gwei: float) -> str:
        """Categorize gas price level."""
        for category, threshold in self.gas_thresholds.items():
            if gas_price_gwei <= threshold:
                return category
        return 'extreme'

    async def get_gas_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive gas optimization report."""
        try:
            gas_estimates = await self.get_enhanced_gas_estimates()
            
            if not gas_estimates:
                return {'error': 'Gas data unavailable'}
            
            current_gas = gas_estimates['current_prices']['standard']
            gas_category = self._categorize_gas_price(current_gas)
            
            # Calculate trading windows
            trading_windows = self._calculate_trading_windows(gas_estimates)
            
            return {
                'current_status': {
                    'gas_price_gwei': current_gas,
                    'category': gas_category,
                    'trend': gas_estimates.get('trend', {}),
                    'congestion': gas_estimates.get('congestion', {})
                },
                'trading_recommendations': gas_estimates.get('recommendations', []),
                'optimal_prices': gas_estimates.get('optimal_prices', {}),
                'trading_windows': trading_windows,
                'profitability_thresholds': {
                    category: threshold for category, threshold in self.min_profit_after_gas.items()
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Gas optimization report error: {e}")
            return {'error': str(e)}

    def _calculate_trading_windows(self, gas_estimates: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal trading windows based on gas patterns."""
        current_gas = gas_estimates['current_prices']['standard']
        trend = gas_estimates.get('trend', {})
        
        windows = {
            'immediate': {
                'recommended': current_gas <= self.gas_thresholds['low'],
                'reason': f"Current gas: {current_gas:.1f} gwei"
            },
            'short_term': {
                'recommended': trend.get('direction') == 'falling',
                'reason': f"Gas trend: {trend.get('direction', 'unknown')}"
            },
            'avoid_trading': {
                'active': current_gas > self.gas_thresholds['high'],
                'reason': f"Gas too high: {current_gas:.1f} gwei"
            }
        }
        
        return windows

    async def disconnect(self):
        """Disconnect from gas optimization APIs."""
        try:
            if self.session:
                await self.session.close()
            logger.info("✅ Gas optimizer disconnected")
        except Exception as e:
            logger.error(f"Disconnect error: {e}")

    def get_gas_stats(self) -> Dict[str, Any]:
        """Get gas price statistics."""
        if not self.gas_history:
            return {'error': 'No gas history available'}
        
        recent_prices = [entry['price'] for entry in self.gas_history[-20:]]
        
        return {
            'current_price': recent_prices[-1] if recent_prices else 0,
            'average_price': statistics.mean(recent_prices),
            'min_price': min(recent_prices),
            'max_price': max(recent_prices),
            'price_volatility': statistics.stdev(recent_prices) if len(recent_prices) > 1 else 0,
            'samples': len(recent_prices),
            'time_range_minutes': (datetime.now() - self.gas_history[0]['timestamp']).total_seconds() / 60 if self.gas_history else 0
        }
