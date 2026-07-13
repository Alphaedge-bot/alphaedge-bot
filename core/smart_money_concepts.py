# core/smart_money_concepts.py
# AlphaEdge V13.0.6 – Smart Money Concepts (LuxAlgo + Validated SMC)
# ICT/SMC: BOS/CHoCH, Order Blocks, FVG, EQH/EQL, Breaker Blocks, IFVG, CISD, OTE
# Full Validation Layer: Sweep + Displacement Required

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SMCValidation:
    """Validation layer for SMC signals"""
    has_sweep: bool = False
    has_displacement: bool = False
    sweep_price: float = 0.0
    displacement_size: float = 0.0
    sweep_type: str = ""  # "swing_high", "swing_low", "internal_high", "internal_low"
    
    def is_valid(self) -> bool:
        """Both sweep and displacement required for validation"""
        return self.has_sweep and self.has_displacement


@dataclass
class SMCSignal:
    """Complete Smart Money Concepts signal data"""
    # Structure
    swing_bos_bullish: bool = False
    swing_bos_bearish: bool = False
    swing_choch_bullish: bool = False
    swing_choch_bearish: bool = False
    internal_bos_bullish: bool = False
    internal_bos_bearish: bool = False
    internal_choch_bullish: bool = False
    internal_choch_bearish: bool = False
    
    # Order Blocks (Validated)
    bullish_ob: bool = False
    bearish_ob: bool = False
    ob_score: int = 0
    ob_validation: Optional[SMCValidation] = None
    
    # Breaker Blocks
    bullish_breaker: bool = False
    bearish_breaker: bool = False
    breaker_score: int = 0
    
    # Fair Value Gaps
    bullish_fvg: bool = False
    bearish_fvg: bool = False
    bullish_ifvg: bool = False  # Inversion FVG
    bearish_ifvg: bool = False
    bpr_active: bool = False  # Balanced Price Range
    
    # Equal Highs/Lows
    eqh_detected: bool = False
    eql_detected: bool = False
    
    # Premium/Discount
    premium_zone: bool = False
    discount_zone: bool = False
    equilibrium_price: float = 0.0
    
    # OTE Zones
    bullish_ote: bool = False
    bearish_ote: bool = False
    ote_top: float = 0.0
    ote_bottom: float = 0.0
    
    # CISD (Change in State of Delivery)
    cisd_bullish: bool = False
    cisd_bearish: bool = False
    
    # Inducement
    inducement_triggered: bool = False
    
    # Trend Bias
    trend_bias: str = "neutral"  # bullish, bearish, neutral
    
    # Confluence Score (0-10)
    confluence_score: int = 0
    
    def get_tps_adjustment(self, config: Dict = None) -> float:
        """Calculate TPS adjustment from all SMC signals"""
        if config is None:
            config = {}
        
        adjustment = 0.0
        
        # --- STRONG BULLISH SIGNALS ---
        if self.swing_bos_bullish:
            adjustment += config.get('swing_bos_bullish', 6.0)
        if self.swing_choch_bullish:
            adjustment += config.get('swing_choch_bullish', 4.0)
        if self.internal_bos_bullish:
            adjustment += config.get('internal_bos_bullish', 3.0)
        
        # --- VALIDATED ORDER BLOCKS ---
        if self.bullish_ob and self.ob_validation and self.ob_validation.is_valid():
            adjustment += config.get('bullish_ob_validated', 8.0)
        elif self.bullish_ob:
            adjustment += config.get('bullish_ob', 4.0)
        
        # --- BREAKER BLOCKS ---
        if self.bullish_breaker:
            adjustment += config.get('bullish_breaker', 6.0)
        
        # --- FVGs ---
        if self.bullish_fvg:
            adjustment += config.get('bullish_fvg', 4.0)
        if self.bullish_ifvg:
            adjustment += config.get('bullish_ifvg', 5.0)
        if self.bpr_active:
            adjustment += config.get('bpr_active', 3.0)
        
        # --- OTE ZONES ---
        if self.bullish_ote:
            adjustment += config.get('bullish_ote', 4.0)
        
        # --- CISD ---
        if self.cisd_bullish:
            adjustment += config.get('cisd_bullish', 3.0)
        
        # --- INDUCEMENT ---
        if self.inducement_triggered:
            adjustment += config.get('inducement_triggered', 3.0)
        
        # --- DISCOUNT ZONE ---
        if self.discount_zone:
            adjustment += config.get('discount_zone', 3.0)
        
        # --- STRONG BEARISH SIGNALS ---
        if self.swing_bos_bearish:
            adjustment -= config.get('swing_bos_bearish', 6.0)
        if self.swing_choch_bearish:
            adjustment -= config.get('swing_choch_bearish', 4.0)
        if self.internal_bos_bearish:
            adjustment -= config.get('internal_bos_bearish', 3.0)
        
        if self.bearish_ob and self.ob_validation and self.ob_validation.is_valid():
            adjustment -= config.get('bearish_ob_validated', 8.0)
        elif self.bearish_ob:
            adjustment -= config.get('bearish_ob', 4.0)
        
        if self.bearish_breaker:
            adjustment -= config.get('bearish_breaker', 6.0)
        if self.bearish_fvg:
            adjustment -= config.get('bearish_fvg', 4.0)
        if self.bearish_ifvg:
            adjustment -= config.get('bearish_ifvg', 5.0)
        if self.bearish_ote:
            adjustment -= config.get('bearish_ote', 4.0)
        if self.cisd_bearish:
            adjustment -= config.get('cisd_bearish', 3.0)
        if self.premium_zone:
            adjustment -= config.get('premium_zone', 3.0)
        
        # --- CONFLUENCE SCORE ---
        if self.confluence_score >= 7:
            adjustment += config.get('confluence_score_high', 6.0)
        elif self.confluence_score >= 4:
            adjustment += config.get('confluence_score_medium', 3.0)
        
        return adjustment


