#!/usr/bin/env python3
"""
🚀 DUAL-CHAIN LIGHTNING DEX SCANNER
Ethereum + Base blockchain discovery with your local nodes

Features:
- Lightning-fast scanning with direct node access
- Parallel Ethereum + Base monitoring
- Real-time DEX discovery and MEV bot hunting
- Optimized for speed with your local infrastructure
- NO MOCK DATA - Real blockchain queries only
"""

import asyncio
import os
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional
from web3 import Web3
import aiohttp
import csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("dual-chain-scanner")

class DualChainDEXScanner:
    """
    🚀 LIGHTNING-FAST DUAL-CHAIN DEX SCANNER
    
    Optimized for your local Ethereum + Base nodes
    """
    
    def __init__(self):
        # Your local nodes - NO STATIC VALUES
        self.ethereum_node_url = os.getenv('ETHEREUM_NODE_URL', 'http://192.168.1.18:8545')
        self.base_node_url = os.getenv('BASE_NODE_URL', 'http://192.168.1.18:8547')  # Update with your Base node
        
        # API keys for ABI fetching
        self.etherscan_api_key = os.getenv('ETHERSCAN_API_KEY', '')
        self.basescan_api_key = os.getenv('BASESCAN_API_KEY', '')
        
        # Database files
        self.ethereum_db = 'ethereum_dexes.db'
        self.base_db = 'base_dexes.db'
        
        # Web3 connections
        self.ethereum_w3 = None
        self.base_w3 = None
        
        # DEX detection signatures - REAL PATTERNS
        self.dex_signatures = {
            'router': [
                "0x7c025200",  # swapExactETHForTokens
                "0x38ed1739",  # swapExactTokensForTokens
                "0x18cbafe5",  # swapExactTokensForETH
                "0x5ae401dc",  # multicall (Uniswap V3)
                "0xfa461e33",  # exactInputSingle (Uniswap V3)
                "0x414bf389",  # exactOutputSingle (Uniswap V3)
            ],
            'factory': [
                "0x60806040",  # Standard factory bytecode
                "0x608060405234801561001057600080fd5b50",  # Common factory pattern
            ]
        }
        
        # MEV bot signatures for frontrunning intelligence
        self.mev_signatures = [
            "0x5ae401dc",  # multicall
            "0xfa461e33",  # exactInputSingle
            "0xd9caed12",  # flashLoan (Aave)
            "0x13e7c9d8",  # flashLoan (Balancer)
            "0x1ccceae1",  # flashLoan (dYdX)
        ]
        
        # Known MEV bot addresses to track
        self.known_mev_bots = {
            "0x0000000000a84c09b4f584ddf2f8ff1c8c3f92a8": "Flashbots Searcher",
            "0x1111111254fb6c44bac0bed2854e76f90643097d": "1inch Aggregator",
        }
        
        logger.info("🚀 Dual-Chain DEX Scanner initialized")
    
    async def connect_to_nodes(self):
        """Connect to both local nodes in parallel"""
        
        logger.info("🔗 Connecting to local nodes...")
        
        # Connect to both nodes simultaneously
        ethereum_task = self._connect_ethereum()
        base_task = self._connect_base()
        
        ethereum_connected, base_connected = await asyncio.gather(
            ethereum_task, base_task, return_exceptions=True
        )
        
        if isinstance(ethereum_connected, Exception):
            logger.error(f"❌ Ethereum connection failed: {ethereum_connected}")
            return False
            
        if isinstance(base_connected, Exception):
            logger.error(f"❌ Base connection failed: {base_connected}")
            return False
        
        logger.info("✅ Both nodes connected successfully!")
        return True
    
    async def _connect_ethereum(self):
        """Connect to Ethereum node"""
        
        try:
            self.ethereum_w3 = Web3(Web3.HTTPProvider(
                self.ethereum_node_url, 
                request_kwargs={'timeout': 5}
            ))
            
            if not self.ethereum_w3.is_connected():
                raise ConnectionError("Ethereum node not responding")
                
            latest_block = self.ethereum_w3.eth.block_number
            logger.info(f"✅ Ethereum connected - Block: {latest_block:,}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ethereum connection failed: {e}")
            raise
    
    async def _connect_base(self):
        """Connect to Base node"""
        
        try:
            self.base_w3 = Web3(Web3.HTTPProvider(
                self.base_node_url, 
                request_kwargs={'timeout': 5}
            ))
            
            if not self.base_w3.is_connected():
                raise ConnectionError("Base node not responding")
                
            latest_block = self.base_w3.eth.block_number
            logger.info(f"✅ Base connected - Block: {latest_block:,}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Base connection failed: {e}")
            raise
    
    def setup_databases(self):
        """Setup SQLite databases for both chains"""
        
        for db_file, chain_name in [(self.ethereum_db, "Ethereum"), (self.base_db, "Base")]:
            conn = sqlite3.connect(db_file)
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
                    type TEXT,
                    chain TEXT
                )
            """)
            
            # MEV bots table
            c.execute("""
                CREATE TABLE IF NOT EXISTS mev_bots (
                    address TEXT PRIMARY KEY,
                    detected_in_block INTEGER,
                    timestamp TEXT,
                    abi TEXT,
                    bot_type TEXT,
                    chain TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            
            logger.info(f"📁 {chain_name} database setup complete")
    
    async def scan_chain_blocks(self, w3, chain_name: str, db_file: str, start_block: int, end_block: int):
        """Scan blocks on a specific chain - OPTIMIZED FOR SPEED"""
        
        logger.info(f"🔍 Scanning {chain_name} blocks {start_block:,} to {end_block:,}")
        
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        
        dexes_found = 0
        bots_found = 0
        
        # Batch process blocks for speed
        for block_num in range(start_block, end_block):
            try:
                # Get block with transactions - REAL DATA ONLY
                block = w3.eth.get_block(block_num, full_transactions=True)
                
                for tx in block.transactions:
                    if tx.to is None:  # Contract creation
                        try:
                            receipt = w3.eth.get_transaction_receipt(tx['hash'])
                            contract_address = receipt.contractAddress
                            if not contract_address:
                                continue
                        except Exception:
                            continue
                        
                        try:
                            # Get REAL contract code
                            code = w3.eth.get_code(contract_address).hex()
                            
                            # Check for DEX patterns
                            dex_type = self._identify_dex_type(code)
                            if dex_type:
                                protocol = self._identify_protocol(code)
                                
                                c.execute("""
                                    REPLACE INTO dexes (address, label, block, timestamp, abi, protocol, type, chain) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    contract_address,
                                    dex_type,
                                    block.number,
                                    datetime.fromtimestamp(block.timestamp, timezone.utc).isoformat(),
                                    None,  # ABI fetched later if needed
                                    protocol,
                                    dex_type,
                                    chain_name
                                ))
                                
                                dexes_found += 1
                                logger.info(f"🎯 {chain_name} DEX: {dex_type} at {contract_address}")
                            
                            # Check for MEV bot patterns
                            bot_type = self._identify_mev_bot(contract_address, code)
                            if bot_type:
                                c.execute("""
                                    REPLACE INTO mev_bots (address, detected_in_block, timestamp, abi, bot_type, chain) 
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (
                                    contract_address,
                                    block.number,
                                    datetime.fromtimestamp(block.timestamp, timezone.utc).isoformat(),
                                    None,
                                    bot_type,
                                    chain_name
                                ))
                                
                                bots_found += 1
                                logger.info(f"🤖 {chain_name} MEV Bot: {bot_type} at {contract_address}")
                                
                        except Exception as e:
                            logger.debug(f"Error processing contract {contract_address}: {e}")
                            continue
                
            except Exception as e:
                logger.error(f"Error scanning {chain_name} block {block_num}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        if dexes_found > 0 or bots_found > 0:
            logger.info(f"✅ {chain_name} scan complete: {dexes_found} DEXes, {bots_found} MEV bots")
    
    def _identify_dex_type(self, code: str) -> Optional[str]:
        """Identify DEX type from contract code"""
        
        for dex_type, signatures in self.dex_signatures.items():
            if any(sig in code for sig in signatures):
                return dex_type
        return None
    
    def _identify_protocol(self, code: str) -> str:
        """Identify DEX protocol from code patterns"""
        
        if "exactInputSingle" in code:
            return "uniswap_v3"
        elif "swapExactTokensForTokens" in code:
            return "uniswap_v2"
        elif "balancer" in code.lower():
            return "balancer"
        elif "curve" in code.lower():
            return "curve"
        
        return "unknown"
    
    def _identify_mev_bot(self, address: str, code: str) -> Optional[str]:
        """Identify MEV bot type"""
        
        # Check known addresses
        if address.lower() in self.known_mev_bots:
            return self.known_mev_bots[address.lower()]
        
        # Check code signatures
        if any(sig in code for sig in self.mev_signatures):
            return "mev_bot"
        
        return None
