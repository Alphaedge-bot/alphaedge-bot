# core/zone_detector.py
# AlphaEdge V13.0.5 – ICT/SMC Zone Detection Module

import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Zone:
    """Represents an ICT/SMC zone"""
    kind: int  # 0=imbalance (gap), 1=pool (swing)
    direction: int  # -1=down (demand/support), 1=up (supply/resistance)
    top: float
    bottom: float
    top0: float = 0.0
    bottom0: float = 0.0
    born_bar: int = 0
    last_bar: int = 0
    tests: int = 0
    volume_abs: float = 0.0
    volume_dir: float = 0.0
    confluence: int = 1
    phase: int = 0  # 0=live, 1=partial, 2=done
    score: float = 0.0
    penetration: float = 0.0
    inside: bool = False
    alive: bool = True
    price: float = 0.0
    
    def is_elite(self, threshold: float = 8.0) -> bool:
        return self.score >= threshold and self.phase != 2
    
    def is_demand(self) -> bool:
        return self.direction < 0
    
    def is_supply(self) -> bool:
        return self.direction > 0
    
    def mid(self) -> float:
        return (self.top + self.bottom) / 2.0
    
    def height(self) -> float:
        return self.top - self.bottom
    
    def to_dict(self) -> Dict:
        return {
            'kind': 'gap' if self.kind == 0 else 'pool',
            'direction': 'supply' if self.direction > 0 else 'demand',
            'top': self.top,
            'bottom': self.bottom,
            'mid': self.mid(),
            'score': self.score,
            'is_elite': self.is_elite(),
            'phase': self.phase,
            'confluence': self.confluence,
            'tests': self.tests
        }


