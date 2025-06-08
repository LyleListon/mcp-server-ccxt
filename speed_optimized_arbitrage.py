#!/usr/bin/env python3
"""
Speed Optimized Arbitrage System
================================

Implementation of the collaborative thinktank speed optimizations.
Target: 4.0s → 3.0s execution time (Week 1)

Features:
- Enhanced Connection Manager (WebSocket + HTTP fallback)
- Advanced Nonce Manager (drift protection)
- Enhanced Performance Profiler (bottleneck detection)
- Speed-optimized execution flow
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.speed_optimizations import (
    create_speed_optimized_web3,
    EnhancedPerformanceProfiler
)
from eth_account import Account

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

class SpeedOptimizedArbitrageExecutor:
    """Speed-optimized arbitrage executor with all Week 1 optimizations."""
    
    def __init__(self):
        """Initialize the speed-optimized arbitrage executor."""
        self.chains = ['arbitrum']  # Start with Arbitrum, expand later
        self.web3_instances = {}
        self.connection_managers = {}
        self.nonce_managers = {}
        self.profiler = EnhancedPerformanceProfiler()
        self.account = None
        
        logger.info("🚀 SPEED OPTIMIZED ARBITRAGE EXECUTOR")
        logger.info("=" * 45)
        logger.info("Week 1 Target: 4.0s → 3.0s execution time")
        
    async def initialize(self):
        """Initialize all speed-optimized components."""
        with self.profiler.time_stage("initialization"):
            # Get environment variables
            private_key = os.getenv('PRIVATE_KEY')
            api_key = os.getenv('ALCHEMY_API_KEY')
            
            if not private_key or not api_key:
                raise ValueError("Missing PRIVATE_KEY or ALCHEMY_API_KEY environment variables")
            
            # Create account
            self.account = Account.from_key(private_key)
            logger.info(f"📍 Account: {self.account.address}")
            
            # Initialize speed-optimized Web3 instances for each chain
            for chain_name in self.chains:
                logger.info(f"🔗 Initializing {chain_name}...")
                
                web3, conn_mgr, nonce_mgr, _ = create_speed_optimized_web3(
                    chain_name, api_key, self.account.address
                )
                
                self.web3_instances[chain_name] = web3
                self.connection_managers[chain_name] = conn_mgr
                self.nonce_managers[chain_name] = nonce_mgr
                
                # Test connection
                try:
                    latest_block = await web3.eth.get_block('latest')
                    balance = await web3.eth.get_balance(self.account.address)
                    
                    logger.info(f"   ✅ Connected - Block: {latest_block['number']}")
                    logger.info(f"   💰 Balance: {web3.from_wei(balance, 'ether'):.6f} ETH")
                except Exception as e:
                    logger.error(f"   ❌ Connection failed: {e}")
                    raise
            
            logger.info("✅ Speed optimization initialization complete!")
    
    async def create_mock_opportunity(self) -> Dict[str, Any]:
        """Create a realistic mock arbitrage opportunity for testing."""
        import random
        
        opportunity = {
            'id': f"speed_test_{int(time.time() * 1000)}",
            'chain': 'arbitrum',
            'flashloan_token': 'USDC',
            'target_token': 'WETH',
            'flashloan_amount': 10000.0,
            'estimated_net_profit_usd': random.uniform(5.0, 25.0),
            'arbitrage_path': {
                'step1': {
                    'action': 'buy',
                    'dex': 'sushiswap',
                    'from_token': 'USDC',
                    'to_token': 'WETH'
                },
                'step2': {
                    'action': 'sell',
                    'dex': 'camelot', 
                    'from_token': 'WETH',
                    'to_token': 'USDC'
                }
            },
            'mock': True
        }
        
        return opportunity
    
    async def execute_speed_optimized_arbitrage(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute arbitrage with all speed optimizations."""
        start_time = time.perf_counter()
        
        logger.info(f"⚡ SPEED OPTIMIZED EXECUTION")
        logger.info(f"   🆔 ID: {opportunity['id']}")
        logger.info(f"   💰 Profit: ${opportunity['estimated_net_profit_usd']:.2f}")
        
        try:
            chain_name = opportunity['chain']
            web3 = self.web3_instances[chain_name]
            conn_mgr = self.connection_managers[chain_name]
            nonce_mgr = self.nonce_managers[chain_name]
            
            # Step 1: Pre-flight checks (optimized)
            with self.profiler.time_stage("pre_flight_checks"):
                # Get nonce (predicted, no network call)
                nonce = await nonce_mgr.get_next_nonce()
                
                # Get current gas price (WebSocket call)
                gas_price = await conn_mgr.execute_call('eth_gasPrice', [])
                
                logger.info(f"   🔢 Nonce: {nonce}")
                logger.info(f"   ⛽ Gas Price: {int(gas_price, 16) / 1e9:.2f} gwei")
            
            # Step 2: Load flashloan contract (cached)
            with self.profiler.time_stage("contract_loading"):
                # Load deployment info
                import json
                with open('flashloan_deployment.json', 'r') as f:
                    deployment_info = json.load(f)
                
                contract_address = deployment_info['contract_address']
                contract_abi = deployment_info['abi']
                
                # Create contract instance
                flashloan_contract = web3.eth.contract(
                    address=contract_address,
                    abi=contract_abi
                )
                
                logger.info(f"   📍 Contract: {contract_address}")
            
            # Step 3: Build transaction (optimized)
            with self.profiler.time_stage("transaction_building"):
                # Get token addresses
                token_address = opportunity.get('flashloan_token_address', 
                    '0xaf88d065e77c8cC2239327C5EDb3A432268e5831')  # USDC on Arbitrum
                amount = int(opportunity['flashloan_amount'] * 1e6)  # Convert to wei
                
                # DEX router addresses (hardcoded for speed)
                sushiswap_router = "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"
                camelot_router = "0xc873fEcbd354f5A56E00E710B90EF4201db2448d"
                
                # Build transaction
                transaction = flashloan_contract.functions.executeFlashloanArbitrage(
                    token_address,
                    amount,
                    sushiswap_router,
                    camelot_router
                ).build_transaction({
                    'from': self.account.address,
                    'gas': 500000,  # Fixed gas limit for speed
                    'gasPrice': gas_price,
                    'nonce': nonce
                })
                
                logger.info(f"   📦 Transaction built")
            
            # Step 4: Simulate transaction (WebSocket call)
            with self.profiler.time_stage("transaction_simulation"):
                try:
                    simulation_result = await conn_mgr.execute_call('eth_call', [
                        {
                            'from': transaction['from'],
                            'to': transaction['to'],
                            'data': transaction['data'],
                            'gas': hex(transaction['gas']),
                            'gasPrice': transaction['gasPrice']
                        },
                        'latest'
                    ])
                    logger.info(f"   🧪 Simulation: SUCCESS")
                except Exception as e:
                    logger.error(f"   🧪 Simulation: FAILED - {e}")
                    return {
                        'success': False,
                        'error': f'Simulation failed: {e}',
                        'execution_time': time.perf_counter() - start_time
                    }
            
            # Step 5: Sign and send transaction (optimized)
            with self.profiler.time_stage("transaction_execution"):
                # Sign transaction
                signed_tx = self.account.sign_transaction(transaction)
                
                # Send transaction (WebSocket)
                tx_hash = await conn_mgr.execute_call('eth_sendRawTransaction', [
                    signed_tx.raw_transaction.hex()
                ])
                
                logger.info(f"   📤 Transaction sent: {tx_hash}")
            
            # Step 6: Wait for confirmation (optimized)
            with self.profiler.time_stage("transaction_confirmation"):
                # Wait for receipt (WebSocket)
                receipt = None
                max_wait = 30  # 30 second timeout
                start_wait = time.time()
                
                while time.time() - start_wait < max_wait:
                    try:
                        receipt = await conn_mgr.execute_call('eth_getTransactionReceipt', [tx_hash])
                        if receipt:
                            break
                    except:
                        pass
                    await asyncio.sleep(1)
                
                if receipt and receipt.get('status') == '0x1':
                    # Mark nonce as confirmed
                    nonce_mgr.mark_nonce_confirmed(nonce)
                    
                    execution_time = time.perf_counter() - start_time
                    logger.info(f"   ✅ SUCCESS in {execution_time:.2f}s")
                    
                    return {
                        'success': True,
                        'transaction_hash': tx_hash,
                        'execution_time': execution_time,
                        'gas_used': int(receipt.get('gasUsed', '0'), 16),
                        'net_profit': opportunity['estimated_net_profit_usd']
                    }
                else:
                    execution_time = time.perf_counter() - start_time
                    logger.error(f"   ❌ FAILED in {execution_time:.2f}s")
                    
                    return {
                        'success': False,
                        'error': 'Transaction failed or timeout',
                        'execution_time': execution_time
                    }
        
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            logger.error(f"❌ Execution error: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'execution_time': execution_time
            }
    
    async def run_speed_test(self, num_tests: int = 5):
        """Run speed tests to measure optimization effectiveness."""
        logger.info(f"🏃 RUNNING SPEED TEST ({num_tests} iterations)")
        logger.info("=" * 40)
        
        results = []
        
        for i in range(num_tests):
            logger.info(f"\n🔍 TEST #{i+1}/{num_tests}")
            logger.info("-" * 25)
            
            # Create mock opportunity
            opportunity = await self.create_mock_opportunity()
            
            # Execute with speed optimizations
            result = await self.execute_speed_optimized_arbitrage(opportunity)
            results.append(result)
            
            # Brief pause between tests
            await asyncio.sleep(2)
        
        # Analyze results
        self.analyze_speed_test_results(results)
    
    def analyze_speed_test_results(self, results: list):
        """Analyze speed test results."""
        logger.info(f"\n📊 SPEED TEST ANALYSIS")
        logger.info("=" * 30)
        
        execution_times = [r['execution_time'] for r in results]
        successful_results = [r for r in results if r['success']]
        
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
            success_rate = len(successful_results) / len(results)
            
            logger.info(f"📈 EXECUTION TIMES:")
            logger.info(f"   ⏱️  Average: {avg_time:.2f}s")
            logger.info(f"   ⚡ Fastest: {min_time:.2f}s")
            logger.info(f"   🐌 Slowest: {max_time:.2f}s")
            logger.info(f"   ✅ Success Rate: {success_rate:.1%}")
            
            # Compare to target
            target_time = 3.0  # Week 1 target
            if avg_time <= target_time:
                logger.info(f"🎉 TARGET ACHIEVED! {avg_time:.2f}s ≤ {target_time}s")
            else:
                improvement_needed = avg_time - target_time
                logger.info(f"🎯 Need {improvement_needed:.2f}s improvement to reach target")
        
        # Show performance breakdown
        self.profiler.log_performance_summary()
        
        # Show bottlenecks
        bottlenecks = self.profiler.get_bottlenecks()
        if bottlenecks:
            logger.info(f"\n🐌 BOTTLENECKS DETECTED:")
            for bottleneck in bottlenecks:
                logger.info(f"   {bottleneck['stage']}: {bottleneck['avg_time']:.3f}s")

async def main():
    """Main entry point for speed optimization testing."""
    try:
        executor = SpeedOptimizedArbitrageExecutor()
        await executor.initialize()
        await executor.run_speed_test(num_tests=3)
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Speed test stopped by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 SPEED OPTIMIZED ARBITRAGE SYSTEM")
    print("=" * 40)
    print("Week 1 Implementation: 4.0s → 3.0s target")
    print("Features: WebSocket, Nonce Prediction, Performance Profiling")
    print()
    
    asyncio.run(main())
