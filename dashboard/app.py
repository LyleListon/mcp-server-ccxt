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

def read_live_data_updates():
    """Read live data from WSL2 file bridge."""
    import time

    file_path = r"C:\temp\mayarbi_dashboard_data.json"
    last_update_count = 0

    while True:
        try:
            # Check if file exists
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)

                    # Check if this is new data
                    current_update_count = data.get('update_count', 0)
                    if current_update_count > last_update_count:
                        last_update_count = current_update_count

                        # Update dashboard with live data
                        if 'trading_stats' in data:
                            ts = data['trading_stats']
                            dashboard_data.trading_stats.update({
                                'session_profit': float(ts.get('session_profit', 0)),
                                'total_trades': int(ts.get('total_trades', 0)),
                                'success_rate': float(ts.get('success_rate', '0%').replace('%', '')),
                                'wallet_balance': float(ts.get('wallet_balance', '$0').replace('$', ''))
                            })

                        if 'system_status' in data:
                            ss = data['system_status']
                            dashboard_data.live_metrics.update({
                                'system_status': 'connected' if 'Connected' in ss.get('wsl2_bot', '') else 'connecting',
                                'last_update': ss.get('last_update', 'Unknown')
                            })

                        if 'network_performance' in data:
                            np = data['network_performance']
                            for network in ['arbitrum', 'base', 'optimism']:
                                if network in np:
                                    opps_text = np[network]
                                    # Extract number from "X opportunities"
                                    opps = int(opps_text.split()[0]) if opps_text.split()[0].isdigit() else 0
                                    dashboard_data.network_performance[network]['opportunities'] = opps

                        # Broadcast update to clients
                        broadcast_update()
                        logger.info(f"📊 Live data updated from WSL2 (#{current_update_count})")

                except json.JSONDecodeError:
                    logger.warning("⚠️ Invalid JSON in data file")
                except Exception as e:
                    logger.error(f"❌ Error reading data file: {e}")
            else:
                # File doesn't exist yet - bot hasn't written data
                dashboard_data.live_metrics['system_status'] = 'waiting_for_bot'

            time.sleep(2)  # Check every 2 seconds

        except Exception as e:
            logger.error(f"❌ Data reader error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    # Start live data reader in background (WSL2 → Windows file bridge)
    data_thread = threading.Thread(target=read_live_data_updates, daemon=True)
    data_thread.start()

    # Use port 9999 for Windows dashboard
    port = 9999
    logger.info(f"🚀 Starting MayArbi Dashboard on http://localhost:{port}")
    logger.info(f"📁 Reading live data from: C:\\temp\\mayarbi_dashboard_data.json")
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
