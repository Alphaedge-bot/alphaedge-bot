# tests/test_config.py
# AlphaEdge V13.0.5 – Configuration Tests
# Created: July 7, 2026

"""
Test suite for configuration loading and validation.
Verifies all config files are properly formatted and accessible.
"""

import unittest
import yaml
import os
from pathlib import Path


class TestConfig(unittest.TestCase):
    """Test configuration files"""
    
    def setUp(self):
        """Setup test environment"""
        self.config_dir = Path("config")
        self.test_configs = [
            "config.yaml",
            "gas_config.yaml",
            "rpc_config.yaml",
            "hedge_config.yaml"
        ]
        
    def test_config_files_exist(self):
        """Test that all config files exist"""
        for config_file in self.test_configs:
            file_path = self.config_dir / config_file
            self.assertTrue(
                file_path.exists(),
                f"Config file {config_file} does not exist"
            )
            print(f"✅ {config_file} exists")
            
    def test_config_files_are_yaml(self):
        """Test that all config files are valid YAML"""
        for config_file in self.test_configs:
            file_path = self.config_dir / config_file
            try:
                with open(file_path, 'r') as f:
                    yaml.safe_load(f)
                print(f"✅ {config_file} is valid YAML")
            except yaml.YAMLError as e:
                self.fail(f"{config_file} is not valid YAML: {e}")
                
    def test_main_config_structure(self):
        """Test main config has required sections"""
        file_path = self.config_dir / "config.yaml"
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Check required sections
        required_sections = [
            'bot',
            'hardware',
            'wallets',
            'blockchain',
            'gold_swap',
            'profit_allocation',
            'stablecoin',
            'scoring',
            'fed_liquidity'
        ]
        
        for section in required_sections:
            self.assertIn(
                section,
                config,
                f"Missing required section: {section}"
            )
            print(f"✅ Found section: {section}")
            
    def test_gas_config_structure(self):
        """Test gas config has required sections"""
        file_path = self.config_dir / "gas_config.yaml"
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
            
        required_sections = [
            'gas_tokens',
            'reserve_management',
            'priority_fees',
            'optimization',
            'monitoring'
        ]
        
        for section in required_sections:
            self.assertIn(
                section,
                config,
                f"Missing required section: {section}"
            )
            print(f"✅ Found gas section: {section}")
            
    def test_rpc_config_structure(self):
        """Test RPC config has required sections"""
        file_path = self.config_dir / "rpc_config.yaml"
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
            
        required_sections = [
            'solana',
            'ethereum',
            'bsc',
            'failover',
            'monitoring'
        ]
        
        for section in required_sections:
            self.assertIn(
                section,
                config,
                f"Missing required section: {section}"
            )
            print(f"✅ Found RPC section: {section}")
            
    def test_hedge_config_structure(self):
        """Test hedge config has required sections"""
        file_path = self.config_dir / "hedge_config.yaml"
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
            
        required_sections = [
            'risk_parameters',
            'stop_loss',
            'take_profit',
            'position_sizing',
            'drawdown_protection',
            'dynamic_hedging'
        ]
        
        for section in required_sections:
            self.assertIn(
                section,
                config,
                f"Missing required section: {section}"
            )
            print(f"✅ Found hedge section: {section}")
            
    def test_config_values_are_valid(self):
        """Test that config values are within valid ranges"""
        file_path = self.config_dir / "config.yaml"
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Check capital limit
        capital_limit = config['wallets']['wallet_1_trading']['capital_limit']
        self.assertEqual(
            capital_limit,
            25000,
            f"Capital limit should be 25000, got {capital_limit}"
        )
        print(f"✅ Capital limit: ${capital_limit}")
        
        # Check gold swap enabled
        gold_swap_enabled = config['gold_swap']['enabled']
        self.assertTrue(gold_swap_enabled, "Gold swap should be enabled")
        print(f"✅ Gold swap enabled: {gold_swap_enabled}")
        
        # Check depeg threshold
        depeg_threshold = config['gold_swap']['recovery']['depeg_threshold']
        self.assertEqual(
            depeg_threshold,
            0.01,
            f"Depeg threshold should be 0.01, got {depeg_threshold}"
        )
        print(f"✅ Depeg threshold: {depeg_threshold}")
        
    def test_wallet_config(self):
        """Test wallet configuration"""
        file_path = self.config_dir / "config.yaml"
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
            
        wallets = config['wallets']
        
        # Check all three wallets exist
        self.assertIn('wallet_1_trading', wallets)
        self.assertIn('wallet_2_operations', wallets)
        self.assertIn('wallet_3_user_profit', wallets)
        
        # Check wallet 1 has USDC
        self.assertEqual(
            wallets['wallet_1_trading']['balance'],
            'USDC',
            "Wallet 1 should be USDC"
        )
        print("✅ Wallet 1: USDC")
        
        # Check wallet 2 has gas tokens
        gas_tokens = wallets['wallet_2_operations']['balance']
        self.assertIn('SOL', gas_tokens)
        self.assertIn('ETH', gas_tokens)
        self.assertIn('BNB', gas_tokens)
        print("✅ Wallet 2: Gas tokens configured")
        
        # Check wallet 3 is deposit only
        self.assertEqual(
            wallets['wallet_3_user_profit']['bot_access'],
            'DEPOSIT ONLY',
            "Wallet 3 should be deposit only"
        )
        print("✅ Wallet 3: Deposit only")


if __name__ == '__main__':
    unittest.main()
