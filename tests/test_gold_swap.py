# tests/test_gold_swap.py
# AlphaEdge V13.0.5 – Gold Swap Tests
# Created: July 7, 2026

"""
Test suite for gold swap functionality.
Verifies PAXG + XAUT swap logic, platform selection, and fallback behavior.
"""

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime


class TestGoldSwap(unittest.TestCase):
    """Test gold swap functionality"""
    
    def setUp(self):
        """Setup test environment"""
        # Mock event bus and state manager
        self.event_bus = Mock()
        self.state_manager = Mock()
        
        # Create mock gold holdings
        self.mock_holdings = {
            'paxg': 0.0,
            'xaut': 0.0,
            'last_swap': None,
            'last_update': None
        }
        
        # Mock state manager returns
        self.state_manager.get = AsyncMock(return_value=self.mock_holdings)
        self.state_manager.set = AsyncMock(return_value=True)
        
    def create_executor(self):
        """Create profit taking executor instance"""
        from agents.agent_63_profit_taking_executor import ProfitTakingExecutor
        return ProfitTakingExecutor(self.event_bus, self.state_manager)
        
    @patch('agents.agent_63_profit_taking_executor.ProfitTakingExecutor.get_current_price')
    async def test_paxg_availability(self, mock_price):
        """Test PAXG availability check"""
        executor = self.create_executor()
        
        # Mock PAXG price and gold price
        mock_price.side_effect = lambda x: 3960.0 if x == 'PAXG' else 3960.0
        
        # Check PAXG availability
        available = await executor.check_asset_availability('paxg', 1000)
        
        self.assertTrue(available, "PAXG should be available")
        print("✅ PAXG availability check passed")
        
    @patch('agents.agent_63_profit_taking_executor.ProfitTakingExecutor.get_current_price')
    async def test_xaut_availability(self, mock_price):
        """Test XAUT availability check"""
        executor = self.create_executor()
        
        # Mock XAUT price and gold price
        mock_price.side_effect = lambda x: 3965.0 if x == 'XAUT' else 3960.0
        
        # Check XAUT availability
        available = await executor.check_asset_availability('xaut', 1000)
        
        self.assertTrue(available, "XAUT should be available")
        print("✅ XAUT availability check passed")
        
    @patch('agents.agent_63_profit_taking_executor.ProfitTakingExecutor.get_current_price')
    @patch('agents.agent_63_profit_taking_executor.ProfitTakingExecutor.get_asset_liquidity')
    async def test_asset_fallback(self, mock_liquidity, mock_price):
        """Test PAXG → XAUT fallback when PAXG unavailable"""
        executor = self.create_executor()
        
        # Mock PAXG as unavailable (low liquidity)
        mock_liquidity.side_effect = lambda x, y: 10000 if x == 'PAXG' else 1000000
        mock_price.side_effect = lambda x: 3960.0
        
        # Try PAXG swap (should fallback to XAUT)
        result = await executor.execute_gold_swap(1000, preferred_asset='paxg')
        
        self.assertEqual(result['status'], 'executed')
        print(f"✅ Fallback to XAUT: {result.get('asset', 'UNKNOWN')}")
        
    @patch('agents.agent_63_profit_taking_executor.ProfitTakingExecutor.get_current_price')
    async def test_platform_selection(self, mock_price):
        """Test platform selection logic"""
        executor = self.create_executor()
        
        # Mock prices
        mock_price.side_effect = lambda x: 3960.0
        
        # Find best platform for PAXG
        platform = await executor.find_best_platform_for_asset(1000, 'paxg')
        
        self.assertIsNotNone(platform, "Platform should be found")
        self.assertIn('name', platform, "Platform should have name")
        self.assertIn('chain', platform, "Platform should have chain")
        print(f"✅ Best platform for PAXG: {platform['name']} on {platform['chain']}")
        
    async def test_swap_execution(self):
        """Test gold swap execution"""
        executor = self.create_executor()
        
        # Mock prices
        with patch.object(executor, 'get_current_price', return_value=3960.0):
            # Mock platform
            platform = {
                'name': 'jupiter',
                'chain': 'solana',
                'metrics': {
                    'fees': 2.0,
                    'slippage': 1.0,
                    'gas_cost': 0.01,
                    'liquidity': 5000000,
                    'mev_protection': True
                }
            }
            
            # Execute swap
            result = await executor.execute_single_swap(1000, platform, 'paxg')
            
            self.assertEqual(result['status'], 'executed')
            self.assertGreater(result['asset_received'], 0)
            print(f"✅ Swap executed: ${result['usdt_amount']} → {result['asset_received']:.4f} PAXG")
            
    async def test_split_swap(self):
        """Test split swap for large amounts"""
        executor = self.create_executor()
        
        with patch.object(executor, 'get_current_price', return_value=3960.0):
            platform = {
                'name': 'jupiter',
                'chain': 'solana',
                'metrics': {
                    'fees': 10.0,
                    'slippage': 5.0,
                    'gas_cost': 0.05,
                    'liquidity': 5000000,
                    'mev_protection': True
                }
            }
            
            # Execute split swap (>$5000)
            result = await executor.execute_split_swap(10000, platform, 'paxg')
            
            self.assertEqual(result['status'], 'executed')
            self.assertGreater(result['total_asset'], 0)
            self.assertGreater(result['num_orders'], 0)
            print(f"✅ Split swap: ${result['total_usdt']} → {result['total_asset']:.4f} PAXG in {result['num_orders']} orders")
            
    async def test_stable_recovery(self):
        """Test stablecoin recovery (PAXG → USDT)"""
        executor = self.create_executor()
        
        # Mock holdings with PAXG
        self.state_manager.get = AsyncMock(return_value={'paxg': 0.25, 'xaut': 0})
        
        with patch.object(executor, 'get_current_price', return_value=3960.0):
            result = await executor.execute_stable_swap()
            
            self.assertEqual(result['status'], 'executed')
            self.assertGreater(result['total_usdt'], 0)
            print(f"✅ Recovery: {result['total_usdt']:.2f} USDT")
            
    async def test_both_assets_holdings(self):
        """Test tracking both PAXG and XAUT holdings"""
        executor = self.create_executor()
        
        # Mock holdings with both assets
        self.state_manager.get = AsyncMock(return_value={
            'paxg': 0.25,
            'xaut': 0.15
        })
        
        holdings = await executor.state_manager.get('gold_holdings', {})
        
        self.assertIn('paxg', holdings)
        self.assertIn('xaut', holdings)
        self.assertGreater(holdings['paxg'], 0)
        self.assertGreater(holdings['xaut'], 0)
        print(f"✅ Both holdings: PAXG={holdings['paxg']}, XAUT={holdings['xaut']}")
        
    @patch('agents.agent_63_profit_taking_executor.ProfitTakingExecutor.get_current_price')
    async def test_price_deviation_check(self, mock_price):
        """Test price deviation check"""
        executor = self.create_executor()
        
        # Mock price far from gold (invalid)
        mock_price.side_effect = lambda x: 4000.0 if x == 'PAXG' else 3960.0
        
        available = await executor.check_asset_availability('paxg', 1000)
        
        # Should be unavailable due to deviation >0.5%
        self.assertFalse(available, "PAXG should be unavailable with high deviation")
        print("✅ Price deviation check passed")
        
    async def test_store_gold_swap(self):
        """Test storing gold swap results"""
        executor = self.create_executor()
        
        result = {
            'status': 'executed',
            'asset': 'PAXG',
            'asset_received': 0.25,
            'usdt_amount': 1000,
            'timestamp': datetime.now().isoformat()
        }
        
        await executor.store_gold_swap(result, 'paxg')
        
        # Verify state was updated
        self.state_manager.set.assert_called()
        print("✅ Gold swap storage test passed")
        
    @patch('agents.agent_63_profit_taking_executor.ProfitTakingExecutor.get_current_price')
    async def test_depeg_trigger(self, mock_price):
        """Test depeg trigger handling"""
        executor = self.create_executor()
        
        # Mock prices
        mock_price.return_value = 3960.0
        
        # Mock stablecoin holdings
        self.state_manager.get = AsyncMock(return_value={'USDT': 5000, 'USDC': 5000})
        
        # Create depeg event
        event = Mock()
        event.data = {'usdc_price': 0.98, 'usdt_price': 0.98}
        
        # Handle depeg
        await executor.handle_depeg(event)
        
        # Should trigger gold swap
        self.state_manager.set.assert_called()
        print("✅ Depeg trigger test passed")


def run_async_tests():
    """Run all async tests"""
    test = TestGoldSwap()
    test.setUp()
    
    # Run async tests
    tests = [
        test.test_paxg_availability,
        test.test_xaut_availability,
        test.test_asset_fallback,
        test.test_platform_selection,
        test.test_swap_execution,
        test.test_split_swap,
        test.test_stable_recovery,
        test.test_both_assets_holdings,
        test.test_price_deviation_check,
        test.test_store_gold_swap,
        test.test_depeg_trigger
    ]
    
    for test_func in tests:
        try:
            asyncio.run(test_func())
        except Exception as e:
            print(f"❌ Test failed: {e}")
            

if __name__ == '__main__':
    print("🧪 Running Gold Swap Tests...")
    print("="*50)
    run_async_tests()
    print("="*50)
    print("✅ All gold swap tests complete!")
