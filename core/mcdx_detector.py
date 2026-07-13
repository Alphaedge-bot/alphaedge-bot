# core/mcdx_detector.py
# AlphaEdge V13.0.6 – MCDX Plus Detector
# Detects MCDX signals: Golden Cross, Death Cross, Bottom Catch, OS, OB

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MCDXSignal:
    """MCDX signal data"""
    golden_cross: bool = False
    death_cross: bool = False
    bottom_catch: bool = False
    oversold: bool = False
    overbought: bool = False
    double_dragon: bool = False
    profit_chips: float = 50.0
    float_chips: float = 0.0
    locked_chips: float = 50.0
    score: float = 0.0
    signal_strength: str = "neutral"  # strong_bullish, bullish, neutral, bearish, strong_bearish
    
    def is_bullish(self) -> bool:
        return self.golden_cross or self.bottom_catch or self.double_dragon
    
    def is_bearish(self) -> bool:
        return self.death_cross or self.overbought
    
    def get_tps_adjustment(self, config: Dict = None) -> float:
        """Get TPS adjustment based on MCDX signals"""
        if config is None:
            config = {}
        
        adjustment = 0.0
        
        if self.golden_cross:
            adjustment += config.get('golden_cross', 5.0)
        if self.bottom_catch:
            adjustment += config.get('bottom_catch', 8.0)
        if self.double_dragon:
            adjustment += config.get('double_dragon', 10.0)
        if self.oversold:
            adjustment += config.get('oversold', 4.0)
        if self.death_cross:
            adjustment -= config.get('death_cross', 5.0)
        if self.overbought:
            adjustment -= config.get('overbought', 4.0)
            
        return adjustment


