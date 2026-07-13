"""
AlphaEdge Agent 69 – Momentum Rotator
Monitor high momentum tickers using Ticker Performance Score (TPS)
Entry ≥82, Exit ≤68
V13.0.6 – UPDATED with ICT/SMC Zone Integration + MCDX Support
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random
import numpy as np

from core.event_bus import Event, EventBus
from core.state_manager import StateManager
from core.zone_detector import ZoneDetector
from core.mcdx_detector import MCDXDetector

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
        
        # ============================================
        # NEW: Zone Detector for TPS Enhancement
        # ============================================
        self.zone_detector = ZoneDetector()
        self.zone_adjustments = {}
        
        # ============================================
        # NEW: MCDX Detector
        # ============================================
        self.mcdx_detector = MCDXDetector()
        self.last_mcdx_signal = None
        
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
        price_data = event.data.get('price_data', {})
        
        if ticker:
            # Store TPS data
            self.ticker_scores[ticker] = {
                'tps': tps,
                'tier': tier,
                'price_data': price_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # ============================================
            # NEW: Calculate zone adjustment for this ticker
            # ============================================
            zone_adjustment = await self._calculate_zone_adjustment(ticker, price_data)
            if zone_adjustment != 0:
                self.zone_adjustments[ticker] = zone_adjustment
                self.ticker_scores[ticker]['zone_adjustment'] = zone_adjustment
            
            # ============================================
            # NEW: Calculate MCDX adjustment for this ticker
            # ============================================
            mcdx_adjustment = await self._calculate_mcdx_tps_adjustment(price_data)
            if mcdx_adjustment != 0:
                self.ticker_scores[ticker]['mcdx_adjustment'] = mcdx_adjustment
                logger.debug(f"MCDX adjustment for {ticker}: {mcdx_adjustment:.1f}")
            
            # Calculate final adjusted TPS
            adjusted_tps = tps + zone_adjustment + mcdx_adjustment
            adjusted_tps = min(adjusted_tps, 100)
            self.ticker_scores[ticker]['adjusted_tps'] = adjusted_tps
            
            logger.debug(f"TPS update: {ticker} = {tps} (adj: {adjusted_tps:.0f})")
            
    # ============================================
    # NEW: Zone Confluence Methods
    # ============================================
    
    async def _calculate_zone_adjustment(self, ticker: str, price_data: Dict) -> float:
        """
        Calculate TPS adjustment based on ICT/SMC zones
        Elite demand zone adds up to +10 points
        """
        try:
            # Extract price data lists from price_data
            price_data_list = price_data.get('price_data_list', [])
            
            if not price_data_list or len(price_data_list) < 50:
                return 0.0
            
            # Extract arrays
            highs = [p.get('high', 0) for p in price_data_list]
            lows = [p.get('low', 0) for p in price_data_list]
            closes = [p.get('close', 0) for p in price_data_list]
            volumes = [p.get('volume', 0) for p in price_data_list]
            opens = [p.get('open', 0) for p in price_data_list]
            
            # Convert to numpy arrays
            high_arr = np.array(highs)
            low_arr = np.array(lows)
            close_arr = np.array(closes)
            vol_arr = np.array(volumes)
            open_arr = np.array(opens)
            
            # Detect zones
            zones = self.zone_detector.detect_zones(
                high_arr, low_arr, close_arr, vol_arr, open_arr
            )
            
            if not zones:
                return 0.0
            
            current_price = closes[-1] if closes else 0
            
            # Check for elite demand zones (support) near price
            elite_zones = self.zone_detector.get_elite_zones()
            if not elite_zones:
                return 0.0
            
            # Find nearest demand zone below price
            nearest_demand = self.zone_detector.get_nearest_zone(current_price, -1)
            if nearest_demand:
                distance_pct = abs(current_price - nearest_demand.mid()) / current_price * 100 if current_price > 0 else 100
                if distance_pct < 2.0:  # Within 2% of zone
                    # Scale adjustment based on zone score (max 10 points)
                    adjustment = nearest_demand.score * 1.2
                    return min(adjustment, 10.0)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Zone adjustment error for {ticker}: {e}")
            return 0.0
    
    # ============================================
    # NEW: MCDX Methods
    # ============================================
    
    async def _calculate_mcdx_tps_adjustment(self, price_data: Dict) -> float:
        """
        Calculate TPS adjustment from MCDX signals
        """
        try:
            close = price_data.get('close', [])
            high = price_data.get('high', [])
            low = price_data.get('low', [])
            open_price = price_data.get('open', [])
            volume = price_data.get('volume', [])
            adx = price_data.get('adx', 20)
            
            if len(close) < 34:
                return 0.0
            
            # Convert to numpy arrays
            close_arr = np.array(close)
            high_arr = np.array(high)
            low_arr = np.array(low)
            open_arr = np.array(open_price)
            vol_arr = np.array(volume)
            
            # Detect MCDX signals
            signal = self.mcdx_detector.detect(
                close_arr, high_arr, low_arr, open_arr, vol_arr, adx
            )
            
            # Store for debugging
            self.last_mcdx_signal = signal
            
            # Get TPS adjustment
            adjustment = signal.get_tps_adjustment(self.mcdx_detector.config.get('tps_adjustments', {}))
            
            # Apply filtering: only use in trending markets (ADX >25)
            min_adx = self.mcdx_detector.config.get('filters', {}).get('min_adx', 25)
            if adx < min_adx:
                adjustment = adjustment * 0.5  # Reduce impact in ranging markets
            
            return adjustment
            
        except Exception as e:
            logger.error(f"MCDX TPS adjustment error: {e}")
            return 0.0
    
    # ============================================
    # END OF NEW METHODS
    # ============================================
            
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
            # Add zone adjustment to status
            if ticker in self.zone_adjustments:
                status['zone_adjustment'] = self.zone_adjustments[ticker]
            if self.last_mcdx_signal:
                status['mcdx_signal'] = self.last_mcdx_signal.signal_strength
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
            # Use adjusted TPS if available
            tps = data.get('adjusted_tps', data.get('tps', 0))
            tier = data.get('tier', 'unknown')
            zone_adj = data.get('zone_adjustment', 0)
            mcdx_adj = data.get('mcdx_adjustment', 0)
            
            # Check if in position
            in_position = ticker in positions
            
            if not in_position:
                # Check entry signal (use adjusted TPS)
                if tps >= self.config['min_score_for_entry']:
                    # Check max positions
                    current_positions = len(positions)
                    if current_positions < self.config['max_positions']:
                        entry_signals.append({
                            'ticker': ticker,
                            'tps': tps,
                            'tier': tier,
                            'zone_adjustment': zone_adj,
                            'mcdx_adjustment': mcdx_adj,
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
                        'zone_adjustment': zone_adj,
                        'mcdx_adjustment': mcdx_adj,
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
            tps = data.get('adjusted_tps', data.get('tps', 0))
            status = 'monitor'
            
            if tps >= self.config['min_score_for_entry']:
                status = 'entry_signal'
            elif tps <= self.config['max_score_for_exit']:
                status = 'exit_signal'
            else:
                status = 'hold'
                
            # Store status with zone info
            await self.state_manager.set(f'ticker_status_{ticker}', {
                'status': status,
                'tps': tps,
                'zone_adjustment': data.get('zone_adjustment', 0),
                'mcdx_adjustment': data.get('mcdx_adjustment', 0),
                'timestamp': datetime.now().isoformat()
            })
            
    async def publish_rotation_update(self):
        """Publish rotation data update"""
        # Get zone summary
        zone_summary = self.zone_detector.get_zone_summary() if self.zone_detector else {}
        
        # Get MCDX summary
        mcdx_summary = {}
        if self.last_mcdx_signal:
            mcdx_summary = {
                'signal_strength': self.last_mcdx_signal.signal_strength,
                'profit_chips': self.last_mcdx_signal.profit_chips,
                'golden_cross': self.last_mcdx_signal.golden_cross,
                'bottom_catch': self.last_mcdx_signal.bottom_catch
            }
        
        rotation_data = {
            'ticker_scores': self.ticker_scores,
            'rotation_signals': self.rotation_signals[-5:],
            'entry_signals': [s for s in self.rotation_signals if s.get('action') == 'entry'][-5:],
            'exit_signals': [s for s in self.rotation_signals if s.get('action') == 'exit'][-5:],
            'zone_summary': zone_summary,
            'mcdx_summary': mcdx_summary,
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
        mcdx_status = {}
        if self.last_mcdx_signal:
            mcdx_status = {
                'signal_strength': self.last_mcdx_signal.signal_strength,
                'profit_chips': self.last_mcdx_signal.profit_chips,
                'golden_cross': self.last_mcdx_signal.golden_cross,
                'bottom_catch': self.last_mcdx_signal.bottom_catch
            }
        
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'ticker_count': len(self.ticker_scores),
            'signals_count': len(self.rotation_signals),
            'entry_threshold': self.config['min_score_for_entry'],
            'exit_threshold': self.config['max_score_for_exit'],
            'zone_adjustments_active': len(self.zone_adjustments),
            'mcdx_status': mcdx_status,
            'timestamp': datetime.now().isoformat()
        }
