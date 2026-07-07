# tests/test_risk.py
# AlphaEdge V13.0.5 – Risk Management Tests
# Created: July 7, 2026

"""
Test suite for risk management functionality.
Verifies stop loss, take profit, position sizing, and drawdown protection.
"""

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import yaml
from pathlib import Path


class TestRisk(unittest.TestCase):
    """Test risk management functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.config_dir = Path("config")
        self.load_config()
        
        # Mock state manager and event bus
        self.event_bus = Mock()
        self.state_manager = Mock()
        self.state_manager.get = AsyncMock(return_value={})
        self.state_manager.set = AsyncMock(return_value=True)
        
        # Test data
        self.test_token = "TEST"
        self.test_entry_price = 100.0
        self.test_quantity = 1.0
        
    def load_config(self):
        """Load hedge configuration"""
        hedge_file = self.config_dir / "hedge_config.yaml"
        if hedge_file.exists():
            with open(hedge_file, 'r') as f:
                self.hedge_config = yaml.safe_load(f)
        else:
            self.hedge_config = {}
            
    def test_hedge_config_loaded(self):
        """Test hedge config loads correctly"""
        self.assertIsNotNone(self.hedge_config)
        self.assertIn('risk_parameters', self.hedge_config)
        self.assertIn('stop_loss', self.hedge_config)
        self.assertIn('take_profit', self.hedge_config)
        self.assertIn('position_sizing', self.hedge_config)
        print("✅ Hedge config loaded successfully")
        
    def test_stop_loss_config(self):
        """Test stop loss configuration"""
        stop_loss = self.hedge_config.get('stop_loss', {})
        
        self.assertTrue(stop_loss.get('enabled', False))
        self.assertIn('fixed_percentage', stop_loss)
        self.assertIn('trailing_stop', stop_loss)
        self.assertIn('atr_stop', stop_loss)
        
        # Check fixed percentages
        fixed = stop_loss.get('fixed_percentage', {})
        self.assertIn('micro_cap', fixed)
        self.assertIn('small_cap', fixed)
        self.assertIn('mid_cap', fixed)
        self.assertIn('large_cap', fixed)
        
        print("✅ Stop loss configuration valid")
        
    def test_take_profit_config(self):
        """Test take profit configuration"""
        take_profit = self.hedge_config.get('take_profit', {})
        
        self.assertTrue(take_profit.get('enabled', False))
        self.assertIn('targets', take_profit)
        self.assertIn('partial_take_profit', take_profit)
        self.assertIn('trailing_take_profit', take_profit)
        
        targets = take_profit.get('targets', {})
        self.assertIn('tier_1', targets)
        self.assertIn('tier_2', targets)
        self.assertIn('tier_3', targets)
        self.assertIn('tier_4', targets)
        
        print("✅ Take profit configuration valid")
        
    def test_position_sizing_config(self):
        """Test position sizing configuration"""
        sizing = self.hedge_config.get('position_sizing', {})
        
        self.assertTrue(sizing.get('enabled', False))
        self.assertIn('base_sizing', sizing)
        self.assertIn('pyramiding', sizing)
        self.assertIn('dynamic_sizing', sizing)
        
        base = sizing.get('base_sizing', {})
        self.assertIn('micro_cap', base)
        self.assertIn('small_cap', base)
        self.assertIn('mid_cap', base)
        self.assertIn('large_cap', base)
        
        print("✅ Position sizing configuration valid")
        
    def test_drawdown_protection_config(self):
        """Test drawdown protection configuration"""
        drawdown = self.hedge_config.get('drawdown_protection', {})
        
        self.assertTrue(drawdown.get('enabled', False))
        self.assertIn('circuit_breakers', drawdown)
        self.assertIn('actions', drawdown)
        
        breakers = drawdown.get('circuit_breakers', {})
        self.assertIn('consecutive_losses', breakers)
        self.assertIn('daily_drawdown', breakers)
        self.assertIn('weekly_drawdown', breakers)
        
        print("✅ Drawdown protection configuration valid")
        
    def test_risk_parameters(self):
        """Test risk parameters"""
        params = self.hedge_config.get('risk_parameters', {})
        
        self.assertIn('max_drawdown_daily', params)
        self.assertIn('max_drawdown_weekly', params)
        self.assertIn('max_drawdown_total', params)
        self.assertIn('max_position_size', params)
        self.assertIn('max_correlation', params)
        
        # Check values are reasonable
        self.assertLess(params.get('max_drawdown_daily', 1.0), 0.5)
        self.assertLess(params.get('max_position_size', 1.0), 0.2)
        
        print("✅ Risk parameters valid")
        
    def test_dynamic_hedging_config(self):
        """Test dynamic hedging configuration"""
        hedging = self.hedge_config.get('dynamic_hedging', {})
        
        self.assertTrue(hedging.get('enabled', False))
        self.assertIn('hedge_assets', hedging)
        self.assertIn('hedge_triggers', hedging)
        self.assertIn('hedge_allocation', hedging)
        
        assets = hedging.get('hedge_assets', [])
        self.assertIn('USDC', assets)
        self.assertIn('USDT', assets)
        self.assertIn('PAXG', assets)
        
        print("✅ Dynamic hedging configuration valid")
        
    def test_var_config(self):
        """Test Value at Risk configuration"""
        var = self.hedge_config.get('var', {})
        
        self.assertTrue(var.get('enabled', False))
        self.assertIn('calculation', var)
        self.assertIn('thresholds', var)
        self.assertIn('action_on_var_breach', var)
        
        calc = var.get('calculation', {})
        self.assertIn('confidence_level', calc)
        self.assertIn('lookback_days', calc)
        
        print("✅ VaR configuration valid")
        
    async def test_stop_loss_calculation(self):
        """Test stop loss calculation"""
        from agents.agent_18_risk_guardian import RiskGuardian
        
        guardian = RiskGuardian(self.event_bus, self.state_manager)
        
        # Calculate stop loss for different caps
        for cap in ['micro_cap', 'small_cap', 'mid_cap', 'large_cap']:
            sl = await guardian.calculate_stop_loss(self.test_token, cap)
            self.assertIsNotNone(sl)
            self.assertLess(sl, self.test_entry_price)
            
        print("✅ Stop loss calculation test passed")
        
    async def test_take_profit_calculation(self):
        """Test take profit calculation"""
        from agents.agent_18_risk_guardian import RiskGuardian
        
        guardian = RiskGuardian(self.event_bus, self.state_manager)
        
        # Calculate take profit targets
        targets = await guardian.calculate_take_profit(
            self.test_token,
            self.test_entry_price
        )
        
        self.assertIn('tier_1', targets)
        self.assertIn('tier_2', targets)
        self.assertIn('tier_3', targets)
        self.assertIn('tier_4', targets)
        
        # Ensure targets are increasing
        self.assertLess(targets['tier_1'], targets['tier_2'])
        self.assertLess(targets['tier_2'], targets['tier_3'])
        self.assertLess(targets['tier_3'], targets['tier_4'])
        
        print("✅ Take profit calculation test passed")
        
    async def test_position_sizing(self):
        """Test position sizing calculation"""
        from agents.agent_18_risk_guardian import RiskGuardian
        
        guardian = RiskGuardian(self.event_bus, self.state_manager)
        
        # Calculate position size for different caps
        for cap in ['micro_cap', 'small_cap', 'mid_cap', 'large_cap']:
            size = await guardian.calculate_position_size(
                self.test_token,
                cap,
                self.test_entry_price
            )
            self.assertIsNotNone(size)
            self.assertGreater(size, 0)
            
        print("✅ Position sizing test passed")
        
    async def test_drawdown_check(self):
        """Test drawdown detection"""
        from agents.agent_18_risk_guardian import RiskGuardian
        
        guardian = RiskGuardian(self.event_bus, self.state_manager)
        
        # Simulate drawdown
        current_value = 8500
        peak_value = 10000
        
        drawdown = (peak_value - current_value) / peak_value
        
        # Check if drawdown exceeds threshold
        threshold = 0.10  # 10%
        self.assertGreater(drawdown, threshold)
        
        # Test drawdown detection
        result = await guardian.check_drawdown(current_value, peak_value)
        self.assertTrue(result)
        
        print("✅ Drawdown detection test passed")
        
    async def test_correlation_calculation(self):
        """Test correlation calculation between assets"""
        from agents.agent_18_risk_guardian import RiskGuardian
        
        guardian = RiskGuardian(self.event_bus, self.state_manager)
        
        # Mock price data for two assets
        asset1_prices = [100, 101, 102, 101, 100]
        asset2_prices = [100, 99, 98, 99, 100]
        
        correlation = await guardian.calculate_correlation(
            asset1_prices,
            asset2_prices
        )
        
        self.assertIsNotNone(correlation)
        self.assertGreaterEqual(correlation, -1.0)
        self.assertLessEqual(correlation, 1.0)
        
        print("✅ Correlation calculation test passed")
        
    async def test_var_calculation(self):
        """Test VaR calculation"""
        from agents.agent_18_risk_guardian import RiskGuardian
        
        guardian = RiskGuardian(self.event_bus, self.state_manager)
        
        # Mock historical returns
        returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01, -0.01]
        
        var = await guardian.calculate_var(returns, confidence_level=0.95)
        
        self.assertIsNotNone(var)
        self.assertLess(var, 0)  # VaR should be negative
        print(f"✅ VaR calculation test passed: {var:.2%}")
        
    async def test_circuit_breaker(self):
        """Test circuit breaker activation"""
        from agents.agent_18_risk_guardian import RiskGuardian
        
        guardian = RiskGuardian(self.event_bus, self.state_manager)
        
        # Simulate consecutive losses
        for i in range(5):
            result = await guardian.record_loss()
            
        # Check if circuit breaker triggered
        self.assertTrue(guardian.circuit_breaker_active)
        print("✅ Circuit breaker test passed")
        
    async def test_regime_risk_adjustment(self):
        """Test regime-based risk adjustment"""
        from agents.agent_18_risk_guardian import RiskGuardian
        
        guardian = RiskGuardian(self.event_bus, self.state_manager)
        
        # Test different regimes
        for regime in ['bull', 'alt_season', 'accumulation', 'bear', 'crash']:
            adjustment = await guardian.get_regime_adjustment(regime)
            self.assertIsNotNone(adjustment)
            self.assertGreaterEqual(adjustment, 0.0)
            self.assertLessEqual(adjustment, 1.0)
            
        print("✅ Regime risk adjustment test passed")
        
    async def test_black_swan_protection(self):
        """Test black swan protection"""
        from agents.agent_18_risk_guardian import RiskGuardian
        
        guardian = RiskGuardian(self.event_bus, self.state_manager)
        
        # Simulate black swan event
        event = {
            'type': 'price_drop',
            'magnitude': 0.25,  # 25% drop
            'asset': 'BTC'
        }
        
        triggered = await guardian.check_black_swan(event)
        
        self.assertTrue(triggered)
        print("✅ Black swan protection test passed")


def run_async_risk_tests():
    """Run all async risk tests"""
    test = TestRisk()
    test.setUp()
    
    async_tests = [
        test.test_stop_loss_calculation,
        test.test_take_profit_calculation,
        test.test_position_sizing,
        test.test_drawdown_check,
        test.test_correlation_calculation,
        test.test_var_calculation,
        test.test_circuit_breaker,
        test.test_regime_risk_adjustment,
        test.test_black_swan_protection
    ]
    
    print("🧪 Running Risk Tests...")
    print("="*50)
    
    for test_func in async_tests:
        try:
            asyncio.run(test_func())
        except Exception as e:
            print(f"❌ Test failed: {e}")
            
    print("="*50)
    print("✅ All risk tests complete!")


if __name__ == '__main__':
    # Sync tests
    print("🧪 Running Risk Tests...")
    print("="*50)
    
    test = TestRisk()
    test.setUp()
    
    sync_tests = [
        test.test_hedge_config_loaded,
        test.test_stop_loss_config,
        test.test_take_profit_config,
        test.test_position_sizing_config,
        test.test_drawdown_protection_config,
        test.test_risk_parameters,
        test.test_dynamic_hedging_config,
        test.test_var_config
    ]
    
    for test_func in sync_tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    # Run async tests
    run_async_risk_tests()
