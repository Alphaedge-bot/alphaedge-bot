"""
AlphaEdge Agent 11 – Model Drift Detector
Detects strategy/agent drift in real-time
Monitors performance degradation and concept drift
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import statistics
import math

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ModelDriftDetector:
    """Model Drift Detector – Monitors strategy and agent drift in real-time"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "drift"
        self.running = False
        
        # Drift detection data
        self.performance_history = []
        self.drift_alerts = []
        self.drift_scores = {}
        
        # Configuration
        self.window_size = 100
        self.drift_threshold = 0.15  # 15% performance degradation
        self.concept_drift_threshold = 0.25  # 25% distribution change
        
    async def start(self):
        """Start the drift detector"""
        logger.info("Model Drift Detector starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("performance_update", self.handle_performance_update)
        await self.event_bus.subscribe("drift_check_request", self.handle_drift_check_request)
        
        # Start drift detection cycle
        asyncio.create_task(self.run_drift_detection_cycle())
        
        logger.info("Model Drift Detector running")
        
    async def stop(self):
        """Stop the drift detector"""
        self.running = False
        logger.info("Model Drift Detector stopped")
        
    async def run_drift_detection_cycle(self):
        """Run regular drift detection"""
        while self.running:
            try:
                # Check for performance drift
                await self.check_performance_drift()
                
                # Check for concept drift
                await self.check_concept_drift()
                
                # Check for agent drift
                await self.check_agent_drift()
                
                # Publish drift update
                await self.publish_drift_update()
                
            except Exception as e:
                logger.error(f"Drift detection cycle error: {e}")
                
            await asyncio.sleep(300)  # Every 5 minutes
            
    async def handle_performance_update(self, event: Event):
        """Handle performance updates"""
        if not self.running:
            return
            
        performance_data = event.data
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'data': performance_data
        })
        
        # Keep last 1000 entries
        if len(self.performance_history) > 1000:
            self.performance_history.pop(0)
            
    async def check_performance_drift(self):
        """Check for performance drift"""
        if len(self.performance_history) < self.window_size:
            return
            
        # Get recent performance
        recent = self.performance_history[-self.window_size:]
        old = self.performance_history[:self.window_size]
        
        # Calculate performance metrics
        recent_win_rate = self.calculate_win_rate(recent)
        old_win_rate = self.calculate_win_rate(old)
        
        recent_sharpe = self.calculate_sharpe(recent)
        old_sharpe = self.calculate_sharpe(old)
        
        # Calculate drift
        win_rate_drift = (old_win_rate - recent_win_rate) / old_win_rate if old_win_rate > 0 else 0
        sharpe_drift = (old_sharpe - recent_sharpe) / old_sharpe if old_sharpe > 0 else 0
        
        self.drift_scores['performance'] = {
            'win_rate_drift': win_rate_drift,
            'sharpe_drift': sharpe_drift,
            'recent_win_rate': recent_win_rate,
            'old_win_rate': old_win_rate,
            'recent_sharpe': recent_sharpe,
            'old_sharpe': old_sharpe
        }
        
        # Check if drift exceeds threshold
        if abs(win_rate_drift) > self.drift_threshold or abs(sharpe_drift) > self.drift_threshold:
            await self.alert_drift('performance', self.drift_scores['performance'])
            
    def calculate_win_rate(self, history: List[Dict]) -> float:
        """Calculate win rate from history"""
        wins = 0
        total = 0
        
        for entry in history:
            data = entry.get('data', {})
            if 'win_rate' in data:
                return data['win_rate']
                
            # Calculate from trades
            trades = data.get('trades', [])
            for trade in trades:
                if trade.get('pnl', 0) > 0:
                    wins += 1
                total += 1
                
        return wins / total if total > 0 else 0
        
    def calculate_sharpe(self, history: List[Dict]) -> float:
        """Calculate Sharpe ratio from history"""
        returns = []
        
        for entry in history:
            data = entry.get('data', {})
            if 'sharpe' in data:
                return data['sharpe']
                
            # Calculate from returns
            daily_return = data.get('daily_return', 0)
            if daily_return != 0:
                returns.append(daily_return)
                
        if len(returns) < 2:
            return 0
            
        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 0.01
        
        return avg_return / std_return if std_return > 0 else 0
        
    async def check_concept_drift(self):
        """Check for concept drift"""
        # Get feature distributions
        recent_features = await self.get_recent_features()
        historical_features = await self.get_historical_features()
        
        if not recent_features or not historical_features:
            return
            
        # Calculate distribution divergence
        divergence = self.calculate_kl_divergence(recent_features, historical_features)
        
        self.drift_scores['concept'] = {
            'divergence': divergence,
            'threshold': self.concept_drift_threshold,
            'drift_detected': divergence > self.concept_drift_threshold
        }
        
        if divergence > self.concept_drift_threshold:
            await self.alert_drift('concept', self.drift_scores['concept'])
            
    async def get_recent_features(self) -> List[float]:
        """Get recent feature distributions"""
        # In production, extract from actual data
        # For now, return sample distribution
        return [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        
    async def get_historical_features(self) -> List[float]:
        """Get historical feature distributions"""
        # In production, extract from actual data
        # For now, return sample distribution
        return [0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95]
        
    def calculate_kl_divergence(self, p: List[float], q: List[float]) -> float:
        """Calculate Kullback-Leibler divergence"""
        if len(p) != len(q) or len(p) == 0:
            return 0
            
        # Normalize distributions
        p_sum = sum(p)
        q_sum = sum(q)
        
        if p_sum == 0 or q_sum == 0:
            return 0
            
        p_norm = [x / p_sum for x in p]
        q_norm = [x / q_sum for x in q]
        
        # Calculate KL divergence
        divergence = 0
        for i in range(len(p_norm)):
            if p_norm[i] > 0 and q_norm[i] > 0:
                divergence += p_norm[i] * math.log(p_norm[i] / q_norm[i])
                
        return divergence
        
    async def check_agent_drift(self):
        """Check for agent behavioral drift"""
        # Get agent statuses
        agent_statuses = await self.state_manager.get('agent_statuses', {})
        
        if not agent_statuses:
            return
            
        # Calculate drift scores for each agent
        drift_counts = {}
        total_agents = len(agent_statuses)
        
        for agent_id, status in agent_statuses.items():
            # Check if agent behavior has changed
            recent_behavior = status.get('recent_behavior', {})
            historical_behavior = status.get('historical_behavior', {})
            
            if recent_behavior and historical_behavior:
                behavior_drift = self.calculate_behavior_drift(
                    recent_behavior, historical_behavior
                )
                
                if behavior_drift > 0.3:  # 30% behavior change
                    drift_counts[agent_id] = behavior_drift
                    
        self.drift_scores['agent'] = {
            'total_agents': total_agents,
            'agents_with_drift': len(drift_counts),
            'drift_ratio': len(drift_counts) / total_agents if total_agents > 0 else 0,
            'drift_details': drift_counts
        }
        
        if self.drift_scores['agent']['drift_ratio'] > 0.3:
            await self.alert_drift('agent', self.drift_scores['agent'])
            
    def calculate_behavior_drift(self, recent: Dict, historical: Dict) -> float:
        """Calculate behavioral drift between recent and historical behavior"""
        if not recent or not historical:
            return 0
            
        # Compare key behavior metrics
        drift_score = 0
        metrics_compared = 0
        
        for key in ['decision_frequency', 'risk_tolerance', 'position_size']:
            if key in recent and key in historical:
                recent_val = recent[key]
                historical_val = historical[key]
                
                if historical_val != 0:
                    drift = abs(recent_val - historical_val) / historical_val
                    drift_score += drift
                    metrics_compared += 1
                    
        return drift_score / metrics_compared if metrics_compared > 0 else 0
        
    async def alert_drift(self, drift_type: str, data: Dict):
        """Alert on detected drift"""
        alert = {
            'type': drift_type,
            'severity': self.calculate_severity(drift_type, data),
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        self.drift_alerts.append(alert)
        
        # Publish alert
        alert_event = Event(
            event_type="drift_alert",
            data=alert,
            source=self.agent_id
        )
        await self.event_bus.publish(alert_event)
        
        logger.warning(f"⚠️ DRIFT DETECTED: {drift_type} - Severity: {alert['severity']}")
        
    def calculate_severity(self, drift_type: str, data: Dict) -> str:
        """Calculate severity of drift"""
        if drift_type == 'performance':
            win_rate_drift = abs(data.get('win_rate_drift', 0))
            if win_rate_drift > 0.3:
                return 'critical'
            elif win_rate_drift > 0.2:
                return 'high'
            elif win_rate_drift > self.drift_threshold:
                return 'medium'
                
        elif drift_type == 'concept':
            divergence = data.get('divergence', 0)
            if divergence > 0.5:
                return 'critical'
            elif divergence > 0.3:
                return 'high'
            elif divergence > self.concept_drift_threshold:
                return 'medium'
                
        elif drift_type == 'agent':
            drift_ratio = data.get('drift_ratio', 0)
            if drift_ratio > 0.5:
                return 'critical'
            elif drift_ratio > 0.4:
                return 'high'
            elif drift_ratio > 0.3:
                return 'medium'
                
        return 'low'
        
    async def publish_drift_update(self):
        """Publish drift data update"""
        drift_data = {
            'drift_scores': self.drift_scores,
            'recent_alerts': self.drift_alerts[-5:],
            'total_alerts': len(self.drift_alerts),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="drift_data_update",
            data=drift_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def handle_drift_check_request(self, event: Event):
        """Handle drift check requests"""
        if not self.running:
            return
            
        drift_data = {
            'drift_scores': self.drift_scores,
            'recent_alerts': self.drift_alerts[-5:],
            'total_alerts': len(self.drift_alerts),
            'timestamp': datetime.now().isoformat()
        }
        
        response = Event(
            event_type="drift_check_response",
            data=drift_data,
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get drift detector status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'performance_history': len(self.performance_history),
            'drift_alerts': len(self.drift_alerts),
            'drift_scores': self.drift_scores,
            'timestamp': datetime.now().isoformat()
        }
