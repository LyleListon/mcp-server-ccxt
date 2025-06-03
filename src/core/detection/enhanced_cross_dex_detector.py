"""
Enhanced Cross-DEX Detector with MCP Intelligence

This module provides intelligent arbitrage opportunity detection with:
- Multi-source data aggregation
- Pattern recognition and learning
- Predictive opportunity scoring
- Knowledge graph integration
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)


@dataclass
class OpportunityScore:
    """Scoring metrics for an arbitrage opportunity."""
    profit_score: float
    liquidity_score: float
    risk_score: float
    historical_score: float
    overall_score: float
    confidence: float


@dataclass
class EnhancedOpportunity:
    """Enhanced arbitrage opportunity with intelligence."""
    base_token: str
    quote_token: str
    buy_dex: str
    sell_dex: str
    buy_price: Decimal
    sell_price: Decimal
    profit_percentage: float
    profit_usd: float
    liquidity: Dict[str, float]
    gas_estimate: int
    score: OpportunityScore
    market_conditions: Dict[str, Any]
    similar_patterns: List[Dict[str, Any]]
    timestamp: datetime


class EnhancedCrossDexDetector:
    """Enhanced cross-DEX detector with MCP intelligence integration."""

    def __init__(self, mcp_clients, config: Dict[str, Any]):
        """Initialize enhanced detector.
        
        Args:
            mcp_clients: MCP client manager
            config: Configuration dictionary
        """
        self.mcp_clients = mcp_clients
        self.config = config
        
        # Detection parameters
        self.min_profit_threshold = config.get('min_profit_threshold', 0.3)  # 0.3%
        self.max_slippage = config.get('max_slippage', 0.5)  # 0.5%
        self.min_liquidity = config.get('min_liquidity', 10000)  # $10k
        
        # Intelligence parameters
        self.pattern_memory_days = config.get('pattern_memory_days', 30)
        self.min_confidence_score = config.get('min_confidence_score', 0.6)
        
        # Caching
        self.opportunity_cache: Dict[str, EnhancedOpportunity] = {}
        self.cache_ttl = config.get('cache_ttl', 60)  # 1 minute
        
        # Performance tracking
        self.detection_stats = {
            'total_scans': 0,
            'opportunities_found': 0,
            'high_confidence_opportunities': 0,
            'successful_predictions': 0,
            'failed_predictions': 0
        }

    async def detect_opportunities_with_intelligence(
        self, 
        dex_prices: Dict[str, Dict[str, Decimal]],
        market_data: Dict[str, Any]
    ) -> List[EnhancedOpportunity]:
        """Detect arbitrage opportunities with intelligence enhancement.
        
        Args:
            dex_prices: Price data from all DEXs
            market_data: Current market conditions
            
        Returns:
            List of enhanced opportunities with scoring
        """
        self.detection_stats['total_scans'] += 1
        
        try:
            # Basic opportunity detection
            basic_opportunities = await self._detect_basic_opportunities(dex_prices)
            
            if not basic_opportunities:
                return []
            
            # Enhance opportunities with intelligence
            enhanced_opportunities = []
            
            for opportunity in basic_opportunities:
                enhanced = await self._enhance_opportunity_with_intelligence(
                    opportunity, market_data
                )
                
                if enhanced and enhanced.score.overall_score >= self.min_confidence_score:
                    enhanced_opportunities.append(enhanced)
                    
                    if enhanced.score.confidence > 0.8:
                        self.detection_stats['high_confidence_opportunities'] += 1
            
            # Sort by overall score
            enhanced_opportunities.sort(key=lambda x: x.score.overall_score, reverse=True)
            
            # Store patterns for learning
            await self._store_detection_patterns(enhanced_opportunities, market_data)
            
            self.detection_stats['opportunities_found'] += len(enhanced_opportunities)
            
            logger.info(f"Enhanced detection found {len(enhanced_opportunities)} opportunities")
            return enhanced_opportunities
            
        except Exception as e:
            logger.error(f"Error in enhanced opportunity detection: {e}")
            return []

    async def _detect_basic_opportunities(
        self, 
        dex_prices: Dict[str, Dict[str, Decimal]]
    ) -> List[Dict[str, Any]]:
        """Detect basic arbitrage opportunities."""
        opportunities = []
        
        try:
            # Get all trading pairs
            all_pairs = set()
            for dex_data in dex_prices.values():
                all_pairs.update(dex_data.keys())
            
            for pair in all_pairs:
                # Get prices from all DEXs for this pair
                pair_prices = {}
                for dex_name, dex_data in dex_prices.items():
                    if pair in dex_data and dex_data[pair] > 0:
                        pair_prices[dex_name] = dex_data[pair]
                
                if len(pair_prices) < 2:
                    continue
                
                # Find arbitrage opportunities
                dex_names = list(pair_prices.keys())
                for i, buy_dex in enumerate(dex_names):
                    for sell_dex in dex_names[i+1:]:
                        buy_price = pair_prices[buy_dex]
                        sell_price = pair_prices[sell_dex]
                        
                        # Calculate profit in both directions
                        profit_1 = ((sell_price - buy_price) / buy_price) * 100
                        profit_2 = ((buy_price - sell_price) / sell_price) * 100
                        
                        if profit_1 > self.min_profit_threshold:
                            opportunities.append({
                                'pair': pair,
                                'base_token': pair.split('/')[0],
                                'quote_token': pair.split('/')[1],
                                'buy_dex': buy_dex,
                                'sell_dex': sell_dex,
                                'buy_price': buy_price,
                                'sell_price': sell_price,
                                'profit_percentage': profit_1
                            })
                        elif profit_2 > self.min_profit_threshold:
                            opportunities.append({
                                'pair': pair,
                                'base_token': pair.split('/')[0],
                                'quote_token': pair.split('/')[1],
                                'buy_dex': sell_dex,
                                'sell_dex': buy_dex,
                                'buy_price': sell_price,
                                'sell_price': buy_price,
                                'profit_percentage': profit_2
                            })
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error in basic opportunity detection: {e}")
            return []

    async def _enhance_opportunity_with_intelligence(
        self, 
        opportunity: Dict[str, Any], 
        market_data: Dict[str, Any]
    ) -> Optional[EnhancedOpportunity]:
        """Enhance opportunity with intelligence and scoring."""
        try:
            # Get historical patterns
            similar_patterns = await self._get_similar_patterns(opportunity)
            
            # Calculate liquidity data
            liquidity = await self._get_liquidity_data(opportunity)
            
            # Estimate gas costs
            gas_estimate = await self._estimate_gas_costs(opportunity)
            
            # Calculate profit in USD
            profit_usd = await self._calculate_profit_usd(opportunity, market_data)
            
            # Generate opportunity score
            score = await self._calculate_opportunity_score(
                opportunity, liquidity, similar_patterns, market_data
            )
            
            # Create enhanced opportunity
            enhanced = EnhancedOpportunity(
                base_token=opportunity['base_token'],
                quote_token=opportunity['quote_token'],
                buy_dex=opportunity['buy_dex'],
                sell_dex=opportunity['sell_dex'],
                buy_price=opportunity['buy_price'],
                sell_price=opportunity['sell_price'],
                profit_percentage=opportunity['profit_percentage'],
                profit_usd=profit_usd,
                liquidity=liquidity,
                gas_estimate=gas_estimate,
                score=score,
                market_conditions=market_data,
                similar_patterns=similar_patterns,
                timestamp=datetime.now()
            )
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Error enhancing opportunity: {e}")
            return None

    async def _get_similar_patterns(self, opportunity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get similar historical patterns from memory."""
        try:
            if not self.mcp_clients or not self.mcp_clients.connected:
                return []
            
            # Query memory for similar patterns
            query = f"arbitrage {opportunity['base_token']} {opportunity['quote_token']} {opportunity['buy_dex']} {opportunity['sell_dex']}"
            
            patterns = await self.mcp_clients._call_mcp_tool(
                'memory_service', 'retrieve_memory', {
                    'query': query,
                    'n_results': 10
                }
            )
            
            return patterns.get('memories', []) if isinstance(patterns, dict) else []
            
        except Exception as e:
            logger.error(f"Error getting similar patterns: {e}")
            return []

    async def _get_liquidity_data(self, opportunity: Dict[str, Any]) -> Dict[str, float]:
        """Get liquidity data for the opportunity."""
        try:
            # Mock liquidity data - in production, this would query actual DEX liquidity
            base_liquidity = {
                'uniswap_v3': 8000000,
                'sushiswap': 2000000,
                'aerodrome': 1200000,
                'velodrome': 900000,
                'camelot': 500000
            }
            
            buy_liquidity = base_liquidity.get(opportunity['buy_dex'], 100000)
            sell_liquidity = base_liquidity.get(opportunity['sell_dex'], 100000)
            
            return {
                'buy_dex_liquidity': buy_liquidity,
                'sell_dex_liquidity': sell_liquidity,
                'total_liquidity': buy_liquidity + sell_liquidity,
                'min_liquidity': min(buy_liquidity, sell_liquidity)
            }
            
        except Exception as e:
            logger.error(f"Error getting liquidity data: {e}")
            return {'buy_dex_liquidity': 0, 'sell_dex_liquidity': 0, 'total_liquidity': 0, 'min_liquidity': 0}

    async def _estimate_gas_costs(self, opportunity: Dict[str, Any]) -> int:
        """Estimate gas costs for the arbitrage."""
        try:
            # Base gas costs by network
            network_gas = {
                'ethereum': 300000,
                'arbitrum': 200000,
                'optimism': 120000,
                'base': 150000,
                'polygon': 160000,
                'bsc': 250000
            }
            
            # COMPLETE DEX to chain mapping (from config analysis + Gemini verification)
            dex_networks = {
                # Ethereum
                'uniswap_v3': 'ethereum',
                'sushiswap': 'ethereum',

                # Arbitrum (Gemini verified)
                'camelot': 'arbitrum',
                'ramses': 'arbitrum',
                'solidly': 'arbitrum',
                'zyberswap': 'arbitrum',
                'woofi': 'arbitrum',
                'dodo': 'arbitrum',
                'balancer': 'arbitrum',

                # Base (Gemini verified)
                'aerodrome': 'base',
                'baseswap': 'base',
                'meshswap': 'base',
                'dackieswap': 'base',
                'swapfish': 'base',

                # Optimism
                'velodrome': 'optimism'
            }
            
            buy_network = dex_networks.get(opportunity['buy_dex'], 'ethereum')
            sell_network = dex_networks.get(opportunity['sell_dex'], 'ethereum')
            
            # If cross-chain, add bridge costs
            if buy_network != sell_network:
                return network_gas.get(buy_network, 300000) + network_gas.get(sell_network, 300000) + 100000
            else:
                return network_gas.get(buy_network, 300000)
                
        except Exception as e:
            logger.error(f"Error estimating gas costs: {e}")
            return 300000  # Default estimate

    async def _calculate_profit_usd(self, opportunity: Dict[str, Any], market_data: Dict[str, Any]) -> float:
        """Calculate profit in USD."""
        try:
            # Get token price in USD from market data
            base_token = opportunity['base_token']

            # TODO: Get real-time prices from market data APIs
            # Using conservative estimates for now
            token_prices = {
                'ETH': 3000.0,   # Conservative estimate
                'WETH': 3000.0,  # Conservative estimate
                'USDC': 1.0,
                'USDT': 1.0,
                'DAI': 1.0,
                'WBTC': 50000.0  # Conservative estimate
            }

            token_price_usd = token_prices.get(base_token, 1.0)

            # Assume $5000 trade size for calculation
            trade_size_usd = 5000.0
            profit_usd = trade_size_usd * (opportunity['profit_percentage'] / 100)

            return profit_usd

        except Exception as e:
            logger.error(f"Error calculating profit USD: {e}")
            return 0.0

    async def _calculate_opportunity_score(
        self,
        opportunity: Dict[str, Any],
        liquidity: Dict[str, float],
        similar_patterns: List[Dict[str, Any]],
        market_data: Dict[str, Any]
    ) -> OpportunityScore:
        """Calculate comprehensive opportunity score."""
        try:
            # Profit score (0-1)
            profit_score = min(opportunity['profit_percentage'] / 2.0, 1.0)  # Cap at 2%

            # Liquidity score (0-1)
            min_liquidity = liquidity['min_liquidity']
            liquidity_score = min(min_liquidity / 1000000, 1.0)  # Cap at $1M

            # Risk score (0-1, higher is better)
            risk_factors = []

            # Cross-chain risk
            if opportunity['buy_dex'] != opportunity['sell_dex']:
                risk_factors.append(0.8)  # Cross-DEX has some risk
            else:
                risk_factors.append(0.9)  # Same DEX is safer

            # Slippage risk based on liquidity
            if min_liquidity > 500000:
                risk_factors.append(0.9)  # High liquidity, low slippage risk
            elif min_liquidity > 100000:
                risk_factors.append(0.7)  # Medium liquidity
            else:
                risk_factors.append(0.5)  # Low liquidity, high slippage risk

            risk_score = statistics.mean(risk_factors)

            # Historical score based on similar patterns
            historical_score = 0.5  # Default
            if similar_patterns:
                # Analyze success rate of similar patterns
                success_count = sum(1 for p in similar_patterns if 'success' in str(p).lower())
                historical_score = min(success_count / len(similar_patterns), 1.0)

            # Overall score (weighted average)
            weights = {
                'profit': 0.3,
                'liquidity': 0.25,
                'risk': 0.25,
                'historical': 0.2
            }

            overall_score = (
                profit_score * weights['profit'] +
                liquidity_score * weights['liquidity'] +
                risk_score * weights['risk'] +
                historical_score * weights['historical']
            )

            # Confidence based on data quality
            confidence_factors = []
            confidence_factors.append(0.9 if liquidity['total_liquidity'] > 100000 else 0.6)
            confidence_factors.append(0.9 if len(similar_patterns) > 3 else 0.7)
            confidence_factors.append(0.8)  # Base confidence

            confidence = statistics.mean(confidence_factors)

            return OpportunityScore(
                profit_score=profit_score,
                liquidity_score=liquidity_score,
                risk_score=risk_score,
                historical_score=historical_score,
                overall_score=overall_score,
                confidence=confidence
            )

        except Exception as e:
            logger.error(f"Error calculating opportunity score: {e}")
            return OpportunityScore(0.5, 0.5, 0.5, 0.5, 0.5, 0.5)

    async def _store_detection_patterns(
        self,
        opportunities: List[EnhancedOpportunity],
        market_data: Dict[str, Any]
    ) -> None:
        """Store detection patterns for learning."""
        try:
            if not self.mcp_clients or not self.mcp_clients.connected:
                return

            for opportunity in opportunities:
                # Store in memory service
                content = f"Enhanced arbitrage detection: {opportunity.base_token}/{opportunity.quote_token} "
                content += f"between {opportunity.buy_dex} and {opportunity.sell_dex}. "
                content += f"Profit: {opportunity.profit_percentage:.3f}%, Score: {opportunity.score.overall_score:.3f}, "
                content += f"Confidence: {opportunity.score.confidence:.3f}"

                metadata = {
                    'tags': f"enhanced_detection,{opportunity.base_token},{opportunity.quote_token},{opportunity.buy_dex},{opportunity.sell_dex}",
                    'type': 'enhanced_opportunity'
                }

                await self.mcp_clients._call_mcp_tool('memory_service', 'store_memory', {
                    'content': content,
                    'metadata': metadata
                })

                # Store in knowledge graph
                entities = [
                    {
                        'name': opportunity.base_token,
                        'entityType': 'Token',
                        'observations': [f"Enhanced arbitrage opportunity with {opportunity.profit_percentage:.3f}% profit"]
                    },
                    {
                        'name': opportunity.buy_dex,
                        'entityType': 'DEX',
                        'observations': [f"Buy side of arbitrage with score {opportunity.score.overall_score:.3f}"]
                    },
                    {
                        'name': opportunity.sell_dex,
                        'entityType': 'DEX',
                        'observations': [f"Sell side of arbitrage with score {opportunity.score.overall_score:.3f}"]
                    }
                ]

                relations = [
                    {
                        'from': opportunity.base_token,
                        'to': opportunity.quote_token,
                        'relationType': 'enhanced_arbitrage_pair'
                    },
                    {
                        'from': opportunity.buy_dex,
                        'to': opportunity.sell_dex,
                        'relationType': 'price_arbitrage'
                    }
                ]

                await self.mcp_clients._call_mcp_tool('knowledge_graph', 'create_entities', {'entities': entities})
                await self.mcp_clients._call_mcp_tool('knowledge_graph', 'create_relations', {'relations': relations})

            logger.debug(f"Stored {len(opportunities)} enhanced detection patterns")

        except Exception as e:
            logger.error(f"Error storing detection patterns: {e}")

    async def get_market_intelligence(self) -> Dict[str, Any]:
        """Get market intelligence summary."""
        try:
            if not self.mcp_clients or not self.mcp_clients.connected:
                return {'intelligence': 'MCP not connected'}

            # Query recent patterns
            recent_patterns = await self.mcp_clients._call_mcp_tool(
                'memory_service', 'retrieve_memory', {
                    'query': 'enhanced arbitrage detection patterns',
                    'n_results': 50
                }
            )

            # Analyze patterns
            patterns = recent_patterns.get('memories', []) if isinstance(recent_patterns, dict) else []

            intelligence = {
                'total_patterns_analyzed': len(patterns),
                'detection_stats': self.detection_stats,
                'top_tokens': self._analyze_top_tokens(patterns),
                'top_dex_pairs': self._analyze_top_dex_pairs(patterns),
                'average_scores': self._analyze_average_scores(patterns),
                'recommendations': self._generate_recommendations()
            }

            return intelligence

        except Exception as e:
            logger.error(f"Error getting market intelligence: {e}")
            return {'error': str(e)}

    def _analyze_top_tokens(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """Analyze most frequent tokens in patterns."""
        token_counts = {}
        for pattern in patterns:
            content = str(pattern.get('content', ''))
            # Simple token extraction - in production, use more sophisticated parsing
            for token in ['ETH', 'USDC', 'USDT', 'DAI', 'WBTC', 'WETH']:
                if token in content:
                    token_counts[token] = token_counts.get(token, 0) + 1

        return sorted(token_counts.keys(), key=lambda x: token_counts[x], reverse=True)[:5]

    def _analyze_top_dex_pairs(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """Analyze most frequent DEX pairs."""
        dex_pair_counts = {}
        for pattern in patterns:
            content = str(pattern.get('content', ''))
            # Simple DEX pair extraction
            if 'between' in content:
                parts = content.split('between')
                if len(parts) > 1:
                    dex_part = parts[1].split('.')[0].strip()
                    if ' and ' in dex_part:
                        dex_pair = dex_part.replace(' and ', '-')
                        dex_pair_counts[dex_pair] = dex_pair_counts.get(dex_pair, 0) + 1

        return sorted(dex_pair_counts.keys(), key=lambda x: dex_pair_counts[x], reverse=True)[:5]

    def _analyze_average_scores(self, patterns: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze average scores from patterns."""
        scores = []
        confidences = []

        for pattern in patterns:
            content = str(pattern.get('content', ''))
            # Extract scores using simple parsing
            if 'Score:' in content:
                try:
                    score_part = content.split('Score:')[1].split(',')[0].strip()
                    score = float(score_part)
                    scores.append(score)
                except:
                    pass

            if 'Confidence:' in content:
                try:
                    conf_part = content.split('Confidence:')[1].strip()
                    confidence = float(conf_part)
                    confidences.append(confidence)
                except:
                    pass

        return {
            'average_score': statistics.mean(scores) if scores else 0.0,
            'average_confidence': statistics.mean(confidences) if confidences else 0.0,
            'total_scored_opportunities': len(scores)
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on detection stats."""
        recommendations = []

        if self.detection_stats['total_scans'] > 10:
            success_rate = (
                self.detection_stats['opportunities_found'] / self.detection_stats['total_scans']
                if self.detection_stats['total_scans'] > 0 else 0
            )

            if success_rate > 0.1:
                recommendations.append("High opportunity detection rate - consider increasing scan frequency")
            elif success_rate < 0.05:
                recommendations.append("Low opportunity detection rate - consider adjusting thresholds")

            confidence_rate = (
                self.detection_stats['high_confidence_opportunities'] / self.detection_stats['opportunities_found']
                if self.detection_stats['opportunities_found'] > 0 else 0
            )

            if confidence_rate > 0.7:
                recommendations.append("High confidence opportunities detected - good for execution")
            elif confidence_rate < 0.3:
                recommendations.append("Low confidence opportunities - consider improving data sources")

        return recommendations

    def get_detection_stats(self) -> Dict[str, Any]:
        """Get current detection statistics."""
        return self.detection_stats.copy()
