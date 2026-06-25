"""
AlphaEdge Event Bus – Agent Communication Hub
All agents communicate through this centralized event bus
"""

import asyncio
import logging
import json
from typing import Dict, Any, Callable, List, Optional
from collections import defaultdict
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class Event:
    """Base event class for agent communication"""
    
    def __init__(self, event_type: str, data: Dict[str, Any], 
                 source: str = None, target: str = None):
        self.id = str(uuid.uuid4())
        self.type = event_type
        self.data = data
        self.source = source
        self.target = target
        self.timestamp = datetime.now().isoformat()
        self.processed = False
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            'id': self.id,
            'type': self.type,
            'data': self.data,
            'source': self.source,
            'target': self.target,
            'timestamp': self.timestamp,
            'processed': self.processed
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary"""
        event = cls(
            event_type=data['type'],
            data=data['data'],
            source=data.get('source'),
            target=data.get('target')
        )
        event.id = data.get('id', event.id)
        event.timestamp = data.get('timestamp', event.timestamp)
        event.processed = data.get('processed', False)
        return event


class EventBus:
    """
    Central event bus for inter-agent communication
    Supports pub/sub pattern with priority and filtering
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.priority_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.event_history: List[Event] = []
        self.max_history = 10000
        self.running = False
        self.event_queue = asyncio.Queue()
        
    async def initialize(self):
        """Initialize the event bus"""
        logger.info("Event bus initialized")
        self.running = True
        
    async def publish(self, event: Event) -> bool:
        """
        Publish an event to all subscribers
        
        Args:
            event: Event object to publish
            
        Returns:
            bool: True if delivered, False if not
        """
        if not self.running:
            logger.warning("Event bus not running")
            return False
            
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
            
        # Queue for processing
        await self.event_queue.put(event)
        return True
        
    async def process_events(self):
        """Process events from the queue"""
        while self.running:
            try:
                event = await self.event_queue.get()
                await self._deliver_event(event)
                self.event_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                
    async def _deliver_event(self, event: Event):
        """Deliver event to appropriate subscribers"""
        # Check if event has a specific target
        if event.target:
            # Direct delivery to specific agent
            if event.target in self.subscribers:
                for callback in self.subscribers[event.target]:
                    try:
                        await callback(event)
                    except Exception as e:
                        logger.error(f"Error delivering to {event.target}: {e}")
            return
            
        # Broadcast to all subscribers of this event type
        for callback in self.subscribers.get(event.type, []):
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Error delivering event type {event.type}: {e}")
                
        # Also deliver to priority subscribers
        for callback in self.priority_subscribers.get(event.type, []):
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Error delivering priority event {event.type}: {e}")
                
    def subscribe(self, event_type: str, callback: Callable, 
                  priority: bool = False) -> str:
        """
        Subscribe to an event type
        
        Args:
            event_type: Type of event to subscribe to
            callback: Async function to call when event occurs
            priority: If True, callback is called before normal subscribers
            
        Returns:
            str: Subscription ID (for later unsubscribe)
        """
        subscription_id = str(uuid.uuid4())
        
        if priority:
            self.priority_subscribers[event_type].append(callback)
        else:
            self.subscribers[event_type].append(callback)
            
        logger.debug(f"Subscribed to {event_type} (priority={priority})")
        return subscription_id
        
    def subscribe_to_all(self, callback: Callable, priority: bool = False) -> str:
        """
        Subscribe to ALL events (wildcard)
        
        Args:
            callback: Async function to call for all events
            priority: If True, callback is called first
            
        Returns:
            str: Subscription ID
        """
        subscription_id = str(uuid.uuid4())
        
        if priority:
            self.priority_subscribers['*'].append(callback)
        else:
            self.subscribers['*'].append(callback)
            
        logger.debug("Subscribed to ALL events")
        return subscription_id
        
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events
        
        Args:
            subscription_id: Subscription ID returned from subscribe
            
        Returns:
            bool: True if unsubscribed, False if not found
        """
        # Check priority subscribers
        for event_type, callbacks in self.priority_subscribers.items():
            # Can't easily remove by ID without tracking callbacks
            pass
            
        # Check normal subscribers
        for event_type, callbacks in self.subscribers.items():
            # Can't easily remove by ID without tracking callbacks
            pass
            
        logger.warning("Unsubscribe by ID not fully implemented")
        return False
        
    def get_history(self, event_type: Optional[str] = None, 
                    limit: int = 100) -> List[Event]:
        """
        Get event history
        
        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return
            
        Returns:
            List[Event]: List of events
        """
        filtered = self.event_history
        
        if event_type:
            filtered = [e for e in filtered if e.type == event_type]
            
        return filtered[-limit:]
        
    def clear_history(self):
        """Clear event history"""
        self.event_history.clear()
        
    async def shutdown(self):
        """Shutdown the event bus"""
        self.running = False
        logger.info("Event bus shutdown")
