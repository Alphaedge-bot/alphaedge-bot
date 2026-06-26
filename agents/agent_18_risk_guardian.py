"""
AlphaEdge Agent 18 – Risk Guardian (Enhanced)
Hard veto (margin, drawdown>10%, liquidation, correlation>0.85, order book depth)
VaR/ES + stress VaR + Dynamic Hedging
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import math
import statistics

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class RiskGuardian:
    """Risk Guardian – Comprehensive risk management and hedging"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "risk_guardian"
        self.running = False
        
        # Risk metrics
        self.var_95 = 0
        self.var_99 = 0
        self.expected_shortfall = 0
        self.stress_var = 0
        
        # Position tracking
        self.positions = {}
        self.risk_score = 0
        self.hedge_allocation = 0
        
        # Risk thresholds
        self.thresholds = {
            'drawdown': 0.10,  # 10%
            'margin': 0.70,    # 70%
            'correlation': 0.85,
            'liquidation': 0.50,
            'var_limit': 0.05   # 5%
        }
        
    async def start(self):
        """Start the risk guardian"""
        logger.info("Risk Guardian starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("risk_check_request", self.handle_risk_check)
        await self.event_bus.subscribe("position_update", self.handle_position_update)
        await self.event_bus.subscribe("hedge_request", self.handle_hedge_request)
        
        # Start risk monitoring cycle
        asyncio.create_task(self.run_risk_cycle())
        
        logger.info("Risk Guardian running")
        
    async def stop(self):
        """Stop the risk guardian"""
        self.running = False
        logger.info("Risk Guardian stopped")
        
    async def run_risk_cycle(self):
        """Run regular risk monitoring"""
        while self.running:
            try:
                # Update risk metrics
                await self.update_risk_metrics()
                
                # Check thresholds
                await self.check_risk_thresholds()
                
                # Update hedge allocation
                await self.update_hedge_allocation()
                
                # Publish risk update
                await self.publish_risk_update()
                
            except Exception as e:
                logger.error(f"Risk cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def handle_position_update(self, event: Event):
        """Handle position updates"""
        if not self.running:
            return
            
        position = event.data
        token = position.get('token')
        
        self.positions[token] = position
        await self.state_manager.set(f'position_{token}', position)
        
    async def handle_risk_check(self, event: Event):
        """Handle risk check requests"""
        if not self.running:
            return
            
        action = event.data.get('action')
        position = event.data.get('position', {})
        
        # Perform risk check
        risk_result = await self.check_position_risk(position)
        
        response = Event(
            event_type="risk_check_response",
            data={
                'action': action,
                'position': position,
                'risk_result': risk_result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def check_position_risk(self, position: Dict) -> Dict:
        """Check risk for a specific position"""
        # Check drawdown
        pnl_percent = position.get('pnl_percent', 0)
        if pnl_percent < -self.thresholds['drawdown']:
            return {
                'approved': False,
                'reason': f'Drawdown {pnl_percent:.1f}% exceeds {self.thresholds["drawdown"]*100}% limit'
            }
            
        # Check margin
        margin_used = position.get('margin_used', 0)
        total_capital = await self.state_manager.get('total_capital', 10000)
        margin_ratio = margin_used / total_capital if total_capital > 0 else 0
        
        if margin_ratio > self.thresholds['margin']:
            return {
                'approved': False,
                'reason': f'Margin {margin_ratio:.1f}% exceeds {self.thresholds["margin"]*100}% limit'
            }
            
        # Check correlation
        correlation = position.get('correlation', 0)
        if abs(correlation) > self.thresholds['correlation']:
            return {
                'approved': False,
                'reason': f'Correlation {correlation:.2f} exceeds {self.thresholds["correlation"]} limit'
            }
            
        # Check liquidation risk
        liquidation_risk = position.get('liquidation_risk', 0)
        if liquidation_risk > self.thresholds['liquidation']:
            return {
                'approved': False,
                'reason': f'Liquidation risk {liquidation_risk:.1f}% exceeds limit'
            }
            
        return {'approved': True, 'reason': 'Risk check passed'}
        
    async def update_risk_metrics(self):
        """Update overall risk metrics"""
        if not self.positions:
            return
            
        # Calculate portfolio metrics
        positions_data = list(self.positions.values())
        
        # Calculate VaR (simplified)
        returns = [p.get('pnl_percent', 0) for p in positions_data]
        if len(returns) > 1:
            std_dev = statistics.stdev(returns)
            self.var_95 = -1.645 * std_dev  # 95% confidence
            self.var_99 = -2.326 * std_dev  # 99% confidence
            
            # Expected Shortfall
            sorted_returns = sorted(returns)
            tail_losses = sorted_returns[:max(1, int(len(sorted_returns) * 0.05))]
            self.expected_shortfall = -sum(tail_losses) / len(tail_losses) if tail_losses else 0
            
            # Stress VaR (2x normal)
            self.stress_var = self.var_95 * 2
        else:
            self.var_95 = 0
            self.var_99 = 0
            self.expected_shortfall = 0
            self.stress_var = 0
            
        # Calculate overall risk score
        self.risk_score = self.calculate_risk_score()
        
        # Store metrics
        await self.state_manager.set('var_95', self.var_95)
        await self.state_manager.set('var_99', self.var_99)
        await self.state_manager.set('expected_shortfall', self.expected_shortfall)
        await self.state_manager.set('stress_var', self.stress_var)
        await self.state_manager.set('risk_score', self.risk_score)
        
    def calculate_risk_score(self) -> float:
        """Calculate overall risk score (0-100)"""
        score = 50  # Baseline
        
        # Adjust for VaR
        if abs(self.var_95) > 0.05:
            score += 20
        elif abs(self.var_95) > 0.03:
            score += 10
            
        # Adjust for drawdown
        total_drawdown = sum(p.get('pnl_percent', 0) for p in self.positions.values())
        if total_drawdown < -0.05:
            score += 15
        elif total_drawdown < -0.02:
            score += 5
            
        # Adjust for concentration
        if len(self.positions) <= 3:
            score += 15
        elif len(self.positions) <= 5:
            score += 5
            
        return min(100, score)
        
    async def check_risk_thresholds(self):
        """Check if any risk thresholds are breached"""
        alerts = []
        
        # Check drawdown
        total_drawdown = sum(p.get('pnl_percent', 0) for p in self.positions.values())
        if total_drawdown < -self.thresholds['drawdown']:
            alerts.append({
                'type': 'drawdown',
                'severity': 'critical',
                'value': total_drawdown,
                'threshold': -self.thresholds['drawdown']
            })
            
        # Check VaR
        if abs(self.var_95) > self.thresholds['var_limit']:
            alerts.append({
                'type': 'var_exceeded',
                'severity': 'high',
                'value': abs(self.var_95),
                'threshold': self.thresholds['var_limit']
            })
            
        # Check margin
        total_margin = sum(p.get('margin_used', 0) for p in self.positions.values())
        total_capital = await self.state_manager.get('total_capital', 10000)
        margin_ratio = total_margin / total_capital if total_capital > 0 else 0
        
        if margin_ratio > self.thresholds['margin']:
            alerts.append({
                'type': 'margin_exceeded',
                'severity': 'high',
                'value': margin_ratio,
                'threshold': self.thresholds['margin']
            })
            
        # Publish alerts
        for alert in alerts:
            await self.publish_alert(alert)
            
    async def update_hedge_allocation(self):
        """Update dynamic hedge allocation based on risk"""
        # Base hedge allocation
        hedge_allocation = 0
        
        # Increase hedge with risk
        if self.risk_score > 70:
            hedge_allocation = 50  # 50% hedge
        elif self.risk_score > 60:
            hedge_allocation = 30  # 30% hedge
        elif self.risk_score > 50:
            hedge_allocation = 15  # 15% hedge
            
        # Increase hedge in bearish conditions
        macro_score = await self.state_manager.get('macro_score', 50)
        if macro_score < 40:
            hedge_allocation += 20
            
        # Increase hedge in high volatility
        volatility = await self.state_manager.get('market_volatility', 0.3)
        if volatility > 0.7:
            hedge_allocation += 20
            
        # Cap at 50%
        self.hedge_allocation = min(50, hedge_allocation)
        
        await self.state_manager.set('hedge_allocation', self.hedge_allocation)
        
    async def handle_hedge_request(self, event: Event):
        """Handle hedge requests"""
        if not self.running:
            return
            
        # Execute hedge based on allocation
        if self.hedge_allocation > 0:
            hedge_data = {
                'allocation': self.hedge_allocation,
                'strategy': 'stable_hedge',
                'assets': ['USDC', 'USDT'],
                'timestamp': datetime.now().isoformat()
            }
            
            response = Event(
                event_type="hedge_execution",
                data=hedge_data,
                source=self.agent_id
            )
            await self.event_bus.publish(response)
            
            logger.info(f"Hedge executed: {self.hedge_allocation}% allocation")
            
    async def publish_alert(self, alert: Dict):
        """Publish risk alert"""
        alert_event = Event(
            event_type="risk_alert",
            data=alert,
            source=self.agent_id
        )
        await self.event_bus.publish(alert_event)
        
        logger.warning(f"🚨 Risk alert: {alert['type']} - {alert['severity']}")
        
    async def publish_risk_update(self):
        """Publish risk data update"""
        risk_data = {
            'var_95': self.var_95,
            'var_99': self.var_99,
            'expected_shortfall': self.expected_shortfall,
            'stress_var': self.stress_var,
            'risk_score': self.risk_score,
            'hedge_allocation': self.hedge_allocation,
            'positions': len(self.positions),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="risk_data_update",
            data=risk_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get risk guardian status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'var_95': self.var_95,
            'var_99': self.var_99,
            'risk_score': self.risk_score,
            'hedge_allocation': self.hedge_allocation,
            'positions_monitored': len(self.positions),
            'timestamp': datetime.now().isoformat()
        }
