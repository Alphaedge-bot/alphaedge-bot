"""
AlphaEdge Agent 33 – Transformer Predictor
Transformer-based price prediction
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


class TransformerPredictor:
    """Transformer Predictor – Transformer-based price prediction model"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "transformer"
        self.running = False
        
        # Model state
        self.input_sequence = []
        self.predictions = []
        self.attention_weights = {}
        
        # Model parameters
        self.sequence_length = 50
        self.prediction_horizon = 10
        self.embedding_dim = 128
        self.num_heads = 8
        
        # Training state
        self.training_epochs = 0
        self.loss_history = []
        
    async def start(self):
        """Start the transformer predictor"""
        logger.info("Transformer Predictor starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("transformer_request", self.handle_prediction_request)
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("attention_request", self.handle_attention_request)
        
        # Start transformer cycle
        asyncio.create_task(self.run_transformer_cycle())
        
        logger.info("Transformer Predictor running")
        
    async def stop(self):
        """Stop the transformer predictor"""
        self.running = False
        logger.info("Transformer Predictor stopped")
        
    async def run_transformer_cycle(self):
        """Run regular transformer prediction cycle"""
        while self.running:
            try:
                if len(self.input_sequence) >= self.sequence_length:
                    # Run transformer prediction
                    prediction = await self.run_transformer()
                    
                    # Store prediction
                    self.predictions.append({
                        'timestamp': datetime.now().isoformat(),
                        'prediction': prediction
                    })
                    
                    # Publish transformer update
                    await self.publish_transformer_update()
                    
            except Exception as e:
                logger.error(f"Transformer cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def handle_prediction_request(self, event: Event):
        """Handle prediction requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        data = event.data.get('data', [])
        
        logger.info(f"Prediction request: {request_id}")
        
        # Run transformer on provided data
        prediction = await self.transform(data)
        
        # Send response
        response = Event(
            event_type="transformer_response",
            data={
                'request_id': request_id,
                'prediction': prediction,
                'attention_weights': self.attention_weights,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        if not self.running:
            return
            
        price_data = event.data.get('price', 0)
        timestamp = event.data.get('timestamp', datetime.now().isoformat())
        
        # Add to input sequence
        self.input_sequence.append({
            'price': price_data,
            'timestamp': timestamp
        })
        
        # Keep only last sequence_length entries
        if len(self.input_sequence) > self.sequence_length * 2:
            self.input_sequence = self.input_sequence[-self.sequence_length:]
            
    async def run_transformer(self) -> Dict:
        """Run transformer prediction"""
        # Prepare input sequence
        prices = [item['price'] for item in self.input_sequence[-self.sequence_length:]]
        
        # Normalize prices
        mean_price = sum(prices) / len(prices)
        std_price = math.sqrt(sum((p - mean_price) ** 2 for p in prices) / len(prices))
        normalized_prices = [(p - mean_price) / (std_price + 0.0001) for p in prices]
        
        # Compute attention (simplified)
        self.attention_weights = await self.compute_attention(normalized_prices)
        
        # Transform input through attention
        transformed = await self.apply_attention(normalized_prices, self.attention_weights)
        
        # Generate prediction
        prediction = await self.generate_prediction(transformed, mean_price, std_price)
        
        # Store in state
        await self.state_manager.set('transformer_prediction', {
            'price': prediction['price'],
            'confidence': prediction['confidence'],
            'attention_weights': self.attention_weights,
            'timestamp': datetime.now().isoformat()
        })
        
        return prediction
        
    async def compute_attention(self, sequence: List[float]) -> Dict:
        """Compute attention weights (simplified)"""
        # In production, implement full transformer attention
        # For now, simulate attention computation
        seq_len = len(sequence)
        attention = {}
        
        # Multi-head attention simulation
        for head in range(self.num_heads):
            attention[f'head_{head}'] = [
                random.uniform(0.1, 0.9) for _ in range(seq_len)
            ]
            # Normalize
            total = sum(attention[f'head_{head}'])
            attention[f'head_{head}'] = [a / total for a in attention[f'head_{head}']]
            
        return attention
        
    async def apply_attention(self, sequence: List[float], attention: Dict) -> List[float]:
        """Apply attention weights to sequence"""
        # Simplified attention application
        # In production, use full transformer architecture
        seq_len = len(sequence)
        transformed = [0] * seq_len
        
        # Aggregate attention from all heads
        for i in range(seq_len):
            head_weights = [attention[f'head_{h}'][i] for h in range(self.num_heads)]
            avg_weight = sum(head_weights) / len(head_weights)
            transformed[i] = sequence[i] * avg_weight
            
        return transformed
        
    async def generate_prediction(self, transformed: List[float], 
                                 mean_price: float, std_price: float) -> Dict:
        """Generate prediction from transformed sequence"""
        # Simplified prediction generation
        # In production, use transformer decoder
        
        # Use last few transformed values to predict next
        pred_value = sum(transformed[-5:]) / 5 if len(transformed) >= 5 else transformed[-1]
        
        # Add some noise
        pred_value *= (1 + random.uniform(-0.01, 0.01))
        
        # Denormalize
        price = pred_value * std_price + mean_price
        
        # Calculate confidence based on attention
        avg_attention = sum(attention_weight for head in self.attention_weights.values() 
                           for attention_weight in head) / (len(self.attention_weights) * len(transformed))
        confidence = min(0.95, 0.5 + avg_attention * 0.5)
        
        return {
            'price': price,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }
        
    async def transform(self, data: List[float]) -> Dict:
        """Transform input data using transformer"""
        # Similar to run_transformer but for arbitrary input
        if not data:
            return {'price': 0, 'confidence': 0}
            
        # Normalize
        mean_price = sum(data) / len(data)
        std_price = math.sqrt(sum((p - mean_price) ** 2 for p in data) / len(data))
        normalized = [(p - mean_price) / (std_price + 0.0001) for p in data]
        
        # Compute attention
        attention = await self.compute_attention(normalized)
        
        # Apply attention
        transformed = await self.apply_attention(normalized, attention)
        
        # Generate prediction
        pred_value = sum(transformed[-3:]) / 3 if len(transformed) >= 3 else transformed[-1]
        price = pred_value * std_price + mean_price
        
        return {
            'price': price,
            'confidence': 0.7,
            'attention_weights': attention
        }
        
    async def handle_attention_request(self, event: Event):
        """Handle attention visualization requests"""
        if not self.running:
            return
            
        response = Event(
            event_type="attention_response",
            data={
                'attention_weights': self.attention_weights,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def publish_transformer_update(self):
        """Publish transformer data update"""
        transformer_data = {
            'latest_prediction': self.predictions[-1] if self.predictions else None,
            'prediction_count': len(self.predictions),
            'sequence_length': len(self.input_sequence),
            'attention_weights': self.attention_weights,
            'training_epochs': self.training_epochs,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="transformer_update",
            data=transformer_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get transformer predictor status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'sequence_length': len(self.input_sequence),
            'prediction_count': len(self.predictions),
            'training_epochs': self.training_epochs,
            'num_heads': self.num_heads,
            'embedding_dim': self.embedding_dim,
            'timestamp': datetime.now().isoformat()
        }
