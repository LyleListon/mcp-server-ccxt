#!/usr/bin/env python3
"""
🚀 MEV EMPIRE DASHBOARD LAUNCHER
Launch dashboard and open browser automatically
"""

import subprocess
import time
import webbrowser
import os
import sys

def main():
    print("🚀" * 30)
    print("🚀 MEV EMPIRE DASHBOARD LAUNCHER")
    print("🚀" * 30)
    
    # Set environment
    os.environ['ETHEREUM_NODE_URL'] = 'http://192.168.1.18:8545'
    
    print("🌐 Starting MEV Empire Dashboard...")
    print("📊 Dashboard will open automatically in your browser")
    print("🔄 Real-time updates every 5 seconds")
    print("")
    
    try:
        # Start dashboard in background
        dashboard_process = subprocess.Popen(
            [sys.executable, 'mev_empire_dashboard.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("⏳ Waiting for dashboard to start...")
        time.sleep(3)
        
        # Test if dashboard is running
        import requests
        try:
            response = requests.get('http://localhost:5000', timeout=5)
            if response.status_code == 200:
                print("✅ Dashboard is running!")
                
                # Open browser
                print("🌐 Opening browser...")
                webbrowser.open('http://localhost:5000')
                
                print("")
                print("📊 MEV EMPIRE DASHBOARD ACTIVE!")
                print("🔗 URL: http://localhost:5000")
                print("🔄 Press Ctrl+C to stop")
                print("")
                
                # Keep running
                dashboard_process.wait()
                
            else:
                print("❌ Dashboard not responding")
                
        except requests.exceptions.RequestException:
            print("❌ Could not connect to dashboard")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping dashboard...")
        dashboard_process.terminate()
        print("✅ Dashboard stopped")
        
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    main()
