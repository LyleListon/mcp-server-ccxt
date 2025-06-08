#!/usr/bin/env python3
"""
🚀 MEV EMPIRE DEPLOYMENT SCRIPT
Deploy your MEV strategies with automatic node detection and fallback

Features:
- Auto-detect your Ethereum node
- Fallback to public RPCs if node not ready
- Environment setup and validation
- Strategy configuration
- Live deployment with monitoring
"""

import asyncio
import logging
import os
import sys
import json
import time
from typing import Dict, Optional
import requests
from web3 import Web3
from web3.providers import HTTPProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

class MEVEmpireDeployer:
    """
    🚀 MEV EMPIRE DEPLOYMENT MANAGER
    """
    
    def __init__(self):
        self.ethereum_node_url = None
        self.w3 = None
        self.account_address = None
        self.deployment_config = {}
        
    async def deploy_mev_empire(self):
        """
        🚀 DEPLOY YOUR MEV EMPIRE!
        """
        
        print("🚀" * 30)
        print("💎 MEV EMPIRE DEPLOYMENT")
        print("🚀" * 30)
        
        try:
            # Step 1: Environment Setup
            await self._setup_environment()
            
            # Step 2: Node Detection
            await self._detect_ethereum_node()
            
            # Step 3: Wallet Validation
            await self._validate_wallet()
            
            # Step 4: Strategy Configuration
            await self._configure_strategies()
            
            # Step 5: Deploy Empire
            await self._deploy_empire()
            
        except Exception as e:
            logger.error(f"💥 Deployment failed: {e}")
            print(f"\n❌ DEPLOYMENT FAILED: {e}")
            return False
        
        return True
    
    async def _setup_environment(self):
        """Setup environment and check dependencies"""
        
        print("\n📋 STEP 1: ENVIRONMENT SETUP")
        print("=" * 40)
        
        # Check Python version
        python_version = sys.version_info
        print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        if python_version < (3, 8):
            raise Exception("Python 3.8+ required")
        
        # Check required packages
        required_packages = ['web3', 'asyncio', 'aiohttp']
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package} installed")
            except ImportError:
                print(f"❌ {package} missing - install with: pip install {package}")
                raise Exception(f"Missing package: {package}")
        
        # Check environment variables
        env_vars = {
            'PRIVATE_KEY': 'Your wallet private key',
            'ALCHEMY_API_KEY': 'Alchemy API key (optional)',
            'ETHEREUM_NODE_URL': 'Your Ethereum node URL (optional)'
        }
        
        print(f"\n🔐 Environment Variables:")
        for var, description in env_vars.items():
            value = os.getenv(var)
            if value:
                if var == 'PRIVATE_KEY':
                    print(f"✅ {var}: {'*' * 20}")
                else:
                    print(f"✅ {var}: {value[:20]}...")
            else:
                print(f"⚠️ {var}: Not set ({description})")
        
        print("✅ Environment setup complete")
    
    async def _detect_ethereum_node(self):
        """Detect and connect to Ethereum node"""
        
        print("\n🔗 STEP 2: ETHEREUM NODE DETECTION")
        print("=" * 40)
        
        # Try custom node URL first
        custom_url = os.getenv('ETHEREUM_NODE_URL')
        if custom_url:
            print(f"🎯 Trying custom node: {custom_url}")
            if await self._test_node_connection(custom_url):
                self.ethereum_node_url = custom_url
                print(f"✅ Connected to your custom Ethereum node!")
                return
        
        # Try common local node URLs
        local_urls = [
            'http://localhost:8545',
            'http://127.0.0.1:8545',
            'ws://localhost:8546',
            'ws://127.0.0.1:8546'
        ]
        
        print("🔍 Scanning for local Ethereum node...")
        for url in local_urls:
            print(f"   Testing {url}...")
            if await self._test_node_connection(url):
                self.ethereum_node_url = url
                print(f"✅ Found your Ethereum node: {url}")
                return
        
        # Fallback to public RPCs
        print("⚠️ No local Ethereum node found")
        print("🔄 Falling back to public RPCs...")
        
        alchemy_key = os.getenv('ALCHEMY_API_KEY')
        if alchemy_key:
            alchemy_url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_key}"
            print(f"🎯 Trying Alchemy: {alchemy_url[:50]}...")
            if await self._test_node_connection(alchemy_url):
                self.ethereum_node_url = alchemy_url
                print("✅ Connected to Alchemy")
                return
        
        # Try free public RPCs
        public_rpcs = [
            'https://eth.llamarpc.com',
            'https://ethereum.blockpi.network/v1/rpc/public',
            'https://rpc.ankr.com/eth'
        ]
        
        for url in public_rpcs:
            print(f"   Testing {url}...")
            if await self._test_node_connection(url):
                self.ethereum_node_url = url
                print(f"✅ Connected to public RPC: {url}")
                return
        
        raise Exception("❌ Could not connect to any Ethereum node!")
    
    async def _test_node_connection(self, url: str) -> bool:
        """Test connection to an Ethereum node"""
        
        try:
            if url.startswith('http'):
                # Test HTTP connection
                response = requests.post(
                    url,
                    json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'result' in data:
                        block_number = int(data['result'], 16)
                        print(f"      📦 Latest block: {block_number}")
                        return True
            else:
                # Test WebSocket connection (simplified)
                return False  # Skip WebSocket testing for now
                
        except Exception as e:
            print(f"      ❌ Failed: {e}")
            return False
        
        return False
    
    async def _validate_wallet(self):
        """Validate wallet and check balance"""
        
        print("\n💰 STEP 3: WALLET VALIDATION")
        print("=" * 40)
        
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            raise Exception("❌ PRIVATE_KEY environment variable not set!")
        
        # Connect to Ethereum
        self.w3 = Web3(HTTPProvider(self.ethereum_node_url))
        
        # Load account
        account = self.w3.eth.account.from_key(private_key)
        self.account_address = account.address
        
        # Check balance
        balance_wei = self.w3.eth.get_balance(self.account_address)
        balance_eth = balance_wei / 1e18
        
        print(f"🔑 Wallet address: {self.account_address}")
        print(f"💰 ETH balance: {balance_eth:.6f} ETH")
        
        # Check if we have enough ETH for gas
        if balance_eth < 0.01:  # 0.01 ETH minimum
            print("⚠️ WARNING: Low ETH balance for gas fees!")
        else:
            print("✅ Sufficient ETH for gas fees")
        
        # Get current gas price
        gas_price_wei = self.w3.eth.gas_price
        gas_price_gwei = gas_price_wei / 1e9
        print(f"⛽ Current gas price: {gas_price_gwei:.1f} Gwei")
        
        print("✅ Wallet validation complete")
    
    async def _configure_strategies(self):
        """Configure MEV strategies"""
        
        print("\n🎯 STEP 4: STRATEGY CONFIGURATION")
        print("=" * 40)
        
        # Get current gas price for strategy configuration
        gas_price_gwei = self.w3.eth.gas_price / 1e9
        
        # Configure strategies based on current conditions
        self.deployment_config = {
            'liquidation': {
                'enabled': True,
                'min_profit_usd': 50.0,
                'max_gas_gwei': min(200.0, gas_price_gwei * 3),  # Adaptive gas limit
                'priority': 1
            },
            'flashloan_arbitrage': {
                'enabled': True,
                'min_profit_usd': 10.0,
                'max_gas_gwei': min(150.0, gas_price_gwei * 2),
                'priority': 2
            },
            'frontrun_frontrunners': {
                'enabled': gas_price_gwei < 100,  # Only enable if gas is reasonable
                'min_profit_usd': 25.0,
                'max_gas_gwei': min(300.0, gas_price_gwei * 4),
                'priority': 3
            }
        }
        
        print("🎯 Strategy Configuration:")
        for strategy, config in self.deployment_config.items():
            status = "✅ ENABLED" if config['enabled'] else "❌ DISABLED"
            print(f"   {strategy}: {status}")
            if config['enabled']:
                print(f"      Min profit: ${config['min_profit_usd']}")
                print(f"      Max gas: {config['max_gas_gwei']:.1f} Gwei")
        
        print("✅ Strategy configuration complete")
    
    async def _deploy_empire(self):
        """Deploy the MEV Empire"""
        
        print("\n🚀 STEP 5: MEV EMPIRE DEPLOYMENT")
        print("=" * 40)
        
        # Create deployment environment file
        env_content = f"""# MEV Empire Environment Configuration
ETHEREUM_NODE_URL={self.ethereum_node_url}
PRIVATE_KEY={os.getenv('PRIVATE_KEY', '')}
ALCHEMY_API_KEY={os.getenv('ALCHEMY_API_KEY', '')}

# Strategy Configuration
LIQUIDATION_ENABLED={self.deployment_config['liquidation']['enabled']}
LIQUIDATION_MIN_PROFIT={self.deployment_config['liquidation']['min_profit_usd']}
LIQUIDATION_MAX_GAS={self.deployment_config['liquidation']['max_gas_gwei']}

FLASHLOAN_ENABLED={self.deployment_config['flashloan_arbitrage']['enabled']}
FLASHLOAN_MIN_PROFIT={self.deployment_config['flashloan_arbitrage']['min_profit_usd']}
FLASHLOAN_MAX_GAS={self.deployment_config['flashloan_arbitrage']['max_gas_gwei']}

FRONTRUN_ENABLED={self.deployment_config['frontrun_frontrunners']['enabled']}
FRONTRUN_MIN_PROFIT={self.deployment_config['frontrun_frontrunners']['min_profit_usd']}
FRONTRUN_MAX_GAS={self.deployment_config['frontrun_frontrunners']['max_gas_gwei']}
"""
        
        # Save configuration
        with open('.env.mev_empire', 'w') as f:
            f.write(env_content)
        
        print("✅ Environment configuration saved to .env.mev_empire")
        
        # Create deployment summary
        deployment_summary = {
            'deployment_time': time.time(),
            'ethereum_node_url': self.ethereum_node_url,
            'wallet_address': self.account_address,
            'strategies': self.deployment_config,
            'network': 'ethereum_mainnet'
        }
        
        with open('mev_empire_deployment.json', 'w') as f:
            json.dump(deployment_summary, f, indent=2)
        
        print("✅ Deployment summary saved to mev_empire_deployment.json")
        
        print("\n🎉 MEV EMPIRE READY FOR LAUNCH!")
        print("=" * 40)
        print("🚀 To start your MEV Empire, run:")
        print("   python ethereum_node_master.py")
        print("")
        print("📊 Your strategies:")
        enabled_strategies = [name for name, config in self.deployment_config.items() if config['enabled']]
        for i, strategy in enumerate(enabled_strategies, 1):
            print(f"   {i}. {strategy.replace('_', ' ').title()}")
        
        print(f"\n💰 Wallet: {self.account_address}")
        print(f"🔗 Node: {self.ethereum_node_url}")
        print(f"⛽ Gas limit: {max(config['max_gas_gwei'] for config in self.deployment_config.values()):.1f} Gwei")


async def main():
    """
    🚀 MAIN DEPLOYMENT FUNCTION
    """
    
    deployer = MEVEmpireDeployer()
    
    try:
        success = await deployer.deploy_mev_empire()
        
        if success:
            print("\n🎉 DEPLOYMENT SUCCESSFUL!")
            print("🚀 Your MEV Empire is ready to launch!")
            
            # Ask if user wants to start immediately
            response = input("\n🚀 Start MEV Empire now? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                print("\n🚀 Launching MEV Empire...")
                os.system("python ethereum_node_master.py")
        else:
            print("\n❌ DEPLOYMENT FAILED!")
            
    except KeyboardInterrupt:
        print("\n🛑 Deployment cancelled by user")
    except Exception as e:
        print(f"\n💥 Deployment error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