class SmartMoneyConcepts:
    """
    Smart Money Concepts Detector (LuxAlgo + Validated SMC)
    Full ICT/SMC implementation with validation layer
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or self.default_config()
        self.last_signal: Optional[SMCSignal] = None
        
        # State tracking
        self.swing_high_price = 0.0
        self.swing_low_price = 0.0
        self.swing_high_idx = 0
        self.swing_low_idx = 0
        self.swing_high_broken = False
        self.swing_low_broken = False
        self.swing_trend_bullish = True
        
        self.internal_high_price = 0.0
        self.internal_low_price = 0.0
        self.internal_high_idx = 0
        self.internal_low_idx = 0
        self.internal_high_broken = False
        self.internal_low_broken = False
        self.internal_trend_bullish = True
        
        # CISD tracking
        self.last_bearish_open = 0.0
        self.last_bullish_open = 0.0
        
        # Inducement tracking
        self.inducement_active = False
        self.inducement_price = 0.0
        self.inducement_is_bullish = True
        self.inducement_triggered = False
        
        # Order Block tracking
        self.bullish_ob_valid = False
        self.bearish_ob_valid = False
        self.last_ob_score = 0
        
    def default_config(self) -> Dict:
        return {
            'enabled': True,
            'swing_length': 10,
            'internal_length': 5,
            'equal_highs_lows_length': 3,
            'equal_highs_lows_threshold': 0.15,
            'fvg_threshold': 0.5,  # ATR multiplier
            'atr_length': 14,
            'min_confluence_score': 3,
            'tps_adjustments': {
                'swing_bos_bullish': 6.0,
                'swing_choch_bullish': 4.0,
                'internal_bos_bullish': 3.0,
                'bullish_ob': 4.0,
                'bullish_ob_validated': 8.0,
                'bullish_breaker': 6.0,
                'bullish_fvg': 4.0,
                'bullish_ifvg': 5.0,
                'bpr_active': 3.0,
                'bullish_ote': 4.0,
                'cisd_bullish': 3.0,
                'inducement_triggered': 3.0,
                'discount_zone': 3.0,
                'swing_bos_bearish': -6.0,
                'swing_choch_bearish': -4.0,
                'internal_bos_bearish': -3.0,
                'bearish_ob': -4.0,
                'bearish_ob_validated': -8.0,
                'bearish_breaker': -6.0,
                'bearish_fvg': -4.0,
                'bearish_ifvg': -5.0,
                'bearish_ote': -4.0,
                'cisd_bearish': -3.0,
                'premium_zone': -3.0,
                'confluence_score_high': 6.0,
                'confluence_score_medium': 3.0
            }
        }
    
    def detect(self, high: np.ndarray, low: np.ndarray, close: np.ndarray,
               open_price: np.ndarray, volume: np.ndarray) -> SMCSignal:
        """Detect all Smart Money Concepts signals"""
        if not self.config.get('enabled', True) or len(close) < 50:
            return SMCSignal()
        
        signal = SMCSignal()
        
        # Calculate ATR
        atr = self._calculate_atr(high, low, close, self.config['atr_length'])
        
        # --- 1. DETECT PIVOTS ---
        self._detect_pivots(high, low)
        
        # --- 2. DETECT STRUCTURE BREAKS (BOS/CHoCH) ---
        structure_result = self._detect_structure_breaks(high, low, close, atr)
        signal.swing_bos_bullish = structure_result.get('swing_bos_bullish', False)
        signal.swing_bos_bearish = structure_result.get('swing_bos_bearish', False)
        signal.swing_choch_bullish = structure_result.get('swing_choch_bullish', False)
        signal.swing_choch_bearish = structure_result.get('swing_choch_bearish', False)
        signal.internal_bos_bullish = structure_result.get('internal_bos_bullish', False)
        signal.internal_bos_bearish = structure_result.get('internal_bos_bearish', False)
        signal.internal_choch_bullish = structure_result.get('internal_choch_bullish', False)
        signal.internal_choch_bearish = structure_result.get('internal_choch_bearish', False)
        
        # --- 3. DETECT ORDER BLOCKS (With Validation) ---
        ob_result = self._detect_order_blocks(high, low, close, open_price, volume, atr)
        signal.bullish_ob = ob_result.get('bullish', False)
        signal.bearish_ob = ob_result.get('bearish', False)
        signal.ob_score = ob_result.get('score', 0)
        signal.ob_validation = ob_result.get('validation')
        
        # --- 4. DETECT BREAKER BLOCKS ---
        breaker_result = self._detect_breaker_blocks(high, low, close, atr)
        signal.bullish_breaker = breaker_result.get('bullish', False)
        signal.bearish_breaker = breaker_result.get('bearish', False)
        signal.breaker_score = breaker_result.get('score', 0)
        
        # --- 5. DETECT FVGs ---
        fvg_result = self._detect_fvg(high, low, close, open_price, atr)
        signal.bullish_fvg = fvg_result.get('bullish', False)
        signal.bearish_fvg = fvg_result.get('bearish', False)
        signal.bullish_ifvg = fvg_result.get('bullish_ifvg', False)
        signal.bearish_ifvg = fvg_result.get('bearish_ifvg', False)
        signal.bpr_active = fvg_result.get('bpr_active', False)
        
        # --- 6. DETECT OTE ZONES ---
        ote_result = self._detect_ote_zones(high, low, close, atr)
        signal.bullish_ote = ote_result.get('bullish', False)
        signal.bearish_ote = ote_result.get('bearish', False)
        signal.ote_top = ote_result.get('top', 0)
        signal.ote_bottom = ote_result.get('bottom', 0)
        
        # --- 7. DETECT EQUAL HIGHS/LOWS ---
        eq_result = self._detect_equal_highs_lows(high, low, atr)
        signal.eqh_detected = eq_result.get('eqh', False)
        signal.eql_detected = eq_result.get('eql', False)
        
        # --- 8. DETECT PREMIUM/DISCOUNT ZONES ---
        pd_result = self._detect_premium_discount_zones(high, low, close)
        signal.premium_zone = pd_result.get('premium', False)
        signal.discount_zone = pd_result.get('discount', False)
        signal.equilibrium_price = pd_result.get('equilibrium', 0)
        
        # --- 9. DETECT CISD ---
        cisd_result = self._detect_cisd(close, open_price)
        signal.cisd_bullish = cisd_result.get('bullish', False)
        signal.cisd_bearish = cisd_result.get('bearish', False)
        
        # --- 10. DETECT INDUCEMENT ---
        inducement_result = self._detect_inducement(high, low, close)
        signal.inducement_triggered = inducement_result.get('triggered', False)
        
        # --- 11. DETERMINE TREND BIAS ---
        signal.trend_bias = self._determine_trend_bias(close, high, low)
        
        # --- 12. CALCULATE CONFLUENCE SCORE ---
        signal.confluence_score = self._calculate_confluence_score(signal)
        
        # --- 13. UPDATE STATE ---
        self.last_signal = signal
        
        return signal
    
    def _detect_pivots(self, high: np.ndarray, low: np.ndarray):
        """Detect swing and internal pivots"""
        n = len(high)
        swing_len = self.config['swing_length']
        internal_len = self.config['internal_length']
        
        # Swing pivots
        if n > swing_len * 2:
            # Swing high
            for i in range(n - swing_len, n):
                is_high = True
                for j in range(max(0, i - swing_len), min(n, i + swing_len + 1)):
                    if j != i and high[j] > high[i]:
                        is_high = False
                        break
                if is_high:
                    self.swing_high_price = high[i]
                    self.swing_high_idx = i
                    self.swing_high_broken = False
                    break
            
            # Swing low
            for i in range(n - swing_len, n):
                is_low = True
                for j in range(max(0, i - swing_len), min(n, i + swing_len + 1)):
                    if j != i and low[j] < low[i]:
                        is_low = False
                        break
                if is_low:
                    self.swing_low_price = low[i]
                    self.swing_low_idx = i
                    self.swing_low_broken = False
                    break
        
        # Internal pivots
        if n > internal_len * 2:
            for i in range(n - internal_len, n):
                is_high = True
                for j in range(max(0, i - internal_len), min(n, i + internal_len + 1)):
                    if j != i and high[j] > high[i]:
                        is_high = False
                        break
                if is_high:
                    self.internal_high_price = high[i]
                    self.internal_high_idx = i
                    self.internal_high_broken = False
                    break
            
            for i in range(n - internal_len, n):
                is_low = True
                for j in range(max(0, i - internal_len), min(n, i + internal_len + 1)):
                    if j != i and low[j] < low[i]:
                        is_low = False
                        break
                if is_low:
                    self.internal_low_price = low[i]
                    self.internal_low_idx = i
                    self.internal_low_broken = False
                    break
    
    def _detect_structure_breaks(self, high: np.ndarray, low: np.ndarray,
                                 close: np.ndarray, atr: float) -> Dict:
        """Detect BOS/CHoCH breaks with real-time detection"""
        n = len(close)
        current_price = close[-1]
        
        result = {
            'swing_bos_bullish': False,
            'swing_bos_bearish': False,
            'swing_choch_bullish': False,
            'swing_choch_bearish': False,
            'internal_bos_bullish': False,
            'internal_bos_bearish': False,
            'internal_choch_bullish': False,
            'internal_choch_bearish': False
        }
        
        # --- SWING STRUCTURE ---
        if self.swing_high_price > 0 and not self.swing_high_broken:
            if current_price > self.swing_high_price:
                self.swing_high_broken = True
                result['swing_bos_bullish'] = True
                if not self.swing_trend_bullish:
                    result['swing_choch_bullish'] = True
                self.swing_trend_bullish = True
        
        if self.swing_low_price > 0 and not self.swing_low_broken:
            if current_price < self.swing_low_price:
                self.swing_low_broken = True
                result['swing_bos_bearish'] = True
                if self.swing_trend_bullish:
                    result['swing_choch_bearish'] = True
                self.swing_trend_bullish = False
        
        # --- INTERNAL STRUCTURE ---
        if self.internal_high_price > 0 and not self.internal_high_broken:
            if current_price > self.internal_high_price:
                self.internal_high_broken = True
                result['internal_bos_bullish'] = True
                if not self.internal_trend_bullish:
                    result['internal_choch_bullish'] = True
                self.internal_trend_bullish = True
        
        if self.internal_low_price > 0 and not self.internal_low_broken:
            if current_price < self.internal_low_price:
                self.internal_low_broken = True
                result['internal_bos_bearish'] = True
                if self.internal_trend_bullish:
                    result['internal_choch_bearish'] = True
                self.internal_trend_bullish = False
        
        return result
    
    def _detect_order_blocks(self, high: np.ndarray, low: np.ndarray,
                             close: np.ndarray, open_price: np.ndarray,
                             volume: np.ndarray, atr: float) -> Dict:
        """Detect Order Blocks with validation (sweep + displacement)"""
        n = len(close)
        result = {
            'bullish': False,
            'bearish': False,
            'score': 0,
            'validation': None
        }
        
        if n < 20:
            return result
        
        # Look for recent swing pivot
        if n > self.config['swing_length']:
            idx = n - 1
            
            # --- BULLISH OB (Bearish candle that swept a swing low) ---
            is_bearish = close[idx] < open_price[idx]
            if is_bearish and self.swing_low_price > 0:
                # Check sweep: OB candle swept the swing low
                has_sweep = low[idx] < self.swing_low_price
                # Check displacement: subsequent bullish FVG
                has_displacement = False
                if n > 3:
                    has_displacement = low[n-1] > high[n-3]
                
                if has_sweep and has_displacement:
                    result['bullish'] = True
                    result['score'] += 4
                    result['validation'] = SMCValidation(
                        has_sweep=True,
                        has_displacement=True,
                        sweep_price=self.swing_low_price,
                        displacement_size=abs(low[n-1] - high[n-3]),
                        sweep_type="swing_low"
                    )
                    self.bullish_ob_valid = True
            
            # --- BEARISH OB (Bullish candle that swept a swing high) ---
            is_bullish = close[idx] > open_price[idx]
            if is_bullish and self.swing_high_price > 0:
                has_sweep = high[idx] > self.swing_high_price
                has_displacement = False
                if n > 3:
                    has_displacement = high[n-1] < low[n-3]
                
                if has_sweep and has_displacement:
                    result['bearish'] = True
                    result['score'] += 4
                    result['validation'] = SMCValidation(
                        has_sweep=True,
                        has_displacement=True,
                        sweep_price=self.swing_high_price,
                        displacement_size=abs(high[n-1] - low[n-3]),
                        sweep_type="swing_high"
                    )
                    self.bearish_ob_valid = True
        
        return result
    
    def _detect_breaker_blocks(self, high: np.ndarray, low: np.ndarray,
                               close: np.ndarray, atr: float) -> Dict:
        """Detect Breaker Blocks (failed OBs that flip direction)"""
        result = {'bullish': False, 'bearish': False, 'score': 0}
        
        # Simplified: if price breaks through a validated OB from the other side
        if self.bullish_ob_valid and close[-1] < self.swing_low_price:
            result['bearish'] = True
            result['score'] += 3
        
        if self.bearish_ob_valid and close[-1] > self.swing_high_price:
            result['bullish'] = True
            result['score'] += 3
        
        return result
    
    def _detect_fvg(self, high: np.ndarray, low: np.ndarray,
                    close: np.ndarray, open_price: np.ndarray,
                    atr: float) -> Dict:
        """Detect Fair Value Gaps and Inversion FVGs"""
        n = len(close)
        threshold = atr * self.config['fvg_threshold']
        
        result = {
            'bullish': False,
            'bearish': False,
            'bullish_ifvg': False,
            'bearish_ifvg': False,
            'bpr_active': False
        }
        
        if n < 3:
            return result
        
        # --- BULLISH FVG (gap up) ---
        gap_up = low[n-1] > high[n-3]
        if gap_up:
            gap_size = low[n-1] - high[n-3]
            if gap_size > threshold:
                result['bullish'] = True
                # Check if FVG is mitigated (filled) = IFVG
                if low[n-1] <= high[n-2]:
                    result['bullish_ifvg'] = True
        
        # --- BEARISH FVG (gap down) ---
        gap_down = high[n-1] < low[n-3]
        if gap_down:
            gap_size = low[n-3] - high[n-1]
            if gap_size > threshold:
                result['bearish'] = True
                if high[n-1] >= low[n-2]:
                    result['bearish_ifvg'] = True
        
        # --- BPR (Balanced Price Range) - overlap of bullish and bearish FVGs ---
        if result['bullish'] and result['bearish']:
            # Check if they overlap
            bull_top = low[n-1]
            bull_bot = high[n-3]
            bear_top = low[n-3]
            bear_bot = high[n-1]
            
            if bull_bot <= bear_top and bull_top >= bear_bot:
                result['bpr_active'] = True
        
        return result
    
    def _detect_equal_highs_lows(self, high: np.ndarray, low: np.ndarray,
                                 atr: float) -> Dict:
        """Detect Equal Highs and Equal Lows"""
        n = len(high)
        length = self.config['equal_highs_lows_length']
        threshold = self.config['equal_highs_lows_threshold']
        
        result = {'eqh': False, 'eql': False}
        
        if n < length + 1:
            return result
        
        tolerance = threshold * atr
        
        # Equal Highs (EQH)
        for i in range(1, length + 1):
            if abs(high[n-1] - high[n-1-i]) < tolerance:
                result['eqh'] = True
                break
        
        # Equal Lows (EQL)
        for i in range(1, length + 1):
            if abs(low[n-1] - low[n-1-i]) < tolerance:
                result['eql'] = True
                break
        
        return result
    
    def _detect_premium_discount_zones(self, high: np.ndarray, low: np.ndarray,
                                       close: np.ndarray) -> Dict:
        """Detect Premium and Discount zones"""
        n = len(close)
        if n < 50:
            return {'premium': False, 'discount': False, 'equilibrium': 0}
        
        swing_high = np.max(high[-50:])
        swing_low = np.min(low[-50:])
        range_val = swing_high - swing_low
        current_price = close[-1]
        eq = (swing_high + swing_low) / 2
        
        result = {'premium': False, 'discount': False, 'equilibrium': eq}
        
        # Premium zone: above 70% retracement
        premium_threshold = swing_high - range_val * 0.3
        if current_price > premium_threshold:
            result['premium'] = True
        
        # Discount zone: below 30% retracement
        discount_threshold = swing_low + range_val * 0.3
        if current_price < discount_threshold:
            result['discount'] = True
        
        return result
    
    def _detect_cisd(self, close: np.ndarray, open_price: np.ndarray) -> Dict:
        """Detect Change in State of Delivery"""
        result = {'bullish': False, 'bearish': False}
        
        if len(close) < 2:
            return result
        
        # Track last bearish and bullish opens
        if close[-2] < open_price[-2]:
            self.last_bearish_open = open_price[-2]
        if close[-2] > open_price[-2]:
            self.last_bullish_open = open_price[-2]
        
        # Bullish CISD: close > last bearish open
        if self.last_bearish_open > 0 and close[-1] > self.last_bearish_open:
            result['bullish'] = True
        
        # Bearish CISD: close < last bullish open
        if self.last_bullish_open > 0 and close[-1] < self.last_bullish_open:
            result['bearish'] = True
        
        return result
    
    def _detect_inducement(self, high: np.ndarray, low: np.ndarray,
                           close: np.ndarray) -> Dict:
        """Detect Inducement (IDM) sweeps"""
        result = {'triggered': False}
        
        if len(close) < 5:
            return result
        
        # Bullish IDM: internal low swept while swing trend is bullish
        if self.swing_trend_bullish and self.internal_low_price > 0:
            if low[-1] < self.internal_low_price and close[-1] > self.internal_low_price:
                result['triggered'] = True
                self.inducement_triggered = True
        
        # Bearish IDM: internal high swept while swing trend is bearish
        if not self.swing_trend_bullish and self.internal_high_price > 0:
            if high[-1] > self.internal_high_price and close[-1] < self.internal_high_price:
                result['triggered'] = True
                self.inducement_triggered = True
        
        return result
    
    def _detect_ote_zones(self, high: np.ndarray, low: np.ndarray,
                          close: np.ndarray, atr: float) -> Dict:
        """Detect OTE Fibonacci zones (61.8%-78.6% retracement)"""
        n = len(close)
        result = {'bullish': False, 'bearish': False, 'top': 0, 'bottom': 0}
        
        if n < 30:
            return result
        
        # Find displacement leg (last 30 bars)
        leg_high = np.max(high[-30:])
        leg_low = np.min(low[-30:])
        leg_range = leg_high - leg_low
        
        if leg_range <= 0:
            return result
        
        # Bullish OTE: buy the dip (retracement down)
        if close[-1] < leg_high and close[-1] > leg_low:
            # Current price is within the leg
            retracement = (leg_high - close[-1]) / leg_range
            if 0.618 <= retracement <= 0.786:
                result['bullish'] = True
                result['top'] = leg_high - leg_range * 0.618
                result['bottom'] = leg_high - leg_range * 0.786
        
        # Bearish OTE: sell the rally (retracement up)
        if close[-1] > leg_low and close[-1] < leg_high:
            retracement = (close[-1] - leg_low) / leg_range
            if 0.618 <= retracement <= 0.786:
                result['bearish'] = True
                result['top'] = leg_low + leg_range * 0.786
                result['bottom'] = leg_low + leg_range * 0.618
        
        return result
    
    def _determine_trend_bias(self, close: np.ndarray, high: np.ndarray,
                              low: np.ndarray) -> str:
        """Determine trend bias from structure and EMA"""
        n = len(close)
        if n < 20:
            return "neutral"
        
        ema20 = np.mean(close[-20:])
        ema50 = np.mean(close[-50:]) if n >= 50 else ema20
        
        if self.swing_trend_bullish and close[-1] > ema20:
            return "bullish"
        elif not self.swing_trend_bullish and close[-1] < ema20:
            return "bearish"
        else:
            return "neutral"
    
    def _calculate_confluence_score(self, signal: SMCSignal) -> int:
        """Calculate confluence score (0-10)"""
        score = 0
        
        # Structure breaks (2 points each)
        if signal.swing_bos_bullish or signal.swing_bos_bearish:
            score += 2
        if signal.swing_choch_bullish or signal.swing_choch_bearish:
            score += 2
        
        # Order Blocks (2 points each)
        if signal.bullish_ob or signal.bearish_ob:
            score += 2
        if signal.ob_validation and signal.ob_validation.is_valid():
            score += 2
        
        # Breaker Blocks (2 points)
        if signal.bullish_breaker or signal.bearish_breaker:
            score += 2
        
        # FVGs (1 point each)
        if signal.bullish_fvg or signal.bearish_fvg:
            score += 1
        if signal.bullish_ifvg or signal.bearish_ifvg:
            score += 1
        
        # CISD (1 point)
        if signal.cisd_bullish or signal.cisd_bearish:
            score += 1
        
        # OTE (1 point)
        if signal.bullish_ote or signal.bearish_ote:
            score += 1
        
        # Inducement (1 point)
        if signal.inducement_triggered:
            score += 1
        
        return min(score, 10)
    
    def _calculate_atr(self, high: np.ndarray, low: np.ndarray,
                       close: np.ndarray, period: int) -> float:
        """Calculate ATR"""
        n = len(close)
        if n < period + 1:
            return 0.01
        
        tr = np.zeros(n)
        for i in range(1, n):
            tr[i] = max(high[i] - low[i],
                       abs(high[i] - close[i-1]),
                       abs(low[i] - close[i-1]))
        
        atr = np.mean(tr[-period:])
        return max(atr, 0.01)
    
    def get_signal_summary(self) -> Dict:
        """Get summary of SMC signals"""
        if not self.last_signal:
            return {'status': 'no_data'}
        
        return {
            'trend_bias': self.last_signal.trend_bias,
            'swing_bos_bullish': self.last_signal.swing_bos_bullish,
            'swing_bos_bearish': self.last_signal.swing_bos_bearish,
            'swing_choch_bullish': self.last_signal.swing_choch_bullish,
            'swing_choch_bearish': self.last_signal.swing_choch_bearish,
            'bullish_ob': self.last_signal.bullish_ob,
            'bearish_ob': self.last_signal.bearish_ob,
            'ob_validated': self.last_signal.ob_validation.is_valid() if self.last_signal.ob_validation else False,
            'bullish_breaker': self.last_signal.bullish_breaker,
            'bearish_breaker': self.last_signal.bearish_breaker,
            'bullish_fvg': self.last_signal.bullish_fvg,
            'bearish_fvg': self.last_signal.bearish_fvg,
            'bullish_ifvg': self.last_signal.bullish_ifvg,
            'bearish_ifvg': self.last_signal.bearish_ifvg,
            'bpr_active': self.last_signal.bpr_active,
            'eqh_detected': self.last_signal.eqh_detected,
            'eql_detected': self.last_signal.eql_detected,
            'premium_zone': self.last_signal.premium_zone,
            'discount_zone': self.last_signal.discount_zone,
            'cisd_bullish': self.last_signal.cisd_bullish,
            'cisd_bearish': self.last_signal.cisd_bearish,
            'inducement_triggered': self.last_signal.inducement_triggered,
            'bullish_ote': self.last_signal.bullish_ote,
            'bearish_ote': self.last_signal.bearish_ote,
            'confluence_score': self.last_signal.confluence_score,
            'tps_adjustment': self.last_signal.get_tps_adjustment(self.config.get('tps_adjustments', {}))
        }
