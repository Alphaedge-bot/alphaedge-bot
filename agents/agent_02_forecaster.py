"""
AlphaEdge Agent 02 – Strategic Forecaster
Long-term scenario planning, macro trend analysis, regime prediction
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class StrategicForecaster:
    """Strategic Forecaster – Long-term scenario planning and regime prediction"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "forecaster"
        self.running = False
        self.forecast_history = []
        self.current_regime = "neutral"
        self.regime_confidence = 0.0
        
        # Regime detection thresholds
        self.regime_thresholds = {
            'bull': 0.7,
            'alt': 0.6,
            'accumulation': 0.5,
            'neutral': 0.4,
            'bear': 0.3,
            'crash': 0.1
        }
        
    async def start(self):
        """Start the forecaster agent"""
        logger.info("Strategic Forecaster starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("forecast_request", self.handle_forecast_request)
        
        # Start regular forecasting
        asyncio.create_task(self.run_forecasting_cycle())
        
        logger.info("Strategic Forecaster running")
        
    async def stop(self):
        """Stop the forecaster agent"""
        self.running = False
        logger.info("Strategic Forecaster stopped")
        
    async def run_forecasting_cycle(self):
        """Run regular forecasting cycles"""
        while self.running:
            try:
                # Update market regime
                await self.update_regime()
                
                # Generate forecasts
                await self.generate_forecasts()
                
                # Publish regime update
                await self.publish_regime_update()
                
            except Exception as e:
                logger.error(f"Forecasting cycle error: {e}")
                
            await asyncio.sleep(300)  # Every 5 minutes
            
    async def update_regime(self):
        """Update current market regime"""
        # Get market data
        macro_score = await self.state_manager.get('fed_liquidity_score', 50)
        dxy_trend = await self.state_manager.get('dxy_trend', 'neutral')
        btc_trend = await self.state_manager.get('btc_trend', 'neutral')
        
        # Calculate regime score
        regime_scores = {
            'bull': self.calculate_bull_score(macro_score, dxy_trend, btc_trend),
            'alt': self.calculate_alt_score(macro_score, dxy_trend, btc_trend),
            'accumulation': self.calculate_accumulation_score(macro_score, dxy_trend, btc_trend),
            'neutral': self.calculate_neutral_score(macro_score, dxy_trend, btc_trend),
            'bear': self.calculate_bear_score(macro_score, dxy_trend, btc_trend),
            'crash': self.calculate_crash_score(macro_score, dxy_trend, btc_trend)
        }
        
        # Find highest confidence regime
        self.current_regime = max(regime_scores, key=regime_scores.get)
        self.regime_confidence = regime_scores[self.current_regime]
        
        logger.info(f"Regime update: {self.current_regime} (confidence: {self.regime_confidence:.2f})")
        
    def calculate_bull_score(self, macro: float, dxy: str, btc: str) -> float:
        """Calculate bull regime score"""
        score = 0.0
        
        # Macro expansion
        if macro >= 80:
            score += 0.4
        elif macro >= 60:
            score += 0.2
            
        # DXY falling
        if dxy == 'falling':
            score += 0.3
            
        # BTC bullish
        if btc == 'bullish':
            score += 0.3
            
        return min(score, 1.0)
        
    def calculate_alt_score(self, macro: float, dxy: str, btc: str) -> float:
        """Calculate alt season regime score"""
        score = 0.0
        
        # Macro moderate
        if 40 <= macro <= 70:
            score += 0.3
            
        # DXY neutral
        if dxy == 'neutral':
            score += 0.2
            
        # BTC consolidating
        if btc == 'neutral':
            score += 0.3
            
        return min(score, 1.0)
        
    def calculate_accumulation_score(self, macro: float, dxy: str, btc: str) -> float:
        """Calculate accumulation regime score"""
        score = 0.0
        
        # Macro recovering
        if 30 <= macro <= 50:
            score += 0.3
            
        # DXY high
        if dxy == 'high':
            score += 0.2
            
        # BTC bottoming
        if btc == 'bearish':
            score += 0.3
            
        return min(score, 1.0)
        
    def calculate_neutral_score(self, macro: float, dxy: str, btc: str) -> float:
        """Calculate neutral regime score"""
        score = 0.3  # Baseline
        
        # Macro neutral
        if 40 <= macro <= 60:
            score += 0.2
            
        # DXY stable
        if dxy == 'neutral':
            score += 0.2
            
        # BTC range-bound
        if btc == 'neutral':
            score += 0.3
            
        return min(score, 1.0)
        
    def calculate_bear_score(self, macro: float, dxy: str, btc: str) -> float:
        """Calculate bear regime score"""
        score = 0.0
        
        # Macro contraction
        if macro <= 30:
            score += 0.4
        elif macro <= 40:
            score += 0.2
            
        # DXY rising
        if dxy == 'rising':
            score += 0.3
            
        # BTC bearish
        if btc == 'bearish':
            score += 0.3
            
        return min(score, 1.0)
        
    def calculate_crash_score(self, macro: float, dxy: str, btc: str) -> float:
        """Calculate crash regime score"""
        score = 0.0
        
        # Macro crash
        if macro <= 20:
            score += 0.5
            
        # DXY spiking
        if dxy == 'spiking':
            score += 0.3
            
        # BTC crashing
        if btc == 'crashing':
            score += 0.2
            
        return min(score, 1.0)
        
    async def generate_forecasts(self):
        """Generate long-term forecasts"""
        forecast = {
            'timestamp': datetime.now().isoformat(),
            'regime': self.current_regime,
            'confidence': self.regime_confidence,
            'outlook': self.generate_outlook(),
            'scenarios': self.generate_scenarios(),
            'risk_factors': self.identify_risk_factors()
        }
        
        self.forecast_history.append(forecast)
        if len(self.forecast_history) > 100:
            self.forecast_history.pop(0)
            
        # Store latest forecast
        await self.state_manager.set('latest_forecast', forecast)
        
    def generate_outlook(self) -> str:
        """Generate outlook based on current regime"""
        outlooks = {
            'bull': "Bullish outlook. Expect continued upward momentum.",
            'alt': "Alt season potential. Rotate to mid-cap assets.",
            'accumulation': "Accumulation phase. Build positions gradually.",
            'neutral': "Neutral outlook. Wait for clear direction.",
            'bear': "Bearish outlook. Capital preservation priority.",
            'crash': "CRASH RISK. Immediate defense positioning."
        }
        return outlooks.get(self.current_regime, "Outlook uncertain")
        
    def generate_scenarios(self) -> List[Dict[str, Any]]:
        """Generate scenario analysis"""
        scenarios = []
        
        # Bull scenario
        if self.current_regime in ['bull', 'alt']:
            scenarios.append({
                'name': 'Bull Continuation',
                'probability': 0.6,
                'description': 'Momentum continues, new highs expected'
            })
            
        # Base scenario
        scenarios.append({
            'name': 'Base Case',
            'probability': 0.3,
            'description': 'Current trends continue'
        })
        
        # Bear scenario
        if self.current_regime in ['bear', 'crash']:
            scenarios.append({
                'name': 'Bear Intensification',
                'probability': 0.5,
                'description': 'Further downside expected'
            })
        else:
            scenarios.append({
                'name': 'Bear Risk',
                'probability': 0.1,
                'description': 'Downside risk from macro factors'
            })
            
        return scenarios
        
    def identify_risk_factors(self) -> List[Dict[str, Any]]:
        """Identify potential risk factors"""
        risks = []
        
        # Fed liquidity
        macro_score = self.state_manager.get('fed_liquidity_score', 50)
        if macro_score < 40:
            risks.append({
                'factor': 'Fed Liquidity Contraction',
                'severity': 'high',
                'probability': 0.7
            })
            
        # DXY
        dxy_trend = self.state_manager.get('dxy_trend', 'neutral')
        if dxy_trend == 'rising':
            risks.append({
                'factor': 'Strong USD',
                'severity': 'medium',
                'probability': 0.6
            })
            
        # Market sentiment
        sentiment = self.state_manager.get('sentiment_score', 50)
        if sentiment < 30:
            risks.append({
                'factor': 'Extreme Fear',
                'severity': 'medium',
                'probability': 0.5
            })
            
        return risks
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        if not self.running:
            return
            
        # Store market data
        await self.state_manager.update('market_data', event.data)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        if not self.running:
            return
            
        # Store macro data
        await self.state_manager.update('macro_data', event.data)
        
    async def handle_forecast_request(self, event: Event):
        """Handle forecast requests"""
        if not self.running:
            return
            
        forecast = await self.state_manager.get('latest_forecast', {})
        
        response = Event(
            event_type="forecast_response",
            data=forecast,
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get forecaster status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'current_regime': self.current_regime,
            'regime_confidence': self.regime_confidence,
            'forecast_count': len(self.forecast_history),
            'timestamp': datetime.now().isoformat()
            }
