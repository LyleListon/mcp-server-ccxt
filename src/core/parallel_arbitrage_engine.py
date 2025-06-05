"""
Parallel Arbitrage Engine
Implements concurrent opportunity detection, validation, and execution preparation.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class OpportunityTask:
    """Represents a parallel opportunity processing task."""
    opportunity_id: str
    opportunity: Dict[str, Any]
    task_type: str  # 'validate', 'prepare', 'execute'
    priority: int   # 1 = highest, 10 = lowest
    created_at: float
    timeout: float = 30.0

class ParallelArbitrageEngine:
    """High-performance parallel arbitrage processing engine."""
    
    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.task_queue = asyncio.Queue()
        self.results_cache = {}
        self.active_tasks = {}
        self.performance_stats = {
            'tasks_processed': 0,
            'tasks_successful': 0,
            'average_processing_time': 0.0,
            'concurrent_tasks_peak': 0
        }
        
        # Task processing locks
        self.cache_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        
        # Processing flags
        self.is_running = False
        self.shutdown_event = threading.Event()
        
        logger.info(f"🚀 Parallel Arbitrage Engine initialized with {max_workers} workers")
    
    async def start(self):
        """Start the parallel processing engine."""
        if self.is_running:
            logger.warning("⚠️ Engine already running")
            return
        
        self.is_running = True
        self.shutdown_event.clear()
        
        logger.info("🚀 STARTING PARALLEL ARBITRAGE ENGINE")
        logger.info("=" * 50)
        
        # Start background task processor
        asyncio.create_task(self._process_task_queue())
        
        logger.info("✅ Parallel engine started successfully")
    
    async def stop(self):
        """Stop the parallel processing engine."""
        logger.info("🛑 Stopping parallel arbitrage engine...")
        
        self.is_running = False
        self.shutdown_event.set()
        
        # Wait for active tasks to complete (with timeout)
        await self._wait_for_active_tasks(timeout=10.0)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("✅ Parallel engine stopped")
    
    async def process_opportunities_parallel(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple opportunities in parallel for maximum speed."""
        try:
            start_time = time.time()
            
            logger.info(f"⚡ PARALLEL PROCESSING: {len(opportunities)} opportunities")
            
            # Create tasks for parallel processing
            tasks = []
            for i, opportunity in enumerate(opportunities):
                task = OpportunityTask(
                    opportunity_id=f"opp_{i}_{int(time.time())}",
                    opportunity=opportunity,
                    task_type='validate_and_prepare',
                    priority=self._calculate_priority(opportunity),
                    created_at=time.time()
                )
                tasks.append(task)
            
            # Process tasks in parallel
            results = await self._process_tasks_parallel(tasks)
            
            # Filter successful results
            successful_results = [r for r in results if r.get('success', False)]
            
            processing_time = time.time() - start_time
            
            logger.info(f"⚡ PARALLEL PROCESSING COMPLETE:")
            logger.info(f"   📊 Processed: {len(opportunities)} opportunities")
            logger.info(f"   ✅ Successful: {len(successful_results)} opportunities")
            logger.info(f"   ⏱️ Time: {processing_time:.2f}s")
            logger.info(f"   🚀 Speed: {len(opportunities)/processing_time:.1f} opp/sec")
            
            return successful_results
            
        except Exception as e:
            logger.error(f"❌ Parallel processing error: {e}")
            return []
    
    async def _process_tasks_parallel(self, tasks: List[OpportunityTask]) -> List[Dict[str, Any]]:
        """Process multiple tasks in parallel using asyncio and threading."""
        try:
            # Sort tasks by priority
            tasks.sort(key=lambda x: x.priority)
            
            # Create async tasks for parallel execution
            async_tasks = []
            for task in tasks:
                async_task = asyncio.create_task(self._process_single_task(task))
                async_tasks.append(async_task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*async_tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"❌ Task {tasks[i].opportunity_id} failed: {result}")
                    processed_results.append({'success': False, 'error': str(result)})
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"❌ Parallel task processing error: {e}")
            return []
    
    async def _process_single_task(self, task: OpportunityTask) -> Dict[str, Any]:
        """Process a single opportunity task."""
        try:
            start_time = time.time()
            
            # Track active task
            with self.stats_lock:
                self.active_tasks[task.opportunity_id] = task
                current_active = len(self.active_tasks)
                if current_active > self.performance_stats['concurrent_tasks_peak']:
                    self.performance_stats['concurrent_tasks_peak'] = current_active
            
            # Process based on task type
            if task.task_type == 'validate_and_prepare':
                result = await self._validate_and_prepare_opportunity(task.opportunity)
            elif task.task_type == 'validate':
                result = await self._validate_opportunity(task.opportunity)
            elif task.task_type == 'prepare':
                result = await self._prepare_opportunity(task.opportunity)
            else:
                result = {'success': False, 'error': f'Unknown task type: {task.task_type}'}
            
            # Update performance stats
            processing_time = time.time() - start_time
            with self.stats_lock:
                self.performance_stats['tasks_processed'] += 1
                if result.get('success', False):
                    self.performance_stats['tasks_successful'] += 1
                
                # Update average processing time
                current_avg = self.performance_stats['average_processing_time']
                task_count = self.performance_stats['tasks_processed']
                self.performance_stats['average_processing_time'] = (
                    (current_avg * (task_count - 1) + processing_time) / task_count
                )
                
                # Remove from active tasks
                self.active_tasks.pop(task.opportunity_id, None)
            
            # Add processing metadata
            result['processing_time'] = processing_time
            result['task_id'] = task.opportunity_id
            result['priority'] = task.priority
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Task {task.opportunity_id} processing error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _validate_and_prepare_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and prepare an opportunity for execution."""
        try:
            # Step 1: Fast validation
            validation_result = await self._validate_opportunity(opportunity)
            if not validation_result.get('success', False):
                return validation_result
            
            # Step 2: Preparation for execution
            preparation_result = await self._prepare_opportunity(opportunity)
            if not preparation_result.get('success', False):
                return preparation_result
            
            # Combine results
            return {
                'success': True,
                'opportunity': opportunity,
                'validation': validation_result,
                'preparation': preparation_result,
                'ready_for_execution': True
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Validation and preparation failed: {e}'}
    
    async def _validate_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Fast opportunity validation."""
        try:
            # Extract opportunity details
            profit_usd = opportunity.get('estimated_profit_usd', 0)
            age_seconds = time.time() - opportunity.get('discovered_at', time.time())
            
            # Validation checks
            validations = {
                'profit_threshold': profit_usd >= 0.05,  # Minimum $0.05 profit
                'freshness': age_seconds <= 15.0,       # Maximum 15 seconds old
                'has_required_fields': all(key in opportunity for key in [
                    'token', 'buy_dex', 'sell_dex', 'source_chain'
                ])
            }
            
            # Overall validation result
            is_valid = all(validations.values())
            
            return {
                'success': is_valid,
                'validations': validations,
                'profit_usd': profit_usd,
                'age_seconds': age_seconds,
                'validation_time': time.time()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Validation error: {e}'}
    
    async def _prepare_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare opportunity for fast execution."""
        try:
            # Simulate preparation tasks that would normally take time
            await asyncio.sleep(0.1)  # Simulate gas estimation
            await asyncio.sleep(0.1)  # Simulate transaction building
            await asyncio.sleep(0.1)  # Simulate route optimization
            
            # Preparation results
            preparation_data = {
                'gas_estimate': 300000,
                'gas_price_gwei': 0.4,
                'execution_route': f"{opportunity.get('buy_dex', 'unknown')} → {opportunity.get('sell_dex', 'unknown')}",
                'estimated_execution_time': 3.5,  # seconds
                'slippage_tolerance': 0.05,  # 5%
                'prepared_at': time.time()
            }
            
            return {
                'success': True,
                'preparation_data': preparation_data,
                'ready_for_execution': True
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Preparation error: {e}'}
    
    def _calculate_priority(self, opportunity: Dict[str, Any]) -> int:
        """Calculate task priority based on opportunity characteristics."""
        try:
            profit_usd = opportunity.get('estimated_profit_usd', 0)
            age_seconds = time.time() - opportunity.get('discovered_at', time.time())
            
            # Higher profit = higher priority (lower number)
            profit_priority = max(1, 10 - int(profit_usd))
            
            # Fresher opportunities = higher priority
            age_priority = min(10, max(1, int(age_seconds)))
            
            # Combined priority (1 = highest, 10 = lowest)
            priority = min(10, (profit_priority + age_priority) // 2)
            
            return priority
            
        except Exception:
            return 5  # Default medium priority
    
    async def _process_task_queue(self):
        """Background task queue processor."""
        while self.is_running and not self.shutdown_event.is_set():
            try:
                # Process any queued tasks
                if not self.task_queue.empty():
                    task = await self.task_queue.get()
                    asyncio.create_task(self._process_single_task(task))
                
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                logger.error(f"❌ Task queue processing error: {e}")
                await asyncio.sleep(1.0)
    
    async def _wait_for_active_tasks(self, timeout: float = 10.0):
        """Wait for active tasks to complete."""
        start_time = time.time()
        
        while self.active_tasks and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)
        
        if self.active_tasks:
            logger.warning(f"⚠️ {len(self.active_tasks)} tasks still active after timeout")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get engine performance statistics."""
        with self.stats_lock:
            stats = self.performance_stats.copy()
            stats['active_tasks'] = len(self.active_tasks)
            stats['success_rate'] = (
                stats['tasks_successful'] / max(1, stats['tasks_processed']) * 100
            )
            return stats
    
    async def add_task(self, task: OpportunityTask):
        """Add a task to the processing queue."""
        await self.task_queue.put(task)
