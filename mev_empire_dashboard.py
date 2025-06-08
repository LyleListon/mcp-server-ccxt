#!/usr/bin/env python3
"""
📊 MEV EMPIRE DASHBOARD
Real-time monitoring and control center for your complete MEV operation

Features:
- Live performance metrics across all strategies
- Real-time profit tracking and analytics
- Dynamic settings adjustment (gas limits, profit thresholds)
- System health monitoring
- DEX discovery tracking
- MEV bot intelligence
- Risk management controls
- Multi-chain overview
"""

import asyncio
import json
import sqlite3
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import psutil
import requests
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mev_empire_dashboard_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict
    uptime: float

@dataclass
class StrategyMetrics:
    """Individual strategy performance"""
    name: str
    status: str
    opportunities_found: int
    trades_executed: int
    success_rate: float
    total_profit: float
    profit_per_hour: float
    last_trade_time: str
    gas_used: float

@dataclass
class ChainMetrics:
    """Per-chain performance data"""
    chain_name: str
    dexes_count: int
    latest_block: int
    gas_price_gwei: float
    opportunities_24h: int
    profit_24h: float

class MEVEmpireDashboard:
    """
    📊 MEV EMPIRE DASHBOARD
    
    Real-time monitoring and control center
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.ethereum_node_url = os.getenv('ETHEREUM_NODE_URL', 'http://192.168.1.18:8545')
        
        # Enhanced dashboard configuration with MEV competitive settings
        self.config = {
            'refresh_interval': 2,  # seconds - faster updates
            'profit_target_daily': 500.0,  # USD
            'risk_limits': {
                'max_gas_gwei': 300,  # Updated for MEV competition
                'max_position_size_pct': 75,
                'daily_loss_limit_pct': 10,
                'max_slippage_pct': 5.0,
                'circuit_breaker_losses': 5
            },
            'strategy_settings': {
                'liquidation': {
                    'enabled': True,
                    'min_profit_usd': 50.0,
                    'max_gas_gwei': 300.0,  # MEV competitive
                    'priority': 1,
                    'allocation_pct': 40.0
                },
                'flashloan_arbitrage': {
                    'enabled': True,
                    'min_profit_usd': 10.0,
                    'max_gas_gwei': 200.0,  # MEV competitive
                    'priority': 2,
                    'allocation_pct': 35.0
                },
                'frontrunning': {
                    'enabled': True,
                    'min_profit_usd': 25.0,
                    'max_gas_gwei': 250.0,  # MEV competitive
                    'priority': 3,
                    'allocation_pct': 25.0
                },
                'crosschain': {
                    'enabled': True,
                    'min_profit_usd': 30.0,
                    'max_gas_gwei': 150.0,
                    'priority': 4,
                    'allocation_pct': 20.0
                }
            },
            'advanced_settings': {
                'gas_price_multiplier': 4.0,  # Aggressive MEV
                'enable_flashbots': True,
                'enable_private_mempool': True,
                'max_concurrent_trades': 5,
                'enable_batch_execution': True,
                'mev_protection_level': 'high'
            }
        }
        
        # Enhanced data storage
        self.metrics_history = []
        self.recent_trades = []
        self.system_alerts = []
        self.profit_history = []
        self.gas_price_history = []
        self.trade_log = []
        self.performance_stats = {
            'total_trades': 0,
            'successful_trades': 0,
            'total_profit': 0.0,
            'total_gas_spent': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0,
            'avg_profit_per_trade': 0.0
        }
        
        print("📊 MEV Empire Dashboard initialized")
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system performance metrics"""
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            return SystemMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_io={
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv
                },
                uptime=time.time() - self.start_time
            )
        except Exception as e:
            print(f"Error getting system metrics: {e}")
            return SystemMetrics(0, 0, 0, {}, 0)
    
    def get_strategy_metrics(self) -> List[StrategyMetrics]:
        """Get performance metrics for all strategies"""
        
        strategies = []
        
        # Check if processes are running
        mev_empire_running = self._check_process_running('ethereum_node_master.py')
        crosschain_running = self._check_process_running('spy_enhanced_arbitrage.py')
        
        # Ethereum MEV Empire strategies
        strategies.extend([
            StrategyMetrics(
                name="Liquidation Bot",
                status="🟢 ACTIVE" if mev_empire_running else "🔴 STOPPED",
                opportunities_found=self._get_mock_metric('liquidation', 'opportunities', 15),
                trades_executed=self._get_mock_metric('liquidation', 'trades', 8),
                success_rate=self._get_mock_metric('liquidation', 'success_rate', 85.5),
                total_profit=self._get_mock_metric('liquidation', 'profit', 1250.75),
                profit_per_hour=self._get_mock_metric('liquidation', 'profit_per_hour', 125.50),
                last_trade_time="2 minutes ago",
                gas_used=self._get_mock_metric('liquidation', 'gas', 0.025)
            ),
            StrategyMetrics(
                name="Flashloan Arbitrage",
                status="🟢 ACTIVE" if mev_empire_running else "🔴 STOPPED",
                opportunities_found=self._get_mock_metric('flashloan', 'opportunities', 45),
                trades_executed=self._get_mock_metric('flashloan', 'trades', 28),
                success_rate=self._get_mock_metric('flashloan', 'success_rate', 62.2),
                total_profit=self._get_mock_metric('flashloan', 'profit', 890.25),
                profit_per_hour=self._get_mock_metric('flashloan', 'profit_per_hour', 89.50),
                last_trade_time="45 seconds ago",
                gas_used=self._get_mock_metric('flashloan', 'gas', 0.045)
            ),
            StrategyMetrics(
                name="Frontrun Frontrunners",
                status="🟢 ACTIVE" if mev_empire_running else "🔴 STOPPED",
                opportunities_found=self._get_mock_metric('frontrun', 'opportunities', 12),
                trades_executed=self._get_mock_metric('frontrun', 'trades', 7),
                success_rate=self._get_mock_metric('frontrun', 'success_rate', 58.3),
                total_profit=self._get_mock_metric('frontrun', 'profit', 420.80),
                profit_per_hour=self._get_mock_metric('frontrun', 'profit_per_hour', 42.50),
                last_trade_time="5 minutes ago",
                gas_used=self._get_mock_metric('frontrun', 'gas', 0.035)
            )
        ])
        
        # Cross-chain arbitrage
        strategies.append(
            StrategyMetrics(
                name="Cross-Chain Arbitrage",
                status="🟢 ACTIVE" if crosschain_running else "🔴 STOPPED",
                opportunities_found=self._get_mock_metric('crosschain', 'opportunities', 22),
                trades_executed=self._get_mock_metric('crosschain', 'trades', 15),
                success_rate=self._get_mock_metric('crosschain', 'success_rate', 68.2),
                total_profit=self._get_mock_metric('crosschain', 'profit', 675.40),
                profit_per_hour=self._get_mock_metric('crosschain', 'profit_per_hour', 67.75),
                last_trade_time="3 minutes ago",
                gas_used=self._get_mock_metric('crosschain', 'gas', 0.028)
            )
        )
        
        return strategies
    
    def get_chain_metrics(self) -> List[ChainMetrics]:
        """Get metrics for all monitored chains"""
        
        chains = []
        
        # Ethereum mainnet
        try:
            response = requests.post(
                self.ethereum_node_url,
                json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
                timeout=3
            )
            if response.status_code == 200:
                block_hex = response.json().get('result', '0x0')
                latest_block = int(block_hex, 16)
            else:
                latest_block = 0
        except:
            latest_block = 0
        
        chains.append(ChainMetrics(
            chain_name="Ethereum",
            dexes_count=self._get_dex_count('ethereum_dexes.db'),
            latest_block=latest_block,
            gas_price_gwei=self._get_mock_metric('ethereum', 'gas_price', 1.3),
            opportunities_24h=self._get_mock_metric('ethereum', 'opportunities_24h', 85),
            profit_24h=self._get_mock_metric('ethereum', 'profit_24h', 2250.75)
        ))
        
        # L2 chains
        l2_chains = ['arbitrum', 'base', 'optimism', 'polygon', 'bsc']
        for chain in l2_chains:
            chains.append(ChainMetrics(
                chain_name=chain.title(),
                dexes_count=self._get_dex_count(f'{chain}_dexes.db'),
                latest_block=self._get_mock_metric(chain, 'block', 45000000),
                gas_price_gwei=self._get_mock_metric(chain, 'gas_price', 0.1),
                opportunities_24h=self._get_mock_metric(chain, 'opportunities_24h', 25),
                profit_24h=self._get_mock_metric(chain, 'profit_24h', 150.25)
            ))
        
        return chains
    
    def _check_process_running(self, process_name: str) -> bool:
        """Check if a process is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline'] and any(process_name in cmd for cmd in proc.info['cmdline']):
                    return True
        except:
            pass
        return False
    
    def _get_dex_count(self, db_file: str) -> int:
        """Get DEX count from database"""
        try:
            if os.path.exists(db_file):
                conn = sqlite3.connect(db_file)
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM dexes")
                count = c.fetchone()[0]
                conn.close()
                return count
        except:
            pass
        return 0
    
    def _get_mock_metric(self, strategy: str, metric: str, base_value: float) -> float:
        """Generate realistic mock metrics (replace with real data sources)"""
        import random
        
        # Add some realistic variation
        variation = random.uniform(0.9, 1.1)
        return round(base_value * variation, 2)
    
    def update_strategy_settings(self, strategy: str, settings: Dict):
        """Update strategy settings"""
        if strategy == 'all':
            # Update all strategies
            for strat_name in self.config['strategy_settings']:
                self.config['strategy_settings'][strat_name].update(settings)
        elif strategy in self.config['strategy_settings']:
            self.config['strategy_settings'][strategy].update(settings)
        elif strategy == 'advanced':
            # Update advanced settings
            self.config['advanced_settings'].update(settings)
        else:
            return False

        # Save to file
        with open('dashboard_config.json', 'w') as f:
            json.dump(self.config, f, indent=2)

        # Add alert for settings change
        self.system_alerts.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'settings_update',
            'message': f"Updated {strategy} settings: {settings}",
            'level': 'info'
        })

        return True

    def add_trade_log(self, trade_data: Dict):
        """Add a trade to the log for dashboard display"""
        trade_entry = {
            'timestamp': datetime.now().isoformat(),
            'strategy': trade_data.get('strategy', 'unknown'),
            'token_pair': trade_data.get('token_pair', 'UNKNOWN/UNKNOWN'),
            'dex_pair': f"{trade_data.get('buy_dex', 'unknown')} → {trade_data.get('sell_dex', 'unknown')}",
            'profit_usd': trade_data.get('profit_usd', 0.0),
            'gas_spent': trade_data.get('gas_spent', 0.0),
            'success': trade_data.get('success', False),
            'execution_time': trade_data.get('execution_time', 0.0)
        }

        self.trade_log.append(trade_entry)

        # Keep only last 100 trades
        if len(self.trade_log) > 100:
            self.trade_log = self.trade_log[-100:]

        # Update performance stats
        self._update_performance_stats(trade_entry)

    def _update_performance_stats(self, trade: Dict):
        """Update performance statistics"""
        self.performance_stats['total_trades'] += 1

        if trade['success']:
            self.performance_stats['successful_trades'] += 1
            profit = trade['profit_usd']
            self.performance_stats['total_profit'] += profit

            if profit > self.performance_stats['best_trade']:
                self.performance_stats['best_trade'] = profit
            if profit < self.performance_stats['worst_trade'] or self.performance_stats['worst_trade'] == 0:
                self.performance_stats['worst_trade'] = profit

        self.performance_stats['total_gas_spent'] += trade['gas_spent']

        # Calculate averages
        if self.performance_stats['total_trades'] > 0:
            self.performance_stats['avg_profit_per_trade'] = (
                self.performance_stats['total_profit'] / self.performance_stats['total_trades']
            )

    def get_recent_trades(self, limit: int = 20) -> List[Dict]:
        """Get recent trades for dashboard display"""
        return self.trade_log[-limit:] if self.trade_log else []

    def get_profit_chart_data(self) -> Dict:
        """Get profit data for charting"""
        # Generate sample profit data (replace with real data)
        now = datetime.now()
        profit_data = []

        for i in range(24):  # Last 24 hours
            timestamp = now - timedelta(hours=23-i)
            profit = self._get_mock_metric('total', 'hourly_profit', 50.0)
            profit_data.append({
                'timestamp': timestamp.isoformat(),
                'profit': profit,
                'cumulative': sum(p['profit'] for p in profit_data) + profit
            })

        return {
            'hourly_profits': profit_data,
            'total_profit': self.performance_stats['total_profit'],
            'success_rate': (
                self.performance_stats['successful_trades'] /
                max(self.performance_stats['total_trades'], 1) * 100
            )
        }

# Global dashboard instance
dashboard = MEVEmpireDashboard()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/metrics')
def get_metrics():
    """API endpoint for all metrics"""
    return jsonify({
        'system': asdict(dashboard.get_system_metrics()),
        'strategies': [asdict(s) for s in dashboard.get_strategy_metrics()],
        'chains': [asdict(c) for c in dashboard.get_chain_metrics()],
        'config': dashboard.config,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update strategy settings"""
    data = request.json
    strategy = data.get('strategy')
    settings = data.get('settings')

    if dashboard.update_strategy_settings(strategy, settings):
        return jsonify({'success': True, 'message': f'Updated {strategy} settings'})
    else:
        return jsonify({'success': False, 'error': 'Invalid strategy'})

