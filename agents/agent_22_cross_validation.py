"""
AlphaEdge Agent 22 – Cross-Validation Oracle (Secondary)
Validates decisions across multiple models
Secondary validation layer for critical decisions
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CrossValidationOracle:
    """Cross-Validation Oracle – Secondary validation layer"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "cross_validation_2"
        self.running = False
        
        # Validation state
        self.validation_results = {}
        self.pending_validations = []
        self.validation_history = []
        
        # Validation thresholds
        self.confidence_threshold = 0.7
        self.consensus_threshold = 0.6
        
    async def start(self):
        """Start the cross-validation oracle"""
        logger.info("Cross-Validation Oracle (2) starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("validation_request", self.handle_validation_request)
        await self.event_bus.subscribe("signal_validation", self.handle_signal_validation)
        
        # Start validation cycle
        asyncio.create_task(self.run_validation_cycle())
        
        logger.info("Cross-Validation Oracle (2) running")
        
    async def stop(self):
        """Stop the cross-validation oracle"""
        self.running = False
        logger.info("Cross-Validation Oracle (2) stopped")
        
    async def run_validation_cycle(self):
        """Run regular validation cycle"""
        while self.running:
            try:
                # Process pending validations
                await self.process_pending_validations()
                
                # Check validation results
                await self.check_validation_results()
                
                # Publish validation update
                await self.publish_validation_update()
                
            except Exception as e:
                logger.error(f"Validation cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def handle_validation_request(self, event: Event):
        """Handle validation requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        data = event.data.get('data')
        source = event.source
        
        # Add to pending validations
        self.pending_validations.append({
            'id': request_id,
            'data': data,
            'source': source,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        })
        
        logger.info(f"Validation requested: {request_id}")
        
    async def handle_signal_validation(self, event: Event):
        """Handle signal validation requests"""
        if not self.running:
            return
            
        signal = event.data.get('signal')
        signal_id = signal.get('id')
        
        # Validate signal
        validation = await self.validate_signal(signal)
        
        # Store result
        self.validation_results[signal_id] = validation
        
        # Send response
        response = Event(
            event_type="signal_validation_response",
            data={
                'signal_id': signal_id,
                'validation': validation,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def validate_signal(self, signal: Dict) -> Dict:
        """Validate a signal against multiple models"""
        # Get model predictions
        model_predictions = await self.get_model_predictions(signal)
        
        # Calculate agreement
        agreement = self.calculate_agreement(model_predictions)
        
        # Determine validation status
        if agreement >= self.consensus_threshold:
            status = 'validated'
            confidence = agreement
        elif agreement >= self.confidence_threshold:
            status = 'partial'
            confidence = agreement
        else:
            status = 'rejected'
            confidence = agreement
            
        return {
            'status': status,
            'confidence': confidence,
            'agreement': agreement,
            'model_predictions': model_predictions,
            'timestamp': datetime.now().isoformat()
        }
        
    async def get_model_predictions(self, signal: Dict) -> Dict:
        """Get predictions from multiple models"""
        # In production, this would query actual ML models
        # For now, simulate model predictions
        
        models = ['technical', 'sentiment', 'onchain', 'macro', 'ensemble']
        predictions = {}
        
        for model in models:
            # Simulate prediction based on signal type
            signal_type = signal.get('type', 'entry')
            base = 0.8 if signal_type == 'entry' else 0.3
            
            # Add some variation
            import random
            predictions[model] = base + random.uniform(-0.2, 0.2)
            
        return predictions
        
    def calculate_agreement(self, predictions: Dict) -> float:
        """Calculate agreement among model predictions"""
        if not predictions:
            return 0
            
        # Convert to list
        values = list(predictions.values())
        
        # Calculate standard deviation (lower = higher agreement)
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        
        # Convert to agreement score (0-1)
        # If all predictions are identical (std=0), agreement=1
        # If predictions are spread out, agreement approaches 0
        max_std = 0.5  # Maximum expected std
        agreement = max(0, 1 - (std_dev / max_std))
        
        return agreement
        
    async def process_pending_validations(self):
        """Process pending validations"""
        for validation in self.pending_validations[:10]:
            # Validate the data
            validation_result = await self.validate_data(validation['data'])
            
            # Update status
            validation['status'] = 'processed'
            validation['result'] = validation_result
            
            # Send response
            if validation['source']:
                response = Event(
                    event_type="validation_result",
                    data={
                        'request_id': validation['id'],
                        'result': validation_result,
                        'timestamp': datetime.now().isoformat()
                    },
                    source=self.agent_id,
                    target=validation['source']
                )
                await self.event_bus.publish(response)
                
            # Move to history
            self.validation_history.append(validation)
            self.pending_validations.remove(validation)
            
    async def validate_data(self, data: Dict) -> Dict:
        """Validate data against multiple sources"""
        # Check data completeness
        required_fields = ['token', 'price', 'timestamp']
        completeness = all(field in data for field in required_fields)
        
        # Check data freshness (simplified)
        timestamp = data.get('timestamp')
        if timestamp:
            # In production, check actual timestamp
            freshness = 0.9
        else:
            freshness = 0.5
            
        # Check data consistency (simplified)
        consistency = 0.85
        
        # Combined validation
        validation_score = (completeness * 0.3 + freshness * 0.3 + consistency * 0.4)
        
        return {
            'valid': validation_score >= 0.7,
            'score': validation_score,
            'details': {
                'completeness': completeness,
                'freshness': freshness,
                'consistency': consistency
            },
            'timestamp': datetime.now().isoformat()
        }
        
    async def check_validation_results(self):
        """Check validation results and trigger alerts if needed"""
        for signal_id, result in self.validation_results.items():
            if result.get('status') == 'rejected':
                logger.warning(f"Signal {signal_id} rejected by validation")
                
                # Trigger alert
                alert_event = Event(
                    event_type="validation_alert",
                    data={
                        'signal_id': signal_id,
                        'reason': 'low_confidence',
                        'confidence': result.get('confidence', 0),
                        'timestamp': datetime.now().isoformat()
                    },
                    source=self.agent_id
                )
                await self.event_bus.publish(alert_event)
                
    async def publish_validation_update(self):
        """Publish validation data update"""
        validation_data = {
            'pending_validations': len(self.pending_validations),
            'validation_history': self.validation_history[-5:],
            'total_validations': len(self.validation_history),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="cross_validation_update",
            data=validation_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get cross-validation oracle status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'pending_validations': len(self.pending_validations),
            'total_validations': len(self.validation_history),
            'validation_results': len(self.validation_results),
            'timestamp': datetime.now().isoformat()
        }
