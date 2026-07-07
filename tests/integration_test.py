# tests/integration_test.py
# AlphaEdge V13.0.5 – Integration Test Suite
# Created: July 7, 2026

"""
Integration test suite for AlphaEdge V13.0.5.
Tests complete system functionality end-to-end.
"""

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import yaml
from pathlib import Path


class IntegrationTest(unittest.TestCase):
    """Full system integration tests"""
    
    def setUp(self):
        """Setup test environment"""
        # Load all configs
        self.config_dir = Path("config")
        self.load_all_configs()
        
        # Setup mocks
        self.event_bus = Mock()
        self.state_manager = Mock()
        self.state_manager.get = AsyncMock(return_value={})
        self.state_manager.set = AsyncMock(return_value=True)
        
        # Test data
        self.test_amount = 1000
        self.test_token = "TEST"
        self.test_price = 100.0
        
    def load_all_configs(self):
        """Load all configuration files"""
        config_files = [
            "config.yaml",
            "gas_config.yaml",
            "rpc_config.yaml",
            "hedge_config.yaml"
        ]
        
        self.configs = {}
        for file in config_files:
            path = self.config_dir / file
            if path.exists():
                with open(path, 'r') as f:
                    self.configs[file] = yaml.safe_load(f)
                    
    def test_all_configs_loaded(self):
        """Test all configs loaded successfully"""
        expected_configs = [
            "config.yaml",
            "gas_config.yaml",
            "rpc_config.yaml",
            "hedge_config.yaml"
        ]
        
        for config in expected_configs:
            self.assertIn(config, self.configs)
            self.assertIsNotNone(self.configs[config])
            print(f"✅ {config} loaded")
            
    async def test_full_system_startup(self):
        """Test full system startup sequence"""
        # Import core components
        from core.event_bus import EventBus
        from core.state_manager import StateManager
        from agents.agent_63_profit_taking_executor import ProfitTakingExecutor
        
        # Create real instances
        event_bus = EventBus()
        state_manager = StateManager()
        
        # Start executor
        executor = ProfitTakingExecutor(event_bus, state_manager)
        await executor.start()
        
        self.assertTrue(executor.running)
        
        # Stop
        await executor.stop()
        self.assertFalse(executor.running)
        
        print("✅ Full system startup test passed")
        
    async def test_gold_swap_workflow(self):
        """Test complete gold swap workflow"""
        from agents.agent_63_profit_taking_executor import ProfitTakingExecutor
        
        executor = ProfitTakingExecutor(self.event_bus, self.state_manager)
        
        # Mock prices
        with patch.object(executor, 'get_current_price', return_value=3960.0):
            # 1. Check availability
            available = await executor.check_asset_availability('paxg', 1000)
            self.assertTrue(available)
            
            # 2. Execute swap
            result = await executor.execute_gold_swap(1000)
            self.assertEqual(result['status'], 'executed')
            
            # 3. Store result
            await executor.store_gold_swap(result, 'paxg')
            
            # 4. Check holdings
            holdings = await executor.state_manager.get('gold_holdings', {})
            self.assertIn('paxg', holdings)
            
        print("✅ Gold swap workflow test passed")
        
    async def test_fallback_workflow(self):
        """Test PAXG → XAUT fallback workflow"""
        from agents.agent_63_profit_taking_executor import ProfitTakingExecutor
        
        executor = ProfitTakingExecutor(self.event_bus, self.state_manager)
        
        # Mock PAXG unavailable, XAUT available
        with patch.object(executor, 'get_asset_liquidity') as mock_liquidity:
            mock_liquidity.side_effect = lambda x, y: 10000 if x == 'PAXG' else 1000000
            
            with patch.object(executor, 'get_current_price', return_value=3960.0):
                # Should fallback to XAUT
                result = await executor.execute_gold_swap(1000, preferred_asset='paxg')
                
                self.assertEqual(result['status'], 'executed')
                self.assertEqual(result['asset'], 'XAUT')
                
        print("✅ Fallback workflow test passed")
        
    async def test_recovery_workflow(self):
        """Test stable recovery workflow"""
        from agents.agent_63_profit_taking_executor import ProfitTakingExecutor
        
        executor = ProfitTakingExecutor(self.event_bus, self.state_manager)
        
        # Set holdings with PAXG
        self.state_manager.get = AsyncMock(return_value={'paxg': 0.25, 'xaut': 0})
        
        with patch.object(executor, 'get_current_price', return_value=3960.0):
            # Execute recovery
            result = await executor.execute_stable_swap()
            
            self.assertEqual(result['status'], 'executed')
            self.assertGreater(result['total_usdt'], 0)
            
        print("✅ Recovery workflow test passed")
        
    async def test_depeg_to_recovery_workflow(self):
        """Test complete depeg → swap → recovery cycle"""
        from agents.agent_63_profit_taking_executor import ProfitTakingExecutor
        
        executor = ProfitTakingExecutor(self.event_bus, self.state_manager)
        
        # Mock all required methods
        with patch.object(executor, 'get_current_price', return_value=3960.0):
            with patch.object(executor, 'get_asset_liquidity', return_value=5000000):
                
                # 1. Depeg event
                self.state_manager.get = AsyncMock(return_value={'USDT': 10000, 'USDC': 5000})
                executor.execute_gold_swap = AsyncMock(return_value={'status': 'executed', 'asset_received': 0.378})
                
                depeg_event = Mock()
                depeg_event.data = {'usdc_price': 0.98, 'usdt_price': 0.98}
                await executor.handle_depeg(depeg_event)
                
                # 2. Recovery event
                recovery_event = Mock()
                recovery_event.data = {'usdc_price': 1.00, 'usdt_price': 1.00}
                
                executor.execute_stable_swap = AsyncMock(return_value={'status': 'executed', 'total_usdt': 15000})
                await executor.handle_recovery(recovery_event)
                
                # Verify both handlers were called
                self.assertTrue(executor.execute_gold_swap.called)
                self.assertTrue(executor.execute_stable_swap.called)
                
        print("✅ Complete depeg → recovery cycle test passed")
        
    async def test_rpc_failover_workflow(self):
        """Test RPC failover workflow"""
        from core.rpc_manager import RPCManager
        
        # Test config
        config = {
            'solana': {
                'jito': {'url': 'https://test.jito.com'},
                'helius': {'url': 'https://test.helius.com'}
            },
            'failover': {
                'enabled': True,
                'fallback_order': {
                    'solana': ['jito', 'helius']
                }
            }
        }
        
        manager = RPCManager(config)
        
        # First endpoint should be jito
        endpoint = await manager.get_endpoint('solana')
        self.assertEqual(endpoint['name'], 'jito')
        
        # Mark as failed
        manager.mark_failed('solana', 'jito')
        
        # Should failover to helius
        endpoint = await manager.get_endpoint('solana')
        self.assertEqual(endpoint['name'], 'helius')
        
        print("✅ RPC failover workflow test passed")
        
    async def test_risk_management_workflow(self):
        """Test risk management workflow"""
        from agents.agent_18_risk_guardian import RiskGuardian
        
        guardian = RiskGuardian(self.event_bus, self.state_manager)
        
        # 1. Check position size
        size = await guardian.calculate_position_size(
            self.test_token,
            'mid_cap',
            self.test_price
        )
        self.assertGreater(size, 0)
        
        # 2. Check stop loss
        sl = await guardian.calculate_stop_loss(self.test_token, 'mid_cap')
        self.assertLess(sl, self.test_price)
        
        # 3. Check take profit
        tp = await guardian.calculate_take_profit(self.test_token, self.test_price)
        self.assertGreater(tp['tier_1'], self.test_price)
        
        # 4. Check risk score
        risk_score = await guardian.calculate_risk_score(self.test_token)
        self.assertIsNotNone(risk_score)
        self.assertGreaterEqual(risk_score, 0)
        self.assertLessEqual(risk_score, 100)
        
        print("✅ Risk management workflow test passed")
        
    async def test_command_workflow(self):
        """Test command interface workflow"""
        from agents.agent_72_command_interface import CommandInterface
        
        interface = CommandInterface(self.event_bus, self.state_manager)
        
        # Test swap command
        result = await interface.cmd_swap_gold(['1000'])
        self.assertEqual(result['status'], 'pending')
        
        # Test gold holdings command
        self.state_manager.get = AsyncMock(return_value={'paxg': 0.25})
        result = await interface.cmd_gold_holdings([])
        self.assertEqual(result['status'], 'success')
        self.assertIn('paxg', result['data'])
        
        # Test gold price command
        result = await interface.cmd_gold_price([])
        self.assertEqual(result['status'], 'success')
        self.assertIn('paxg_usd', result['data'])
        
        print("✅ Command workflow test passed")
        
    async def test_config_validation_workflow(self):
        """Test config validation workflow"""
        from core.config_validator import ConfigValidator
        
        validator = ConfigValidator()
        
        # Validate all configs
        for name, config in self.configs.items():
            result = await validator.validate_config(name, config)
            self.assertTrue(result['valid'], f"{name} validation failed: {result.get('errors', [])}")
            
        print("✅ Config validation workflow test passed")
        
    async def test_error_recovery_workflow(self):
        """Test error recovery workflow"""
        from agents.agent_41_auto_healer import AutoHealer
        
        healer = AutoHealer(self.event_bus, self.state_manager)
        
        # Simulate agent crash
        agent_id = "agent_63"
        
        # Start monitoring
        await healer.start()
        
        # Trigger failure
        await healer.report_failure(agent_id, "Connection timeout")
        
        # Verify recovery attempt
        self.assertTrue(healer.recovery_attempts.get(agent_id, 0) > 0)
        
        print("✅ Error recovery workflow test passed")


def run_integration_tests():
    """Run all integration tests"""
    test = IntegrationTest()
    test.setUp()
    
    print("🧪 Running Integration Tests...")
    print("="*60)
    print("Testing full system integration...")
    print("="*60)
    
    # Sync tests first
    test.test_all_configs_loaded()
    
    # Async tests
    async_tests = [
        test.test_full_system_startup,
        test.test_gold_swap_workflow,
        test.test_fallback_workflow,
        test.test_recovery_workflow,
        test.test_depeg_to_recovery_workflow,
        test.test_rpc_failover_workflow,
        test.test_risk_management_workflow,
        test.test_command_workflow,
        test.test_config_validation_workflow,
        test.test_error_recovery_workflow
    ]
    
    print("\n" + "="*60)
    print("Running async integration tests...")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_func in async_tests:
        try:
            asyncio.run(test_func())
            passed += 1
        except Exception as e:
            failed += 1
            print(f"❌ Test failed: {e}")
            
    print("\n" + "="*60)
    print(f"📊 RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ AlphaEdge V13.0.5 is ready for production!")
    else:
        print(f"⚠️ {failed} test(s) failed. Please review.")
        
    return failed == 0


if __name__ == '__main__':
    success = run_integration_tests()
    exit(0 if success else 1)
