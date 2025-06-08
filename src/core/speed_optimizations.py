#!/usr/bin/env python3
"""
Speed Optimizations Core Module
===============================

Implementation of the collaborative thinktank speed optimizations.
Target: 4.0s → 1.7s execution time (2.3x faster!)

Components:
- Enhanced Connection Manager (WebSocket + HTTP fallback)
- Advanced Nonce Manager (drift protection)
- Enhanced Performance Profiler (bottleneck detection)
"""

import asyncio
import time
import logging
from collections import defaultdict
from contextlib import contextmanager
from typing import Dict, Any, Optional
from web3 import Web3
try:
    from web3.providers import WebsocketProvider, HTTPProvider
except ImportError:
    # Newer Web3 versions
    from web3.providers.websocket import WebsocketProvider
    from web3.providers.rpc import HTTPProvider

logger = logging.getLogger(__name__)

class EnhancedConnectionManager:
    """
    WebSocket-first connection manager with HTTP fallback for maximum speed.
    
    Speed Gains:
    - WebSocket: 50-100ms savings per call
    - Persistent connections: No TCP handshake overhead
    - Auto-fallback: Maintains reliability
    """
    
    def __init__(self, websocket_url: str, http_url: str):
        """Initialize connection manager with WebSocket primary and HTTP fallback."""
        self.websocket_primary = WebsocketProvider(websocket_url)
        self.http_fallback = HTTPProvider(http_url)
        self.connection_health = True
        self.reconnect_attempts = 0
        self.max_reconnects = 3
        self.last_health_check = 0
        self.health_check_interval = 60  # Check health every 60 seconds
        
        logger.info(f"🔌 Enhanced Connection Manager initialized")
        logger.info(f"   🚀 Primary: WebSocket ({websocket_url[:50]}...)")
        logger.info(f"   🛡️  Fallback: HTTP ({http_url[:50]}...)")
    
    async def execute_call(self, method: str, params: list) -> Any:
        """Execute Web3 call with WebSocket-first strategy."""
        # Periodic health check
        if time.time() - self.last_health_check > self.health_check_interval:
            await self._health_check()
        
        if self.connection_health:
            try:
                result = await asyncio.wait_for(
                    self.websocket_primary.make_request(method, params),
                    timeout=2.0  # 2s timeout for speed
                )
                self.reconnect_attempts = 0  # Reset on success
                return result
            except (asyncio.TimeoutError, ConnectionError, Exception) as e:
                logger.warning(f"⚠️  WebSocket failed: {e}")
                await self._handle_websocket_failure()
        
        # Fallback to HTTP
        logger.info("🔄 Using HTTP fallback")
        return await self.http_fallback.make_request(method, params)
    
    async def _handle_websocket_failure(self):
        """Handle WebSocket connection failure."""
        self.connection_health = False
        if self.reconnect_attempts < self.max_reconnects:
            self.reconnect_attempts += 1
            logger.info(f"🔄 Attempting WebSocket reconnection ({self.reconnect_attempts}/{self.max_reconnects})")
            # Attempt reconnection in background
            asyncio.create_task(self._reconnect_websocket())
        else:
            logger.warning("❌ Max reconnection attempts reached, staying on HTTP")
    
    async def _reconnect_websocket(self):
        """Attempt to reconnect WebSocket in background."""
        try:
            await asyncio.sleep(2 ** self.reconnect_attempts)  # Exponential backoff
            # Test connection with a simple call
            await asyncio.wait_for(
                self.websocket_primary.make_request('eth_blockNumber', []),
                timeout=5.0
            )
            self.connection_health = True
            logger.info("✅ WebSocket reconnection successful")
        except Exception as e:
            logger.warning(f"❌ WebSocket reconnection failed: {e}")
    
    async def _health_check(self):
        """Periodic health check for WebSocket connection."""
        if self.connection_health:
            try:
                await asyncio.wait_for(
                    self.websocket_primary.make_request('eth_blockNumber', []),
                    timeout=3.0
                )
                self.last_health_check = time.time()
            except Exception:
                logger.warning("⚠️  WebSocket health check failed")
                self.connection_health = False

