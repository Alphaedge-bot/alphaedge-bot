"""
AlphaEdge Agent 06 – Technical Analyst
TA/PA/ICT/SMC patterns, 29 strategies, RSI/MACD/MA, per candle updates
V13.0.5 – UPDATED with ICT/SMC Zone Detection
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import math
import numpy as np

from core.event_bus import Event, EventBus
from core.state_manager import StateManager
from core.zone_detector import ZoneDetector, Zone

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
        
        # ============================================
        # NEW: ICT/SMC Zone Detector
        # ============================================
        self.zone_detector = ZoneDetector()
        self.zone_summary = {}
        
    async def start(self):
        """Start the technical analyst"""
        logger.info("Technical Analyst starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("technical_request", self.handle_technical_request)
        await self.event_bus.subscribe("price_update", self.handle_price_update)
        
        # Start analysis cycle
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
                    # Calculate indicators
                    await self.calculate_indicators()
                    
                    # Detect patterns
                    await self.detect_patterns()
                    
                    # Generate signals
                    await self.generate_signals()
                    
                    # NEW: Analyze zones
                    await self.analyze_zones()
                    
                    # Publish technical update
                    await self.publish_technical_update()
                    
            except Exception as e:
                logger.error(f"Technical analysis cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def handle_price_update(self, event: Event):
        """Handle price updates from market data"""
        if not self.running:
            return
            
        price_data = event.data
        self.price_data.append(price_data)
        
        # Keep last 1000 candles
        if len(self.price_data) > 1000:
            self.price_data.pop(0)
            
    # ============================================
    # NEW: ICT/SMC Zone Methods
    # ============================================
    
    async def analyze_zones(self):
        """Analyze ICT/SMC zones from price data"""
        try:
            if len(self.price_data) < 100:
                return
            
            # Extract price arrays
            highs = [p.get('high', 0) for p in self.price_data]
            lows = [p.get('low', 0) for p in self.price_data]
            closes = [p.get('close', 0) for p in self.price_data]
            volumes = [p.get('volume', 0) for p in self.price_data]
            opens = [p.get('open', 0) for p in self.price_data]
            
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
            
            # Update zones with latest price
            if zones and self.price_data:
                latest = self.price_data[-1]
                self.zone_detector.update_zones(
                    latest.get('high', 0),
                    latest.get('low', 0),
                    latest.get('close', 0),
                    latest.get('volume', 0),
                    latest.get('open', 0)
                )
            
            # Get zone summary
            self.zone_summary = self.zone_detector.get_zone_summary()
            
            # Add zones to patterns
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
            
            # Store zone summary in state
            await self.state_manager.set('zone_summary', self.zone_summary)
            
        except Exception as e:
            logger.error(f"Zone analysis error: {e}")
    
    async def get_zone_tps_adjustment(self, current_price: float) -> float:
        """
        Calculate TPS adjustment based on zones
        Elite zone adds up to +10 TPS points
        """
        elite_zones = self.zone_detector.get_elite_zones()
        
        if not elite_zones:
            return 0.0
        
        # Check if price is near an elite demand zone (support)
        nearest_demand = self.zone_detector.get_nearest_zone(current_price, -1)
        if nearest_demand:
            distance_pct = abs(current_price - nearest_demand.mid()) / current_price * 100
            if distance_pct < 2.0:  # Within 2% of zone
                # Scale adjustment based on score
                adjustment = nearest_demand.score * 1.2  # Max ~10 points
                return min(adjustment, 10.0)
        
        return 0.0
    
    async def get_zone_based_sl_tp(self, entry_price: float) -> Dict:
        """
        Get zone-based stop loss and take profit levels
        """
        result = {'sl': None, 'tp': None}
        
        if not self.price_data:
            return result
        
        current_price = self.price_data[-1].get('close', 0)
        
        # Find nearest demand zone for stop loss
        nearest_demand = self.zone_detector.get_nearest_zone(current_price, -1)
        if nearest_demand:
            sl_price = nearest_demand.bottom * 0.995  # 0.5% below zone
            sl_pct = (entry_price - sl_price) / entry_price * 100 if entry_price > 0 else 0
            if sl_pct <= 15:  # Max 15% stop loss
                result['sl'] = sl_price
                result['sl_zone'] = nearest_demand.to_dict()
        
        # Find nearest supply zone for take profit
        nearest_supply = self.zone_detector.get_nearest_zone(current_price, 1)
        if nearest_supply:
            tp_price = nearest_supply.top
            tp_pct = (tp_price - entry_price) / entry_price * 100 if entry_price > 0 else 0
            if 1 <= tp_pct <= 50:  # Between 1% and 50% profit
                result['tp'] = tp_price
                result['tp_zone'] = nearest_supply.to_dict()
        
        return result
    
    # ============================================
    # END OF NEW ZONE METHODS
    # ============================================
    
    async def calculate_indicators(self):
        """Calculate technical indicators"""
        if len(self.price_data) < 50:
            return
            
        closes = [p.get('close', 0) for p in self.price_data]
        highs = [p.get('high', 0) for p in self.price_data]
        lows = [p.get('low', 0) for p in self.price_data]
        volumes = [p.get('volume', 0) for p in self.price_data]
        
        # Calculate RSI
        self.indicators['rsi'] = self.calculate_rsi(closes)
        
        # Calculate MACD
        self.indicators['macd'] = self.calculate_macd(closes)
        
        # Calculate EMAs
        self.indicators['emas'] = {}
        for period in self.ema_periods:
            self.indicators['emas'][period] = self.calculate_ema(closes, period)
            
        # Calculate ATR
        self.indicators['atr'] = self.calculate_atr(highs, lows, closes)
        
        # Calculate ADX
        self.indicators['adx'] = self.calculate_adx(highs, lows, closes)
        
        # Store indicators
        await self.state_manager.set('technical_indicators', self.indicators)
        
    def calculate_rsi(self, prices: List[float]) -> float:
        """Calculate RSI (Relative Strength Index)"""
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
        rsi = 100 - (100 / (1 + rs))
        return rsi
        
    def calculate_macd(self, prices: List[float]) -> Dict[str, float]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < self.macd_slow:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
            
        ema_fast = self.calculate_ema(prices, self.macd_fast)
        ema_slow = self.calculate_ema(prices, self.macd_slow)
        macd_line = ema_fast - ema_slow
        
        # Signal line (9-period EMA of MACD)
        # Simplified: use average of last 9 MACD values
        if len(prices) >= self.macd_slow + self.macd_signal:
            signal_line = sum(prices[-self.macd_signal:]) / self.macd_signal
        else:
            signal_line = macd_line
            
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
        
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate EMA (Exponential Moving Average)"""
        if len(prices) < period:
            return prices[-1] if prices else 0
            
        multiplier = 2 / (period + 1)
        ema = prices[-period]
        
        for price in prices[-period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
            
        return ema
        
    def calculate_atr(self, highs: List[float], lows: List[float], 
                      closes: List[float], period: int = 14) -> float:
        """Calculate ATR (Average True Range)"""
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
        """Calculate ADX (Average Directional Index)"""
        # Simplified ADX calculation
        if len(closes) < period * 2:
            return 25
            
        # Calculate directional movement
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
            
        # Simplified ADX (use average of +DI and -DI)
        di_plus = (dm_plus / tr_sum) * 100 if tr_sum > 0 else 25
        di_minus = (dm_minus / tr_sum) * 100 if tr_sum > 0 else 25
        
        adx = abs(di_plus - di_minus) / (di_plus + di_minus) * 100 if (di_plus + di_minus) > 0 else 25
        return min(adx, 100)
        
    def calculate_true_range(self, high: float, low: float, prev_close: float) -> float:
        """Calculate True Range"""
        return max(high - low, abs(high - prev_close), abs(low - prev_close))
        
    async def detect_patterns(self):
        """Detect technical patterns"""
        if len(self.price_data) < 50:
            return
            
        patterns = []
        
        # Check for support/resistance
        support_resistance = self.find_support_resistance()
        if support_resistance:
            patterns.extend(support_resistance)
            
        # Check for breakouts
        breakout = self.detect_breakout()
        if breakout:
            patterns.append(breakout)
            
        # Check for trend reversal
        reversal = self.detect_reversal()
        if reversal:
            patterns.append(reversal)
            
        self.patterns = patterns
        await self.state_manager.set('technical_patterns', patterns)
        
    def find_support_resistance(self) -> List[Dict[str, Any]]:
        """Find support and resistance levels"""
        if len(self.price_data) < 20:
            return []
            
        levels = []
        prices = [p.get('close', 0) for p in self.price_data[-20:]]
        
        # Find local minima and maxima
        for i in range(5, len(prices) - 5):
            if prices[i] < min(prices[i-5:i]) and prices[i] < min(prices[i+1:i+6]):
                levels.append({
                    'type': 'support',
                    'price': prices[i],
                    'strength': 'medium'
                })
            elif prices[i] > max(prices[i-5:i]) and prices[i] > max(prices[i+1:i+6]):
                levels.append({
                    'type': 'resistance',
                    'price': prices[i],
                    'strength': 'medium'
                })
                
        return levels[:5]  # Return top 5 levels
        
    def detect_breakout(self) -> Optional[Dict[str, Any]]:
        """Detect breakout patterns"""
        if len(self.price_data) < 20:
            return None
            
        current_price = self.price_data[-1].get('close', 0)
        prev_high = max([p.get('high', 0) for p in self.price_data[-20:-1]])
        
        if current_price > prev_high * 1.02:  # 2% breakout
            return {
                'type': 'breakout',
                'direction': 'up',
                'price': current_price,
                'resistance': prev_high,
                'strength': 'strong'
            }
            
        return None
        
    def detect_reversal(self) -> Optional[Dict[str, Any]]:
        """Detect trend reversal patterns"""
        if len(self.price_data) < 30:
            return None
            
        # Check for double bottom/top
        prices = [p.get('close', 0) for p in self.price_data[-30:]]
        
        # Simple reversal detection using RSI divergence
        rsi = self.indicators.get('rsi', 50)
        price_trend = prices[-1] > prices[-5]  # Up trend?
        
        if rsi > 70 and not price_trend:
            return {
                'type': 'reversal',
                'direction': 'bearish',
                'confidence': 0.6,
                'rsi': rsi
            }
        elif rsi < 30 and price_trend:
            return {
                'type': 'reversal',
                'direction': 'bullish',
                'confidence': 0.6,
                'rsi': rsi
            }
            
        return None
        
    async def generate_signals(self):
        """Generate trading signals from technical analysis"""
        signals = []
        
        # RSI signals
        rsi = self.indicators.get('rsi', 50)
        if rsi > 70:
            signals.append({'type': 'rsi', 'signal': 'overbought', 'value': rsi})
        elif rsi < 30:
            signals.append({'type': 'rsi', 'signal': 'oversold', 'value': rsi})
            
        # MACD signals
        macd = self.indicators.get('macd', {})
        macd_line = macd.get('macd', 0)
        signal_line = macd.get('signal', 0)
        
        if macd_line > signal_line and macd_line > 0:
            signals.append({'type': 'macd', 'signal': 'bullish', 'value': macd_line})
        elif macd_line < signal_line and macd_line < 0:
            signals.append({'type': 'macd', 'signal': 'bearish', 'value': macd_line})
            
        # EMA signals
        emas = self.indicators.get('emas', {})
        current_price = self.price_data[-1].get('close', 0) if self.price_data else 0
        
        if current_price > emas.get(20, 0) > emas.get(50, 0):
            signals.append({'type': 'ema', 'signal': 'bullish', 'value': 'golden_cross'})
        elif current_price < emas.get(20, 0) < emas.get(50, 0):
            signals.append({'type': 'ema', 'signal': 'bearish', 'value': 'death_cross'})
            
        # ADX signals
        adx = self.indicators.get('adx', 25)
        if adx > 40:
            signals.append({'type': 'adx', 'signal': 'strong_trend', 'value': adx})
        elif adx < 20:
            signals.append({'type': 'adx', 'signal': 'weak_trend', 'value': adx})
            
        self.signals = signals
        await self.state_manager.set('technical_signals', signals)
        
    async def publish_technical_update(self):
        """Publish technical analysis update"""
        technical_data = {
            'indicators': self.indicators,
            'patterns': self.patterns,
            'signals': self.signals,
            'zone_summary': self.zone_summary,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="technical_data_update",
            data=technical_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def handle_technical_request(self, event: Event):
        """Handle technical data requests"""
        if not self.running:
            return
            
        technical_data = {
            'indicators': self.indicators,
            'patterns': self.patterns,
            'signals': self.signals,
            'zone_summary': self.zone_summary,
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
        """Get technical analyst status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'data_points': len(self.price_data),
            'indicators_calculated': len(self.indicators),
            'patterns_detected': len(self.patterns),
            'signals_generated': len(self.signals),
            'zone_summary': self.zone_summary,
            'timestamp': datetime.now().isoformat()
        }
