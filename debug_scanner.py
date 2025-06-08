#!/usr/bin/env python3
"""
🔍 DEBUG SCANNER - Find out why the main scanner locks up
"""

import asyncio
import os
from web3 import Web3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("debug-scanner")

async def test_connection():
    """Test basic connection to your Ethereum node"""
    
    node_url = os.getenv('ETHEREUM_NODE_URL', 'http://192.168.1.18:8545')
    logger.info(f"🔗 Testing connection to: {node_url}")
    
    try:
        # Test with timeout
        w3 = Web3(Web3.HTTPProvider(node_url, request_kwargs={'timeout': 10}))
        
        logger.info("📡 Checking connection...")
        if w3.is_connected():
            logger.info("✅ Connection successful!")
            
            # Test basic calls
            logger.info("📊 Getting latest block...")
            latest_block = w3.eth.block_number
            logger.info(f"✅ Latest block: {latest_block:,}")
            
            # Test getting a single block
            logger.info("📦 Getting block details...")
            block = w3.eth.get_block(latest_block)
            logger.info(f"✅ Block {latest_block} has {len(block.transactions)} transactions")
            
            # Test getting block with transactions (this might be the problem)
            logger.info("📦 Getting block with full transactions...")
            block_with_txs = w3.eth.get_block(latest_block, full_transactions=True)
            logger.info(f"✅ Block with transactions loaded: {len(block_with_txs.transactions)} txs")
            
            return True
            
        else:
            logger.error("❌ Connection failed - not connected")
            return False
            
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")
        return False

async def test_fallback():
    """Test fallback RPC"""
    
    fallback_url = "https://eth.llamarpc.com"
    logger.info(f"🔗 Testing fallback: {fallback_url}")
    
    try:
        w3 = Web3(Web3.HTTPProvider(fallback_url, request_kwargs={'timeout': 10}))
        
        if w3.is_connected():
            latest_block = w3.eth.block_number
            logger.info(f"✅ Fallback works! Latest block: {latest_block:,}")
            return True
        else:
            logger.error("❌ Fallback failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fallback error: {e}")
        return False

async def test_block_scanning():
    """Test the block scanning logic that might be hanging"""
    
    node_url = os.getenv('ETHEREUM_NODE_URL', 'http://192.168.1.18:8545')
    
    try:
        w3 = Web3(Web3.HTTPProvider(node_url, request_kwargs={'timeout': 10}))
        
        if not w3.is_connected():
            logger.error("❌ Can't connect for block scanning test")
            return False
        
        latest_block = w3.eth.block_number
        test_block = latest_block - 1  # Test with previous block
        
        logger.info(f"🔍 Testing block scanning on block {test_block}")
        
        # Get block with transactions
        block = w3.eth.get_block(test_block, full_transactions=True)
        logger.info(f"📦 Block {test_block} has {len(block.transactions)} transactions")
        
        # Test processing first few transactions
        contract_creations = 0
        for i, tx in enumerate(block.transactions[:5]):  # Only test first 5
            logger.info(f"📝 TX {i+1}: from={tx['from']}, to={tx.get('to', 'None')}")
            
            if tx.to is None:  # Contract creation
                contract_creations += 1
                logger.info(f"🏗️ Contract creation detected!")
        
        logger.info(f"✅ Found {contract_creations} contract creations in first 5 transactions")
        return True
        
    except Exception as e:
        logger.error(f"❌ Block scanning error: {e}")
        return False

async def main():
    """Run all debug tests"""
    
    print("🔍" * 30)
    print("🔍 DEBUG SCANNER")
    print("🔍 Finding why the main scanner locks up")
    print("🔍" * 30)
    
    # Test 1: Basic connection
    logger.info("🧪 TEST 1: Basic connection")
    connection_ok = await test_connection()
    
    if not connection_ok:
        # Test 2: Fallback connection
        logger.info("🧪 TEST 2: Fallback connection")
        fallback_ok = await test_fallback()
        
        if not fallback_ok:
            logger.error("💥 Both connections failed!")
            return
    
    # Test 3: Block scanning logic
    logger.info("🧪 TEST 3: Block scanning logic")
    scanning_ok = await test_block_scanning()
    
    if scanning_ok:
        logger.info("✅ All tests passed! The issue might be in the continuous scanning loop.")
    else:
        logger.error("❌ Block scanning failed - this is likely where it hangs!")

if __name__ == "__main__":
    asyncio.run(main())
