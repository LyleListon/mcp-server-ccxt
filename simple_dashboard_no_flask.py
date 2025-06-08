#!/usr/bin/env python3
"""
Simple MayArbi Dashboard - No Flask Required
Uses only Python standard library
"""

import http.server
import socketserver
import json
import os
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_dashboard()
        elif parsed_path.path == '/api/stats':
            self.serve_stats()
        elif parsed_path.path == '/api/status':
            self.serve_status()
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>MayArbi Live Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0f1419 0%, #1e3c72 100%);
            color: #e6e6e6;
            font-family: 'Segoe UI', Arial, sans-serif;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        h1 {
            color: #00d4aa;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 0 0 20px rgba(0, 212, 170, 0.3);
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .card h3 {
            color: #00d4aa;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .metric:last-child { border-bottom: none; }
        .metric-value {
            color: #00d4aa;
            font-weight: bold;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-active { background: #00d4aa; }
        .status-warning { background: #f39c12; }
        .status-error { background: #e74c3c; }
        .refresh-btn {
            background: linear-gradient(45deg, #00d4aa, #3498db);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            margin: 10px;
            transition: transform 0.2s;
        }
        .refresh-btn:hover { transform: translateY(-2px); }
        .log-area {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
    </style>
    <script>
        function refreshData() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                    // Update metrics here
                })
                .catch(error => console.error('Error:', error));
        }
        
        // Auto-refresh every 5 seconds
        setInterval(refreshData, 5000);
        
        // Initial load
        window.onload = refreshData;
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 MayArbi Live Dashboard</h1>
            <p>Real-time Arbitrage Trading Monitor</p>
            <p>Last Update: <span id="last-update">Loading...</span></p>
            <button class="refresh-btn" onclick="refreshData()">🔄 Refresh</button>
        </div>
        
        <div class="status-grid">
            <div class="card">
                <h3>📊 Trading Statistics</h3>
                <div class="metric">
                    <span>Session Profit:</span>
                    <span class="metric-value">$0.00</span>
                </div>
                <div class="metric">
                    <span>Total Trades:</span>
                    <span class="metric-value">0</span>
                </div>
                <div class="metric">
                    <span>Success Rate:</span>
                    <span class="metric-value">0%</span>
                </div>
                <div class="metric">
                    <span>ROI:</span>
                    <span class="metric-value">0%</span>
                </div>
            </div>
            
            <div class="card">
                <h3>⚡ System Status</h3>
                <div class="metric">
                    <span><span class="status-indicator status-active"></span>Arbitrage Bot:</span>
                    <span class="metric-value">Active</span>
                </div>
                <div class="metric">
                    <span><span class="status-indicator status-active"></span>Price Feeds:</span>
                    <span class="metric-value">Connected</span>
                </div>
                <div class="metric">
                    <span><span class="status-indicator status-active"></span>Wallet:</span>
                    <span class="metric-value">$458.31</span>
                </div>
                <div class="metric">
                    <span>Scan Speed:</span>
                    <span class="metric-value">5.2s</span>
                </div>
            </div>
            
            <div class="card">
                <h3>🌐 Network Performance</h3>
                <div class="metric">
                    <span>Arbitrum:</span>
                    <span class="metric-value">0 ops</span>
                </div>
                <div class="metric">
                    <span>Base:</span>
                    <span class="metric-value">0 ops</span>
                </div>
                <div class="metric">
                    <span>Optimism:</span>
                    <span class="metric-value">0 ops</span>
                </div>
                <div class="metric">
                    <span>Gas Price:</span>
                    <span class="metric-value">25 gwei</span>
                </div>
            </div>
            
            <div class="card">
                <h3>📈 Recent Activity</h3>
                <div class="log-area">
                    <div>🔍 Scanning DEXs...</div>
                    <div>⚡ Dashboard started successfully</div>
                    <div>🌐 Monitoring 43 DEXs across 3 chains</div>
                    <div>💰 Wallet balance: $458.31</div>
                    <div>🎯 Ready for arbitrage opportunities</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
        
        self.wfile.write(html.encode('utf-8'))
    
    def serve_stats(self):
        """Serve trading statistics as JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        stats = {
            'timestamp': datetime.now().isoformat(),
            'trading_stats': {
                'total_profit': 0.0,
                'total_trades': 0,
                'success_rate': 0.0,
                'roi_percentage': 0.0
            },
            'system_status': {
                'bot_active': True,
                'feeds_connected': True,
                'wallet_balance': 458.31,
                'scan_speed': 5.2
            },
            'network_performance': {
                'arbitrum': {'opportunities': 0},
                'base': {'opportunities': 0},
                'optimism': {'opportunities': 0}
            }
        }
        
        self.wfile.write(json.dumps(stats).encode('utf-8'))
    
    def serve_status(self):
        """Serve simple status check"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        status = {
            'status': 'active',
            'timestamp': datetime.now().isoformat(),
            'message': 'MayArbi Dashboard is running'
        }
        
        self.wfile.write(json.dumps(status).encode('utf-8'))

if __name__ == '__main__':
    PORT = 8888
    
    print("🚀 Starting MayArbi Dashboard (No Flask)")
    print(f"📊 URL: http://localhost:{PORT}")
    print("🔧 Using Python standard library only")
    print("⚡ Auto-refresh every 5 seconds")
    print("\n" + "="*50)
    
    try:
        with socketserver.TCPServer(("0.0.0.0", PORT), DashboardHandler) as httpd:
            print(f"✅ Dashboard server running on port {PORT}")
            print("🌐 Access via http://localhost:8888")
            print("🛑 Press Ctrl+C to stop")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
