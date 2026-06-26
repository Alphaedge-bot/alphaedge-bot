"""
AlphaEdge Agent 69 – Momentum Rotator
Monitor high momentum tickers using Ticker Performance Score (TPS)
Entry ≥82, Exit ≤68
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class MomentumRotator:
    """Momentum Rotator – Monitors and rotates based on Ticker Performance Score (TPS)"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "momentum_rotator"
        self.running = False
        
        # Rotation state
        self.ticker_scores = {}
        self.rotation_signals = []
        self.rotation_history = []
        
        # TPS thresholds
        self.tps_entry_threshold = 82
        self.tps_exit_threshold = 68
        
        # Configuration
        self.config = {
            'min_score_for_entry': 82,
            'max_score_for_exit': 68,
            'rotation_check_interval': 60,  # seconds
            'max_positions': 18
        }
        
    async def start(self):
        """Start the momentum rotator"""
        logger.info("Momentum Rotator starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("tps_update", self.handle_tps_update)
        await self.event_bus.subscribe("rotation_request", self.handle_rotation_request)
        await self.event_bus.subscribe("ticker_status_request", self.handle_ticker_status)
        
        # Start rotation cycle
        asyncio.create_task(self.run_rotation_cycle())
        
        logger.info("Momentum Rotator running")
        
    async def stop(self):
        """Stop the momentum rotator"""
        self.running = False
        logger.info("Momentum Rotator stopped")
        
    async def run_rotation_cycle(self):
        """Run regular rotation cycle"""
        while self.running:
            try:
                # Check for rotations
                await self.check_rotations()
                
                # Update ticker status
                await self.update_ticker_status()
                
                # Publish rotation update
                await self.publish_rotation_update()
                
            except Exception as e:
                logger.error(f"Rotation cycle error: {e}")
                
            await asyncio.sleep(self.config['rotation_check_interval'])
            
    async def handle_tps_update(self, event: Event):
        """Handle TPS updates"""
        if not self.running:
            return
            
        ticker = event.data.get('ticker')
        tps = event.data.get('tps', 0)
        tier = event.data.get('tier', 'unknown')
        
        if ticker:
            self.ticker_scores[ticker] = {
                'tps': tps,
                'tier': tier,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.debug(f"TPS update: {ticker} = {tps}")
            
    async def handle_rotation_request(self, event: Event):
        """Handle rotation requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        
        # Calculate rotations
        result = await self.calculate_rotations()
        
        response = Event(
            event_type="rotation_response",
            data={
                'request_id': request_id,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_ticker_status(self, event: Event):
        """Handle ticker status requests"""
        if not self.running:
            return
            
        ticker = event.data.get('ticker')
        
        if ticker:
            status = self.ticker_scores.get(ticker, {})
        else:
            status = self.ticker_scores
            
        response = Event(
            event_type="ticker_status_response",
            data={
                'ticker': ticker,
                'status': status,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def check_rotations(self):
        """Check for rotations"""
        if not self.ticker_scores:
            return
            
        # Calculate rotations
        result = await self.calculate_rotations()
        
        # Store signals
        if result.get('signals'):
            self.rotation_signals.extend(result['signals'])
            
        # Keep last 100 signals
        if len(self.rotation_signals) > 100:
            self.rotation_signals = self.rotation_signals[-100:]
            
    async def calculate_rotations(self) -> Dict:
        """Calculate rotation signals"""
        signals = []
        entry_signals = []
        exit_signals = []
        
        # Get current positions
        positions = await self.state_manager.get('positions', {})
        
        # Check each ticker
        for ticker, data in self.ticker_scores.items():
            tps = data.get('tps', 0)
            tier = data.get('tier', 'unknown')
            
            # Check if in position
            in_position = ticker in positions
            
            if not in_position:
                # Check entry signal
                if tps >= self.config['min_score_for_entry']:
                    # Check max positions
                    current_positions = len(positions)
                    if current_positions < self.config['max_positions']:
                        entry_signals.append({
                            'ticker': ticker,
                            'tps': tps,
                            'tier': tier,
                            'action': 'entry',
                            'timestamp': datetime.now().isoformat()
                        })
                    else:
                        logger.info(f"Max positions reached ({self.config['max_positions']})")
            else:
                # Check exit signal
                if tps <= self.config['max_score_for_exit']:
                    exit_signals.append({
                        'ticker': ticker,
                        'tps': tps,
                        'tier': tier,
                        'action': 'exit',
                        'timestamp': datetime.now().isoformat()
                    })
                    
        # Combine signals
        signals = entry_signals + exit_signals
        
        # Sort by priority (entry first, then exit)
        signals.sort(key=lambda x: 0 if x['action'] == 'entry' else 1)
        
        result = {
            'signals': signals,
            'entry_count': len(entry_signals),
            'exit_count': len(exit_signals),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in state
        await self.state_manager.set('rotation_signals', signals)
        
        return result
        
    async def update_ticker_status(self):
        """Update ticker status"""
        # Update status for each ticker
        for ticker, data in self.ticker_scores.items():
            tps = data.get('tps', 0)
            status = 'monitor'
            
            if tps >= self.config['min_score_for_entry']:
                status = 'entry_signal'
            elif tps <= self.config['max_score_for_exit']:
                status = 'exit_signal'
            else:
                status = 'hold'
                
            # Store status
            await self.state_manager.set(f'ticker_status_{ticker}', {
                'status': status,
                'tps': tps,
                'timestamp': datetime.now().isoformat()
            })
            
    async def publish_rotation_update(self):
        """Publish rotation data update"""
        rotation_data = {
            'ticker_scores': self.ticker_scores,
            'rotation_signals': self.rotation_signals[-5:],
            'entry_signals': [s for s in self.rotation_signals if s.get('action') == 'entry'][-5:],
            'exit_signals': [s for s in self.rotation_signals if s.get('action') == 'exit'][-5:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="momentum_rotation_update",
            data=rotation_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get momentum rotator status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'ticker_count': len(self.ticker_scores),
            'signals_count': len(self.rotation_signals),
            'entry_threshold': self.config['min_score_for_entry'],
            'exit_threshold': self.config['max_score_for_exit'],
            'timestamp': datetime.now().isoformat()
        }