class ZoneDetector:
    """Detects and manages ICT/SMC zones"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self.default_config()
        self.zones: List[Zone] = []
        self.atr = 0.0
        self.vol_base = 0.0
        self.bar_index = 0
        
    def default_config(self) -> Dict:
        return {
            'max_zones': 28,
            'lookback': 3000,
            'atr_length': 200,
            'vol_length': 50,
            'min_gap_atr': 0.05,
            'min_gap_pct': 0.0,
            'left_bars': 12,
            'right_bars': 4,
            'pool_height': 0.45,
            'pool_buffer': 0.03,
            'elite_threshold': 8.0,
            'size_norm': 1.20,
            'vol_norm': 1.40,
            'test_norm': 3.0,
            'conf_norm': 2.0,
            'prox_norm': 6.0,
            'merge_overlap': 0.15,
            'stale_deviation': 6.0,
            'keep_done': True,
            'enabled': True
        }
    
    def update_config(self, config: Dict):
        self.config.update(config)
    
    def detect_zones(self, high: np.ndarray, low: np.ndarray, 
                     close: np.ndarray, volume: np.ndarray,
                     open_price: np.ndarray) -> List[Zone]:
        if not self.config.get('enabled', True):
            return []
        
        n = len(close)
        self.bar_index = n - 1
        self.atr = self._calculate_atr(high, low, close)
        self.vol_base = self._calculate_volume_baseline(volume)
        
        if self.atr <= 0:
            return []
        
        zones = []
        gaps = self._detect_gaps(high, low, close, open_price, volume)
        zones.extend(gaps)
        pools = self._detect_pools(high, low, close, volume)
        zones.extend(pools)
        
        if self.config['merge_overlap'] > 0:
            zones = self._merge_zones(zones)
        
        for zone in zones:
            zone.score = self._calculate_score(zone, close[-1])
        
        zones = self._filter_stale_zones(zones, close[-1])
        zones.sort(key=lambda z: z.score, reverse=True)
        
        if len(zones) > self.config['max_zones']:
            zones = zones[:self.config['max_zones']]
        
        self.zones = zones
        return zones
    
    def _detect_gaps(self, high: np.ndarray, low: np.ndarray,
                     close: np.ndarray, open_price: np.ndarray,
                     volume: np.ndarray) -> List[Zone]:
        zones = []
        n = len(close)
        
        for i in range(2, n):
            if low[i] > high[i-2]:
                gap_size = low[i] - high[i-2]
                if gap_size >= self.atr * self.config['min_gap_atr']:
                    if close[i-1] > 0:
                        gap_pct = gap_size / close[i-1] * 100.0
                        if gap_pct >= self.config['min_gap_pct']:
                            vol_abs = volume[i-1] + volume[i]
                            vol_dir = (volume[i-1] * (close[i-1] - open_price[i-1])) + \
                                     (volume[i] * (close[i] - open_price[i]))
                            zone = Zone(
                                kind=0, direction=-1,
                                top=low[i], bottom=high[i-2],
                                top0=low[i], bottom0=high[i-2],
                                born_bar=i-1, last_bar=i-1,
                                volume_abs=vol_abs, volume_dir=vol_dir,
                                price=close[i]
                            )
                            zones.append(zone)
            
            elif high[i] < low[i-2]:
                gap_size = low[i-2] - high[i]
                if gap_size >= self.atr * self.config['min_gap_atr']:
                    if close[i-1] > 0:
                        gap_pct = gap_size / close[i-1] * 100.0
                        if gap_pct >= self.config['min_gap_pct']:
                            vol_abs = volume[i-1] + volume[i]
                            vol_dir = (volume[i-1] * (close[i-1] - open_price[i-1])) + \
                                     (volume[i] * (close[i] - open_price[i]))
                            zone = Zone(
                                kind=0, direction=1,
                                top=low[i-2], bottom=high[i],
                                top0=low[i-2], bottom0=high[i],
                                born_bar=i-1, last_bar=i-1,
                                volume_abs=vol_abs, volume_dir=vol_dir,
                                price=close[i]
                            )
                            zones.append(zone)
        return zones
    
    def _detect_pools(self, high: np.ndarray, low: np.ndarray,
                      close: np.ndarray, volume: np.ndarray) -> List[Zone]:
        zones = []
        n = len(close)
        left = self.config['left_bars']
        right = self.config['right_bars']
        
        for i in range(left, n - right):
            is_high = True
            for j in range(i - left, i + right + 1):
                if j != i and high[j] > high[i]:
                    is_high = False
                    break
            if is_high:
                base = high[i] + self.atr * self.config['pool_buffer']
                vol_abs = sum(volume[i-left:i+right+1]) if i-left >= 0 else 0
                vol_dir = 0.0
                for j in range(1, right + left + 1):
                    idx = i - left + j
                    if 0 < idx < n:
                        vol_dir += volume[idx] * (close[idx] - close[idx-1])
                zone = Zone(
                    kind=1, direction=1,
                    top=base + self.atr * self.config['pool_height'], bottom=base,
                    top0=base + self.atr * self.config['pool_height'], bottom0=base,
                    born_bar=i - right, last_bar=i - right,
                    volume_abs=vol_abs, volume_dir=vol_dir,
                    price=close[i]
                )
                zones.append(zone)
            
            is_low = True
            for j in range(i - left, i + right + 1):
                if j != i and low[j] < low[i]:
                    is_low = False
                    break
            if is_low:
                base = low[i] - self.atr * self.config['pool_buffer']
                vol_abs = sum(volume[i-left:i+right+1]) if i-left >= 0 else 0
                vol_dir = 0.0
                for j in range(1, right + left + 1):
                    idx = i - left + j
                    if 0 < idx < n:
                        vol_dir += volume[idx] * (close[idx] - close[idx-1])
                zone = Zone(
                    kind=1, direction=-1,
                    top=base, bottom=base - self.atr * self.config['pool_height'],
                    top0=base, bottom0=base - self.atr * self.config['pool_height'],
                    born_bar=i - right, last_bar=i - right,
                    volume_abs=vol_abs, volume_dir=vol_dir,
                    price=close[i]
                )
                zones.append(zone)
        return zones
    
    def _merge_zones(self, zones: List[Zone]) -> List[Zone]:
        merged = []
        for zone in zones:
            is_merged = False
            for existing in merged:
                overlap = self._overlap_percentage(existing, zone)
                if overlap >= self.config['merge_overlap'] and existing.direction == zone.direction:
                    existing.top = max(existing.top, zone.top)
                    existing.bottom = min(existing.bottom, zone.bottom)
                    existing.top0 = max(existing.top0, zone.top0)
                    existing.bottom0 = min(existing.bottom0, zone.bottom0)
                    existing.volume_abs += zone.volume_abs
                    existing.volume_dir += zone.volume_dir
                    existing.confluence += 1
                    is_merged = True
                    break
            if not is_merged:
                merged.append(zone)
        return merged
    
    def _overlap_percentage(self, a: Zone, b: Zone) -> float:
        overlap = min(a.top, b.top) - max(a.bottom, b.bottom)
        min_height = min(a.height(), b.height())
        if min_height > 0 and overlap > 0:
            return overlap / min_height
        return 0.0
    
    def _calculate_score(self, zone: Zone, current_price: float) -> float:
        size_factor = min(zone.height() / (self.atr * self.config['size_norm']), 1.0) if self.atr > 0 else 0.0
        leg_len = self.config['left_bars'] + self.config['right_bars']
        v_base = self.vol_base * leg_len
        vol_factor = min(abs(zone.volume_abs) / (v_base * self.config['vol_norm']), 1.0) if v_base > 0 else 0.0
        test_factor = min(zone.tests / self.config['test_norm'], 1.0)
        conf_factor = min((zone.confluence - 1) / self.config['conf_norm'], 1.0)
        dist = abs(zone.mid() - current_price)
        prox_factor = max(1.0 - dist / (self.atr * self.config['prox_norm']), 0.0) if self.atr > 0 else 0.0
        
        weights = {'volume': 0.25, 'size': 0.20, 'test': 0.20, 'confluence': 0.20, 'proximity': 0.15}
        raw_score = (vol_factor * weights['volume'] + size_factor * weights['size'] +
                     test_factor * weights['test'] + conf_factor * weights['confluence'] +
                     prox_factor * weights['proximity'])
        return min(raw_score * 10.0, 10.0)
    
    def _filter_stale_zones(self, zones: List[Zone], current_price: float) -> List[Zone]:
        deviation = self.config['stale_deviation']
        if deviation < 0:
            return zones
        filtered = []
        for zone in zones:
            mid = zone.mid()
            if mid > 0:
                pct_dev = abs(current_price - mid) / mid * 100.0
                if pct_dev <= deviation:
                    filtered.append(zone)
        return filtered
    
    def _calculate_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> float:
        n = len(close)
        if n < 2:
            return 0.0
        length = min(n - 1, self.config['atr_length'])
        atr = 0.0
        for i in range(1, length + 1):
            tr = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
            atr += tr
        return atr / length if length > 0 else 0.0
    
    def _calculate_volume_baseline(self, volume: np.ndarray) -> float:
        n = len(volume)
        length = min(n, self.config['vol_length'])
        if length < 5:
            return 0.0
        return sum(volume[-length:]) / length
    
    def update_zones(self, high: float, low: float, close: float, volume: float, open_price: float) -> List[Zone]:
        if not self.zones:
            return self.zones
        self.bar_index += 1
        for zone in self.zones:
            if zone.phase == 2 or not zone.alive:
                continue
            touching = (zone.direction > 0 and high >= zone.bottom) or (zone.direction < 0 and low <= zone.top)
            if touching:
                h = zone.height()
                if h > 0:
                    penetration = (high - zone.bottom) / h if zone.direction > 0 else (zone.top - low) / h
                    penetration = min(penetration, 1.0)
                    if penetration > zone.penetration:
                        zone.penetration = penetration
                        if zone.direction > 0:
                            zone.bottom = min(zone.bottom0 + penetration * h, zone.top)
                        else:
                            zone.top = max(zone.top0 - penetration * h, zone.bottom)
                if not zone.inside:
                    zone.tests += 1
                zone.inside = True
                zone.last_bar = self.bar_index
                if (zone.direction > 0 and high >= zone.top) or (zone.direction < 0 and low <= zone.bottom):
                    zone.phase = 2
            else:
                zone.inside = False
            zone.score = self._calculate_score(zone, close)
        self.zones = [z for z in self.zones if z.alive]
        return self.zones
    
    def get_best_zone(self, direction: Optional[int] = None) -> Optional[Zone]:
        if not self.zones:
            return None
        candidates = [z for z in self.zones if z.phase != 2]
        if direction is not None:
            candidates = [z for z in candidates if z.direction == direction]
        if not candidates:
            return None
        return max(candidates, key=lambda z: z.score)
    
    def get_elite_zones(self) -> List[Zone]:
        return [z for z in self.zones if z.is_elite(self.config['elite_threshold'])]
    
    def get_nearest_zone(self, current_price: float, direction: int) -> Optional[Zone]:
        if not self.zones:
            return None
        candidates = [z for z in self.zones if z.phase != 2 and z.direction == direction]
        if not candidates:
            return None
        if direction > 0:
            above = [z for z in candidates if z.mid() > current_price]
            if not above:
                return None
            return min(above, key=lambda z: z.mid() - current_price)
        else:
            below = [z for z in candidates if z.mid() < current_price]
            if not below:
                return None
            return max(below, key=lambda z: current_price - z.mid())
    
    def get_supply_zones(self) -> List[Zone]:
        return [z for z in self.zones if z.is_supply() and z.phase != 2]
    
    def get_demand_zones(self) -> List[Zone]:
        return [z for z in self.zones if z.is_demand() and z.phase != 2]
    
    def get_zone_summary(self) -> Dict:
        elite = self.get_elite_zones()
        supply = self.get_supply_zones()
        demand = self.get_demand_zones()
        best = self.get_best_zone()
        return {
            'total_zones': len(self.zones),
            'elite_zones': len(elite),
            'supply_zones': len(supply),
            'demand_zones': len(demand),
            'best_score': best.score if best else 0,
            'best_direction': 'supply' if best and best.is_supply() else 'demand' if best else None,
            'has_elite': len(elite) > 0,
            'elite_details': [z.to_dict() for z in elite[:3]]
        }
    
    def clear_zones(self):
        self.zones = []
