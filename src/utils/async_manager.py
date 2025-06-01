"""
Async utilities for thread-safe operations
"""

import asyncio
from typing import Any, Optional


class AsyncLock:
    """Async lock for thread-safe operations"""
    
    def __init__(self):
        self._lock = asyncio.Lock()
    
    async def __aenter__(self):
        await self._lock.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()
    
    async def acquire(self):
        """Acquire the lock"""
        await self._lock.acquire()
    
    def release(self):
        """Release the lock"""
        self._lock.release()
    
    def locked(self) -> bool:
        """Check if lock is currently held"""
        return self._lock.locked()


class AsyncEvent:
    """Async event for coordination"""
    
    def __init__(self):
        self._event = asyncio.Event()
    
    async def wait(self, timeout: Optional[float] = None):
        """Wait for event to be set"""
        if timeout:
            await asyncio.wait_for(self._event.wait(), timeout=timeout)
        else:
            await self._event.wait()
    
    def set(self):
        """Set the event"""
        self._event.set()
    
    def clear(self):
        """Clear the event"""
        self._event.clear()
    
    def is_set(self) -> bool:
        """Check if event is set"""
        return self._event.is_set()


class AsyncQueue:
    """Async queue for producer-consumer patterns"""
    
    def __init__(self, maxsize: int = 0):
        self._queue = asyncio.Queue(maxsize=maxsize)
    
    async def put(self, item: Any):
        """Put item in queue"""
        await self._queue.put(item)
    
    async def get(self) -> Any:
        """Get item from queue"""
        return await self._queue.get()
    
    def task_done(self):
        """Mark task as done"""
        self._queue.task_done()
    
    async def join(self):
        """Wait for all tasks to complete"""
        await self._queue.join()
    
    def qsize(self) -> int:
        """Get queue size"""
        return self._queue.qsize()
    
    def empty(self) -> bool:
        """Check if queue is empty"""
        return self._queue.empty()
    
    def full(self) -> bool:
        """Check if queue is full"""
        return self._queue.full()
