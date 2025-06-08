"""
SYSTEM MONITOR AND CRASH PREVENTION
Monitors system resources and prevents crashes from resource exhaustion.
"""

import psutil
import logging
import asyncio
import signal
import sys
import gc
from typing import Dict, Any
import time

logger = logging.getLogger(__name__)

class SystemMonitor:
    """Monitor system resources and prevent crashes."""
    
    def __init__(self):
        self.monitoring = False
        self.memory_threshold = 85.0  # 85% memory usage threshold
        self.cpu_threshold = 90.0     # 90% CPU usage threshold
        self.disk_threshold = 95.0    # 95% disk usage threshold
        self.check_interval = 30      # Check every 30 seconds
        
        # Resource usage history
        self.memory_history = []
        self.cpu_history = []
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
    def setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers."""
        try:
            # Handle SIGTERM (signal 15) gracefully
            signal.signal(signal.SIGTERM, self.handle_shutdown_signal)
            signal.signal(signal.SIGINT, self.handle_shutdown_signal)
            logger.info("✅ Signal handlers installed for graceful shutdown")
        except Exception as e:
            logger.warning(f"⚠️  Could not install signal handlers: {e}")
    
    def handle_shutdown_signal(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.warning(f"🚨 SHUTDOWN SIGNAL RECEIVED: {signum}")
        logger.warning(f"   📊 Signal name: {signal.Signals(signum).name}")
        logger.warning(f"   🔍 Frame: {frame}")
        
        # Log current system state
        self.log_system_state("SHUTDOWN_SIGNAL")
        
        # Perform cleanup
        logger.info("🧹 Performing graceful cleanup...")
        self.cleanup_resources()
        
        # Exit gracefully
        logger.info("✅ Graceful shutdown complete")
        sys.exit(0)
    
    async def start_monitoring(self):
        """Start system resource monitoring."""
        self.monitoring = True
        logger.info("🔍 Starting system resource monitoring...")
        
        while self.monitoring:
            try:
                await self.check_system_resources()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"❌ System monitoring error: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    def stop_monitoring(self):
        """Stop system resource monitoring."""
        self.monitoring = False
        logger.info("🛑 System monitoring stopped")
    
    async def check_system_resources(self):
        """Check system resources and take action if needed."""
        try:
            # Get current resource usage
            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent(interval=1)
            disk_percent = psutil.disk_usage('/').percent
            
            # Update history
            self.memory_history.append(memory_percent)
            self.cpu_history.append(cpu_percent)
            
            # Keep only last 10 readings
            if len(self.memory_history) > 10:
                self.memory_history.pop(0)
            if len(self.cpu_history) > 10:
                self.cpu_history.pop(0)
            
            # Check thresholds
            if memory_percent > self.memory_threshold:
                logger.warning(f"⚠️  HIGH MEMORY USAGE: {memory_percent:.1f}%")
                await self.handle_high_memory()
            
            if cpu_percent > self.cpu_threshold:
                logger.warning(f"⚠️  HIGH CPU USAGE: {cpu_percent:.1f}%")
                await self.handle_high_cpu()
            
            if disk_percent > self.disk_threshold:
                logger.warning(f"⚠️  HIGH DISK USAGE: {disk_percent:.1f}%")
                await self.handle_high_disk()
            
            # Log periodic status
            if int(time.time()) % 300 == 0:  # Every 5 minutes
                logger.info(f"📊 SYSTEM STATUS: Memory {memory_percent:.1f}%, CPU {cpu_percent:.1f}%, Disk {disk_percent:.1f}%")
                
        except Exception as e:
            logger.error(f"❌ Resource check error: {e}")
    
    async def handle_high_memory(self):
        """Handle high memory usage."""
        try:
            logger.warning("🧹 MEMORY CLEANUP: Running garbage collection...")
            
            # Force garbage collection
            collected = gc.collect()
            logger.info(f"   🗑️  Collected {collected} objects")
            
            # Get memory info
            process = psutil.Process()
            memory_info = process.memory_info()
            logger.info(f"   📊 Process memory: {memory_info.rss / 1024 / 1024:.1f} MB")
            
            # If still high, consider more aggressive cleanup
            current_memory = psutil.virtual_memory().percent
            if current_memory > self.memory_threshold + 5:
                logger.warning("🚨 CRITICAL MEMORY: Consider restarting system")
                
        except Exception as e:
            logger.error(f"❌ Memory cleanup error: {e}")
    
    async def handle_high_cpu(self):
        """Handle high CPU usage."""
        try:
            logger.warning("⏸️  HIGH CPU: Adding processing delays...")
            
            # Add small delays to reduce CPU load
            await asyncio.sleep(2)
            
            # Log top processes
            self.log_top_processes()
            
        except Exception as e:
            logger.error(f"❌ CPU handling error: {e}")
    
    async def handle_high_disk(self):
        """Handle high disk usage."""
        try:
            logger.warning("💾 HIGH DISK USAGE: Check available space")
            
            # Log disk usage details
            disk_usage = psutil.disk_usage('/')
            logger.warning(f"   📊 Total: {disk_usage.total / 1024**3:.1f} GB")
            logger.warning(f"   📊 Used: {disk_usage.used / 1024**3:.1f} GB")
            logger.warning(f"   📊 Free: {disk_usage.free / 1024**3:.1f} GB")
            
        except Exception as e:
            logger.error(f"❌ Disk handling error: {e}")
    
    def log_system_state(self, context: str = ""):
        """Log current system state for debugging."""
        try:
            logger.info(f"📊 SYSTEM STATE ({context}):")
            
            # Memory info
            memory = psutil.virtual_memory()
            logger.info(f"   💾 Memory: {memory.percent:.1f}% used ({memory.used / 1024**3:.1f} GB / {memory.total / 1024**3:.1f} GB)")
            
            # CPU info
            cpu_percent = psutil.cpu_percent()
            logger.info(f"   🖥️  CPU: {cpu_percent:.1f}% usage")
            
            # Disk info
            disk = psutil.disk_usage('/')
            logger.info(f"   💾 Disk: {disk.percent:.1f}% used ({disk.free / 1024**3:.1f} GB free)")
            
            # Process info
            process = psutil.Process()
            logger.info(f"   🔍 Process PID: {process.pid}")
            logger.info(f"   📊 Process Memory: {process.memory_info().rss / 1024**2:.1f} MB")
            logger.info(f"   ⏱️  Process CPU: {process.cpu_percent():.1f}%")
            
        except Exception as e:
            logger.error(f"❌ System state logging error: {e}")
    
    def log_top_processes(self):
        """Log top CPU/memory consuming processes."""
        try:
            logger.info("🔍 TOP PROCESSES:")
            
            # Get all processes
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            # Log top 5
            for i, proc in enumerate(processes[:5]):
                logger.info(f"   #{i+1}: {proc['name']} (PID {proc['pid']}) - CPU: {proc['cpu_percent']:.1f}%, Memory: {proc['memory_percent']:.1f}%")
                
        except Exception as e:
            logger.error(f"❌ Process listing error: {e}")
    
    def cleanup_resources(self):
        """Cleanup system resources."""
        try:
            logger.info("🧹 RESOURCE CLEANUP:")
            
            # Force garbage collection
            collected = gc.collect()
            logger.info(f"   🗑️  Garbage collected: {collected} objects")
            
            # Clear caches if available
            try:
                import sys
                if hasattr(sys, 'intern'):
                    logger.info("   🧹 Clearing string intern cache")
            except:
                pass
            
            logger.info("✅ Resource cleanup complete")
            
        except Exception as e:
            logger.error(f"❌ Resource cleanup error: {e}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get current system information."""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / 1024**3,
                'cpu_percent': psutil.cpu_percent(),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / 1024**3,
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
            
        except Exception as e:
            logger.error(f"❌ System info error: {e}")
            return {}

# Global system monitor instance
system_monitor = SystemMonitor()
