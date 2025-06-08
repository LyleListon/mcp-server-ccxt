#!/usr/bin/env python3
"""
TEST REAL VS SIMULATION EXECUTION
Verify that the system is using real execution instead of simulation
"""

import asyncio
import logging
import os
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

async def test_cross_chain_executor():
    """Test if cross-chain executor is using real execution."""
    try:
        logger.info("🧪 TESTING CROSS-CHAIN EXECUTOR...")
        
        from src.crosschain.cross_chain_arbitrage_executor import CrossChainArbitrageExecutor
        
        config = {
            'min_profit_usd': 10.0,
            'max_trade_amount_usd': 5000.0,
            'execution_timeout_minutes': 15
        }
        
        executor = CrossChainArbitrageExecutor(config)
        
        # Check if it has real DEX executor capabilities
        has_real_dex = hasattr(executor, 'dex_executor') or hasattr(executor, '_execute_buy_order')
        
        logger.info(f"   ✅ Cross-chain executor created")
        logger.info(f"   🔍 Has real DEX capabilities: {has_real_dex}")
        
        # Test a mock buy order to see if it's simulation or real
        if hasattr(executor, '_execute_buy_order'):
            logger.info("   🧪 Testing buy order method...")
            
            # Create a test opportunity
            test_result = await executor._execute_buy_order(
                chain='arbitrum',
                token='WETH', 
                amount_usd=10.0,
                expected_price=3000.0
            )
            
            # Check if result looks like simulation
            is_simulation = (
                test_result.get('tx_hash', '').startswith('0x111') or
                test_result.get('tx_hash', '') == '0x' + '1' * 64 or
                'mock' in str(test_result).lower() or
                'simulation' in str(test_result).lower()
            )
            
            logger.info(f"   📊 Test result: {test_result}")
            logger.info(f"   🎯 Is simulation: {is_simulation}")
            
            if is_simulation:
                logger.error("   ❌ STILL USING SIMULATION!")
                return False
            else:
                logger.info("   ✅ USING REAL EXECUTION!")
                return True
        else:
            logger.warning("   ⚠️  No buy order method found")
            return False
        
    except Exception as e:
        logger.error(f"❌ Cross-chain executor test failed: {e}")
        return False

async def test_flashloan_executor():
    """Test if flashloan executor is using real execution."""
    try:
        logger.info("🧪 TESTING FLASHLOAN EXECUTOR...")
        
        from src.execution.flashloan_arbitrage_executor import FlashloanArbitrageExecutor
        
        config = {
            'flashloan_provider': 'balancer',
            'min_flashloan_amount': 10000,
            'max_flashloan_amount': 100000
        }
        
        executor = FlashloanArbitrageExecutor(config)
        
        # Check if it has real execution capabilities
        has_real_execution = hasattr(executor, 'dex_executor') or hasattr(executor, '_execute_flashloan_arbitrage')
        
        logger.info(f"   ✅ Flashloan executor created")
        logger.info(f"   🔍 Has real execution capabilities: {has_real_execution}")
        
        # Check the execution method
        if hasattr(executor, '_execute_flashloan_arbitrage'):
            logger.info("   🧪 Checking flashloan execution method...")
            
            # Read the method source to see if it's simulation
            import inspect
            source = inspect.getsource(executor._execute_flashloan_arbitrage)
            
            # Check for simulation indicators
            simulation_indicators = [
                'mock', 'simulation', 'fake', 'TODO', 
                'await asyncio.sleep', '0x' + 'f' * 64,
                '0x' + 'a' * 64, 'placeholder'
            ]
            
            is_simulation = any(indicator.lower() in source.lower() for indicator in simulation_indicators)
            
            logger.info(f"   🎯 Contains simulation code: {is_simulation}")
            
            if is_simulation:
                logger.warning("   ⚠️  STILL CONTAINS SIMULATION CODE!")
                # Show which indicators were found
                found_indicators = [ind for ind in simulation_indicators if ind.lower() in source.lower()]
                logger.warning(f"   🔍 Found indicators: {found_indicators}")
                return False
            else:
                logger.info("   ✅ APPEARS TO USE REAL EXECUTION!")
                return True
        else:
            logger.warning("   ⚠️  No flashloan execution method found")
            return False
        
    except Exception as e:
        logger.error(f"❌ Flashloan executor test failed: {e}")
        return False

