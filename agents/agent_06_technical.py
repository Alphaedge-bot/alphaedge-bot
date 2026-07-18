"""
AlphaEdge Agent 06 – Technical Analyst
TA/PA/ICT/SMC patterns, 29 strategies, RSI/MACD/MA, per candle updates
V13.0.7 – UPDATED with Volume Profile Integration (Item 12)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import math
import numpy as np

from core.event_bus import Event, EventBus
from core.state_manager import StateManager
from core.zone_detector import ZoneDetector
from core.volume_profile import VolumeProfile

logger = logging.getLogger(__name__)


class TechnicalAnalyst:
    """Technical Analyst – Performs technical analysis and pattern detection"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "technical"
        self.running = False
        
        # Technical data cache
        self.price_data = []
        self.indicators = {}
        self.patterns = []
        self.signals = []
        
        # Technical parameters
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.ema_periods = [9, 20, 50, 200]
        
        # Zone Detector
        self.zone_detector = ZoneDetector()
        self.zone_summary = {}
        
        # ============================================
        # ITEM 12: VOLUME PROFILE
        # ============================================
        self.volume_profile = VolumeProfile()
        self.last_vp_data = {}
        
    async def start(self):
        """Start the technical analyst"""
        logger.info("Technical Analyst starting...")
        self.running = True
        
        await self.event_bus.subscribe("technical_request", self.handle_technical_request)
        await self.event_bus.subscribe("price_update", self.handle_price_update)
        
        asyncio.create_task(self.run_analysis_cycle())
        logger.info("Technical Analyst running")
        
    async def stop(self):
        """Stop the technical analyst"""
        self.running = False
        logger.info("Technical Analyst stopped")
        
    async def run_analysis_cycle(self):
        """Run regular technical analysis"""
        while self.running:
            try:
                if self.price_data:
                    await self.calculate_indicators()
                    await self.detect_patterns()
                    await self.generate_signals()
                    await self.analyze_zones()
                    await self.analyze_volume_profile()
                    await self.publish_technical_update()
            except Exception as e:
                logger.error(f"Technical analysis cycle error: {e}")
            await asyncio.sleep(60)
            
    async def handle_price_update(self, event: Event):
        """Handle price updates from market data"""
        if not self.running:
            return
            
        price_data = event.data
        self.price_data.append(price_data)
        
        if len(self.price_data) > 1000:
            self.price_data.pop(0)
            
    # ============================================
    # ITEM 12: VOLUME PROFILE METHODS
    # ============================================
    
    async def analyze_volume_profile(self):
        """Analyze Volume Profile across multiple timeframes"""
        try:
            if len(self.price_data) < 50:
                return
            
            # Prepare data for each timeframe
            vp_data = {}
            
            # Use current data for all timeframes
            # In production, fetch different timeframe data
            closes = [p.get('close', 0) for p in self.price_data]
            highs = [p.get('high', 0) for p in self.price_data]
            lows = [p.get('low', 0) for p in self.price_data]
            volumes = [p.get('volume', 0) for p in self.price_data]
            
            for tf in self.volume_profile.config['timeframes']:
                vp_data[tf] = {
                    'high': highs,
                    'low': lows,
                    'close': closes,
                    'volume': volumes
                }
            
            # Analyze Volume Profile
            result = self.volume_profile.analyze_multi_timeframe(vp_data)
            
            # Get support/resistance levels
            sr_levels = self.volume_profile.get_support_resistance(result)
            
            self.last_vp_data = {
                'result': result,
                'sr_levels': sr_levels,
                'timestamp': datetime.now().isoformat()
            }
            
            # Store in state
            await self.state_manager.set('volume_profile_data', self.last_vp_data)
            
        except Exception as e:
            logger.error(f"Volume Profile analysis error: {e}")
            
    async def get_volume_profile_tps_adjustment(self, current_price: float) -> float:
        """
        Calculate TPS adjustment from Volume Profile
        """
        try:
            if not self.last_vp_data:
                return 0.0
            
            result = self.last_vp_data.get('result', {})
            adjustment = self.volume_profile.get_tps_adjustment(result, current_price)
            return adjustment
            
        except Exception as e:
            logger.error(f"Volume Profile TPS adjustment error: {e}")
            return 0.0
            
    # ============================================
    # ZONE METHODS
    # ============================================
    
    async def analyze_zones(self):
        """Analyze ICT/SMC zones"""
        try:
            if len(self.price_data) < 100:
                return
            
            highs = [p.get('high', 0) for p in self.price_data]
            lows = [p.get('low', 0) for p in self.price_data]
            closes = [p.get('close', 0) for p in self.price_data]
            volumes = [p.get('volume', 0) for p in self.price_data]
            opens = [p.get('open', 0) for p in self.price_data]
            
            high_arr = np.array(highs)
            low_arr = np.array(lows)
            close_arr = np.array(closes)
            vol_arr = np.array(volumes)
            open_arr = np.array(opens)
            
            zones = self.zone_detector.detect_zones(
                high_arr, low_arr, close_arr, vol_arr, open_arr
            )
            
            if zones and self.price_data:
                latest = self.price_data[-1]
                self.zone_detector.update_zones(
                    latest.get('high', 0),
                    latest.get('low', 0),
                    latest.get('close', 0),
                    latest.get('volume', 0),
                    latest.get('open', 0)
                )
            
            self.zone_summary = self.zone_detector.get_zone_summary()
            
            if self.zone_summary.get('has_elite', False):
                elite_zones = self.zone_detector.get_elite_zones()
                for zone in elite_zones[:3]:
                    self.patterns.append({
                        'type': 'elite_zone',
                        'direction': 'supply' if zone.is_supply() else 'demand',
                        'price': zone.mid(),
                        'score': zone.score,
                        'strength': 'strong'
                    })
            
            await self.state_manager.set('zone_summary', self.zone_summary)
            
        except Exception as e:
            logger.error(f"Zone analysis error: {e}")
    
    async def get_zone_tps_adjustment(self, current_price: float) -> float:
        """Calculate TPS adjustment based on zones"""
        elite_zones = self.zone_detector.get_elite_zones()
        if not elite_zones:
            return 0.0
        
        nearest_demand = self.zone_detector.get_nearest_zone(current_price, -1)
        if nearest_demand:
            distance_pct = abs(current_price - nearest_demand.mid()) / current_price * 100
            if distance_pct < 2.0:
                adjustment = nearest_demand.score * 1.2
                return min(adjustment, 10.0)
        return 0.0
    
    async def get_zone_based_sl_tp(self, entry_price: float) -> Dict:
        """Get zone-based stop loss and take profit levels"""
        result = {'sl': None, 'tp': None}
        if not self.price_data:
            return result
        
        current_price = self.price_data[-1].get('close', 0)
        
        nearest_demand = self.zone_detector.get_nearest_zone(current_price, -1)
        if nearest_demand:
            sl_price = nearest_demand.bottom * 0.995
            sl_pct = (entry_price - sl_price) / entry_price * 100 if entry_price > 0 else 0
            if sl_pct <= 15:
                result['sl'] = sl_price
                result['sl_zone'] = nearest_demand.to_dict()
        
        nearest_supply = self.zone_detector.get_nearest_zone(current_price, 1)
        if nearest_supply:
            tp_price = nearest_supply.top
            tp_pct = (tp_price - entry_price) / entry_price * 100 if entry_price > 0 else 0
            if 1 <= tp_pct <= 50:
                result['tp'] = tp_price
                result['tp_zone'] = nearest_supply.to_dict()
        return result
    
    # ============================================
    # INDICATOR CALCULATIONS
    # ============================================
    
    async def calculate_indicators(self):
        """Calculate technical indicators"""
        if len(self.price_data) < 50:
            return
            
        closes = [p.get('close', 0) for p in self.price_data]
        highs = [p.get('high', 0) for p in self.price_data]
        lows = [p.get('low', 0) for p in self.price_data]
        volumes = [p.get('volume', 0) for p in self.price_data]
        
        self.indicators['rsi'] = self.calculate_rsi(closes)
        self.indicators['macd'] = self.calculate_macd(closes)
        
        self.indicators['emas'] = {}
        for period in self.ema_periods:
            self.indicators['emas'][period] = self.calculate_ema(closes, period)
            
        self.indicators['atr'] = self.calculate_atr(highs, lows, closes)
        self.indicators['adx'] = self.calculate_adx(highs, lows, closes)
        
        await self.state_manager.set('technical_indicators', self.indicators)
        
    def calculate_rsi(self, prices: List[float]) -> float:
        if len(prices) < self.rsi_period + 1:
            return 50
        gains = 0
        losses = 0
        for i in range(-self.rsi_period, 0):
            diff = prices[i] - prices[i-1]
            if diff > 0:
                gains += diff
            else:
                losses += abs(diff)
        if losses == 0:
            return 100
        rs = gains / losses
        return 100 - (100 / (1 + rs))
        
    def calculate_macd(self, prices: List[float]) -> Dict[str, float]:
        if len(prices) < self.macd_slow:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        ema_fast = self.calculate_ema(prices, self.macd_fast)
        ema_slow = self.calculate_ema(prices, self.macd_slow)
        macd_line = ema_fast - ema_slow
        if len(prices) >= self.macd_slow + self.macd_signal:
            signal_line = sum(prices[-self.macd_signal:]) / self.macd_signal
        else:
            signal_line = macd_line
        histogram = macd_line - signal_line
        return {'macd': macd_line, 'signal': signal_line, 'histogram': histogram}
        
    def calculate_ema(self, prices: List[float], period: int) -> float:
        if len(prices) < period:
            return prices[-1] if prices else 0
        multiplier = 2 / (period + 1)
        ema = prices[-period]
        for price in prices[-period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        return ema
        
    def calculate_atr(self, highs: List[float], lows: List[float], 
                      closes: List[float], period: int = 14) -> float:
        if len(closes) < period + 1:
            return 0
        tr_values = []
        for i in range(-period, 0):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            tr = max(high_low, high_close, low_close)
            tr_values.append(tr)
        return sum(tr_values) / period
        
    def calculate_adx(self, highs: List[float], lows: List[float], 
                      closes: List[float], period: int = 14) -> float:
        if len(closes) < period * 2:
            return 25
        dm_plus = 0
        dm_minus = 0
        tr_sum = 0
        for i in range(-period, 0):
            high_diff = highs[i] - highs[i-1]
            low_diff = lows[i-1] - lows[i]
            if high_diff > low_diff and high_diff > 0:
                dm_plus += high_diff
            elif low_diff > high_diff and low_diff > 0:
                dm_minus += low_diff
            tr_sum += self.calculate_true_range(highs[i], lows[i], closes[i-1])
        di_plus = (dm_plus / tr_sum) * 100 if tr_sum > 0 else 25
        di_minus = (dm_minus / tr_sum) * 100 if tr_sum > 0 else 25
        adx = abs(di_plus - di_minus) / (di_plus + di_minus) * 100 if (di_plus + di_minus) > 0 else 25
        return min(adx, 100)
        
    def calculate_true_range(self, high: float, low: float, prev_close: float) -> float:
        return max(high - low, abs(high - prev_close), abs(low - prev_close))
        
    async def detect_patterns(self):
        if len(self.price_data) < 50:
            return
        patterns = []
        support_resistance = self.find_support_resistance()
        if support_resistance:
            patterns.extend(support_resistance)
        breakout = self.detect_breakout()
        if breakout:
            patterns.append(breakout)
        reversal = self.detect_reversal()
        if reversal:
            patterns.append(reversal)
        self.patterns = patterns
        await self.state_manager.set('technical_patterns', patterns)
        
    def find_support_resistance(self) -> List[Dict[str, Any]]:
        if len(self.price_data) < 20:
            return []
        levels = []
        prices = [p.get('close', 0) for p in self.price_data[-20:]]
        for i in range(5, len(prices) - 5):
            if prices[i] < min(prices[i-5:i]) and prices[i] < min(prices[i+1:i+6]):
                levels.append({'type': 'support', 'price': prices[i], 'strength': 'medium'})
            elif prices[i] > max(prices[i-5:i]) and prices[i] > max(prices[i+1:i+6]):
                levels.append({'type': 'resistance', 'price': prices[i], 'strength': 'medium'})
        return levels[:5]
        
    def detect_breakout(self) -> Optional[Dict[str, Any]]:
        if len(self.price_data) < 20:
            return None
        current_price = self.price_data[-1].get('close', 0)
        prev_high = max([p.get('high', 0) for p in self.price_data[-20:-1]])
        if current_price > prev_high * 1.02:
            return {'type': 'breakout', 'direction': 'up', 'price': current_price, 'resistance': prev_high, 'strength': 'strong'}
        return None
        
    def detect_reversal(self) -> Optional[Dict[str, Any]]:
        if len(self.price_data) < 30:
            return None
        prices = [p.get('close', 0) for p in self.price_data[-30:]]
        rsi = self.indicators.get('rsi', 50)
        price_trend = prices[-1] > prices[-5]
        if rsi > 70 and not price_trend:
            return {'type': 'reversal', 'direction': 'bearish', 'confidence': 0.6, 'rsi': rsi}
        elif rsi < 30 and price_trend:
            return {'type': 'reversal', 'direction': 'bullish', 'confidence': 0.6, 'rsi': rsi}
        return None
        
    async def generate_signals(self):
        signals = []
        rsi = self.indicators.get('rsi', 50)
        if rsi > 70:
            signals.append({'type': 'rsi', 'signal': 'overbought', 'value': rsi})
        elif rsi < 30:
            signals.append({'type': 'rsi', 'signal': 'oversold', 'value': rsi})
        macd = self.indicators.get('macd', {})
        macd_line = macd.get('macd', 0)
        signal_line = macd.get('signal', 0)
        if macd_line > signal_line and macd_line > 0:
            signals.append({'type': 'macd', 'signal': 'bullish', 'value': macd_line})
        elif macd_line < signal_line and macd_line < 0:
            signals.append({'type': 'macd', 'signal': 'bearish', 'value': macd_line})
        emas = self.indicators.get('emas', {})
        current_price = self.price_data[-1].get('close', 0) if self.price_data else 0
        if current_price > emas.get(20, 0) > emas.get(50, 0):
            signals.append({'type': 'ema', 'signal': 'bullish', 'value': 'golden_cross'})
        elif current_price < emas.get(20, 0) < emas.get(50, 0):
            signals.append({'type': 'ema', 'signal': 'bearish', 'value': 'death_cross'})
        adx = self.indicators.get('adx', 25)
        if adx > 40:
            signals.append({'type': 'adx', 'signal': 'strong_trend', 'value': adx})
        elif adx < 20:
            signals.append({'type': 'adx', 'signal': 'weak_trend', 'value': adx})
        self.signals = signals
        await self.state_manager.set('technical_signals', signals)
        
    async def publish_technical_update(self):
        technical_data = {
            'indicators': self.indicators,
            'patterns': self.patterns,
            'signals': self.signals,
            'zone_summary': self.zone_summary,
            'volume_profile': self.last_vp_data,
            'timestamp': datetime.now().isoformat()
        }
        event = Event(event_type="technical_data_update", data=technical_data, source=self.agent_id)
        await self.event_bus.publish(event)
        
    async def handle_technical_request(self, event: Event):
        if not self.running:
            return
        technical_data = {
            'indicators': self.indicators,
            'patterns': self.patterns,
            'signals': self.signals,
            'zone_summary': self.zone_summary,
            'volume_profile': self.last_vp_data,
            'timestamp': datetime.now().isoformat()
        }
        response = Event(
            event_type="technical_response",
            data=technical_data,
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def get_status(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'data_points': len(self.price_data),
            'indicators_calculated': len(self.indicators),
            'patterns_detected': len(self.patterns),
            'signals_generated': len(self.signals),
            'zone_summary': self.zone_summary,
            'volume_profile_enabled': self.volume_profile.config.get('enabled', True),
            'timestamp': datetime.now().isoformat()
        }
