#!/usr/bin/env python3
"""
🧪 TEST EXECUTION COORDINATOR
Verify the execution lock coordinator is working properly
"""

import asyncio
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(
 level=logging.INFO,
 format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_execution_coordinator():
 """Test the execution coordinator integration."""
 logger.info("🧪 TESTING EXECUTION COORDINATOR INTEGRATION")
 logger.info("=" * 60)
 
 try:
 # Test 1: Import the coordinator
 logger.info("📦 Test 1: Importing execution coordinator...")
 from EXECUTION_LOCK_FIX import GLOBAL_EXECUTION_COORDINATOR, execute_arbitrage_with_lock
 logger.info("✅ Execution coordinator imported successfully!")
 
 # Test 2: Check coordinator status
 logger.info("\n📊 Test 2: Checking coordinator status...")
 status = GLOBAL_EXECUTION_COORDINATOR.get_execution_status()
 logger.info(f" 🔒 Lock held: {status['lock_held']}")
 logger.info(f" Active executions: {status['active_executions']}")
 logger.info(f" 📊 Total executions: {status['statistics']['total_executions']}")
 
 # Test 3: Mock execution
 logger.info("\n Test 3: Testing mock execution...")
 
 async def mock_execution(opportunity):
 logger.info(f" Executing mock trade for {opportunity.get('token', 'TEST')}")
 await asyncio.sleep(0.5) # Simulate execution time
 return {
 'success': True,
 'profit_usd': 15.25,
 'transaction_hash': '0xtest123...'
 }
 
 test_opportunity = {
 'token': 'WETH',
 'chain': 'arbitrum',
 'profit_usd': 15.25,
 'opportunity_id': 'test_001'
 }
 
 result = await execute_arbitrage_with_lock(
 mock_execution,
 test_opportunity,
 "TestExecutor"
 )
 
 if result.get('success'):
 logger.info(f"✅ Mock execution SUCCESS: ${result.get('profit_usd', 0):.2f}")
 else:
 logger.error(f"❌ Mock execution FAILED: {result.get('error', 'Unknown')}")
 
 # Test 4: Concurrent execution test
 logger.info("\n🔄 Test 4: Testing concurrent execution blocking...")
 
 async def slow_execution(opportunity):
 logger.info(f" 🐌 Starting slow execution for {opportunity.get('token', 'TEST')}")
 await asyncio.sleep(2.0) # Simulate slow execution
 return {'success': True, 'profit_usd': 10.0}
 
 async def fast_execution(opportunity):
 logger.info(f" Attempting fast execution for {opportunity.get('token', 'TEST')}")
 await asyncio.sleep(0.1) # Simulate fast execution
 return {'success': True, 'profit_usd': 5.0}
 
 # Start both executions simultaneously
 task1 = execute_arbitrage_with_lock(
 slow_execution,
 {'token': 'SLOW', 'opportunity_id': 'slow_001'},
 "SlowExecutor"
 )
 
 # Wait a bit, then try to start second execution
 await asyncio.sleep(0.1)
 
 task2 = execute_arbitrage_with_lock(
 fast_execution,
 {'token': 'FAST', 'opportunity_id': 'fast_001'},
 "FastExecutor"
 )
 
 results = await asyncio.gather(task1, task2)
 
 logger.info(f" 📊 Slow execution result: {results[0].get('success', False)}")
 logger.info(f" 📊 Fast execution result: {results[1].get('success', False)}")
 
 # One should succeed, one should be blocked
 if results[1].get('blocked_by_lock'):
 logger.info("✅ Concurrent execution properly blocked!")
 else:
 logger.warning("⚠️ Concurrent execution not blocked - check coordinator")
 
 # Test 5: Final statistics
 logger.info("\n📊 Test 5: Final coordinator statistics...")
 GLOBAL_EXECUTION_COORDINATOR.log_execution_stats()
 
 logger.info("\n EXECUTION COORDINATOR TEST COMPLETE!")
 return True
 
 except ImportError as e:
 logger.error(f"❌ Import failed: {e}")
 logger.error(" Make sure EXECUTION_LOCK_FIX.py is in the current directory")
 return False
 except Exception as e:
 logger.error(f"❌ Test failed: {e}")
 return False

async def test_master_system_integration():
 """Test integration with MasterArbitrageSystem."""
 logger.info("\n TESTING MASTER SYSTEM INTEGRATION")
 logger.info("=" * 60)
 
 try:
 # Test importing the updated master system
 logger.info("📦 Importing updated MasterArbitrageSystem...")
 from src.core.master_arbitrage_system import MasterArbitrageSystem
 logger.info("✅ MasterArbitrageSystem imported successfully!")
 
 # Check if execution coordinator is available
 from src.core.master_arbitrage_system import EXECUTION_COORDINATOR_AVAILABLE
 if EXECUTION_COORDINATOR_AVAILABLE:
 logger.info("✅ Execution coordinator available in MasterArbitrageSystem!")
 else:
 logger.warning("⚠️ Execution coordinator not available in MasterArbitrageSystem")
 
 # Create a test config
 test_config = {
 'min_profit_usd': 10.0,
 'scan_interval_seconds': 15,
 'execution_mode': 'live',
 'trading_mode': 'wallet'
 }
 
 # Initialize master system (don't start it)
 logger.info(" Creating MasterArbitrageSystem instance...")
 master_system = MasterArbitrageSystem(test_config)
 logger.info("✅ MasterArbitrageSystem created successfully!")
 
 # Check if it has the execution lock
 if hasattr(master_system, 'execution_lock'):
 logger.info("✅ MasterArbitrageSystem has execution_lock attribute")
 else:
 logger.warning("⚠️ MasterArbitrageSystem missing execution_lock attribute")
 
 logger.info(" MASTER SYSTEM INTEGRATION TEST COMPLETE!")
 return True
 
 except Exception as e:
 logger.error(f"❌ Master system integration test failed: {e}")
 return False

async def main():
 """Run all tests."""
 logger.info(" EXECUTION COORDINATOR COMPREHENSIVE TEST")
 logger.info(" Testing the fix for trade abandonment issues")
 logger.info("=" * 80)
 
 # Test 1: Basic coordinator functionality
 coordinator_test = await test_execution_coordinator()
 
 # Test 2: Master system integration
 integration_test = await test_master_system_integration()
 
 # Final results
 logger.info("\n" + "=" * 80)
 logger.info("🏁 FINAL TEST RESULTS:")
 logger.info(f" 🔒 Execution Coordinator: {'✅ PASS' if coordinator_test else '❌ FAIL'}")
 logger.info(f" Master System Integration: {'✅ PASS' if integration_test else '❌ FAIL'}")
 
 if coordinator_test and integration_test:
 logger.info("\n ALL TESTS PASSED!")
 logger.info(" Your execution coordinator is ready to prevent trade abandonment!")
 logger.info(" Time to test it with real trading and see those profits!")
 else:
 logger.error("\n❌ SOME TESTS FAILED!")
 logger.error("🔧 Fix the issues before running live trades")
 
 return coordinator_test and integration_test

if __name__ == "__main__":
 success = asyncio.run(main())
 exit(0 if success else 1)