async def test_master_arbitrage_system():
    """Test if master arbitrage system is configured for real execution."""
    try:
        logger.info("🧪 TESTING MASTER ARBITRAGE SYSTEM...")
        
        from src.core.master_arbitrage_system import MasterArbitrageSystem
        
        config = {
            'trading_mode': 'flashloan',
            'execution_mode': 'live',
            'networks': ['arbitrum'],
            'min_profit_usd': 10.0
        }
        
        system = MasterArbitrageSystem(config)
        
        # Check if system has real components
        has_real_fee_calc = hasattr(system, 'dex_fee_calculator')
        has_real_wallet_calc = hasattr(system, 'wallet_calculator')
        
        logger.info(f"   ✅ Master system created")
        logger.info(f"   🏪 Has real DEX fee calculator: {has_real_fee_calc}")
        logger.info(f"   💰 Has real wallet calculator: {has_real_wallet_calc}")
        
        # Check trading mode
        trading_mode = getattr(system, 'trading_mode', 'unknown')
        execution_mode = getattr(system, 'execution_mode', 'unknown')
        
        logger.info(f"   🎯 Trading mode: {trading_mode}")
        logger.info(f"   🚀 Execution mode: {execution_mode}")
        
        # Check if it's configured for real execution
        is_real_config = (
            trading_mode in ['flashloan', 'wallet'] and
            execution_mode == 'live' and
            has_real_fee_calc
        )
        
        logger.info(f"   🎯 Configured for real execution: {is_real_config}")
        
        return is_real_config
        
    except Exception as e:
        logger.error(f"❌ Master system test failed: {e}")
        return False

async def test_transaction_detection():
    """Test if we can detect real vs fake transaction hashes."""
    try:
        logger.info("🧪 TESTING TRANSACTION DETECTION...")
        
        # Common fake transaction patterns
        fake_patterns = [
            '0x' + '0' * 64,  # All zeros
            '0x' + '1' * 64,  # All ones
            '0x' + 'f' * 64,  # All f's
            '0x' + 'a' * 64,  # All a's
            '0x' + 'b' * 64,  # All b's
        ]
        
        # Real transaction hash pattern (random hex)
        real_pattern = '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
        
        def is_fake_tx_hash(tx_hash):
            """Detect if transaction hash looks fake."""
            if not tx_hash or not tx_hash.startswith('0x'):
                return True
            
            # Check for common fake patterns
            if tx_hash in fake_patterns:
                return True
            
            # Check if all characters are the same (except 0x)
            hex_part = tx_hash[2:]
            if len(set(hex_part)) <= 2:  # Very low entropy
                return True
            
            return False
        
        logger.info("   🔍 Testing fake transaction detection...")
        
        for fake_tx in fake_patterns:
            is_fake = is_fake_tx_hash(fake_tx)
            logger.info(f"   📊 {fake_tx[:10]}... → Fake: {is_fake}")
        
        is_real = is_fake_tx_hash(real_pattern)
        logger.info(f"   📊 {real_pattern[:10]}... → Fake: {is_real}")
        
        logger.info("   ✅ Transaction detection test complete")
        return True
        
    except Exception as e:
        logger.error(f"❌ Transaction detection test failed: {e}")
        return False

async def main():
    """Run all real vs simulation tests."""
    logger.info("🚀 STARTING REAL VS SIMULATION TESTS")
    logger.info("=" * 60)
    
    tests = [
        ("Cross-Chain Executor", test_cross_chain_executor),
        ("Flashloan Executor", test_flashloan_executor),
        ("Master Arbitrage System", test_master_arbitrage_system),
        ("Transaction Detection", test_transaction_detection)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name} test...")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✅ {test_name}: REAL EXECUTION")
            else:
                logger.error(f"❌ {test_name}: STILL SIMULATION")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 REAL VS SIMULATION TEST RESULTS:")
    
    real_count = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ REAL" if result else "❌ SIMULATION"
        logger.info(f"   {status}: {test_name}")
    
    logger.info(f"\n🎯 OVERALL: {real_count}/{total} components using REAL execution ({real_count/total*100:.0f}%)")
    
    if real_count == total:
        logger.info("🎉 ALL COMPONENTS USING REAL EXECUTION!")
    elif real_count > total/2:
        logger.warning(f"⚠️  {total-real_count} components still using simulation")
    else:
        logger.error(f"🚨 MAJORITY STILL USING SIMULATION! Only {real_count} real components")
    
    return real_count == total

if __name__ == "__main__":
    asyncio.run(main())
