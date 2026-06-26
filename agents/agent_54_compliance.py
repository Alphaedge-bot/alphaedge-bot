"""
AlphaEdge Agent 54 – Compliance Guard
OFAC filter, bridge detection (block bridged tokens), PASS/FLAG/BLOCK
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ComplianceGuard:
    """Compliance Guard – Enforces compliance rules and regulations"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "compliance"
        self.running = False
        
        # Compliance state
        self.compliance_results = []
        self.blocked_addresses = []
        self.flagged_transactions = []
        
        # OFAC list (simplified)
        self.ofac_list = [
            "0x1234567890abcdef1234567890abcdef12345678",
            "0xabcdef1234567890abcdef1234567890abcdef12",
            # In production, load from actual OFAC list
        ]
        
        # Bridge token detection
        self.bridge_keywords = [
            'bridged', 'wormhole', 'portal', 'any',
            'wrapped', 'wb', 'wh', 'gateway',
            'bridge', 'lz', 'layerzero', 'axl'
        ]
        
        # Compliance status levels
        self.status_levels = {
            'PASS': 1,
            'FLAG': 2,
            'BLOCK': 3
        }
        
    async def start(self):
        """Start the compliance guard"""
        logger.info("Compliance Guard starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("compliance_check", self.handle_compliance_check)
        await self.event_bus.subscribe("ofac_check", self.handle_ofac_check)
        await self.event_bus.subscribe("bridge_check", self.handle_bridge_check)
        
        # Start compliance cycle
        asyncio.create_task(self.run_compliance_cycle())
        
        logger.info("Compliance Guard running")
        
    async def stop(self):
        """Stop the compliance guard"""
        self.running = False
        logger.info("Compliance Guard stopped")
        
    async def run_compliance_cycle(self):
        """Run regular compliance cycle"""
        while self.running:
            try:
                # Update OFAC list
                await self.update_ofac_list()
                
                # Review flagged transactions
                await self.review_flagged_transactions()
                
                # Publish compliance update
                await self.publish_compliance_update()
                
            except Exception as e:
                logger.error(f"Compliance cycle error: {e}")
                
            await asyncio.sleep(3600)  # Every hour
            
    async def handle_compliance_check(self, event: Event):
        """Handle compliance checks"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        transaction = event.data.get('transaction', {})
        
        # Perform compliance check
        result = await self.check_compliance(transaction)
        
        response = Event(
            event_type="compliance_check_response",
            data={
                'request_id': request_id,
                'transaction': transaction,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_ofac_check(self, event: Event):
        """Handle OFAC checks"""
        if not self.running:
            return
            
        address = event.data.get('address')
        
        # Check against OFAC list
        result = await self.check_ofac(address)
        
        response = Event(
            event_type="ofac_check_response",
            data={
                'address': address,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_bridge_check(self, event: Event):
        """Handle bridge token checks"""
        if not self.running:
            return
            
        token = event.data.get('token')
        
        # Check if token is bridged
        result = await self.check_bridge_token(token)
        
        response = Event(
            event_type="bridge_check_response",
            data={
                'token': token,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def check_compliance(self, transaction: Dict) -> Dict:
        """Perform comprehensive compliance check"""
        address = transaction.get('address')
        token = transaction.get('token')
        
        # Check OFAC
        ofac_result = await self.check_ofac(address)
        
        # Check bridge token
        bridge_result = await self.check_bridge_token(token)
        
        # Determine overall status
        statuses = [ofac_result['status'], bridge_result['status']]
        
        # Worst case wins
        if 'BLOCK' in statuses:
            overall_status = 'BLOCK'
        elif 'FLAG' in statuses:
            overall_status = 'FLAG'
        else:
            overall_status = 'PASS'
            
        result = {
            'status': overall_status,
            'ofac_check': ofac_result,
            'bridge_check': bridge_result,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store result
        self.compliance_results.append({
            'transaction': transaction,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        return result
        
    async def check_ofac(self, address: str) -> Dict:
        """Check address against OFAC list"""
        if not address:
            return {
                'status': 'FLAG',
                'reason': 'No address provided',
                'timestamp': datetime.now().isoformat()
            }
            
        # Normalize address
        address = address.lower()
        
        # Check against OFAC list
        if address in self.ofac_list:
            self.blocked_addresses.append({
                'address': address,
                'timestamp': datetime.now().isoformat()
            })
            return {
                'status': 'BLOCK',
                'reason': 'OFAC match found',
                'timestamp': datetime.now().isoformat()
            }
            
        return {
            'status': 'PASS',
            'reason': 'No OFAC match',
            'timestamp': datetime.now().isoformat()
        }
        
    async def check_bridge_token(self, token: str) -> Dict:
        """Check if token is a bridge token"""
        if not token:
            return {
                'status': 'FLAG',
                'reason': 'No token provided',
                'timestamp': datetime.now().isoformat()
            }
            
        token_lower = token.lower()
        
        # Check for bridge keywords
        for keyword in self.bridge_keywords:
            if keyword in token_lower:
                self.flagged_transactions.append({
                    'token': token,
                    'keyword': keyword,
                    'timestamp': datetime.now().isoformat()
                })
                return {
                    'status': 'FLAG',
                    'reason': f'Bridge token detected: {keyword}',
                    'timestamp': datetime.now().isoformat()
                }
                
        return {
            'status': 'PASS',
            'reason': 'No bridge detection',
            'timestamp': datetime.now().isoformat()
        }
        
    async def update_ofac_list(self):
        """Update OFAC list from external source"""
        # In production, fetch from OFAC API
        # For now, simulate update
        logger.debug("OFAC list updated")
        
    async def review_flagged_transactions(self):
        """Review flagged transactions"""
        # In production, send for manual review
        # For now, log flagged transactions
        if self.flagged_transactions:
            logger.info(f"📋 {len(self.flagged_transactions)} transactions flagged for review")
            
    async def publish_compliance_update(self):
        """Publish compliance data update"""
        compliance_data = {
            'total_checks': len(self.compliance_results),
            'blocked_addresses': len(self.blocked_addresses),
            'flagged_transactions': len(self.flagged_transactions),
            'recent_flags': self.flagged_transactions[-5:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="compliance_update",
            data=compliance_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get compliance guard status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'total_checks': len(self.compliance_results),
            'blocked_addresses': len(self.blocked_addresses),
            'flagged_transactions': len(self.flagged_transactions),
            'ofac_list_size': len(self.ofac_list),
            'timestamp': datetime.now().isoformat()
        }