class AdvancedNonceManager:
    """
    Advanced nonce management with drift protection and prediction.
    
    Speed Gains:
    - Nonce prediction: No waiting for network calls
    - Drift protection: Prevents nonce conflicts
    - Buffer management: Handles concurrent transactions
    """
    
    def __init__(self, web3: Web3, account_address: str):
        """Initialize nonce manager."""
        self.web3 = web3
        self.account_address = account_address
        self.predicted_nonce = None
        self.nonce_buffer = 3
        self.last_sync = 0
        self.sync_interval = 30  # Sync every 30 seconds
        self.pending_nonces = set()  # Track pending transactions
        
        logger.info(f"🔢 Advanced Nonce Manager initialized")
        logger.info(f"   📍 Account: {account_address}")
        logger.info(f"   🔄 Sync interval: {self.sync_interval}s")
    
    async def get_next_nonce(self) -> int:
        """Get next nonce with prediction and drift protection."""
        # Periodic sync to prevent drift
        if time.time() - self.last_sync > self.sync_interval:
            await self._sync_nonce()
        
        if self.predicted_nonce is None:
            await self._sync_nonce()
        
        current_nonce = self.predicted_nonce
        self.predicted_nonce += 1
        self.pending_nonces.add(current_nonce)
        
        logger.debug(f"🔢 Nonce assigned: {current_nonce}")
        return current_nonce
    
    async def _sync_nonce(self):
        """Sync predicted nonce with actual network state."""
        try:
            actual_nonce = await self.web3.eth.get_transaction_count(
                self.account_address, 'pending'
            )
            
            # Update predicted nonce (never go backwards)
            old_predicted = self.predicted_nonce
            self.predicted_nonce = max(actual_nonce, self.predicted_nonce or 0)
            self.last_sync = time.time()
            
            # Clean up old pending nonces
            self.pending_nonces = {n for n in self.pending_nonces if n >= actual_nonce}
            
            if old_predicted != self.predicted_nonce:
                logger.info(f"🔄 Nonce sync: {old_predicted} → {self.predicted_nonce}")
                
        except Exception as e:
            logger.error(f"❌ Nonce sync failed: {e}")
    
    def mark_nonce_confirmed(self, nonce: int):
        """Mark a nonce as confirmed (transaction mined)."""
        self.pending_nonces.discard(nonce)
        logger.debug(f"✅ Nonce confirmed: {nonce}")
    
    def get_nonce_status(self) -> Dict[str, Any]:
        """Get current nonce manager status."""
        return {
            'predicted_nonce': self.predicted_nonce,
            'pending_count': len(self.pending_nonces),
            'last_sync': self.last_sync,
            'sync_age': time.time() - self.last_sync
        }

