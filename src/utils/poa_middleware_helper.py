#!/usr/bin/env python3
"""
🔧 POA MIDDLEWARE HELPER
Utility to automatically configure POA middleware for chains that need it.
"""

import logging
from typing import Dict, Set
from web3 import Web3

logger = logging.getLogger(__name__)

# Chains that require POA middleware
POA_CHAINS: Set[str] = {
    'bsc',           # Binance Smart Chain
    'polygon',       # Polygon (Matic)
    'linea',         # Linea
    'mantle',        # Mantle Network
    'scroll',        # Scroll
    'base',          # Base (Coinbase L2)
    'avalanche',     # Avalanche C-Chain
    'fantom',        # Fantom
    'harmony',       # Harmony
    'moonbeam',      # Moonbeam
    'moonriver',     # Moonriver
    'celo',          # Celo
    'gnosis',        # Gnosis Chain (xDai)
    'aurora',        # Aurora (NEAR)
    'cronos',        # Cronos
    'evmos',         # Evmos
    'kava',          # Kava
    'metis',         # Metis
    'boba',          # Boba Network
    'fuse',          # Fuse Network
    'palm',          # Palm Network
    'theta',         # Theta Network
    'klaytn',        # Klaytn
    'oasis',         # Oasis Network
    'velas',         # Velas
    'wanchain',      # Wanchain
    'tomochain',     # TomoChain
    'heco',          # Huobi ECO Chain
    'okexchain',     # OKEx Chain
    'energyweb',     # Energy Web Chain
    'rsk',           # RSK
    'thundercore',   # ThunderCore
    'iotex',         # IoTeX
    'elastos',       # Elastos
    'gochain',       # GoChain
    'callisto',      # Callisto Network
    'poa',           # POA Network
    'sokol',         # Sokol Testnet
    'xdai',          # xDai (now Gnosis)
    'lukso',         # LUKSO
    'neon',          # Neon EVM
    'milkomeda',     # Milkomeda
    'godwoken',      # Godwoken
    'syscoin',       # Syscoin NEVM
    'flare',         # Flare Network
    'songbird',      # Songbird
    'step',          # Step Network
    'rei',           # REI Network
    'shiden',        # Shiden Network
    'astar',         # Astar Network
}

def is_poa_chain(chain_name: str) -> bool:
    """Check if a chain requires POA middleware."""
    return chain_name.lower() in POA_CHAINS

def inject_poa_middleware(web3_instance: Web3, chain_name: str) -> bool:
    """
    Inject POA middleware into a Web3 instance if needed.
    
    Args:
        web3_instance: Web3 instance to configure
        chain_name: Name of the blockchain
        
    Returns:
        bool: True if middleware was injected, False otherwise
    """
    if not is_poa_chain(chain_name):
        return False
    
    try:
        from web3.middleware import geth_poa_middleware
        
        # Check if middleware is already injected
        middleware_names = [str(middleware) for middleware in web3_instance.middleware_onion]
        if any('geth_poa_middleware' in name for name in middleware_names):
            logger.debug(f"POA middleware already present for {chain_name}")
            return True
        
        # Inject POA middleware
        web3_instance.middleware_onion.inject(geth_poa_middleware, layer=0)
        logger.info(f"✅ POA middleware injected for {chain_name}")
        return True
        
    except ImportError:
        logger.warning(f"⚠️ POA middleware not available for {chain_name}")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to inject POA middleware for {chain_name}: {e}")
        return False

def create_web3_connection(rpc_url: str, chain_name: str) -> Web3:
    """
    Create a Web3 connection with automatic POA middleware injection.
    
    Args:
        rpc_url: RPC endpoint URL
        chain_name: Name of the blockchain
        
    Returns:
        Web3: Configured Web3 instance
    """
    try:
        # Create Web3 instance
        web3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Inject POA middleware if needed
        inject_poa_middleware(web3, chain_name)
        
        # Test connection
        if web3.is_connected():
            logger.info(f"✅ Connected to {chain_name}")
            try:
                latest_block = web3.eth.get_block('latest')
                logger.info(f"   📦 Latest block: {latest_block['number']}")
            except Exception as e:
                logger.warning(f"   ⚠️ Could not fetch latest block: {e}")
        else:
            logger.error(f"❌ Failed to connect to {chain_name}")
        
        return web3
        
    except Exception as e:
        logger.error(f"❌ Error creating Web3 connection for {chain_name}: {e}")
        raise

def configure_multiple_connections(chain_configs: Dict[str, str]) -> Dict[str, Web3]:
    """
    Configure multiple Web3 connections with automatic POA middleware.
    
    Args:
        chain_configs: Dict mapping chain names to RPC URLs
        
    Returns:
        Dict[str, Web3]: Configured Web3 connections
    """
    connections = {}
    
    for chain_name, rpc_url in chain_configs.items():
        try:
            connections[chain_name] = create_web3_connection(rpc_url, chain_name)
        except Exception as e:
            logger.error(f"Failed to configure {chain_name}: {e}")
            continue
    
    logger.info(f"✅ Configured {len(connections)}/{len(chain_configs)} chain connections")
    return connections

def get_chain_info(chain_name: str) -> Dict[str, any]:
    """Get information about a specific chain."""
    chain_info = {
        'name': chain_name,
        'requires_poa': is_poa_chain(chain_name),
        'consensus': 'Proof of Authority' if is_poa_chain(chain_name) else 'Proof of Stake/Work'
    }
    
    # Add specific chain details
    chain_details = {
        'bsc': {
            'full_name': 'Binance Smart Chain',
            'chain_id': 56,
            'native_token': 'BNB',
            'block_time': 3
        },
        'polygon': {
            'full_name': 'Polygon',
            'chain_id': 137,
            'native_token': 'MATIC',
            'block_time': 2
        },
        'linea': {
            'full_name': 'Linea',
            'chain_id': 59144,
            'native_token': 'ETH',
            'block_time': 12
        },
        'mantle': {
            'full_name': 'Mantle Network',
            'chain_id': 5000,
            'native_token': 'MNT',
            'block_time': 2
        },
        'scroll': {
            'full_name': 'Scroll',
            'chain_id': 534352,
            'native_token': 'ETH',
            'block_time': 3
        },
        'base': {
            'full_name': 'Base',
            'chain_id': 8453,
            'native_token': 'ETH',
            'block_time': 2
        },
        'avalanche': {
            'full_name': 'Avalanche C-Chain',
            'chain_id': 43114,
            'native_token': 'AVAX',
            'block_time': 2
        },
        'arbitrum': {
            'full_name': 'Arbitrum One',
            'chain_id': 42161,
            'native_token': 'ETH',
            'block_time': 0.25
        },
        'optimism': {
            'full_name': 'Optimism',
            'chain_id': 10,
            'native_token': 'ETH',
            'block_time': 2
        }
    }
    
    if chain_name in chain_details:
        chain_info.update(chain_details[chain_name])
    
    return chain_info

def diagnose_connection_issues(web3_instance: Web3, chain_name: str) -> Dict[str, any]:
    """Diagnose common Web3 connection issues."""
    diagnosis = {
        'chain': chain_name,
        'connected': False,
        'poa_required': is_poa_chain(chain_name),
        'poa_middleware_present': False,
        'latest_block': None,
        'issues': [],
        'recommendations': []
    }
    
    try:
        # Check connection
        diagnosis['connected'] = web3_instance.is_connected()
        if not diagnosis['connected']:
            diagnosis['issues'].append('Web3 not connected to RPC endpoint')
            diagnosis['recommendations'].append('Check RPC URL and network connectivity')
        
        # Check POA middleware
        middleware_names = [str(middleware) for middleware in web3_instance.middleware_onion]
        diagnosis['poa_middleware_present'] = any('geth_poa_middleware' in name for name in middleware_names)
        
        if diagnosis['poa_required'] and not diagnosis['poa_middleware_present']:
            diagnosis['issues'].append('POA middleware required but not present')
            diagnosis['recommendations'].append('Inject geth_poa_middleware')
        
        # Test block fetching
        if diagnosis['connected']:
            try:
                latest_block = web3_instance.eth.get_block('latest')
                diagnosis['latest_block'] = latest_block['number']
            except Exception as e:
                diagnosis['issues'].append(f'Cannot fetch latest block: {e}')
                if 'extraData' in str(e) and 'POA' in str(e):
                    diagnosis['recommendations'].append('Add POA middleware to handle POA chain blocks')
    
    except Exception as e:
        diagnosis['issues'].append(f'Diagnosis error: {e}')
    
    return diagnosis

# Example usage and testing
async def test_poa_connections():
    """Test POA middleware with various chains."""
    
    print("🔧 POA MIDDLEWARE TESTING")
    print("=" * 40)
    
    # Test chain configurations
    test_configs = {
        'linea': 'https://rpc.linea.build',
        'base': 'https://mainnet.base.org',
        'polygon': 'https://polygon-rpc.com',
        'bsc': 'https://bsc-dataseed.binance.org'
    }
    
    for chain_name, rpc_url in test_configs.items():
        print(f"\n🔗 Testing {chain_name}...")
        
        try:
            # Get chain info
            info = get_chain_info(chain_name)
            print(f"   📋 {info.get('full_name', chain_name)}")
            print(f"   🔗 Chain ID: {info.get('chain_id', 'Unknown')}")
            print(f"   ⚡ POA Required: {'Yes' if info['requires_poa'] else 'No'}")
            
            # Test connection
            web3 = create_web3_connection(rpc_url, chain_name)
            
            # Diagnose any issues
            diagnosis = diagnose_connection_issues(web3, chain_name)
            
            if diagnosis['issues']:
                print(f"   ⚠️ Issues found:")
                for issue in diagnosis['issues']:
                    print(f"      - {issue}")
                print(f"   💡 Recommendations:")
                for rec in diagnosis['recommendations']:
                    print(f"      - {rec}")
            else:
                print(f"   ✅ All checks passed!")
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_poa_connections())
