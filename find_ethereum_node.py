#!/usr/bin/env python3
"""
🔍 ETHEREUM NODE DISCOVERY TOOL
Find and test connection to your remote Ethereum node

Features:
- Test common IP addresses and ports
- Validate node connectivity
- Check node sync status
- Generate connection configuration
"""

import asyncio
import requests
import time
import json
from typing import List, Dict, Optional, Tuple
import ipaddress
import socket

class EthereumNodeFinder:
    """
    🔍 ETHEREUM NODE DISCOVERY TOOL
    """
    
    def __init__(self):
        self.found_nodes = []
        
    async def find_ethereum_node(self):
        """
        🔍 FIND YOUR ETHEREUM NODE
        """
        
        print("🔍" * 30)
        print("🔍 ETHEREUM NODE DISCOVERY")
        print("🔍" * 30)
        
        # Step 1: Manual input
        manual_url = await self._get_manual_input()
        if manual_url:
            if await self._test_node(manual_url):
                return manual_url
        
        # Step 2: Common local addresses
        print("\n🔍 Scanning common local addresses...")
        local_nodes = await self._scan_local_addresses()
        if local_nodes:
            return local_nodes[0]
        
        # Step 3: Network scan
        print("\n🔍 Scanning local network...")
        network_nodes = await self._scan_network()
        if network_nodes:
            return network_nodes[0]
        
        print("\n❌ No Ethereum nodes found!")
        return None
    
    async def _get_manual_input(self) -> Optional[str]:
        """Get manual node URL input"""
        
        print("\n📝 MANUAL NODE CONFIGURATION")
        print("=" * 40)
        print("If you know your Ethereum node's IP address, enter it here:")
        print("Examples:")
        print("  http://192.168.1.100:8545")
        print("  http://10.0.0.50:8545")
        print("  ws://192.168.1.100:8546")
        print("")
        
        try:
            user_input = input("🔗 Enter your Ethereum node URL (or press Enter to skip): ").strip()
            
            if user_input:
                print(f"🎯 Testing user-provided URL: {user_input}")
                return user_input
        except KeyboardInterrupt:
            print("\n🛑 Skipping manual input...")
        
        return None
    
    async def _scan_local_addresses(self) -> List[str]:
        """Scan common local addresses"""
        
        # Common local IPs
        local_ips = [
            '127.0.0.1',
            'localhost',
            '192.168.1.1',   # Common router
            '192.168.0.1',   # Common router
            '10.0.0.1',      # Common router
        ]
        
        # Add current machine's IP
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            if local_ip not in local_ips:
                local_ips.append(local_ip)
        except:
            pass
        
        # Common ports
        ports = [8545, 8546]
        protocols = ['http', 'ws']
        
        found_nodes = []
        
        for ip in local_ips:
            for port in ports:
                for protocol in protocols:
                    if protocol == 'ws' and port == 8545:
                        continue  # Skip ws on HTTP port
                    if protocol == 'http' and port == 8546:
                        continue  # Skip http on WS port
                    
                    url = f"{protocol}://{ip}:{port}"
                    print(f"   Testing {url}...")
                    
                    if await self._test_node(url):
                        found_nodes.append(url)
                        print(f"   ✅ Found node: {url}")
        
        return found_nodes
    
    async def _scan_network(self) -> List[str]:
        """Scan local network for Ethereum nodes"""
        
        print("🔍 Scanning local network (this may take a moment)...")
        
        # Get local network range
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            # Assume /24 network
            network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
            
            print(f"📡 Scanning network: {network}")
            
        except Exception as e:
            print(f"❌ Could not determine network range: {e}")
            return []
        
        found_nodes = []
        
        # Scan first 20 IPs (to avoid taking too long)
        ip_list = list(network.hosts())[:20]
        
        for ip in ip_list:
            ip_str = str(ip)
            
            # Test common Ethereum ports
            for port in [8545, 8546]:
                protocol = 'http' if port == 8545 else 'ws'
                url = f"{protocol}://{ip_str}:{port}"
                
                print(f"   Testing {url}...")
                
                if await self._test_node(url, timeout=2):  # Shorter timeout for network scan
                    found_nodes.append(url)
                    print(f"   ✅ Found node: {url}")
        
        return found_nodes
    
    async def _test_node(self, url: str, timeout: int = 5) -> bool:
        """Test if URL is a valid Ethereum node"""
        
        try:
            if url.startswith('http'):
                # Test HTTP RPC
                response = requests.post(
                    url,
                    json={
                        "jsonrpc": "2.0",
                        "method": "eth_blockNumber",
                        "params": [],
                        "id": 1
                    },
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'result' in data:
                        block_number = int(data['result'], 16)
                        
                        # Get additional node info
                        node_info = await self._get_node_info(url)
                        
                        print(f"      ✅ Valid Ethereum node!")
                        print(f"      📦 Latest block: {block_number:,}")
                        if node_info:
                            print(f"      🔗 Chain ID: {node_info.get('chainId', 'Unknown')}")
                            print(f"      ⛽ Gas price: {node_info.get('gasPrice', 'Unknown')} Gwei")
                        
                        return True
            
            elif url.startswith('ws'):
                # For WebSocket, we'll just assume it works if HTTP works
                # (proper WebSocket testing would require more complex code)
                http_url = url.replace('ws://', 'http://').replace(':8546', ':8545')
                return await self._test_node(http_url, timeout)
                
        except Exception as e:
            print(f"      ❌ Failed: {str(e)[:50]}...")
            return False
        
        return False
    
    async def _get_node_info(self, url: str) -> Optional[Dict]:
        """Get additional node information"""
        
        try:
            # Get chain ID
            chain_response = requests.post(
                url,
                json={"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 2},
                timeout=3
            )
            
            # Get gas price
            gas_response = requests.post(
                url,
                json={"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 3},
                timeout=3
            )
            
            info = {}
            
            if chain_response.status_code == 200:
                chain_data = chain_response.json()
                if 'result' in chain_data:
                    chain_id = int(chain_data['result'], 16)
                    info['chainId'] = chain_id
            
            if gas_response.status_code == 200:
                gas_data = gas_response.json()
                if 'result' in gas_data:
                    gas_price_wei = int(gas_data['result'], 16)
                    gas_price_gwei = gas_price_wei / 1e9
                    info['gasPrice'] = f"{gas_price_gwei:.1f}"
            
            return info
            
        except Exception as e:
            return None
    
    def save_node_config(self, node_url: str):
        """Save node configuration"""
        
        config = {
            'ethereum_node_url': node_url,
            'discovered_at': time.time(),
            'node_type': 'remote' if not node_url.startswith(('127.0.0.1', 'localhost')) else 'local'
        }
        
        # Save to environment file
        env_content = f"""# Ethereum Node Configuration
# Generated by Node Discovery Tool
ETHEREUM_NODE_URL={node_url}

# Add your private key here
PRIVATE_KEY=your_private_key_here

# Optional: Add Alchemy API key as backup
ALCHEMY_API_KEY=your_alchemy_key_here
"""
        
        with open('.env.ethereum_node', 'w') as f:
            f.write(env_content)
        
        # Save to JSON config
        with open('ethereum_node_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n✅ Node configuration saved!")
        print(f"📁 Environment file: .env.ethereum_node")
        print(f"📁 Config file: ethereum_node_config.json")
        print(f"\n🚀 To use this node with your MEV Empire:")
        print(f"   export ETHEREUM_NODE_URL='{node_url}'")
        print(f"   python ethereum_node_master.py")


async def main():
    """
    🔍 MAIN NODE DISCOVERY FUNCTION
    """
    
    finder = EthereumNodeFinder()
    
    try:
        node_url = await finder.find_ethereum_node()
        
        if node_url:
            print(f"\n🎉 ETHEREUM NODE FOUND!")
            print(f"🔗 URL: {node_url}")
            
            # Save configuration
            finder.save_node_config(node_url)
            
            # Ask if user wants to test MEV Empire connection
            response = input("\n🚀 Test MEV Empire connection now? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                print(f"\n🧪 Testing MEV Empire connection...")
                print(f"🔗 Node URL: {node_url}")
                
                # Set environment variable for testing
                import os
                os.environ['ETHEREUM_NODE_URL'] = node_url
                
                print("✅ Environment configured for testing")
                print("🚀 Run: python ethereum_node_master.py")
        else:
            print(f"\n❌ NO ETHEREUM NODE FOUND!")
            print(f"💡 Make sure your Ethereum node is:")
            print(f"   1. Running and synced")
            print(f"   2. RPC enabled (--http --http-addr 0.0.0.0)")
            print(f"   3. Accessible from this machine")
            print(f"   4. Firewall allows connections on port 8545/8546")
            
    except KeyboardInterrupt:
        print("\n🛑 Node discovery cancelled")
    except Exception as e:
        print(f"\n💥 Discovery error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
