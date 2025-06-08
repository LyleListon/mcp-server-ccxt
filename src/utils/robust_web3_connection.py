#!/usr/bin/env python3
"""
🔗 IMPROVED WEB3 CONNECTION HELPER
Robust connection management with proper timeouts and fallbacks.
"""

import os
from web3 import Web3
from web3.providers import HTTPProvider
import logging

logger = logging.getLogger(__name__)

def create_robust_web3_connection(network: str) -> Web3:
    """Create a robust Web3 connection with proper timeouts."""
    
    # Network configurations with multiple fallbacks
    network_configs = {
        'arbitrum': [
            f"https://arb-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}",
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum.llamarpc.com"
        ],
        'base': [
            f"https://base-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}",
            "https://mainnet.base.org",
            "https://base.llamarpc.com"
        ],
        'optimism': [
            f"https://opt-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}",
            "https://mainnet.optimism.io",
            "https://optimism.llamarpc.com"
        ]
    }
    
    if network not in network_configs:
        raise ValueError(f"Unsupported network: {network}")
    
    for rpc_url in network_configs[network]:
        try:
            # Longer timeout for reliability
            w3 = Web3(HTTPProvider(rpc_url, request_kwargs={'timeout': 30}))
            
            # Test connection
            if w3.is_connected():
                latest_block = w3.eth.block_number
                logger.info(f"✅ Connected to {network} via {rpc_url[:50]}... Block: {latest_block}")
                return w3
                
        except Exception as e:
            logger.warning(f"❌ Failed to connect to {rpc_url}: {e}")
            continue
    
    raise ConnectionError(f"Failed to connect to any {network} RPC endpoints")
