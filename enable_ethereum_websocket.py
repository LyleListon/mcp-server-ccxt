#!/usr/bin/env python3
"""
🔌 ETHEREUM NODE WEBSOCKET ENABLEMENT GUIDE
Enable WebSocket on your Ethereum node for real-time mempool access

Features:
- Check current node configuration
- Generate WebSocket startup commands
- Test WebSocket connectivity
- Provide step-by-step instructions
"""

import asyncio
import json
import requests
import websockets
import time
from typing import Optional

class EthereumWebSocketEnabler:
    """
    🔌 ETHEREUM WEBSOCKET ENABLEMENT TOOL
    """
    
    def __init__(self, node_ip: str = "192.168.1.18"):
        self.node_ip = node_ip
        self.http_port = 8545
        self.ws_port = 8546
        self.http_url = f"http://{node_ip}:{self.http_port}"
        self.ws_url = f"ws://{node_ip}:{self.ws_port}"
    
    async def enable_websocket_guide(self):
        """
        🔌 WEBSOCKET ENABLEMENT GUIDE
        """
        
        print("🔌" * 30)
        print("🔌 ETHEREUM WEBSOCKET ENABLEMENT")
        print("🔌" * 30)
        
        # Step 1: Check current status
        print("\n📊 STEP 1: CURRENT STATUS CHECK")
        print("=" * 40)
        
        http_status = await self._test_http_connection()
        ws_status = await self._test_websocket_connection()
        
        print(f"📡 HTTP RPC ({self.http_url}): {'✅ Working' if http_status else '❌ Failed'}")
        print(f"🔌 WebSocket ({self.ws_url}): {'✅ Working' if ws_status else '❌ Not enabled'}")
        
        if ws_status:
            print("\n🎉 WebSocket is already enabled! Your MEV Empire is ready!")
            return True
        
        # Step 2: Generate enablement commands
        print("\n🔧 STEP 2: ENABLE WEBSOCKET ON YOUR NODE")
        print("=" * 40)
        
        await self._generate_enablement_commands()
        
        # Step 3: Test instructions
        print("\n🧪 STEP 3: TESTING INSTRUCTIONS")
        print("=" * 40)
        
        await self._provide_testing_instructions()
        
        return False
    
    async def _test_http_connection(self) -> bool:
        """Test HTTP RPC connection"""
        
        try:
            response = requests.post(
                self.http_url,
                json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data:
                    block = int(data['result'], 16)
                    print(f"   📦 Latest block: {block:,}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"   ❌ HTTP test failed: {e}")
            return False
    
    async def _test_websocket_connection(self) -> bool:
        """Test WebSocket connection"""
        
        try:
            async with websockets.connect(self.ws_url, timeout=5) as websocket:
                # Send a test request
                request = {
                    "jsonrpc": "2.0",
                    "method": "eth_blockNumber",
                    "params": [],
                    "id": 1
                }
                
                await websocket.send(json.dumps(request))
                response = await websocket.recv()
                data = json.loads(response)
                
                if 'result' in data:
                    block = int(data['result'], 16)
                    print(f"   📦 WebSocket block: {block:,}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"   ❌ WebSocket test failed: {e}")
            return False
    
    async def _generate_enablement_commands(self):
        """Generate commands to enable WebSocket"""
        
        print("🎯 TO ENABLE WEBSOCKET ON YOUR ETHEREUM NODE:")
        print("")
        
        # Geth commands
        print("📋 FOR GETH:")
        print("   Add these flags to your geth startup command:")
        print(f"   --ws --ws-addr 0.0.0.0 --ws-port {self.ws_port}")
        print("   --ws-api eth,net,web3,txpool,debug")
        print("   --ws-origins '*'")
        print("")
        print("   Full example:")
        print("   geth --http --http-addr 0.0.0.0 --http-port 8545 \\")
        print("        --ws --ws-addr 0.0.0.0 --ws-port 8546 \\")
        print("        --ws-api eth,net,web3,txpool,debug \\")
        print("        --ws-origins '*' \\")
        print("        --syncmode snap")
        print("")
        
        # Erigon commands
        print("📋 FOR ERIGON:")
        print("   Add these flags:")
        print(f"   --ws --ws.addr 0.0.0.0 --ws.port {self.ws_port}")
        print("   --ws.api eth,net,web3,txpool,debug")
        print("   --ws.origins '*'")
        print("")
        
        # Nethermind commands
        print("📋 FOR NETHERMIND:")
        print("   Add to config or command line:")
        print("   --JsonRpc.WebSocketsPort 8546")
        print("   --JsonRpc.EnabledModules 'Eth,Net,Web3,TxPool,Debug'")
        print("")
        
        # Docker commands
        print("📋 FOR DOCKER:")
        print("   Add port mapping: -p 8546:8546")
        print("   Example:")
        print("   docker run -p 8545:8545 -p 8546:8546 \\")
        print("     ethereum/client-go:latest \\")
        print("     --ws --ws-addr 0.0.0.0 --ws-port 8546")
        print("")
        
        # Firewall
        print("🔥 FIREWALL CONFIGURATION:")
        print("   Make sure port 8546 is open:")
        print("   sudo ufw allow 8546")
        print("   # OR for specific IP:")
        print(f"   sudo ufw allow from {self._get_local_ip()} to any port 8546")
    
    async def _provide_testing_instructions(self):
        """Provide testing instructions"""
        
        print("🧪 AFTER ENABLING WEBSOCKET:")
        print("")
        print("1. 🔄 Restart your Ethereum node with WebSocket flags")
        print("2. ⏳ Wait for it to sync (check logs)")
        print("3. 🧪 Test WebSocket connection:")
        print(f"   python -c \"import asyncio, websockets, json")
        print(f"   async def test():")
        print(f"       async with websockets.connect('{self.ws_url}') as ws:")
        print(f"           await ws.send(json.dumps({{'jsonrpc':'2.0','method':'eth_blockNumber','id':1}}))") 
        print(f"           print(await ws.recv())")
        print(f"   asyncio.run(test())\"")
        print("")
        print("4. 🚀 Run this script again to verify:")
        print("   python enable_ethereum_websocket.py")
        print("")
        print("5. 🎯 Launch your complete MEV Empire:")
        print("   python ethereum_node_master.py")
        print("")
        
        print("💡 TROUBLESHOOTING:")
        print("   • Check node logs for WebSocket startup messages")
        print("   • Verify firewall allows port 8546")
        print("   • Ensure --ws-origins '*' or specific origin")
        print("   • Try telnet 192.168.1.18 8546 to test port")
    
    def _get_local_ip(self) -> str:
        """Get local machine IP for firewall rules"""
        try:
            import socket
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except:
            return "YOUR_LOCAL_IP"
    
    async def wait_for_websocket(self, timeout: int = 300):
        """Wait for WebSocket to become available"""
        
        print(f"\n⏳ Waiting for WebSocket to become available (timeout: {timeout}s)...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if await self._test_websocket_connection():
                    print("🎉 WebSocket is now available!")
                    return True
                
                print("   ⏳ Still waiting... (checking every 10 seconds)")
                await asyncio.sleep(10)
                
            except KeyboardInterrupt:
                print("\n🛑 Waiting cancelled by user")
                return False
        
        print(f"⏰ Timeout reached. WebSocket not available after {timeout}s")
        return False


async def main():
    """
    🔌 MAIN WEBSOCKET ENABLEMENT FUNCTION
    """
    
    enabler = EthereumWebSocketEnabler()
    
    try:
        success = await enabler.enable_websocket_guide()
        
        if success:
            print("\n🎉 WEBSOCKET ALREADY ENABLED!")
            print("🚀 Your MEV Empire is ready for full deployment!")
        else:
            print("\n🔧 WEBSOCKET NEEDS TO BE ENABLED")
            print("📋 Follow the instructions above to enable WebSocket")
            
            # Ask if user wants to wait for WebSocket
            try:
                response = input("\n⏳ Wait for WebSocket to be enabled? (y/n): ").lower().strip()
                if response in ['y', 'yes']:
                    await enabler.wait_for_websocket()
            except KeyboardInterrupt:
                print("\n🛑 Cancelled by user")
        
    except Exception as e:
        print(f"\n💥 Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
