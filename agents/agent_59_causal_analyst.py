"""
AlphaEdge Agent 59 – Causal Analyst
Root cause analysis (DoWhy), causal graph, prevention rules, counterfactual simulation
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random
import networkx as nx

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CausalAnalyst:
    """Causal Analyst – Root cause analysis and causal inference"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "causal_analyst"
        self.running = False
        
        # Causal state
        self.causal_graph = nx.DiGraph()
        self.causal_effects = {}
        self.root_causes = []
        self.counterfactual_results = []
        
        # Prevention rules
        self.prevention_rules = []
        
        # Configuration
        self.config = {
            'max_causes': 5,
            'confidence_threshold': 0.7,
            'analysis_window': 100,  # events
            'counterfactual_samples': 10
        }
        
    async def start(self):
        """Start the causal analyst"""
        logger.info("Causal Analyst starting...")
        self.running = True
        
        # Initialize causal graph
        await self.initialize_causal_graph()
        
        # Subscribe to events
        await self.event_bus.subscribe("causal_analysis_request", self.handle_causal_analysis_request)
        await self.event_bus.subscribe("root_cause_request", self.handle_root_cause_request)
        await self.event_bus.subscribe("counterfactual_request", self.handle_counterfactual_request)
        
        # Start analysis cycle
        asyncio.create_task(self.run_analysis_cycle())
        
        logger.info("Causal Analyst running")
        
    async def stop(self):
        """Stop the causal analyst"""
        self.running = False
        logger.info("Causal Analyst stopped")
        
    async def initialize_causal_graph(self):
        """Initialize the causal graph"""
        # Create basic causal structure
        # Nodes represent variables, edges represent causal relationships
        
        # Add nodes
        variables = [
            'market_sentiment', 'macro_conditions', 'technical_indicators',
            'onchain_metrics', 'trading_volume', 'price_movement',
            'execution_quality', 'slippage', 'pnl'
        ]
        
        for var in variables:
            self.causal_graph.add_node(var)
            
        # Add edges (causal relationships)
        edges = [
            ('market_sentiment', 'technical_indicators'),
            ('macro_conditions', 'technical_indicators'),
            ('macro_conditions', 'market_sentiment'),
            ('technical_indicators', 'trading_volume'),
            ('onchain_metrics', 'trading_volume'),
            ('trading_volume', 'price_movement'),
            ('price_movement', 'pnl'),
            ('execution_quality', 'slippage'),
            ('slippage', 'pnl'),
            ('market_sentiment', 'price_movement'),
            ('macro_conditions', 'price_movement')
        ]
        
        for source, target in edges:
            self.causal_graph.add_edge(source, target)
            
        # Store graph
        await self.state_manager.set('causal_graph', 
            nx.node_link_data(self.causal_graph))
            
    async def run_analysis_cycle(self):
        """Run regular analysis cycle"""
        while self.running:
            try:
                # Analyze recent events
                await self.analyze_causal_relationships()
                
                # Update root causes
                await self.update_root_causes()
                
                # Update prevention rules
                await self.update_prevention_rules()
                
                # Publish causal update
                await self.publish_causal_update()
                
            except Exception as e:
                logger.error(f"Causal analysis cycle error: {e}")
                
            await asyncio.sleep(300)  # Every 5 minutes
            
    async def handle_causal_analysis_request(self, event: Event):
        """Handle causal analysis requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        data = event.data.get('data', {})
        
        # Perform causal analysis
        result = await self.perform_causal_analysis(data)
        
        response = Event(
            event_type="causal_analysis_response",
            data={
                'request_id': request_id,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_root_cause_request(self, event: Event):
        """Handle root cause requests"""
        if not self.running:
            return
            
        event_data = event.data.get('event')
        
        # Find root causes
        root_causes = await self.find_root_causes(event_data)
        
        response = Event(
            event_type="root_cause_response",
            data={
                'event': event_data,
                'root_causes': root_causes,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_counterfactual_request(self, event: Event):
        """Handle counterfactual requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        scenario = event.data.get('scenario')
        intervention = event.data.get('intervention')
        
        # Run counterfactual simulation
        result = await self.run_counterfactual(scenario, intervention)
        
        response = Event(
            event_type="counterfactual_response",
            data={
                'request_id': request_id,
                'scenario': scenario,
                'intervention': intervention,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def perform_causal_analysis(self, data: Dict) -> Dict:
        """Perform causal analysis on data"""
        # Identify variables
        variables = list(data.keys())
        
        # Calculate correlations
        correlations = {}
        for var1 in variables:
            for var2 in variables:
                if var1 != var2 and var1 in data and var2 in data:
                    # Simulate correlation calculation
                    corr = self.simulate_correlation(data[var1], data[var2])
                    correlations[f"{var1}_{var2}"] = corr
                    
        # Identify potential causal relationships
        causal_effects = {}
        for var in variables:
            if var in self.causal_graph.nodes:
                # Find ancestors (causes)
                ancestors = nx.ancestors(self.causal_graph, var)
                causes = []
                
                for ancestor in ancestors:
                    if ancestor in data:
                        # Calculate causal effect (simplified)
                        effect = self.estimate_causal_effect(
                            data[ancestor], data[var]
                        )
                        if abs(effect) > 0.1:  # Non-negligible effect
                            causes.append({
                                'variable': ancestor,
                                'effect': effect,
                                'confidence': random.uniform(0.6, 0.9)
                            })
                            
                causal_effects[var] = sorted(
                    causes,
                    key=lambda x: abs(x['effect']),
                    reverse=True
                )
                
        return {
            'correlations': correlations,
            'causal_effects': causal_effects,
            'causal_graph': nx.node_link_data(self.causal_graph)
        }
        
    def simulate_correlation(self, series1: List, series2: List) -> float:
        """Simulate correlation between two series"""
        # In production, use actual correlation calculation
        # For now, simulate
        return random.uniform(-0.8, 0.8)
        
    def estimate_causal_effect(self, cause: List, effect: List) -> float:
        """Estimate causal effect between two variables"""
        # In production, use DoWhy or similar
        # For now, simulate
        return random.uniform(-0.5, 0.5)
        
    async def find_root_causes(self, event_data: Dict) -> List:
        """Find root causes of an event"""
        # Identify variables involved
        variables = list(event_data.keys())
        
        # Find root causes for each variable
        root_causes = []
        
        for var in variables:
            if var in self.causal_graph.nodes:
                # Find ancestors
                ancestors = nx.ancestors(self.causal_graph, var)
                if ancestors:
                    # Find root cause (top-level ancestor)
                    root = self.find_top_level_ancestor(var)
                    if root and root != var:
                        root_causes.append({
                            'variable': var,
                            'root_cause': root,
                            'path': nx.shortest_path(self.causal_graph, root, var),
                            'confidence': random.uniform(0.5, 0.9)
                        })
                        
        # Sort by confidence
        root_causes.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Keep top N
        self.root_causes = root_causes[:self.config['max_causes']]
        
        return self.root_causes
        
    def find_top_level_ancestor(self, node: str) -> Optional[str]:
        """Find top-level ancestor of a node"""
        ancestors = list(nx.ancestors(self.causal_graph, node))
        if not ancestors:
            return None
            
        # Find node with no ancestors in the set
        for ancestor in ancestors:
            if not any(a in self.causal_graph.successors(ancestor) for a in ancestors):
                return ancestor
                
        return ancestors[0] if ancestors else None
        
    async def run_counterfactual(self, scenario: Dict, intervention: Dict) -> Dict:
        """Run counterfactual simulation"""
        results = []
        
        for _ in range(self.config['counterfactual_samples']):
            # Simulate counterfactual
            result = self.simulate_counterfactual(scenario, intervention)
            results.append(result)
            
        # Analyze results
        success_rate = sum(1 for r in results if r['success']) / len(results)
        
        counterfactual_result = {
            'success_rate': success_rate,
            'sample_results': results,
            'recommendation': 'intervene' if success_rate > 0.7 else 'avoid_intervention',
            'timestamp': datetime.now().isoformat()
        }
        
        self.counterfactual_results.append(counterfactual_result)
        
        return counterfactual_result
        
    def simulate_counterfactual(self, scenario: Dict, intervention: Dict) -> Dict:
        """Simulate a single counterfactual scenario"""
        # Simulate outcome with and without intervention
        base_outcome = random.uniform(0.3, 0.7)
        intervention_effect = random.uniform(-0.3, 0.3)
        
        if intervention.get('type') == 'increase':
            intervention_effect = abs(intervention_effect)
        elif intervention.get('type') == 'decrease':
            intervention_effect = -abs(intervention_effect)
            
        new_outcome = base_outcome + intervention_effect
        success = new_outcome > base_outcome
        
        return {
            'base_outcome': base_outcome,
            'new_outcome': new_outcome,
            'intervention_effect': intervention_effect,
            'success': success
        }
        
    async def update_prevention_rules(self):
        """Update prevention rules based on causal analysis"""
        new_rules = []
        
        for cause in self.root_causes[:5]:
            if cause['confidence'] > self.config['confidence_threshold']:
                rule = {
                    'condition': f"if {cause['root_cause']} exceeds threshold",
                    'action': f"monitor {cause['variable']}",
                    'confidence': cause['confidence'],
                    'timestamp': datetime.now().isoformat()
                }
                new_rules.append(rule)
                
        # Update rules
        self.prevention_rules = new_rules
        
        # Store in state
        await self.state_manager.set('prevention_rules', self.prevention_rules)
        
    async def publish_causal_update(self):
        """Publish causal data update"""
        causal_data = {
            'causal_graph': nx.node_link_data(self.causal_graph),
            'root_causes': self.root_causes,
            'prevention_rules': self.prevention_rules,
            'counterfactual_results': self.counterfactual_results[-5:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="causal_update",
            data=causal_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get causal analyst status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'causal_graph_nodes': len(self.causal_graph.nodes),
            'causal_graph_edges': len(self.causal_graph.edges),
            'root_causes': len(self.root_causes),
            'counterfactual_results': len(self.counterfactual_results),
            'timestamp': datetime.now().isoformat()
        }
