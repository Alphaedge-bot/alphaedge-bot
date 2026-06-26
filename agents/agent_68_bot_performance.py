"""
AlphaEdge Agent 68 – Bot Performance Auditor
Calculate Bot Performance Grade (BPG) A-F daily
Monitor multi-timescale drift
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


class BotPerformanceAuditor:
    """Bot Performance Auditor – Calculates Bot Performance Grade (BPG) daily"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "bot_performance"
        self.running = False
        
        # Performance state
        self.bpg = 0
        self.bpg_grade = 'N/A'
        self.grade_history = []
        self.component_scores = {}
        self.drift_metrics = {}
        
        # Grade thresholds
        self.grade_thresholds = {
            'A': {'min': 90, 'label': 'Exceptional'},
            'A-': {'min': 85, 'label': 'Outstanding'},
            'B+': {'min': 80, 'label': 'Very Strong'},
            'B': {'min': 75, 'label': 'Strong'},
            'B-': {'min': 70, 'label': 'Good'},
            'C+': {'min': 65, 'label': 'Above Average'},
            'C': {'min': 60, 'label': 'Average'},
            'C-': {'min': 55, 'label': 'Below Average'},
            'D': {'min': 45, 'label': 'Needs Improvement'},
            'F': {'min': 0, 'label': 'Critical Issues'}
        }
        
        # Component weights
        self.component_weights = {
            'sharpe_ratio': 0.30,
            'win_rate': 0.25,
            'max_drawdown': 0.20,
            'monthly_return': 0.15,
            'uptime': 0.10
        }
        
    async def start(self):
        """Start the bot performance auditor"""
        logger.info("Bot Performance Auditor starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("bpg_request", self.handle_bpg_request)
        await self.event_bus.subscribe("drift_check_request", self.handle_drift_check)
        await self.event_bus.subscribe("grade_history_request", self.handle_grade_history)
        
        # Start performance cycle
        asyncio.create_task(self.run_performance_cycle())
        
        logger.info("Bot Performance Auditor running")
        
    async def stop(self):
        """Stop the bot performance auditor"""
        self.running = False
        logger.info("Bot Performance Auditor stopped")
        
    async def run_performance_cycle(self):
        """Run regular performance cycle"""
        while self.running:
            try:
                # Calculate daily BPG
                await self.calculate_bpg()
                
                # Check for drift
                await self.check_drift()
                
                # Publish performance update
                await self.publish_performance_update()
                
            except Exception as e:
                logger.error(f"Performance cycle error: {e}")
                
            # Run daily at midnight
            await asyncio.sleep(3600)  # Check every hour
            
    async def handle_bpg_request(self, event: Event):
        """Handle BPG requests"""
        if not self.running:
            return
            
        response = Event(
            event_type="bpg_response",
            data={
                'bpg': self.bpg,
                'grade': self.bpg_grade,
                'component_scores': self.component_scores,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_drift_check(self, event: Event):
        """Handle drift check requests"""
        if not self.running:
            return
            
        response = Event(
            event_type="drift_check_response",
            data={
                'drift_metrics': self.drift_metrics,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_grade_history(self, event: Event):
        """Handle grade history requests"""
        if not self.running:
            return
            
        days = event.data.get('days', 30)
        
        # Get history
        history = self.grade_history[-days:]
        
        response = Event(
            event_type="grade_history_response",
            data={
                'days': days,
                'history': history,
                'average_grade': self.calculate_average_grade(history),
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def calculate_bpg(self):
        """Calculate Bot Performance Grade (BPG)"""
        # Get performance metrics
        metrics = await self.get_performance_metrics()
        
        # Calculate component scores (0-100)
        component_scores = {}
        
        # Sharpe ratio (30%)
        sharpe = metrics.get('sharpe_ratio', 0)
        component_scores['sharpe_ratio'] = self.calculate_sharpe_score(sharpe)
        
        # Win rate (25%)
        win_rate = metrics.get('win_rate', 0)
        component_scores['win_rate'] = min(100, win_rate * 100)
        
        # Max drawdown (20%)
        max_drawdown = metrics.get('max_drawdown', 0)
        component_scores['max_drawdown'] = self.calculate_drawdown_score(max_drawdown)
        
        # Monthly return (15%)
        monthly_return = metrics.get('monthly_return', 0)
        component_scores['monthly_return'] = self.calculate_return_score(monthly_return)
        
        # Uptime (10%)
        uptime = metrics.get('uptime', 99.9)
        component_scores['uptime'] = uptime
        
        # Calculate weighted score
        weighted_score = sum(
            component_scores[component] * weight
            for component, weight in self.component_weights.items()
        )
        
        # Round to nearest integer
        bpg_score = round(weighted_score)
        
        # Determine grade
        bpg_grade = self.determine_grade(bpg_score)
        
        # Store results
        self.bpg = bpg_score
        self.bpg_grade = bpg_grade
        self.component_scores = component_scores
        
        # Record history
        self.grade_history.append({
            'date': datetime.now().date().isoformat(),
            'bpg': bpg_score,
            'grade': bpg_grade,
            'components': component_scores,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep last 365 days
        if len(self.grade_history) > 365:
            self.grade_history = self.grade_history[-365:]
            
        # Store in state
        await self.state_manager.set('bpg', bpg_score)
        await self.state_manager.set('bpg_grade', bpg_grade)
        await self.state_manager.set('bpg_components', component_scores)
        
        logger.info(f"BPG: {bpg_score} ({bpg_grade})")
        
    async def get_performance_metrics(self) -> Dict:
        """Get performance metrics for BPG calculation"""
        # In production, fetch from actual data
        # For now, simulate
        
        return {
            'sharpe_ratio': random.uniform(1.5, 3.5),
            'win_rate': random.uniform(0.55, 0.80),
            'max_drawdown': random.uniform(0.02, 0.15),
            'monthly_return': random.uniform(0.10, 0.35),
            'uptime': random.uniform(99.5, 100)
        }
        
    def calculate_sharpe_score(self, sharpe: float) -> float:
        """Convert Sharpe ratio to 0-100 score"""
        if sharpe <= 0:
            return 0
        if sharpe >= 3.0:
            return 100
        return (sharpe / 3.0) * 100
        
    def calculate_drawdown_score(self, drawdown: float) -> float:
        """Convert drawdown to 0-100 score"""
        # 0% drawdown = 100, 50% drawdown = 0
        if drawdown <= 0:
            return 100
        if drawdown >= 0.5:
            return 0
        return 100 - (drawdown * 200)
        
    def calculate_return_score(self, monthly_return: float) -> float:
        """Convert monthly return to 0-100 score"""
        # 25% monthly return = 100
        if monthly_return <= 0:
            return 0
        if monthly_return >= 0.25:
            return 100
        return monthly_return * 400
        
    def determine_grade(self, score: int) -> str:
        """Determine grade from score"""
        for grade, thresholds in self.grade_thresholds.items():
            if score >= thresholds['min']:
                return grade
        return 'F'
        
    def calculate_average_grade(self, history: List[Dict]) -> Dict:
        """Calculate average grade from history"""
        if not history:
            return {'score': 0, 'grade': 'N/A'}
            
        avg_score = sum(h['bpg'] for h in history) / len(history)
        avg_grade = self.determine_grade(round(avg_score))
        
        return {'score': avg_score, 'grade': avg_grade}
        
    async def check_drift(self):
        """Check for multi-timescale drift"""
        if len(self.grade_history) < 30:
            return
            
        # Get different time windows
        windows = {
            '1d': self.grade_history[-1:],
            '7d': self.grade_history[-7:],
            '30d': self.grade_history[-30:],
            '90d': self.grade_history[-90:],
            '180d': self.grade_history[-180:],
            '365d': self.grade_history[-365:]
        }
        
        # Calculate averages for each window
        window_averages = {}
        for window_name, window_data in windows.items():
            if window_data:
                avg = sum(h['bpg'] for h in window_data) / len(window_data)
                window_averages[window_name] = avg
                
        # Calculate drift
        drift_metrics = {}
        if len(window_averages) >= 2:
            # Compare current to different periods
            current = window_averages.get('1d', 0)
            for window_name, avg in window_averages.items():
                if window_name != '1d' and avg > 0:
                    drift = (current - avg) / avg
                    drift_metrics[f'drift_{window_name}'] = drift
                    
        self.drift_metrics = drift_metrics
        
        # Alert if significant drift detected
        for key, drift in drift_metrics.items():
            if abs(drift) > 0.15:  # 15% drift
                logger.warning(f"⚠️ Significant drift detected: {key} = {drift:.2%}")
                
        # Store in state
        await self.state_manager.set('drift_metrics', drift_metrics)
        
    async def publish_performance_update(self):
        """Publish performance data update"""
        performance_data = {
            'bpg': self.bpg,
            'grade': self.bpg_grade,
            'component_scores': self.component_scores,
            'drift_metrics': self.drift_metrics,
            'grade_history': self.grade_history[-7:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="bot_performance_update",
            data=performance_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get bot performance auditor status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'bpg': self.bpg,
            'grade': self.bpg_grade,
            'component_scores': self.component_scores,
            'grade_history': len(self.grade_history),
            'drift_metrics': self.drift_metrics,
            'timestamp': datetime.now().isoformat()
        }
