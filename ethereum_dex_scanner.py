#!/usr/bin/env python3
"""
🔍 DUAL-CHAIN DEX SCANNER
Ethereum + Base blockchain DEX discovery for your MEV Empire

Features:
- Continuous Ethereum + Base scanning
- Real-time DEX discovery and verification
- Integration with your local nodes
- Automatic database updates for MEV strategies
- Bot detection for frontrunning intelligence
- Parallel chain monitoring for maximum coverage
"""

import asyncio
import json
import os
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional
from web3 import Web3
import time
import requests
import aiohttp
import csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("ethereum-dex-scanner")

class DualChainDEXScanner:
    """
    🔍 DUAL-CHAIN DEX SCANNER

    Dedicated scanner for Ethereum + Base DEX discovery and MEV bot hunting
    """

    def __init__(self):
        # Your local nodes - NO STATIC VALUES, get from environment
        self.ethereum_node_url = os.getenv('ETHEREUM_NODE_URL', 'http://192.168.1.18:8545')
        self.base_node_url = os.getenv('BASE_NODE_URL', 'http://192.168.1.18:8546')  # Update with your Base node

        # API keys for ABI fetching
        self.etherscan_api_key = os.getenv('ETHERSCAN_API_KEY', '')
        self.basescan_api_key = os.getenv('BASESCAN_API_KEY', '')

        # Database files for each chain
        self.ethereum_db = 'ethereum_dexes.db'
        self.base_db = 'base_dexes.db'

        # Web3 connections
        self.ethereum_w3 = None
        self.base_w3 = None
        
        # DEX detection signatures
        self.factory_signatures = [
            "0x60806040",  # Standard factory bytecode
            "0x608060405234801561001057600080fd5b50",  # Common factory pattern
        ]
        
        self.router_signatures = [
            "0x7c025200",  # swapExactETHForTokens
            "0x38ed1739",  # swapExactTokensForTokens
            "0x18cbafe5",  # swapExactTokensForETH
            "0x5ae401dc",  # multicall (Uniswap V3)
            "0xfa461e33",  # exactInputSingle (Uniswap V3)
            "0x414bf389",  # exactOutputSingle (Uniswap V3)
        ]
        
        # Known MEV bot signatures for frontrunning intelligence
        self.mev_bot_signatures = [
            "0x5ae401dc",  # multicall
            "0xfa461e33",  # exactInputSingle
            "0x4f1eb3d8",  # MEV bot pattern
            "0xd9caed12",  # flashLoan (Aave)
            "0x13e7c9d8",  # flashLoan (Balancer)
            "0x1ccceae1",  # flashLoan (dYdX)
        ]
        
        # Known MEV bot addresses
        self.known_mev_bots = {
            "0x0000000000a84c09b4f584ddf2f8ff1c8c3f92a8": "Flashbots Searcher",
            "0x1111111254fb6c44bac0bed2854e76f90643097d": "1inch Aggregator",
            "0x2222222222222222222222222222222222222222": "Generic MEV Bot",
            "0x3333333333333333333333333333333333333333": "Sandwich Bot",
        }
        
        logger.info("🔍 Ethereum DEX Scanner initialized")
    
    async def connect(self):
        """Connect to Ethereum node"""
        
        logger.info(f"🔗 Connecting to Ethereum node: {self.ethereum_node_url}")
        
        try:
            self.ethereum_w3 = Web3(Web3.HTTPProvider(self.ethereum_node_url, request_kwargs={'timeout': 10}))

            # Test connection
            if self.ethereum_w3.is_connected():
                latest_block = self.ethereum_w3.eth.block_number
                logger.info(f"✅ Connected to Ethereum. Latest block: {latest_block:,}")
                return True
            else:
                raise ConnectionError("Failed to connect to Ethereum node")
                
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            
            # Fallback to public RPC
            logger.info("🔄 Trying fallback public RPC...")
            try:
                fallback_url = "https://eth.llamarpc.com"
                self.ethereum_w3 = Web3(Web3.HTTPProvider(fallback_url, request_kwargs={'timeout': 10}))

                if self.ethereum_w3.is_connected():
                    latest_block = self.ethereum_w3.eth.block_number
                    logger.info(f"✅ Connected to fallback RPC. Latest block: {latest_block:,}")
                    return True
                else:
                    raise ConnectionError("Fallback RPC also failed")
                    
            except Exception as fallback_error:
                logger.error(f"❌ Fallback connection failed: {fallback_error}")
                raise
    
    def setup_database(self):
        """Setup SQLite database for DEX storage"""

        conn = sqlite3.connect(self.ethereum_db)
        c = conn.cursor()
        
        # DEXes table
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
        
        # MEV bots table
        c.execute("""
            CREATE TABLE IF NOT EXISTS mev_bots (
                address TEXT PRIMARY KEY,
                detected_in_block INTEGER,
                timestamp TEXT,
                abi TEXT,
                bot_type TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("📁 Database setup complete")
    
    async def scan_blocks(self, start_block: int, end_block: int):
        """Scan Ethereum blocks for DEX contracts"""
        
        logger.info(f"🔍 Scanning Ethereum blocks {start_block:,} to {end_block:,}")
        
        conn = sqlite3.connect(self.ethereum_db)
        c = conn.cursor()
        
        dexes_found = 0
        bots_found = 0
        
        for block_num in range(start_block, end_block):
            try:
                block = self.ethereum_w3.eth.get_block(block_num, full_transactions=True)
                
                for tx in block.transactions:
                    if tx.to is None:  # Contract creation transaction
                        # Get the transaction receipt to find the actual contract address
                        try:
                            receipt = self.ethereum_w3.eth.get_transaction_receipt(tx['hash'])
                            contract_address = receipt.contractAddress
                            if not contract_address:
                                continue  # Skip if no contract was created
                        except Exception as e:
                            logger.debug(f"Failed to get receipt for tx {tx['hash'].hex()}: {e}")
                            continue
                        
                        try:
                            # Get contract code
                            code = self.ethereum_w3.eth.get_code(contract_address).hex()
                            
                            # Check for DEX patterns
                            dex_type = self._identify_dex_type(code)
                            if dex_type:
                                abi = await self._fetch_abi(contract_address)
                                protocol = self._identify_protocol(code, abi)
                                
                                c.execute("""
                                    REPLACE INTO dexes (address, label, block, timestamp, abi, protocol, type) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    contract_address,
                                    dex_type,
                                    block.number,
                                    datetime.utcfromtimestamp(block.timestamp).isoformat(),
                                    abi,
                                    protocol,
                                    dex_type
                                ))
                                
                                dexes_found += 1
                                logger.info(f"🎯 DEX found: {dex_type} at {contract_address} (block {block.number:,})")
                            
                            # Check for MEV bot patterns
                            bot_type = self._identify_mev_bot(contract_address, code)
                            if bot_type:
                                abi = await self._fetch_abi(contract_address)
                                
                                c.execute("""
                                    REPLACE INTO mev_bots (address, detected_in_block, timestamp, abi, bot_type) 
                                    VALUES (?, ?, ?, ?, ?)
                                """, (
                                    contract_address,
                                    block.number,
                                    datetime.utcfromtimestamp(block.timestamp).isoformat(),
                                    abi,
                                    bot_type
                                ))
                                
                                bots_found += 1
                                logger.info(f"🤖 MEV Bot found: {bot_type} at {contract_address} (block {block.number:,})")
                                
                        except Exception as e:
                            logger.debug(f"Error processing contract {contract_address}: {e}")
                            continue
                
            except Exception as e:
                logger.error(f"Error scanning block {block_num}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        if dexes_found > 0 or bots_found > 0:
            logger.info(f"✅ Scan complete: {dexes_found} DEXes, {bots_found} MEV bots found")
    
    def _identify_dex_type(self, code: str) -> Optional[str]:
        """Identify DEX type from contract code"""
        
        if any(code.startswith(sig) for sig in self.factory_signatures):
            return "factory"
        elif any(sig in code for sig in self.router_signatures):
            return "router"
        
        return None
    
    def _identify_protocol(self, code: str, abi: Optional[str]) -> str:
        """Identify DEX protocol from code and ABI"""
        
        if abi:
            abi_lower = abi.lower()
            if "uniswap" in abi_lower:
                if "v3" in abi_lower or "exactinputsingle" in abi_lower:
                    return "uniswap_v3"
                else:
                    return "uniswap_v2"
            elif "sushiswap" in abi_lower or "sushi" in abi_lower:
                return "sushiswap"
            elif "balancer" in abi_lower:
                return "balancer"
            elif "curve" in abi_lower:
                return "curve"
            elif "1inch" in abi_lower:
                return "1inch"
        
        # Fallback to code analysis
        if "exactInputSingle" in code:
            return "uniswap_v3"
        elif "swapExactTokensForTokens" in code:
            return "uniswap_v2"
        
        return "unknown"
    
    def _identify_mev_bot(self, address: str, code: str) -> Optional[str]:
        """Identify MEV bot type"""
        
        # Check known addresses
        if address.lower() in self.known_mev_bots:
            return self.known_mev_bots[address.lower()]
        
        # Check code signatures
        if any(sig in code for sig in self.mev_bot_signatures):
            return "mev_bot"
        
        return None
    
    async def _fetch_abi(self, address: str) -> Optional[str]:
        """Fetch contract ABI from Etherscan"""
        
        if not self.etherscan_api_key:
            return None
        
        url = f"https://api.etherscan.io/api?module=contract&action=getabi&address={address}&apikey={self.etherscan_api_key}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == '1':
                            return data['result']
        except Exception as e:
            logger.debug(f"ABI fetch failed for {address}: {e}")
        
        return None
    
    def export_reports(self):
        """Export DEX and bot reports"""
        
        # Export DEX report
        conn = sqlite3.connect(self.ethereum_db)
        c = conn.cursor()
        
        c.execute("SELECT * FROM dexes")
        dex_rows = c.fetchall()
        
        with open("ethereum_dex_report.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["address", "label", "block", "timestamp", "abi", "protocol", "type"])
            writer.writerows(dex_rows)
        
        # Export MEV bot report
        c.execute("SELECT * FROM mev_bots")
        bot_rows = c.fetchall()
        
        with open("ethereum_mev_bot_report.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["address", "detected_in_block", "timestamp", "abi", "bot_type"])
            writer.writerows(bot_rows)
        
        conn.close()
        
        logger.info(f"📊 Exported reports: {len(dex_rows)} DEXes, {len(bot_rows)} MEV bots")
    
    async def continuous_scan(self):
        """Continuous Ethereum scanning - FRESH BLOCKS FIRST"""

        logger.info("🚀 Starting continuous Ethereum DEX scanning...")

        # Get LATEST block - NO STATIC VALUES
        latest_block = self.ethereum_w3.eth.block_number
        last_scanned_block = latest_block

        logger.info(f"📊 Starting from LATEST block {latest_block:,} (FRESH INTEL)")
        logger.info("🎯 Prioritizing new blocks for real-time frontrunning opportunities")

        while True:
            try:
                current_block = self.ethereum_w3.eth.block_number

                # Scan ONLY new blocks for fresh intel
                if current_block > last_scanned_block:
                    logger.info(f"� FRESH BLOCKS: {last_scanned_block + 1:,} to {current_block:,}")
                    await self.scan_blocks(last_scanned_block + 1, current_block + 1)
                    last_scanned_block = current_block

                    # Export reports every 5 blocks for faster updates
                    if current_block % 5 == 0:
                        self.export_reports()

                # Faster polling for fresh blocks - SPEED OPTIMIZATION
                await asyncio.sleep(6)  # Check every 6 seconds for new blocks
                
            except KeyboardInterrupt:
                logger.info("🛑 Scanner stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Scanning error: {e}")
                await asyncio.sleep(30)  # Wait before retrying


async def main():
    """
    🔍 MAIN ETHEREUM DEX SCANNER
    """
    
    print("🔍" * 30)
    print("🔍 ETHEREUM DEX SCANNER")
    print("🔍 Dedicated Ethereum Mainnet Discovery")
    print("🔍" * 30)
    
    scanner = DualChainDEXScanner()
    
    try:
        # Connect to Ethereum
        await scanner.connect()
        
        # Setup database
        scanner.setup_database()
        
        # Start continuous scanning
        await scanner.continuous_scan()
        
    except KeyboardInterrupt:
        print("\n🛑 Ethereum DEX Scanner stopped by user")
    except Exception as e:
        logger.error(f"💥 Scanner failed: {e}")
        print(f"💥 Scanner failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
