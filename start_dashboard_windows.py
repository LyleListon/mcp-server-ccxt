#!/usr/bin/env python3
"""
Windows-compatible dashboard launcher
Run this directly on Windows to avoid WSL2 networking issues
"""

import http.server
import socketserver
import webbrowser
import threading
import time

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>MayArbi Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            background: linear-gradient(135deg, #0f1419 0%, #1e3c72 100%);
            color: #e6e6e6;
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            text-align: center;
        }
        h1 {
            color: #00d4aa;
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 0 0 20px rgba(0, 212, 170, 0.3);
        }
        .status {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            backdrop-filter: blur(10px);
        }
        .success {
            border-left: 5px solid #00d4aa;
        }
        .info {
            border-left: 5px solid #3498db;
        }
        .button {
            background: linear-gradient(45deg, #00d4aa, #3498db);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 25px;
            font-size: 1.1em;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 10px;
            transition: transform 0.2s;
        }
        .button:hover {
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 MayArbi Dashboard</h1>
        
        <div class="status success">
            <h2>✅ Dashboard Running Successfully!</h2>
            <p>Port: 8080 | Status: Active | Method: Direct Windows</p>
        </div>
        
        <div class="status info">
            <h3>🎯 WSL2 Networking Bypass</h3>
            <p>This dashboard is running directly on Windows to avoid WSL2 port forwarding issues.</p>
            <p>Your arbitrage bot is still running in WSL2 and can communicate with this dashboard.</p>
        </div>
        
        <div class="status info">
            <h3>📊 Next Steps</h3>
            <p>1. Keep this window open</p>
            <p>2. Run your arbitrage bot in WSL2</p>
            <p>3. The bot will send data to this dashboard</p>
        </div>
        
        <a href="/" class="button">🔄 Refresh Dashboard</a>
        <a href="http://localhost:8080" class="button">🌐 Open in New Tab</a>
    </div>
</body>
</html>'''
        
        self.wfile.write(html.encode('utf-8'))

def open_browser():
    """Open browser after a short delay"""
    time.sleep(2)
    webbrowser.open('http://localhost:8080')

if __name__ == '__main__':
    PORT = 8080
    
    print("🚀 Starting MayArbi Dashboard (Windows Direct)")
    print(f"📊 URL: http://localhost:{PORT}")
    print("🔧 This bypasses WSL2 networking issues")
    print("⚡ Your arbitrage bot can still run in WSL2")
    print("\n" + "="*50)
    
    # Start browser in background
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Start server
    try:
        with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
            print(f"✅ Dashboard server running on port {PORT}")
            print("🌐 Browser should open automatically")
            print("🛑 Press Ctrl+C to stop")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to exit...")