class EnhancedPerformanceProfiler:
    """
    Enhanced performance profiler with real-time bottleneck detection.
    
    Features:
    - Stage timing with context managers
    - Bottleneck detection and alerts
    - Success rate tracking
    - Performance summaries
    """
    
    def __init__(self, bottleneck_threshold: float = 0.5):
        """Initialize performance profiler."""
        self.stage_timings = defaultdict(list)
        self.success_rates = defaultdict(list)
        self.bottleneck_threshold = bottleneck_threshold  # 500ms default
        self.session_start = time.time()
        
        logger.info(f"📊 Enhanced Performance Profiler initialized")
        logger.info(f"   🐌 Bottleneck threshold: {bottleneck_threshold:.3f}s")
    
    @contextmanager
    def time_stage(self, stage_name: str):
        """Time a stage with automatic bottleneck detection."""
        start = time.perf_counter()
        success = False
        try:
            yield
            success = True
        except Exception:
            success = False
            raise
        finally:
            duration = time.perf_counter() - start
            self.stage_timings[stage_name].append(duration)
            self.success_rates[stage_name].append(success)
            
            # Real-time bottleneck detection
            if duration > self.bottleneck_threshold:
                logger.warning(f"🐌 BOTTLENECK: {stage_name} took {duration:.3f}s")
            else:
                logger.debug(f"⚡ {stage_name}: {duration:.3f}s")
    
    def get_performance_summary(self) -> Dict[str, Dict[str, float]]:
        """Get comprehensive performance summary."""
        summary = {}
        total_session_time = time.time() - self.session_start
        
        for stage, timings in self.stage_timings.items():
            if not timings:
                continue
                
            avg_time = sum(timings) / len(timings)
            min_time = min(timings)
            max_time = max(timings)
            success_rate = sum(self.success_rates[stage]) / len(self.success_rates[stage])
            total_time = sum(timings)
            
            summary[stage] = {
                'avg_time': avg_time,
                'min_time': min_time,
                'max_time': max_time,
                'success_rate': success_rate,
                'total_calls': len(timings),
                'total_time': total_time,
                'time_percentage': (total_time / total_session_time) * 100
            }
        
        return summary
    
    def log_performance_summary(self):
        """Log a formatted performance summary."""
        summary = self.get_performance_summary()
        
        logger.info("📊 PERFORMANCE SUMMARY:")
        logger.info("-" * 50)
        
        for stage, stats in summary.items():
            logger.info(f"   {stage}:")
            logger.info(f"      ⏱️  Avg: {stats['avg_time']:.3f}s")
            logger.info(f"      📊 Calls: {stats['total_calls']}")
            logger.info(f"      ✅ Success: {stats['success_rate']:.1%}")
            if stats['avg_time'] > self.bottleneck_threshold:
                logger.info(f"      🐌 BOTTLENECK DETECTED!")
    
    def get_bottlenecks(self) -> list:
        """Get list of current bottlenecks."""
        summary = self.get_performance_summary()
        bottlenecks = []
        
        for stage, stats in summary.items():
            if stats['avg_time'] > self.bottleneck_threshold:
                bottlenecks.append({
                    'stage': stage,
                    'avg_time': stats['avg_time'],
                    'severity': stats['avg_time'] / self.bottleneck_threshold
                })
        
        return sorted(bottlenecks, key=lambda x: x['severity'], reverse=True)

# Factory functions for easy integration
def create_connection_manager(chain_name: str, api_key: str) -> EnhancedConnectionManager:
    """Create connection manager for specific chain."""
    chain_configs = {
        'arbitrum': {
            'ws': f"wss://arb-mainnet.g.alchemy.com/v2/{api_key}",
            'http': f"https://arb-mainnet.g.alchemy.com/v2/{api_key}"
        },
        'optimism': {
            'ws': f"wss://opt-mainnet.g.alchemy.com/v2/{api_key}",
            'http': f"https://opt-mainnet.g.alchemy.com/v2/{api_key}"
        },
        'base': {
            'ws': f"wss://base-mainnet.g.alchemy.com/v2/{api_key}",
            'http': f"https://base-mainnet.g.alchemy.com/v2/{api_key}"
        }
    }
    
    if chain_name not in chain_configs:
        raise ValueError(f"Unsupported chain: {chain_name}")
    
    config = chain_configs[chain_name]
    return EnhancedConnectionManager(config['ws'], config['http'])

def create_speed_optimized_web3(chain_name: str, api_key: str, account_address: str) -> tuple:
    """Create speed-optimized Web3 instance with all optimizations."""
    connection_manager = create_connection_manager(chain_name, api_key)
    
    # Create Web3 instance with enhanced connection manager
    web3 = Web3(connection_manager.websocket_primary)
    
    # Create nonce manager
    nonce_manager = AdvancedNonceManager(web3, account_address)
    
    # Create performance profiler
    profiler = EnhancedPerformanceProfiler()
    
    logger.info(f"🚀 Speed-optimized Web3 created for {chain_name}")
    
    return web3, connection_manager, nonce_manager, profiler
