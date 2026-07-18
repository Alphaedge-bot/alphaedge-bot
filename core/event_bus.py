# core/event_bus.py
# AlphaEdge V13.0.7 – Event Bus (In-Memory + Redis)
# Item 20: Redis Message Bus Upgrade

import logging
import asyncio
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Event object for inter-agent communication"""
    event_type: str
    data: Dict[str, Any]
    source: str = "unknown"
    target: str = "all"
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
            
    def to_dict(self) -> Dict:
        return {
            'event_type': self.event_type,
            'data': self.data,
            'source': self.source,
            'target': self.target,
            'timestamp': self.timestamp
        }


class EventBus:
    """
    Central event bus for inter-agent communication
    V13.0.7 – Item 20: Redis Message Bus Upgrade
    """
    
    def __init__(self, redis_config: Dict = None):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[Event] = []
        self.max_history = 1000
        
        # ============================================
        # ITEM 20: REDIS CONFIGURATION
        # ============================================
        self.redis_config = redis_config or {
            'enabled': False,
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': None,
            'pubsub_channel': 'alphaedge_events'
        }
        
        self.redis_client = None
        self.pubsub = None
        self._redis_connected = False
        
    async def connect_redis(self):
        """Connect to Redis if enabled"""
        if not self.redis_config.get('enabled', False):
            logger.info("Redis disabled, using in-memory event bus")
            return
            
        try:
            import redis.asyncio as aioredis
            self.redis_client = await aioredis.from_url(
                f"redis://{self.redis_config['host']}:{self.redis_config['port']}/{self.redis_config['db']}",
                password=self.redis_config.get('password'),
                decode_responses=True
            )
            self._redis_connected = True
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe(self.redis_config['pubsub_channel'])
            
            # Start listening to Redis messages
            asyncio.create_task(self._listen_redis())
            logger.info(f"✅ Redis connected on {self.redis_config['host']}:{self.redis_config['port']}")
            
        except ImportError:
            logger.warning("redis.asyncio not installed. Redis disabled.")
            self.redis_config['enabled'] = False
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_config['enabled'] = False
            
    async def _listen_redis(self):
        """Listen to Redis pubsub messages"""
        if not self._redis_connected or not self.pubsub:
            return
            
        try:
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        event = Event(
                            event_type=data.get('event_type', 'unknown'),
                            data=data.get('data', {}),
                            source=data.get('source', 'redis'),
                            target=data.get('target', 'all'),
                            timestamp=data.get('timestamp')
                        )
                        await self._process_event(event)
                    except Exception as e:
                        logger.error(f"Redis message processing error: {e}")
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
            
    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers
        
        Args:
            event: Event object with type and data
        """
        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
            
        # Process locally
        await self._process_event(event)
        
        # Publish to Redis if enabled
        if self.redis_config.get('enabled', False) and self._redis_connected:
            try:
                await self.redis_client.publish(
                    self.redis_config['pubsub_channel'],
                    json.dumps(event.to_dict())
                )
                logger.debug(f"📡 Published to Redis: {event.event_type}")
            except Exception as e:
                logger.error(f"Redis publish error: {e}")
                
    async def _process_event(self, event: Event) -> None:
        """Process an event locally"""
        # Send to specific target if specified
        if event.target != 'all':
            handlers = self.subscribers.get(f"{event.target}_{event.event_type}", [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"Event handler error for {event.event_type}: {e}")
            return
            
        # Send to all subscribers of this event type
        handlers = self.subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error for {event.event_type}: {e}")
                
    async def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribe to an event type
        
        Args:
            event_type: String identifier for the event
            handler: Async function to handle the event
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
        logger.debug(f"📥 Subscribed to {event_type}")
        
    async def subscribe_target(self, target: str, event_type: str, handler: Callable) -> None:
        """
        Subscribe to a specific target's event type
        
        Args:
            target: Target agent ID
            event_type: Event type
            handler: Async function to handle the event
        """
        key = f"{target}_{event_type}"
        if key not in self.subscribers:
            self.subscribers[key] = []
        self.subscribers[key].append(handler)
        logger.debug(f"📥 Subscribed to {target}.{event_type}")
        
    async def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event type"""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(handler)
                if not self.subscribers[event_type]:
                    del self.subscribers[event_type]
            except ValueError:
                pass
                
    async def get_history(self, event_type: Optional[str] = None) -> List[Event]:
        """Get event history"""
        if event_type:
            return [e for e in self.event_history if e.event_type == event_type]
        return self.event_history
        
    def is_redis_connected(self) -> bool:
        """Check if Redis is connected"""
        return self._redis_connected
        
    async def close(self):
        """Close Redis connection"""
        if self._redis_connected and self.redis_client:
            try:
                await self.redis_client.close()
                self._redis_connected = False
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Redis close error: {e}")
