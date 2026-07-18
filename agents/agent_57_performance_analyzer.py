"""
AlphaEdge Agent 57 – Performance Analyzer
Real-time attribution, per-strategy P&L, per-agent contribution, win rate by regime
V13.0.7 – UPDATED with Performance Metrics Dashboard (Item 8)
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
    """
    Performance Analyzer – Tracks and analyzes bot performance
    V13.0.7 – Item 8: Performance Metrics Dashboard
    """
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "performance_analyzer"
        self.running = False
        
        # Performance data
        self.trade_history = []
        self.strategy_performance = {}
        self.agent_contributions = {}
        
        # ============================================
        # ITEM 8: PERFORMANCE METRICS
        # ============================================
        self.metrics = {
            'profit_factor': 0.0,
            'expectancy': 0.0,
            'sharpe_ratio': 0.0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'max_drawdown': 0.0,
            'current_drawdown': 0.0,
            'regime_performance': {
                'bull': {'win_rate': 0.0, 'avg_return': 0.0, 'trades': 0},
                'bear': {'win_rate': 0.0, 'avg_return': 0.0, 'trades': 0},
                'neutral': {'win_rate': 0.0, 'avg_return': 0.0, 'trades': 0}
            },
            'tier_performance': {
                'micro_cap': {'win_rate': 0.0, 'avg_return': 0.0, 'trades': 0},
                'small_cap': {'win_rate': 0.0, 'avg_return': 0.0, 'trades': 0},
                'mid_cap': {'win_rate': 0.0, 'avg_return': 0.0, 'trades': 0}
            },
            'last_updated': None
        }
        
        # Rolling windows
        self.window_sizes = {
            'short': 10,
            'medium': 50,
            'long': 100
        }
        
    async def start(self):
        """Start the performance analyzer"""
        logger.info("Performance Analyzer starting...")
        self.running = True
        
        await self.event_bus.subscribe("trade_completed", self.handle_trade_completed)
        await self.event_bus.subscribe("performance_request", self.handle_performance_request)
        await self.event_bus.subscribe("strategy_update", self.handle_strategy_update)
        
        asyncio.create_task(self.run_analysis_cycle())
        logger.info("Performance Analyzer running")
        
    async def stop(self):
        """Stop the performance analyzer"""
        self.running = False
        logger.info("Performance Analyzer stopped")
        
    async def run_analysis_cycle(self):
        """Run regular analysis cycle"""
        while self.running:
            try:
                await self.update_metrics()
                await self.publish_performance_update()
            except Exception as e:
                logger.error(f"Analysis cycle error: {e}")
            await asyncio.sleep(60)
            
    # ============================================
    # ITEM 8: METRICS CALCULATION
    # ============================================
    
    async def update_metrics(self):
        """Update all performance metrics"""
        if not self.trade_history:
            return
            
        # Get recent trades
        trades = self.trade_history[-100:]  # Last 100 trades
        
        if len(trades) < 5:
            return
            
        # 1. Win Rate
        wins = [t for t in trades if t.get('pnl', 0) > 0]
        losses = [t for t in trades if t.get('pnl', 0) <= 0]
        self.metrics['win_rate'] = len(wins) / len(trades) if trades else 0
        
        # 2. Average Win/Loss
        self.metrics['avg_win'] = sum(t.get('pnl', 0) for t in wins) / len(wins) if wins else 0
        self.metrics['avg_loss'] = abs(sum(t.get('pnl', 0) for t in losses) / len(losses)) if losses else 0
        
        # 3. Profit Factor
        gross_profit = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0)
        gross_loss = abs(sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0))
        self.metrics['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # 4. Expectancy
        expectancy = (self.metrics['win_rate'] * self.metrics['avg_win']) - ((1 - self.metrics['win_rate']) * self.metrics['avg_loss'])
        self.metrics['expectancy'] = expectancy
        
        # 5. Sharpe Ratio
        returns = [t.get('return_pct', 0) for t in trades]
        if len(returns) > 1 and statistics.stdev(returns) > 0:
            self.metrics['sharpe_ratio'] = (sum(returns) / len(returns)) / statistics.stdev(returns)
        else:
            self.metrics['sharpe_ratio'] = 0
            
        # 6. Drawdown
        self.metrics['max_drawdown'] = await self._calculate_max_drawdown()
        self.metrics['current_drawdown'] = await self._calculate_current_drawdown()
        
        # 7. Regime Performance
        await self._update_regime_performance()
        
        # 8. Tier Performance
        await self._update_tier_performance()
        
        # 9. Update timestamp
        self.metrics['last_updated'] = datetime.now().isoformat()
        
        # Store in state
        await self.state_manager.set('performance_metrics', self.metrics)
        
    async def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if not self.trade_history:
            return 0.0
            
        peak = 0
        max_dd = 0
        cumulative = 0
        
        for trade in self.trade_history[-100:]:
            cumulative += trade.get('pnl', 0)
            if cumulative > peak:
                peak = cumulative
            dd = (peak - cumulative) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
                
        return max_dd
        
    async def _calculate_current_drawdown(self) -> float:
        """Calculate current drawdown"""
        if not self.trade_history:
            return 0.0
            
        cumulative = sum(t.get('pnl', 0) for t in self.trade_history[-100:])
        peak = max(sum(t.get('pnl', 0) for t in self.trade_history[:i]) for i in range(1, len(self.trade_history)+1))
        
        return (peak - cumulative) / peak if peak > 0 else 0
        
    async def _update_regime_performance(self):
        """Update performance by market regime"""
        regimes = ['bull', 'bear', 'neutral']
        for regime in regimes:
            trades = [t for t in self.trade_history[-100:] if t.get('regime') == regime]
            if trades:
                wins = [t for t in trades if t.get('pnl', 0) > 0]
                self.metrics['regime_performance'][regime]['win_rate'] = len(wins) / len(trades) if trades else 0
                self.metrics['regime_performance'][regime]['avg_return'] = sum(t.get('return_pct', 0) for t in trades) / len(trades) if trades else 0
                self.metrics['regime_performance'][regime]['trades'] = len(trades)
                
    async def _update_tier_performance(self):
        """Update performance by cap tier"""
        tiers = ['micro_cap', 'small_cap', 'mid_cap']
        for tier in tiers:
            trades = [t for t in self.trade_history[-100:] if t.get('tier') == tier]
            if trades:
                wins = [t for t in trades if t.get('pnl', 0) > 0]
                self.metrics['tier_performance'][tier]['win_rate'] = len(wins) / len(trades) if trades else 0
                self.metrics['tier_performance'][tier]['avg_return'] = sum(t.get('return_pct', 0) for t in trades) / len(trades) if trades else 0
                self.metrics['tier_performance'][tier]['trades'] = len(trades)
                
    # ============================================
    # EVENT HANDLERS
    # ============================================
    
    async def handle_trade_completed(self, event: Event):
        """Handle trade completed events"""
        if not self.running:
            return
            
        trade_data = event.data
        self.trade_history.append(trade_data)
        
        # Keep last 1000 trades
        if len(self.trade_history) > 1000:
            self.trade_history = self.trade_history[-1000:]
            
        # Update strategy performance
        strategy = trade_data.get('strategy', 'unknown')
        if strategy not in self.strategy_performance:
            self.strategy_performance[strategy] = {'wins': 0, 'losses': 0, 'total_pnl': 0, 'trades': 0}
        
        pnl = trade_data.get('pnl', 0)
        self.strategy_performance[strategy]['trades'] += 1
        self.strategy_performance[strategy]['total_pnl'] += pnl
        if pnl > 0:
            self.strategy_performance[strategy]['wins'] += 1
        else:
            self.strategy_performance[strategy]['losses'] += 1
            
        # Update agent contribution
        agent = trade_data.get('agent', 'unknown')
        if agent not in self.agent_contributions:
            self.agent_contributions[agent] = {'wins': 0, 'losses': 0, 'total_pnl': 0, 'trades': 0}
        
        self.agent_contributions[agent]['trades'] += 1
        self.agent_contributions[agent]['total_pnl'] += pnl
        if pnl > 0:
            self.agent_contributions[agent]['wins'] += 1
        else:
            self.agent_contributions[agent]['losses'] += 1
            
    async def handle_performance_request(self, event: Event):
        """Handle performance requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        metric = event.data.get('metric', 'all')
        
        if metric == 'all':
            data = self.metrics
        elif metric in self.metrics:
            data = self.metrics[metric]
        else:
            data = {'error': f'Metric not found: {metric}'}
            
        response = Event(
            event_type="performance_response",
            data={
                'request_id': request_id,
                'metric': metric,
                'data': data,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_strategy_update(self, event: Event):
        """Handle strategy updates"""
        if not self.running:
            return
            
        strategy = event.data.get('strategy')
        performance = event.data.get('performance', {})
        
        if strategy:
            self.strategy_performance[strategy] = performance
            
    async def publish_performance_update(self):
        """Publish performance update"""
        event = Event(
            event_type="performance_data_update",
            data={
                'metrics': self.metrics,
                'strategy_performance': self.strategy_performance,
                'agent_contributions': self.agent_contributions,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get performance analyzer status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'trades_tracked': len(self.trade_history),
            'strategies_tracked': len(self.strategy_performance),
            'agents_tracked': len(self.agent_contributions),
            'metrics': self.metrics,
            'timestamp': datetime.now().isoformat()
        }
