"""
AlphaEdge Agent 28 – FPGA Execution Kernel
FPGA-accelerated order routing (<1ms, Stage 2)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class FPGAExecutionKernel:
    """FPGA Execution Kernel – Hardware-accelerated order execution (<1ms)"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "fpga_execution"
        self.running = False
        
        # FPGA state
        self.fpga_available = False
        self.fpga_utilization = 0
        self.execution_count = 0
        self.avg_latency = 0
        self.latency_history = []
        
        # Stage detection
        self.stage = "Stage 1"
        
    async def start(self):
        """Start the FPGA execution kernel"""
        logger.info("FPGA Execution Kernel starting...")
        self.running = True
        
        # Detect FPGA hardware
        await self.detect_fpga()
        
        # Subscribe to events
        await self.event_bus.subscribe("fpga_execution_request", self.handle_execution_request)
        await self.event_bus.subscribe("fpga_status_request", self.handle_status_request)
        
        # Start FPGA monitoring
        asyncio.create_task(self.run_fpga_cycle())
        
        logger.info(f"FPGA Execution Kernel running (Stage: {self.stage})")
        
    async def stop(self):
        """Stop the FPGA execution kernel"""
        self.running = False
        logger.info("FPGA Execution Kernel stopped")
        
    async def detect_fpga(self):
        """Detect FPGA hardware availability"""
        # In production, detect actual FPGA hardware
        # For now, simulate detection
        stage = await self.state_manager.get('hardware_stage', 'Stage 1')
        self.stage = stage
        
        if stage == 'Stage 2':
            self.fpga_available = True
            self.fpga_utilization = 70
            logger.info("✅ FPGA hardware detected (Stage 2) – <1ms latency")
        else:
            self.fpga_available = False
            logger.info("❌ No FPGA hardware detected (Stage 1) – CPU execution")
            
        await self.state_manager.set('fpga_available', self.fpga_available)
        
    async def run_fpga_cycle(self):
        """Run regular FPGA monitoring"""
        while self.running:
            try:
                if self.fpga_available:
                    # Update utilization
                    await self.update_utilization()
                    
                    # Update latency metrics
                    await self.update_latency_metrics()
                    
                # Publish FPGA status
                await self.publish_fpga_status()
                
            except Exception as e:
                logger.error(f"FPGA cycle error: {e}")
                
            await asyncio.sleep(30)  # Every 30 seconds
            
    async def handle_execution_request(self, event: Event):
        """Handle FPGA execution requests"""
        if not self.running:
            return
            
        order = event.data.get('order')
        execution_id = order.get('execution_id', f"fpga_{datetime.now().timestamp()}")
        
        logger.info(f"FPGA execution request: {execution_id}")
        
        if self.fpga_available:
            # Execute via FPGA (<1ms)
            result = await self.execute_via_fpga(order)
        else:
            # Fallback to CPU
            logger.warning("FPGA unavailable, using CPU fallback")
            result = await self.execute_via_cpu(order)
            
        # Send response
        response = Event(
            event_type="fpga_execution_result",
            data={
                'execution_id': execution_id,
                'result': result,
                'fpga_used': self.fpga_available,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def execute_via_fpga(self, order: Dict) -> Dict:
        """Execute order via FPGA (<1ms)"""
        start_time = datetime.now()
        
        # Simulate FPGA execution (hardware accelerated)
        await asyncio.sleep(0.0001)  # 0.1ms
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Update metrics
        self.execution_count += 1
        self.latency_history.append(execution_time)
        if len(self.latency_history) > 100:
            self.latency_history.pop(0)
            
        self.avg_latency = sum(self.latency_history) / len(self.latency_history) if self.latency_history else 0
        
        return {
            'status': 'executed',
            'method': 'fpga',
            'execution_time_ms': execution_time,
            'order': order,
            'timestamp': datetime.now().isoformat()
        }
        
    async def execute_via_cpu(self, order: Dict) -> Dict:
        """Execute order via CPU (fallback)"""
        start_time = datetime.now()
        
        # Simulate CPU execution
        await asyncio.sleep(0.01)  # 10ms
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Update metrics
        self.execution_count += 1
        self.latency_history.append(execution_time)
        if len(self.latency_history) > 100:
            self.latency_history.pop(0)
            
        self.avg_latency = sum(self.latency_history) / len(self.latency_history) if self.latency_history else 0
        
        return {
            'status': 'executed',
            'method': 'cpu',
            'execution_time_ms': execution_time,
            'order': order,
            'timestamp': datetime.now().isoformat()
        }
        
    async def update_utilization(self):
        """Update FPGA utilization"""
        if self.fpga_available:
            # Simulate varying utilization
            self.fpga_utilization = random.randint(60, 95)
            await self.state_manager.set('fpga_utilization', self.fpga_utilization)
            
    async def update_latency_metrics(self):
        """Update latency metrics"""
        # Calculate average latency
        if self.latency_history:
            self.avg_latency = sum(self.latency_history) / len(self.latency_history)
        else:
            self.avg_latency = 0
            
        await self.state_manager.set('fpga_avg_latency', self.avg_latency)
        
    async def handle_status_request(self, event: Event):
        """Handle FPGA status requests"""
        if not self.running:
            return
            
        status = {
            'fpga_available': self.fpga_available,
            'stage': self.stage,
            'utilization': self.fpga_utilization if self.fpga_available else 0,
            'execution_count': self.execution_count,
            'avg_latency_ms': self.avg_latency,
            'timestamp': datetime.now().isoformat()
        }
        
        response = Event(
            event_type="fpga_status_response",
            data=status,
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def publish_fpga_status(self):
        """Publish FPGA status update"""
        fpga_status = {
            'available': self.fpga_available,
            'stage': self.stage,
            'utilization': self.fpga_utilization if self.fpga_available else 0,
            'execution_count': self.execution_count,
            'avg_latency_ms': self.avg_latency,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="fpga_execution_update",
            data=fpga_status,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get FPGA execution kernel status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'fpga_available': self.fpga_available,
            'stage': self.stage,
            'utilization': self.fpga_utilization if self.fpga_available else 0,
            'execution_count': self.execution_count,
            'avg_latency_ms': self.avg_latency,
            'timestamp': datetime.now().isoformat()
        }
