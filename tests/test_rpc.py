# tests/test_rpc.py
# AlphaEdge V13.0.5 – RPC Connection Tests
# Created: July 7, 2026

"""
Test suite for RPC connections and failover.
Verifies multi-chain RPC connectivity and fallback behavior.
"""

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import yaml
from pathlib import Path


class TestRPC(unittest.TestCase):
    """Test RPC connectivity and failover"""
    
    def setUp(self):
        """Setup test environment"""
        self.config_dir = Path("config")
        self.load_config()
        
        # Mock responses
        self.mock_success_response = {
            'jsonrpc': '2.0',
            'result': 'success',
            'id': 1
        }
        
        self.mock_error_response = {
            'jsonrpc': '2.0',
            'error': {'code': -32000, 'message': 'Server error'},
            'id': 1
        }
        
    def load_config(self):
        """Load RPC configuration"""
        rpc_file = self.config_dir / "rpc_config.yaml"
        if rpc_file.exists():
            with open(rpc_file, 'r') as f:
                self.rpc_config = yaml.safe_load(f)
        else:
            self.rpc_config = {}
            
    def test_rpc_config_loaded(self):
        """Test RPC config loads correctly"""
        self.assertIsNotNone(self.rpc_config)
        self.assertIn('solana', self.rpc_config)
        self.assertIn('ethereum', self.rpc_config)
        self.assertIn('bsc', self.rpc_config)
        print("✅ RPC config loaded successfully")
        
    def test_solana_endpoints(self):
        """Test Solana RPC endpoints exist"""
        solana = self.rpc_config.get('solana', {})
        
        # Check all required endpoints
        required_endpoints = ['jito', 'helius', 'helius_free', 'public_solana']
        for endpoint in required_endpoints:
            self.assertIn(endpoint, solana, f"Missing endpoint: {endpoint}")
            
        # Check Jito endpoint details
        jito = solana.get('jito', {})
        self.assertEqual(jito.get('priority'), 1)
        self.assertTrue(jito.get('mev_protection', False))
        print("✅ Solana endpoints configured")
        
    def test_ethereum_endpoints(self):
        """Test Ethereum RPC endpoints exist"""
        ethereum = self.rpc_config.get('ethereum', {})
        
        required_endpoints = ['infura', 'alchemy', 'public_ethereum']
        for endpoint in required_endpoints:
            self.assertIn(endpoint, ethereum, f"Missing endpoint: {endpoint}")
            
        print("✅ Ethereum endpoints configured")
        
    def test_bsc_endpoints(self):
        """Test BSC RPC endpoints exist"""
        bsc = self.rpc_config.get('bsc', {})
        
        required_endpoints = ['binance', 'binance_backup', 'public_bsc']
        for endpoint in required_endpoints:
            self.assertIn(endpoint, bsc, f"Missing endpoint: {endpoint}")
            
        print("✅ BSC endpoints configured")
        
    def test_failover_config(self):
        """Test RPC failover configuration"""
        failover = self.rpc_config.get('failover', {})
        
        self.assertTrue(failover.get('enabled', False))
        self.assertIn('fallback_order', failover)
        self.assertIn('solana', failover['fallback_order'])
        self.assertIn('ethereum', failover['fallback_order'])
        self.assertIn('bsc', failover['fallback_order'])
        print("✅ Failover configuration present")
        
    def test_monitoring_config(self):
        """Test RPC monitoring configuration"""
        monitoring = self.rpc_config.get('monitoring', {})
        
        self.assertTrue(monitoring.get('enabled', False))
        self.assertIn('metrics', monitoring)
        self.assertIn('alerts', monitoring)
        print("✅ Monitoring configuration present")
        
    @patch('aiohttp.ClientSession.post')
    async def test_rpc_connection_success(self, mock_post):
        """Test successful RPC connection"""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=self.mock_success_response)
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Test Solana connection
        from core.rpc_manager import RPCManager
        manager = RPCManager(self.rpc_config)
        
        result = await manager.test_connection('solana', 'jito')
        
        self.assertTrue(result)
        print("✅ RPC connection test passed")
        
    @patch('aiohttp.ClientSession.post')
    async def test_rpc_connection_failover(self, mock_post):
        """Test RPC failover on connection failure"""
        # Mock failure then success
        mock_response_error = AsyncMock()
        mock_response_error.status = 500
        mock_response_error.json = AsyncMock(return_value=self.mock_error_response)
        
        mock_response_success = AsyncMock()
        mock_response_success.status = 200
        mock_response_success.json = AsyncMock(return_value=self.mock_success_response)
        
        # First call fails, second succeeds
        mock_post.return_value.__aenter__.side_effect = [
            mock_response_error,
            mock_response_success
        ]
        
        from core.rpc_manager import RPCManager
        manager = RPCManager(self.rpc_config)
        
        # Should try Jito (fail) then fallback to Helius (success)
        result = await manager.get_connection('solana')
        
        self.assertIsNotNone(result)
        print("✅ RPC failover test passed")
        
    @patch('aiohttp.ClientSession.post')
    async def test_rpc_rate_limit_handling(self, mock_post):
        """Test RPC rate limit handling"""
        # Mock rate limit response (429)
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.text = AsyncMock(return_value='Rate limit exceeded')
        mock_post.return_value.__aenter__.return_value = mock_response
        
        from core.rpc_manager import RPCManager
        manager = RPCManager(self.rpc_config)
        
        # Should handle rate limit and move to next endpoint
        result = await manager.get_connection('solana')
        
        # Should have moved to fallback
        self.assertIsNotNone(result)
        print("✅ Rate limit handling test passed")
        
    @patch('aiohttp.ClientSession.post')
    async def test_rpc_timeout_handling(self, mock_post):
        """Test RPC timeout handling"""
        # Mock timeout
        mock_post.return_value.__aenter__.side_effect = asyncio.TimeoutError()
        
        from core.rpc_manager import RPCManager
        manager = RPCManager(self.rpc_config)
        
        # Should handle timeout and move to fallback
        result = await manager.get_connection('solana')
        
        # Should have moved to fallback
        self.assertIsNotNone(result)
        print("✅ Timeout handling test passed")
        
    def test_websocket_config(self):
        """Test WebSocket configuration"""
        websocket = self.rpc_config.get('websocket', {})
        
        self.assertTrue(websocket.get('enabled', False))
        self.assertIn('endpoints', websocket)
        self.assertIn('solana', websocket['endpoints'])
        self.assertIn('reconnect', websocket)
        print("✅ WebSocket configuration present")
        
    def test_optimization_config(self):
        """Test RPC optimization configuration"""
        optimization = self.rpc_config.get('optimization', {})
        
        self.assertTrue(optimization.get('enabled', False))
        self.assertIn('connection_pool', optimization)
        self.assertIn('caching', optimization)
        print("✅ Optimization configuration present")
        
    async def test_health_check(self):
        """Test RPC health check"""
        from core.rpc_manager import RPCManager
        manager = RPCManager(self.rpc_config)
        
        # Mock health check
        with patch.object(manager, 'test_connection', return_value=True):
            health = await manager.check_health()
            
        self.assertIn('status', health)
        self.assertIn('latency', health)
        print("✅ Health check test passed")
        
    def test_rpc_security(self):
        """Test RPC security configuration"""
        security = self.rpc_config.get('security', {})
        
        self.assertTrue(security.get('enabled', False))
        self.assertIn('encryption', security)
        self.assertIn('rate_limiting', security)
        print("✅ Security configuration present")
        
    def test_rpc_logging(self):
        """Test RPC logging configuration"""
        logging = self.rpc_config.get('logging', {})
        
        self.assertTrue(logging.get('enabled', False))
        self.assertIn('log_events', logging)
        self.assertIn('retention_days', logging)
        print("✅ RPC logging configuration present")


