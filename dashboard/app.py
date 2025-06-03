#!/usr/bin/env python3
"""
MayArbi Live Trading Dashboard
Real-time web dashboard for monitoring arbitrage trading performance.
"""

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import json
import os
import time
from datetime import datetime, timedelta
import threading
import logging
from typing import Dict, List, Any
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mayarbi_dashboard_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

class DashboardData:
    """Centralized data store for dashboard metrics."""
    
    def __init__(self):
        self.reset_data()
        
    def reset_data(self):
        """Reset all dashboard data."""
        self.trading_stats = {
            'session_start': datetime.now().isoformat(),
            'total_scans': 0,
            'opportunities_found': 0,
            'opportunities_executed': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_profit_usd': 0.0,
            'total_costs_usd': 0.0,
            'net_profit_usd': 0.0,
            'best_trade_usd': 0.0,
            'worst_trade_usd': 0.0,
            'success_rate': 0.0,
            'avg_profit_per_trade': 0.0,
            'trades_per_hour': 0.0,
            'capital_deployed': 832.0,
            'roi_percentage': 0.0
        }
        
        self.live_metrics = {
            'current_scan': 0,
            'scan_speed_seconds': 5.0,
            'active_trades': 0,
            'gas_price_gwei': 0.0,
            'gas_category': 'unknown',
            'last_opportunity': None,
            'system_status': 'starting',
            'uptime_seconds': 0
        }
        
        self.dex_performance = {}
        self.network_performance = {
            'arbitrum': {'opportunities': 0, 'executed': 0, 'profit': 0.0},
            'base': {'opportunities': 0, 'executed': 0, 'profit': 0.0},
            'optimism': {'opportunities': 0, 'executed': 0, 'profit': 0.0}
        }
        
        self.recent_trades = []
        self.opportunity_history = []
        self.error_log = []
        
        # DEX list from config
        self.dex_list = [
            'uniswap_v3', 'sushiswap', 'paraswap', 'camelot', 'traderjoe',
            'aerodrome', 'velodrome', 'kyberswap', 'curve', 'balancer',
            'zyberswap', 'swapfish', 'woofi', 'chronos', 'pancakeswap',
            'quickswap_polygon', 'spookyswap'
        ]
        
        # Initialize DEX performance tracking
        for dex in self.dex_list:
            self.dex_performance[dex] = {
                'opportunities': 0,
                'executed': 0,
                'profit': 0.0,
                'success_rate': 0.0,
                'avg_profit': 0.0,
                'status': 'unknown'
            }

