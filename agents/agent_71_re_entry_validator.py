"""
AlphaEdge Agent 71 – Re-Entry Validator
Validate re-entry (TPS≥82, breakout confirmation, 7-day cooldown), calculate size
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ReEntryValidator:
    """Re-Entry Validator – Validates re-entry conditions and calculates size"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "re_entry_validator"
        self.running = False
        
        # Validation state
        self.validations = []
        self.re_entry_history = []
        self.cooldown_tracking = {}
        
        # Configuration
        self.config = {
            'min_tps': 82,
            'cooldown_days': 7,
            'breakout_confirmation_required': True,
            'min_breakout_confidence': 0.7,
            'max_re_entry_size': 0.06  # 6%
        }
        
    async def start(self):
        """Start the re-entry validator"""
        logger.info("Re-Entry Validator starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("re_entry_check", self.handle_re_entry_check)
        await self.event_bus.subscribe("re_entry_request", self.handle_re_entry_request)
        await self.event_bus.subscribe("validation_status_request", self.handle_validation_status)
        
        # Start validation cycle
        asyncio.create_task(self.run_validation_cycle())
        
        logger.info("Re-Entry Validator running")
        
    async def stop(self):
        """Stop the re-entry validator"""
        self.running = False
        logger.info("Re-Entry Validator stopped")
        
    async def run_validation_cycle(self):
        """Run regular validation cycle"""
        while self.running:
            try:
                # Update cooldown tracking
                await self.update_cooldowns()
                
                # Clean old validations
                await self.clean_old_validations()
                
                # Publish validator update
                await self.publish_validator_update()
                
            except Exception as e:
                logger.error(f"Validation cycle error: {e}")
                
            await asyncio.sleep(300)  # Every 5 minutes
            
    async def handle_re_entry_check(self, event: Event):
        """Handle re-entry check requests"""
        if not self.running:
            return
            
        token = event.data.get('token')
        entry_data = event.data.get('entry_data', {})
        
        # Validate re-entry
        result = await self.validate_re_entry(token, entry_data)
        
        response = Event(
            event_type="re_entry_check_response",
            data={
                'token': token,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_re_entry_request(self, event: Event):
        """Handle re-entry requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        token = event.data.get('token')
        entry_data = event.data.get('entry_data', {})
        
        # Validate re-entry
        validation = await self.validate_re_entry(token, entry_data)
        
        if validation['valid']:
            # Calculate re-entry size
            size = await self.calculate_re_entry_size(token, entry_data)
            validation['size'] = size
            
            # Record re-entry
            self.re_entry_history.append({
                'token': token,
                'validation': validation,
                'timestamp': datetime.now().isoformat()
            })
            
        response = Event(
            event_type="re_entry_response",
            data={
                'request_id': request_id,
                'token': token,
                'validation': validation,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_validation_status(self, event: Event):
        """Handle validation status requests"""
        if not self.running:
            return
            
        token = event.data.get('token')
        
        if token:
            validations = [v for v in self.validations if v['token'] == token]
        else:
            validations = self.validations
            
        response = Event(
            event_type="validation_status_response",
            data={
                'token': token,
                'validations': validations[-10:],
                'total_validations': len(validations),
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def validate_re_entry(self, token: str, entry_data: Dict) -> Dict:
        """Validate re-entry conditions"""
        issues = []
        warnings = []
        
        # Check cooldown
        if token in self.cooldown_tracking:
            cooldown_until = self.cooldown_tracking[token]
            if datetime.now() < cooldown_until:
                remaining = (cooldown_until - datetime.now()).days
                issues.append(f"Cooldown active ({remaining} days remaining)")
                
        # Check TPS
        tps = entry_data.get('tps', 0)
        if tps < self.config['min_tps']:
            issues.append(f"TPS {tps} < {self.config['min_tps']}")
            
        # Check breakout confirmation
        if self.config['breakout_confirmation_required']:
            breakout_confirmed = entry_data.get('breakout_confirmed', False)
            breakout_confidence = entry_data.get('breakout_confidence', 0)
            
            if not breakout_confirmed:
                issues.append("Breakout not confirmed")
            elif breakout_confidence < self.config['min_breakout_confidence']:
                warnings.append(f"Breakout confidence {breakout_confidence:.2f} < {self.config['min_breakout_confidence']}")
                
        # Check volume
        volume_trend = entry_data.get('volume_trend', 'neutral')
        if volume_trend == 'declining':
            warnings.append("Volume trend declining")
            
        # Check sentiment
        sentiment = entry_data.get('sentiment', 50)
        if sentiment < 40:
            warnings.append(f"Sentiment {sentiment} < 40")
            
        # Determine if valid
        valid = len(issues) == 0
        
        validation = {
            'valid': valid,
            'issues': issues,
            'warnings': warnings,
            'token': token,
            'tps': tps,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store validation
        self.validations.append(validation)
        
        return validation
        
    async def calculate_re_entry_size(self, token: str, entry_data: Dict) -> float:
        """Calculate re-entry position size"""
        base_size = 0.04  # 4% base
        
        # Adjust based on TPS
        tps = entry_data.get('tps', 0)
        if tps >= 90:
            base_size *= 1.2
        elif tps >= 85:
            base_size *= 1.1
            
        # Adjust based on confidence
        confidence = entry_data.get('breakout_confidence', 0.5)
        base_size *= confidence
        
        # Adjust based on volatility
        volatility = entry_data.get('volatility', 0.3)
        base_size *= (1 / (1 + volatility))
        
        # Ensure within limits
        size = min(self.config['max_re_entry_size'], max(0.01, base_size))
        
        return size
        
    async def update_cooldowns(self):
        """Update cooldown tracking"""
        current_time = datetime.now()
        
        # Remove expired cooldowns
        expired = []
        for token, cooldown_until in self.cooldown_tracking.items():
            if current_time > cooldown_until:
                expired.append(token)
                
        for token in expired:
            del self.cooldown_tracking[token]
            
    async def clean_old_validations(self):
        """Clean old validations"""
        # Keep last 1000 validations
        if len(self.validations) > 1000:
            self.validations = self.validations[-1000:]
            
    async def publish_validator_update(self):
        """Publish validator data update"""
        validator_data = {
            'validations': self.validations[-5:],
            're_entry_history': self.re_entry_history[-5:],
            'cooldown_tracking': self.cooldown_tracking,
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="re_entry_validator_update",
            data=validator_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get re-entry validator status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'validations': len(self.validations),
            're_entries': len(self.re_entry_history),
            'cooldowns': len(self.cooldown_tracking),
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }
