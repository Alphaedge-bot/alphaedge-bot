"""
AlphaEdge Agent 09 – Advanced Technical
Enhanced TA with ML integration
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import math
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AdvancedTechnical:
    """Advanced Technical – Enhanced TA with ML integration"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "advanced_tech"
        self.running = False
        
        # Advanced indicators cache
        self.indicators = {}
        self.ml_predictions = {}
        self.anomalies = []
        
    async def start(self):
        """Start the advanced technical agent"""
        logger.info("Advanced Technical starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("advanced_tech_request", self.handle_advanced_tech_request)
        
        # Start analysis cycle
        asyncio.create_task(self.run_advanced_cycle())
        
        logger.info("Advanced Technical running")
        
    async def stop(self):
        """Stop the advanced technical agent"""
        self.running = False
        logger.info("Advanced Technical stopped")
        
    async def run_advanced_cycle(self):
        """Run regular advanced technical analysis"""
        while self.running:
            try:
                # Calculate advanced indicators
                await self.calculate_advanced_indicators()
                
                # Detect anomalies
                await self.detect_anomalies()
                
                # Generate ML predictions
                await self.generate_ml_predictions()
                
                # Publish advanced update
                await self.publish_advanced_update()
                
            except Exception as e:
                logger.error(f"Advanced cycle error: {e}")
                
            await asyncio.sleep(300)  # Every 5 minutes
            
    async def calculate_advanced_indicators(self):
        """Calculate advanced technical indicators"""
        # Get price data from state
        price_data = await self.state_manager.get('price_data', [])
        if len(price_data) < 50:
            return
            
        closes = [p.get('close', 0) for p in price_data[-50:]]
        
        # Bollinger Bands
        self.indicators['bollinger'] = self.calculate_bollinger_bands(closes)
        
        # Ichimoku Cloud
        self.indicators['ichimoku'] = self.calculate_ichimoku(closes)
        
        # Fibonacci Levels
        self.indicators['fibonacci'] = self.calculate_fibonacci(closes)
        
        # VWAP
        self.indicators['vwap'] = self.calculate_vwap(price_data[-50:])
        
        # Volume Profile
        self.indicators['volume_profile'] = self.calculate_volume_profile(price_data[-50:])
        
        logger.info("Advanced indicators calculated")
        
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, 
                                  std_dev: float = 2) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return {'upper': 0, 'middle': 0, 'lower': 0}
            
        middle = sum(prices[-period:]) / period
        
        variance = sum((p - middle) ** 2 for p in prices[-period:]) / period
        std = math.sqrt(variance)
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'band_width': ((upper - lower) / middle) * 100
        }
        
    def calculate_ichimoku(self, prices: List[float]) -> Dict[str, float]:
        """Calculate Ichimoku Cloud components"""
        if len(prices) < 52:
            return {'tenkan': 0, 'kijun': 0, 'senkou_a': 0, 'senkou_b': 0}
            
        # Tenkan-sen (Conversion Line) - 9 periods
        tenkan_high = max(prices[-9:])
        tenkan_low = min(prices[-9:])
        tenkan = (tenkan_high + tenkan_low) / 2
        
        # Kijun-sen (Base Line) - 26 periods
        kijun_high = max(prices[-26:])
        kijun_low = min(prices[-26:])
        kijun = (kijun_high + kijun_low) / 2
        
        # Senkou Span A - 26 periods ahead
        senkou_a = (tenkan + kijun) / 2
        
        # Senkou Span B - 52 periods
        senkou_high = max(prices[-52:])
        senkou_low = min(prices[-52:])
        senkou_b = (senkou_high + senkou_low) / 2
        
        return {
            'tenkan': tenkan,
            'kijun': kijun,
            'senkou_a': senkou_a,
            'senkou_b': senkou_b,
            'cloud_bullish': senkou_a > senkou_b
        }
        
    def calculate_fibonacci(self, prices: List[float]) -> Dict[str, float]:
        """Calculate Fibonacci retracement levels"""
        if len(prices) < 20:
            return {}
            
        high = max(prices)
        low = min(prices)
        diff = high - low
        
        return {
            'high': high,
            'low': low,
            'fib_0': high,
            'fib_236': high - (diff * 0.236),
            'fib_382': high - (diff * 0.382),
            'fib_500': high - (diff * 0.500),
            'fib_618': high - (diff * 0.618),
            'fib_786': high - (diff * 0.786),
            'fib_100': low
        }
        
    def calculate_vwap(self, data: List[Dict]) -> float:
        """Calculate Volume Weighted Average Price"""
        if not data:
            return 0
            
        total_volume = 0
        weighted_sum = 0
        
        for candle in data:
            price = candle.get('close', 0)
            volume = candle.get('volume', 0)
            weighted_sum += price * volume
            total_volume += volume
            
        return weighted_sum / total_volume if total_volume > 0 else 0
        
    def calculate_volume_profile(self, data: List[Dict]) -> Dict[str, Any]:
        """Calculate Volume Profile"""
        if len(data) < 10:
            return {}
            
        # Simple volume profile by price levels
        price_volume = {}
        
        for candle in data:
            price = round(candle.get('close', 0), 2)
            volume = candle.get('volume', 0)
            
            if price not in price_volume:
                price_volume[price] = 0
            price_volume[price] += volume
            
        # Find point of control (POC)
        if price_volume:
            poc = max(price_volume, key=price_volume.get)
            volume_range = max(price_volume.values()) - min(price_volume.values())
            
            return {
                'point_of_control': poc,
                'volume_range': volume_range,
                'levels': len(price_volume)
            }
            
        return {}
        
    async def detect_anomalies(self):
        """Detect anomalies in market data"""
        self.anomalies = []
        
        # Check for volume anomalies
        volume = await self.state_manager.get('volume_24h', 0)
        avg_volume = await self.state_manager.get('avg_volume_24h', volume)
        
        if volume > avg_volume * 3:
            self.anomalies.append({
                'type': 'volume_spike',
                'severity': 'high',
                'value': volume,
                'threshold': avg_volume * 3
            })
            
        # Check for price anomalies
        price = await self.state_manager.get('price', 0)
        avg_price = await self.state_manager.get('avg_price_30d', price)
        
        if price > avg_price * 1.2:
            self.anomalies.append({
                'type': 'price_breakout',
                'severity': 'medium',
                'value': price,
                'threshold': avg_price * 1.2
            })
            
    async def generate_ml_predictions(self):
        """Generate ML-based predictions"""
        # Simplified ML predictions
        # In production, this would use actual ML models
        
        # Get current indicators
        rsi = await self.state_manager.get('rsi', 50)
        macd = await self.state_manager.get('macd', 0)
        volume_spike = await self.state_manager.get('volume_spike', False)
        
        # Simple prediction model (weighted combination)
        prediction_score = 50  # Neutral
        
        # RSI signals
        if rsi < 30:
            prediction_score += 15  # Oversold = potential bounce
        elif rsi > 70:
            prediction_score -= 15  # Overbought = potential pullback
            
        # MACD signals
        if macd > 0:
            prediction_score += 10  # Bullish momentum
        else:
            prediction_score -= 10  # Bearish momentum
            
        # Volume signals
        if volume_spike:
            if rsi < 50:
                prediction_score += 10  # Accumulation
            else:
                prediction_score -= 10  # Distribution
                
        self.ml_predictions = {
            'prediction_score': prediction_score,
            'trend_probability': {
                'bullish': max(0, min(100, prediction_score + 20)),
                'neutral': 50,
                'bearish': max(0, min(100, 80 - prediction_score))
            },
            'confidence': random.uniform(0.5, 0.85),
            'model': 'simple_ensemble_v1'
        }
        
        logger.info(f"ML prediction: {self.ml_predictions['prediction_score']}/100")
        
    async def publish_advanced_update(self):
        """Publish advanced technical data update"""
        advanced_data = {
            'indicators': self.indicators,
            'anomalies': self.anomalies,
            'ml_predictions': self.ml_predictions,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="advanced_tech_data_update",
            data=advanced_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def handle_advanced_tech_request(self, event: Event):
        """Handle advanced technical data requests"""
        if not self.running:
            return
            
        advanced_data = {
            'indicators': self.indicators,
            'anomalies': self.anomalies,
            'ml_predictions': self.ml_predictions,
            'timestamp': datetime.now().isoformat()
        }
        
        response = Event(
            event_type="advanced_tech_response",
            data=advanced_data,
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get advanced technical status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'indicators_calculated': len(self.indicators),
            'anomalies_detected': len(self.anomalies),
            'ml_predictions_ready': bool(self.ml_predictions),
            'timestamp': datetime.now().isoformat()
        }
