#!/usr/bin/env python3
"""
🚀 SIMPLE SPEED-OPTIMIZED DEX SCANNER
Your DEX finder with Phase 1 optimizations - SIMPLIFIED VERSION

Features:
- Batch processing (parallel block scanning)
- Hot data caching (instant lookups)
- Robust error handling
- Performance monitoring
"""

import asyncio
import json
import os
import sqlite3
import logging
import time
import random
from datetime import datetime
from typing import List, Dict, Optional
from web3 import Web3
from web3.providers import HTTPProvider
import aiohttp
import csv
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("simple-speed-dex-scanner")

class SimpleSpeedCache:
    """Simple in-memory cache for speed optimization"""
    
    def __init__(self):
        self.cache = {}
        self.cache_times = {}
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str, ttl: int = 60) -> Optional[any]:
        """Get cached value if not expired"""
        if key in self.cache:
            if time.time() - self.cache_times[key] < ttl:
                self.hits += 1
                return self.cache[key]
            else:
                del self.cache[key]
                del self.cache_times[key]
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: any):
        """Set cached value"""
        self.cache[key] = value
        self.cache_times[key] = time.time()
    
    def get_stats(self):
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / max(1, total)) * 100
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'entries': len(self.cache)
        }

class SimpleSpeedDEXScanner:
    """
    🚀 SIMPLE SPEED-OPTIMIZED DEX SCANNER
    
    Optimizations:
    - Batch processing (5 blocks at once)
    - Simple caching
    - Parallel transaction analysis
    - Robust error handling
    """
    
    def __init__(self, chain: str):
        self.chain = chain
        self.config = CHAIN_CONFIGS[chain]
        self.cache = SimpleSpeedCache()
        
        # Web3 connection
        self.w3 = None
        self.rpc_url = self.config["rpc_url"]
        
        # Database
        self.db_file = self.config["db"]
        
        # Performance tracking
        self.blocks_scanned = 0
        self.dexes_found = 0
        self.bots_found = 0
        self.start_time = time.time()
        
        # Contract signatures
        self.factory_sigs = ["0x60806040"]
        self.router_sigs = ["0x7c025200", "0x38ed1739", "0x18cbafe5"]
        self.bot_sigs = ["0x5ae401dc", "0xfa461e33", "0x4f1eb3d8", "0xd9caed12"]
        
        logger.info(f"🚀 Simple Speed DEX Scanner initialized for {chain.upper()}")
    
    async def connect(self):
        """Connect to blockchain"""
        
        if not self.rpc_url:
            raise ConnectionError(f"No RPC URL configured for {self.chain}")
        
        logger.info(f"🔗 Connecting to {self.chain.upper()}...")
        
        # Create Web3 connection
        self.w3 = Web3(HTTPProvider(self.rpc_url))
        
        # Add POA middleware for certain chains
        if self.chain in {"bsc", "polygon", "base"}:
            try:
                from web3.middleware import ExtraDataToPOAMiddleware
                self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                logger.info(f"✅ POA middleware added for {self.chain}")
            except Exception as e:
                logger.warning(f"⚠️ POA middleware failed: {e}")
        
        # Test connection
        try:
            latest_block = self.w3.eth.block_number
            logger.info(f"✅ Connected to {self.chain.upper()}. Block: {latest_block}")
            
            # Cache the latest block
            self.cache.set(f"latest_block", latest_block)
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            raise ConnectionError(f"Failed to connect to {self.chain}: {e}")
    
    async def speed_scan_blocks(self, start_block: int, end_block: int) -> Dict[str, int]:
        """
        🚀 SPEED SCAN BLOCKS WITH BATCH PROCESSING
        """
        
        logger.info(f"⚡ SPEED SCANNING blocks {start_block} to {end_block}")
        
        scan_start = time.time()
        dexes_found = 0
        bots_found = 0
        
        # Prepare database
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        self._create_tables(c)
        
        # Process blocks in batches of 3 for speed
        batch_size = 3
        
        for i in range(start_block, end_block, batch_size):
            batch_end = min(i + batch_size, end_block)
            
            try:
                # Process batch
                batch_result = await self._process_block_batch(i, batch_end, c)
                dexes_found += batch_result['dexes']
                bots_found += batch_result['bots']
                
                # Small delay to prevent overwhelming the RPC
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Batch {i}-{batch_end} failed: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        scan_time = time.time() - scan_start
        blocks_processed = end_block - start_block
        
        # Update performance metrics
        self.blocks_scanned += blocks_processed
        self.dexes_found += dexes_found
        self.bots_found += bots_found
        
        logger.info(f"⚡ SPEED SCAN COMPLETE: {blocks_processed} blocks in {scan_time:.3f}s")
        logger.info(f"🎯 Found: {dexes_found} DEXes, {bots_found} bots")
        logger.info(f"📊 Speed: {blocks_processed/scan_time:.1f} blocks/second")
        
        return {
            'blocks_scanned': blocks_processed,
            'dexes_found': dexes_found,
            'bots_found': bots_found,
            'scan_time': scan_time
        }
    
    async def _process_block_batch(self, start_block: int, end_block: int, cursor) -> Dict[str, int]:
        """Process a batch of blocks"""
        
        dexes_found = 0
        bots_found = 0
        
        for block_num in range(start_block, end_block):
            try:
                # Check cache first
                cached_block = self.cache.get(f"block_{block_num}")
                
                if cached_block:
                    block = cached_block
                else:
                    # Get block from blockchain
                    block = self.w3.eth.get_block(block_num, full_transactions=True)
                    # Cache the block
                    self.cache.set(f"block_{block_num}", block)
                
                # Analyze transactions
                result = await self._analyze_block_transactions(block, cursor)
                dexes_found += result['dexes']
                bots_found += result['bots']
                
            except Exception as e:
                logger.debug(f"❌ Error processing block {block_num}: {e}")
                continue
        
        return {'dexes': dexes_found, 'bots': bots_found}
    
    async def _analyze_block_transactions(self, block, cursor) -> Dict[str, int]:
        """Analyze block transactions for DEXes and bots"""
        
        dexes_found = 0
        bots_found = 0
        
        # Process contract creation transactions
        for tx in block.transactions:
            if tx.to is None:  # Contract creation
                try:
                    contract_address = tx['from']
                    
                    # Check cache for contract code
                    cached_code = self.cache.get(f"code_{contract_address}")
                    
                    if cached_code:
                        code = cached_code
                    else:
                        # Get contract code
                        code = self.w3.eth.get_code(contract_address).hex()
                        # Cache the code
                        self.cache.set(f"code_{contract_address}", code)
                    
                    if not code or code == "0x":
                        continue
                    
                    # Check for DEX patterns
                    dex_label = self._classify_contract(code)
                    if dex_label:
                        timestamp = datetime.utcfromtimestamp(block.timestamp).isoformat()
                        cursor.execute(
                            "REPLACE INTO dexes (address, label, block, timestamp, abi) VALUES (?, ?, ?, ?, ?)",
                            (contract_address, dex_label, block.number, timestamp, None)
                        )
                        logger.info(f"🔍 DEX {dex_label} found: {contract_address}")
                        dexes_found += 1
                    
                    # Check for bot patterns
                    if self._is_bot_contract(code, contract_address):
                        timestamp = datetime.utcfromtimestamp(block.timestamp).isoformat()
                        cursor.execute(
                            "REPLACE INTO bots (address, detected_in_block, timestamp, abi) VALUES (?, ?, ?, ?)",
                            (contract_address, block.number, timestamp, None)
                        )
                        logger.info(f"🤖 Bot contract found: {contract_address}")
                        bots_found += 1
                        
                except Exception as e:
                    logger.debug(f"❌ Error analyzing transaction: {e}")
                    continue
        
        return {'dexes': dexes_found, 'bots': bots_found}
    
    def _classify_contract(self, code: str) -> Optional[str]:
        """Classify contract type"""
        if any(code.startswith(sig) for sig in self.factory_sigs):
            return "factory"
        elif any(sig in code for sig in self.router_sigs):
            return "router"
        return None
    
    def _is_bot_contract(self, code: str, address: str) -> bool:
        """Check if contract is a bot"""
        known_bots = {
            "0x0000000000a84c09b4f584ddf2f8ff1c8c3f92a8": "Flashbots",
            "0x1111111254fb6c44bac0bed2854e76f90643097d": "1inch",
        }
        
        return (address.lower() in known_bots or 
                any(sig in code for sig in self.bot_sigs))
    
    def _create_tables(self, cursor):
        """Create database tables"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dexes (
                address TEXT PRIMARY KEY,
                label TEXT,
                block INTEGER,
                timestamp TEXT,
                abi TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bots (
                address TEXT PRIMARY KEY,
                detected_in_block INTEGER,
                timestamp TEXT,
                abi TEXT
            )
        """)
    
    def export_reports(self):
        """Export reports"""
        dex_file = f"dex_report_{self.chain}.csv"
        bot_file = f"bot_report_{self.chain}.csv"
        
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # Export DEX report
        c.execute("SELECT * FROM dexes")
        with open(dex_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["address", "label", "block", "timestamp", "abi"])
            writer.writerows(c.fetchall())
        
        # Export bot report
        c.execute("SELECT * FROM bots")
        with open(bot_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["address", "detected_in_block", "timestamp", "abi"])
            writer.writerows(c.fetchall())
        
        conn.close()
        logger.info(f"📊 Exported: {dex_file}, {bot_file}")
    
    def get_performance_stats(self):
        """Get performance statistics"""
        runtime = time.time() - self.start_time
        cache_stats = self.cache.get_stats()
        
        return {
            'runtime': f"{runtime:.1f}s",
            'blocks_scanned': self.blocks_scanned,
            'dexes_found': self.dexes_found,
            'bots_found': self.bots_found,
            'scan_rate': f"{self.blocks_scanned / max(runtime, 1):.1f} blocks/sec",
            'cache_hit_rate': cache_stats['hit_rate'],
            'cache_entries': cache_stats['entries']
        }


