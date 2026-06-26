"""
AlphaEdge Agent 58 – Error Memory Curator
Vector database of mistakes, similarity detection (>0.85), pre-execution check
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import hashlib
import random
import math

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ErrorMemoryCurator:
    """Error Memory Curator – Stores and retrieves error patterns for prevention"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "error_memory"
        self.running = False
        
        # Memory state
        self.error_memories = []
        self.similarity_cache = {}
        self.prevention_checks = []
        
        # Configuration
        self.config = {
            'similarity_threshold': 0.85,
            'max_memories': 10000,
            'min_memories_for_check': 10,
            'importance_weight': 0.5
        }
        
    async def start(self):
        """Start the error memory curator"""
        logger.info("Error Memory Curator starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("error_memory_request", self.handle_error_memory_request)
        await self.event_bus.subscribe("similarity_check", self.handle_similarity_check)
        await self.event_bus.subscribe("prevention_check", self.handle_prevention_check)
        
        # Start memory cycle
        asyncio.create_task(self.run_memory_cycle())
        
        logger.info("Error Memory Curator running")
        
    async def stop(self):
        """Stop the error memory curator"""
        self.running = False
        logger.info("Error Memory Curator stopped")
        
    async def run_memory_cycle(self):
        """Run regular memory cycle"""
        while self.running:
            try:
                # Clean old memories
                await self.clean_memories()
                
                # Update similarity cache
                await self.update_similarity_cache()
                
                # Publish memory update
                await self.publish_memory_update()
                
            except Exception as e:
                logger.error(f"Memory cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def handle_error_memory_request(self, event: Event):
        """Handle error memory requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        action = event.data.get('action')
        
        if action == 'store':
            result = await self.store_error_memory(event.data.get('error'))
        elif action == 'retrieve':
            result = await self.retrieve_error_memories(event.data.get('query'))
        elif action == 'similar':
            result = await self.find_similar_errors(event.data.get('error'))
        else:
            result = {'status': 'unknown_action'}
            
        response = Event(
            event_type="error_memory_response",
            data={
                'request_id': request_id,
                'action': action,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_similarity_check(self, event: Event):
        """Handle similarity checks"""
        if not self.running:
            return
            
        error = event.data.get('error')
        threshold = event.data.get('threshold', self.config['similarity_threshold'])
        
        # Check similarity
        similar = await self.find_similar_errors(error, threshold)
        
        response = Event(
            event_type="similarity_check_response",
            data={
                'error': error,
                'threshold': threshold,
                'similar': similar,
                'has_similar': len(similar) > 0,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_prevention_check(self, event: Event):
        """Handle prevention checks"""
        if not self.running:
            return
            
        action = event.data.get('action')
        
        # Check if action is similar to past errors
        prevention_result = await self.check_action_prevention(action)
        
        response = Event(
            event_type="prevention_check_response",
            data={
                'action': action,
                'result': prevention_result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def store_error_memory(self, error: Dict) -> Dict:
        """Store an error in memory"""
        # Generate error hash
        error_hash = self.generate_error_hash(error)
        
        # Check if error already exists
        for memory in self.error_memories:
            if memory['hash'] == error_hash:
                memory['occurrence_count'] += 1
                memory['last_seen'] = datetime.now().isoformat()
                return {'status': 'updated', 'hash': error_hash}
                
        # Create new memory
        memory = {
            'hash': error_hash,
            'error': error,
            'features': self.extract_features(error),
            'importance': self.calculate_importance(error),
            'occurrence_count': 1,
            'first_seen': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat(),
            'timestamp': datetime.now().isoformat()
        }
        
        self.error_memories.append(memory)
        
        # Remove old memories if needed
        if len(self.error_memories) > self.config['max_memories']:
            # Sort by importance and occurrence
            self.error_memories.sort(
                key=lambda x: (x['importance'] * x['occurrence_count']),
                reverse=True
            )
            self.error_memories = self.error_memories[:self.config['max_memories']]
            
        return {'status': 'stored', 'hash': error_hash}
        
    async def retrieve_error_memories(self, query: Dict) -> Dict:
        """Retrieve error memories by query"""
        results = []
        
        for memory in self.error_memories:
            # Calculate similarity score
            score = self.calculate_similarity(query, memory['error'])
            
            if score > self.config['similarity_threshold']:
                results.append({
                    'memory': memory,
                    'similarity': score
                })
                
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return {
            'results': results[:10],  # Return top 10
            'total': len(results),
            'timestamp': datetime.now().isoformat()
        }
        
    async def find_similar_errors(self, error: Dict, threshold: Optional[float] = None) -> List:
        """Find similar errors"""
        if threshold is None:
            threshold = self.config['similarity_threshold']
            
        similar = []
        
        for memory in self.error_memories:
            similarity = self.calculate_similarity(error, memory['error'])
            if similarity > threshold:
                similar.append({
                    'memory': memory,
                    'similarity': similarity
                })
                
        return sorted(similar, key=lambda x: x['similarity'], reverse=True)
        
    async def check_action_prevention(self, action: Dict) -> Dict:
        """Check if action is similar to past errors"""
        # Get recent errors
        recent_errors = [
            m['error'] for m in self.error_memories[-20:]
        ]
        
        if len(recent_errors) < self.config['min_memories_for_check']:
            return {
                'prevent': False,
                'reason': 'insufficient_memory',
                'similarity': 0
            }
            
        # Check similarity
        max_similarity = 0
        most_similar = None
        
        for error in recent_errors:
            similarity = self.calculate_similarity(action, error)
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar = error
                
        if max_similarity > self.config['similarity_threshold']:
            return {
                'prevent': True,
                'similarity': max_similarity,
                'similar_error': most_similar,
                'reason': 'similar_to_past_error'
            }
            
        return {
            'prevent': False,
            'similarity': max_similarity,
            'reason': 'no_similar_error'
        }
        
    def generate_error_hash(self, error: Dict) -> str:
        """Generate unique hash for error"""
        error_string = json.dumps(error, sort_keys=True)
        return hashlib.sha256(error_string.encode()).hexdigest()
        
    def extract_features(self, error: Dict) -> List[float]:
        """Extract features from error for similarity calculation"""
        # In production, use proper feature extraction
        # For now, use simplified features
        features = []
        
        # Error type
        error_type = error.get('type', 'unknown')
        type_map = {
            'network': [1, 0, 0, 0, 0],
            'rpc': [0, 1, 0, 0, 0],
            'execution': [0, 0, 1, 0, 0],
            'data': [0, 0, 0, 1, 0],
            'system': [0, 0, 0, 0, 1]
        }
        features.extend(type_map.get(error_type, [0, 0, 0, 0, 0]))
        
        # Error severity
        severity = error.get('severity', 0)
        features.append(severity / 10)  # Normalize
        
        # Error message length
        message = error.get('message', '')
        features.append(min(1, len(message) / 1000))
        
        return features
        
    def calculate_similarity(self, error1: Dict, error2: Dict) -> float:
        """Calculate similarity between two errors"""
        features1 = self.extract_features(error1)
        features2 = self.extract_features(error2)
        
        if len(features1) != len(features2):
            return 0
            
        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(features1, features2))
        mag1 = math.sqrt(sum(a * a for a in features1))
        mag2 = math.sqrt(sum(b * b for b in features2))
        
        if mag1 == 0 or mag2 == 0:
            return 0
            
        return dot_product / (mag1 * mag2)
        
    def calculate_importance(self, error: Dict) -> float:
        """Calculate importance of an error"""
        # Importance based on severity and occurrence
        severity = error.get('severity', 0)
        importance = severity / 10  # Normalize
        
        # Add some randomness for initial importance
        importance = importance * (0.8 + random.random() * 0.4)
        
        return min(1, importance)
        
    async def clean_memories(self):
        """Clean old memories"""
        # Remove old memories with low importance
        current_time = datetime.now().timestamp()
        
        to_remove = []
        for i, memory in enumerate(self.error_memories):
            # Check age
            last_seen = datetime.fromisoformat(memory['last_seen'])
            age_days = (datetime.now() - last_seen).days
            
            # Remove old, low-importance memories
            if age_days > 30 and memory['importance'] < 0.3:
                to_remove.append(i)
                
        # Remove in reverse order
        for i in reversed(to_remove):
            del self.error_memories[i]
            
    async def update_similarity_cache(self):
        """Update similarity cache"""
        # In production, use vector database
        # For now, just log
        pass
        
    async def publish_memory_update(self):
        """Publish memory data update"""
        memory_data = {
            'total_memories': len(self.error_memories),
            'recent_memories': self.error_memories[-5:],
            'prevention_checks': self.prevention_checks[-5:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="memory_update",
            data=memory_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get error memory curator status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'total_memories': len(self.error_memories),
            'prevention_checks': len(self.prevention_checks),
            'similarity_threshold': self.config['similarity_threshold'],
            'timestamp': datetime.now().isoformat()
        }
