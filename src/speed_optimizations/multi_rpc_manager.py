#!/usr/bin/env python3
"""
🚀 PHASE 1 SPEED OPTIMIZATION: MULTI-RPC MANAGER
Parallel RPC calls for 2-5x faster blockchain interactions
"""

import asyncio
import aiohttp
import time
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from web3 import Web3
from web3.providers import HTTPProvider
import json

logger = logging.getLogger(__name__)

@dataclass
class RPCEndpoint:
    """RPC endpoint configuration"""
    name: str
    url: str
    priority: int  # Lower = higher priority
    latency: float = 0.0
    success_rate: float = 1.0
    last_used: float = 0.0
    failures: int = 0
    max_failures: int = 3

class MultiRPCManager:
    """
    🚀 MULTI-RPC MANAGER FOR MAXIMUM SPEED
    
    Features:
    - Parallel RPC calls to multiple endpoints
    - Automatic failover and load balancing
    - Latency tracking and optimization
    - Success rate monitoring
    - Smart endpoint selection
    """
    
    def __init__(self, chain_name: str):
        self.chain_name = chain_name
        self.endpoints: List[RPCEndpoint] = []
        self.web3_instances: Dict[str, Web3] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Performance tracking
        self.total_calls = 0
        self.successful_calls = 0
        self.average_latency = 0.0
        
        # Load RPC endpoints for the chain
        self._load_rpc_endpoints()
        
    def _load_rpc_endpoints(self):
        """Load RPC endpoints for the specified chain"""
        
        # Get API key from environment
        alchemy_key = os.getenv('ALCHEMY_API_KEY', '')

        rpc_configs = {
            'arbitrum': [
                RPCEndpoint("arbitrum_official", "https://arb1.arbitrum.io/rpc", 1),
                RPCEndpoint("llamarpc", "https://arbitrum.llamarpc.com", 2),
                RPCEndpoint("blockpi", "https://arbitrum.blockpi.network/v1/rpc/public", 3),
                RPCEndpoint("ankr", "https://rpc.ankr.com/arbitrum", 4),
            ],
            'base': [
                RPCEndpoint("base_official", "https://mainnet.base.org", 1),
                RPCEndpoint("llamarpc", "https://base.llamarpc.com", 2),
                RPCEndpoint("blockpi", "https://base.blockpi.network/v1/rpc/public", 3),
                RPCEndpoint("ankr", "https://rpc.ankr.com/base", 4),
            ],
            'optimism': [
                RPCEndpoint("optimism_official", "https://mainnet.optimism.io", 1),
                RPCEndpoint("llamarpc", "https://optimism.llamarpc.com", 2),
                RPCEndpoint("blockpi", "https://optimism.blockpi.network/v1/rpc/public", 3),
                RPCEndpoint("ankr", "https://rpc.ankr.com/optimism", 4),
            ]
        }

        # Add Alchemy endpoints if API key is available
        if alchemy_key:
            rpc_configs['arbitrum'].insert(0,
                RPCEndpoint("alchemy", f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_key}", 0))
            rpc_configs['base'].insert(0,
                RPCEndpoint("alchemy", f"https://base-mainnet.g.alchemy.com/v2/{alchemy_key}", 0))
            rpc_configs['optimism'].insert(0,
                RPCEndpoint("alchemy", f"https://opt-mainnet.g.alchemy.com/v2/{alchemy_key}", 0))
        
        if self.chain_name in rpc_configs:
            self.endpoints = rpc_configs[self.chain_name]
            logger.info(f"🔗 Loaded {len(self.endpoints)} RPC endpoints for {self.chain_name}")
        else:
            raise ValueError(f"Unsupported chain: {self.chain_name}")
        
        # Initialize Web3 instances
        for endpoint in self.endpoints:
            try:
                self.web3_instances[endpoint.name] = Web3(HTTPProvider(endpoint.url))
                logger.info(f"✅ Connected to {endpoint.name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to connect to {endpoint.name}: {e}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5.0),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=20)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def get_fastest_endpoints(self, count: int = 3) -> List[RPCEndpoint]:
        """Get the fastest available endpoints"""
        
        # Filter out failed endpoints
        available = [ep for ep in self.endpoints if ep.failures < ep.max_failures]
        
        if not available:
            # Reset all endpoints if none available
            for ep in self.endpoints:
                ep.failures = 0
            available = self.endpoints
        
        # Sort by latency and success rate
        available.sort(key=lambda ep: (ep.latency, -ep.success_rate, ep.priority))
        
        return available[:count]
    
    async def parallel_rpc_call(self, method: str, params: List = None, timeout: float = 3.0) -> Any:
        """
        🚀 PARALLEL RPC CALL - FASTEST RESPONSE WINS!
        
        Sends the same RPC call to multiple endpoints simultaneously
        Returns the first successful response
        """
        
        if params is None:
            params = []
        
        fastest_endpoints = self.get_fastest_endpoints(3)  # Use top 3 endpoints
        
        if not fastest_endpoints:
            raise Exception("No available RPC endpoints")
        
        # Create tasks for parallel execution
        tasks = []
        for endpoint in fastest_endpoints:
            task = asyncio.create_task(
                self._single_rpc_call(endpoint, method, params, timeout)
            )
            tasks.append((task, endpoint))
        
        # Wait for first successful response
        try:
            done, pending = await asyncio.wait(
                [task for task, _ in tasks],
                return_when=asyncio.FIRST_COMPLETED,
                timeout=timeout
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            # Get the first successful result
            for task in done:
                try:
                    result = await task
                    self.successful_calls += 1
                    return result
                except Exception as e:
                    logger.debug(f"RPC call failed: {e}")
                    continue
            
            raise Exception("All RPC calls failed")
            
        except asyncio.TimeoutError:
            # Cancel all tasks
            for task, _ in tasks:
                task.cancel()
            raise Exception(f"RPC call timeout after {timeout}s")
        
        finally:
            self.total_calls += 1
    
    async def _single_rpc_call(self, endpoint: RPCEndpoint, method: str, params: List, timeout: float) -> Any:
        """Execute a single RPC call to one endpoint"""
        
        start_time = time.time()
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": 1
            }
            
            async with self.session.post(
                endpoint.url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                data = await response.json()
                
                if "error" in data:
                    raise Exception(f"RPC error: {data['error']}")
                
                # Update endpoint performance metrics
                latency = time.time() - start_time
                endpoint.latency = (endpoint.latency * 0.9) + (latency * 0.1)  # Moving average
                endpoint.last_used = time.time()
                endpoint.failures = max(0, endpoint.failures - 1)  # Decay failures
                
                return data["result"]
                
        except Exception as e:
            # Update failure metrics
            endpoint.failures += 1
            endpoint.success_rate = max(0.1, endpoint.success_rate * 0.95)  # Decay success rate
            
            logger.debug(f"RPC call to {endpoint.name} failed: {e}")
            raise e
    
    async def get_latest_block(self) -> int:
        """Get latest block number using fastest endpoint"""
        result = await self.parallel_rpc_call("eth_blockNumber")
        return int(result, 16)
    
    async def get_balance(self, address: str) -> int:
        """Get ETH balance using fastest endpoint"""
        result = await self.parallel_rpc_call("eth_getBalance", [address, "latest"])
        return int(result, 16)
    
    async def call_contract(self, to: str, data: str) -> str:
        """Call contract using fastest endpoint"""
        params = [{
            "to": to,
            "data": data
        }, "latest"]
        return await self.parallel_rpc_call("eth_call", params)
    
    async def send_transaction(self, signed_tx: str) -> str:
        """Send transaction using fastest endpoint"""
        return await self.parallel_rpc_call("eth_sendRawTransaction", [signed_tx])
    
    async def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict]:
        """Get transaction receipt using fastest endpoint"""
        try:
            return await self.parallel_rpc_call("eth_getTransactionReceipt", [tx_hash])
        except:
            return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        
        success_rate = (self.successful_calls / max(1, self.total_calls)) * 100
        
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "success_rate": f"{success_rate:.1f}%",
            "average_latency": f"{self.average_latency:.3f}s",
            "endpoints": [
                {
                    "name": ep.name,
                    "latency": f"{ep.latency:.3f}s",
                    "success_rate": f"{ep.success_rate:.1f}",
                    "failures": ep.failures
                }
                for ep in self.endpoints
            ]
        }
    
    def print_performance_stats(self):
        """Print performance statistics"""
        
        stats = self.get_performance_stats()
        
        print(f"\n🚀 MULTI-RPC PERFORMANCE STATS ({self.chain_name.upper()})")
        print("=" * 50)
        print(f"📊 Total calls: {stats['total_calls']}")
        print(f"✅ Success rate: {stats['success_rate']}")
        print(f"⚡ Average latency: {stats['average_latency']}")
        print("\n📡 Endpoint Performance:")
        
        for ep_stats in stats['endpoints']:
            print(f"   {ep_stats['name']}: {ep_stats['latency']} latency, "
                  f"{ep_stats['success_rate']} success, {ep_stats['failures']} failures")


# Example usage
async def test_multi_rpc():
    """Test the multi-RPC manager"""
    
    async with MultiRPCManager("arbitrum") as rpc:
        
        print("🚀 Testing Multi-RPC Manager...")
        
        # Test parallel calls
        start_time = time.time()
        
        tasks = [
            rpc.get_latest_block(),
            rpc.get_balance("0x55e701F8f224Dfd080924cf30FFDa42aff6467B1"),
            rpc.get_latest_block(),
        ]
        
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        print(f"⚡ Completed 3 parallel calls in {elapsed:.3f}s")
        print(f"📦 Latest block: {results[0]}")
        print(f"💰 Wallet balance: {results[1] / 1e18:.6f} ETH")
        
        # Print performance stats
        rpc.print_performance_stats()


if __name__ == "__main__":
    asyncio.run(test_multi_rpc())
