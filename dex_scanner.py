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
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("refactored-dex-scanner")

class DEXDiscovery:
    def __init__(self, chain: str):
        self.chain = chain
        self.config = CHAIN_CONFIGS[chain]
        self.api_key = os.getenv(self.config["api_key_env"], "")
        self.explorer_key = os.getenv(self.config["explorer_api_key_env"], "")
        self.rpc_url = self.config["rpc_url"]
        self.db_file = self.config["db"]
        self.explorer_url = self.config["explorer_url"]
        self.w3 = None

    async def connect(self):
        logger.info(f"Attempting to connect to {self.chain} using RPC URL: {self.rpc_url}")

        if not self.rpc_url:
            raise ConnectionError(f"No RPC URL configured for {self.chain}. Check your environment variable.")

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        # For POA chains, add the middleware if needed
        if self.chain in {"bsc", "polygon", "linea", "mantle", "scroll", "base", "avalanche", "fantom"}:
            try:
                # Use the correct POA middleware for Web3 v7+
                from web3.middleware import ExtraDataToPOAMiddleware

                # Inject the middleware directly (it's a curry object)
                self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                logger.info(f"✅ POA middleware injected for {self.chain}")

            except ImportError:
                logger.warning(f"⚠️ POA middleware not available for {self.chain}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to inject POA middleware for {self.chain}: {e}")

        # Test connection with more detailed error handling
        try:
            is_connected = self.w3.is_connected()
            if not is_connected:
                # Try a simple call to get more specific error info
                try:
                    block_number = self.w3.eth.block_number
                    logger.info(f"Connection test successful. Current block: {block_number}")
                except Exception as e:
                    logger.error(f"Connection test failed with error: {e}")
                    raise ConnectionError(f"Failed to connect to {self.chain} RPC: {e}")
            else:
                logger.info(f"Connected to {self.chain.capitalize()}. Block: {self.w3.eth.block_number}")
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise ConnectionError(f"Failed to connect to {self.chain} RPC: {e}")

    async def scan_blocks(self, start_block: int, end_block: int):
        logger.info(f"Scanning blocks {start_block} to {end_block}")
        factory_sigs = [
            "0x60806040",
        ]
        router_sigs = [
            "0x7c025200",
            "0x38ed1739",
            "0x18cbafe5",
        ]
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS dexes (
                address TEXT PRIMARY KEY,
                label TEXT,
                block INTEGER,
                timestamp TEXT,
                abi TEXT
            )
        """)

        for block_num in range(start_block, end_block):
            block = self.w3.eth.get_block(block_num, full_transactions=True)
            for tx in block.transactions:
                if tx.to is None:  # contract creation
                    code = self.w3.eth.get_code(tx['from']).hex()
                    label = None
                    if any(code.startswith(sig) for sig in factory_sigs):
                        label = "factory"
                    elif any(code.startswith(sig) for sig in router_sigs):
                        label = "router"
                    if label:
                        abi = await self.fetch_abi(tx['from'])
                        c.execute("REPLACE INTO dexes (address, label, block, timestamp, abi) VALUES (?, ?, ?, ?, ?)",
                                  (tx['from'], label, block.number, datetime.utcfromtimestamp(block.timestamp).isoformat(), abi))
                        logger.info(f"Detected {label} ({self.chain}) at {tx['from']}")
        conn.commit()
        conn.close()

    async def fetch_abi(self, address: str) -> Optional[str]:
        if not self.explorer_key:
            return None
        url = f"{self.explorer_url}?module=contract&action=getabi&address={address}&apikey={self.explorer_key}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.json()
                    if data['status'] == '1':
                        return data['result']
                    else:
                        logger.warning(f"ABI fetch failed for {address}: {data.get('result')}")
        except Exception as e:
            logger.error(f"Exception while fetching ABI: {e}")
        return None

    def export_dex_report(self):
        output_file = f"dex_report_{self.chain}.csv"
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT * FROM dexes")
        rows = c.fetchall()
        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["address", "label", "block", "timestamp", "abi"])
            writer.writerows(rows)
        conn.close()
        logger.info(f"\U0001F4C4 Exported report to {output_file}")

    def export_bot_report(self):
        output_file = f"bot_report_{self.chain}.csv"
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS bots (
                address TEXT PRIMARY KEY,
                detected_in_block INTEGER,
                timestamp TEXT,
                abi TEXT
            )
        """)
        c.execute("SELECT * FROM bots")
        rows = c.fetchall()
        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["address", "detected_in_block", "timestamp", "abi"])
            writer.writerows(rows)
        conn.close()
        logger.info(f"🤖 Exported bot report to {output_file}")

    async def scan_for_bots(self, start_block: int, end_block: int):
        known_bot_addresses = {
            "0x0000000000a84c09b4f584ddf2f8ff1c8c3f92a8": "Flashbots",
            "0x1111111254fb6c44bac0bed2854e76f90643097d": "1inch Aggregator",
            "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee": "Placeholder Bot"
        }
        flashloan_sigs = [
            "0xd9caed12",
            "0x13e7c9d8",
            "0x1ccceae1"
        ]
        logger.info(f"Scanning for bot contracts in blocks {start_block} to {end_block}")
        bot_sigs = [
            "0x5ae401dc",
            "0xfa461e33",
            "0x4f1eb3d8"
        ]
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS bots (
                address TEXT PRIMARY KEY,
                detected_in_block INTEGER,
                timestamp TEXT,
                abi TEXT
            )
        """)
        for block_num in range(start_block, end_block):
            block = self.w3.eth.get_block(block_num, full_transactions=True)
            for tx in block.transactions:
                if tx.to is None:
                    code = self.w3.eth.get_code(tx['from']).hex()
                    tag = known_bot_addresses.get(tx['from'].lower(), None)
                    if tag or any(sig in code for sig in bot_sigs) or any(sig in code for sig in flashloan_sigs):
                        abi = await self.fetch_abi(tx['from'])
                        c.execute("REPLACE INTO bots (address, detected_in_block, timestamp, abi) VALUES (?, ?, ?, ?)",
                                  (tx['from'], block.number, datetime.utcfromtimestamp(block.timestamp).isoformat(), abi))
                        logger.info(f"🤖 Bot-like contract detected at {tx['from']} ({tag or 'heuristic match'})")
        conn.commit()
        conn.close()

CHAIN_CONFIGS = {
    "arbitrum": {
        "rpc_url": os.getenv("ALCHEMY_ARB_KEY"),
        "api_key_env": "",
        "explorer_url": "https://api.arbiscan.io/api",
        "explorer_api_key_env": "ARBISCAN_API_KEY",
        "db": "arbitrum_dexes.db"
    },
    "base": {
        "rpc_url": os.getenv("BASE_RPC_KEY"),
        "api_key_env": "",
        "explorer_url": "https://api.basescan.org/api",
        "explorer_api_key_env": "BASESCAN_API_KEY",
        "db": "base_dexes.db"
    },
    "optimism": {
        "rpc_url": os.getenv("ALCHEMY_OPT_KEY"),
        "api_key_env": "",
        "explorer_url": "https://api-optimistic.etherscan.io/api",
        "explorer_api_key_env": "OPTIMISTIC_ETHERSCAN_KEY",
        "db": "optimism_dexes.db"
    },
    "polygon": {
        "rpc_url": os.getenv("ALCHEMY_POLY_KEY"),
        "api_key_env": "",
        "explorer_url": "https://api.polygonscan.com/api",
        "explorer_api_key_env": "POLYGONSCAN_API_KEY",
        "db": "polygon_dexes.db"
    },
    "bsc": {
        "rpc_url": os.getenv("BSC_RPC_KEY"),
        "api_key_env": "",
        "explorer_url": "https://api.bscscan.com/api",
        "explorer_api_key_env": "BSCSCAN_API_KEY",
        "db": "bsc_dexes.db"
    },
    "avalanche": {
        "rpc_url": os.getenv("AVALANCHE_RPC_KEY"),
        "api_key_env": "",
        "explorer_url": "https://api.snowtrace.io/api",
        "explorer_api_key_env": "SNOWTRACE_API_KEY",
        "db": "avalanche_dexes.db"
    },
    "linea": {
        "rpc_url": os.getenv("LINEA_RPC_KEY"),
        "api_key_env": "",
        "explorer_url": "https://api.lineascan.build/api",
        "explorer_api_key_env": "LINEASCAN_API_KEY",
        "db": "linea_dexes.db"
    },
    "scroll": {
        "rpc_url": os.getenv("SCROLL_RPC_KEY"),
        "api_key_env": "",
        "explorer_url": "https://api.scrollscan.com/api",
        "explorer_api_key_env": "SCROLLSCAN_API_KEY",
        "db": "scroll_dexes.db"
    },
    "mantle": {
        "rpc_url": os.getenv("MANTLE_RPC_KEY"),
        "api_key_env": "",
        "explorer_url": "https://explorer.mantle.xyz/api",
        "explorer_api_key_env": "MANTLESCAN_API_KEY",
        "db": "mantle_dexes.db"
    },
    "blast": {
        "rpc_url": os.getenv("BLAST_RPC_KEY"),
        "api_key_env": "",
        "explorer_url": "https://api.blastscan.io/api",
        "explorer_api_key_env": "BLASTSCAN_API_KEY",
        "db": "blast_dexes.db"
    }
}

async def scan_chain(chain_name: str, duration_minutes: int = 30):
    """Scan a specific chain for the given duration"""
    print(f"🔗 Starting {duration_minutes}-minute scan on {chain_name.upper()}")

    try:
        scanner = DEXDiscovery(chain_name)
        await scanner.connect()

        # Get starting block and time
        latest_block = scanner.w3.eth.block_number
        last_scanned_block = latest_block
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)  # Convert to seconds

        print(f"📊 Connected to {chain_name.upper()}. Starting from block {latest_block}")

        # Scan for the specified duration
        while time.time() < end_time:
            try:
                current_block = scanner.w3.eth.block_number

                # Only scan if there are new blocks
                if current_block > last_scanned_block:
                    print(f"🔍 [{chain_name.upper()}] New blocks: {last_scanned_block + 1} to {current_block}")
                    await scanner.scan_blocks(last_scanned_block + 1, current_block + 1)
                    await scanner.scan_for_bots(last_scanned_block + 1, current_block + 1)
                    last_scanned_block = current_block

                    # Export reports every 10 blocks
                    if current_block % 10 == 0:
                        scanner.export_dex_report()
                        scanner.export_bot_report()
                else:
                    # Wait before checking for new blocks
                    await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Error scanning {chain_name}: {e}")
                await asyncio.sleep(5)

        # Export final reports for this chain
        scanner.export_dex_report()
        scanner.export_bot_report()
        print(f"✅ Completed {duration_minutes}-minute scan on {chain_name.upper()}")

    except Exception as e:
        logger.error(f"Failed to scan {chain_name}: {e}")
        print(f"❌ Failed to scan {chain_name}: {e}")

async def main():
    print("🚀 Starting multi-chain DEX scanner with 30-minute rotations...")

    # Get available chains (only those with RPC URLs configured)
    available_chains = []
    for chain_name, config in CHAIN_CONFIGS.items():
        if config["rpc_url"]:  # Only include chains with RPC URLs
            available_chains.append(chain_name)

    if not available_chains:
        print("❌ No chains configured with RPC URLs!")
        return

    print(f"📋 Available chains: {', '.join(available_chains)}")

    try:
        while True:
            # Randomly select a chain
            current_chain = random.choice(available_chains)
            print(f"\n🎲 Randomly selected: {current_chain.upper()}")

            # Scan the selected chain for 30 minutes
            await scan_chain(current_chain, 30)

            print("⏰ 30 minutes completed, switching to next random chain...\n")

    except KeyboardInterrupt:
        print("\n🛑 Scanner stopped by user. Goodbye!")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        print(f"💥 Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
 