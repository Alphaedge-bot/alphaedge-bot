"""
AlphaEdge Agent 10 – Cross-Validation Oracle
Validates signals across multiple data sources
Multi-oracle price validation integrated
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import statistics

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CrossValidationOracle:
    """Cross-Validation Oracle – Validates signals across multiple data sources"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "cross_validation"
        self.running = False
        
        # Validation cache
        self.validation_results = {}
        self.signal_history = []
        self.confidence_scores = {}
        
    async def start(self):
        """Start the cross-validation oracle"""
        logger.info("Cross-Validation Oracle starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("validation_request", self.handle_validation_request)
        await self.event_bus.subscribe("signal_generated", self.handle_signal)
        
        # Start validation cycle
        asyncio.create_task(self.run_validation_cycle())
        
        logger.info("Cross-Validation Oracle running")
        
    async def stop(self):
        """Stop the cross-validation oracle"""
        self.running = False
        logger.info("Cross-Validation Oracle stopped")
        
    async def run_validation_cycle(self):
        """Run regular validation cycle"""
        while self.running:
            try:
                # Validate current signals
                await self.validate_signals()
                
                # Calculate confidence scores
                await self.calculate_confidence_scores()
                
                # Publish validation update
                await self.publish_validation_update()
                
            except Exception as e:
                logger.error(f"Validation cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def handle_signal(self, event: Event):
        """Handle signal generation events"""
        if not self.running:
            return
            
        signal = event.data
        signal_id = signal.get('id')
        
        self.signal_history.append({
            'id': signal_id,
            'signal': signal,
            'timestamp': datetime.now().isoformat(),
            'validated': False
        })
        
        # Keep last 1000 signals
        if len(self.signal_history) > 1000:
            self.signal_history.pop(0)
            
    async def validate_signals(self):
        """Validate signals against multiple data sources"""
        if not self.signal_history:
            return
            
        # Get data from different sources
        technical_data = await self.state_manager.get('technical_indicators', {})
        sentiment_data = await self.state_manager.get('sentiment_score', 50)
        onchain_data = await self.state_manager.get('onchain_metrics', {})
        macro_data = await self.state_manager.get('macro_score', 50)
        
        for entry in self.signal_history[-10:]:  # Validate last 10 signals
            signal = entry['signal']
            signal_type = signal.get('type', 'unknown')
            
            # Validate based on signal type
            validation = self.validate_signal(
                signal_type, 
                technical_data,
                sentiment_data,
                onchain_data,
                macro_data
            )
            
            entry['validated'] = True
            entry['validation_result'] = validation
            
    def validate_signal(self, signal_type: str, technical: Dict, 
                        sentiment: float, onchain: Dict, macro: float) -> Dict[str, Any]:
        """Validate a signal against multiple data sources"""
        score = 0
        max_score = 0
        validations = []
        
        # Technical validation
        tech_score = self.validate_technical(signal_type, technical)
        score += tech_score
        max_score += 33
        
        # Sentiment validation
        sent_score = self.validate_sentiment(signal_type, sentiment)
        score += sent_score
        max_score += 33
        
        # Macro validation
        macro_score = self.validate_macro(signal_type, macro)
        score += macro_score
        max_score += 34
        
        confidence = (score / max_score) * 100 if max_score > 0 else 0
        
        return {
            'score': score,
            'max_score': max_score,
            'confidence': confidence,
            'is_valid': confidence >= 60,
            'components': {
                'technical': tech_score,
                'sentiment': sent_score,
                'macro': macro_score
            }
        }
        
    def validate_technical(self, signal_type: str, technical: Dict) -> float:
        """Validate signal against technical indicators"""
        score = 0
        
        if signal_type == 'entry':
            rsi = technical.get('rsi', 50)
            macd = technical.get('macd', {}).get('macd', 0)
            
            if 60 <= rsi <= 75:
                score += 15
            if macd > 0:
                score += 18
                
        elif signal_type == 'exit':
            rsi = technical.get('rsi', 50)
            macd = technical.get('macd', {}).get('macd', 0)
            
            if rsi > 70 or rsi < 30:
                score += 15
            if macd < 0:
                score += 18
                
        return score
        
    def validate_sentiment(self, signal_type: str, sentiment: float) -> float:
        """Validate signal against sentiment data"""
        score = 0
        
        if signal_type == 'entry':
            if sentiment >= 70:
                score += 33
            elif sentiment >= 60:
                score += 20
                
        elif signal_type == 'exit':
            if sentiment <= 30:
                score += 33
            elif sentiment <= 40:
                score += 20
                
        return score
        
    def validate_macro(self, signal_type: str, macro: float) -> float:
        """Validate signal against macro conditions"""
        score = 0
        
        if signal_type == 'entry':
            if macro >= 60:
                score += 34
            elif macro >= 50:
                score += 20
                
        elif signal_type == 'exit':
            if macro <= 40:
                score += 34
            elif macro <= 50:
                score += 20
                
        return score
        
    async def calculate_confidence_scores(self):
        """Calculate confidence scores for all signals"""
        for entry in self.signal_history[-20:]:
            if entry.get('validated'):
                validation = entry.get('validation_result', {})
                confidence = validation.get('confidence', 0)
                
                self.confidence_scores[entry['id']] = confidence
                
    async def publish_validation_update(self):
        """Publish validation data update"""
        validation_data = {
            'signal_count': len(self.signal_history),
            'validated_count': len([s for s in self.signal_history if s.get('validated')]),
            'average_confidence': self.calculate_average_confidence(),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="validation_data_update",
            data=validation_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    def calculate_average_confidence(self) -> float:
        """Calculate average confidence of validated signals"""
        confidences = [v for v in self.confidence_scores.values() if v > 0]
        if confidences:
            return statistics.mean(confidences)
        return 0
        
    async def handle_validation_request(self, event: Event):
        """Handle validation requests"""
        if not self.running:
            return
            
        signal_id = event.data.get('signal_id')
        validation = None
        
        for entry in self.signal_history:
            if entry['id'] == signal_id:
                validation = entry.get('validation_result')
                break
                
        response = Event(
            event_type="validation_response",
            data={
                'signal_id': signal_id,
                'validation': validation,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get cross-validation status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'signal_count': len(self.signal_history),
            'validated_count': len([s for s in self.signal_history if s.get('validated')]),
            'average_confidence': self.calculate_average_confidence(),
            'timestamp': datetime.now().isoformat()
        }
