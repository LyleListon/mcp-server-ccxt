#!/usr/bin/env python3
"""
Comprehensive WSL2 networking diagnostic
"""

import subprocess
import socket
import requests
import time
import os

def run_command(cmd):
    """Run a command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)

def test_basic_connectivity():
    """Test basic network connectivity."""
    print("🔍 BASIC CONNECTIVITY TEST")
    print("=" * 40)
    
    # Test DNS resolution
    print("📡 DNS Resolution:")
    code, out, err = run_command("nslookup google.com")
    if code == 0:
        print("   ✅ DNS working")
    else:
        print(f"   ❌ DNS failed: {err}")
    
    # Test ping
    print("🏓 Ping Test:")
    code, out, err = run_command("ping -c 3 8.8.8.8")
    if code == 0:
        print("   ✅ Ping working")
    else:
        print(f"   ❌ Ping failed: {err}")
    
    # Test HTTP
    print("🌐 HTTP Test:")
    try:
        response = requests.get("http://httpbin.org/ip", timeout=5)
        print(f"   ✅ HTTP working: {response.status_code}")
    except Exception as e:
        print(f"   ❌ HTTP failed: {e}")
    
    # Test HTTPS
    print("🔒 HTTPS Test:")
    try:
        response = requests.get("https://httpbin.org/ip", timeout=5)
        print(f"   ✅ HTTPS working: {response.status_code}")
    except Exception as e:
        print(f"   ❌ HTTPS failed: {e}")

def test_blockchain_rpcs():
    """Test specific blockchain RPC endpoints."""
    print("\n🔗 BLOCKCHAIN RPC TEST")
    print("=" * 40)
    
    rpcs = [
        ("Ethereum Public", "https://ethereum.publicnode.com"),
        ("Arbitrum Public", "https://arbitrum.public-rpc.com"),
        ("Base Public", "https://mainnet.base.org"),
    ]
    
    for name, url in rpcs:
        print(f"🔍 Testing {name}:")
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_chainId",
                "params": [],
                "id": 1
            }
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                result = response.json()
                chain_id = result.get('result', 'unknown')
                print(f"   ✅ Working: Chain ID {chain_id}")
            else:
                print(f"   ❌ Failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")

def test_local_network():
    """Test local network connectivity."""
    print("\n🏠 LOCAL NETWORK TEST")
    print("=" * 40)
    
    # Test local Ethereum node
    print("🔍 Testing local Ethereum node:")
    local_ips = ["192.168.1.18", "localhost", "127.0.0.1"]
    
    for ip in local_ips:
        print(f"   Testing {ip}:8545...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((ip, 8545))
            sock.close()
            
            if result == 0:
                print(f"   ✅ {ip}:8545 reachable")
                # Try actual RPC call
                try:
                    payload = {
                        "jsonrpc": "2.0",
                        "method": "eth_chainId",
                        "params": [],
                        "id": 1
                    }
                    response = requests.post(f"http://{ip}:8545", json=payload, timeout=3)
                    if response.status_code == 200:
                        result = response.json()
                        chain_id = result.get('result', 'unknown')
                        print(f"   ✅ RPC working: Chain ID {chain_id}")
                    else:
                        print(f"   ⚠️  Port open but RPC failed: {response.status_code}")
                except Exception as e:
                    print(f"   ⚠️  Port open but RPC failed: {e}")
            else:
                print(f"   ❌ {ip}:8545 not reachable")
        except Exception as e:
            print(f"   ❌ {ip}:8545 error: {e}")

def test_wsl2_config():
    """Check WSL2 configuration."""
    print("\n⚙️  WSL2 CONFIGURATION")
    print("=" * 40)
    
    # Check WSL version
    print("📋 WSL Info:")
    code, out, err = run_command("wsl --version")
    if code == 0:
        print(f"   {out}")
    else:
        print(f"   ❌ WSL version check failed")
    
    # Check network interfaces
    print("🌐 Network Interfaces:")
    code, out, err = run_command("ip addr show")
    if code == 0:
        lines = out.split('\n')
        for line in lines:
            if 'inet ' in line and ('eth0' in line or 'wsl' in line):
                print(f"   {line.strip()}")
    
    # Check routing
    print("🛣️  Routing Table:")
    code, out, err = run_command("ip route show")
    if code == 0:
        print(f"   {out}")
    
    # Check DNS
    print("📡 DNS Config:")
    try:
        with open('/etc/resolv.conf', 'r') as f:
            dns_config = f.read().strip()
            print(f"   {dns_config}")
    except Exception as e:
        print(f"   ❌ Can't read DNS config: {e}")

def main():
    """Run comprehensive networking diagnostic."""
    print("🔍 WSL2 NETWORKING DIAGNOSTIC")
    print("=" * 60)
    print("Diagnosing why Web3 connections are failing...")
    print()
    
    test_basic_connectivity()
    test_blockchain_rpcs()
    test_local_network()
    test_wsl2_config()
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSTIC COMPLETE")
    print("Check the results above to identify the networking issue.")

if __name__ == "__main__":
    main()
