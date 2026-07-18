# core/volume_profile.py
# AlphaEdge V13.0.7 – Volume Profile Module
# Item 12: Volume Profile Detection

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class VolumeProfileLevel:
    """Volume Profile level data"""
    price: float
    volume: float
    is_poc: bool = False
    is_vah: bool = False
    is_val: bool = False
    timeframe: str = "1H"
    reliability: float = 0.0


class VolumeProfile:
    """
    Volume Profile calculator for multiple timeframes
    Item 12: Volume Profile Detection
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or self.default_config()
        self.profiles = {}
        
    def default_config(self) -> Dict:
        return {
            'enabled': True,
            'bins': 50,
            'value_area_pct': 0.70,
            'min_volume_threshold': 1000,
            'timeframes': ['15M', '1H', '4H'],
            'lookback_bars': 200
        }
    
    def calculate_profile(self, high: np.ndarray, low: np.ndarray,
                         close: np.ndarray, volume: np.ndarray,
                         timeframe: str = "1H") -> Dict:
        """
        Calculate Volume Profile for a single timeframe
        """
        if not self.config.get('enabled', True):
            return {}
        
        # Use only the last N bars
        n = min(len(close), self.config['lookback_bars'])
        high = high[-n:]
        low = low[-n:]
        close = close[-n:]
        volume = volume[-n:]
        
        # Determine price range
        price_high = np.max(high)
        price_low = np.min(low)
        price_range = price_high - price_low
        
        if price_range <= 0:
            return {}
        
        # Create price bins
        bin_size = price_range / self.config['bins']
        bins = np.arange(price_low, price_high + bin_size, bin_size)
        
        # Assign volume to bins
        volume_by_price = np.zeros(len(bins) - 1)
        
        for i in range(len(high)):
            # Determine which bin this candle belongs to
            mid_price = (high[i] + low[i]) / 2
            bin_idx = int((mid_price - price_low) / bin_size)
            
            if 0 <= bin_idx < len(volume_by_price):
                volume_by_price[bin_idx] += volume[i]
        
        # Find POC (Point of Control)
        poc_idx = np.argmax(volume_by_price)
        poc_price = (bins[poc_idx] + bins[poc_idx + 1]) / 2
        poc_volume = volume_by_price[poc_idx]
        
        # Calculate Value Area (70% of volume)
        total_volume = np.sum(volume_by_price)
        target_volume = total_volume * self.config['value_area_pct']
        
        # Sort by volume descending
        sorted_indices = np.argsort(volume_by_price)[::-1]
        
        cumulative_volume = 0
        value_area_indices = []
        
        for idx in sorted_indices:
            cumulative_volume += volume_by_price[idx]
            value_area_indices.append(idx)
            if cumulative_volume >= target_volume:
                break
        
        # Find VAH and VAL
        va_high_idx = max(value_area_indices)
        va_low_idx = min(value_area_indices)
        
        vah_price = (bins[va_high_idx] + bins[va_high_idx + 1]) / 2
        val_price = (bins[va_low_idx] + bins[va_low_idx + 1]) / 2
        
        # Calculate reliability based on volume concentration
        volume_concentration = poc_volume / total_volume if total_volume > 0 else 0
        reliability = min(volume_concentration * 10, 1.0)
        
        return {
            'poc': poc_price,
            'poc_volume': poc_volume,
            'vah': vah_price,
            'val': val_price,
            'value_area_pct': self.config['value_area_pct'],
            'reliability': reliability,
            'total_volume': total_volume,
            'timeframe': timeframe,
            'bins': bins,
            'volume_by_price': volume_by_price.tolist()
        }
    
    def analyze_multi_timeframe(self, price_data: Dict) -> Dict:
        """
        Analyze Volume Profile across multiple timeframes
        """
        result = {}
        
        for tf in self.config['timeframes']:
            # Get data for this timeframe
            data = price_data.get(tf, {})
            if not data:
                continue
            
            high = data.get('high', [])
            low = data.get('low', [])
            close = data.get('close', [])
            volume = data.get('volume', [])
            
            if len(high) < 20:
                continue
            
            profile = self.calculate_profile(
                np.array(high),
                np.array(low),
                np.array(close),
                np.array(volume),
                tf
            )
            
            if profile:
                result[tf] = profile
        
        # Find confluence across timeframes
        result['confluence'] = self._find_confluence(result)
        
        return result
    
    def _find_confluence(self, profiles: Dict) -> Dict:
        """
        Find price levels that appear across multiple timeframes
        """
        levels = {}
        
        for tf, profile in profiles.items():
            for level_type in ['poc', 'vah', 'val']:
                price = profile.get(level_type, 0)
                if price > 0:
                    if price not in levels:
                        levels[price] = {
                            'timeframes': [],
                            'types': []
                        }
                    levels[price]['timeframes'].append(tf)
                    levels[price]['types'].append(level_type)
        
        # Filter for levels appearing in 2+ timeframes
        confluence = {}
        for price, data in levels.items():
            if len(data['timeframes']) >= 2:
                confluence[price] = {
                    'strength': len(data['timeframes']) * 2 + len(set(data['types'])),
                    'timeframes': data['timeframes'],
                    'types': data['types']
                }
        
        return confluence
    
    def get_tps_adjustment(self, profiles: Dict, current_price: float) -> float:
        """
        Calculate TPS adjustment from Volume Profile
        """
        adjustment = 0.0
        
        # Check if current price is near POC of any timeframe
        for tf, profile in profiles.items():
            if tf == 'confluence':
                continue
                
            poc = profile.get('poc', 0)
            if poc > 0:
                distance_pct = abs(current_price - poc) / current_price * 100
                if distance_pct < 2.0:
                    reliability = profile.get('reliability', 0.5)
                    adjustment += 3.0 * reliability
        
        # Check for confluence
        confluence = profiles.get('confluence', {})
        for price, data in confluence.items():
            if abs(current_price - price) / current_price * 100 < 1.0:
                strength = data.get('strength', 0)
                adjustment += min(strength / 2, 5.0)
        
        return min(adjustment, 10.0)
    
    def get_support_resistance(self, profiles: Dict) -> Dict:
        """
        Extract support/resistance levels from Volume Profile
        """
        levels = {
            'support': [],
            'resistance': []
        }
        
        current_price = 0
        for tf, profile in profiles.items():
            if tf == 'confluence':
                continue
            
            poc = profile.get('poc', 0)
            vah = profile.get('vah', 0)
            val = profile.get('val', 0)
            
            # Determine if level is support or resistance
            if current_price > 0:
                if poc < current_price:
                    levels['support'].append({'price': poc, 'timeframe': tf, 'type': 'poc'})
                else:
                    levels['resistance'].append({'price': poc, 'timeframe': tf, 'type': 'poc'})
                
                if val < current_price:
                    levels['support'].append({'price': val, 'timeframe': tf, 'type': 'val'})
                else:
                    levels['resistance'].append({'price': val, 'timeframe': tf, 'type': 'val'})
                
                if vah < current_price:
                    levels['support'].append({'price': vah, 'timeframe': tf, 'type': 'vah'})
                else:
                    levels['resistance'].append({'price': vah, 'timeframe': tf, 'type': 'vah'})
        
        # Sort and deduplicate
        for key in levels:
            levels[key] = sorted(levels[key], key=lambda x: x['price'])
        
        return levels
