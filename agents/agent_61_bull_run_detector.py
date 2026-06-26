"""
AlphaEdge Agent 61 – Bull Run Detector
Parabolic trend, alt season, new ATH breakout, social FOMO, confidence 30-95%
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class BullRunDetector:
    """Bull Run Detector – Detects bull run conditions and alt seasons"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "bull_run_detector"
        self.running = False
        
        # Detection state
        self.bull_run_signals = []
        self.alt_season_score = 0
        self.parabolic_trends = []
        
        # Confidence levels
        self.bull_run_confidence = 30  # 30-95%
        self.alt_season_confidence = 30
        
        # Configuration
        self.config = {
            'bull_run_threshold': 60,
            'alt_season_threshold': 50,
            'parabolic_threshold': 1.5,  # 50% gain in short period
            'fomo_threshold': 0.7,
            'ath_breakout_threshold': 0.05  # 5% above ATH
        }
        
    async def start(self):
        """Start the bull run detector"""
        logger.info("Bull Run Detector starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("bull_run_check", self.handle_bull_run_check)
        await self.event_bus.subscribe("alt_season_check", self.handle_alt_season_check)
        await self.event_bus.subscribe("parabolic_trend_check", self.handle_parabolic_check)
        
        # Start detection cycle
        asyncio.create_task(self.run_detection_cycle())
        
        logger.info("Bull Run Detector running")
        
    async def stop(self):
        """Stop the bull run detector"""
        self.running = False
        logger.info("Bull Run Detector stopped")
        
    async def run_detection_cycle(self):
        """Run regular detection cycle"""
        while self.running:
            try:
                # Check for bull run
                await self.detect_bull_run()
                
                # Check for alt season
                await self.detect_alt_season()
                
                # Check for parabolic trends
                await self.detect_parabolic_trends()
                
                # Check for FOMO
                await self.detect_fomo()
                
                # Check for new ATH
                await self.detect_new_ath()
                
                # Publish detector update
                await self.publish_detector_update()
                
            except Exception as e:
                logger.error(f"Detection cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def handle_bull_run_check(self, event: Event):
        """Handle bull run check requests"""
        if not self.running:
            return
            
        response = Event(
            event_type="bull_run_check_response",
            data={
                'is_bull_run': self.bull_run_confidence > self.config['bull_run_threshold'],
                'confidence': self.bull_run_confidence,
                'signals': self.bull_run_signals[-5:],
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_alt_season_check(self, event: Event):
        """Handle alt season check requests"""
        if not self.running:
            return
            
        response = Event(
            event_type="alt_season_check_response",
            data={
                'is_alt_season': self.alt_season_confidence > self.config['alt_season_threshold'],
                'confidence': self.alt_season_confidence,
                'score': self.alt_season_score,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_parabolic_check(self, event: Event):
        """Handle parabolic trend check requests"""
        if not self.running:
            return
            
        response = Event(
            event_type="parabolic_check_response",
            data={
                'parabolic_trends': self.parabolic_trends,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def detect_bull_run(self):
        """Detect bull run conditions"""
        signals = []
        confidence = 30  # Base confidence
        
        # Check price trends
        price_trend = await self.state_manager.get('price_trend', 'neutral')
        if price_trend == 'bullish':
            confidence += 20
            signals.append('bullish_price_trend')
            
        # Check volume
        volume_trend = await self.state_manager.get('volume_trend', 'stable')
        if volume_trend == 'increasing':
            confidence += 15
            signals.append('increasing_volume')
            
        # Check market sentiment
        sentiment = await self.state_manager.get('sentiment_score', 50)
        if sentiment > 70:
            confidence += 15
            signals.append('high_sentiment')
            
        # Check macro conditions
        macro_score = await self.state_manager.get('macro_score', 50)
        if macro_score > 60:
            confidence += 10
            signals.append('favorable_macro')
            
        # Check on-chain metrics
        whale_activity = await self.state_manager.get('whale_activity', 'neutral')
        if whale_activity == 'accumulating':
            confidence += 10
            signals.append('whale_accumulation')
            
        # Check social sentiment
        social_sentiment = await self.state_manager.get('social_sentiment', 50)
        if social_sentiment > 60:
            confidence += 10
            signals.append('positive_social')
            
        # Add some randomness
        confidence += random.uniform(-5, 5)
        confidence = max(30, min(95, confidence))
        
        self.bull_run_confidence = confidence
        self.bull_run_signals.append({
            'signals': signals,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep last 100 signals
        if len(self.bull_run_signals) > 100:
            self.bull_run_signals = self.bull_run_signals[-100:]
            
        # Store in state
        await self.state_manager.set('bull_run_confidence', confidence)
        await self.state_manager.set('bull_run_signals', signals)
        
    async def detect_alt_season(self):
        """Detect alt season conditions"""
        # Track alt coin performance relative to BTC
        btc_performance = await self.state_manager.get('btc_performance', 0)
        alt_performance = await self.state_manager.get('alt_performance', 0)
        
        # Calculate alt season score
        if alt_performance > btc_performance * 1.2:
            self.alt_season_score += 10
        elif alt_performance > btc_performance * 1.1:
            self.alt_season_score += 5
            
        # Check alt coin volume
        alt_volume = await self.state_manager.get('alt_volume', 0)
        btc_volume = await self.state_manager.get('btc_volume', 0)
        
        if alt_volume > btc_volume * 0.5:
            self.alt_season_score += 10
            
        # Check alt coin breadth
        alt_breadth = await self.state_manager.get('alt_breadth', 0)
        if alt_breadth > 0.6:  # 60% of alts positive
            self.alt_season_score += 15
            
        # Calculate confidence
        confidence = max(30, min(95, self.alt_season_score + 30))
        self.alt_season_confidence = confidence
        
        # Store in state
        await self.state_manager.set('alt_season_confidence', confidence)
        await self.state_manager.set('alt_season_score', self.alt_season_score)
        
    async def detect_parabolic_trends(self):
        """Detect parabolic price trends"""
        # Get recent price data
        prices = await self.state_manager.get('price_history', [])
        
        if len(prices) < 20:
            return
            
        # Check for parabolic moves
        recent_prices = prices[-20:]
        gains = []
        
        for i in range(1, len(recent_prices)):
            if recent_prices[i-1] > 0:
                gain = (recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
                gains.append(gain)
                
        if gains:
            avg_gain = sum(gains) / len(gains)
            
            if avg_gain > 0.05:  # 5% average gain
                self.parabolic_trends.append({
                    'avg_gain': avg_gain,
                    'duration': len(gains),
                    'timestamp': datetime.now().isoformat()
                })
                
        # Keep last 10 trends
        if len(self.parabolic_trends) > 10:
            self.parabolic_trends = self.parabolic_trends[-10:]
            
    async def detect_fomo(self):
        """Detect FOMO (Fear Of Missing Out)"""
        # Check social media activity
        social_volume = await self.state_manager.get('social_volume', 0)
        social_volume_avg = await self.state_manager.get('social_volume_avg', 0)
        
        if social_volume_avg > 0:
            fomo_score = social_volume / social_volume_avg
        else:
            fomo_score = 1
            
        # Check search trends
        search_trends = await self.state_manager.get('search_trends', 0)
        search_avg = await self.state_manager.get('search_avg', 0)
        
        if search_avg > 0:
            fomo_score += search_trends / search_avg
        else:
            fomo_score += 1
            
        fomo_score = min(1, fomo_score / 2)
        
        # Store in state
        await self.state_manager.set('fomo_score', fomo_score)
        
    async def detect_new_ath(self):
        """Detect new all-time-high breakouts"""
        current_price = await self.state_manager.get('price', 0)
        ath_price = await self.state_manager.get('ath_price', current_price)
        
        if ath_price > 0:
            ath_breakout = (current_price - ath_price) / ath_price
        else:
            ath_breakout = 0
            
        if ath_breakout > self.config['ath_breakout_threshold']:
            await self.state_manager.set('ath_breakout', True)
            await self.state_manager.set('ath_breakout_pct', ath_breakout * 100)
            
        # Store in state
        await self.state_manager.set('ath_breakout', False)
        
    async def publish_detector_update(self):
        """Publish detector data update"""
        detector_data = {
            'bull_run_confidence': self.bull_run_confidence,
            'alt_season_confidence': self.alt_season_confidence,
            'alt_season_score': self.alt_season_score,
            'parabolic_trends': self.parabolic_trends[-3:],
            'bull_run_signals': self.bull_run_signals[-3:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="bull_run_detector_update",
            data=detector_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get bull run detector status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'bull_run_confidence': self.bull_run_confidence,
            'alt_season_confidence': self.alt_season_confidence,
            'alt_season_score': self.alt_season_score,
            'parabolic_trends': len(self.parabolic_trends),
            'timestamp': datetime.now().isoformat()
        }
