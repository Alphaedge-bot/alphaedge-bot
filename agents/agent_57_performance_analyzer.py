"""
AlphaEdge Agent 57 – Performance Analyzer
Real-time attribution, per-strategy P&L, per-agent contribution, win rate by regime
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import statistics

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """Performance Analyzer – Real-time performance analysis and attribution"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "performance_analyzer"
        self.running = False
        
        # Performance data
        self.strategy_performance = {}
        self.agent_performance = {}
        self.regime_performance = {}
        self.realtime_metrics = {}
        
        # Historical data
        self.performance_history = []
        self.daily_snapshots = []
        
        # Configuration
        self.config = {
            'attribution_window': 30,  # days
            'min_trades_for_analysis': 10,
            'update_interval': 60,  # seconds
            'snapshot_time': 0  # midnight UTC
        }
        
    async def start(self):
        """Start the performance analyzer"""
        logger.info("Performance Analyzer starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("performance_request", self.handle_performance_request)
        await self.event_bus.subscribe("trade_update", self.handle_trade_update)
        await self.event_bus.subscribe("analysis_request", self.handle_analysis_request)
        
        # Start analysis cycle
        asyncio.create_task(self.run_analysis_cycle())
        
        logger.info("Performance Analyzer running")
        
    async def stop(self):
        """Stop the performance analyzer"""
        self.running = False
        logger.info("Performance Analyzer stopped")
        
    async def run_analysis_cycle(self):
        """Run regular analysis cycle"""
        last_snapshot = datetime.now()
        
        while self.running:
            try:
                # Update performance metrics
                await self.update_performance_metrics()
                
                # Calculate attribution
                await self.calculate_attribution()
                
                # Take daily snapshot
                if datetime.now().date() > last_snapshot.date():
                    await self.take_snapshot()
                    last_snapshot = datetime.now()
                    
                # Publish performance update
                await self.publish_performance_update()
                
            except Exception as e:
                logger.error(f"Analysis cycle error: {e}")
                
            await asyncio.sleep(self.config['update_interval'])
            
    async def handle_performance_request(self, event: Event):
        """Handle performance requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        metric = event.data.get('metric')
        period = event.data.get('period', 'daily')
        
        if metric == 'all':
            result = await self.get_all_performance(period)
        else:
            result = await self.get_specific_performance(metric, period)
            
        response = Event(
            event_type="performance_response",
            data={
                'request_id': request_id,
                'metric': metric,
                'period': period,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_trade_update(self, event: Event):
        """Handle trade updates"""
        if not self.running:
            return
            
        trade = event.data
        
        # Update strategy performance
        strategy = trade.get('strategy', 'unknown')
        if strategy not in self.strategy_performance:
            self.strategy_performance[strategy] = {
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'pnl': 0,
                'win_rate': 0
            }
            
        pnl = trade.get('pnl', 0)
        self.strategy_performance[strategy]['trades'] += 1
        self.strategy_performance[strategy]['pnl'] += pnl
        if pnl > 0:
            self.strategy_performance[strategy]['wins'] += 1
        else:
            self.strategy_performance[strategy]['losses'] += 1
            
        # Update win rate
        total = self.strategy_performance[strategy]['trades']
        wins = self.strategy_performance[strategy]['wins']
        self.strategy_performance[strategy]['win_rate'] = wins / total if total > 0 else 0
        
        # Update agent performance
        agent = trade.get('agent', 'unknown')
        if agent not in self.agent_performance:
            self.agent_performance[agent] = {
                'trades': 0,
                'pnl': 0,
                'accuracy': 0,
                'avg_score': 0
            }
            
        self.agent_performance[agent]['trades'] += 1
        self.agent_performance[agent]['pnl'] += pnl
        
        # Update regime performance
        regime = trade.get('regime', 'neutral')
        if regime not in self.regime_performance:
            self.regime_performance[regime] = {
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'pnl': 0,
                'win_rate': 0
            }
            
        self.regime_performance[regime]['trades'] += 1
        self.regime_performance[regime]['pnl'] += pnl
        if pnl > 0:
            self.regime_performance[regime]['wins'] += 1
        else:
            self.regime_performance[regime]['losses'] += 1
            
        total = self.regime_performance[regime]['trades']
        wins = self.regime_performance[regime]['wins']
        self.regime_performance[regime]['win_rate'] = wins / total if total > 0 else 0
        
    async def update_performance_metrics(self):
        """Update real-time performance metrics"""
        # Calculate overall metrics
        total_trades = sum(s['trades'] for s in self.strategy_performance.values())
        total_pnl = sum(s['pnl'] for s in self.strategy_performance.values())
        
        # Calculate win rate
        wins = sum(s['wins'] for s in self.strategy_performance.values())
        win_rate = wins / total_trades if total_trades > 0 else 0
        
        # Calculate average PnL
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        
        # Calculate Sharpe ratio (simplified)
        returns = []
        for strategy in self.strategy_performance.values():
            if strategy['trades'] > 0:
                returns.append(strategy['pnl'] / strategy['trades'])
                
        sharpe = 0
        if len(returns) > 1:
            avg_return = statistics.mean(returns)
            std_return = statistics.stdev(returns)
            sharpe = avg_return / std_return if std_return > 0 else 0
            
        self.realtime_metrics = {
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'sharpe_ratio': sharpe,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in state
        await self.state_manager.set('realtime_metrics', self.realtime_metrics)
        
    async def calculate_attribution(self):
        """Calculate performance attribution"""
        attribution = {
            'top_strategies': [],
            'top_agents': [],
            'best_regime': None,
            'worst_regime': None
        }
        
        # Top strategies by PnL
        if self.strategy_performance:
            sorted_strategies = sorted(
                self.strategy_performance.items(),
                key=lambda x: x[1]['pnl'],
                reverse=True
            )
            attribution['top_strategies'] = sorted_strategies[:5]
            
        # Top agents by PnL
        if self.agent_performance:
            sorted_agents = sorted(
                self.agent_performance.items(),
                key=lambda x: x[1]['pnl'],
                reverse=True
            )
            attribution['top_agents'] = sorted_agents[:5]
            
        # Best and worst regimes
        if self.regime_performance:
            sorted_regimes = sorted(
                self.regime_performance.items(),
                key=lambda x: x[1]['win_rate'],
                reverse=True
            )
            if sorted_regimes:
                attribution['best_regime'] = sorted_regimes[0][0]
                attribution['worst_regime'] = sorted_regimes[-1][0]
                
        # Store in state
        await self.state_manager.set('attribution_data', attribution)
        
    async def take_snapshot(self):
        """Take daily performance snapshot"""
        snapshot = {
            'date': datetime.now().date().isoformat(),
            'metrics': self.realtime_metrics.copy(),
            'strategy_performance': self.strategy_performance.copy(),
            'agent_performance': self.agent_performance.copy(),
            'regime_performance': self.regime_performance.copy(),
            'timestamp': datetime.now().isoformat()
        }
        
        self.daily_snapshots.append(snapshot)
        if len(self.daily_snapshots) > 365:  # Keep 1 year
            self.daily_snapshots = self.daily_snapshots[-365:]
            
        # Store in state
        await self.state_manager.set('daily_snapshots', self.daily_snapshots)
        
    async def get_all_performance(self, period: str) -> Dict:
        """Get all performance metrics for a period"""
        # Determine date range
        end_date = datetime.now()
        if period == 'daily':
            start_date = end_date - timedelta(days=1)
        elif period == 'weekly':
            start_date = end_date - timedelta(weeks=1)
        elif period == 'monthly':
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=self.config['attribution_window'])
            
        # Filter snapshots
        filtered = []
        for snapshot in self.daily_snapshots:
            snapshot_date = datetime.fromisoformat(snapshot['date']).date()
            if start_date.date() <= snapshot_date <= end_date.date():
                filtered.append(snapshot)
                
        return {
            'period': period,
            'snapshots': filtered,
            'realtime_metrics': self.realtime_metrics,
            'attribution': await self.state_manager.get('attribution_data', {}),
            'timestamp': datetime.now().isoformat()
        }
        
    async def get_specific_performance(self, metric: str, period: str) -> Dict:
        """Get specific performance metric"""
        if metric == 'strategies':
            return {'strategies': self.strategy_performance}
        elif metric == 'agents':
            return {'agents': self.agent_performance}
        elif metric == 'regimes':
            return {'regimes': self.regime_performance}
        elif metric == 'overall':
            return {'metrics': self.realtime_metrics}
        else:
            return {'error': 'unknown_metric'}
            
    async def handle_analysis_request(self, event: Event):
        """Handle analysis requests"""
        if not self.running:
            return
            
        analysis_type = event.data.get('type')
        
        if analysis_type == 'attribution':
            result = await self.calculate_attribution()
        else:
            result = {'status': 'unknown_analysis'}
            
        response = Event(
            event_type="analysis_response",
            data={
                'type': analysis_type,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def publish_performance_update(self):
        """Publish performance data update"""
        performance_data = {
            'realtime_metrics': self.realtime_metrics,
            'attribution': await self.state_manager.get('attribution_data', {}),
            'strategy_count': len(self.strategy_performance),
            'agent_count': len(self.agent_performance),
            'regime_count': len(self.regime_performance),
            'daily_snapshots': self.daily_snapshots[-7:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="performance_update",
            data=performance_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get performance analyzer status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'strategy_count': len(self.strategy_performance),
            'agent_count': len(self.agent_performance),
            'regime_count': len(self.regime_performance),
            'daily_snapshots': len(self.daily_snapshots),
            'timestamp': datetime.now().isoformat()
        }