# Global dashboard data
dashboard_data = DashboardData()

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    """Get current trading statistics."""
    return jsonify({
        'trading_stats': dashboard_data.trading_stats,
        'live_metrics': dashboard_data.live_metrics,
        'network_performance': dashboard_data.network_performance,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/dex-performance')
def get_dex_performance():
    """Get DEX performance data."""
    return jsonify({
        'dex_performance': dashboard_data.dex_performance,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/recent-trades')
def get_recent_trades():
    """Get recent trade history."""
    return jsonify({
        'trades': dashboard_data.recent_trades[-50:],  # Last 50 trades
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/opportunities')
def get_opportunities():
    """Get recent opportunity data."""
    return jsonify({
        'opportunities': dashboard_data.opportunity_history[-100:],  # Last 100 opportunities
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/errors')
def get_errors():
    """Get recent error log."""
    return jsonify({
        'errors': dashboard_data.error_log[-50:],  # Last 50 errors
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info("Dashboard client connected")
    emit('status', {'message': 'Connected to MayArbi Dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info("Dashboard client disconnected")

def update_trading_stats(trade_data: Dict[str, Any]):
    """Update trading statistics with new trade data."""
    stats = dashboard_data.trading_stats
    
    if trade_data.get('success'):
        stats['successful_trades'] += 1
        profit = trade_data.get('net_profit_usd', 0)
        stats['total_profit_usd'] += profit
        stats['net_profit_usd'] = stats['total_profit_usd'] - stats['total_costs_usd']
        
        if profit > stats['best_trade_usd']:
            stats['best_trade_usd'] = profit
    else:
        stats['failed_trades'] += 1
        loss = abs(trade_data.get('net_profit_usd', 0))
        if -loss < stats['worst_trade_usd']:
            stats['worst_trade_usd'] = -loss
    
    # Update costs
    stats['total_costs_usd'] += trade_data.get('costs_usd', 0)
    stats['net_profit_usd'] = stats['total_profit_usd'] - stats['total_costs_usd']
    
    # Calculate derived metrics
    total_trades = stats['successful_trades'] + stats['failed_trades']
    if total_trades > 0:
        stats['success_rate'] = (stats['successful_trades'] / total_trades) * 100
        stats['avg_profit_per_trade'] = stats['total_profit_usd'] / total_trades
    
    # ROI calculation
    if stats['capital_deployed'] > 0:
        stats['roi_percentage'] = (stats['net_profit_usd'] / stats['capital_deployed']) * 100
    
    # Trades per hour
    session_hours = (datetime.now() - datetime.fromisoformat(stats['session_start'])).total_seconds() / 3600
    if session_hours > 0:
        stats['trades_per_hour'] = total_trades / session_hours

def update_opportunity_data(opportunity: Dict[str, Any]):
    """Update opportunity tracking data."""
    dashboard_data.trading_stats['opportunities_found'] += 1
    
    # Add to opportunity history
    opportunity['timestamp'] = datetime.now().isoformat()
    dashboard_data.opportunity_history.append(opportunity)
    
    # Update network performance
    network = opportunity.get('source_chain', 'unknown')
    if network in dashboard_data.network_performance:
        dashboard_data.network_performance[network]['opportunities'] += 1
    
    # Update DEX performance if available
    dex = opportunity.get('dex', 'unknown')
    if dex in dashboard_data.dex_performance:
        dashboard_data.dex_performance[dex]['opportunities'] += 1

def broadcast_update():
    """Broadcast real-time updates to connected clients."""
    socketio.emit('trading_update', {
        'trading_stats': dashboard_data.trading_stats,
        'live_metrics': dashboard_data.live_metrics,
        'network_performance': dashboard_data.network_performance,
        'timestamp': datetime.now().isoformat()
    })

def simulate_data_updates():
    """Simulate trading data updates for testing."""
    import random
    import time
    
    while True:
        try:
            # Simulate scan update
            dashboard_data.live_metrics['current_scan'] += 1
            dashboard_data.trading_stats['total_scans'] += 1
            
            # Simulate gas price
            dashboard_data.live_metrics['gas_price_gwei'] = random.uniform(15, 45)
            
            # Simulate opportunity
            if random.random() < 0.3:  # 30% chance of opportunity
                opportunity = {
                    'token': random.choice(['ETH', 'USDC', 'USDT', 'WBTC']),
                    'source_chain': random.choice(['arbitrum', 'base', 'optimism']),
                    'target_chain': random.choice(['arbitrum', 'base', 'optimism']),
                    'profit_percentage': random.uniform(0.1, 0.5),
                    'dex': random.choice(dashboard_data.dex_list[:5])
                }
                update_opportunity_data(opportunity)
                
                # Simulate trade execution
                if random.random() < 0.7:  # 70% execution rate
                    trade = {
                        'success': random.random() < 0.85,  # 85% success rate
                        'net_profit_usd': random.uniform(-2, 15),
                        'costs_usd': random.uniform(0.5, 3),
                        'execution_time': random.uniform(2, 8)
                    }
                    update_trading_stats(trade)
                    dashboard_data.recent_trades.append({
                        **trade,
                        'timestamp': datetime.now().isoformat(),
                        'opportunity': opportunity
                    })
            
            # Update uptime
            dashboard_data.live_metrics['uptime_seconds'] += 5
            
            # Broadcast update
            broadcast_update()
            
            time.sleep(5)  # Update every 5 seconds
            
        except Exception as e:
            logger.error(f"Data simulation error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    # Start data simulation in background
    data_thread = threading.Thread(target=simulate_data_updates, daemon=True)
    data_thread.start()
    
    logger.info("🚀 Starting MayArbi Dashboard on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