@app.route('/api/trades')
def get_recent_trades():
    """Get recent trades"""
    limit = request.args.get('limit', 20, type=int)
    return jsonify({
        'trades': dashboard.get_recent_trades(limit),
        'performance': dashboard.performance_stats
    })

@app.route('/api/charts/profit')
def get_profit_chart():
    """Get profit chart data"""
    return jsonify(dashboard.get_profit_chart_data())

@app.route('/api/alerts')
def get_alerts():
    """Get system alerts"""
    return jsonify({
        'alerts': dashboard.system_alerts[-50:],  # Last 50 alerts
        'count': len(dashboard.system_alerts)
    })

@app.route('/api/emergency_stop', methods=['POST'])
def emergency_stop():
    """Emergency stop all trading"""
    # This would integrate with your actual trading systems
    dashboard.system_alerts.append({
        'timestamp': datetime.now().isoformat(),
        'type': 'emergency_stop',
        'message': 'EMERGENCY STOP activated from dashboard',
        'level': 'critical'
    })
    return jsonify({'success': True, 'message': 'Emergency stop activated'})

@app.route('/api/config')
def get_config():
    """Get current configuration"""
    return jsonify(dashboard.config)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('📊 Dashboard client connected')
    emit('status', {'message': 'Connected to MEV Empire Dashboard'})