class MCDXDetector:
    """
    MCDX Plus Detector – Python translation of Pine Script
    Detects market chip distribution signals
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or self.default_config()
        self.last_signal: Optional[MCDXSignal] = None
        
    def default_config(self) -> Dict:
        return {
            'auto_length': True,
            'length': 34,
            'sma_pc_len': 10,
            'sma_lc_len': 10,
            'enabled': True,
            'tps_adjustments': {
                'golden_cross': 5.0,
                'bottom_catch': 8.0,
                'double_dragon': 10.0,
                'oversold': 4.0,
                'death_cross': -5.0,
                'overbought': -4.0
            },
            'filters': {
                'min_adx': 25
            }
        }
    
    def detect(self, close: np.ndarray, high: np.ndarray, low: np.ndarray,
               open_price: np.ndarray, volume: np.ndarray,
               adx: float = 25) -> MCDXSignal:
        """Detect MCDX signals from price data"""
        if not self.config.get('enabled', True) or len(close) < 34:
            return MCDXSignal()
        
        # Calculate MCDX components
        profit_chips = self._calculate_profit_chips(close, high, low, volume)
        float_chips = self._calculate_float_chips(close, high, low, open_price, volume)
        locked_chips = 100 - float_chips
        
        # Calculate SMAs
        sma_pc = np.mean(profit_chips[-self.config['sma_pc_len']:]) if len(profit_chips) >= self.config['sma_pc_len'] else 50
        sma_lc = np.mean(locked_chips[-self.config['sma_lc_len']:]) if len(locked_chips) >= self.config['sma_lc_len'] else 50
        
        # Detect signals
        current_pc = profit_chips[-1] if len(profit_chips) > 0 else 50
        current_lc = locked_chips[-1] if len(locked_chips) > 0 else 50
        
        # Get previous values for cross detection
        prev_pc = profit_chips[-2] if len(profit_chips) > 1 else 50
        prev_lc = locked_chips[-2] if len(locked_chips) > 1 else 50
        prev_sma_pc = sma_pc
        prev_sma_lc = sma_lc
        
        signal = MCDXSignal()
        signal.profit_chips = current_pc
        signal.float_chips = float_chips[-1] if len(float_chips) > 0 else 0
        signal.locked_chips = current_lc
        
        # Golden Cross: SMA_PC crosses above SMA_LC
        if prev_sma_pc <= prev_sma_lc and sma_pc > sma_lc:
            signal.golden_cross = True
            signal.signal_strength = "bullish"
        
        # Death Cross: SMA_PC crosses below SMA_LC
        if prev_sma_pc >= prev_sma_lc and sma_pc < sma_lc:
            signal.death_cross = True
            signal.signal_strength = "bearish"
        
        # Bottom Catch: oversold conditions + volume spike
        signal.bottom_catch = self._detect_bottom_catch(close, high, low, volume, profit_chips, locked_chips)
        
        # Oversold
        if current_pc < 30 and not signal.bottom_catch:
            signal.oversold = True
        
        # Overbought
        if current_pc > 80:
            signal.overbought = True
        
        # Double Dragon: PC > 75 + bullish price + crossover
        if current_pc > 75 and close[-1] > open_price[-1]:
            signal.double_dragon = True
            signal.signal_strength = "strong_bullish"
        
        # Determine overall signal strength
        score = 0
        if signal.golden_cross: score += 3
        if signal.bottom_catch: score += 4
        if signal.double_dragon: score += 5
        if signal.oversold: score += 2
        if signal.death_cross: score -= 3
        if signal.overbought: score -= 2
        
        signal.score = score
        
        # Final strength classification
        if score >= 5:
            signal.signal_strength = "strong_bullish"
        elif score >= 3:
            signal.signal_strength = "bullish"
        elif score <= -5:
            signal.signal_strength = "strong_bearish"
        elif score <= -3:
            signal.signal_strength = "bearish"
        else:
            signal.signal_strength = "neutral"
        
        self.last_signal = signal
        return signal
    
    def _calculate_profit_chips(self, close: np.ndarray, high: np.ndarray,
                                low: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """Calculate Profit Chips % (0-100)"""
        n = len(close)
        length = min(self.config['length'], n)
        
        if n < length:
            return np.array([50.0] * n)
        
        profit_chips = np.zeros(n)
        
        for i in range(length, n):
            window_high = np.max(high[i-length:i])
            window_low = np.min(low[i-length:i])
            range_val = window_high - window_low
            
            if range_val > 0:
                position = (close[i] - window_low) / range_val * 100
                momentum = (close[i] - close[i-1]) / close[i-1] * 100 if i > 0 else 0
                profit_chips[i] = min(max(position + momentum * 0.5, 0), 100)
            else:
                profit_chips[i] = 50
        
        return profit_chips
    
    def _calculate_float_chips(self, close: np.ndarray, high: np.ndarray,
                               low: np.ndarray, open_price: np.ndarray,
                               volume: np.ndarray) -> np.ndarray:
        """Calculate Float Chips % (0-100)"""
        n = len(close)
        length = min(self.config['length'], n)
        
        if n < length:
            return np.array([0.0] * n)
        
        float_chips = np.zeros(n)
        
        for i in range(length, n):
            window_high = np.max(high[i-length:i])
            window_low = np.min(low[i-length:i])
            range_val = window_high - window_low
            
            if range_val > 0:
                price_position = (window_high - close[i]) / range_val * 100
                vol_avg = np.mean(volume[i-20:i]) if i >= 20 else volume[i]
                vol_factor = min(volume[i] / vol_avg, 3.0) if vol_avg > 0 else 1
                float_chips[i] = min(max(price_position * 0.5 + vol_factor * 10, 0), 100)
            else:
                float_chips[i] = 0
        
        return float_chips
    
    def _detect_bottom_catch(self, close: np.ndarray, high: np.ndarray,
                             low: np.ndarray, volume: np.ndarray,
                             profit_chips: np.ndarray,
                             locked_chips: np.ndarray) -> bool:
        """Detect bottom catch signals"""
        if len(close) < 20:
            return False
        
        current_pc = profit_chips[-1] if len(profit_chips) > 0 else 50
        prev_pc = profit_chips[-2] if len(profit_chips) > 1 else 50
        prev2_pc = profit_chips[-3] if len(profit_chips) > 2 else 50
        
        # PC forming a bottom
        pc_bottom = prev2_pc > prev_pc and prev_pc < current_pc
        
        current_lc = locked_chips[-1] if len(locked_chips) > 0 else 50
        prev_lc = locked_chips[-2] if len(locked_chips) > 1 else 50
        prev2_lc = locked_chips[-3] if len(locked_chips) > 2 else 50
        
        # LC forming a top
        lc_top = prev2_lc < prev_lc and prev_lc > current_lc
        
        # Volume spike
        avg_vol = np.mean(volume[-20:-1]) if len(volume) > 20 else 1
        vol_spike = volume[-1] > avg_vol * 1.5
        
        # Price reversal
        price_up = close[-1] > open_price[-1] and close[-1] > close[-2]
        
        return pc_bottom and lc_top and vol_spike and price_up
    
    def get_signal_summary(self) -> Dict:
        """Get summary of MCDX signals"""
        if not self.last_signal:
            return {'status': 'no_data'}
        
        return {
            'golden_cross': self.last_signal.golden_cross,
            'death_cross': self.last_signal.death_cross,
            'bottom_catch': self.last_signal.bottom_catch,
            'oversold': self.last_signal.oversold,
            'overbought': self.last_signal.overbought,
            'double_dragon': self.last_signal.double_dragon,
            'profit_chips': self.last_signal.profit_chips,
            'locked_chips': self.last_signal.locked_chips,
            'score': self.last_signal.score,
            'signal_strength': self.last_signal.signal_strength,
            'tps_adjustment': self.last_signal.get_tps_adjustment(self.config.get('tps_adjustments', {}))
        }
