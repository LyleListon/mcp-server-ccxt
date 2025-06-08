#!/usr/bin/env python3
"""
📊 SIMPLE MEV EMPIRE DASHBOARD
Simplified version for easier debugging
"""

from flask import Flask, render_template_string
import json
import time
import os
import psutil
import sqlite3

app = Flask(__name__)

# Simple HTML template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>🎯 MEV Empire Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            background: #1a1a2e; 
            color: white; 
            margin: 20px; 
        }
        .header { 
            text-align: center; 
            background: #16213e; 
            padding: 20px; 
            border-radius: 10px; 
            margin-bottom: 20px; 
        }
        .card { 
            background: #0f3460; 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 8px; 
            border-left: 4px solid #4CAF50; 
        }
        .metric { 
            display: flex; 
            justify-content: space-between; 
            margin: 5px 0; 
        }
        .value { 
            color: #4CAF50; 
            font-weight: bold; 
        }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 20px; 
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 MEV Empire Dashboard</h1>
        <p>Real-time Monitoring (Auto-refresh every 5 seconds)</p>
        <p>🟢 LIVE | Last Update: {{ timestamp }}</p>
    </div>

    <div class="grid">
        <div class="card">
            <h3>🖥️ System Performance</h3>
            <div class="metric">
                <span>CPU Usage:</span>
                <span class="value">{{ system.cpu }}%</span>
            </div>
            <div class="metric">
                <span>Memory Usage:</span>
                <span class="value">{{ system.memory }}%</span>
            </div>
            <div class="metric">
                <span>Uptime:</span>
                <span class="value">{{ system.uptime }}</span>
            </div>
        </div>

        <div class="card">
            <h3>📡 Ethereum Node</h3>
            <div class="metric">
                <span>Node URL:</span>
                <span class="value">{{ ethereum.url }}</span>
            </div>
            <div class="metric">
                <span>Latest Block:</span>
                <span class="value">{{ ethereum.block }}</span>
            </div>
            <div class="metric">
                <span>DEXes Found:</span>
                <span class="value">{{ ethereum.dexes }}</span>
            </div>
        </div>

        <div class="card">
            <h3>🎯 MEV Strategies</h3>
            <div class="metric">
                <span>Ethereum MEV Empire:</span>
                <span class="value">{{ strategies.ethereum_status }}</span>
            </div>
            <div class="metric">
                <span>Cross-Chain Arbitrage:</span>
                <span class="value">{{ strategies.crosschain_status }}</span>
            </div>
            <div class="metric">
                <span>DEX Scanner:</span>
                <span class="value">{{ strategies.scanner_status }}</span>
            </div>
        </div>

        <div class="card">
            <h3>💰 Performance Summary</h3>
            <div class="metric">
                <span>Total Processes:</span>
                <span class="value">{{ performance.processes }}</span>
            </div>
            <div class="metric">
                <span>Active Strategies:</span>
                <span class="value">{{ performance.active_strategies }}</span>
            </div>
            <div class="metric">
                <span>System Status:</span>
                <span class="value">{{ performance.status }}</span>
            </div>
        </div>
    </div>

    <div style="text-align: center; margin-top: 30px; padding: 20px; background: #16213e; border-radius: 10px;">
        <h3>🚀 MEV Empire Control Center</h3>
        <p>Your complete MEV operation monitoring dashboard</p>
        <p>Ethereum Node: {{ ethereum.url }} | Dashboard Port: 8080</p>
    </div>
</body>
</html>
"""

def get_system_metrics():
    """Get system performance metrics"""
    try:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_hours = int(uptime_seconds // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)
        uptime = f"{uptime_hours}h {uptime_minutes}m"
        
        return {
            'cpu': round(cpu, 1),
            'memory': round(memory, 1),
            'uptime': uptime
        }
    except:
        return {'cpu': 0, 'memory': 0, 'uptime': '0h 0m'}

def get_ethereum_metrics():
    """Get Ethereum node metrics"""
    ethereum_url = os.getenv('ETHEREUM_NODE_URL', 'http://192.168.1.18:8545')
    
    try:
        import requests
        response = requests.post(
            ethereum_url,
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
    
    # Get DEX count
    dex_count = 0
    try:
        if os.path.exists('ethereum_dexes.db'):
            conn = sqlite3.connect('ethereum_dexes.db')
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM dexes")
            dex_count = c.fetchone()[0]
            conn.close()
    except:
        pass
    
    return {
        'url': ethereum_url,
        'block': f"{latest_block:,}" if latest_block > 0 else "Not connected",
        'dexes': dex_count
    }

def get_strategy_status():
    """Get MEV strategy status"""
    
    def check_process(name):
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline'] and any(name in cmd for cmd in proc.info['cmdline']):
                    return "🟢 RUNNING"
        except:
            pass
        return "🔴 STOPPED"
    
    return {
        'ethereum_status': check_process('ethereum_node_master.py'),
        'crosschain_status': check_process('spy_enhanced_arbitrage.py'),
        'scanner_status': check_process('ethereum_dex_scanner.py')
    }

def get_performance_summary():
    """Get overall performance summary"""
    
    # Count MEV-related processes
    mev_processes = 0
    active_strategies = 0
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if any(keyword in cmdline for keyword in ['mev', 'arbitrage', 'dex_scanner', 'ethereum_node']):
                    mev_processes += 1
                    if any(strategy in cmdline for strategy in ['master', 'arbitrage', 'scanner']):
                        active_strategies += 1
    except:
        pass
    
    status = "🟢 OPERATIONAL" if active_strategies > 0 else "🔴 INACTIVE"
    
    return {
        'processes': mev_processes,
        'active_strategies': active_strategies,
        'status': status
    }

@app.route('/')
def dashboard():
    """Main dashboard route"""
    
    data = {
        'timestamp': time.strftime('%H:%M:%S'),
        'system': get_system_metrics(),
        'ethereum': get_ethereum_metrics(),
        'strategies': get_strategy_status(),
        'performance': get_performance_summary()
    }
    
    return render_template_string(DASHBOARD_HTML, **data)

@app.route('/api/status')
def api_status():
    """API endpoint for status"""
    return {
        'status': 'running',
        'timestamp': time.time(),
        'system': get_system_metrics(),
        'ethereum': get_ethereum_metrics(),
        'strategies': get_strategy_status()
    }

if __name__ == '__main__':
    print("📊" * 20)
    print("📊 SIMPLE MEV EMPIRE DASHBOARD")
    print("📊" * 20)
    print("🌐 Starting on port 8080...")
    print("📊 Dashboard URL: http://localhost:8080")
    print("🔄 Auto-refresh every 5 seconds")
    print("📊" * 20)
    
    try:
        app.run(host='0.0.0.0', port=8080, debug=False)
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        print("💡 Try a different port or check if port 8080 is available")
