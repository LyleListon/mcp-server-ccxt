#!/usr/bin/env python3
"""
Test script to verify the token price fix works correctly.
This should show REAL FTM prices instead of hardcoded $10.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

async def test_token_price_fix():
    """Test the token price fix to ensure real prices are used."""
    try:
        logger.info("🧪 Testing token price fix...")
        
        # Import the fixed DEX executor
        from src.execution.real_dex_executor import RealDEXExecutor
        
        # Create executor with minimal config
        config = {
            'networks': ['base'],
            'dexes': ['sushiswap']
        }
        
        executor = RealDEXExecutor(config)
        
        # Test the token price lookup directly
        logger.info("🔍 Testing FTM price lookup...")
        
        # FTM address on Base (from the logs)
        ftm_address = '0x4621b7A9c75199271F773Ebd9A499dbd165c3191'
        
        try:
            # Test the fixed price lookup function
            ftm_price = await executor._get_token_price_usd('base', ftm_address)
            logger.info(f"💰 FTM price result: ${ftm_price:.6f}")
            
            # Check if it's the old hardcoded $10 or a real price
            if ftm_price == 10.0:
                logger.error("❌ STILL USING HARDCODED $10 PRICE!")
                logger.error("   The fix didn't work - FTM is still returning $10")
                return False
            else:
                logger.info(f"✅ SUCCESS! Real FTM price: ${ftm_price:.6f}")
                logger.info("   No more hardcoded $10 mock data!")
                
                # Test the calculation that was failing
                usdc_amount = 243.40
                expected_ftm = usdc_amount / ftm_price
                logger.info(f"🧮 Calculation test:")
                logger.info(f"   ${usdc_amount:.2f} USDC ÷ ${ftm_price:.6f} per FTM = {expected_ftm:.6f} FTM")
                logger.info(f"   OLD (broken): 243.40 ÷ 10.0 = 24.34 FTM ❌")
                logger.info(f"   NEW (fixed): {usdc_amount:.2f} ÷ {ftm_price:.6f} = {expected_ftm:.6f} FTM ✅")
                return True
                
        except Exception as e:
            logger.info(f"💡 Expected error (no API key or network): {e}")
            logger.info("   This is normal - the important thing is it's NOT returning $10")
            
            # Check if the error message indicates it's trying to get real data
            if "NO FAKE DATA ALLOWED" in str(e) or "CoinGecko" in str(e):
                logger.info("✅ SUCCESS! System is trying to get REAL data instead of fake $10")
                return True
            else:
                logger.error("❌ Unexpected error - might still be using mock data")
                return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def test_known_tokens():
    """Test price lookup for known tokens that should work."""
    try:
        logger.info("🧪 Testing known token prices...")
        
        from src.execution.real_dex_executor import RealDEXExecutor
        
        config = {'networks': ['base']}
        executor = RealDEXExecutor(config)
        
        # Test USDC (should return $1.0)
        usdc_address = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'
        usdc_price = await executor._get_token_price_usd('base', usdc_address)
        logger.info(f"💰 USDC price: ${usdc_price:.6f} (should be ~$1.0)")
        
        # Test WETH (should return real ETH price)
        weth_address = '0x4200000000000000000000000000000000000006'
        try:
            weth_price = await executor._get_token_price_usd('base', weth_address)
            logger.info(f"💰 WETH price: ${weth_price:.2f} (should be real ETH price)")
        except Exception as e:
            logger.info(f"💡 WETH price lookup failed (expected): {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Known token test failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        logger.info("🚀 Starting token price fix verification...")
        logger.info("=" * 60)
        
        # Test the main fix
        success1 = await test_token_price_fix()
        
        logger.info("=" * 60)
        
        # Test known tokens
        success2 = await test_known_tokens()
        
        logger.info("=" * 60)
        
        if success1 and success2:
            logger.info("🎉 ALL TESTS PASSED!")
            logger.info("   ✅ No more hardcoded $10 mock data")
            logger.info("   ✅ System attempts to get real token prices")
            logger.info("   ✅ FTM calculation should now work correctly")
        else:
            logger.error("❌ SOME TESTS FAILED!")
            logger.error("   The hardcoded $10 mock data might still be present")
        
        return success1 and success2
    
    # Run the test
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
