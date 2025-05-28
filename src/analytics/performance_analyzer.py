"""
Performance Analyzer with MCP Integration

This module provides comprehensive performance tracking and analytics with:
- Real-time profit/loss tracking
- Strategy effectiveness analysis
- Market condition correlation
- Predictive performance modeling
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass
import statistics
import json

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for arbitrage operations."""
    total_trades: int
    successful_trades: int
    failed_trades: int
    total_profit: Decimal
    total_loss: Decimal
    net_profit: Decimal
    success_rate: float
    average_profit_per_trade: Decimal
    average_gas_cost: Decimal
    roi: float
    sharpe_ratio: float
    max_drawdown: Decimal


@dataclass
class TradeAnalysis:
    """Analysis of individual trade performance."""
    trade_id: str
    timestamp: datetime
    token_pair: str
    dex_pair: str
    profit_percentage: float
    profit_usd: Decimal
    gas_cost: Decimal
    execution_time: float
    market_conditions: Dict[str, Any]
    success: bool
    failure_reason: Optional[str] = None


class PerformanceAnalyzer:
    """Advanced performance analyzer with MCP memory integration."""

    def __init__(self, mcp_client_manager, config: Dict[str, Any]):
        """Initialize performance analyzer.
        
        Args:
            mcp_client_manager: MCP client manager for data storage
            config: Configuration dictionary
        """
        self.mcp_client = mcp_client_manager
        self.config = config
        
        # Performance tracking
        self.trade_history: List[TradeAnalysis] = []
        self.performance_cache: Dict[str, Any] = {}
        
        # Configuration
        self.max_trade_history = config.get('max_trade_history', 10000)
        self.analysis_window_days = config.get('analysis_window_days', 30)
        self.cache_ttl = config.get('cache_ttl', 300)  # 5 minutes
        
        # Performance metrics
        self.current_metrics = PerformanceMetrics(
            total_trades=0,
            successful_trades=0,
            failed_trades=0,
            total_profit=Decimal('0'),
            total_loss=Decimal('0'),
            net_profit=Decimal('0'),
            success_rate=0.0,
            average_profit_per_trade=Decimal('0'),
            average_gas_cost=Decimal('0'),
            roi=0.0,
            sharpe_ratio=0.0,
            max_drawdown=Decimal('0')
        )

    async def record_trade_execution(
        self, 
        opportunity: Dict[str, Any], 
        execution_result: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> None:
        """Record a trade execution for performance analysis.
        
        Args:
            opportunity: Original arbitrage opportunity
            execution_result: Result of trade execution
            market_conditions: Market conditions at time of trade
        """
        try:
            # Create trade analysis
            trade = TradeAnalysis(
                trade_id=execution_result.get('trade_id', f"trade_{datetime.now().timestamp()}"),
                timestamp=datetime.now(),
                token_pair=f"{opportunity.get('base_token', 'UNKNOWN')}/{opportunity.get('quote_token', 'UNKNOWN')}",
                dex_pair=f"{opportunity.get('buy_dex', 'unknown')}-{opportunity.get('sell_dex', 'unknown')}",
                profit_percentage=opportunity.get('profit_percentage', 0.0),
                profit_usd=Decimal(str(execution_result.get('profit_usd', 0.0))),
                gas_cost=Decimal(str(execution_result.get('gas_cost', 0.0))),
                execution_time=execution_result.get('execution_time', 0.0),
                market_conditions=market_conditions,
                success=execution_result.get('success', False),
                failure_reason=execution_result.get('error') if not execution_result.get('success') else None
            )
            
            # Add to history
            self.trade_history.append(trade)
            if len(self.trade_history) > self.max_trade_history:
                self.trade_history = self.trade_history[-self.max_trade_history:]
            
            # Update metrics
            await self._update_performance_metrics()
            
            # Store in MCP memory
            await self._store_trade_analysis(trade)
            
            logger.info(f"Recorded trade execution: {trade.trade_id}")
            
        except Exception as e:
            logger.error(f"Error recording trade execution: {e}")

    async def _update_performance_metrics(self) -> None:
        """Update current performance metrics."""
        try:
            if not self.trade_history:
                return
            
            # Basic counts
            total_trades = len(self.trade_history)
            successful_trades = sum(1 for t in self.trade_history if t.success)
            failed_trades = total_trades - successful_trades
            
            # Profit calculations
            total_profit = sum(t.profit_usd for t in self.trade_history if t.success)
            total_loss = sum(abs(t.profit_usd) for t in self.trade_history if not t.success and t.profit_usd < 0)
            net_profit = total_profit - total_loss
            
            # Success rate
            success_rate = successful_trades / total_trades if total_trades > 0 else 0.0
            
            # Average metrics
            avg_profit = total_profit / successful_trades if successful_trades > 0 else Decimal('0')
            avg_gas = sum(t.gas_cost for t in self.trade_history) / total_trades if total_trades > 0 else Decimal('0')
            
            # ROI calculation
            total_investment = sum(t.gas_cost for t in self.trade_history)
            roi = float(net_profit / total_investment * 100) if total_investment > 0 else 0.0
            
            # Sharpe ratio (simplified)
            if successful_trades > 1:
                profits = [float(t.profit_usd) for t in self.trade_history if t.success]
                avg_return = statistics.mean(profits)
                std_return = statistics.stdev(profits)
                sharpe_ratio = avg_return / std_return if std_return > 0 else 0.0
            else:
                sharpe_ratio = 0.0
            
            # Max drawdown
            running_profit = Decimal('0')
            peak_profit = Decimal('0')
            max_drawdown = Decimal('0')
            
            for trade in self.trade_history:
                running_profit += trade.profit_usd
                if running_profit > peak_profit:
                    peak_profit = running_profit
                
                drawdown = peak_profit - running_profit
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # Update metrics
            self.current_metrics = PerformanceMetrics(
                total_trades=total_trades,
                successful_trades=successful_trades,
                failed_trades=failed_trades,
                total_profit=total_profit,
                total_loss=total_loss,
                net_profit=net_profit,
                success_rate=success_rate,
                average_profit_per_trade=avg_profit,
                average_gas_cost=avg_gas,
                roi=roi,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown
            )
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")

    async def _store_trade_analysis(self, trade: TradeAnalysis) -> None:
        """Store trade analysis in MCP memory."""
        try:
            if not self.mcp_client or not self.mcp_client.connected:
                return
            
            # Create memory content
            content = f"Trade Analysis: {trade.token_pair} on {trade.dex_pair}. "
            content += f"{'Success' if trade.success else 'Failed'} - "
            content += f"Profit: ${trade.profit_usd:.4f}, Gas: ${trade.gas_cost:.4f}, "
            content += f"Execution: {trade.execution_time:.2f}s"
            
            if trade.failure_reason:
                content += f", Reason: {trade.failure_reason}"
            
            metadata = {
                'tags': f"trade_analysis,{trade.token_pair.replace('/', '_')},{trade.dex_pair},{'success' if trade.success else 'failed'}",
                'type': 'trade_performance'
            }
            
            # Store in memory service
            await self.mcp_client._call_mcp_tool('memory_service', 'store_memory', {
                'content': content,
                'metadata': metadata
            })
            
            # Store in knowledge graph
            entities = [
                {
                    'name': trade.token_pair,
                    'entityType': 'TradingPair',
                    'observations': [f"Trade executed with {trade.profit_percentage:.3f}% profit"]
                },
                {
                    'name': trade.dex_pair,
                    'entityType': 'DEXPair',
                    'observations': [f"Trade {'successful' if trade.success else 'failed'} with ${trade.profit_usd:.4f} profit"]
                }
            ]
            
            relations = [
                {
                    'from': trade.token_pair,
                    'to': trade.dex_pair,
                    'relationType': 'executed_on'
                }
            ]
            
            await self.mcp_client._call_mcp_tool('knowledge_graph', 'create_entities', {'entities': entities})
            await self.mcp_client._call_mcp_tool('knowledge_graph', 'create_relations', {'relations': relations})
            
            logger.debug(f"Stored trade analysis in memory: {trade.trade_id}")
            
        except Exception as e:
            logger.error(f"Error storing trade analysis: {e}")

    async def get_performance_report(self, days: Optional[int] = None) -> Dict[str, Any]:
        """Generate comprehensive performance report.
        
        Args:
            days: Number of days to analyze (default: all data)
            
        Returns:
            Dict with performance report
        """
        try:
            # Filter trades by date if specified
            if days:
                cutoff_date = datetime.now() - timedelta(days=days)
                filtered_trades = [t for t in self.trade_history if t.timestamp >= cutoff_date]
            else:
                filtered_trades = self.trade_history
            
            if not filtered_trades:
                return {'error': 'No trades found for the specified period'}
            
            # Calculate metrics for filtered trades
            metrics = await self._calculate_metrics_for_trades(filtered_trades)
            
            # Strategy analysis
            strategy_analysis = await self._analyze_strategy_effectiveness(filtered_trades)
            
            # Market correlation
            market_correlation = await self._analyze_market_correlation(filtered_trades)
            
            # Performance trends
            trends = await self._analyze_performance_trends(filtered_trades)
            
            # Recommendations
            recommendations = await self._generate_performance_recommendations(metrics, strategy_analysis)
            
            report = {
                'period': f"Last {days} days" if days else "All time",
                'metrics': metrics,
                'strategy_analysis': strategy_analysis,
                'market_correlation': market_correlation,
                'trends': trends,
                'recommendations': recommendations,
                'generated_at': datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {'error': str(e)}

    async def _calculate_metrics_for_trades(self, trades: List[TradeAnalysis]) -> Dict[str, Any]:
        """Calculate performance metrics for a set of trades."""
        if not trades:
            return {}
        
        successful_trades = [t for t in trades if t.success]
        failed_trades = [t for t in trades if not t.success]
        
        total_profit = sum(t.profit_usd for t in successful_trades)
        total_loss = sum(abs(t.profit_usd) for t in failed_trades if t.profit_usd < 0)
        
        return {
            'total_trades': len(trades),
            'successful_trades': len(successful_trades),
            'failed_trades': len(failed_trades),
            'success_rate': len(successful_trades) / len(trades) * 100,
            'total_profit_usd': float(total_profit),
            'total_loss_usd': float(total_loss),
            'net_profit_usd': float(total_profit - total_loss),
            'average_profit_per_trade': float(total_profit / len(successful_trades)) if successful_trades else 0.0,
            'average_gas_cost': float(sum(t.gas_cost for t in trades) / len(trades)),
            'average_execution_time': sum(t.execution_time for t in trades) / len(trades)
        }

    async def _analyze_strategy_effectiveness(self, trades: List[TradeAnalysis]) -> Dict[str, Any]:
        """Analyze effectiveness of different strategies."""
        try:
            # Group by token pairs
            token_pair_performance = {}
            for trade in trades:
                pair = trade.token_pair
                if pair not in token_pair_performance:
                    token_pair_performance[pair] = {'trades': [], 'profit': Decimal('0'), 'success_count': 0}
                
                token_pair_performance[pair]['trades'].append(trade)
                token_pair_performance[pair]['profit'] += trade.profit_usd
                if trade.success:
                    token_pair_performance[pair]['success_count'] += 1
            
            # Group by DEX pairs
            dex_pair_performance = {}
            for trade in trades:
                pair = trade.dex_pair
                if pair not in dex_pair_performance:
                    dex_pair_performance[pair] = {'trades': [], 'profit': Decimal('0'), 'success_count': 0}
                
                dex_pair_performance[pair]['trades'].append(trade)
                dex_pair_performance[pair]['profit'] += trade.profit_usd
                if trade.success:
                    dex_pair_performance[pair]['success_count'] += 1
            
            # Find best performing strategies
            best_token_pairs = sorted(
                token_pair_performance.items(),
                key=lambda x: x[1]['profit'],
                reverse=True
            )[:5]
            
            best_dex_pairs = sorted(
                dex_pair_performance.items(),
                key=lambda x: x[1]['profit'],
                reverse=True
            )[:5]
            
            return {
                'best_token_pairs': [
                    {
                        'pair': pair,
                        'total_profit': float(data['profit']),
                        'trade_count': len(data['trades']),
                        'success_rate': data['success_count'] / len(data['trades']) * 100
                    }
                    for pair, data in best_token_pairs
                ],
                'best_dex_pairs': [
                    {
                        'pair': pair,
                        'total_profit': float(data['profit']),
                        'trade_count': len(data['trades']),
                        'success_rate': data['success_count'] / len(data['trades']) * 100
                    }
                    for pair, data in best_dex_pairs
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing strategy effectiveness: {e}")
            return {}

    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        return self.current_metrics

    async def get_trade_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get trade history.
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            List of trade data
        """
        trades = self.trade_history[-limit:] if limit else self.trade_history
        
        return [
            {
                'trade_id': trade.trade_id,
                'timestamp': trade.timestamp.isoformat(),
                'token_pair': trade.token_pair,
                'dex_pair': trade.dex_pair,
                'profit_percentage': trade.profit_percentage,
                'profit_usd': float(trade.profit_usd),
                'gas_cost': float(trade.gas_cost),
                'execution_time': trade.execution_time,
                'success': trade.success,
                'failure_reason': trade.failure_reason
            }
            for trade in trades
        ]

    async def _analyze_market_correlation(self, trades: List[TradeAnalysis]) -> Dict[str, Any]:
        """Analyze correlation between market conditions and performance."""
        try:
            if not trades:
                return {}

            # Analyze performance by market conditions
            volatility_performance = {'high': [], 'medium': [], 'low': []}
            volume_performance = {'high': [], 'medium': [], 'low': []}

            for trade in trades:
                market_conditions = trade.market_conditions

                # Categorize volatility (mock categorization)
                volatility = market_conditions.get('volatility', 0.5)
                if volatility > 0.7:
                    volatility_performance['high'].append(trade)
                elif volatility > 0.4:
                    volatility_performance['medium'].append(trade)
                else:
                    volatility_performance['low'].append(trade)

                # Categorize volume (mock categorization)
                volume = market_conditions.get('volume', 0.5)
                if volume > 0.7:
                    volume_performance['high'].append(trade)
                elif volume > 0.4:
                    volume_performance['medium'].append(trade)
                else:
                    volume_performance['low'].append(trade)

            # Calculate success rates for each category
            volatility_analysis = {}
            for level, level_trades in volatility_performance.items():
                if level_trades:
                    successful = sum(1 for t in level_trades if t.success)
                    volatility_analysis[level] = {
                        'trade_count': len(level_trades),
                        'success_rate': successful / len(level_trades) * 100,
                        'avg_profit': float(sum(t.profit_usd for t in level_trades if t.success) / max(successful, 1))
                    }

            volume_analysis = {}
            for level, level_trades in volume_performance.items():
                if level_trades:
                    successful = sum(1 for t in level_trades if t.success)
                    volume_analysis[level] = {
                        'trade_count': len(level_trades),
                        'success_rate': successful / len(level_trades) * 100,
                        'avg_profit': float(sum(t.profit_usd for t in level_trades if t.success) / max(successful, 1))
                    }

            return {
                'volatility_correlation': volatility_analysis,
                'volume_correlation': volume_analysis
            }

        except Exception as e:
            logger.error(f"Error analyzing market correlation: {e}")
            return {}

    async def _analyze_performance_trends(self, trades: List[TradeAnalysis]) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        try:
            if len(trades) < 10:
                return {'message': 'Insufficient data for trend analysis'}

            # Sort trades by timestamp
            sorted_trades = sorted(trades, key=lambda x: x.timestamp)

            # Calculate rolling metrics
            window_size = min(10, len(sorted_trades) // 3)
            rolling_success_rates = []
            rolling_profits = []

            for i in range(window_size, len(sorted_trades)):
                window_trades = sorted_trades[i-window_size:i]
                successful = sum(1 for t in window_trades if t.success)
                success_rate = successful / len(window_trades) * 100
                avg_profit = float(sum(t.profit_usd for t in window_trades if t.success) / max(successful, 1))

                rolling_success_rates.append(success_rate)
                rolling_profits.append(avg_profit)

            # Calculate trends
            if len(rolling_success_rates) > 1:
                success_trend = 'improving' if rolling_success_rates[-1] > rolling_success_rates[0] else 'declining'
                profit_trend = 'improving' if rolling_profits[-1] > rolling_profits[0] else 'declining'
            else:
                success_trend = 'stable'
                profit_trend = 'stable'

            return {
                'success_rate_trend': success_trend,
                'profit_trend': profit_trend,
                'recent_success_rate': rolling_success_rates[-1] if rolling_success_rates else 0,
                'recent_avg_profit': rolling_profits[-1] if rolling_profits else 0,
                'trend_data_points': len(rolling_success_rates)
            }

        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
            return {}

    async def _generate_performance_recommendations(
        self,
        metrics: Dict[str, Any],
        strategy_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        try:
            # Success rate recommendations
            success_rate = metrics.get('success_rate', 0)
            if success_rate < 50:
                recommendations.append("Low success rate detected. Consider tightening opportunity filters or improving execution speed.")
            elif success_rate > 80:
                recommendations.append("High success rate achieved. Consider expanding to more aggressive opportunities.")

            # Profit recommendations
            avg_profit = metrics.get('average_profit_per_trade', 0)
            if avg_profit < 5:
                recommendations.append("Low average profit per trade. Consider focusing on higher-profit opportunities or reducing gas costs.")

            # Gas cost recommendations
            avg_gas = metrics.get('average_gas_cost', 0)
            if avg_gas > 20:
                recommendations.append("High gas costs detected. Consider optimizing for L2 networks or batching transactions.")

            # Strategy recommendations
            best_pairs = strategy_analysis.get('best_token_pairs', [])
            if best_pairs:
                top_pair = best_pairs[0]['pair']
                recommendations.append(f"Focus on {top_pair} - highest performing token pair with {best_pairs[0]['total_profit']:.2f} total profit.")

            best_dex_pairs = strategy_analysis.get('best_dex_pairs', [])
            if best_dex_pairs:
                top_dex_pair = best_dex_pairs[0]['pair']
                recommendations.append(f"Prioritize {top_dex_pair} DEX pair - best performance with {best_dex_pairs[0]['success_rate']:.1f}% success rate.")

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Error generating recommendations"]

    async def predict_opportunity_success(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Predict success probability for an opportunity based on historical data.

        Args:
            opportunity: Arbitrage opportunity to analyze

        Returns:
            Dict with prediction results
        """
        try:
            if not self.mcp_client or not self.mcp_client.connected:
                return {'prediction': 'unavailable', 'reason': 'MCP not connected'}

            # Query similar historical trades
            base_token = opportunity.get('base_token', '')
            quote_token = opportunity.get('quote_token', '')
            buy_dex = opportunity.get('buy_dex', '')
            sell_dex = opportunity.get('sell_dex', '')

            query = f"trade analysis {base_token} {quote_token} {buy_dex} {sell_dex}"
            similar_trades = await self.mcp_client._call_mcp_tool(
                'memory_service', 'retrieve_memory', {
                    'query': query,
                    'n_results': 20
                }
            )

            # Analyze historical performance
            memories = similar_trades.get('memories', []) if isinstance(similar_trades, dict) else []

            if not memories:
                return {
                    'prediction': 'unknown',
                    'confidence': 0.5,
                    'reason': 'No historical data available'
                }

            # Simple success prediction based on historical data
            success_count = sum(1 for m in memories if 'success' in str(m).lower())
            total_count = len(memories)
            success_probability = success_count / total_count if total_count > 0 else 0.5

            # Adjust based on current opportunity characteristics
            profit_percentage = opportunity.get('profit_percentage', 0)
            if profit_percentage > 1.0:  # High profit opportunities are riskier
                success_probability *= 0.9
            elif profit_percentage > 0.5:
                success_probability *= 0.95

            # Confidence based on data quantity
            confidence = min(total_count / 10, 1.0)  # Max confidence with 10+ data points

            prediction_level = 'high' if success_probability > 0.7 else 'medium' if success_probability > 0.4 else 'low'

            return {
                'prediction': prediction_level,
                'success_probability': success_probability,
                'confidence': confidence,
                'historical_trades_analyzed': total_count,
                'recommendation': self._get_prediction_recommendation(success_probability, confidence)
            }

        except Exception as e:
            logger.error(f"Error predicting opportunity success: {e}")
            return {'prediction': 'error', 'reason': str(e)}

    def _get_prediction_recommendation(self, success_probability: float, confidence: float) -> str:
        """Get recommendation based on prediction."""
        if confidence < 0.3:
            return "Insufficient historical data for reliable prediction"
        elif success_probability > 0.8:
            return "High success probability - recommended for execution"
        elif success_probability > 0.6:
            return "Good success probability - proceed with caution"
        elif success_probability > 0.4:
            return "Moderate success probability - consider risk tolerance"
        else:
            return "Low success probability - not recommended"

    async def export_performance_data(self, format: str = 'json') -> str:
        """Export performance data for external analysis.

        Args:
            format: Export format ('json', 'csv')

        Returns:
            Exported data as string
        """
        try:
            if format == 'json':
                data = {
                    'metrics': {
                        'total_trades': self.current_metrics.total_trades,
                        'successful_trades': self.current_metrics.successful_trades,
                        'success_rate': self.current_metrics.success_rate,
                        'net_profit': float(self.current_metrics.net_profit),
                        'roi': self.current_metrics.roi,
                        'sharpe_ratio': self.current_metrics.sharpe_ratio
                    },
                    'trades': await self.get_trade_history(),
                    'exported_at': datetime.now().isoformat()
                }
                return json.dumps(data, indent=2)

            elif format == 'csv':
                # Simple CSV export
                csv_lines = ['trade_id,timestamp,token_pair,dex_pair,profit_usd,gas_cost,success']
                for trade in self.trade_history:
                    csv_lines.append(
                        f"{trade.trade_id},{trade.timestamp.isoformat()},{trade.token_pair},"
                        f"{trade.dex_pair},{trade.profit_usd},{trade.gas_cost},{trade.success}"
                    )
                return '\n'.join(csv_lines)

            else:
                return f"Unsupported format: {format}"

        except Exception as e:
            logger.error(f"Error exporting performance data: {e}")
            return f"Export error: {e}"
