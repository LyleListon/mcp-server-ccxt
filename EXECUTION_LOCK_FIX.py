#!/usr/bin/env python3
"""
🔒 EXECUTION LOCK COORDINATOR FIX
Ensure ALL execution paths respect the execution lock!

PROBLEM: Multiple executors bypassing the lock
SOLUTION: Centralized execution coordinator
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ExecutionCoordinator:
 """
 🔒 CENTRALIZED EXECUTION COORDINATOR
 
 Forces ALL execution through a single lock to prevent:
 - Scan interruption during trades
 - Multiple concurrent executions
 - Threading conflicts
 - Trade abandonment
 """
 
 def __init__(self):
 # 🔒 THE MASTER EXECUTION LOCK
 self.execution_lock = asyncio.Lock()
 
 # Track active executions
 self.active_executions = {}
 self.execution_stats = {
 'total_executions': 0,
 'successful_executions': 0,
 'failed_executions': 0,
 'abandoned_executions': 0,
 'lock_violations': 0
 }
 
 # Execution timeout (prevent hanging)
 self.execution_timeout = 300 # 5 minutes max per trade
 
 def is_execution_in_progress(self) -> bool:
 """Check if any execution is currently in progress."""
 return self.execution_lock.locked()
 
 async def execute_with_lock(self,
 execution_func,
 opportunity: Dict[str, Any],
 executor_name: str = "unknown") -> Dict[str, Any]:
 """
 🔒 EXECUTE WITH MANDATORY LOCK
 
 ALL executions MUST go through this method!
 """
 
 execution_id = f"{executor_name}_{int(datetime.now().timestamp() * 1000)}"
 
 # Check if lock is already held
 if self.execution_lock.locked():
 logger.warning(f"🔒 EXECUTION BLOCKED: {executor_name} - Trade already in progress")
 self.execution_stats['lock_violations'] += 1
 return {
 'success': False,
 'error': 'Execution blocked - trade already in progress',
 'executor': executor_name,
 'blocked_by_lock': True
 }
 
 try:
 # 🔒 ACQUIRE THE MASTER LOCK
 async with self.execution_lock:
 logger.info(f"🔒 EXECUTION LOCK ACQUIRED: {executor_name}")

 # Safely extract opportunity details (handle both dict and object)
 def safe_get(obj, *keys):
 """Safely get value from dict or object attributes."""
 for key in keys:
 try:
 if isinstance(obj, dict):
 if key in obj:
 return obj[key]
 else:
 if hasattr(obj, key):
 return getattr(obj, key)
 except:
 continue
 return 'Unknown' if 'token' in keys or 'chain' in keys else 0

 token = safe_get(opportunity, 'token', 'token_symbol')
 chain = safe_get(opportunity, 'chain', 'source_chain')
 profit = safe_get(opportunity, 'profit_usd', 'estimated_profit_usd')

 logger.info(f" Opportunity: {token} on {chain}")
 logger.info(f" Expected profit: ${profit:.2f}")
 
 # Track execution
 self.active_executions[execution_id] = {
 'executor': executor_name,
 'opportunity': opportunity,
 'start_time': datetime.now(),
 'status': 'executing'
 }
 
 self.execution_stats['total_executions'] += 1
 
 # Execute with timeout protection
 try:
 result = await asyncio.wait_for(
 execution_func(opportunity),
 timeout=self.execution_timeout
 )
 
 # Update tracking
 if result.get('success', False):
 self.execution_stats['successful_executions'] += 1
 logger.info(f"✅ EXECUTION COMPLETE: {executor_name} - SUCCESS")
 logger.info(f" Actual profit: ${result.get('profit_usd', 0):.2f}")
 else:
 self.execution_stats['failed_executions'] += 1
 logger.error(f"❌ EXECUTION COMPLETE: {executor_name} - FAILED")
 logger.error(f" Error: {result.get('error', 'Unknown error')}")
 
 # Clean up tracking
 if execution_id in self.active_executions:
 del self.active_executions[execution_id]
 
 logger.info(f"🔓 EXECUTION LOCK RELEASED: {executor_name}")
 return result
 
 except asyncio.TimeoutError:
 logger.error(f"⏰ EXECUTION TIMEOUT: {executor_name} after {self.execution_timeout}s")
 self.execution_stats['abandoned_executions'] += 1
 
 # Clean up tracking
 if execution_id in self.active_executions:
 del self.active_executions[execution_id]
 
 return {
 'success': False,
 'error': f'Execution timeout after {self.execution_timeout}s',
 'executor': executor_name,
 'timeout': True
 }
 
 except Exception as e:
 logger.error(f" EXECUTION COORDINATOR ERROR: {executor_name} - {e}")
 self.execution_stats['failed_executions'] += 1
 
 # Clean up tracking
 if execution_id in self.active_executions:
 del self.active_executions[execution_id]
 
 return {
 'success': False,
 'error': str(e),
 'executor': executor_name,
 'coordinator_error': True
 }
 
 def get_execution_status(self) -> Dict[str, Any]:
 """Get current execution status and statistics."""
 return {
 'lock_held': self.execution_lock.locked(),
 'active_executions': len(self.active_executions),
 'execution_details': list(self.active_executions.values()),
 'statistics': self.execution_stats.copy()
 }
 
 def log_execution_stats(self):
 """Log execution statistics."""
 stats = self.execution_stats
 total = stats['total_executions']
 
 if total > 0:
 success_rate = (stats['successful_executions'] / total) * 100
 logger.info("📊 EXECUTION COORDINATOR STATS:")
 logger.info(f" Total executions: {total}")
 logger.info(f" ✅ Successful: {stats['successful_executions']} ({success_rate:.1f}%)")
 logger.info(f" ❌ Failed: {stats['failed_executions']}")
 logger.info(f" ⏰ Abandoned: {stats['abandoned_executions']}")
 logger.info(f" 🔒 Lock violations: {stats['lock_violations']}")

# 🌍 GLOBAL EXECUTION COORDINATOR
# All executors MUST use this instance
GLOBAL_EXECUTION_COORDINATOR = ExecutionCoordinator()

async def execute_arbitrage_with_lock(execution_func,
 opportunity: Dict[str, Any],
 executor_name: str) -> Dict[str, Any]:
 """
 🔒 GLOBAL EXECUTION FUNCTION
 
 ALL arbitrage executions MUST use this function!
 """
 return await GLOBAL_EXECUTION_COORDINATOR.execute_with_lock(
 execution_func, opportunity, executor_name
 )

def check_execution_status() -> Dict[str, Any]:
 """Check if any execution is currently in progress."""
 return GLOBAL_EXECUTION_COORDINATOR.get_execution_status()

def is_execution_blocked() -> bool:
 """Quick check if execution is currently blocked."""
 return GLOBAL_EXECUTION_COORDINATOR.is_execution_in_progress()

# 🔧 INTEGRATION EXAMPLES:

async def example_master_system_integration():
 """Example: How MasterArbitrageSystem should integrate."""
 
 async def execute_opportunity(opp):
 # Your existing execution logic here
 return {'success': True, 'profit_usd': 25.50}
 
 # Instead of direct execution:
 # result = await self.executor.execute(opportunity)
 
 # Use coordinated execution:
 result = await execute_arbitrage_with_lock(
 execute_opportunity,
 opportunity={'token': 'WETH', 'chain': 'arbitrum', 'profit_usd': 25.50},
 executor_name='MasterArbitrageSystem'
 )
 
 return result

async def example_batch_executor_integration():
 """Example: How BatchExecutor should integrate."""
 
 async def execute_batch(opportunities):
 # Your existing batch logic here
 return {'success': True, 'trades_executed': len(opportunities)}
 
 # For each opportunity in batch:
 for opp in opportunities:
 result = await execute_arbitrage_with_lock(
 lambda o: execute_batch([o]),
 opp,
 executor_name='BatchExecutor'
 )

async def example_flashbots_integration():
 """Example: How Flashbots should integrate."""
 
 async def execute_flashbots_trade(opp):
 # Your existing Flashbots logic here
 return {'success': True, 'profit_usd': 15.25, 'protection': 'flashbots'}
 
 result = await execute_arbitrage_with_lock(
 execute_flashbots_trade,
 opportunity={'token': 'USDC', 'chain': 'ethereum'},
 executor_name='FlashbotsExecutor'
 )

if __name__ == "__main__":
 # Test the coordinator
 async def test_coordinator():
 logger.info("🧪 Testing Execution Coordinator...")
 
 # Test normal execution
 async def mock_execution(opp):
 await asyncio.sleep(0.1) # Simulate execution time
 return {'success': True, 'profit_usd': 10.0}
 
 result = await execute_arbitrage_with_lock(
 mock_execution,
 {'token': 'TEST', 'chain': 'test'},
 'TestExecutor'
 )
 
 print(f"Result: {result}")
 
 # Test concurrent execution (should block)
 async def test_concurrent():
 task1 = execute_arbitrage_with_lock(mock_execution, {'token': 'TEST1'}, 'Executor1')
 task2 = execute_arbitrage_with_lock(mock_execution, {'token': 'TEST2'}, 'Executor2')
 
 results = await asyncio.gather(task1, task2)
 print(f"Concurrent results: {results}")
 
 await test_concurrent()
 
 # Show stats
 GLOBAL_EXECUTION_COORDINATOR.log_execution_stats()
 
 asyncio.run(test_coordinator())
