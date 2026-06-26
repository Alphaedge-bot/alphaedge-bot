"""
AlphaEdge Agent 26 – Execution Quality Auditor
Post-trade slippage analysis, compare vs VWAP, flag leaking venues
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


class ExecutionQualityAuditor:
    """Execution Quality Auditor – Monitors and audits trade execution quality"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "execution_auditor"
        self.running = False
        
        # Audit state
        self.execution_records = []
        self.audit_results = []
        self.leaking_venues = set()
        self.quality_scores = {}
        
        # Quality thresholds
        self.slippage_threshold = 0.01  # 1%
        self.vwap_deviation_threshold = 0.02  # 2%
        
    async def start(self):
        """Start the execution auditor"""
        logger.info("Execution Quality Auditor starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("execution_result", self.handle_execution_result)
        await self.event_bus.subscribe("audit_request", self.handle_audit_request)
        await self.event_bus.subscribe("venue_report_request", self.handle_venue_report)
        
        # Start audit cycle
        asyncio.create_task(self.run_audit_cycle())
        
        logger.info("Execution Quality Auditor running")
        
    async def stop(self):
        """Stop the execution auditor"""
        self.running = False
        logger.info("Execution Quality Auditor stopped")
        
    async def run_audit_cycle(self):
        """Run regular audit cycle"""
        while self.running:
            try:
                # Process pending audits
                await self.process_audits()
                
                # Update venue quality scores
                await self.update_venue_scores()
                
                # Check for leaking venues
                await self.check_leaking_venues()
                
                # Publish audit update
                await self.publish_audit_update()
                
            except Exception as e:
                logger.error(f"Audit cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def handle_execution_result(self, event: Event):
        """Handle execution results"""
        if not self.running:
            return
            
        execution = event.data
        execution_id = execution.get('order_id')
        
        logger.info(f"Execution result received: {execution_id}")
        
        # Store execution record
        self.execution_records.append({
            'execution_id': execution_id,
            'data': execution,
            'timestamp': datetime.now().isoformat()
        })
        
        # Queue audit
        await self.queue_audit(execution_id)
        
    async def queue_audit(self, execution_id: str):
        """Queue an execution for audit"""
        # Find execution
        execution = None
        for record in self.execution_records:
            if record['execution_id'] == execution_id:
                execution = record['data']
                break
                
        if execution:
            # Calculate VWAP benchmark
            vwap = await self.calculate_vwap_benchmark(execution)
            
            # Check slippage
            slippage = await self.check_slippage(execution, vwap)
            
            # Check venue quality
            venue_quality = await self.check_venue_quality(execution)
            
            # Create audit result
            audit = {
                'execution_id': execution_id,
                'slippage': slippage,
                'vwap': vwap,
                'venue_quality': venue_quality,
                'quality_score': self.calculate_quality_score(slippage, venue_quality),
                'timestamp': datetime.now().isoformat()
            }
            
            self.audit_results.append(audit)
            
            # Flag if poor quality
            if audit['quality_score'] < 0.5:
                await self.flag_poor_execution(audit)
                
    async def calculate_vwap_benchmark(self, execution: Dict) -> float:
        """Calculate VWAP benchmark for an execution"""
        token = execution.get('token')
        execution_price = execution.get('execution_price', 0)
        quantity = execution.get('quantity', 0)
        
        # In production, fetch actual VWAP from market data
        # For now, simulate VWAP calculation
        price_range = execution_price * 0.02  # 2% range
        vwap = execution_price + (price_range * (0.5 - random.random()))
        
        return vwap
        
    async def check_slippage(self, execution: Dict, vwap: float) -> Dict:
        """Check slippage against VWAP"""
        execution_price = execution.get('execution_price', 0)
        
        if vwap == 0 or execution_price == 0:
            return {'slippage': 0, 'acceptable': True}
            
        slippage = (execution_price - vwap) / vwap
        acceptable = abs(slippage) < self.slippage_threshold
        
        return {
            'slippage': slippage,
            'acceptable': acceptable,
            'threshold': self.slippage_threshold
        }
        
    async def check_venue_quality(self, execution: Dict) -> Dict:
        """Check venue execution quality"""
        dex = execution.get('dex', 'unknown')
        
        # In production, check historical performance
        # For now, simulate quality check
        quality_score = random.uniform(0.3, 0.95)
        
        return {
            'dex': dex,
            'score': quality_score,
            'status': 'good' if quality_score > 0.7 else 'poor'
        }
        
    def calculate_quality_score(self, slippage: Dict, venue_quality: Dict) -> float:
        """Calculate overall execution quality score"""
        # Slippage component (0-1)
        slippage_score = 1 - min(1, abs(slippage.get('slippage', 0)) / 0.1)
        
        # Venue quality component (0-1)
        venue_score = venue_quality.get('score', 0.5)
        
        # Weighted average
        quality_score = (slippage_score * 0.6) + (venue_score * 0.4)
        
        return max(0, min(1, quality_score))
        
    async def flag_poor_execution(self, audit: Dict):
        """Flag poor execution quality"""
        execution_id = audit['execution_id']
        quality_score = audit['quality_score']
        
        logger.warning(f"⚠️ Poor execution quality: {execution_id} (score: {quality_score:.2f})")
        
        # Publish alert
        alert_event = Event(
            event_type="execution_alert",
            data={
                'execution_id': execution_id,
                'quality_score': quality_score,
                'issues': self.identify_issues(audit),
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        )
        await self.event_bus.publish(alert_event)
        
    def identify_issues(self, audit: Dict) -> List[str]:
        """Identify issues in execution"""
        issues = []
        
        slippage = audit.get('slippage', {})
        if not slippage.get('acceptable', True):
            issues.append(f"Slippage {slippage.get('slippage', 0)*100:.2f}% exceeds threshold")
            
        venue_quality = audit.get('venue_quality', {})
        if venue_quality.get('status') == 'poor':
            issues.append(f"Venue {venue_quality.get('dex')} quality score {venue_quality.get('score'):.2f}")
            
        return issues
        
    async def update_venue_scores(self):
        """Update venue quality scores"""
        venue_scores = {}
        
        for record in self.audit_results[-100:]:  # Last 100 audits
            venue = record.get('venue_quality', {}).get('dex')
            score = record.get('venue_quality', {}).get('score', 0)
            
            if venue:
                if venue not in venue_scores:
                    venue_scores[venue] = []
                venue_scores[venue].append(score)
                
        # Calculate average scores
        for venue, scores in venue_scores.items():
            self.quality_scores[venue] = statistics.mean(scores) if scores else 0.5
            
    async def check_leaking_venues(self):
        """Check for leaking venues"""
        for venue, score in self.quality_scores.items():
            if score < 0.5:
                self.leaking_venues.add(venue)
                logger.warning(f"Leaking venue detected: {venue} (score: {score:.2f})")
            elif score > 0.7 and venue in self.leaking_venues:
                self.leaking_venues.remove(venue)
                
    async def process_audits(self):
        """Process queued audits"""
        # Audits are processed in queue_audit method
        pass
        
    async def handle_audit_request(self, event: Event):
        """Handle audit requests"""
        if not self.running:
            return
            
        execution_id = event.data.get('execution_id')
        
        # Find audit result
        audit = None
        for result in self.audit_results:
            if result['execution_id'] == execution_id:
                audit = result
                break
                
        response = Event(
            event_type="audit_response",
            data={
                'execution_id': execution_id,
                'audit': audit,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_venue_report(self, event: Event):
        """Handle venue report requests"""
        if not self.running:
            return
            
        venue_report = {
            'quality_scores': self.quality_scores,
            'leaking_venues': list(self.leaking_venues),
            'recommendations': self.generate_recommendations(),
            'timestamp': datetime.now().isoformat()
        }
        
        response = Event(
            event_type="venue_report_response",
            data=venue_report,
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    def generate_recommendations(self) -> List[str]:
        """Generate venue recommendations"""
        recommendations = []
        
        for venue, score in self.quality_scores.items():
            if score < 0.5:
                recommendations.append(f"Avoid {venue} (quality score: {score:.2f})")
            elif score > 0.8:
                recommendations.append(f"Prefer {venue} (quality score: {score:.2f})")
                
        return recommendations
        
    async def publish_audit_update(self):
        """Publish audit data update"""
        audit_data = {
            'total_audits': len(self.audit_results),
            'quality_scores': self.quality_scores,
            'leaking_venues': list(self.leaking_venues),
            'recent_audits': self.audit_results[-5:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="audit_update",
            data=audit_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get execution auditor status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'total_audits': len(self.audit_results),
            'quality_scores': self.quality_scores,
            'leaking_venues': list(self.leaking_venues),
            'timestamp': datetime.now().isoformat()
        }
