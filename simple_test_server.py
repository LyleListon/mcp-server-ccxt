#!/usr/bin/env python3
"""
Simple test server to verify browser connectivity
"""

from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>🎯 MEV Empire - Connection Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            text-align: center;
            padding: 50px;
            margin: 0;
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(0,0,0,0.3);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        h1 { font-size: 3rem; margin-bottom: 2rem; }
        .status { font-size: 1.5rem; margin: 2rem 0; }
        .success { color: #4CAF50; }
        .info { color: #2196F3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 MEV EMPIRE DASHBOARD</h1>
        <div class="status success">✅ CONNECTION SUCCESSFUL!</div>
        <div class="status info">🚀 Browser connectivity verified</div>
        <div class="status info">📊 Ready for full dashboard</div>
        
        <p>If you can see this page, your browser can connect to the server!</p>
        <p>The full MEV Empire Dashboard will work on this same port.</p>
        
        <button onclick="location.reload()" style="
            background: #4CAF50;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 1.2rem;
            border-radius: 10px;
            cursor: pointer;
            margin-top: 2rem;
        ">🔄 Refresh Test</button>
    </div>
</body>
</html>
    ''')

if __name__ == '__main__':
    print("🧪" * 30)
    print("🧪 MEV EMPIRE - CONNECTION TEST")
    print("🧪" * 30)
    print("🌐 Starting simple test server...")
    print("📊 Test URL: http://127.0.0.1:5003")
    print("🔍 Verifying browser connectivity...")
    
    app.run(host='0.0.0.0', port=5003, debug=False)
