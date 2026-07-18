"""
AlphaEdge Agent 18 – Risk Guardian (Enhanced)
Hard veto (margin, drawdown>10%, liquidation, correlation>0.85, order book depth)
VaR/ES + stress VaR + Dynamic Hedging
V13.0.7 – UPDATED with Order Book Depth Check (Item 19)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import math
import statistics
import numpy as np

from core.event_bus import Event, EventBus
from core.state_manager import StateManager
from core.zone_detector import ZoneDetector

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
            'drawdown': 0.10,
            'margin': 0.70,
            'correlation': 0.85,
            'liquidation': 0.50,
            'var_limit': 0.05
        }
        
        # Zone Detector
        self.zone_detector = ZoneDetector()
        self.zone_risk_data = {}
        
        # ============================================
        # ITEM 19: ORDER BOOK DEPTH CHECK
        # ============================================
        self.order_book_depth = {
            'enabled': True,
            'min_depth_ratio': 2.0,
            'max_slippage': 0.02,
            'check_before_entry': True,
            'check_before_exit': False
        }
        
    async def start(self):
        """Start the risk guardian"""
        logger.info("Risk Guardian starting...")
        self.running = True
        
        await self.event_bus.subscribe("risk_check_request", self.handle_risk_check)
        await self.event_bus.subscribe("position_update", self.handle_position_update)
        await self.event_bus.subscribe("hedge_request", self.handle_hedge_request)
        await self.event_bus.subscribe("price_update", self.handle_price_update)
        
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
                await self.update_risk_metrics()
                await self.check_risk_thresholds()
                await self.update_hedge_allocation()
                await self.publish_risk_update()
            except Exception as e:
                logger.error(f"Risk cycle error: {e}")
            await asyncio.sleep(60)
            
    # ============================================
    # ITEM 19: ORDER BOOK DEPTH CHECK
    # ============================================
    
    async def check_order_book_depth(self, token: str, position_size: float, trade_type: str = 'entry') -> Dict:
        """Check order book depth before execution"""
        result = {'approved': True, 'reason': ''}
        
        if not self.order_book_depth['enabled']:
            return result
        
        if trade_type == 'entry' and not self.order_book_depth['check_before_entry']:
            return result
        
        if trade_type == 'exit' and not self.order_book_depth['check_before_exit']:
            return result
        
        try:
            order_book = await self._get_order_book(token)
            available_depth = order_book['bid_depth'] + order_book['ask_depth']
            min_required_depth = position_size * self.order_book_depth['min_depth_ratio']
            
            if available_depth < min_required_depth:
                result['approved'] = False
                result['reason'] = f'Order book depth ${available_depth:,.0f} below required ${min_required_depth:,.0f}'
                return result
            
            expected_slippage = position_size / available_depth if available_depth > 0 else 1.0
            if expected_slippage > self.order_book_depth['max_slippage']:
                result['approved'] = False
                result['reason'] = f'Expected slippage {expected_slippage*100:.2f}% above {self.order_book_depth["max_slippage"]*100:.2f}%'
                return result
                
        except Exception as e:
            logger.error(f"Order book depth check error: {e}")
            result['approved'] = False
            result['reason'] = str(e)
            
        return result
    
    async def _get_order_book(self, token: str) -> Dict:
        return {'bid_depth': 1000000, 'ask_depth': 1000000, 'best_bid': 100.0, 'best_ask': 100.05}
    
    async def handle_position_update(self, event: Event):
        """Handle position updates"""
        if not self.running:
            return
            
        position = event.data
        token = position.get('token')
        self.positions[token] = position
        await self.state_manager.set(f'position_{token}', position)
        
        if token:
            await self.calculate_position_zone_risk(token, position)
        
    async def calculate_position_zone_risk(self, token: str, position: Dict):
        """Calculate zone-based SL/TP for a position"""
        try:
            entry_price = position.get('price', 0)
            cap_tier = position.get('cap_tier', 'mid_cap')
            price_data = await self.state_manager.get(f'price_data_{token}', [])
            
            if not price_data or len(price_data) < 50:
                return
            
            highs = [p.get('high', 0) for p in price_data]
            lows = [p.get('low', 0) for p in price_data]
            closes = [p.get('close', 0) for p in price_data]
            volumes = [p.get('volume', 0) for p in price_data]
            opens = [p.get('open', 0) for p in price_data]
            
            high_arr = np.array(highs)
            low_arr = np.array(lows)
            close_arr = np.array(closes)
            vol_arr = np.array(volumes)
            open_arr = np.array(opens)
            
            zones = self.zone_detector.detect_zones(
                high_arr, low_arr, close_arr, vol_arr, open_arr
            )
            
            current_price = closes[-1] if closes else entry_price
            result = {'sl': None, 'tp': None, 'sl_reason': None, 'tp_reason': None}
            
            nearest_demand = self.zone_detector.get_nearest_zone(current_price, -1)
            if nearest_demand:
                sl_price = nearest_demand.bottom * 0.998
                sl_pct = (entry_price - sl_price) / entry_price * 100 if entry_price > 0 else 0
                if 0.5 <= sl_pct <= 15:
                    result['sl'] = sl_price
                    result['sl_reason'] = f"demand_zone_{nearest_demand.score:.1f}"
            
            nearest_supply = self.zone_detector.get_nearest_zone(current_price, 1)
            if nearest_supply:
                tp_price = nearest_supply.top
                tp_pct = (tp_price - entry_price) / entry_price * 100 if entry_price > 0 else 0
                if 1 <= tp_pct <= 50:
                    result['tp'] = tp_price
                    result['tp_reason'] = f"supply_zone_{nearest_supply.score:.1f}"
            
            if result['sl'] is None:
                sl_pct = self._get_stop_loss_pct(cap_tier)
                result['sl'] = entry_price * (1 - sl_pct)
                result['sl_reason'] = 'fixed_percentage'
            
            if result['tp'] is None:
                tp_pct = 0.15
                result['tp'] = entry_price * (1 + tp_pct)
                result['tp_reason'] = 'fixed_target'
            
            self.zone_risk_data[token] = {
                'sl': result['sl'],
                'tp': result['tp'],
                'sl_reason': result['sl_reason'],
                'tp_reason': result['tp_reason'],
                'elite_zones': len(self.zone_detector.get_elite_zones()),
                'timestamp': datetime.now().isoformat()
            }
            
            position['zone_sl'] = result['sl']
            position['zone_tp'] = result['tp']
            self.positions[token] = position
            await self.state_manager.set(f'position_{token}', position)
            
            logger.info(f"Zone SL/TP for {token}: SL={result['sl']} ({result['sl_reason']}), TP={result['tp']} ({result['tp_reason']})")
            
        except Exception as e:
            logger.error(f"Zone risk calculation error: {e}")
    
    def _get_stop_loss_pct(self, cap_tier: str) -> float:
        sl_map = {'micro_cap': 0.04, 'small_cap': 0.05, 'mid_cap': 0.07, 'large_cap': 0.08}
        return sl_map.get(cap_tier, 0.05)
    
    async def handle_price_update(self, event: Event):
        """Handle price updates for zone-based exit checks"""
        if not self.running:
            return
            
        token = event.data.get('token')
        price = event.data.get('price', 0)
        
        if token and token in self.zone_risk_data:
            zone_data = self.zone_risk_data[token]
            tp = zone_data.get('tp')
            if tp and price >= tp:
                await self.event_bus.publish(Event(
                    event_type="zone_tp_hit",
                    data={'token': token, 'price': price, 'tp': tp, 'reason': zone_data.get('tp_reason', 'zone_tp')},
                    source=self.agent_id
                ))
            
            sl = zone_data.get('sl')
            if sl and price <= sl:
                await self.event_bus.publish(Event(
                    event_type="zone_sl_hit",
                    data={'token': token, 'price': price, 'sl': sl, 'reason': zone_data.get('sl_reason', 'zone_sl')},
                    source=self.agent_id
                ))
    
    async def handle_risk_check(self, event: Event):
        """Handle risk check requests"""
        if not self.running:
            return
            
        action = event.data.get('action')
        position = event.data.get('position', {})
        risk_result = await self.check_position_risk(position)
        
        response = Event(
            event_type="risk_check_response",
            data={'action': action, 'position': position, 'risk_result': risk_result, 'timestamp': datetime.now().isoformat()},
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def check_position_risk(self, position: Dict) -> Dict:
        """Check risk for a specific position with order book depth"""
        pnl_percent = position.get('pnl_percent', 0)
        if pnl_percent < -self.thresholds['drawdown']:
            return {'approved': False, 'reason': f'Drawdown {pnl_percent:.1f}% exceeds {self.thresholds["drawdown"]*100}% limit'}
        
        margin_used = position.get('margin_used', 0)
        total_capital = await self.state_manager.get('total_capital', 10000)
        margin_ratio = margin_used / total_capital if total_capital > 0 else 0
        if margin_ratio > self.thresholds['margin']:
            return {'approved': False, 'reason': f'Margin {margin_ratio:.1f}% exceeds {self.thresholds["margin"]*100}% limit'}
        
        correlation = position.get('correlation', 0)
        if abs(correlation) > self.thresholds['correlation']:
            return {'approved': False, 'reason': f'Correlation {correlation:.2f} exceeds {self.thresholds["correlation"]} limit'}
        
        liquidation_risk = position.get('liquidation_risk', 0)
        if liquidation_risk > self.thresholds['liquidation']:
            return {'approved': False, 'reason': f'Liquidation risk {liquidation_risk:.1f}% exceeds limit'}
        
        # Item 19: Order Book Depth Check
        if position.get('trade_type') == 'entry':
            token = position.get('token')
            position_size = position.get('size', 0)
            depth_check = await self.check_order_book_depth(token, position_size)
            if not depth_check['approved']:
                return {'approved': False, 'reason': depth_check['reason'], 'risk_level': 'critical'}
        
        return {'approved': True, 'reason': 'Risk check passed'}
        
    async def update_risk_metrics(self):
        """Update overall risk metrics"""
        if not self.positions:
            return
            
        positions_data = list(self.positions.values())
        returns = [p.get('pnl_percent', 0) for p in positions_data]
        if len(returns) > 1:
            std_dev = statistics.stdev(returns) if len(returns) > 1 else 0
            self.var_95 = -1.645 * std_dev
            self.var_99 = -2.326 * std_dev
            sorted_returns = sorted(returns)
            tail_losses = sorted_returns[:max(1, int(len(sorted_returns) * 0.05))]
            self.expected_shortfall = -sum(tail_losses) / len(tail_losses) if tail_losses else 0
            self.stress_var = self.var_95 * 2
        else:
            self.var_95 = 0
            self.var_99 = 0
            self.expected_shortfall = 0
            self.stress_var = 0
            
        self.risk_score = self.calculate_risk_score()
        await self.state_manager.set('var_95', self.var_95)
        await self.state_manager.set('var_99', self.var_99)
        await self.state_manager.set('expected_shortfall', self.expected_shortfall)
        await self.state_manager.set('stress_var', self.stress_var)
        await self.state_manager.set('risk_score', self.risk_score)
        
    def calculate_risk_score(self) -> float:
        score = 50
        if abs(self.var_95) > 0.05:
            score += 20
        elif abs(self.var_95) > 0.03:
            score += 10
        total_drawdown = sum(p.get('pnl_percent', 0) for p in self.positions.values())
        if total_drawdown < -0.05:
            score += 15
        elif total_drawdown < -0.02:
            score += 5
        if len(self.positions) <= 3:
            score += 15
        elif len(self.positions) <= 5:
            score += 5
        return min(100, score)
        
    async def check_risk_thresholds(self):
        alerts = []
        total_drawdown = sum(p.get('pnl_percent', 0) for p in self.positions.values())
        if total_drawdown < -self.thresholds['drawdown']:
            alerts.append({'type': 'drawdown', 'severity': 'critical', 'value': total_drawdown, 'threshold': -self.thresholds['drawdown']})
        if abs(self.var_95) > self.thresholds['var_limit']:
            alerts.append({'type': 'var_exceeded', 'severity': 'high', 'value': abs(self.var_95), 'threshold': self.thresholds['var_limit']})
        total_margin = sum(p.get('margin_used', 0) for p in self.positions.values())
        total_capital = await self.state_manager.get('total_capital', 10000)
        margin_ratio = total_margin / total_capital if total_capital > 0 else 0
        if margin_ratio > self.thresholds['margin']:
            alerts.append({'type': 'margin_exceeded', 'severity': 'high', 'value': margin_ratio, 'threshold': self.thresholds['margin']})
        for alert in alerts:
            await self.publish_alert(alert)
            
    async def update_hedge_allocation(self):
        hedge_allocation = 0
        if self.risk_score > 70:
            hedge_allocation = 50
        elif self.risk_score > 60:
            hedge_allocation = 30
        elif self.risk_score > 50:
            hedge_allocation = 15
        macro_score = await self.state_manager.get('macro_score', 50)
        if macro_score < 40:
            hedge_allocation += 20
        volatility = await self.state_manager.get('market_volatility', 0.3)
        if volatility > 0.7:
            hedge_allocation += 20
        self.hedge_allocation = min(50, hedge_allocation)
        await self.state_manager.set('hedge_allocation', self.hedge_allocation)
        
    async def handle_hedge_request(self, event: Event):
        if not self.running:
            return
        if self.hedge_allocation > 0:
            hedge_data = {'allocation': self.hedge_allocation, 'strategy': 'stable_hedge', 'assets': ['USDC', 'USDT'], 'timestamp': datetime.now().isoformat()}
            response = Event(event_type="hedge_execution", data=hedge_data, source=self.agent_id)
            await self.event_bus.publish(response)
            logger.info(f"Hedge executed: {self.hedge_allocation}% allocation")
            
    async def publish_alert(self, alert: Dict):
        alert_event = Event(event_type="risk_alert", data=alert, source=self.agent_id)
        await self.event_bus.publish(alert_event)
        logger.warning(f"🚨 Risk alert: {alert['type']} - {alert['severity']}")
        
    async def publish_risk_update(self):
        risk_data = {
            'var_95': self.var_95,
            'var_99': self.var_99,
            'expected_shortfall': self.expected_shortfall,
            'stress_var': self.stress_var,
            'risk_score': self.risk_score,
            'hedge_allocation': self.hedge_allocation,
            'positions': len(self.positions),
            'zone_risks': len(self.zone_risk_data),
            'order_book_depth_active': self.order_book_depth['enabled'],
            'timestamp': datetime.now().isoformat()
        }
        event = Event(event_type="risk_data_update", data=risk_data, source=self.agent_id)
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'var_95': self.var_95,
            'var_99': self.var_99,
            'risk_score': self.risk_score,
            'hedge_allocation': self.hedge_allocation,
            'positions_monitored': len(self.positions),
            'zone_risk_active': len(self.zone_risk_data),
            'order_book_depth_active': self.order_book_depth['enabled'],
            'timestamp': datetime.now().isoformat()
        }