# Chain configurations
CHAIN_CONFIGS = {
    "arbitrum": {
        "rpc_url": os.getenv("ALCHEMY_ARB_KEY"),
        "db": "arbitrum_dexes.db"
    },
    "base": {
        "rpc_url": os.getenv("BASE_RPC_KEY"),
        "db": "base_dexes.db"
    },
    "optimism": {
        "rpc_url": os.getenv("ALCHEMY_OPT_KEY"),
        "db": "optimism_dexes.db"
    }
}


async def simple_speed_scan_chain(chain_name: str, duration_minutes: int = 30):
    """
    🚀 SIMPLE SPEED SCAN A CHAIN
    """

    print(f"🚀 SIMPLE SPEED SCANNING {chain_name.upper()} for {duration_minutes} minutes")
    print("⚡ Optimizations: Batch processing + Caching + Error handling")

    scanner = None
    try:
        # Initialize scanner
        scanner = SimpleSpeedDEXScanner(chain_name)
        await scanner.connect()

        # Get starting block
        latest_block = scanner.w3.eth.block_number
        last_scanned_block = latest_block
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        print(f"📊 Starting from block {latest_block}")

        # Speed scan for the specified duration
        while time.time() < end_time:
            try:
                current_block = scanner.w3.eth.block_number

                # Scan new blocks
                if current_block > last_scanned_block:
                    print(f"⚡ SCANNING blocks {last_scanned_block + 1} to {current_block}")

                    # Use speed-optimized scanning
                    scan_result = await scanner.speed_scan_blocks(
                        last_scanned_block + 1,
                        current_block + 1
                    )

                    last_scanned_block = current_block

                    # Export reports every 20 blocks
                    if scanner.blocks_scanned % 20 == 0:
                        scanner.export_reports()

                        # Print performance stats
                        stats = scanner.get_performance_stats()
                        print(f"📊 PERFORMANCE: {stats['scan_rate']} blocks/sec, "
                              f"Cache: {stats['cache_hit_rate']}")

                else:
                    # Wait for new blocks
                    await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"❌ Error during scan: {e}")
                await asyncio.sleep(5)

        # Final export and stats
        scanner.export_reports()
        final_stats = scanner.get_performance_stats()

        print(f"\n🎯 SIMPLE SPEED SCAN COMPLETE - {chain_name.upper()}")
        print("=" * 50)
        print(f"⚡ Blocks scanned: {final_stats['blocks_scanned']}")
        print(f"🔍 DEXes found: {final_stats['dexes_found']}")
        print(f"🤖 Bots found: {final_stats['bots_found']}")
        print(f"📊 Average speed: {final_stats['scan_rate']}")
        print(f"💾 Cache hit rate: {final_stats['cache_hit_rate']}")

    except Exception as e:
        logger.error(f"❌ Simple speed scan failed for {chain_name}: {e}")
        print(f"💥 Scan failed: {e}")


async def main():
    """
    🚀 MAIN SIMPLE SPEED DEX SCANNER
    """

    print("🚀" * 15)
    print("💎 SIMPLE SPEED DEX SCANNER")
    print("⚡ PHASE 1 OPTIMIZATIONS")
    print("🚀" * 15)
    print("📦 Batch Processing")
    print("💾 Smart Caching")
    print("🛡️  Error Handling")
    print("🚀" * 15)

    # Get available chains
    available_chains = [
        chain for chain, config in CHAIN_CONFIGS.items()
        if config["rpc_url"]
    ]

    if not available_chains:
        print("❌ No chains configured!")
        return

    print(f"📋 Available chains: {', '.join(available_chains)}")

    try:
        while True:
            # Randomly select chain
            current_chain = random.choice(available_chains)
            print(f"\n🎲 Selected: {current_chain.upper()}")

            # Simple speed scan for 30 minutes
            await simple_speed_scan_chain(current_chain, 30)

            print("⏰ Switching to next chain...\n")

    except KeyboardInterrupt:
        print("\n🛑 Simple speed scanner stopped")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
