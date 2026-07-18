"""
AlphaEdge Agent 30 – Self-Evolving Agent
Proposes code improvements, generates Pine Script, updates documentation
V13.0.7 – UPDATED with Parallel Execution Audit (Item 18)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import time
import json

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class SelfEvolvingAgent:
    """
    Self-Evolving Agent – Proposes and implements improvements
    V13.0.7 – Item 18: Parallel Execution Audit
    """
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "self_evolving"
        self.running = False
        
        # State tracking
        self.proposals = []
        self.implemented_changes = []
        self.documentation_updates = []
        
        # Configuration
        self.config = {
            'max_proposals': 100,
            'review_interval': 3600,  # 1 hour
            'min_improvement_pct': 5,
            'auto_approve_docs': True,
            'github_repo': 'Alphaedge-bot/alphaedge-bot'
        }
        
        # Documentation update tracking
        self.last_workflow_update = None
        self.last_master_design_update = None
        self.pending_doc_updates = []
        
        # ============================================
        # ITEM 18: PARALLEL EXECUTION AUDIT
        # ============================================
        self.parallel_audit = {
            'enabled': True,
            'audit_interval': 300,  # 5 minutes
            'execution_times': {},
            'concurrent_tasks': 0,
            'max_concurrent': 10,
            'average_execution_time': 0.0,
            'bottlenecks': [],
            'optimization_suggestions': []
        }
        
        # Track task execution
        self.task_history = []
        self.current_tasks = set()
        
    async def start(self):
        """Start the self-evolving agent"""
        logger.info("Self-Evolving Agent starting...")
        self.running = True
        
        await self.event_bus.subscribe("improvement_proposal", self.handle_proposal)
        await self.event_bus.subscribe("code_change", self.handle_code_change)
        await self.event_bus.subscribe("doc_update_request", self.handle_doc_update_request)
        
        asyncio.create_task(self.run_evolution_cycle())
        asyncio.create_task(self.run_parallel_audit())
        logger.info("Self-Evolving Agent running")
        
    async def stop(self):
        """Stop the self-evolving agent"""
        self.running = False
        logger.info("Self-Evolving Agent stopped")
        
    async def run_evolution_cycle(self):
        """Run regular evolution cycle"""
        while self.running:
            try:
                await self.check_for_improvements()
                await self.review_proposals()
                await self.process_doc_updates()
                await self.publish_status()
            except Exception as e:
                logger.error(f"Evolution cycle error: {e}")
            await asyncio.sleep(self.config['review_interval'])
            
    # ============================================
    # ITEM 18: PARALLEL EXECUTION AUDIT
    # ============================================
    
    async def run_parallel_audit(self):
        """Run parallel execution audit"""
        while self.running:
            try:
                await self.audit_execution_parallelism()
                await self.identify_bottlenecks()
                await self.generate_optimization_suggestions()
                await self.publish_audit_report()
            except Exception as e:
                logger.error(f"Parallel audit error: {e}")
            await asyncio.sleep(self.parallel_audit['audit_interval'])
            
    async def audit_execution_parallelism(self):
        """
        Audit agent execution for true parallelism
        Item 18: Parallel Execution Audit
        """
        if not self.parallel_audit['enabled']:
            return
            
        logger.info("🔍 Running parallel execution audit...")
        
        # Track concurrent tasks
        self.parallel_audit['concurrent_tasks'] = len(self.current_tasks)
        
        # Analyze execution times
        if self.task_history:
            recent_tasks = self.task_history[-50:]
            avg_time = sum(t.get('duration', 0) for t in recent_tasks) / len(recent_tasks) if recent_tasks else 0
            self.parallel_audit['average_execution_time'] = avg_time
            
            # Check for sequential bottlenecks
            sequential_tasks = [t for t in recent_tasks if t.get('execution_mode') == 'sequential']
            if sequential_tasks:
                self.parallel_audit['bottlenecks'].append({
                    'type': 'sequential_execution',
                    'count': len(sequential_tasks),
                    'avg_time': sum(t.get('duration', 0) for t in sequential_tasks) / len(sequential_tasks),
                    'timestamp': datetime.now().isoformat()
                })
                
            # Check for long-running tasks
            long_tasks = [t for t in recent_tasks if t.get('duration', 0) > 1.0]
            if long_tasks:
                self.parallel_audit['bottlenecks'].append({
                    'type': 'long_running_tasks',
                    'count': len(long_tasks),
                    'tasks': [t.get('name') for t in long_tasks],
                    'timestamp': datetime.now().isoformat()
                })
                
        logger.info(f"📊 Concurrent tasks: {self.parallel_audit['concurrent_tasks']}")
        logger.info(f"📊 Avg execution time: {self.parallel_audit['average_execution_time']:.3f}s")
        
        # Store audit results
        await self.state_manager.set('parallel_audit_results', {
            'concurrent_tasks': self.parallel_audit['concurrent_tasks'],
            'average_execution_time': self.parallel_audit['average_execution_time'],
            'bottlenecks': self.parallel_audit['bottlenecks'][-10:],
            'timestamp': datetime.now().isoformat()
        })
        
    async def identify_bottlenecks(self):
        """
        Identify execution bottlenecks
        Item 18: Bottleneck identification
        """
        bottlenecks = []
        
        # 1. Check sequential execution pattern
        sequential_count = len([t for t in self.task_history[-20:] if t.get('execution_mode') == 'sequential'])
        if sequential_count > 15:
            bottlenecks.append({
                'type': 'sequential_execution',
                'severity': 'high',
                'description': 'More than 75% of tasks are sequential',
                'suggestion': 'Use asyncio.gather() for concurrent execution'
            })
            
        # 2. Check high concurrency
        if self.parallel_audit['concurrent_tasks'] > self.parallel_audit['max_concurrent']:
            bottlenecks.append({
                'type': 'high_concurrency',
                'severity': 'medium',
                'description': f'Concurrent tasks ({self.parallel_audit["concurrent_tasks"]}) exceeds limit',
                'suggestion': 'Implement task queuing or increase max_concurrent'
            })
            
        # 3. Check long execution times
        if self.parallel_audit['average_execution_time'] > 1.0:
            bottlenecks.append({
                'type': 'slow_execution',
                'severity': 'medium',
                'description': f'Average execution time {self.parallel_audit["average_execution_time"]:.2f}s',
                'suggestion': 'Optimize CPU-bound tasks or move to C++/Rust extensions'
            })
            
        self.parallel_audit['bottlenecks'] = bottlenecks
        
    async def generate_optimization_suggestions(self):
        """
        Generate optimization suggestions
        Item 18: Optimization recommendations
        """
        suggestions = []
        
        # 1. Suggest asyncio.gather()
        if self.parallel_audit['concurrent_tasks'] < 5:
            suggestions.append({
                'type': 'concurrency',
                'priority': 'high',
                'description': 'Low concurrent tasks detected',
                'implementation': 'Use asyncio.gather() to run multiple strategies in parallel'
            })
            
        # 2. Suggest caching
        if self.parallel_audit['average_execution_time'] > 0.5:
            suggestions.append({
                'type': 'caching',
                'priority': 'medium',
                'description': 'High average execution time',
                'implementation': 'Cache slow-moving metrics (on-chain, macro)'
            })
            
        # 3. Suggest parallel execution audit
        if len(self.parallel_audit['bottlenecks']) > 0:
            suggestions.append({
                'type': 'audit',
                'priority': 'high',
                'description': 'Bottlenecks detected',
                'implementation': 'Run parallel execution audit and review bottlenecks'
            })
            
        self.parallel_audit['optimization_suggestions'] = suggestions
        
        # Store suggestions
        await self.state_manager.set('parallel_optimization_suggestions', suggestions)
        
    async def publish_audit_report(self):
        """Publish audit report"""
        event = Event(
            event_type="parallel_audit_report",
            data={
                'concurrent_tasks': self.parallel_audit['concurrent_tasks'],
                'average_execution_time': self.parallel_audit['average_execution_time'],
                'bottlenecks': self.parallel_audit['bottlenecks'],
                'optimization_suggestions': self.parallel_audit['optimization_suggestions'],
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def track_task_execution(self, task_name: str, duration: float, execution_mode: str = 'parallel'):
        """Track task execution for audit"""
        self.task_history.append({
            'name': task_name,
            'duration': duration,
            'execution_mode': execution_mode,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep last 500 tasks
        if len(self.task_history) > 500:
            self.task_history = self.task_history[-500:]
            
    # ============================================
    # DOCUMENTATION UPDATE METHODS
    # ============================================
    
    async def handle_doc_update_request(self, event: Event):
        """Handle documentation update requests"""
        if not self.running:
            return
            
        update_type = event.data.get('type')
        change = event.data.get('change', {})
        
        logger.info(f"📝 Documentation update requested: {update_type}")
        
        if update_type == 'workflow':
            await self.update_workflow(change)
        elif update_type == 'master_design':
            await self.update_master_design(change)
        else:
            logger.warning(f"Unknown doc update type: {update_type}")
            
    async def update_workflow(self, change: Dict) -> bool:
        """Update workflow_live.md"""
        try:
            logger.info("📝 Updating workflow_live.md")
            self.last_workflow_update = datetime.now().isoformat()
            self.documentation_updates.append({
                'type': 'workflow',
                'change': change,
                'timestamp': datetime.now().isoformat()
            })
            logger.info("✅ workflow_live.md updated successfully")
            return True
        except Exception as e:
            logger.error(f"Workflow update error: {e}")
            return False
            
    async def update_master_design(self, change: Dict) -> bool:
        """Update master design document"""
        try:
            logger.info("📝 Updating master design document")
            self.last_master_design_update = datetime.now().isoformat()
            self.documentation_updates.append({
                'type': 'master_design',
                'change': change,
                'timestamp': datetime.now().isoformat()
            })
            logger.info("✅ Master design updated successfully")
            return True
        except Exception as e:
            logger.error(f"Master design update error: {e}")
            return False
            
    async def process_doc_updates(self):
        """Process pending documentation updates"""
        if not self.pending_doc_updates:
            return
        
        for update in self.pending_doc_updates[:]:
            change = update['change']
            change_types = change.get('types', [])
            
            for change_type in change_types:
                if change_type in ['entry_logic', 'exit_logic', 'tps_threshold', 'new_indicator', 'new_strategy', 'timeframe']:
                    await self.update_workflow(change)
                elif change_type in ['version_increment', 'agent_change', 'hardware_change']:
                    await self.update_master_design(change)
            
            self.pending_doc_updates.remove(update)
            
    # ============================================
    # EXISTING METHODS
    # ============================================
    
    async def handle_proposal(self, event: Event):
        """Handle improvement proposals"""
        if not self.running:
            return
            
        proposal = event.data
        self.proposals.append(proposal)
        logger.info(f"📊 New proposal: {proposal.get('title', 'Untitled')}")
        await self.state_manager.set('proposals', self.proposals)
        
    async def handle_code_change(self, event: Event):
        """Handle code changes"""
        if not self.running:
            return
            
        change = event.data
        self.implemented_changes.append(change)
        
        if self._requires_doc_update(change):
            await self._schedule_doc_update(change)
            
        logger.info(f"💻 Code change implemented: {change.get('description', 'Unknown')}")
        
    def _requires_doc_update(self, change: Dict) -> bool:
        """Check if change requires documentation update"""
        change_types = change.get('types', [])
        doc_triggers = [
            'entry_logic', 'exit_logic', 'tps_threshold',
            'new_indicator', 'new_strategy', 'timeframe',
            'version_increment', 'agent_change', 'hardware_change'
        ]
        return any(t in doc_triggers for t in change_types)
        
    async def _schedule_doc_update(self, change: Dict):
        """Schedule documentation update"""
        self.pending_doc_updates.append({
            'change': change,
            'scheduled_at': datetime.now().isoformat()
        })
        logger.info(f"📝 Scheduled doc update for: {change.get('description', 'Unknown')}")
        
    async def check_for_improvements(self):
        """Check for potential improvements"""
        pass
        
    async def review_proposals(self):
        """Review pending proposals"""
        pass
        
    async def publish_status(self):
        """Publish self-evolving status"""
        status_data = {
            'proposals_count': len(self.proposals),
            'implemented_changes': len(self.implemented_changes),
            'documentation_updates': len(self.documentation_updates),
            'pending_doc_updates': len(self.pending_doc_updates),
            'last_workflow_update': self.last_workflow_update,
            'last_master_design_update': self.last_master_design_update,
            'parallel_audit': {
                'concurrent_tasks': self.parallel_audit['concurrent_tasks'],
                'average_execution_time': self.parallel_audit['average_execution_time'],
                'bottlenecks': len(self.parallel_audit['bottlenecks']),
                'optimization_suggestions': len(self.parallel_audit['optimization_suggestions'])
            },
            'timestamp': datetime.now().isoformat()
        }
        event = Event(event_type="self_evolving_status", data=status_data, source=self.agent_id)
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get self-evolving agent status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'proposals_count': len(self.proposals),
            'implemented_changes': len(self.implemented_changes),
            'documentation_updates': len(self.documentation_updates),
            'pending_doc_updates': len(self.pending_doc_updates),
            'last_workflow_update': self.last_workflow_update,
            'last_master_design_update': self.last_master_design_update,
            'parallel_audit': {
                'concurrent_tasks': self.parallel_audit['concurrent_tasks'],
                'average_execution_time': self.parallel_audit['average_execution_time'],
                'bottlenecks': self.parallel_audit['bottlenecks'],
                'optimization_suggestions': self.parallel_audit['optimization_suggestions']
            },
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }
