#!/usr/bin/env python3
"""
Multi-Chain Configuration
=========================

Configuration for deploying flashloan contracts across multiple chains.
Supports Arbitrum, Optimism, and Base for maximum arbitrage coverage.
"""

# Multi-chain configuration for flashloan arbitrage
CHAIN_CONFIGS = {
    'arbitrum': {
        'chain_id': 42161,
        'name': 'Arbitrum One',
        'rpc_url': 'https://arb-mainnet.g.alchemy.com/v2/',
        'aave_address_provider': '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
        'tokens': {
            'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
            'USDC': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
            'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
            'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'
        },
        'dex_routers': {
            'sushiswap': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
            'camelot': '0xc873fEcbd354f5A56E00E710B90EF4201db2448d',
            'uniswap_v3': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
            'balancer': '0xBA12222222228d8Ba445958a75a0704d566BF2C8'
        },
        'block_explorer': 'https://arbiscan.io',
        'gas_price_gwei': 0.1,
        'deployment_gas_limit': 4000000
    },
    
    'optimism': {
        'chain_id': 10,
        'name': 'Optimism',
        'rpc_url': 'https://opt-mainnet.g.alchemy.com/v2/',
        'aave_address_provider': '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
        'tokens': {
            'WETH': '0x4200000000000000000000000000000000000006',
            'USDC': '0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85',
            'USDT': '0x94b008aA00579c1307B0EF2c499aD98a8ce58e58',
            'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'
        },
        'dex_routers': {
            'uniswap_v3': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
            'velodrome': '0xa062aE8A9c5e11aaA026fc2670B0D65cCc8B2858',
            'balancer': '0xBA12222222228d8Ba445958a75a0704d566BF2C8',
            'sushiswap': '0x4C5D5234f232BD2D76B96aA33F5AE4FCF0E4BFaB'
        },
        'block_explorer': 'https://optimistic.etherscan.io',
        'gas_price_gwei': 0.001,  # Very low on Optimism
        'deployment_gas_limit': 4000000
    },
    
    'base': {
        'chain_id': 8453,
        'name': 'Base',
        'rpc_url': 'https://base-mainnet.g.alchemy.com/v2/',
        'aave_address_provider': '0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D',
        'tokens': {
            'WETH': '0x4200000000000000000000000000000000000006',
            'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
            'DAI': '0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb',
            'USDT': '0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2'
        },
        'dex_routers': {
            'uniswap_v3': '0x2626664c2603336E57B271c5C0b26F421741e481',
            'aerodrome': '0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43',
            'balancer': '0xBA12222222228d8Ba445958a75a0704d566BF2C8',
            'sushiswap': '0x6BDED42c6DA8FBf0d2bA55B2fa120C5e0c8D7891'
        },
        'block_explorer': 'https://basescan.org',
        'gas_price_gwei': 0.001,  # Very low on Base
        'deployment_gas_limit': 4000000
    }
}

def get_chain_config(chain_name: str) -> dict:
    """Get configuration for a specific chain."""
    if chain_name not in CHAIN_CONFIGS:
        raise ValueError(f"Unsupported chain: {chain_name}")
    return CHAIN_CONFIGS[chain_name]

def get_all_chains() -> list:
    """Get list of all supported chains."""
    return list(CHAIN_CONFIGS.keys())

def get_rpc_url(chain_name: str, api_key: str) -> str:
    """Get full RPC URL for a chain."""
    config = get_chain_config(chain_name)
    return f"{config['rpc_url']}{api_key}"

def get_contract_addresses(chain_name: str) -> dict:
    """Get contract addresses for a chain."""
    config = get_chain_config(chain_name)
    return {
        'aave_address_provider': config['aave_address_provider'],
        'tokens': config['tokens'],
        'dex_routers': config['dex_routers']
    }

def get_deployment_params(chain_name: str) -> dict:
    """Get deployment parameters for a chain."""
    config = get_chain_config(chain_name)
    return {
        'gas_price_gwei': config['gas_price_gwei'],
        'gas_limit': config['deployment_gas_limit'],
        'chain_id': config['chain_id']
    }

# Flashloan provider priorities by chain
FLASHLOAN_PRIORITIES = {
    'arbitrum': ['aave', 'balancer', 'dydx'],
    'optimism': ['aave', 'balancer'],
    'base': ['aave', 'balancer']
}

# DEX priorities by chain (for arbitrage)
DEX_PRIORITIES = {
    'arbitrum': ['sushiswap', 'camelot', 'uniswap_v3'],
    'optimism': ['uniswap_v3', 'velodrome', 'sushiswap'],
    'base': ['uniswap_v3', 'aerodrome', 'sushiswap']
}

# Minimum profit thresholds by chain (in USD)
MIN_PROFIT_THRESHOLDS = {
    'arbitrum': 0.25,  # Higher gas costs
    'optimism': 0.10,  # Lower gas costs
    'base': 0.10       # Lower gas costs
}

# Maximum flashloan amounts by chain and token
MAX_FLASHLOAN_AMOUNTS = {
    'arbitrum': {
        'USDC': 10000000,  # $10M
        'WETH': 5000,      # 5000 ETH
        'USDT': 10000000,  # $10M
        'DAI': 10000000    # $10M
    },
    'optimism': {
        'USDC': 5000000,   # $5M
        'WETH': 2500,      # 2500 ETH
        'USDT': 5000000,   # $5M
        'DAI': 5000000     # $5M
    },
    'base': {
        'USDC': 5000000,   # $5M
        'WETH': 2500,      # 2500 ETH
        'DAI': 5000000,    # $5M
        'USDT': 5000000    # $5M
    }
}

if __name__ == "__main__":
    print("🌐 MULTI-CHAIN FLASHLOAN CONFIGURATION")
    print("=" * 45)
    
    for chain_name in get_all_chains():
        config = get_chain_config(chain_name)
        print(f"\n🔗 {config['name']} (Chain ID: {config['chain_id']})")
        print(f"   📍 Aave Provider: {config['aave_address_provider']}")
        print(f"   💰 Tokens: {len(config['tokens'])}")
        print(f"   🔄 DEXes: {len(config['dex_routers'])}")
        print(f"   ⛽ Gas Price: {config['gas_price_gwei']} gwei")
        print(f"   🔍 Explorer: {config['block_explorer']}")
