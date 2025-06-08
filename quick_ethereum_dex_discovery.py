#!/usr/bin/env python3
"""
🚀 QUICK ETHEREUM DEX DISCOVERY
Find major Ethereum DEXes in minutes, not hours!

Features:
- Known major DEX addresses
- Quick contract verification
- ABI fetching for verified contracts
- Integration with your MEV Empire
- Database creation for your scanner
"""

import asyncio
import logging
import time
import sqlite3
import json
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import aiohttp

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EthereumDEX:
    """Ethereum DEX data structure"""
    name: str
    address: str
    type: str  # router, factory, pool
    protocol: str  # uniswap_v2, uniswap_v3, etc.
    verified: bool = False
    abi: Optional[str] = None

class QuickEthereumDEXDiscovery:
    """
    🚀 QUICK ETHEREUM DEX DISCOVERY
    
    Find major Ethereum DEXes using known addresses and verification
    """
    
    def __init__(self):
        self.ethereum_node_url = "http://192.168.1.18:8545"
        self.etherscan_api_key = ""  # Will try without API key first
        
        # Major Ethereum DEXes (known addresses)
        self.known_dexes = {
            # Uniswap V2
            'uniswap_v2_router': EthereumDEX(
                name="Uniswap V2 Router",
                address="0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
                type="router",
                protocol="uniswap_v2"
            ),
            'uniswap_v2_factory': EthereumDEX(
                name="Uniswap V2 Factory",
                address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
                type="factory",
                protocol="uniswap_v2"
            ),
            
            # Uniswap V3
            'uniswap_v3_router': EthereumDEX(
                name="Uniswap V3 Router",
                address="0xE592427A0AEce92De3Edee1F18E0157C05861564",
                type="router",
                protocol="uniswap_v3"
            ),
            'uniswap_v3_factory': EthereumDEX(
                name="Uniswap V3 Factory",
                address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
                type="factory",
                protocol="uniswap_v3"
            ),
            'uniswap_v3_router_v2': EthereumDEX(
                name="Uniswap V3 Router V2",
                address="0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
                type="router",
                protocol="uniswap_v3"
            ),
            
            # SushiSwap
            'sushiswap_router': EthereumDEX(
                name="SushiSwap Router",
                address="0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
                type="router",
                protocol="sushiswap"
            ),
            'sushiswap_factory': EthereumDEX(
                name="SushiSwap Factory",
                address="0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac",
                type="factory",
                protocol="sushiswap"
            ),
            
            # Balancer
            'balancer_vault': EthereumDEX(
                name="Balancer Vault",
                address="0xBA12222222228d8Ba445958a75a0704d566BF2C8",
                type="vault",
                protocol="balancer"
            ),
            
            # Curve
            'curve_registry': EthereumDEX(
                name="Curve Registry",
                address="0x90E00ACe148ca3b23Ac1bC8C240C2a7Dd9c2d7f5",
                type="registry",
                protocol="curve"
            ),
            'curve_router': EthereumDEX(
                name="Curve Router",
                address="0x99a58482BD75cbab83b27EC03CA68fF489b5788f",
                type="router",
                protocol="curve"
            ),
            
            # 1inch
            'oneinch_v5_router': EthereumDEX(
                name="1inch V5 Router",
                address="0x1111111254EEB25477B68fb85Ed929f73A960582",
                type="router",
                protocol="1inch"
            ),
            
            # Pancakeswap (Ethereum)
            'pancakeswap_router': EthereumDEX(
                name="PancakeSwap Router",
                address="0xEfF92A263d31888d860bD50809A8D171709b7b1c",
                type="router",
                protocol="pancakeswap"
            ),
            
            # Shibaswap
            'shibaswap_router': EthereumDEX(
                name="ShibaSwap Router",
                address="0x03f7724180AA6b939894B5Ca4314783B0b36b329",
                type="router",
                protocol="shibaswap"
            ),
            
            # Fraxswap
            'fraxswap_router': EthereumDEX(
                name="Fraxswap Router",
                address="0xC14d550632db8592D1243Edc8B95b0Ad06703867",
                type="router",
                protocol="fraxswap"
            ),
            
            # Maverick
            'maverick_router': EthereumDEX(
                name="Maverick Router",
                address="0x32C1A6e986B8b4c2B9dC9C9bC8d3a7F8c8F8c8F8",
                type="router",
                protocol="maverick"
            ),
            
            # Kyber Network
            'kyber_router': EthereumDEX(
                name="Kyber Router",
                address="0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
                type="router",
                protocol="kyber"
            )
        }
        
        self.verified_dexes = []
        
    async def discover_ethereum_dexes(self):
        """
        🚀 DISCOVER ETHEREUM DEXES QUICKLY
        """
        
        print("🚀" * 20)
        print("🔍 QUICK ETHEREUM DEX DISCOVERY")
        print("🚀" * 20)
        
        print(f"📡 Using Ethereum node: {self.ethereum_node_url}")
        print(f"🎯 Checking {len(self.known_dexes)} known DEX addresses...")
        
        # Verify each known DEX
        for dex_id, dex in self.known_dexes.items():
            print(f"\n🔍 Checking {dex.name}...")
            
            verified = await self._verify_dex_contract(dex)
            if verified:
                self.verified_dexes.append(dex)
                print(f"   ✅ Verified: {dex.address}")
            else:
                print(f"   ❌ Failed: {dex.address}")
        
        # Create database
        await self._create_ethereum_dex_database()
        
        # Generate report
        await self._generate_discovery_report()
        
        print(f"\n🎉 DISCOVERY COMPLETE!")
        print(f"✅ Found {len(self.verified_dexes)} verified Ethereum DEXes")
        print(f"📁 Database: ethereum_dexes.db")
        print(f"📁 Report: ethereum_dex_report.json")
    
    async def _verify_dex_contract(self, dex: EthereumDEX) -> bool:
        """Verify DEX contract exists and has code"""
        
        try:
            # Check if contract has code
            response = requests.post(
                self.ethereum_node_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "eth_getCode",
                    "params": [dex.address, "latest"],
                    "id": 1
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data and data['result'] != '0x':
                    dex.verified = True
                    
                    # Try to get ABI from Etherscan
                    abi = await self._get_contract_abi(dex.address)
                    if abi:
                        dex.abi = abi
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error verifying {dex.name}: {e}")
            return False
    
    async def _get_contract_abi(self, address: str) -> Optional[str]:
        """Get contract ABI from Etherscan"""
        
        try:
            # Try without API key first
            url = f"https://api.etherscan.io/api?module=contract&action=getabi&address={address}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == '1':
                            return data['result']
        except Exception as e:
            logger.debug(f"Failed to get ABI for {address}: {e}")
        
        return None
    
    async def _create_ethereum_dex_database(self):
        """Create Ethereum DEX database"""
        
        print(f"\n📁 Creating ethereum_dexes.db...")
        
        conn = sqlite3.connect('ethereum_dexes.db')
        c = conn.cursor()
        
        # Create tables
        c.execute("""
            CREATE TABLE IF NOT EXISTS dexes (
                address TEXT PRIMARY KEY,
                label TEXT,
                block INTEGER,
                timestamp TEXT,
                abi TEXT,
                protocol TEXT,
                type TEXT
            )
        """)
        
        # Insert verified DEXes
        for dex in self.verified_dexes:
            c.execute(
                "REPLACE INTO dexes (address, label, block, timestamp, abi, protocol, type) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    dex.address,
                    dex.name,
                    0,  # Block number (not applicable for known addresses)
                    datetime.utcnow().isoformat(),
                    dex.abi,
                    dex.protocol,
                    dex.type
                )
            )
        
        conn.commit()
        conn.close()
        
        print(f"✅ Database created with {len(self.verified_dexes)} DEXes")
    
    async def _generate_discovery_report(self):
        """Generate discovery report"""
        
        report = {
            'discovery_time': datetime.utcnow().isoformat(),
            'ethereum_node': self.ethereum_node_url,
            'total_checked': len(self.known_dexes),
            'total_verified': len(self.verified_dexes),
            'dexes': []
        }
        
        # Group by protocol
        protocols = {}
        for dex in self.verified_dexes:
            if dex.protocol not in protocols:
                protocols[dex.protocol] = []
            protocols[dex.protocol].append({
                'name': dex.name,
                'address': dex.address,
                'type': dex.type,
                'has_abi': bool(dex.abi)
            })
        
        report['protocols'] = protocols
        
        # Save report
        with open('ethereum_dex_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print(f"\n📊 DISCOVERY SUMMARY:")
        print(f"=" * 40)
        for protocol, dexes in protocols.items():
            print(f"🔹 {protocol.upper()}: {len(dexes)} DEXes")
            for dex in dexes:
                abi_status = "✅ ABI" if dex['has_abi'] else "❌ No ABI"
                print(f"   • {dex['name']} ({dex['type']}) - {abi_status}")


async def main():
    """
    🚀 MAIN QUICK DISCOVERY FUNCTION
    """
    
    discovery = QuickEthereumDEXDiscovery()
    
    try:
        await discovery.discover_ethereum_dexes()
        
        print(f"\n🎯 NEXT STEPS:")
        print(f"1. ✅ Ethereum DEXes discovered and saved")
        print(f"2. 🚀 Update your MEV Empire to use these DEXes")
        print(f"3. 🔍 Start dedicated Ethereum scanning for more DEXes")
        print(f"4. 💰 Launch MEV Empire with full Ethereum coverage")
        
    except Exception as e:
        logger.error(f"💥 Discovery failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
