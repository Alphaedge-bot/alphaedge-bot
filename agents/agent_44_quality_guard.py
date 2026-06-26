"""
AlphaEdge Agent 44 – Quality Guard
Validation (completeness, freshness<5min, type safety, null checks), pause on low quality
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class QualityGuard:
    """Quality Guard – Data quality validation and enforcement"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "quality_guard"
        self.running = False
        
        # Quality state
        self.quality_score = 100
        self.quality_issues = []
        self.quality_history = []
        
        # Quality thresholds
        self.thresholds = {
            'min_quality_score': 60,
            'max_freshness_seconds': 300,  # 5 minutes
            'max_failure_rate': 0.1,       # 10%
            'min_completeness': 0.8        # 80%
        }
        
        # Validation rules
        self.validation_rules = {
            'completeness': True,
            'freshness': True,
            'type_safety': True,
            'null_checks': True
        }
        
        self.paused = False
        
    async def start(self):
        """Start the quality guard"""
        logger.info("Quality Guard starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("quality_check_request", self.handle_quality_check)
        await self.event_bus.subscribe("data_validation", self.handle_data_validation)
        await self.event_bus.subscribe("quality_status_request", self.handle_quality_status)
        
        # Start quality cycle
        asyncio.create_task(self.run_quality_cycle())
        
        logger.info("Quality Guard running")
        
    async def stop(self):
        """Stop the quality guard"""
        self.running = False
        logger.info("Quality Guard stopped")
        
    async def run_quality_cycle(self):
        """Run regular quality cycle"""
        while self.running:
            try:
                # Validate system data
                await self.validate_system_data()
                
                # Update quality score
                await self.update_quality_score()
                
                # Check if quality is too low
                await self.check_quality_threshold()
                
                # Publish quality update
                await self.publish_quality_update()
                
            except Exception as e:
                logger.error(f"Quality cycle error: {e}")
                
            await asyncio.sleep(30)  # Every 30 seconds
            
    async def handle_quality_check(self, event: Event):
        """Handle quality check requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        data = event.data.get('data', {})
        
        # Validate data
        validation_result = await self.validate_data(data)
        
        response = Event(
            event_type="quality_check_response",
            data={
                'request_id': request_id,
                'validation': validation_result,
                'quality_score': self.quality_score,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_data_validation(self, event: Event):
        """Handle data validation events"""
        if not self.running:
            return
            
        data = event.data
        validation_result = await self.validate_data(data)
        
        if not validation_result['valid']:
            logger.warning(f"⚠️ Data validation failed: {validation_result['issues']}")
            self.quality_issues.append({
                'timestamp': datetime.now().isoformat(),
                'data': data,
                'issues': validation_result['issues']
            })
            
    async def handle_quality_status(self, event: Event):
        """Handle quality status requests"""
        if not self.running:
            return
            
        response = Event(
            event_type="quality_status_response",
            data={
                'quality_score': self.quality_score,
                'paused': self.paused,
                'quality_issues': self.quality_issues[-10:],
                'quality_history': self.quality_history[-10:],
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def validate_system_data(self):
        """Validate system data"""
        # Get system data
        system_data = {
            'agents': await self.state_manager.get('active_agents', 0),
            'positions': await self.state_manager.get_all_positions(),
            'market_data': await self.state_manager.get('market_data', {}),
            'performance': await self.state_manager.get('performance', {})
        }
        
        # Validate
        validation = await self.validate_data(system_data)
        
        if not validation['valid']:
            logger.warning(f"⚠️ System data validation issues: {validation['issues']}")
            
    async def validate_data(self, data: Dict) -> Dict:
        """Validate data quality"""
        issues = []
        warnings = []
        
        # Completeness check
        if self.validation_rules['completeness']:
            completeness = await self.check_completeness(data)
            if completeness < self.thresholds['min_completeness']:
                issues.append(f"Completeness low: {completeness:.2f}")
                
        # Freshness check
        if self.validation_rules['freshness']:
            freshness = await self.check_freshness(data)
            if not freshness:
                issues.append("Data stale (>5 minutes)")
                
        # Type safety check
        if self.validation_rules['type_safety']:
            type_issues = await self.check_type_safety(data)
            if type_issues:
                issues.extend(type_issues)
                
        # Null checks
        if self.validation_rules['null_checks']:
            null_issues = await self.check_null_values(data)
            if null_issues:
                warnings.extend(null_issues)
                
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'completeness': await self.check_completeness(data),
            'timestamp': datetime.now().isoformat()
        }
        
    async def check_completeness(self, data: Dict) -> float:
        """Check data completeness"""
        if not data:
            return 0
            
        # Check for required fields
        required_fields = ['timestamp', 'id', 'type']
        fields_present = sum(1 for f in required_fields if f in data)
        
        return fields_present / len(required_fields)
        
    async def check_freshness(self, data: Dict) -> bool:
        """Check data freshness"""
        timestamp = data.get('timestamp')
        if not timestamp:
            return False
            
        try:
            # Parse timestamp
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                return False
                
            # Check age
            age = (datetime.now() - dt).total_seconds()
            return age < self.thresholds['max_freshness_seconds']
            
        except Exception:
            return False
            
    async def check_type_safety(self, data: Dict) -> List[str]:
        """Check type safety"""
        issues = []
        
        # Check value types
        for key, value in data.items():
            if value is None:
                continue
                
            if key in ['price', 'amount', 'size']:
                if not isinstance(value, (int, float)):
                    issues.append(f"{key} should be numeric, got {type(value)}")
                    
            if key in ['id', 'type', 'status']:
                if not isinstance(value, str):
                    issues.append(f"{key} should be string, got {type(value)}")
                    
        return issues
        
    async def check_null_values(self, data: Dict) -> List[str]:
        """Check for null values"""
        issues = []
        
        for key, value in data.items():
            if value is None:
                issues.append(f"{key} is null")
            elif isinstance(value, dict):
                issues.extend(await self.check_null_values(value))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        issues.extend(await self.check_null_values(item))
                        
        return issues
        
    async def update_quality_score(self):
        """Update quality score"""
        # Calculate issues factor
        issue_count = len(self.quality_issues)
        issue_factor = min(1, issue_count / 10)  # 10 issues = 100% penalty
        
        # Calculate completeness factor
        completeness = 1.0
        if self.quality_issues:
            completeness = 1 - (len(self.quality_issues) / 20)  # Max 20 issues
        
        # Quality score
        self.quality_score = max(0, min(100, 100 * (1 - issue_factor) * completeness))
        
        # Store in state
        await self.state_manager.set('quality_score', self.quality_score)
        
        # Record history
        self.quality_history.append({
            'timestamp': datetime.now().isoformat(),
            'score': self.quality_score,
            'issues': len(self.quality_issues)
        })
        if len(self.quality_history) > 100:
            self.quality_history = self.quality_history[-100:]
            
    async def check_quality_threshold(self):
        """Check if quality is too low"""
        if self.quality_score < self.thresholds['min_quality_score']:
            if not self.paused:
                self.paused = True
                logger.warning("⚠️ Quality guard: PAUSING operations (low quality)")
                
                # Publish pause event
                pause_event = Event(
                    event_type="quality_pause",
                    data={
                        'reason': f'Quality score {self.quality_score} below {self.thresholds["min_quality_score"]}',
                        'timestamp': datetime.now().isoformat()
                    },
                    source=self.agent_id
                )
                await self.event_bus.publish(pause_event)
        else:
            if self.paused:
                self.paused = False
                logger.info("Quality guard: RESUMING operations")
                
                # Publish resume event
                resume_event = Event(
                    event_type="quality_resume",
                    data={
                        'reason': f'Quality score {self.quality_score} recovered',
                        'timestamp': datetime.now().isoformat()
                    },
                    source=self.agent_id
                )
                await self.event_bus.publish(resume_event)
                
    async def publish_quality_update(self):
        """Publish quality data update"""
        quality_data = {
            'quality_score': self.quality_score,
            'paused': self.paused,
            'quality_issues': len(self.quality_issues),
            'recent_issues': self.quality_issues[-5:],
            'quality_history': self.quality_history[-5:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="quality_update",
            data=quality_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get quality guard status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'quality_score': self.quality_score,
            'paused': self.paused,
            'quality_issues': len(self.quality_issues),
            'quality_history': len(self.quality_history),
            'timestamp': datetime.now().isoformat()
        }
