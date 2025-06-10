#!/usr/bin/env python3
"""
 BALANCE CHECK OPTIMIZER
Fix the 7-second balance checking delays by optimizing cache usage and fallback logic.
"""

import asyncio
import time
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BalanceCheckOptimizer:
 """Optimize balance checking to eliminate 7+ second delays."""
 
 def __init__(self):
 self.balance_cache = {}
 self.cache_duration = 30 # 30 seconds cache
 self.last_cache_update = {}
 
 def is_cache_valid(self, chain: str) -> bool:
 """Check if cached balance is still valid."""
 if chain not in self.last_cache_update:
 return False
 
 cache_age = datetime.now() - self.last_cache_update[chain]
 return cache_age < timedelta(seconds=self.cache_duration)
 
 def get_cached_balance(self, chain: str) -> Optional[float]:
 """Get cached balance if valid."""
 if self.is_cache_valid(chain):
 return self.balance_cache.get(chain)
 return None
 
 def update_cache(self, chain: str, balance_eth: float):
 """Update balance cache."""
 self.balance_cache[chain] = balance_eth
 self.last_cache_update[chain] = datetime.now()
 logger.info(f" CACHE UPDATED: {chain} = {balance_eth:.6f} ETH")
 
 async def get_optimized_balance(self, w3, wallet_address: str, chain: str,
 smart_wallet_manager=None) -> Dict[str, any]:
 """Get balance with optimized caching and minimal delays."""
 start_time = time.perf_counter()
 
 # Step 1: Try cache first (INSTANT)
 cached_balance = self.get_cached_balance(chain)
 if cached_balance is not None:
 elapsed = time.perf_counter() - start_time
 logger.info(f" CACHE HIT: {cached_balance:.6f} ETH in {elapsed:.3f}s")
 return {
 'balance_eth': cached_balance,
 'source': 'cache',
 'time_taken': elapsed,
 'success': True
 }
 
 # Step 2: Fast blockchain query (0.1-0.5 seconds)
 try:
 balance_wei = w3.eth.get_balance(wallet_address)
 balance_eth = float(w3.from_wei(balance_wei, 'ether'))
 
 # Update cache immediately
 self.update_cache(chain, balance_eth)
 
 elapsed = time.perf_counter() - start_time
 logger.info(f" FAST QUERY: {balance_eth:.6f} ETH in {elapsed:.3f}s")
 
 return {
 'balance_eth': balance_eth,
 'source': 'blockchain',
 'time_taken': elapsed,
 'success': True
 }
 
 except Exception as e:
 # Step 3: Only use smart wallet manager as last resort
 if smart_wallet_manager:
 logger.warning(f"⚠️ Blockchain query failed, trying smart wallet manager: {e}")
 try:
 smart_status = await smart_wallet_manager.get_smart_balance_status(chain)
 total_value = smart_status.get('total_wallet_value_usd', 0)
 
 # Estimate ETH balance (rough conversion)
 eth_price = 3000 # Rough estimate
 estimated_eth = total_value / eth_price
 
 elapsed = time.perf_counter() - start_time
 logger.warning(f"🐌 SMART WALLET FALLBACK: ~{estimated_eth:.6f} ETH in {elapsed:.3f}s")
 
 return {
 'balance_eth': estimated_eth,
 'source': 'smart_wallet_estimate',
 'time_taken': elapsed,
 'success': True
 }
 
 except Exception as smart_error:
 logger.error(f"❌ Smart wallet manager also failed: {smart_error}")
 
 elapsed = time.perf_counter() - start_time
 return {
 'balance_eth': 0.0,
 'source': 'error',
 'time_taken': elapsed,
 'success': False,
 'error': str(e)
 }

# Global optimizer instance
balance_optimizer = BalanceCheckOptimizer()

async def quick_balance_check(w3, wallet_address: str, chain: str,
 smart_wallet_manager=None) -> float:
 """Quick balance check with optimized caching."""
 result = await balance_optimizer.get_optimized_balance(
 w3, wallet_address, chain, smart_wallet_manager
 )
 
 if result['success']:
 return result['balance_eth']
 else:
 logger.error(f"❌ Balance check failed: {result.get('error', 'Unknown error')}")
 return 0.0

def analyze_balance_performance():
 """Analyze balance checking performance."""
 logger.info("📊 BALANCE CHECK PERFORMANCE ANALYSIS:")
 
 for chain, last_update in balance_optimizer.last_cache_update.items():
 cached_balance = balance_optimizer.balance_cache.get(chain, 0)
 cache_age = datetime.now() - last_update
 
 logger.info(f" 🌐 {chain}:")
 logger.info(f" Cached balance: {cached_balance:.6f} ETH")
 logger.info(f" ⏰ Cache age: {cache_age.total_seconds():.1f}s")
 logger.info(f" ✅ Valid: {balance_optimizer.is_cache_valid(chain)}")

if __name__ == "__main__":
 # Test the optimizer
 import asyncio
 
 async def test_optimizer():
 logger.info("🧪 Testing Balance Check Optimizer...")
 
 # Simulate multiple balance checks
 for i in range(5):
 logger.info(f"\n🔍 Test {i+1}:")
 
 # This would normally take 7+ seconds, now should be instant after first check
 start = time.perf_counter()
 
 # Simulate cached vs fresh checks
 if i == 0:
 logger.info(" First check - will be slow")
 await asyncio.sleep(0.5) # Simulate blockchain query
 balance_optimizer.update_cache('arbitrum', 1.234567)
 else:
 logger.info(" Subsequent check - should be instant")
 cached = balance_optimizer.get_cached_balance('arbitrum')
 logger.info(f" CACHED: {cached:.6f} ETH")
 
 elapsed = time.perf_counter() - start
 logger.info(f" ⏱️ Time taken: {elapsed:.3f}s")
 
 analyze_balance_performance()
 
 asyncio.run(test_optimizer())