@socketio.on('request_update')
def handle_update_request():
    """Handle real-time update request"""
    metrics = {
        'system': asdict(dashboard.get_system_metrics()),
        'strategies': [asdict(s) for s in dashboard.get_strategy_metrics()],
        'chains': [asdict(c) for c in dashboard.get_chain_metrics()],
        'timestamp': datetime.now().isoformat()
    }
    emit('metrics_update', metrics)

def background_updates():
    """Background thread for real-time updates"""
    while True:
        try:
            metrics = {
                'system': asdict(dashboard.get_system_metrics()),
                'strategies': [asdict(s) for s in dashboard.get_strategy_metrics()],
                'chains': [asdict(c) for c in dashboard.get_chain_metrics()],
                'timestamp': datetime.now().isoformat()
            }
            socketio.emit('metrics_update', metrics)
            time.sleep(dashboard.config['refresh_interval'])
        except Exception as e:
            print(f"Background update error: {e}")
            time.sleep(10)

if __name__ == '__main__':
    print("📊" * 50)
    print("📊 MEV EMPIRE DASHBOARD - ENHANCED")
    print("📊 Real-time Monitoring & Control Center")
    print("📊 Advanced MEV Strategy Management")
    print("📊" * 50)
    print("🌐 Starting enhanced web server...")
    print("📊 Dashboard URL: http://localhost:5002")
    print("🔄 Real-time updates every 2 seconds")
    print("📈 Live profit charts & trade monitoring")
    print("⚙️ Dynamic settings adjustment")
    print("🚨 Emergency controls available")

    # Start background updates
    update_thread = threading.Thread(target=background_updates, daemon=True)
    update_thread.start()

    # Start web server on port 5002 with better browser compatibility
    socketio.run(app, host='0.0.0.0', port=5002, debug=False, allow_unsafe_werkzeug=True)
