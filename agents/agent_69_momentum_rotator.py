"""
AlphaEdge Agent 69 – Momentum Rotator
Monitor high momentum tickers using Ticker Performance Score (TPS)
Entry ≥82, Exit ≤68
V13.0.7 – UPDATED with Hysteresis Buffer + TPS Normalization Cap
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
from core.smart_money_concepts import SmartMoneyConcepts

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
        
        # Zone Detector
        self.zone_detector = ZoneDetector()
        self.zone_adjustments = {}
        
        # MCDX Detector
        self.mcdx_detector = MCDXDetector()
        self.last_mcdx_signal = None
        
        # Smart Money Concepts
        self.smc_detector = SmartMoneyConcepts()
        self.last_smc_signal = None
        
        # ============================================
        # ITEM 14: HYSTERESIS BUFFER
        # ============================================
        self.hysteresis_buffer = {
            'enabled': True,
            'exit_threshold': 68.0,
            'warning_threshold': 70.0,
            'hold_buffer_ticks': 3,
            'position_tracker': {}
        }
        
        # ============================================
        # ITEM 21: TPS NORMALIZATION CAP
        # ============================================
        self.tps_normalization = {
            'enabled': True,
            'max_tps': 100.0,
            'min_tps': 0.0,
            'base_bonus_cap': 100.0
        }
        
    async def start(self):
        """Start the momentum rotator"""
        logger.info("Momentum Rotator starting...")
        self.running = True
        
        await self.event_bus.subscribe("tps_update", self.handle_tps_update)
        await self.event_bus.subscribe("rotation_request", self.handle_rotation_request)
        await self.event_bus.subscribe("ticker_status_request", self.handle_ticker_status)
        
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
                await self.check_rotations()
                await self.update_ticker_status()
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
            # Apply Item 21: Normalization Cap
            raw_tps = tps
            normalized_tps = min(self.tps_normalization['max_tps'], 
                                 max(self.tps_normalization['min_tps'], raw_tps))
            
            if normalized_tps > self.tps_normalization['base_bonus_cap']:
                normalized_tps = self.tps_normalization['base_bonus_cap']
            
            self.ticker_scores[ticker] = {
                'tps': normalized_tps,
                'tier': tier,
                'price_data': price_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # Zone adjustment
            zone_adjustment = await self._calculate_zone_adjustment(ticker, price_data)
            if zone_adjustment != 0:
                self.zone_adjustments[ticker] = zone_adjustment
                self.ticker_scores[ticker]['zone_adjustment'] = zone_adjustment
            
            # MCDX adjustment
            mcdx_adjustment = await self._calculate_mcdx_tps_adjustment(price_data)
            if mcdx_adjustment != 0:
                self.ticker_scores[ticker]['mcdx_adjustment'] = mcdx_adjustment
            
            # SMC adjustment
            smc_adjustment = await self._calculate_smc_tps_adjustment(price_data)
            if smc_adjustment != 0:
                self.ticker_scores[ticker]['smc_adjustment'] = smc_adjustment
                self.last_smc_signal = self.smc_detector.last_signal
            
            # Calculate final adjusted TPS
            adjusted_tps = normalized_tps + zone_adjustment + mcdx_adjustment + smc_adjustment
            adjusted_tps = min(self.tps_normalization['base_bonus_cap'], adjusted_tps)
            self.ticker_scores[ticker]['adjusted_tps'] = adjusted_tps
            
            # Item 14: Apply Hysteresis Buffer
            in_position = ticker in await self.state_manager.get('positions', {})
            hysteresis_result = await self._process_hysteresis(ticker, adjusted_tps, in_position)
            
            if hysteresis_result['action'] == 'sell':
                await self.event_bus.publish(Event(
                    event_type="exit_signal",
                    data={
                        'token': ticker,
                        'tps': adjusted_tps,
                        'reason': hysteresis_result['reason']
                    },
                    source=self.agent_id
                ))
            
            logger.debug(f"TPS update: {ticker} = {adjusted_tps:.0f}")
            
    # ============================================
    # ITEM 14: HYSTERESIS BUFFER
    # ============================================
    
    async def _process_hysteresis(self, token: str, normalized_tps: float, in_position: bool) -> Dict:
        """Process hysteresis buffer to prevent micro-cap churn"""
        result = {'action': 'hold', 'reason': ''}
        
        if not self.hysteresis_buffer['enabled']:
            return result
            
        if token not in self.hysteresis_buffer['position_tracker']:
            self.hysteresis_buffer['position_tracker'][token] = {
                'under_threshold_ticks': 0,
                'entry_time': datetime.now().isoformat()
            }
        
        tracker = self.hysteresis_buffer['position_tracker'][token]
        
        if in_position:
            if normalized_tps <= self.hysteresis_buffer['exit_threshold']:
                result['action'] = 'sell'
                result['reason'] = 'TPS Cross Below Exit Margin'
                del self.hysteresis_buffer['position_tracker'][token]
            elif normalized_tps < self.hysteresis_buffer['warning_threshold']:
                tracker['under_threshold_ticks'] += 1
                if tracker['under_threshold_ticks'] >= self.hysteresis_buffer['hold_buffer_ticks']:
                    result['action'] = 'sell'
                    result['reason'] = 'Exceeded Temporal Churn Buffer'
                    del self.hysteresis_buffer['position_tracker'][token]
                else:
                    result['action'] = 'hold'
                    result['reason'] = f'Warning zone ({tracker["under_threshold_ticks"]}/{self.hysteresis_buffer["hold_buffer_ticks"]})'
            else:
                tracker['under_threshold_ticks'] = 0
                result['action'] = 'hold'
                result['reason'] = 'Momentum recovered'
        
        return result
    
    async def _calculate_zone_adjustment(self, ticker: str, price_data: Dict) -> float:
        """Calculate TPS adjustment based on ICT/SMC zones"""
        try:
            price_data_list = price_data.get('price_data_list', [])
            if not price_data_list or len(price_data_list) < 50:
                return 0.0
            
            highs = [p.get('high', 0) for p in price_data_list]
            lows = [p.get('low', 0) for p in price_data_list]
            closes = [p.get('close', 0) for p in price_data_list]
            volumes = [p.get('volume', 0) for p in price_data_list]
            opens = [p.get('open', 0) for p in price_data_list]
            
            high_arr = np.array(highs)
            low_arr = np.array(lows)
            close_arr = np.array(closes)
            vol_arr = np.array(volumes)
            open_arr = np.array(opens)
            
            zones = self.zone_detector.detect_zones(
                high_arr, low_arr, close_arr, vol_arr, open_arr
            )
            
            if not zones:
                return 0.0
            
            current_price = closes[-1] if closes else 0
            nearest_demand = self.zone_detector.get_nearest_zone(current_price, -1)
            if nearest_demand:
                distance_pct = abs(current_price - nearest_demand.mid()) / current_price * 100 if current_price > 0 else 100
                if distance_pct < 2.0:
                    adjustment = nearest_demand.score * 1.2
                    return min(adjustment, 10.0)
            return 0.0
        except Exception as e:
            logger.error(f"Zone adjustment error: {e}")
            return 0.0
    
    async def _calculate_mcdx_tps_adjustment(self, price_data: Dict) -> float:
        """Calculate TPS adjustment from MCDX signals"""
        try:
            close = price_data.get('close', [])
            high = price_data.get('high', [])
            low = price_data.get('low', [])
            open_price = price_data.get('open', [])
            volume = price_data.get('volume', [])
            adx = price_data.get('adx', 20)
            
            if len(close) < 34:
                return 0.0
            
            close_arr = np.array(close)
            high_arr = np.array(high)
            low_arr = np.array(low)
            open_arr = np.array(open_price)
            vol_arr = np.array(volume)
            
            signal = self.mcdx_detector.detect(
                close_arr, high_arr, low_arr, open_arr, vol_arr, adx
            )
            
            self.last_mcdx_signal = signal
            adjustment = signal.get_tps_adjustment(self.mcdx_detector.config.get('tps_adjustments', {}))
            
            min_adx = self.mcdx_detector.config.get('filters', {}).get('min_adx', 25)
            if adx < min_adx:
                adjustment = adjustment * 0.5
            return adjustment
        except Exception as e:
            logger.error(f"MCDX adjustment error: {e}")
            return 0.0
    
    async def _calculate_smc_tps_adjustment(self, price_data: Dict) -> float:
        """Calculate TPS adjustment from Smart Money Concepts signals"""
        try:
            close = price_data.get('close', [])
            high = price_data.get('high', [])
            low = price_data.get('low', [])
            open_price = price_data.get('open', [])
            volume = price_data.get('volume', [])
            
            if len(close) < 50:
                return 0.0
            
            close_arr = np.array(close)
            high_arr = np.array(high)
            low_arr = np.array(low)
            open_arr = np.array(open_price)
            vol_arr = np.array(volume)
            
            signal = self.smc_detector.detect(
                high_arr, low_arr, close_arr, open_arr, vol_arr
            )
            
            self.last_smc_signal = signal
            adjustment = signal.get_tps_adjustment(
                self.smc_detector.config.get('tps_adjustments', {})
            )
            return adjustment
        except Exception as e:
            logger.error(f"SMC adjustment error: {e}")
            return 0.0
    
    async def handle_rotation_request(self, event: Event):
        """Handle rotation requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
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
            if ticker in self.zone_adjustments:
                status['zone_adjustment'] = self.zone_adjustments[ticker]
            if self.last_mcdx_signal:
                status['mcdx_signal'] = self.last_mcdx_signal.signal_strength
            if self.last_smc_signal:
                status['smc_confluence'] = self.last_smc_signal.confluence_score
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
            
        result = await self.calculate_rotations()
        if result.get('signals'):
            self.rotation_signals.extend(result['signals'])
        if len(self.rotation_signals) > 100:
            self.rotation_signals = self.rotation_signals[-100:]
            
    async def calculate_rotations(self) -> Dict:
        """Calculate rotation signals"""
        signals = []
        entry_signals = []
        exit_signals = []
        
        positions = await self.state_manager.get('positions', {})
        
        for ticker, data in self.ticker_scores.items():
            tps = data.get('adjusted_tps', data.get('tps', 0))
            tier = data.get('tier', 'unknown')
            zone_adj = data.get('zone_adjustment', 0)
            mcdx_adj = data.get('mcdx_adjustment', 0)
            smc_adj = data.get('smc_adjustment', 0)
            
            in_position = ticker in positions
            
            if not in_position:
                if tps >= self.config['min_score_for_entry']:
                    current_positions = len(positions)
                    if current_positions < self.config['max_positions']:
                        entry_signals.append({
                            'ticker': ticker,
                            'tps': tps,
                            'tier': tier,
                            'zone_adjustment': zone_adj,
                            'mcdx_adjustment': mcdx_adj,
                            'smc_adjustment': smc_adj,
                            'action': 'entry',
                            'timestamp': datetime.now().isoformat()
                        })
            else:
                if tps <= self.config['max_score_for_exit']:
                    exit_signals.append({
                        'ticker': ticker,
                        'tps': tps,
                        'tier': tier,
                        'zone_adjustment': zone_adj,
                        'mcdx_adjustment': mcdx_adj,
                        'smc_adjustment': smc_adj,
                        'action': 'exit',
                        'timestamp': datetime.now().isoformat()
                    })
                    
        signals = entry_signals + exit_signals
        signals.sort(key=lambda x: 0 if x['action'] == 'entry' else 1)
        
        result = {
            'signals': signals,
            'entry_count': len(entry_signals),
            'exit_count': len(exit_signals),
            'timestamp': datetime.now().isoformat()
        }
        
        await self.state_manager.set('rotation_signals', signals)
        return result
        
    async def update_ticker_status(self):
        """Update ticker status"""
        for ticker, data in self.ticker_scores.items():
            tps = data.get('adjusted_tps', data.get('tps', 0))
            status = 'monitor'
            
            if tps >= self.config['min_score_for_entry']:
                status = 'entry_signal'
            elif tps <= self.config['max_score_for_exit']:
                status = 'exit_signal'
            else:
                status = 'hold'
                
            await self.state_manager.set(f'ticker_status_{ticker}', {
                'status': status,
                'tps': tps,
                'zone_adjustment': data.get('zone_adjustment', 0),
                'mcdx_adjustment': data.get('mcdx_adjustment', 0),
                'smc_adjustment': data.get('smc_adjustment', 0),
                'timestamp': datetime.now().isoformat()
            })
            
    async def publish_rotation_update(self):
        """Publish rotation data update"""
        zone_summary = self.zone_detector.get_zone_summary() if self.zone_detector else {}
        
        mcdx_summary = {}
        if self.last_mcdx_signal:
            mcdx_summary = {
                'signal_strength': self.last_mcdx_signal.signal_strength,
                'profit_chips': self.last_mcdx_signal.profit_chips,
                'golden_cross': self.last_mcdx_signal.golden_cross,
                'bottom_catch': self.last_mcdx_signal.bottom_catch
            }
        
        smc_summary = {}
        if self.last_smc_signal:
            smc_summary = {
                'confluence_score': self.last_smc_signal.confluence_score,
                'trend_bias': self.last_smc_signal.trend_bias,
                'bos_bullish': self.last_smc_signal.swing_bos_bullish,
                'bos_bearish': self.last_smc_signal.swing_bos_bearish,
                'bullish_ob_validated': self.last_smc_signal.ob_validation.is_valid() if self.last_smc_signal.ob_validation else False
            }
        
        rotation_data = {
            'ticker_scores': self.ticker_scores,
            'rotation_signals': self.rotation_signals[-5:],
            'entry_signals': [s for s in self.rotation_signals if s.get('action') == 'entry'][-5:],
            'exit_signals': [s for s in self.rotation_signals if s.get('action') == 'exit'][-5:],
            'zone_summary': zone_summary,
            'mcdx_summary': mcdx_summary,
            'smc_summary': smc_summary,
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
        
        smc_status = {}
        if self.last_smc_signal:
            smc_status = {
                'confluence_score': self.last_smc_signal.confluence_score,
                'trend_bias': self.last_smc_signal.trend_bias
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
            'smc_status': smc_status,
            'hysteresis_active': self.hysteresis_buffer['enabled'],
            'normalization_active': self.tps_normalization['enabled'],
            'timestamp': datetime.now().isoformat()
        }
