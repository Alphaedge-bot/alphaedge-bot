"""
AlphaEdge Agent 38 – Zero-Trust Auditor
Cryptographic signing + verification of all inter-agent messages
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import hmac
import base64
import json
import os

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ZeroTrustAuditor:
    """Zero-Trust Auditor – Cryptographic verification of all inter-agent messages"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "zero_trust"
        self.running = False
        
        # Audit state
        self.verified_messages = 0
        self.failed_verifications = 0
        self.audit_log = []
        self.suspicious_activity = []
        
        # Cryptographic keys
        self.master_key = os.getenv('ZERO_TRUST_KEY', 'default_key_please_change')
        self.agent_keys = {}
        
    async def start(self):
        """Start the zero-trust auditor"""
        logger.info("Zero-Trust Auditor starting...")
        self.running = True
        
        # Initialize agent keys
        await self.initialize_keys()
        
        # Subscribe to events
        await self.event_bus.subscribe("message_audit", self.handle_message_audit)
        await self.event_bus.subscribe("signature_request", self.handle_signature_request)
        await self.event_bus.subscribe("verification_request", self.handle_verification_request)
        await self.event_bus.subscribe("audit_log_request", self.handle_audit_log_request)
        
        # Start audit cycle
        asyncio.create_task(self.run_audit_cycle())
        
        logger.info("Zero-Trust Auditor running")
        
    async def stop(self):
        """Stop the zero-trust auditor"""
        self.running = False
        logger.info("Zero-Trust Auditor stopped")
        
    async def initialize_keys(self):
        """Initialize cryptographic keys for agents"""
        # In production, use a proper key management system
        # For now, derive keys from master key
        for agent_id in range(73):  # 00-72
            agent_name = f"agent_{agent_id:02d}"
            key = hashlib.sha256(f"{self.master_key}_{agent_name}".encode()).digest()
            self.agent_keys[agent_name] = key
            
    async def run_audit_cycle(self):
        """Run regular audit cycle"""
        while self.running:
            try:
                # Check for replay attacks
                await self.check_replay_attacks()
                
                # Check for key compromise
                await self.check_key_compromise()
                
                # Publish audit update
                await self.publish_audit_update()
                
            except Exception as e:
                logger.error(f"Audit cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def handle_message_audit(self, event: Event):
        """Handle message audit events"""
        if not self.running:
            return
            
        message = event.data.get('message')
        signature = event.data.get('signature')
        sender = event.source
        
        # Verify signature
        verified = await self.verify_signature(sender, message, signature)
        
        if verified:
            self.verified_messages += 1
        else:
            self.failed_verifications += 1
            self.suspicious_activity.append({
                'type': 'invalid_signature',
                'sender': sender,
                'timestamp': datetime.now().isoformat()
            })
            logger.warning(f"⚠️ Invalid signature from {sender}")
            
        # Store in audit log
        self.audit_log.append({
            'sender': sender,
            'verified': verified,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep last 10000 audit entries
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-10000:]
            
        # If verification failed, block message
        if not verified:
            event.processed = True  # Mark as processed to prevent further handling
            
    async def handle_signature_request(self, event: Event):
        """Handle signature requests"""
        if not self.running:
            return
            
        message = event.data.get('message')
        sender = event.source
        
        signature = await self.sign_message(sender, message)
        
        response = Event(
            event_type="signature_response",
            data={
                'signature': signature,
                'message': message,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_verification_request(self, event: Event):
        """Handle verification requests"""
        if not self.running:
            return
            
        message = event.data.get('message')
        signature = event.data.get('signature')
        sender = event.data.get('sender')
        
        verified = await self.verify_signature(sender, message, signature)
        
        response = Event(
            event_type="verification_response",
            data={
                'verified': verified,
                'message': message,
                'sender': sender,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def sign_message(self, sender: str, message: Dict) -> str:
        """Sign a message with HMAC-SHA256"""
        # Get sender's key
        key = self.agent_keys.get(sender)
        if not key:
            logger.warning(f"No key found for {sender}")
            return None
            
        # Serialize message
        message_json = json.dumps(message, sort_keys=True)
        
        # Create HMAC
        signature = hmac.new(key, message_json.encode(), hashlib.sha256).hexdigest()
        
        return signature
        
    async def verify_signature(self, sender: str, message: Dict, signature: str) -> bool:
        """Verify a message signature"""
        if not signature:
            return False
            
        # Get sender's key
        key = self.agent_keys.get(sender)
        if not key:
            logger.warning(f"No key found for {sender}")
            return False
            
        # Serialize message
        message_json = json.dumps(message, sort_keys=True)
        
        # Compute expected signature
        expected = hmac.new(key, message_json.encode(), hashlib.sha256).hexdigest()
        
        # Compare in constant time to prevent timing attacks
        return hmac.compare_digest(signature, expected)
        
    async def check_replay_attacks(self):
        """Check for replay attacks"""
        # In production, implement nonce/timestamp tracking
        # For now, check for duplicate messages
        messages_seen = {}
        
        for entry in self.audit_log[-100:]:
            # Simple replay detection based on sender and timestamp
            key = f"{entry['sender']}_{entry['timestamp']}"
            if key in messages_seen:
                self.suspicious_activity.append({
                    'type': 'replay_attack',
                    'sender': entry['sender'],
                    'timestamp': datetime.now().isoformat()
                })
                logger.warning(f"⚠️ Replay attack detected from {entry['sender']}")
            messages_seen[key] = True
            
    async def check_key_compromise(self):
        """Check for key compromise"""
        # In production, implement key rotation
        # For now, check for unusual activity patterns
        if self.failed_verifications > 10:
            self.suspicious_activity.append({
                'type': 'possible_key_compromise',
                'failed_count': self.failed_verifications,
                'timestamp': datetime.now().isoformat()
            })
            logger.warning("⚠️ Possible key compromise detected")
            
    async def handle_audit_log_request(self, event: Event):
        """Handle audit log requests"""
        if not self.running:
            return
            
        response = Event(
            event_type="audit_log_response",
            data={
                'audit_log': self.audit_log[-100:],
                'suspicious_activity': self.suspicious_activity[-10:],
                'verified_messages': self.verified_messages,
                'failed_verifications': self.failed_verifications,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def publish_audit_update(self):
        """Publish audit data update"""
        audit_data = {
            'verified_messages': self.verified_messages,
            'failed_verifications': self.failed_verifications,
            'suspicious_activity': self.suspicious_activity[-5:],
            'audit_log_size': len(self.audit_log),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="audit_update",
            data=audit_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get zero-trust auditor status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'verified_messages': self.verified_messages,
            'failed_verifications': self.failed_verifications,
            'suspicious_activity_count': len(self.suspicious_activity),
            'audit_log_size': len(self.audit_log),
            'timestamp': datetime.now().isoformat()
        }
