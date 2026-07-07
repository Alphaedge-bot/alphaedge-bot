# tests/test_agents.py
# AlphaEdge V13.0.5 – Agent Tests
# Created: July 7, 2026

"""
Test suite for agent functionality.
Verifies agent initialization, event handling, and communication.
"""

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime


class TestAgents(unittest.TestCase):
    """Test agent functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.event_bus = Mock()
        self.state_manager = Mock()
        
        # Mock state manager
        self.state_manager.get = AsyncMock(return_value={})
        self.state_manager.set = AsyncMock(return_value=True)
        
    def test_agent_63_initialization(self):
        """Test Profit Taking Executor initialization"""
        from agents.agent_63_profit_taking_executor import ProfitTakingExecutor
        
        executor = ProfitTakingExecutor(self.event_bus, self.state_manager)
        
        self.assertEqual(executor.agent_id, "profit_taking_executor")
        self.assertFalse(executor.running)
        self.assertIn('gold_config', dir(executor))
        self.assertIn('paxg', executor.gold_config['assets'])
        self.assertIn('xaut', executor.gold_config['assets'])
        print("✅ Agent 63 initialized with PAXG + XAUT")
        
    async def test_agent_63_start_stop(self):
        """Test Profit Taking Executor start/stop"""
        from agents.agent_63_profit_taking_executor import ProfitTakingExecutor
        
        executor = ProfitTakingExecutor(self.event_bus, self.state_manager)
        
        # Start
        await executor.start()
        self.assertTrue(executor.running)
        
        # Stop
        await executor.stop()
        self.assertFalse(executor.running)
        print("✅ Agent 63 start/stop test passed")
        
    async def test_agent_63_event_subscriptions(self):
        """Test Profit Taking Executor event subscriptions"""
        from agents.agent_63_profit_taking_executor import ProfitTakingExecutor
        
        executor = ProfitTakingExecutor(self.event_bus, self.state_manager)
        await executor.start()
        
        # Check event bus subscriptions
        self.event_bus.subscribe.assert_any_call(
            "profit_take_request",
            executor.handle_profit_take_request
        )
        self.event_bus.subscribe.assert_any_call(
            "depeg_detected",
            executor.handle_depeg
        )
        self.event_bus.subscribe.assert_any_call(
            "gold_swap_requested",
            executor.handle_swap_request
        )
        
        print("✅ Agent 63 event subscriptions confirmed")
        
    async def test_agent_63_handle_swap_request(self):
        """Test Profit Taking Executor handles swap requests"""
        from agents.agent_63_profit_taking_executor import ProfitTakingExecutor
        
        executor = ProfitTakingExecutor(self.event_bus, self.state_manager)
        
        # Mock execute_gold_swap
        executor.execute_gold_swap = AsyncMock(return_value={'status': 'executed'})
        
        # Create swap request
        event = Mock()
        event.data = {'amount': 1000, 'asset': 'paxg'}
        
        await executor.handle_swap_request(event)
        
        executor.execute_gold_swap.assert_called_with(1000, preferred_asset='paxg')
        print("✅ Agent 63 swap request handler test passed")
        
    async def test_agent_63_handle_depeg(self):
        """Test Profit Taking Executor handles depeg"""
        from agents.agent_63_profit_taking_executor import ProfitTakingExecutor
        
        executor = ProfitTakingExecutor(self.event_bus, self.state_manager)
        
        # Mock holdings
        self.state_manager.get = AsyncMock(return_value={'USDT': 10000, 'USDC': 5000})
        
        # Mock execute_gold_swap
        executor.execute_gold_swap = AsyncMock(return_value={'status': 'executed'})
        
        # Create depeg event
        event = Mock()
        event.data = {'usdc_price': 0.98, 'usdt_price': 0.98}
        
        await executor.handle_depeg(event)
        
        executor.execute_gold_swap.assert_called_with(15000, preferred_asset='paxg')
        print("✅ Agent 63 depeg handler test passed")
        
    async def test_agent_63_handle_recovery(self):
        """Test Profit Taking Executor handles recovery"""
        from agents.agent_63_profit_taking_executor import ProfitTakingExecutor
        
        executor = ProfitTakingExecutor(self.event_bus, self.state_manager)
        
        # Mock execute_stable_swap
        executor.execute_stable_swap = AsyncMock(return_value={'status': 'executed'})
        
        # Create recovery event
        event = Mock()
        event.data = {'usdc_price': 1.00, 'usdt_price': 1.00}
        
        await executor.handle_recovery(event)
        
        executor.execute_stable_swap.assert_called()
        print("✅ Agent 63 recovery handler test passed")
        
    async def test_agent_63_get_status(self):
        """Test Profit Taking Executor status"""
        from agents.agent_63_profit_taking_executor import ProfitTakingExecutor
        
        executor = ProfitTakingExecutor(self.event_bus, self.state_manager)
        
        # Mock holdings
        self.state_manager.get = AsyncMock(return_value={'paxg': 0.25, 'xaut': 0.15})
        
        # Get status
        status = await executor.get_status()
        
        self.assertEqual(status['agent_id'], 'profit_taking_executor')
        self.assertIn('gold_holdings', status)
        self.assertIn('asset_availability', status)
        self.assertIn('paxg', status['asset_availability'])
        self.assertIn('xaut', status['asset_availability'])
        print("✅ Agent 63 status test passed")
        
    def test_agent_18_initialization(self):
        """Test Risk Guardian initialization"""
        from agents.agent_18_risk_guardian import RiskGuardian
        
        guardian = RiskGuardian(self.event_bus, self.state_manager)
        
        self.assertEqual(guardian.agent_id, "risk_guardian")
        self.assertIn('max_drawdown', guardian.config)
        self.assertIn('max_position_size', guardian.config)
        print("✅ Agent 18 initialized")
        
    def test_agent_69_initialization(self):
        """Test Momentum Rotator initialization"""
        from agents.agent_69_momentum_rotator import MomentumRotator
        
        rotator = MomentumRotator(self.event_bus, self.state_manager)
        
        self.assertEqual(rotator.agent_id, "momentum_rotator")
        self.assertIn('entry_threshold', rotator.config)
        self.assertIn('exit_threshold', rotator.config)
        print("✅ Agent 69 initialized")
        
    def test_agent_72_initialization(self):
        """Test Command Interface initialization"""
        from agents.agent_72_command_interface import CommandInterface
        
        interface = CommandInterface(self.event_bus, self.state_manager)
        
        self.assertEqual(interface.agent_id, "command_interface")
        self.assertIn('/swap_gold', interface.commands)
        self.assertIn('/gold_holdings', interface.commands)
        print("✅ Agent 72 initialized with gold swap commands")
        
    async def test_agent_72_gold_commands(self):
        """Test Command Interface gold swap commands"""
        from agents.agent_72_command_interface import CommandInterface
        
        interface = CommandInterface(self.event_bus, self.state_manager)
        
        # Test /swap_gold
        result = await interface.cmd_swap_gold(['1000'])
        self.assertEqual(result['status'], 'pending')
        print("✅ /swap_gold command test passed")
        
        # Test /gold_holdings
        self.state_manager.get = AsyncMock(return_value={'paxg': 0.5})
        result = await interface.cmd_gold_holdings([])
        self.assertEqual(result['status'], 'success')
        print("✅ /gold_holdings command test passed")
        
        # Test /gold_price
        result = await interface.cmd_gold_price([])
        self.assertEqual(result['status'], 'success')
        self.assertIn('paxg_usd', result['data'])
        print("✅ /gold_price command test passed")
        
    def test_agent_65_initialization(self):
        """Test Capital Allocator initialization"""
        from agents.agent_65_capital_allocator import CapitalAllocator
        
        allocator = CapitalAllocator(self.event_bus, self.state_manager)
        
        self.assertEqual(allocator.agent_id, "capital_allocator")
        self.assertIn('allocation_modes', dir(allocator))
        print("✅ Agent 65 initialized")
        
    def test_agent_00_initialization(self):
        """Test CEO Agent initialization"""
        from agents.agent_00_ceo import CEOAgent
        
        ceo = CEOAgent(self.event_bus, self.state_manager)
        
        self.assertEqual(ceo.agent_id, "ceo")
        self.assertIn('strategic_goals', dir(ceo))
        self.assertIn('approval_queue', dir(ceo))
        print("✅ Agent 00 initialized")


def run_async_agent_tests():
    """Run all async agent tests"""
    test = TestAgents()
    test.setUp()
    
    # List of async tests to run
    async_tests = [
        test.test_agent_63_start_stop,
        test.test_agent_63_event_subscriptions,
        test.test_agent_63_handle_swap_request,
        test.test_agent_63_handle_depeg,
        test.test_agent_63_handle_recovery,
        test.test_agent_63_get_status,
        test.test_agent_72_gold_commands
    ]
    
    print("🧪 Running Agent Tests...")
    print("="*50)
    
    for test_func in async_tests:
        try:
            asyncio.run(test_func())
        except Exception as e:
            print(f"❌ Test failed: {e}")
            
    print("="*50)
    print("✅ All agent tests complete!")


if __name__ == '__main__':
    # Run sync tests first
    print("🧪 Running Agent Tests...")
    print("="*50)
    
    test = TestAgents()
    test.setUp()
    
    # Sync tests
    sync_tests = [
        test.test_agent_63_initialization,
        test.test_agent_18_initialization,
        test.test_agent_69_initialization,
        test.test_agent_72_initialization,
        test.test_agent_65_initialization,
        test.test_agent_00_initialization
    ]
    
    for test_func in sync_tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    # Run async tests
    run_async_agent_tests()
