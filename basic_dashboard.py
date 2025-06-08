#!/usr/bin/env python3
"""
Basic MEV Empire Dashboard - No SocketIO
"""

from flask import Flask, render_template_string, jsonify
import json
import psutil
import time
from datetime import datetime

app = Flask(__name__)

# Basic dashboard template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 MEV Empire Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 2rem;
            background: rgba(0,0,0,0.3);
            padding: 2rem;
            border-radius: 15px;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 2rem;
        }
        .card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .status-active { color: #4CAF50; }
        .status-stopped { color: #f44336; }
        .btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            cursor: pointer;
            margin: 0.25rem;
        }
        .btn:hover { background: #45a049; }
        .emergency-btn {
            background: #f44336;
            font-size: 1.2rem;
            padding: 1rem 2rem;
            margin: 1rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 MEV EMPIRE DASHBOARD</h1>
        <p>Real-time MEV Strategy Monitoring & Control</p>
        <p id="timestamp">{{ timestamp }}</p>
    </div>

    <div class="dashboard-grid">
        <!-- System Status -->
        <div class="card">
            <h3>🖥️ System Status</h3>
            <div class="metric">
                <span>CPU Usage:</span>
                <span id="cpu">{{ cpu }}%</span>
            </div>
            <div class="metric">
                <span>Memory:</span>
                <span id="memory">{{ memory }}%</span>
            </div>
            <div class="metric">
                <span>Disk:</span>
                <span id="disk">{{ disk }}%</span>
            </div>
        </div>

        <!-- MEV Strategies -->
        <div class="card">
            <h3>🎯 MEV Strategies</h3>
            <div class="metric">
                <span>Liquidation Bot:</span>
                <span class="status-stopped">🔴 STOPPED</span>
            </div>
            <div class="metric">
                <span>Arbitrage Bot:</span>
                <span class="status-stopped">🔴 STOPPED</span>
            </div>
            <div class="metric">
                <span>Frontrunning:</span>
                <span class="status-stopped">🔴 STOPPED</span>
            </div>
        </div>

        <!-- Performance -->
        <div class="card">
            <h3>📊 Performance</h3>
            <div class="metric">
                <span>Total Profit:</span>
                <span style="color: #4CAF50;">$0.00</span>
            </div>
            <div class="metric">
                <span>Trades Today:</span>
                <span>0</span>
            </div>
            <div class="metric">
                <span>Success Rate:</span>
                <span>0%</span>
            </div>
        </div>

        <!-- Controls -->
        <div class="card">
            <h3>⚙️ Quick Controls</h3>
            <div style="text-align: center;">
                <button class="btn" onclick="alert('Settings updated!')">Update Gas Price</button>
                <button class="btn" onclick="alert('Threshold updated!')">Set Profit Threshold</button>
                <button class="emergency-btn" onclick="alert('EMERGENCY STOP ACTIVATED!')">
                    🚨 EMERGENCY STOP
                </button>
            </div>
        </div>
    </div>

    <script>
        // Auto-refresh every 5 seconds
        setInterval(() => {
            location.reload();
        }, 5000);
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    # Get system metrics
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template_string(DASHBOARD_HTML, 
                                cpu=cpu, 
                                memory=memory, 
                                disk=disk,
                                timestamp=timestamp)

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'cpu': psutil.cpu_percent(),
        'memory': psutil.virtual_memory().percent
    })

if __name__ == '__main__':
    print("🎯" * 40)
    print("🎯 MEV EMPIRE BASIC DASHBOARD")
    print("🎯" * 40)
    print("🌐 Starting basic web server...")
    print("📊 Dashboard URL: http://127.0.0.1:5004")
    print("🔄 Auto-refresh every 5 seconds")
    
    app.run(host='0.0.0.0', port=5004, debug=False)
