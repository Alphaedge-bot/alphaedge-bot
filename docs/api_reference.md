# AlphaEdge V13.0.5 – API Reference

## Overview

This document provides a comprehensive API reference for AlphaEdge V13.0.5. The API is organized by agent functionality and includes both internal and external interfaces.

---

## Table of Contents

1. [Core APIs](#core-apis)
2. [Agent APIs](#agent-apis)
3. [Gold Swap APIs](#gold-swap-apis)
4. [RPC APIs](#rpc-apis)
5. [Risk Management APIs](#risk-management-apis)
6. [Event Bus APIs](#event-bus-apis)
7. [State Manager APIs](#state-manager-apis)
8. [Command APIs](#command-apis)

---

## Core APIs

### EventBus

The central event bus for inter-agent communication.

```python
class EventBus:
    """Central event bus for inter-agent communication"""
    
    async def publish(event: Event) -> None:
        """
        Publish an event to all subscribers
        
        Args:
            event: Event object with type and data
            
        Example:
            event = Event(
                event_type="gold_swap_requested",
                data={'amount': 1000, 'asset': 'paxg'},
                source="command_interface"
            )
            await event_bus.publish(event)
        """
        
    async def subscribe(event_type: str, handler: Callable) -> None:
        """
        Subscribe to an event type
        
        Args:
            event_type: String identifier for the event
            handler: Async function to handle the event
            
        Example:
            await event_bus.subscribe("depeg_detected", self.handle_depeg)
        """
        
    async def unsubscribe(event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event type"""