class TestRPCManager(unittest.TestCase):
    """Test RPC Manager functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.config = {
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
        
    def test_manager_initialization(self):
        """Test RPC Manager initialization"""
        from core.rpc_manager import RPCManager
        
        manager = RPCManager(self.config)
        
        self.assertIsNotNone(manager)
        self.assertIn('solana', manager.endpoints)
        print("✅ RPC Manager initialized")
        
    async def test_endpoint_rotation(self):
        """Test endpoint rotation on failure"""
        from core.rpc_manager import RPCManager
        
        manager = RPCManager(self.config)
        
        # First endpoint should be jito
        endpoint = await manager.get_endpoint('solana')
        self.assertEqual(endpoint['name'], 'jito')
        
        # Mark as failed
        manager.mark_failed('solana', 'jito')
        
        # Next should be helius
        endpoint = await manager.get_endpoint('solana')
        self.assertEqual(endpoint['name'], 'helius')
        
        print("✅ Endpoint rotation test passed")
        
    async def test_endpoint_recovery(self):
        """Test endpoint recovery after failure"""
        from core.rpc_manager import RPCManager
        
        manager = RPCManager(self.config)
        
        # Mark as failed
        manager.mark_failed('solana', 'jito')
        
        # Wait for recovery (simulate)
        manager.recovery_times['solana_jito'] = 0  # Force immediate recovery
        
        # Should be available again
        await manager.recover_endpoints()
        self.assertNotIn('jito', manager.failed_endpoints.get('solana', []))
        
        print("✅ Endpoint recovery test passed")


def run_async_rpc_tests():
    """Run all async RPC tests"""
    test = TestRPC()
    test.setUp()
    
    async_tests = [
        test.test_rpc_connection_success,
        test.test_rpc_connection_failover,
        test.test_rpc_rate_limit_handling,
        test.test_rpc_timeout_handling,
        test.test_health_check
    ]
    
    print("🧪 Running RPC Tests...")
    print("="*50)
    
    for test_func in async_tests:
        try:
            asyncio.run(test_func())
        except Exception as e:
            print(f"❌ Test failed: {e}")
            
    print("="*50)
    print("✅ All RPC tests complete!")


if __name__ == '__main__':
    # Sync tests
    print("🧪 Running RPC Tests...")
    print("="*50)
    
    test = TestRPC()
    test.setUp()
    
    sync_tests = [
        test.test_rpc_config_loaded,
        test.test_solana_endpoints,
        test.test_ethereum_endpoints,
        test.test_bsc_endpoints,
        test.test_failover_config,
        test.test_monitoring_config,
        test.test_websocket_config,
        test.test_optimization_config,
        test.test_rpc_security,
        test.test_rpc_logging
    ]
    
    for test_func in sync_tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    # RPC Manager tests
    rpc_manager_test = TestRPCManager()
    rpc_manager_test.setUp()
    
    # Sync manager tests
    rpc_manager_test.test_manager_initialization()
    
    # Async manager tests
    asyncio.run(rpc_manager_test.test_endpoint_rotation())
    asyncio.run(rpc_manager_test.test_endpoint_recovery())
    
    # Run async tests
    run_async_rpc_tests()
