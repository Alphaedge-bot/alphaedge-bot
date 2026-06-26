"""
AlphaEdge Agent 55 – Inscription Scanner
BTC blockspace monitoring (mempool.space), congestion level, fee spike alert
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class InscriptionScanner:
    """Inscription Scanner – Monitors BTC blockspace and inscription activity"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "inscription_scanner"
        self.running = False
        
        # Scanner state
        self.mempool_data = {}
        self.congestion_history = []
        self.fee_spikes = []
        self.inscription_alerts = []
        
        # Configuration
        self.config = {
            'monitor_interval': 30,  # seconds
            'congestion_threshold': 0.7,  # 70% full
            'fee_spike_threshold': 2.0,  # 2x normal
            'alert_cooldown': 300  # 5 minutes
        }
        
        # Mempool.space endpoints
        self.endpoints = {
            'mempool': 'https://mempool.space/api/v1/mempool',
            'fees': 'https://mempool.space/api/v1/fees/recommended',
            'blockchain': 'https://mempool.space/api/v1/blockchain'
        }
        
    async def start(self):
        """Start the inscription scanner"""
        logger.info("Inscription Scanner starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("inscription_request", self.handle_inscription_request)
        await self.event_bus.subscribe("mempool_status_request", self.handle_mempool_status)
        await self.event_bus.subscribe("fee_alert_request", self.handle_fee_alert_request)
        
        # Start scanning cycle
        asyncio.create_task(self.run_scanning_cycle())
        
        logger.info("Inscription Scanner running")
        
    async def stop(self):
        """Stop the inscription scanner"""
        self.running = False
        logger.info("Inscription Scanner stopped")
        
    async def run_scanning_cycle(self):
        """Run regular scanning cycle"""
        last_alert_time = 0
        
        while self.running:
            try:
                # Scan mempool
                await self.scan_mempool()
                
                # Check congestion
                await self.check_congestion()
                
                # Check fee spikes
                fee_spike = await self.check_fee_spikes()
                
                # Send alerts if needed
                current_time = datetime.now().timestamp()
                if fee_spike and (current_time - last_alert_time) > self.config['alert_cooldown']:
                    await self.send_fee_alert(fee_spike)
                    last_alert_time = current_time
                    
                # Publish scanner update
                await self.publish_scanner_update()
                
            except Exception as e:
                logger.error(f"Scanning cycle error: {e}")
                
            await asyncio.sleep(self.config['monitor_interval'])
            
    async def handle_inscription_request(self, event: Event):
        """Handle inscription requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        action = event.data.get('action')
        
        if action == 'scan':
            result = await self.scan_mempool()
        elif action == 'congestion':
            result = await self.check_congestion()
        else:
            result = {'status': 'unknown_action'}
            
        response = Event(
            event_type="inscription_response",
            data={
                'request_id': request_id,
                'action': action,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_mempool_status(self, event: Event):
        """Handle mempool status requests"""
        if not self.running:
            return
            
        response = Event(
            event_type="mempool_status_response",
            data={
                'mempool_data': self.mempool_data,
                'congestion_history': self.congestion_history[-10:],
                'fee_spikes': self.fee_spikes[-5:],
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_fee_alert_request(self, event: Event):
        """Handle fee alert requests"""
        if not self.running:
            return
            
        response = Event(
            event_type="fee_alert_response",
            data={
                'alerts': self.inscription_alerts[-5:],
                'fee_spikes': self.fee_spikes[-5:],
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def scan_mempool(self) -> Dict:
        """Scan mempool for inscription activity"""
        # In production, fetch from mempool.space
        # For now, simulate data
        
        # Simulate mempool data
        tx_count = random.randint(1000, 50000)
        vsize = random.randint(100000, 5000000)
        fee_rates = [random.randint(10, 200) for _ in range(3)]
        
        self.mempool_data = {
            'tx_count': tx_count,
            'vsize': vsize,
            'fee_rates': {
                'low': fee_rates[0],
                'medium': fee_rates[1],
                'high': fee_rates[2]
            },
            'inscriptions': random.randint(10, 500),
            'timestamp': datetime.now().isoformat()
        }
        
        return self.mempool_data
        
    async def check_congestion(self) -> Dict:
        """Check mempool congestion level"""
        if not self.mempool_data:
            return {'congestion': 0, 'level': 'unknown'}
            
        vsize = self.mempool_data.get('vsize', 0)
        # Assume max vsize is 10,000,000 vbytes
        congestion = min(1, vsize / 10000000)
        
        # Determine level
        if congestion < 0.3:
            level = 'low'
        elif congestion < 0.6:
            level = 'medium'
        elif congestion < 0.8:
            level = 'high'
        else:
            level = 'critical'
            
        # Store history
        self.congestion_history.append({
            'congestion': congestion,
            'level': level,
            'timestamp': datetime.now().isoformat()
        })
        if len(self.congestion_history) > 100:
            self.congestion_history = self.congestion_history[-100:]
            
        return {
            'congestion': congestion,
            'level': level,
            'tx_count': self.mempool_data.get('tx_count', 0)
        }
        
    async def check_fee_spikes(self) -> Optional[Dict]:
        """Check for fee spikes"""
        if not self.mempool_data:
            return None
            
        current_fee = self.mempool_data.get('fee_rates', {}).get('high', 0)
        
        # Calculate average fee from history
        avg_fee = 0
        if self.fee_spikes:
            avg_fee = sum(f.get('fee', 0) for f in self.fee_spikes[-20:]) / 20
        else:
            avg_fee = current_fee
            
        # Check for spike
        if avg_fee > 0:
            spike_ratio = current_fee / avg_fee
        else:
            spike_ratio = 1
            
        if spike_ratio > self.config['fee_spike_threshold']:
            return {
                'spike_ratio': spike_ratio,
                'current_fee': current_fee,
                'avg_fee': avg_fee,
                'timestamp': datetime.now().isoformat()
            }
            
        return None
        
    async def send_fee_alert(self, fee_spike: Dict):
        """Send fee spike alert"""
        alert = {
            'type': 'fee_spike',
            'severity': 'high' if fee_spike['spike_ratio'] > 3 else 'medium',
            'message': f"Fee spike detected: {fee_spike['spike_ratio']:.1f}x normal",
            'details': fee_spike,
            'timestamp': datetime.now().isoformat()
        }
        
        self.inscription_alerts.append(alert)
        
        # Publish alert
        alert_event = Event(
            event_type="fee_spike_alert",
            data=alert,
            source=self.agent_id
        )
        await self.event_bus.publish(alert_event)
        
        logger.warning(f"🚨 {alert['message']}")
        
    async def publish_scanner_update(self):
        """Publish scanner data update"""
        scanner_data = {
            'mempool_data': self.mempool_data,
            'congestion': await self.check_congestion(),
            'fee_spikes': self.fee_spikes[-5:],
            'alerts': self.inscription_alerts[-3:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="scanner_update",
            data=scanner_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get inscription scanner status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'last_scan': self.mempool_data,
            'congestion_history': len(self.congestion_history),
            'fee_spikes_detected': len(self.fee_spikes),
            'alerts_sent': len(self.inscription_alerts),
            'timestamp': datetime.now().isoformat()
        }
