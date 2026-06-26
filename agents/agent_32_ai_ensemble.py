"""
AlphaEdge Agent 32 – Advanced AI/ML Ensemble
LSTM + XGBoost + Transformer + Reinforcement Learning
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random
import math

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AIEnsemble:
    """AI Ensemble – Multiple ML models for price prediction and trading signals"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "ai_ensemble"
        self.running = False
        
        # Model state
        self.models = {
            'lstm': {'weight': 0.3, 'prediction': 0, 'confidence': 0},
            'xgboost': {'weight': 0.25, 'prediction': 0, 'confidence': 0},
            'transformer': {'weight': 0.3, 'prediction': 0, 'confidence': 0},
            'reinforcement': {'weight': 0.15, 'prediction': 0, 'confidence': 0}
        }
        
        # Ensemble state
        self.ensemble_predictions = []
        self.training_data = []
        self.performance_history = []
        
    async def start(self):
        """Start the AI ensemble"""
        logger.info("AI Ensemble starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("ensemble_request", self.handle_ensemble_request)
        await self.event_bus.subscribe("training_data_update", self.handle_training_data)
        await self.event_bus.subscribe("model_update", self.handle_model_update)
        
        # Start ensemble cycle
        asyncio.create_task(self.run_ensemble_cycle())
        
        logger.info("AI Ensemble running")
        
    async def stop(self):
        """Stop the AI ensemble"""
        self.running = False
        logger.info("AI Ensemble stopped")
        
    async def run_ensemble_cycle(self):
        """Run regular ensemble prediction cycle"""
        while self.running:
            try:
                # Get latest data
                data = await self.get_latest_data()
                
                if data:
                    # Run all models
                    await self.run_models(data)
                    
                    # Generate ensemble prediction
                    await self.generate_ensemble_prediction()
                    
                    # Publish ensemble update
                    await self.publish_ensemble_update()
                    
            except Exception as e:
                logger.error(f"Ensemble cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def handle_ensemble_request(self, event: Event):
        """Handle ensemble prediction requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        data = event.data.get('data', {})
        
        logger.info(f"Ensemble request: {request_id}")
        
        # Run ensemble prediction
        prediction = await self.predict(data)
        
        # Send response
        response = Event(
            event_type="ensemble_response",
            data={
                'request_id': request_id,
                'prediction': prediction,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def get_latest_data(self) -> Dict:
        """Get latest market data for prediction"""
        # In production, fetch from state manager
        # For now, simulate data
        return {
            'price': random.uniform(100, 200),
            'volume': random.uniform(1000, 10000),
            'rsi': random.uniform(30, 70),
            'macd': random.uniform(-5, 5),
            'volatility': random.uniform(0.1, 0.5)
        }
        
    async def run_models(self, data: Dict):
        """Run all models on the data"""
        # LSTM prediction
        self.models['lstm']['prediction'] = await self.run_lstm(data)
        self.models['lstm']['confidence'] = random.uniform(0.6, 0.9)
        
        # XGBoost prediction
        self.models['xgboost']['prediction'] = await self.run_xgboost(data)
        self.models['xgboost']['confidence'] = random.uniform(0.5, 0.85)
        
        # Transformer prediction
        self.models['transformer']['prediction'] = await self.run_transformer(data)
        self.models['transformer']['confidence'] = random.uniform(0.6, 0.95)
        
        # Reinforcement learning prediction
        self.models['reinforcement']['prediction'] = await self.run_reinforcement(data)
        self.models['reinforcement']['confidence'] = random.uniform(0.4, 0.8)
        
    async def run_lstm(self, data: Dict) -> float:
        """Run LSTM model prediction"""
        # Simulate LSTM prediction
        # In production, load actual LSTM model
        price = data.get('price', 100)
        return price * (1 + random.uniform(-0.02, 0.02))
        
    async def run_xgboost(self, data: Dict) -> float:
        """Run XGBoost model prediction"""
        # Simulate XGBoost prediction
        price = data.get('price', 100)
        return price * (1 + random.uniform(-0.015, 0.015))
        
    async def run_transformer(self, data: Dict) -> float:
        """Run Transformer model prediction"""
        # Simulate Transformer prediction
        price = data.get('price', 100)
        return price * (1 + random.uniform(-0.01, 0.01))
        
    async def run_reinforcement(self, data: Dict) -> float:
        """Run Reinforcement Learning model prediction"""
        # Simulate RL prediction
        price = data.get('price', 100)
        return price * (1 + random.uniform(-0.03, 0.03))
        
    async def generate_ensemble_prediction(self):
        """Generate ensemble prediction from all models"""
        # Weighted average
        total_weight = 0
        weighted_sum = 0
        
        for model_name, model_data in self.models.items():
            weight = model_data['weight']
            prediction = model_data['prediction']
            confidence = model_data['confidence']
            
            weighted_sum += prediction * weight * confidence
            total_weight += weight * confidence
            
        if total_weight > 0:
            ensemble_prediction = weighted_sum / total_weight
        else:
            ensemble_prediction = 0
            
        # Calculate confidence
        confidence_scores = [m['confidence'] for m in self.models.values()]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        # Store prediction
        self.ensemble_predictions.append({
            'timestamp': datetime.now().isoformat(),
            'prediction': ensemble_prediction,
            'confidence': avg_confidence,
            'model_predictions': {m: self.models[m]['prediction'] for m in self.models}
        })
        
        # Keep last 1000 predictions
        if len(self.ensemble_predictions) > 1000:
            self.ensemble_predictions.pop(0)
            
        # Store in state
        await self.state_manager.set('ensemble_prediction', {
            'price': ensemble_prediction,
            'confidence': avg_confidence,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Ensemble prediction: {ensemble_prediction:.2f} (confidence: {avg_confidence:.2f})")
        
    async def predict(self, data: Dict) -> Dict:
        """Make a prediction using the ensemble"""
        # Run models on provided data
        await self.run_models(data)
        
        # Generate ensemble prediction
        total_weight = 0
        weighted_sum = 0
        
        for model_name, model_data in self.models.items():
            weight = model_data['weight']
            prediction = model_data['prediction']
            confidence = model_data['confidence']
            
            weighted_sum += prediction * weight * confidence
            total_weight += weight * confidence
            
        if total_weight > 0:
            prediction = weighted_sum / total_weight
        else:
            prediction = 0
            
        confidence_scores = [m['confidence'] for m in self.models.values()]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        return {
            'prediction': prediction,
            'confidence': avg_confidence,
            'model_predictions': {m: self.models[m]['prediction'] for m in self.models}
        }
        
    async def handle_training_data(self, event: Event):
        """Handle training data updates"""
        if not self.running:
            return
            
        data = event.data
        self.training_data.append(data)
        
        # Keep last 10000 data points
        if len(self.training_data) > 10000:
            self.training_data.pop(0)
            
        # Update model weights if enough data
        if len(self.training_data) % 100 == 0:
            await self.update_model_weights()
            
    async def handle_model_update(self, event: Event):
        """Handle model updates"""
        if not self.running:
            return
            
        model_name = event.data.get('model')
        weights = event.data.get('weights')
        
        if model_name in self.models:
            self.models[model_name]['weight'] = weights
            logger.info(f"Updated {model_name} weight to {weights}")
            
    async def update_model_weights(self):
        """Update model weights based on performance"""
        # In production, evaluate model performance
        # For now, simulate weight adjustment
        if len(self.ensemble_predictions) < 10:
            return
            
        # Calculate recent performance
        recent = self.ensemble_predictions[-10:]
        for model_name in self.models:
            # Get model predictions
            model_preds = [p['model_predictions'][model_name] for p in recent]
            
            # Calculate error
            errors = [abs(p['prediction'] - pred) for p, pred in zip(recent, model_preds)]
            avg_error = sum(errors) / len(errors) if errors else 0
            
            # Adjust weight inversely to error
            if avg_error > 0:
                self.models[model_name]['weight'] = max(0.05, 1 / (1 + avg_error))
                
        # Normalize weights
        total_weight = sum(m['weight'] for m in self.models.values())
        if total_weight > 0:
            for model_name in self.models:
                self.models[model_name]['weight'] /= total_weight
                
    async def publish_ensemble_update(self):
        """Publish ensemble data update"""
        ensemble_data = {
            'latest_prediction': self.ensemble_predictions[-1] if self.ensemble_predictions else None,
            'model_weights': {m: self.models[m]['weight'] for m in self.models},
            'prediction_count': len(self.ensemble_predictions),
            'training_data_size': len(self.training_data),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="ensemble_update",
            data=ensemble_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get AI ensemble status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'models': list(self.models.keys()),
            'prediction_count': len(self.ensemble_predictions),
            'training_data_size': len(self.training_data),
            'model_weights': {m: self.models[m]['weight'] for m in self.models},
            'timestamp': datetime.now().isoformat()
        }
