"""Simple event bus for arbitrage bot components."""

import asyncio
import logging
from typing import Dict, List, Callable, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class EventBus:
    """Simple event bus for component communication."""
    
    def __init__(self):
        """Initialize the event bus."""
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[Dict[str, Any]] = []
        self.max_history = 1000
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event occurs
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to event type: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Function to remove from subscribers
        """
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from event type: {event_type}")
            except ValueError:
                logger.warning(f"Callback not found for event type: {event_type}")
    
    async def publish(self, event_type: str, data: Any = None) -> None:
        """Publish an event to all subscribers.
        
        Args:
            event_type: Type of event to publish
            data: Event data to send to subscribers
        """
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Notify subscribers
        if event_type in self.subscribers:
            tasks = []
            for callback in self.subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        tasks.append(callback(event))
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback for {event_type}: {e}")
            
            # Wait for async callbacks
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug(f"Published event: {event_type}")
    
    def get_event_history(self, event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get event history.
        
        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return
            
        Returns:
            List of recent events
        """
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e['type'] == event_type]
        
        return events[-limit:] if limit else events
    
    def clear_history(self) -> None:
        """Clear event history."""
        self.event_history.clear()
        logger.info("Event history cleared")
    
    def get_subscriber_count(self, event_type: str = None) -> int:
        """Get number of subscribers.
        
        Args:
            event_type: Specific event type (optional)
            
        Returns:
            Number of subscribers
        """
        if event_type:
            return len(self.subscribers.get(event_type, []))
        else:
            return sum(len(subs) for subs in self.subscribers.values())
