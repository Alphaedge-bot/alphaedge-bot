"""
AlphaEdge Agent 53 – Tax & Audit Agent
Log trades (hash, cost basis, fee), capital gains reports, immutable audit
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import hashlib

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TaxAuditAgent:
    """Tax & Audit Agent – Tax reporting and trade auditing"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "tax_audit"
        self.running = False
        
        # Tax and audit state
        self.trade_log = []
        self.cost_basis = {}
        self.tax_reports = []
        self.audit_trail = []
        
        # Configuration
        self.config = {
            'tax_year': datetime.now().year,
            'cost_basis_method': 'fifo',  # fifo, lifo, specific
            'currency': 'USD',
            'capital_gains_rate': 0.20  # 20% default
        }
        
    async def start(self):
        """Start the tax & audit agent"""
        logger.info("Tax & Audit Agent starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("trade_log", self.handle_trade_log)
        await self.event_bus.subscribe("tax_report_request", self.handle_tax_report_request)
        await self.event_bus.subscribe("audit_request", self.handle_audit_request)
        
        # Start tax cycle
        asyncio.create_task(self.run_tax_cycle())
        
        logger.info("Tax & Audit Agent running")
        
    async def stop(self):
        """Stop the tax & audit agent"""
        self.running = False
        logger.info("Tax & Audit Agent stopped")
        
    async def run_tax_cycle(self):
        """Run regular tax cycle"""
        while self.running:
            try:
                # Update cost basis
                await self.update_cost_basis()
                
                # Generate periodic reports
                await self.generate_periodic_reports()
                
                # Publish tax update
                await self.publish_tax_update()
                
            except Exception as e:
                logger.error(f"Tax cycle error: {e}")
                
            await asyncio.sleep(3600)  # Every hour
            
    async def handle_trade_log(self, event: Event):
        """Handle trade logging"""
        if not self.running:
            return
            
        trade = event.data
        trade_id = trade.get('id', f"trade_{datetime.now().timestamp()}")
        
        # Create trade record
        record = {
            'id': trade_id,
            'timestamp': datetime.now().isoformat(),
            'token': trade.get('token'),
            'side': trade.get('side', 'buy'),
            'quantity': trade.get('quantity', 0),
            'price': trade.get('price', 0),
            'fee': trade.get('fee', 0),
            'cost_basis': trade.get('cost_basis', 0),
            'hash': self.calculate_trade_hash(trade),
            'raw_data': trade
        }
        
        # Add to trade log
        self.trade_log.append(record)
        
        # Update cost basis
        await self.update_cost_basis_for_trade(record)
        
        # Update audit trail
        self.audit_trail.append({
            'action': 'trade_logged',
            'trade_id': trade_id,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Trade logged: {trade_id}")
        
    async def handle_tax_report_request(self, event: Event):
        """Handle tax report requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        year = event.data.get('year', self.config['tax_year'])
        
        # Generate report
        report = await self.generate_tax_report(year)
        
        response = Event(
            event_type="tax_report_response",
            data={
                'request_id': request_id,
                'year': year,
                'report': report,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_audit_request(self, event: Event):
        """Handle audit requests"""
        if not self.running:
            return
            
        start_date = event.data.get('start_date')
        end_date = event.data.get('end_date')
        
        # Perform audit
        audit_result = await self.perform_audit(start_date, end_date)
        
        response = Event(
            event_type="audit_response",
            data={
                'start_date': start_date,
                'end_date': end_date,
                'audit_result': audit_result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    def calculate_trade_hash(self, trade: Dict) -> str:
        """Calculate hash for a trade"""
        trade_string = json.dumps(trade, sort_keys=True)
        return hashlib.sha256(trade_string.encode()).hexdigest()
        
    async def update_cost_basis_for_trade(self, trade: Dict):
        """Update cost basis for a trade"""
        token = trade.get('token')
        side = trade.get('side')
        quantity = trade.get('quantity', 0)
        price = trade.get('price', 0)
        
        if token not in self.cost_basis:
            self.cost_basis[token] = {
                'total_cost': 0,
                'total_quantity': 0,
                'trades': []
            }
            
        if side == 'buy':
            self.cost_basis[token]['total_cost'] += quantity * price
            self.cost_basis[token]['total_quantity'] += quantity
            self.cost_basis[token]['trades'].append({
                'type': 'buy',
                'quantity': quantity,
                'price': price,
                'timestamp': datetime.now().isoformat()
            })
        elif side == 'sell':
            # Calculate cost basis using FIFO
            if self.config['cost_basis_method'] == 'fifo':
                cost_basis = self.calculate_fifo_cost_basis(token, quantity)
            elif self.config['cost_basis_method'] == 'lifo':
                cost_basis = self.calculate_lifo_cost_basis(token, quantity)
            else:
                cost_basis = 0
                
            self.cost_basis[token]['total_cost'] -= cost_basis
            self.cost_basis[token]['total_quantity'] -= quantity
            
    def calculate_fifo_cost_basis(self, token: str, quantity: float) -> float:
        """Calculate FIFO cost basis"""
        if token not in self.cost_basis:
            return 0
            
        trades = self.cost_basis[token]['trades']
        remaining_quantity = quantity
        total_cost = 0
        
        # Process buys in order (FIFO)
        for trade in trades:
            if trade['type'] == 'buy' and remaining_quantity > 0:
                trade_quantity = trade['quantity']
                if trade_quantity <= remaining_quantity:
                    total_cost += trade_quantity * trade['price']
                    remaining_quantity -= trade_quantity
                else:
                    total_cost += remaining_quantity * trade['price']
                    remaining_quantity = 0
                    
        return total_cost
        
    def calculate_lifo_cost_basis(self, token: str, quantity: float) -> float:
        """Calculate LIFO cost basis"""
        if token not in self.cost_basis:
            return 0
            
        trades = self.cost_basis[token]['trades']
        remaining_quantity = quantity
        total_cost = 0
        
        # Process buys in reverse (LIFO)
        for trade in reversed(trades):
            if trade['type'] == 'buy' and remaining_quantity > 0:
                trade_quantity = trade['quantity']
                if trade_quantity <= remaining_quantity:
                    total_cost += trade_quantity * trade['price']
                    remaining_quantity -= trade_quantity
                else:
                    total_cost += remaining_quantity * trade['price']
                    remaining_quantity = 0
                    
        return total_cost
        
    async def generate_tax_report(self, year: int) -> Dict:
        """Generate tax report for a specific year"""
        # Filter trades by year
        year_trades = []
        for trade in self.trade_log:
            trade_year = datetime.fromisoformat(trade['timestamp']).year
            if trade_year == year:
                year_trades.append(trade)
                
        # Calculate totals
        total_buys = 0
        total_sells = 0
        total_cost_basis = 0
        total_proceeds = 0
        
        for trade in year_trades:
            if trade['side'] == 'buy':
                total_buys += trade['quantity'] * trade['price']
                total_cost_basis += trade['cost_basis']
            else:
                total_sells += trade['quantity'] * trade['price']
                total_proceeds += trade['quantity'] * trade['price']
                
        # Calculate capital gains
        capital_gains = total_proceeds - total_cost_basis
        capital_gains_tax = capital_gains * self.config['capital_gains_rate']
        
        report = {
            'year': year,
            'total_trades': len(year_trades),
            'total_buys': total_buys,
            'total_sells': total_sells,
            'total_cost_basis': total_cost_basis,
            'total_proceeds': total_proceeds,
            'capital_gains': capital_gains,
            'capital_gains_tax': capital_gains_tax,
            'trades': year_trades,
            'timestamp': datetime.now().isoformat()
        }
        
        self.tax_reports.append(report)
        
        return report
        
    async def generate_periodic_reports(self):
        """Generate periodic reports"""
        # Generate monthly reports
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Check if we have a report for this month
        has_report = False
        for report in self.tax_reports:
            if report['year'] == current_year and report.get('month') == current_month:
                has_report = True
                break
                
        if not has_report and self.trade_log:
            # Generate monthly report
            monthly_trades = []
            for trade in self.trade_log:
                trade_date = datetime.fromisoformat(trade['timestamp'])
                if trade_date.year == current_year and trade_date.month == current_month:
                    monthly_trades.append(trade)
                    
            if monthly_trades:
                report = {
                    'year': current_year,
                    'month': current_month,
                    'total_trades': len(monthly_trades),
                    'trades': monthly_trades,
                    'timestamp': datetime.now().isoformat()
                }
                self.tax_reports.append(report)
                
    async def update_cost_basis(self):
        """Update cost basis calculations"""
        # Recalculate cost basis for all tokens
        for token in set(t['token'] for t in self.trade_log):
            self.cost_basis[token] = {
                'total_cost': 0,
                'total_quantity': 0,
                'trades': []
            }
            
            for trade in self.trade_log:
                if trade['token'] == token:
                    await self.update_cost_basis_for_trade(trade)
                    
    async def perform_audit(self, start_date: str, end_date: str) -> Dict:
        """Perform audit for a date range"""
        # Filter trades by date range
        filtered_trades = []
        for trade in self.trade_log:
            trade_date = datetime.fromisoformat(trade['timestamp'])
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            
            if start <= trade_date <= end:
                filtered_trades.append(trade)
                
        # Verify trade hashes
        hash_verification = []
        for trade in filtered_trades:
            expected_hash = self.calculate_trade_hash(trade['raw_data'])
            actual_hash = trade['hash']
            hash_verification.append({
                'trade_id': trade['id'],
                'valid': expected_hash == actual_hash,
                'expected_hash': expected_hash,
                'actual_hash': actual_hash
            })
            
        return {
            'total_trades': len(filtered_trades),
            'hash_verification': hash_verification,
            'valid_count': sum(1 for v in hash_verification if v['valid']),
            'invalid_count': sum(1 for v in hash_verification if not v['valid']),
            'timestamp': datetime.now().isoformat()
        }
        
    async def publish_tax_update(self):
        """Publish tax data update"""
        tax_data = {
            'trade_count': len(self.trade_log),
            'cost_basis': self.cost_basis,
            'tax_reports': self.tax_reports[-5:],
            'audit_trail': self.audit_trail[-10:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="tax_update",
            data=tax_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get tax & audit agent status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'trade_count': len(self.trade_log),
            'cost_basis_tokens': len(self.cost_basis),
            'tax_reports': len(self.tax_reports),
            'audit_trail_size': len(self.audit_trail),
            'timestamp': datetime.now().isoformat()
        }
